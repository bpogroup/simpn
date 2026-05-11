"""
solvers.py — Solution methods for the SMDP induced by a BPMN+OPT model.

All solvers work with typed actions:
  ("assign", task_name, case_id, resource_id)
  ("schedule", case_id, offset)
  ("route", case_id, route_value)

Abstraction is delegated to the environment:
  env.abstract_state()
  env.abstract_action(action)
  env.resolve_abstract_action(abs_action, actions)

Solvers:
  1. Heuristic  — Composable per-decision-type rules
  2. Approximate — Tabular Q-Learning (SMDP-adjusted TD updates)
  3. Exact       — Value Iteration via Monte Carlo transition estimation
"""

import random
import math
from collections import defaultdict
from bpmnopt_builder import match_condition


# ===========================================================================
# 1. HEURISTIC SOLVERS — composable per decision type
# ===========================================================================

# --- Scheduling sub-policies ---

def schedule_immediate(actions, env):
    """Always schedule immediately (offset=0)."""
    immediates = [a for a in actions if a[2] == 0]
    return immediates[0] if immediates else min(actions, key=lambda a: a[2])


def schedule_spread(actions, env):
    """Pick the largest offset to distribute load over time."""
    return max(actions, key=lambda a: a[2])


def schedule_queue_aware(actions, env, threshold=3):
    """If the downstream queue is short, schedule now; otherwise delay."""
    sched_cfg = env.spec.get("process", {}).get("scheduling", {})
    out_flow = sched_cfg.get("outgoing_flow", "")
    queue_len = 0
    if out_flow and out_flow in env.model.flows:
        queue_len = len([t for t in env.model.flows[out_flow].marking
                         if t.time <= env.model.problem.clock + 1e-9])
    if queue_len >= threshold:
        return max(actions, key=lambda a: a[2])
    return schedule_immediate(actions, env)


# --- Routing sub-policies ---

def route_always_standard(actions, env):
    """Always choose standard infusion (minimizes chair time)."""
    standards = [a for a in actions if a[2] == "standard"]
    return standards[0] if standards else actions[0]


def route_always_intensive(actions, env):
    """Always choose intensive infusion."""
    intensives = [a for a in actions if a[2] == "intensive"]
    return intensives[0] if intensives else actions[0]


def route_by_measurements(actions, env, threshold=0.5):
    """Route by patient measurements: high → intensive, low → standard."""
    c_id = actions[0][1]
    meas = _lookup_patient_attr(env, c_id, "measurements")
    if meas is not None and meas > threshold:
        return route_always_intensive(actions, env)
    return route_always_standard(actions, env)


def route_shortest_queue(actions, env):
    """Route to the infusion queue with fewer waiting patients."""
    queue_counts = {}
    for a in actions:
        route_val = a[2]
        flow_name = f"waiting_{route_val}_infusion"
        cnt = 0
        if flow_name in env.model.flows:
            cnt = len([t for t in env.model.flows[flow_name].marking
                       if t.time <= env.model.problem.clock + 1e-9])
        queue_counts[route_val] = cnt
    best_route = min(queue_counts, key=queue_counts.get)
    candidates = [a for a in actions if a[2] == best_route]
    return candidates[0] if candidates else actions[0]


# --- Assignment sub-policies ---

def assign_fifo(actions, env):
    """Longest-waiting patient first, tiebreak by resource id."""
    best = None
    best_wait = -1
    for a in actions:
        _, task_name, c_id, r_id = a
        start = env._lookup_start_time(c_id)
        wait = env.model.problem.clock - start
        if wait > best_wait or (wait == best_wait and (best is None or r_id < best[3])):
            best = a
            best_wait = wait
    return best


def assign_spt(actions, env, task_rules=None):
    """Shortest expected processing time pair."""
    if task_rules is None:
        return assign_fifo(actions, env)
    best = None
    best_pt = float("inf")
    for a in actions:
        _, task_name, c_id, r_id = a
        r_val = _lookup_resource_val(env, task_name, r_id)
        c_val = _lookup_case_val(env, task_name, c_id)
        pt = _expected_ptime(task_rules, task_name, r_val, c_val)
        if pt < best_pt or (pt == best_pt and (best is None or r_id < best[3])):
            best_pt = pt
            best = a
    return best


def assign_random(actions, env):
    """Uniformly random assignment."""
    return random.choice(actions)


# --- Helper functions for heuristics ---

def _lookup_patient_attr(env, case_id, attr):
    """Find a patient attribute by scanning flows."""
    for flow in env.model.flows.values():
        for tok in flow.marking:
            v = tok.value
            cid = v["id"] if isinstance(v, dict) else getattr(v, "id", None)
            if cid == case_id:
                if isinstance(v, dict):
                    return v.get(attr)
                return getattr(v, attr, None)
    return None


