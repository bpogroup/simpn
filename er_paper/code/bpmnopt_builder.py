"""
bpmnopt_builder.py — Unified BPMN+OPT builder.

Parses a BPMN+OPT JSON problem definition and constructs:
  1. A SimPN SimProblem (flows, lanes, tasks, gateways, scheduling, routing)
  2. Decision-variable state and task guards
  3. Typed action interface: ("assign", task, cid, rid) / ("schedule", cid, offset) / ("route", cid, val)

Handles both simple models (Figure 2: single task, assignment only) and
complex models (Figure 1: multiple tasks, gateways, scheduling, routing).
"""

import json
import random
from simpn.simulator import SimProblem, SimToken, SimVar
from simpn.prototypes import (
    BPMNFlow, BPMNLane, BPMNStartEvent, BPMNTask, BPMNEndEvent,
    BPMNParallelSplitGateway, BPMNIntermediateEvent,
)


def sample_distribution(dist_spec):
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
    dist = iat_spec["distribution"]
    if dist == "exponential":
        return random.expovariate(1.0 / iat_spec["mean"])
    elif dist == "constant":
        return iat_spec["value"]
    else:
        raise ValueError(f"Unknown interarrival distribution: {dist}")


def match_condition(condition, resource_val, case_val):
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
    def sampler(resource_val, case_val):
        for rule in rules:
            if match_condition(rule["condition"], resource_val, case_val):
                return sample_distribution(rule["distribution"])
        raise ValueError(f"No processing-time rule matched for resource={resource_val}, case={case_val}")
    return sampler


