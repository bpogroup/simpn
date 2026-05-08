"""
bpmnopt_builder.py — Parses a BPMN+OPT JSON problem definition and constructs:
  1. A SimPN SimProblem (with BPMNFlow, BPMNLane, BPMNStartEvent, BPMNTask, BPMNEndEvent)
  2. Decision-variable state and task guards wired to those variables
  3. Metadata needed by the SMDP environment (flows, lanes, objectives, horizon, etc.)
"""

import json
import random
from simpn.simulator import SimProblem, SimToken, SimVar
from simpn.prototypes import BPMNFlow, BPMNLane, BPMNStartEvent, BPMNTask, BPMNEndEvent


def sample_distribution(dist_spec):
    """Sample a single value from a distribution specification dict."""
    dtype = dist_spec["type"]
    if dtype == "uniform":
        return random.uniform(dist_spec["low"], dist_spec["high"])
    elif dtype == "exponential":
        return random.expovariate(1.0 / dist_spec["mean"])
    elif dtype == "normal":
        return max(0, random.gauss(dist_spec["mean"], dist_spec["std"]))
    elif dtype == "constant":
        return dist_spec["value"]
    else:
        raise ValueError(f"Unknown distribution type: {dtype}")


def sample_interarrival(iat_spec):
    """Sample an interarrival time from a specification dict."""
    dist = iat_spec["distribution"]
    if dist == "exponential":
        return random.expovariate(1.0 / iat_spec["mean"])
    elif dist == "constant":
        return iat_spec["value"]
    else:
        raise ValueError(f"Unknown interarrival distribution: {dist}")


def match_condition(condition, resource_val, case_val):
    """Check whether a rule condition matches the given resource and case token values."""
    for key, expected in condition.items():
        if key.startswith("resource."):
            attr = key.split(".", 1)[1]
            actual = resource_val[attr] if isinstance(resource_val, dict) else getattr(resource_val, attr, None)
            if actual != expected:
                return False
        elif key.startswith("case."):
            attr = key.split(".", 1)[1]
            actual = case_val[attr] if isinstance(case_val, dict) else getattr(case_val, attr, None)
            if actual != expected:
                return False
    return True


def make_ptime_sampler(rules):
    """Build a function (resource_val, case_val) -> delay from processing-time rules."""
    def sampler(resource_val, case_val):
        for rule in rules:
            if match_condition(rule["condition"], resource_val, case_val):
                return sample_distribution(rule["distribution"])
        raise ValueError(f"No processing-time rule matched for resource={resource_val}, case={case_val}")
    return sampler