def _lookup_case_val(env, task_name, case_id):
    t_spec = env.model.tasks_meta[task_name]
    in_flow = env.model.flows[t_spec["incoming_flow"]]
    for tok in in_flow.marking:
        v = tok.value
        if (v["id"] if isinstance(v, dict) else v.id) == case_id:
            return v
    return {}


def _lookup_resource_val(env, task_name, resource_id):
    t_spec = env.model.tasks_meta[task_name]
    res_lane = env.model.lanes[t_spec["resource_lane"]]
    for tok in res_lane.marking:
        v = tok.value
        if (v["id"] if isinstance(v, dict) else v.id) == resource_id:
            return v
    return {}


def _expected_ptime(task_rules, task_name, resource_val, case_val):
    rules = task_rules.get(task_name, [])
    for rule in rules:
        if match_condition(rule["condition"], resource_val, case_val):
            d = rule["distribution"]
            if d["type"] == "uniform":
                return (d["low"] + d["high"]) / 2.0
            elif d["type"] == "exponential":
                return d["mean"]
            elif d["type"] == "constant":
                return d["value"]
    return float("inf")


# --- Composite heuristic policy ---

class CompositePolicy:
    """
    Composable heuristic: plug in a sub-policy for each decision type.

    Parameters:
        schedule_fn : callable(actions, env) -> action
        route_fn    : callable(actions, env) -> action
        assign_fn   : callable(actions, env) -> action
        name        : human-readable label
    """
    def __init__(self, schedule_fn=None, route_fn=None, assign_fn=None, name="Composite"):
        self.schedule_fn = schedule_fn or schedule_immediate
        self.route_fn = route_fn or route_always_standard
        self.assign_fn = assign_fn or assign_fifo
        self.name = name

    def __call__(self, state, actions, env):
        schedule_acts = [a for a in actions if a[0] == "schedule"]
        if schedule_acts:
            return self.schedule_fn(schedule_acts, env)

        route_acts = [a for a in actions if a[0] == "route"]
        if route_acts:
            return self.route_fn(route_acts, env)

        assign_acts = [a for a in actions if a[0] == "assign"]
        if assign_acts:
            return self.assign_fn(assign_acts, env)

        return actions[0]


def build_heuristics(problem_spec):
    """
    Build a named dict of composite heuristics for a given problem spec.
    Returns: dict[str, CompositePolicy]
    """
    task_rules = {}
    for task in problem_spec.get("process", {}).get("tasks", []):
        task_rules[task["name"]] = task["processing_time"]["rules"]
    spt_fn = lambda actions, env: assign_spt(actions, env, task_rules=task_rules)

    has_scheduling = any(
        d["type"] == "scheduling" for d in problem_spec.get("decision", {}).get("types", []))
    has_routing = any(
        d["type"] == "routing" for d in problem_spec.get("decision", {}).get("types", []))

    heuristics = {}

    heuristics["FIFO"] = CompositePolicy(
        schedule_fn=schedule_immediate,
        route_fn=route_always_standard,
        assign_fn=assign_fifo,
        name="FIFO",
    )

    heuristics["SPT"] = CompositePolicy(
        schedule_fn=schedule_immediate,
        route_fn=route_always_standard,
        assign_fn=spt_fn,
        name="SPT",
    )

    if has_routing:
        heuristics["Clinical"] = CompositePolicy(
            schedule_fn=schedule_immediate,
            route_fn=route_by_measurements,
            assign_fn=spt_fn,
            name="Clinical",
        )

        heuristics["ShortQ"] = CompositePolicy(
            schedule_fn=schedule_immediate,
            route_fn=route_shortest_queue,
            assign_fn=spt_fn,
            name="ShortQ",
        )

    if has_scheduling:
        heuristics["Stagger+SPT"] = CompositePolicy(
            schedule_fn=schedule_queue_aware,
            route_fn=route_by_measurements if has_routing else route_always_standard,
            assign_fn=spt_fn,
            name="Stagger+SPT",
        )

    heuristics["Random"] = CompositePolicy(
        schedule_fn=schedule_immediate,
        route_fn=lambda acts, env: random.choice(acts),
        assign_fn=assign_random,
        name="Random",
    )

    return heuristics


# Backward-compatible wrappers
FIFOPolicy = lambda: CompositePolicy(
    schedule_fn=schedule_immediate,
    route_fn=route_always_standard,
    assign_fn=assign_fifo,
    name="FIFO",
)

