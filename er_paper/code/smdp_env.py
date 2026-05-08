"""
smdp_env.py — SMDP Environment wrapping a BPMNOPTModel.

Provides a gym-like interface: reset(), step(action), get_actions(), get_state().
Implements the sequential decision semantics from the BPMN+OPT paper:
  1. At a decision epoch, one assignment X_(p,o)=1 is made (the action).
  2. The corresponding task guard fires, consuming the patient and oncologist.
  3. The decision moment is re-evaluated: if another unassigned pair exists,
     a new epoch occurs at the same simulation time.
  4. Otherwise, the simulation evolves until the next state-changing event
     (task completion or new arrival) that triggers a new decision moment.
"""

import json
import random
from copy import deepcopy
from bpmnopt_builder import BPMNOPTModel, load_problem


class SMDPEnv:
    """
    SMDP environment for BPMN+OPT resource-assignment problems.

    States are decision epochs. Actions are (case_id, resource_id) assignments.
    Between decision epochs, the SimPN simulation advances autonomously.
    """

    def __init__(self, json_path=None, spec_dict=None, seed=None):
        if json_path is not None:
            with open(json_path, "r") as f:
                self.spec = json.load(f)
        elif spec_dict is not None:
            self.spec = spec_dict
        else:
            raise ValueError("Must provide json_path or spec_dict")

        self.horizon = self.spec["smdp"]["horizon"]
        self.discount = self.spec["smdp"]["discount"]
        self.seed = seed
        self.model = None
        self.done = False
        self.total_reward = 0.0

    def reset(self, seed=None):
        """Reset the environment to the initial state and advance to the first decision epoch."""
        if seed is not None:
            self.seed = seed
        if self.seed is not None:
            random.seed(self.seed)

        self.model = BPMNOPTModel(self.spec)
        self.done = False
        self.total_reward = 0.0

        self._advance_to_decision_epoch_with_cost()
        return self.get_state()

    def get_state(self):
        """Return a hashable state snapshot for tabular methods."""
        if self.model is None:
            return None
        return self.model.get_state_snapshot()

    def get_state_info(self):
        """Return a human-readable dict describing the current state."""
        if self.model is None:
            return {}
        waiting = []
        for tok in self.model.get_waiting_cases():
            val = tok.value
            waiting.append({
                "id": val["id"] if isinstance(val, dict) else val.id,
                "type": val["type"] if isinstance(val, dict) else val.type,
            })
        idle = []
        for tok in self.model.get_idle_resources():
            val = tok.value
            idle.append(val["id"] if isinstance(val, dict) else val.id)
        return {
            "time": self.model.problem.clock,
            "waiting": waiting,
            "idle_resources": idle,
            "assignments": dict(self.model.assignments),
            "n_completed": len(self.model.get_completed_cases()),
        }

    def get_actions(self):
        """Return list of feasible actions (case_id, resource_id) in the current state."""
        if self.done or self.model is None:
            return []
        return self.model.get_feasible_actions()

    def _count_patients_in_system(self):
        """Count patients currently in the system (waiting + being processed)."""
        n = 0
        for flow in self.model.flows.values():
            n += len(flow.marking)
        for task_name in self.model.tasks_meta:
            busy_var_name = task_name + "_busy"
            if busy_var_name in self.model.problem.id2node:
                n += len(self.model.problem.id2node[busy_var_name].marking)
        return n

    def step(self, action):
        """
        Execute one SMDP action: assign X_(case_id, resource_id) = 1.

        Under sequential semantics:
        - Apply the assignment
        - Fire the task start (SimPN step picks it up via the guard)
        - Re-evaluate the decision moment
        - If another feasible pair exists -> return new state (same time, no sim advance)
        - If no feasible pair -> advance simulation to next decision epoch

        Step reward uses the exact integral of n(t) over the holding interval,
        computed event-by-event during simulation advance:
          reward = -integral_{t_k}^{t_{k+1}} n(t) dt
        This equals the total cycle time contribution of this interval.

        Returns: (next_state, reward, done, info)
        """
        if self.done:
            return self.get_state(), 0.0, True, {"reason": "already_done"}

        case_id, resource_id = action
        t_before = self.model.problem.clock
        n_before = self._count_patients_in_system()

        self.model.apply_action(case_id, resource_id)
        self._fire_pending_assignments()

        actions_after = self.model.get_feasible_actions()
        if actions_after:
            return self.get_state(), 0.0, False, {"same_time": True}

        self.model.clear_assignments()
        holding_cost = self._advance_to_decision_epoch_with_cost(
            t_start=t_before, n_start=n_before
        )

        step_reward = -holding_cost

        if self.done:
            self.total_reward += step_reward
            return self.get_state(), step_reward, True, {"reason": "horizon"}

        self.total_reward += step_reward
        return self.get_state(), step_reward, False, {"same_time": False}

    def _fire_pending_assignments(self):
        """
        Fire SimPN steps to process any task starts enabled by current assignments.
        Only fires bindings at the ORIGINAL clock time. Restores the clock if
        bindings() advanced it as a side effect without any binding being available.
        """
        problem = self.model.problem
        current_time = problem.clock
        max_steps = 100
        for _ in range(max_steps):
            saved_clock = problem.clock
            bindings = problem.bindings()
            current_time_bindings = [b for b in bindings if b[1] <= current_time]
            if not current_time_bindings:
                problem.clock = saved_clock
                break
            binding = problem.binding_priority(current_time_bindings)
            problem.fire(binding)

    def _advance_to_decision_epoch_with_cost(self, t_start=None, n_start=None):
        """
        Advance the SimPN simulation until a decision moment is reached or the horizon.
        Tracks the exact integral of n(t) over the interval by sampling n at each event.
        Returns the accumulated holding cost.
        """
        problem = self.model.problem
        max_steps = 100000
        total_cost = 0.0
        prev_time = t_start if t_start is not None else problem.clock
        prev_n = n_start if n_start is not None else self._count_patients_in_system()

        for _ in range(max_steps):
            if problem.clock > self.horizon:
                total_cost += prev_n * (self.horizon - prev_time)
                self.done = True
                return total_cost

            actions = self.model.get_feasible_actions()
            if actions:
                dt = problem.clock - prev_time
                total_cost += prev_n * dt
                return total_cost

            bindings = problem.bindings()
            if not bindings:
                self.done = True
                return total_cost

            binding = problem.binding_priority(bindings)

            old_clock = problem.clock
            problem.fire(binding)
            new_clock = problem.clock

            dt = new_clock - prev_time
            total_cost += prev_n * dt
            prev_time = new_clock
            prev_n = self._count_patients_in_system()

            if problem.clock > self.horizon:
                self.done = True
                return total_cost

        return total_cost

    def run_with_policy(self, policy_fn, seed=None, verbose=False):
        """
        Run a complete episode using the given policy function.
        policy_fn(state, actions, env) -> action

        Returns: (total_reward, info_dict)
        """
        state = self.reset(seed=seed)
        total_reward = 0.0
        n_decisions = 0

        while not self.done:
            actions = self.get_actions()
            if not actions:
                break
            action = policy_fn(state, actions, self)
            state, reward, done, info = self.step(action)
            total_reward += reward
            n_decisions += 1
            if verbose and not info.get("same_time", False):
                si = self.get_state_info()
                print(f"  t={si['time']:.2f} | waiting={len(si['waiting'])} | "
                      f"idle={len(si['idle_resources'])} | completed={si['n_completed']}")

        return total_reward, {
            "n_decisions": n_decisions,
            "final_time": self.model.problem.clock if self.model else 0,
            "n_completed": len(self.model.get_completed_cases()) if self.model else 0,
            "total_cycle_time": self.model.compute_total_cycle_time() if self.model else 0,
        }
