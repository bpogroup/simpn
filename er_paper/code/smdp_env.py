"""
smdp_env.py — Unified SMDP Environment wrapping a BPMNOPTModel.

Provides a gym-like interface: reset(), step(action), get_actions(), get_state().
Implements sequential decision semantics for all decision types:
  - Scheduling: assign appointment times
  - Assignment: assign resources to patients at controlled tasks
  - Routing: choose among alternative paths

Actions are typed tuples:
  ("assign", task_name, case_id, resource_id)
  ("schedule", case_id, offset)
  ("route", case_id, route_value)

Abstraction levels for state/action:
  Level 0 ("counts"):       queue lengths + resource counts (most abstract)
  Level 1 ("resource_ids"):  queue lengths + idle resource IDs (default)
  Level 2 ("full_cpn"):      per-token patient attributes + idle resource IDs
"""

import json
import random
from bpmnopt_builder import BPMNOPTModel

ABSTRACTION_LEVELS = {0: "counts", 1: "resource_ids", 2: "patient_attrs", 3: "cpn_marking"}


class SMDPEnv:
    """
    Unified SMDP environment for BPMN+OPT models.
    Works for both simple (assignment-only) and complex (multi-decision) processes.

    abstraction_level controls state/action granularity:
      0 = counts only (queue lengths, resource counts)
      1 = resource IDs (queue lengths + which resources are idle)  [default]
      2 = full CPN marking (per-token attributes + resource IDs)
    """

    def __init__(self, json_path=None, spec_dict=None, seed=None,
                 abstraction_level=1):
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
        self.abstraction_level = abstraction_level

        # Detect model complexity for abstraction
        decision = self.spec.get("decision", {})
        self._is_simple = (
            "variables" in decision
            and decision["variables"].get("type") == "assignment"
        )

    def reset(self, seed=None):
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
        if self.model is None:
            return None
        return self.abstract_state()

    def get_actions(self):
        if self.done or self.model is None:
            return []
        return self.model.get_all_feasible_actions()

    def get_state_info(self):
        if self.model is None:
            return {}
        return {
            "time": self.model.problem.clock,
            "n_in_system": self.model.count_patients_in_system(),
            "n_completed": len(self.model.get_completed_cases()),
        }

    def step(self, action):
        if self.done:
            return self.get_state(), 0.0, True, {"reason": "already_done"}

        t_before = self.model.problem.clock
        n_before = self.model.count_patients_in_system()

        self.model.apply_action(action)
        self._fire_pending(t_before)

        actions_after = self.model.get_all_feasible_actions()
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

    def _fire_pending(self, original_time):
        problem = self.model.problem
        for _ in range(200):
            saved_clock = problem.clock
            bindings = problem.bindings()
            current_time_bindings = [b for b in bindings if b[1] <= original_time + 1e-9]
            if not current_time_bindings:
                problem.clock = saved_clock
                break
            binding = problem.binding_priority(current_time_bindings)
            problem.fire(binding)

    def _advance_to_decision_epoch_with_cost(self, t_start=None, n_start=None):
        problem = self.model.problem
        max_steps = 200000
        total_cost = 0.0
        prev_time = t_start if t_start is not None else problem.clock
        prev_n = n_start if n_start is not None else self.model.count_patients_in_system()

        for _ in range(max_steps):
            if problem.clock > self.horizon:
                total_cost += prev_n * (self.horizon - prev_time)
                self.done = True
                return total_cost

            actions = self.model.get_all_feasible_actions()
            if actions:
                dt = problem.clock - prev_time
                total_cost += prev_n * dt
                return total_cost

            bindings = problem.bindings()
            if not bindings:
                self.done = True
                return total_cost

            binding = problem.binding_priority(bindings)
            problem.fire(binding)
            new_clock = problem.clock

            dt = new_clock - prev_time
            total_cost += prev_n * dt
            prev_time = new_clock
            prev_n = self.model.count_patients_in_system()

            if problem.clock > self.horizon:
                self.done = True
                return total_cost

        return total_cost

    # ---- Abstraction methods (used by compiler and solvers) ----
    # L0: counts | L1: resource IDs | L2: patient attrs | L3: full CPN marking

    WAIT_BUCKETS = [0, 2, 5, 15, 30]  # boundaries in minutes

    def _available_tokens(self, marking):
        """Filter marking to only currently-available tokens."""
        clock = self.model.problem.clock
        return [tok for tok in marking if tok.time <= clock + 1e-9]

    def _wait_bucket(self, start_time):
        """Discretize waiting time into bucket index."""
        wait = self.model.problem.clock - start_time
        for i, boundary in enumerate(self.WAIT_BUCKETS):
            if wait < boundary:
                return i
        return len(self.WAIT_BUCKETS)

    def _clock_bucket(self):
        """Discretize clock into 10 equal-width bins over the horizon."""
        return min(9, int(self.model.problem.clock / max(1, self.horizon) * 10))

    def abstract_state(self):
        if self._is_simple:
            return self._abstract_state_simple()
        return self._abstract_state_complex()

    # ---- Simple model (Fig 2) state abstraction ----

    def _abstract_state_simple(self):
        dec = self.spec["decision"]["variables"]
        flow = self.model.flows[dec["case_flow"]]
        lane = self.model.lanes[dec["resource_lane"]]
        avail_flow = self._available_tokens(flow.marking)
        avail_lane = self._available_tokens(lane.marking)

        if self.abstraction_level == 0:
            type_counts = {}
            for tok in avail_flow:
                t = tok.value["type"] if isinstance(tok.value, dict) else tok.value.type
                type_counts[t] = type_counts.get(t, 0) + 1
            return (tuple(sorted(type_counts.items())), len(avail_lane))

        idle_ids = tuple(sorted(
            (tok.value["id"] if isinstance(tok.value, dict) else tok.value.id)
            for tok in avail_lane
        ))

        if self.abstraction_level <= 2:
            type_counts = {}
            for tok in avail_flow:
                t = tok.value["type"] if isinstance(tok.value, dict) else tok.value.type
                type_counts[t] = type_counts.get(t, 0) + 1
            return (tuple(sorted(type_counts.items())), idle_ids)

        # L3: per-patient (type, wait_bucket), idle IDs, clock bucket
        patients = []
        for tok in avail_flow:
            val = tok.value
            t = val["type"] if isinstance(val, dict) else val.type
            start = val["start"] if isinstance(val, dict) else val.start
            wb = self._wait_bucket(start)
            patients.append((t, wb))
        return (tuple(sorted(patients)), idle_ids, self._clock_bucket())

    # ---- Complex model (Fig 1) state abstraction ----

    def _abstract_state_complex(self):
        flow_part = self._flow_state()
        idle_part = self._idle_state()
        if self.abstraction_level >= 3:
            return (flow_part, idle_part, self._clock_bucket())
        return (flow_part, idle_part)

    def _flow_state(self):
        flow_info = {}
        for fname, flow in sorted(self.model.flows.items()):
            avail = self._available_tokens(flow.marking)
            if not avail:
                continue
            if self.abstraction_level >= 3:
                flow_info[fname] = self._extract_full_tokens(avail)
            elif self.abstraction_level == 2:
                flow_info[fname] = self._extract_patient_attrs(avail)
            else:
                flow_info[fname] = len(avail)
        for tname in sorted(self.model.tasks_meta.keys()):
            bvar = tname + "_busy"
            if bvar in self.model.problem.id2node:
                n = len(self.model.problem.id2node[bvar].marking)
                if n > 0:
                    flow_info["busy_" + tname] = n
        return tuple(sorted(flow_info.items()))

    def _idle_state(self):
        idle = {}
        for lname, lane in sorted(self.model.lanes.items()):
            avail = self._available_tokens(lane.marking)
            if self.abstraction_level == 0:
                idle[lname] = len(avail)
            else:
                idle[lname] = tuple(sorted(
                    (tok.value["id"] if isinstance(tok.value, dict) else tok.value.id)
                    for tok in avail
                ))
        return tuple(sorted(idle.items()))

    def _extract_patient_attrs(self, tokens):
        """L2: decision-relevant attributes (measurements, infusion_type)."""
        attrs = []
        for tok in tokens:
            val = tok.value
            if isinstance(val, dict):
                meas = val.get("measurements")
                itype = val.get("infusion_type")
            else:
                meas = getattr(val, "measurements", None)
                itype = getattr(val, "infusion_type", None)
            meas_bin = None if meas is None else (1 if meas > 0.5 else 0)
            attrs.append((meas_bin, itype))
        return tuple(sorted(attrs))

    def _extract_full_tokens(self, tokens):
        """L3: full CPN marking — per-token (wait_bucket, meas_bin, infusion_type)."""
        details = []
        for tok in tokens:
            val = tok.value
            if isinstance(val, dict):
                start = val.get("start", 0)
                meas = val.get("measurements")
                itype = val.get("infusion_type")
            else:
                start = getattr(val, "start", 0)
                meas = getattr(val, "measurements", None)
                itype = getattr(val, "infusion_type", None)
            wb = self._wait_bucket(start) if start else 0
            meas_bin = None if meas is None else (1 if meas > 0.5 else 0)
            details.append((wb, meas_bin, itype))
        return tuple(sorted(details))

    # ---- Action abstraction ----

    def abstract_action(self, action):
        atype = action[0]
        if atype == "assign":
            _, task_name, case_id, resource_id = action
            if self._is_simple:
                case_type = self._lookup_case_type(case_id, task_name)
                if self.abstraction_level == 0:
                    return ("assign", task_name, case_type)
                return ("assign", task_name, case_type, resource_id)
            if self.abstraction_level == 0:
                return ("assign", task_name)
            return ("assign", task_name, resource_id)
        elif atype == "schedule":
            return ("schedule", action[2])
        elif atype == "route":
            return ("route", action[2])
        return action

    # ---- Helpers ----

    def _lookup_case_type(self, case_id, task_name):
        t_spec = self.model.tasks_meta[task_name]
        flow = self.model.flows[t_spec["incoming_flow"]]
        for tok in flow.marking:
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            if pid == case_id:
                return val["type"] if isinstance(val, dict) else val.type
        return "unknown"

    def resolve_abstract_action(self, abs_action, concrete_actions):
        """Resolve abstract→concrete with FIFO tiebreaking."""
        atype = abs_action[0]

        if atype == "assign":
            if self._is_simple:
                if self.abstraction_level == 0:
                    _, task_name, case_type = abs_action
                    candidates = [
                        a for a in concrete_actions
                        if a[0] == "assign" and a[1] == task_name
                           and self._lookup_case_type(a[2], task_name) == case_type
                    ]
                else:
                    _, task_name, case_type, r_id = abs_action
                    candidates = [
                        a for a in concrete_actions
                        if a[0] == "assign" and a[1] == task_name and a[3] == r_id
                           and self._lookup_case_type(a[2], task_name) == case_type
                    ]
            else:
                if self.abstraction_level == 0:
                    _, task_name = abs_action
                    candidates = [
                        a for a in concrete_actions
                        if a[0] == "assign" and a[1] == task_name
                    ]
                else:
                    _, task_name, r_id = abs_action
                    candidates = [
                        a for a in concrete_actions
                        if a[0] == "assign" and a[1] == task_name and a[3] == r_id
                    ]
        elif atype == "schedule":
            _, offset = abs_action
            candidates = [a for a in concrete_actions if a[0] == "schedule" and a[2] == offset]
        elif atype == "route":
            _, route_val = abs_action
            candidates = [a for a in concrete_actions if a[0] == "route" and a[2] == route_val]
        else:
            candidates = [a for a in concrete_actions if a == abs_action]

        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        best = None
        earliest = float("inf")
        for ca in candidates:
            c_id = ca[1] if ca[0] in ("schedule", "route") else ca[2]
            start = self._lookup_start_time(c_id)
            if start < earliest:
                earliest = start
                best = ca
        return best if best else candidates[0]

    def _lookup_start_time(self, case_id):
        for flow in self.model.flows.values():
            for tok in flow.marking:
                val = tok.value
                pid = val["id"] if isinstance(val, dict) else val.id
                if pid == case_id:
                    return val["start"] if isinstance(val, dict) else val.start
        return float("inf")

    def run_with_policy(self, policy_fn, seed=None, verbose=False):
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
                print(f"  t={si['time']:.1f} | in_system={si['n_in_system']} | "
                      f"completed={si['n_completed']}")

        return total_reward, {
            "n_decisions": n_decisions,
            "final_time": self.model.problem.clock if self.model else 0,
            "n_completed": len(self.model.get_completed_cases()) if self.model else 0,
            "total_cycle_time": self.model.compute_total_cycle_time() if self.model else 0,
        }