class ShortestProcessingTimePolicy:
    def __init__(self, problem_spec):
        self._task_rules = {}
        for task in problem_spec["process"]["tasks"]:
            self._task_rules[task["name"]] = task["processing_time"]["rules"]
        spt_fn = lambda actions, env: assign_spt(actions, env, task_rules=self._task_rules)
        self._policy = CompositePolicy(
            schedule_fn=schedule_immediate,
            route_fn=route_always_standard,
            assign_fn=spt_fn,
            name="SPT",
        )

    def __call__(self, state, actions, env):
        return self._policy(state, actions, env)


class RandomPolicy:
    def __call__(self, state, actions, env):
        schedule_acts = [a for a in actions if a[0] == "schedule"]
        if schedule_acts:
            return schedule_immediate(schedule_acts, env)
        return random.choice(actions)


# ===========================================================================
# 2. APPROXIMATE SOLVER — Tabular Q-Learning
# ===========================================================================

class QLearningAgent:
    """
    Tabular Q-Learning for SMDP with typed actions.

    Delegates state/action abstraction to the environment.
    SMDP-adjusted TD update:
      Q(s,a) <- Q(s,a) + alpha * [r + gamma^tau * max_a' Q(s',a') - Q(s,a)]
    """

    def __init__(self, problem_spec, alpha=0.1, gamma=1.0, epsilon=0.3,
                 epsilon_decay=0.999, min_epsilon=0.01):
        self.problem_spec = problem_spec
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.q_table = defaultdict(float)

    def _get_q(self, state, action):
        return self.q_table[(state, action)]

    def _max_q(self, state, actions, env):
        if not actions:
            return 0.0
        seen = set()
        max_val = -float("inf")
        for a in actions:
            abs_a = env.abstract_action(a)
            if abs_a not in seen:
                seen.add(abs_a)
                max_val = max(max_val, self._get_q(state, abs_a))
        return max_val

    def select_action(self, state, actions, env):
        if random.random() < self.epsilon:
            # For exploration, schedule immediately to avoid backlogs
            schedule_acts = [a for a in actions if a[0] == "schedule"]
            if schedule_acts and random.random() < 0.7:
                immediates = [a for a in schedule_acts if a[2] == 0]
                return immediates[0] if immediates else schedule_acts[0]
            return random.choice(actions)

        abs_state = env.abstract_state()
        best_val = -float("inf")
        best_abs_actions = []
        seen = set()
        for a in actions:
            abs_a = env.abstract_action(a)
            if abs_a in seen:
                continue
            seen.add(abs_a)
            q = self._get_q(abs_state, abs_a)
            if q > best_val:
                best_val = q
                best_abs_actions = [abs_a]
            elif q == best_val:
                best_abs_actions.append(abs_a)
        chosen_abs = random.choice(best_abs_actions)
        concrete = env.resolve_abstract_action(chosen_abs, actions)
        return concrete if concrete else random.choice(actions)

    def train(self, env, n_episodes=500, verbose=True):
        rewards_history = []
        for ep in range(n_episodes):
            state = env.reset(seed=ep)
            abs_state = env.abstract_state()
            prev_time = env.model.problem.clock
            episode_reward = 0.0

            while not env.done:
                actions = env.get_actions()
                if not actions:
                    break

                action = self.select_action(state, actions, env)
                abs_action = env.abstract_action(action)

                next_state, reward, done, info = env.step(action)
                abs_next_state = env.abstract_state()
                current_time = env.model.problem.clock

                tau = current_time - prev_time
                discount_factor = self.gamma ** tau if tau > 0 else 1.0

                next_actions = env.get_actions()
                max_next_q = self._max_q(abs_next_state, next_actions, env) if next_actions else 0.0

                td_target = reward + discount_factor * max_next_q
                td_error = td_target - self._get_q(abs_state, abs_action)
                self.q_table[(abs_state, abs_action)] += self.alpha * td_error

                if not info.get("same_time", False):
                    prev_time = current_time

                abs_state = abs_next_state
                state = next_state
                episode_reward += reward

            rewards_history.append(episode_reward)
            self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

            if verbose and (ep + 1) % 50 == 0:
                avg = sum(rewards_history[-50:]) / min(50, len(rewards_history))
                print(f"  Episode {ep+1}/{n_episodes} | "
                      f"avg reward (last 50): {avg:.2f} | "
                      f"epsilon: {self.epsilon:.4f} | "
                      f"Q-table size: {len(self.q_table)}")

        return rewards_history

    def policy(self):
        agent = self
        def policy_fn(state, actions, env):
            abs_state = env.abstract_state()
            best_val = -float("inf")
            best_abs_actions = []
            seen = set()
            for a in actions:
                abs_a = env.abstract_action(a)
                if abs_a in seen:
                    continue
                seen.add(abs_a)
                q = agent._get_q(abs_state, abs_a)
                if q > best_val:
                    best_val = q
                    best_abs_actions = [abs_a]
                elif q == best_val:
                    best_abs_actions.append(abs_a)
            chosen_abs = random.choice(best_abs_actions)
            concrete = env.resolve_abstract_action(chosen_abs, actions)
            return concrete if concrete else random.choice(actions)
        return policy_fn


