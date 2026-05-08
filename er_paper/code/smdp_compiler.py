"""
smdp_compiler.py — Compile a BPMN+OPT JSON problem into a general SMDP JSON.

The compilation runs Monte Carlo simulation episodes to discover:
  - The abstract state space S
  - Available actions A(s) for each state
  - Transition probabilities P(s' | s, a)
  - Expected step rewards R(s, a, s')
  - Expected holding times τ(s, a, s')

The output is a self-contained SMDP JSON that any standard SMDP solver can
consume, independent of the original BPMN+OPT model or SimPN runtime.

Usage:
    python smdp_compiler.py --input ../models/fig2_problem.json --output ../models/fig2_smdp.json
"""

import sys
import os
import json
import random
import argparse
from collections import defaultdict

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_ER_PAPER_DIR = os.path.dirname(_CODE_DIR)
sys.path.insert(0, _CODE_DIR)
sys.path.insert(0, os.path.dirname(_ER_PAPER_DIR))

from smdp_env import SMDPEnv


def _abstract_state(env):
    """Map environment state to a hashable abstract state tuple."""
    waiting = env.model.get_waiting_cases()
    idle = env.model.get_idle_resources()
    type_counts = {}
    for tok in waiting:
        t = tok.value["type"] if isinstance(tok.value, dict) else tok.value.type
        type_counts[t] = type_counts.get(t, 0) + 1
    idle_ids = tuple(sorted(
        (tok.value["id"] if isinstance(tok.value, dict) else tok.value.id)
        for tok in idle
    ))
    return (tuple(sorted(type_counts.items())), idle_ids)


def _abstract_action(action, env):
    """Map (case_id, resource_id) to (case_type, resource_id)."""
    c_id, r_id = action
    for tok in env.model.get_waiting_cases():
        val = tok.value
        pid = val["id"] if isinstance(val, dict) else val.id
        if pid == c_id:
            c_type = val["type"] if isinstance(val, dict) else val.type
            return (c_type, r_id)
    return action


def _resolve_abstract_to_concrete(abs_action, actions, env):
    """FIFO tiebreaking: pick earliest-waiting patient of the given type."""
    c_type, r_id = abs_action
    waiting = env.model.get_waiting_cases()
    best_concrete = None
    earliest_start = float("inf")
    for tok in waiting:
        val = tok.value
        pid = val["id"] if isinstance(val, dict) else val.id
        ptype = val["type"] if isinstance(val, dict) else val.type
        start = val["start"] if isinstance(val, dict) else val.start
        if ptype == c_type and start < earliest_start:
            if any(cid == pid and rid == r_id for cid, rid in actions):
                earliest_start = start
                best_concrete = (pid, r_id)
    return best_concrete


def _state_to_str(state):
    """Convert abstract state tuple to a readable string key."""
    type_counts, idle_ids = state
    parts = []
    for ct, n in type_counts:
        parts.append(f"{n}x{ct}")
    waiting_str = ",".join(parts) if parts else "empty"
    idle_str = ",".join(idle_ids) if idle_ids else "none"
    return f"W({waiting_str})_R({idle_str})"


def _action_to_str(action):
    """Convert abstract action tuple to a readable string key."""
    c_type, r_id = action
    return f"{c_type}->{r_id}"