class BPMNOPTModel:
    """
    The result of building a BPMN+OPT problem from JSON.
    Holds the SimProblem, decision state, and metadata for the SMDP environment.
    """

    def __init__(self, problem_def):
        self.spec = problem_def
        self.problem = SimProblem(debugging=True)
        self.flows = {}
        self.lanes = {}
        self.tasks_meta = {}
        self.start_events_meta = {}
        self.end_events_meta = {}
        self.completed_var = {}
        self.patient_counter = [0]

        # Decision variable state: dict mapping (case_id, resource_id) -> 0/1
        self.assignments = {}

        self._build()

    def _build(self):
        self._build_flows()
        self._build_lanes()
        self._build_initial_resources()
        self._build_start_events()
        self._build_tasks()
        self._build_end_events()

    def _build_flows(self):
        for fspec in self.spec["process"]["flows"]:
            flow = BPMNFlow(self.problem, fspec["name"])
            self.flows[fspec["name"]] = flow

    def _build_lanes(self):
        for lspec in self.spec["process"]["lanes"]:
            lane = BPMNLane(self.problem, lspec["name"])
            self.lanes[lspec["name"]] = lane

    def _build_initial_resources(self):
        for rspec in self.spec["process"].get("initial_resources", []):
            lane = self.lanes[rspec["lane"]]
            for inst in rspec["instances"]:
                lane.put(dict(inst))

    def _build_start_events(self):
        for se_spec in self.spec["process"]["start_events"]:
            outflow = self.flows[se_spec["outgoing_flow"]]
            iat_spec = se_spec["interarrival_time"]
            gen_spec = se_spec.get("case_generator", {})
            counter = self.patient_counter

            def make_behavior(gen_spec_inner, counter_inner, problem_inner):
                def behavior(a):
                    counter_inner[0] += 1
                    case_data = {"id": counter_inner[0]}
                    for attr, val_spec in gen_spec_inner.items():
                        if val_spec == "current_time":
                            case_data[attr] = problem_inner.clock
                        elif val_spec is None:
                            case_data[attr] = None
                        elif isinstance(val_spec, dict) and "distribution" in val_spec:
                            if val_spec["distribution"] == "choice":
                                case_data[attr] = random.choice(val_spec["values"])
                        else:
                            case_data[attr] = val_spec
                    return SimToken(case_data)
                return behavior

            beh = make_behavior(gen_spec, counter, self.problem)
            iat_func = lambda spec=iat_spec: sample_interarrival(spec)

            BPMNStartEvent(
                self.problem, [], [outflow], se_spec["name"],
                interarrival_time=iat_func,
                behavior=beh
            )
            self.start_events_meta[se_spec["name"]] = se_spec

    def _build_tasks(self):
        for t_spec in self.spec["process"]["tasks"]:
            in_flow = self.flows[t_spec["incoming_flow"]]
            out_flow = self.flows[t_spec["outgoing_flow"]]
            res_lane = self.lanes[t_spec["resource_lane"]]
            ptime_sampler = make_ptime_sampler(t_spec["processing_time"]["rules"])
            assignments = self.assignments

            def make_guard(task_name, assignments_ref):
                def guard(case_tok, resource_tok):
                    c_id = case_tok["id"] if isinstance(case_tok, dict) else case_tok.id
                    r_id = resource_tok["id"] if isinstance(resource_tok, dict) else resource_tok.id
                    return assignments_ref.get((c_id, r_id), 0) == 1
                return guard

            def make_behavior(ptime_fn):
                def behavior(case_tok, resource_tok):
                    delay = ptime_fn(resource_tok, case_tok)
                    return [SimToken((case_tok, resource_tok), delay=delay)]
                return behavior

            guard_fn = make_guard(t_spec["name"], assignments)
            beh_fn = make_behavior(ptime_sampler)

            BPMNTask(
                self.problem,
                [in_flow, res_lane],
                [out_flow, res_lane],
                t_spec["name"],
                behavior=beh_fn,
                guard=guard_fn if t_spec.get("controlled", False) else None
            )
            self.tasks_meta[t_spec["name"]] = t_spec

    def _build_end_events(self):
        for ee_spec in self.spec["process"]["end_events"]:
            in_flow = self.flows[ee_spec["incoming_flow"]]
            end_beh = ee_spec.get("behavior", {})
            problem = self.problem

            completed_name = ee_spec["name"] + "_completed"

            if end_beh:
                def make_end_behavior(beh_spec, problem_ref):
                    def behavior(case_tok):
                        if isinstance(case_tok, dict):
                            updated = dict(case_tok)
                        else:
                            updated = case_tok
                        for attr, val_spec in beh_spec.items():
                            if val_spec == "current_time":
                                if isinstance(updated, dict):
                                    updated[attr] = problem_ref.clock
                                else:
                                    setattr(updated, attr, problem_ref.clock)
                        return [SimToken(updated)]
                    return behavior

                beh_fn = make_end_behavior(end_beh, problem)
                end_event_name = ee_spec["name"] + "<end_event>"
                completed_var = self.problem.add_var(completed_name)
                self.problem.add_event(
                    [in_flow], [completed_var], beh_fn,
                    name=end_event_name
                )
            else:
                completed_var = self.problem.add_var(completed_name)
                self.problem.add_event(
                    [in_flow], [completed_var], lambda c: [SimToken(c)],
                    name=ee_spec["name"] + "<end_event>"
                )

            self.completed_var[ee_spec["name"]] = completed_var
            self.end_events_meta[ee_spec["name"]] = ee_spec

    # ---- Decision interface used by the SMDP environment ----

    def get_waiting_cases(self):
        """Return list of case tokens currently in the decision case flow."""
        flow_name = self.spec["decision"]["variables"]["case_flow"]
        flow = self.flows[flow_name]
        return [tok for tok in flow.marking]

    def get_idle_resources(self):
        """Return list of resource tokens currently in the decision resource lane."""
        lane_name = self.spec["decision"]["variables"]["resource_lane"]
        lane = self.lanes[lane_name]
        return [tok for tok in lane.marking]

    def get_feasible_actions(self):
        """
        Return list of feasible (case_id, resource_id) pairs.
        Under sequential semantics, each action assigns one unassigned pair.
        """
        waiting = self.get_waiting_cases()
        idle = self.get_idle_resources()
        actions = []
        for c_tok in waiting:
            c_id = c_tok.value["id"] if isinstance(c_tok.value, dict) else c_tok.value.id
            already_assigned = any(
                self.assignments.get((c_id, r_tok.value["id"] if isinstance(r_tok.value, dict) else r_tok.value.id), 0) == 1
                for r_tok in idle
            )
            if already_assigned:
                continue
            for r_tok in idle:
                r_id = r_tok.value["id"] if isinstance(r_tok.value, dict) else r_tok.value.id
                case_assigned = any(
                    self.assignments.get((c_id2, r_id), 0) == 1
                    for c_tok2 in waiting
                    for c_id2 in [c_tok2.value["id"] if isinstance(c_tok2.value, dict) else c_tok2.value.id]
                )
                if case_assigned:
                    continue
                actions.append((c_id, r_id))
        return actions

    def apply_action(self, case_id, resource_id):
        """Set X_(case_id, resource_id) = 1."""
        self.assignments[(case_id, resource_id)] = 1

    def clear_assignments(self):
        """Clear all decision variable assignments."""
        self.assignments.clear()

    def get_completed_cases(self):
        """Return all completed case tokens."""
        all_completed = []
        for name, var in self.completed_var.items():
            for tok in var.marking:
                all_completed.append(tok)
        return all_completed

    def compute_total_cycle_time(self):
        """
        Compute total cycle time across all patients.
        Completed: complete - start
        In-progress/waiting: current_time - start
        """
        total = 0.0
        current_time = self.problem.clock
        seen_ids = set()

        for tok in self.get_completed_cases():
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            start = val["start"] if isinstance(val, dict) else val.start
            complete = val["complete"] if isinstance(val, dict) else val.complete
            if complete is not None:
                total += complete - start
            else:
                total += current_time - start
            seen_ids.add(pid)

        for flow in self.flows.values():
            for tok in flow.marking:
                val = tok.value
                pid = val["id"] if isinstance(val, dict) else val.id
                if pid not in seen_ids:
                    start = val["start"] if isinstance(val, dict) else val.start
                    total += current_time - start
                    seen_ids.add(pid)

        for task_name, meta in self.tasks_meta.items():
            busy_var_name = task_name + "_busy"
            if busy_var_name in self.problem.id2node:
                busy_var = self.problem.id2node[busy_var_name]
                for tok in busy_var.marking:
                    val = tok.value
                    if isinstance(val, tuple):
                        case_val = val[0]
                    else:
                        case_val = val
                    pid = case_val["id"] if isinstance(case_val, dict) else case_val.id
                    if pid not in seen_ids:
                        start = case_val["start"] if isinstance(case_val, dict) else case_val.start
                        total += current_time - start
                        seen_ids.add(pid)

        return total

    def compute_reward(self):
        """Compute SMDP reward (terminal, negative cycle time for minimization)."""
        reward_type = self.spec["smdp"].get("reward_type", "terminal")
        if reward_type == "terminal":
            return -self.compute_total_cycle_time()
        return 0.0

    def get_state_snapshot(self):
        """
        Return a hashable representation of the current SMDP state.
        Used for tabular methods.
        """
        waiting_ids = []
        for tok in self.get_waiting_cases():
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            ptype = val["type"] if isinstance(val, dict) else val.type
            waiting_ids.append((pid, ptype))
        waiting_ids.sort()

        idle_ids = []
        for tok in self.get_idle_resources():
            val = tok.value
            rid = val["id"] if isinstance(val, dict) else val.id
            idle_ids.append(rid)
        idle_ids.sort()

        active_assignments = tuple(sorted(
            (k, v) for k, v in self.assignments.items() if v == 1
        ))

        return (tuple(waiting_ids), tuple(idle_ids), active_assignments)


def load_problem(json_path):
    """Load a BPMN+OPT problem definition from a JSON file and build the SimPN model."""
    with open(json_path, "r") as f:
        spec = json.load(f)
    return BPMNOPTModel(spec)


def build_from_dict(spec):
    """Build a BPMN+OPT model from a Python dict (already parsed JSON)."""
    return BPMNOPTModel(spec)