# ===========================================================================
# 3. EXACT SOLVER — Value Iteration with Monte Carlo Transition Estimation
# ===========================================================================

class ValueIterationSolver:
    """
    Value iteration over discretized states discovered by Monte Carlo exploration.
    Delegates abstraction to the environment.
    """

    def __init__(self, problem_spec, gamma=1.0, theta=1e-6, max_iter=1000):
        self.problem_spec = problem_spec
        self.gamma = gamma
        self.theta = theta
        self.max_iter = max_iter
        self.V = defaultdict(float)
        self.transitions = defaultdict(lambda: defaultdict(list))
        self.state_actions = defaultdict(set)

    def collect_samples(self, env, n_episodes=300, verbose=True):
        if verbose:
            print(f"  Collecting transition samples over {n_episodes} episodes...")

        for ep in range(n_episodes):
            env.reset(seed=ep)
            abs_state = env.abstract_state()
            prev_time = env.model.problem.clock

            while not env.done:
                actions = env.get_actions()
                if not actions:
                    break

                abs_actions_available = set()
                for a in actions:
                    abs_actions_available.add(env.abstract_action(a))
                chosen_abs = random.choice(sorted(abs_actions_available))
                action = env.resolve_abstract_action(chosen_abs, actions)
                if action is None:
                    action = random.choice(actions)

                abs_action = env.abstract_action(action)
                self.state_actions[abs_state].add(abs_action)

                next_raw, reward, done, info = env.step(action)
                abs_next = env.abstract_state()
                current_time = env.model.problem.clock
                tau = current_time - prev_time

                self.transitions[(abs_state, abs_action)][abs_next].append((reward, tau))

                if not info.get("same_time", False):
                    prev_time = current_time
                abs_state = abs_next

        if verbose:
            print(f"  Discovered {len(self.state_actions)} abstract states, "
                  f"{sum(len(a) for a in self.state_actions.values())} state-action pairs.")

    def solve(self, verbose=True):
        if verbose:
            print(f"  Running value iteration (max {self.max_iter} iterations, theta={self.theta})...")

        for iteration in range(self.max_iter):
            delta = 0.0
            for state, actions in self.state_actions.items():
                if not actions:
                    continue
                old_v = self.V[state]
                best_q = -float("inf")

                for action in actions:
                    trans = self.transitions[(state, action)]
                    if not trans:
                        continue
                    total_samples = sum(len(samples) for samples in trans.values())
                    q_val = 0.0
                    for next_state, samples in trans.items():
                        prob = len(samples) / total_samples
                        avg_reward = sum(r for r, t in samples) / len(samples)
                        avg_tau = sum(t for r, t in samples) / len(samples)
                        discount = self.gamma ** avg_tau if avg_tau > 0 else 1.0
                        q_val += prob * (avg_reward + discount * self.V[next_state])
                    best_q = max(best_q, q_val)

                if best_q > -float("inf"):
                    self.V[state] = best_q
                    delta = max(delta, abs(old_v - self.V[state]))

            if verbose and (iteration + 1) % 20 == 0:
                print(f"    Iteration {iteration+1}: delta={delta:.6f}")

            if delta < self.theta:
                if verbose:
                    print(f"  Converged after {iteration+1} iterations (delta={delta:.8f}).")
                break

    def policy(self):
        solver = self
        def policy_fn(state, actions, env):
            abs_state = env.abstract_state()
            best_val = -float("inf")
            best_abs_actions = []
            seen = set()
            for a in actions:
                abs_a = env.abstract_action(a)
                if abs_a in seen:
                    continue
                seen.add(abs_a)
                trans = solver.transitions.get((abs_state, abs_a), {})
                if not trans:
                    best_abs_actions.append(abs_a)
                    continue
                total_samples = sum(len(s) for s in trans.values())
                q_val = 0.0
                for ns, samples in trans.items():
                    prob = len(samples) / total_samples
                    avg_r = sum(r for r, t in samples) / len(samples)
                    avg_tau = sum(t for r, t in samples) / len(samples)
                    disc = solver.gamma ** avg_tau if avg_tau > 0 else 1.0
                    q_val += prob * (avg_r + disc * solver.V[ns])
                if q_val > best_val:
                    best_val = q_val
                    best_abs_actions = [abs_a]
                elif q_val == best_val:
                    best_abs_actions.append(abs_a)
            chosen_abs = random.choice(best_abs_actions) if best_abs_actions else None
            if chosen_abs:
                concrete = env.resolve_abstract_action(chosen_abs, actions)
                if concrete:
                    return concrete
            return random.choice(actions)
        return policy_fn