class BPMNOPTModel:
    """
    Unified BPMN+OPT model. Handles:
      - Simple models (single task, assignment only)
      - Complex models (multiple tasks, gateways, scheduling, routing)
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

        # Assignment keys: (task_name, case_id, resource_id)
        self.assignments = {}

        self._scheduling_spec = problem_def["process"].get("scheduling", None)
        self._routing_gateways = {}
        self._controlled_tasks = []

        self._build()

    def _build(self):
        self._build_flows()
        self._build_lanes()
        self._build_initial_resources()
        self._build_start_events()
        self._build_tasks()
        self._build_gateways()
        self._build_scheduling_events()
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
            task_name = t_spec["name"]
            is_controlled = t_spec.get("controlled", False)
            resource_constraint = t_spec.get("resource_constraint", None)
            behavior_spec = t_spec.get("behavior", {})

            if is_controlled:
                self._controlled_tasks.append(t_spec)

            def make_guard(tname, assignments_ref, res_constraint):
                def guard(case_tok, resource_tok):
                    c_id = case_tok["id"] if isinstance(case_tok, dict) else case_tok.id
                    r_id = resource_tok["id"] if isinstance(resource_tok, dict) else resource_tok.id
                    if assignments_ref.get((tname, c_id, r_id), 0) != 1:
                        return False
                    if res_constraint == "case.chair_id == resource.id":
                        c_chair = case_tok.get("chair_id") if isinstance(case_tok, dict) else getattr(case_tok, "chair_id", None)
                        return c_chair == r_id
                    return True
                return guard

            def make_constraint_guard(res_constraint):
                def guard(case_tok, resource_tok):
                    if res_constraint == "case.chair_id == resource.id":
                        c_chair = case_tok.get("chair_id") if isinstance(case_tok, dict) else getattr(case_tok, "chair_id", None)
                        r_id = resource_tok["id"] if isinstance(resource_tok, dict) else resource_tok.id
                        return c_chair == r_id
                    return True
                return guard

            def make_behavior(ptime_fn, beh_spec):
                def behavior(case_tok, resource_tok):
                    if isinstance(case_tok, dict):
                        if beh_spec.get("set_measurements"):
                            case_tok["measurements"] = random.random()
                        if beh_spec.get("bind_chair"):
                            r_id = resource_tok["id"] if isinstance(resource_tok, dict) else resource_tok.id
                            case_tok["chair_id"] = r_id
                    delay = ptime_fn(resource_tok, case_tok)
                    return [SimToken((case_tok, resource_tok), delay=delay)]
                return behavior

            if is_controlled:
                guard_fn = make_guard(task_name, assignments, resource_constraint)
            elif resource_constraint:
                guard_fn = make_constraint_guard(resource_constraint)
            else:
                guard_fn = None

            beh_fn = make_behavior(ptime_sampler, behavior_spec)

            BPMNTask(
                self.problem,
                [in_flow, res_lane],
                [out_flow, res_lane],
                task_name,
                behavior=beh_fn,
                guard=guard_fn
            )
            self.tasks_meta[task_name] = t_spec

    def _build_gateways(self):
        for gw_spec in self.spec["process"].get("gateways", []):
            gw_type = gw_spec["type"]

            if gw_type == "AND-split":
                in_flow = self.flows[gw_spec["incoming"]]
                out_flows = [self.flows[name] for name in gw_spec["outgoing"]]
                BPMNParallelSplitGateway(
                    self.problem, [in_flow], out_flows, gw_spec["name"]
                )

            elif gw_type == "AND-join":
                in_flows = [self.flows[name] for name in gw_spec["incoming"]]
                out_flow = self.flows[gw_spec["outgoing"]]
                self._build_and_join(gw_spec["name"], in_flows, out_flow)

            elif gw_type == "XOR-split":
                in_flow = self.flows[gw_spec["incoming"]]
                self._build_xor_split(gw_spec, in_flow)

    def _build_and_join(self, name, in_flows, out_flow):
        def guard(*args):
            first_id = args[0]["id"] if isinstance(args[0], dict) else args[0].id
            for a in args[1:]:
                a_id = a["id"] if isinstance(a, dict) else a.id
                if a_id != first_id:
                    return False
            return True

        def behavior(*args):
            return [SimToken(args[0])]

        self.problem.add_event(
            in_flows, [out_flow], behavior, name=name + "<and_join>", guard=guard
        )

    def _build_xor_split(self, gw_spec, in_flow):
        self._routing_gateways[gw_spec["name"]] = gw_spec
        for branch in gw_spec["outgoing"]:
            out_flow = self.flows[branch["flow"]]
            condition = branch["condition"]

            def make_route_guard(cond_str):
                attr, val = cond_str.replace(" ", "").split("==")
                attr_name = attr.split(".")[-1]
                def guard(case_tok):
                    c_val = case_tok.get(attr_name) if isinstance(case_tok, dict) else getattr(case_tok, attr_name, None)
                    return c_val == val
                return guard

            route_guard = make_route_guard(condition)
            self.problem.add_event(
                [in_flow], [out_flow],
                lambda c: [SimToken(c)],
                name=f"{gw_spec['name']}_to_{branch['flow']}<xor_route>",
                guard=route_guard
            )

    def _build_scheduling_events(self):
        sched = self._scheduling_spec
        if sched is None:
            return

        arrived_flow = self.flows[sched["incoming_flow"]]
        target_flow = self.flows[sched["outgoing_flow"]]
        problem = self.problem

        def sched_guard(case_tok):
            at = case_tok.get("appointment_time") if isinstance(case_tok, dict) else getattr(case_tok, "appointment_time", None)
            return at is not None

        def sched_behavior(case_tok):
            at = case_tok["appointment_time"] if isinstance(case_tok, dict) else case_tok.appointment_time
            delay = max(0.0, at - problem.clock)
            return [SimToken(case_tok, delay=delay)]

        BPMNIntermediateEvent(
            self.problem, [arrived_flow], [target_flow],
            "scheduling_wait",
            behavior=sched_behavior,
            guard=sched_guard
        )

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
                completed_var = self.problem.add_var(completed_name)
                self.problem.add_event(
                    [in_flow], [completed_var], beh_fn,
                    name=ee_spec["name"] + "<end_event>"
                )
            else:
                completed_var = self.problem.add_var(completed_name)
                self.problem.add_event(
                    [in_flow], [completed_var], lambda c: [SimToken(c)],
                    name=ee_spec["name"] + "<end_event>"
                )

            self.completed_var[ee_spec["name"]] = completed_var
            self.end_events_meta[ee_spec["name"]] = ee_spec

    # ---- Unified decision interface (typed actions) ----

    def _token_available(self, tok):
        """Check if a token is currently available (not delayed into the future)."""
        return tok.time <= self.problem.clock + 1e-9

    def get_scheduling_actions(self):
        sched = self._scheduling_spec
        if sched is None:
            return []
        arrived_flow = self.flows[sched["incoming_flow"]]
        offsets = sched["slot_offsets"]
        actions = []
        for tok in arrived_flow.marking:
            if not self._token_available(tok):
                continue
            val = tok.value
            at = val.get("appointment_time") if isinstance(val, dict) else getattr(val, "appointment_time", None)
            if at is None:
                c_id = val["id"] if isinstance(val, dict) else val.id
                for off in offsets:
                    actions.append(("schedule", c_id, off))
        return actions

    def get_assignment_actions(self):
        actions = []
        for t_spec in self._controlled_tasks:
            task_name = t_spec["name"]
            in_flow = self.flows[t_spec["incoming_flow"]]
            res_lane = self.lanes[t_spec["resource_lane"]]
            res_constraint = t_spec.get("resource_constraint", None)

            waiting = [t for t in in_flow.marking if self._token_available(t)]
            idle = [t for t in res_lane.marking if self._token_available(t)]

            for c_tok in waiting:
                c_val = c_tok.value
                c_id = c_val["id"] if isinstance(c_val, dict) else c_val.id
                already_assigned = any(
                    self.assignments.get((task_name, c_id,
                        r_tok.value["id"] if isinstance(r_tok.value, dict) else r_tok.value.id), 0) == 1
                    for r_tok in idle
                )
                if already_assigned:
                    continue
                for r_tok in idle:
                    r_val = r_tok.value
                    r_id = r_val["id"] if isinstance(r_val, dict) else r_val.id
                    resource_already_used = any(
                        self.assignments.get((task_name,
                            c2_tok.value["id"] if isinstance(c2_tok.value, dict) else c2_tok.value.id,
                            r_id), 0) == 1
                        for c2_tok in waiting
                    )
                    if resource_already_used:
                        continue
                    if res_constraint == "case.chair_id == resource.id":
                        c_chair = c_val.get("chair_id") if isinstance(c_val, dict) else getattr(c_val, "chair_id", None)
                        if c_chair != r_id:
                            continue
                    actions.append(("assign", task_name, c_id, r_id))
        return actions

    def get_routing_actions(self):
        actions = []
        for gw_name, gw_spec in self._routing_gateways.items():
            in_flow = self.flows[gw_spec["incoming"]]
            for tok in in_flow.marking:
                if not self._token_available(tok):
                    continue
                val = tok.value
                attr_name = None
                for branch in gw_spec["outgoing"]:
                    cond = branch["condition"].replace(" ", "")
                    attr_name = cond.split("==")[0].split(".")[-1]
                    break
                if attr_name is None:
                    continue
                current_val = val.get(attr_name) if isinstance(val, dict) else getattr(val, attr_name, None)
                if current_val is not None:
                    continue
                c_id = val["id"] if isinstance(val, dict) else val.id
                for branch in gw_spec["outgoing"]:
                    cond = branch["condition"].replace(" ", "")
                    route_val = cond.split("==")[1]
                    actions.append(("route", c_id, route_val))
        return actions

    def get_all_feasible_actions(self):
        actions = []
        actions.extend(self.get_scheduling_actions())
        actions.extend(self.get_routing_actions())
        actions.extend(self.get_assignment_actions())
        return actions

    def apply_action(self, action):
        action_type = action[0]
        if action_type == "schedule":
            _, case_id, offset = action
            self._apply_scheduling(case_id, offset)
        elif action_type == "assign":
            _, task_name, case_id, resource_id = action
            self.assignments[(task_name, case_id, resource_id)] = 1
        elif action_type == "route":
            _, case_id, route_value = action
            self._apply_routing(case_id, route_value)
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    def _apply_scheduling(self, case_id, offset):
        sched = self._scheduling_spec
        arrived_flow = self.flows[sched["incoming_flow"]]
        for tok in arrived_flow.marking:
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            if pid == case_id:
                if isinstance(val, dict):
                    val["appointment_time"] = self.problem.clock + offset
                else:
                    val.appointment_time = self.problem.clock + offset
                return

    def _apply_routing(self, case_id, route_value):
        for gw_name, gw_spec in self._routing_gateways.items():
            in_flow = self.flows[gw_spec["incoming"]]
            for tok in in_flow.marking:
                val = tok.value
                pid = val["id"] if isinstance(val, dict) else val.id
                if pid == case_id:
                    attr_name = None
                    for branch in gw_spec["outgoing"]:
                        cond = branch["condition"].replace(" ", "")
                        attr_name = cond.split("==")[0].split(".")[-1]
                        break
                    if attr_name and isinstance(val, dict):
                        val[attr_name] = route_value
                    return

    def clear_assignments(self):
        self.assignments.clear()

    def get_completed_cases(self):
        all_completed = []
        for name, var in self.completed_var.items():
            for tok in var.marking:
                all_completed.append(tok)
        return all_completed

    def count_patients_in_system(self):
        n = 0
        for flow in self.flows.values():
            n += len(flow.marking)
        for task_name in self.tasks_meta:
            busy_var_name = task_name + "_busy"
            if busy_var_name in self.problem.id2node:
                n += len(self.problem.id2node[busy_var_name].marking)
        return n

    def compute_total_cycle_time(self):
        total = 0.0
        current_time = self.problem.clock
        seen_ids = set()

        for tok in self.get_completed_cases():
            val = tok.value
            pid = val["id"] if isinstance(val, dict) else val.id
            start = val["start"] if isinstance(val, dict) else val.start
            complete = val.get("complete") if isinstance(val, dict) else getattr(val, "complete", None)
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

        for task_name in self.tasks_meta:
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


def load_problem(json_path):
    with open(json_path, "r") as f:
        spec = json.load(f)
    return BPMNOPTModel(spec)
