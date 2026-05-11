"""
smdp_compiler.py — Compile a BPMN+OPT JSON problem into a general SMDP JSON.

The compilation runs Monte Carlo simulation episodes to discover:
  - The abstract state space S
  - Available actions A(s) for each state
  - Transition probabilities P(s' | s, a)
  - Expected step rewards R(s, a, s')
  - Expected holding times τ(s, a, s')

Uses the environment's own abstraction methods (abstract_state, abstract_action,
resolve_abstract_action), making the compiler fully generic across any BPMN+OPT model.

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
        abs_state = env.abstract_state()
        initial_state_counts[abs_state] += 1
        prev_time = env.model.problem.clock

        step_count = 0
        max_steps = 5000
        while not env.done and step_count < max_steps:
            actions = env.get_actions()
            if not actions:
                break

            # Bias scheduling toward immediate to prevent backlogs
            schedule_acts = [a for a in actions if a[0] == "schedule"]
            if schedule_acts and random.random() < 0.7:
                immediates = [a for a in schedule_acts if a[2] == 0]
                concrete = immediates[0] if immediates else schedule_acts[0]
            else:
                abs_actions = set()
                for a in actions:
                    abs_actions.add(env.abstract_action(a))
                chosen_abs = random.choice(sorted(abs_actions))
                concrete = env.resolve_abstract_action(chosen_abs, actions)
                if concrete is None:
                    concrete = random.choice(actions)

            abs_action = env.abstract_action(concrete)
            state_actions[abs_state].add(abs_action)

            _, reward, done, info = env.step(concrete)
            abs_next = env.abstract_state()
            current_time = env.model.problem.clock
            tau = current_time - prev_time

            transitions[(abs_state, abs_action)][abs_next].append({
                "reward": reward,
                "holding_time": tau,
            })

            if not info.get("same_time", False):
                prev_time = current_time
            abs_state = abs_next
            step_count += 1

        if verbose and (ep + 1) % max(1, n_episodes // 10) == 0:
            print(f"  Episode {ep+1}/{n_episodes} (states: {len(state_actions)})")

    all_states = set(state_actions.keys())
    for (s, a), trans in transitions.items():
        all_states.add(s)
        all_states.update(trans.keys())

    state_index = {s: _state_to_str(s) for s in sorted(all_states, key=str)}

    action_index = {}
    for s, acts in state_actions.items():
        for a in acts:
            if a not in action_index:
                action_index[a] = _action_to_str(a)

    smdp_states = []
    for s in sorted(all_states, key=str):
        smdp_states.append({"id": state_index[s], "raw": str(s)})

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
            avg_reward = sum(sm["reward"] for sm in samples) / len(samples)
            avg_tau = sum(sm["holding_time"] for sm in samples) / len(samples)
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
                "description": "Step reward = -integral of n(t) over the holding interval.",
            },
            "objective": spec["decision"]["objectives"][0] if spec["decision"].get("objectives") else {},
        },
    }

    if verbose:
        print(f"  States:      {len(smdp_states)}")
        print(f"  Actions:     {len(action_index)}")
        total_trans = sum(
            len(ns_map)
            for a_map in smdp_transitions.values()
            for ns_map in a_map.values()
        )
        print(f"  Total (s,a,s') triples: {total_trans}")

    return smdp_json


def _state_to_str(state):
    """Generic state-to-string for any abstract state tuple."""
    parts = []
    for component in state:
        if isinstance(component, tuple):
            items = []
            for k, v in component:
                items.append(f"{k}={v}")
            parts.append(",".join(items) if items else "empty")
        else:
            parts.append(str(component))
    return "S(" + "|".join(parts) + ")"


def _action_to_str(action):
    """Generic action-to-string for any typed abstract action tuple."""
    atype = action[0]
    if atype == "assign":
        if len(action) == 4:
            return f"assign({action[1]},{action[2]},{action[3]})"
        return f"assign({','.join(str(x) for x in action[1:])})"
    elif atype == "schedule":
        return f"sched(+{action[1]})"
    elif atype == "route":
        return f"route({action[1]})"
    return str(action)


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