def compile_smdp(bpmnopt_json_path, n_episodes=2000, seed_base=0, verbose=True):
    """
    Compile a BPMN+OPT problem into an SMDP model via Monte Carlo exploration.

    Returns a dict representing the complete SMDP, ready for JSON serialization.
    """
    with open(bpmnopt_json_path) as f:
        spec = json.load(f)

    env = SMDPEnv(json_path=bpmnopt_json_path)

    transitions = defaultdict(lambda: defaultdict(list))
    state_actions = defaultdict(set)
    initial_state_counts = defaultdict(int)

    if verbose:
        print(f"Compiling BPMN+OPT -> SMDP ({n_episodes} episodes)...")

    for ep in range(n_episodes):
        env.reset(seed=seed_base + ep)
        abs_state = _abstract_state(env)
        initial_state_counts[abs_state] += 1
        prev_time = env.model.problem.clock

        while not env.done:
            actions = env.get_actions()
            if not actions:
                break

            abs_actions = set()
            for a in actions:
                abs_actions.add(_abstract_action(a, env))
            chosen_abs = random.choice(list(abs_actions))
            concrete = _resolve_abstract_to_concrete(chosen_abs, actions, env)
            if concrete is None:
                concrete = random.choice(actions)

            abs_action = _abstract_action(concrete, env)
            state_actions[abs_state].add(abs_action)

            _, reward, done, info = env.step(concrete)
            abs_next = _abstract_state(env)
            current_time = env.model.problem.clock
            tau = current_time - prev_time

            transitions[(abs_state, abs_action)][abs_next].append({
                "reward": reward,
                "holding_time": tau,
            })

            if not info.get("same_time", False):
                prev_time = current_time
            abs_state = abs_next

    all_states = set(state_actions.keys())
    for (s, a), trans in transitions.items():
        all_states.add(s)
        all_states.update(trans.keys())

    state_index = {}
    for s in sorted(all_states, key=str):
        state_index[s] = _state_to_str(s)

    action_index = {}
    for s, acts in state_actions.items():
        for a in acts:
            if a not in action_index:
                action_index[a] = _action_to_str(a)

    smdp_states = []
    for s in sorted(all_states, key=str):
        tc, idle = s
        smdp_states.append({
            "id": state_index[s],
            "waiting_type_counts": {ct: n for ct, n in tc},
            "idle_resources": list(idle),
        })

    smdp_actions = {}
    for s, acts in state_actions.items():
        s_id = state_index[s]
        smdp_actions[s_id] = sorted(action_index[a] for a in acts)

    smdp_transitions = {}
    for (s, a), trans_map in transitions.items():
        s_id = state_index[s]
        a_id = action_index[a]
        total_samples = sum(len(samples) for samples in trans_map.values())

        if s_id not in smdp_transitions:
            smdp_transitions[s_id] = {}
        if a_id not in smdp_transitions[s_id]:
            smdp_transitions[s_id][a_id] = {}

        for ns, samples in trans_map.items():
            ns_id = state_index[ns]
            prob = len(samples) / total_samples
            avg_reward = sum(s["reward"] for s in samples) / len(samples)
            avg_tau = sum(s["holding_time"] for s in samples) / len(samples)
            smdp_transitions[s_id][a_id][ns_id] = {
                "probability": round(prob, 6),
                "expected_reward": round(avg_reward, 4),
                "expected_holding_time": round(avg_tau, 4),
                "n_samples": len(samples),
            }

    total_initial = sum(initial_state_counts.values())
    initial_distribution = {
        state_index[s]: round(c / total_initial, 6)
        for s, c in initial_state_counts.items()
    }

    smdp_json = {
        "name": spec["name"] + "_smdp",
        "description": f"SMDP compiled from BPMN+OPT problem '{spec['name']}'",
        "source": {
            "type": "bpmn+opt",
            "problem_name": spec["name"],
            "compilation_episodes": n_episodes,
        },
        "smdp": {
            "discount": spec["smdp"]["discount"],
            "horizon": spec["smdp"]["horizon"],
            "n_states": len(smdp_states),
            "n_actions": len(action_index),
            "states": smdp_states,
            "actions": smdp_actions,
            "transitions": smdp_transitions,
            "initial_state_distribution": initial_distribution,
            "reward_semantics": {
                "type": "holding_cost",
                "description": "Step reward = -integral of n(t) over the holding interval between decision epochs. "
                               "Represents the cycle-time contribution of each interval.",
            },
            "objective": spec["decision"]["objectives"][0] if spec["decision"].get("objectives") else {},
        },
    }

    if verbose:
        print(f"  States:      {len(smdp_states)}")
        print(f"  Actions:     {len(action_index)}")
        print(f"  Transitions: {sum(len(a) for a in smdp_transitions.values())} state-action pairs")
        total_trans = sum(
            len(ns_map)
            for a_map in smdp_transitions.values()
            for ns_map in a_map.values()
        )
        print(f"  Total (s,a,s') triples: {total_trans}")

    return smdp_json


def main():
    parser = argparse.ArgumentParser(description="Compile BPMN+OPT JSON to SMDP JSON")
    parser.add_argument("--input", "-i", required=True, help="Path to BPMN+OPT problem JSON")
    parser.add_argument("--output", "-o", required=True, help="Output path for SMDP JSON")
    parser.add_argument("--episodes", "-n", type=int, default=2000, help="Monte Carlo episodes")
    args = parser.parse_args()

    smdp = compile_smdp(args.input, n_episodes=args.episodes)

    with open(args.output, "w") as f:
        json.dump(smdp, f, indent=2)

    print(f"\nSMDP model written to: {args.output}")


if __name__ == "__main__":
    main()
