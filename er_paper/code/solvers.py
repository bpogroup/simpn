"""
solvers.py — Three solution methods for the SMDP induced by a BPMN+OPT model:

  1. Heuristic solvers  (FIFO, Shortest Processing Time, Random)
  2. Approximate solver (Tabular Q-Learning with SMDP-adjusted TD updates)
  3. Exact solver       (Value Iteration via Monte Carlo transition estimation)
"""

import random
import math
from collections import defaultdict


# ===========================================================================
# 1. HEURISTIC SOLVERS
# ===========================================================================

class FIFOPolicy:
    """
    First-In-First-Out: assign the longest-waiting patient to the first
    available resource (lexicographic by resource id).
    """
    def __call__(self, state, actions, env):
        waiting = env.model.get_waiting_cases()
        wait_times = {}
        for tok in waiting:
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            start = val["start"] if isinstance(val, dict) else val.start
            wait_times[pid] = env.model.problem.clock - start

        best = None
        best_wait = -1
        for (c_id, r_id) in actions:
            w = wait_times.get(c_id, 0)
            if w > best_wait or (w == best_wait and (best is None or r_id < best[1])):
                best = (c_id, r_id)
                best_wait = w
        return best


class ShortestProcessingTimePolicy:
    """
    Shortest Processing Time: pick the (patient, resource) pair whose
    expected processing time is smallest, using the midpoint of the
    uniform distribution from the processing-time rules.
    """
    def __init__(self, problem_spec):
        self.rules = {}
        for task in problem_spec["process"]["tasks"]:
            for rule in task["processing_time"]["rules"]:
                key = tuple(sorted(rule["condition"].items()))
                dist = rule["distribution"]
                if dist["type"] == "uniform":
                    self.rules[key] = (dist["low"] + dist["high"]) / 2.0
                elif dist["type"] == "exponential":
                    self.rules[key] = dist["mean"]
                elif dist["type"] == "constant":
                    self.rules[key] = dist["value"]
                else:
                    self.rules[key] = float("inf")

    def _expected_ptime(self, case_val, resource_val):
        c_type = case_val["type"] if isinstance(case_val, dict) else case_val.type
        r_id = resource_val["id"] if isinstance(resource_val, dict) else resource_val.id
        key = tuple(sorted([("case.type", c_type), ("resource.id", r_id)]))
        return self.rules.get(key, float("inf"))

    def __call__(self, state, actions, env):
        waiting_map = {}
        for tok in env.model.get_waiting_cases():
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            waiting_map[pid] = val

        idle_map = {}
        for tok in env.model.get_idle_resources():
            val = tok.value
            rid = val["id"] if isinstance(val, dict) else val.id
            idle_map[rid] = val

        best = None
        best_pt = float("inf")
        for (c_id, r_id) in actions:
            pt = self._expected_ptime(waiting_map[c_id], idle_map[r_id])
            if pt < best_pt:
                best = (c_id, r_id)
                best_pt = pt
        return best


class RandomPolicy:
    """Uniformly random action selection."""
    def __call__(self, state, actions, env):
        return random.choice(actions)


# ===========================================================================
# 2. APPROXIMATE SOLVER — Tabular Q-Learning
# ===========================================================================

class QLearningAgent:
    """
    Tabular Q-Learning for SMDP.

    Uses SMDP-adjusted TD update:
      Q(s,a) <- Q(s,a) + alpha * [r + gamma^tau * max_a' Q(s',a') - Q(s,a)]

    where tau is the holding time (time between decision epochs).

    State representation: abstract feature tuple from the environment.
    Action: (case_id, resource_id)

    Since case/resource IDs change across episodes, we use abstract features:
      state  -> (n_waiting, n_idle, tuple of waiting types)
      action -> (case_type, resource_id)
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

    def _abstract_state(self, env):
        """Convert raw state to an abstract feature tuple."""
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

    def _abstract_action(self, action, env):
        """Convert (case_id, resource_id) to (case_type, resource_id)."""
        c_id, r_id = action
        for tok in env.model.get_waiting_cases():
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            if pid == c_id:
                c_type = val["type"] if isinstance(val, dict) else val.type
                return (c_type, r_id)
        return action

    def _resolve_abstract_to_concrete(self, abs_action, actions, env):
        """
        Given an abstract action (case_type, resource_id) and the list of
        concrete feasible actions, return the concrete action that assigns
        the EARLIEST-waiting patient of that type (FIFO within type).
        """
        c_type, r_id = abs_action
        waiting = env.model.get_waiting_cases()
        arrival_times = {}
        for tok in waiting:
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            ptype = val["type"] if isinstance(val, dict) else val.type
            start = val["start"] if isinstance(val, dict) else val.start
            arrival_times[pid] = (ptype, start)

        best_concrete = None
        earliest_start = float("inf")
        for (cid, rid) in actions:
            if rid != r_id:
                continue
            if cid in arrival_times and arrival_times[cid][0] == c_type:
                if arrival_times[cid][1] < earliest_start:
                    earliest_start = arrival_times[cid][1]
                    best_concrete = (cid, rid)
        return best_concrete

    def _get_q(self, state, action):
        return self.q_table[(state, action)]

    def _max_q(self, state, actions, env):
        if not actions:
            return 0.0
        seen = set()
        max_val = -float("inf")
        for a in actions:
            abs_a = self._abstract_action(a, env)
            if abs_a not in seen:
                seen.add(abs_a)
                max_val = max(max_val, self._get_q(state, abs_a))
        return max_val

    def select_action(self, state, actions, env):
        """Epsilon-greedy action selection with FIFO tiebreaking."""
        if random.random() < self.epsilon:
            return random.choice(actions)
        abs_state = self._abstract_state(env)
        best_val = -float("inf")
        best_abs_actions = []
        seen = set()
        for a in actions:
            abs_a = self._abstract_action(a, env)
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
        concrete = self._resolve_abstract_to_concrete(chosen_abs, actions, env)
        return concrete if concrete else random.choice(actions)

    def train(self, env, n_episodes=500, verbose=True):
        """Train the Q-learning agent over multiple episodes."""
        rewards_history = []
        for ep in range(n_episodes):
            state = env.reset(seed=ep)
            abs_state = self._abstract_state(env)
            prev_time = env.model.problem.clock
            episode_reward = 0.0

            while not env.done:
                actions = env.get_actions()
                if not actions:
                    break

                action = self.select_action(state, actions, env)
                abs_action = self._abstract_action(action, env)

                next_state, reward, done, info = env.step(action)
                abs_next_state = self._abstract_state(env)
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

            if episode_reward == 0.0 and env.model:
                episode_reward = env.model.compute_reward()

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
        """Return a greedy policy function with FIFO tiebreaking."""
        agent = self
        def policy_fn(state, actions, env):
            abs_state = agent._abstract_state(env)
            best_val = -float("inf")
            best_abs_actions = []
            seen = set()
            for a in actions:
                abs_a = agent._abstract_action(a, env)
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
            concrete = agent._resolve_abstract_to_concrete(chosen_abs, actions, env)
            return concrete if concrete else random.choice(actions)
        return policy_fn


# ===========================================================================
# 3. EXACT SOLVER — Value Iteration with Monte Carlo Transition Estimation
# ===========================================================================

class ValueIterationSolver:
    """
    Exact solver using value iteration over discretized/enumerated states.

    For continuous-state SMDPs, we approximate by:
    1. Running many simulation episodes with an exploratory policy to discover
       reachable abstract states and collect transition samples.
    2. Building empirical transition probabilities P(s'|s,a) and expected rewards R(s,a).
    3. Running value iteration until convergence.

    This is "exact" in the sense of solving the discretized problem to optimality
    (up to the abstraction granularity), as opposed to the RL agent which learns
    online without a model.
    """

    def __init__(self, problem_spec, gamma=1.0, theta=1e-6, max_iter=1000):
        self.problem_spec = problem_spec
        self.gamma = gamma
        self.theta = theta
        self.max_iter = max_iter
        self.V = defaultdict(float)
        self.transitions = defaultdict(lambda: defaultdict(list))
        self.state_actions = defaultdict(set)

    def _abstract_state(self, env):
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

    def _abstract_action(self, action, env):
        c_id, r_id = action
        for tok in env.model.get_waiting_cases():
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            if pid == c_id:
                c_type = val["type"] if isinstance(val, dict) else val.type
                return (c_type, r_id)
        return action

    def _resolve_abstract_to_concrete(self, abs_action, actions, env):
        """FIFO within-type tiebreaking for abstract actions."""
        c_type, r_id = abs_action
        waiting = env.model.get_waiting_cases()
        arrival_times = {}
        for tok in waiting:
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            ptype = val["type"] if isinstance(val, dict) else val.type
            start = val["start"] if isinstance(val, dict) else val.start
            arrival_times[pid] = (ptype, start)

        best_concrete = None
        earliest_start = float("inf")
        for (cid, rid) in actions:
            if rid != r_id:
                continue
            if cid in arrival_times and arrival_times[cid][0] == c_type:
                if arrival_times[cid][1] < earliest_start:
                    earliest_start = arrival_times[cid][1]
                    best_concrete = (cid, rid)
        return best_concrete

    def collect_samples(self, env, n_episodes=300, verbose=True):
        """
        Run exploratory episodes to collect (s, a, r, s', tau) transition samples.
        Uses random abstract-action selection with FIFO tiebreaking within type.
        """
        if verbose:
            print(f"  Collecting transition samples over {n_episodes} episodes...")

        for ep in range(n_episodes):
            env.reset(seed=ep)
            abs_state = self._abstract_state(env)
            prev_time = env.model.problem.clock

            while not env.done:
                actions = env.get_actions()
                if not actions:
                    break

                abs_actions_available = set()
                for a in actions:
                    abs_actions_available.add(self._abstract_action(a, env))
                chosen_abs = random.choice(list(abs_actions_available))
                action = self._resolve_abstract_to_concrete(chosen_abs, actions, env)
                if action is None:
                    action = random.choice(actions)

                abs_action = self._abstract_action(action, env)
                self.state_actions[abs_state].add(abs_action)

                next_raw, reward, done, info = env.step(action)
                abs_next = self._abstract_state(env)
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
        """Run value iteration to convergence."""
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
        """Return the greedy policy with FIFO tiebreaking within type."""
        solver = self
        def policy_fn(state, actions, env):
            abs_state = solver._abstract_state(env)
            best_val = -float("inf")
            best_abs_actions = []
            seen = set()
            for a in actions:
                abs_a = solver._abstract_action(a, env)
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
                concrete = solver._resolve_abstract_to_concrete(chosen_abs, actions, env)
                if concrete:
                    return concrete
            return random.choice(actions)
        return policy_fn
