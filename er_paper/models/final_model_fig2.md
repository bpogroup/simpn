# BPMN+OPT Model — Fig 2: Simplified Resource-Assignment Fragment (Final)

> Status: All questions resolved.

## Object Types (C, R)

```
# Case object type
Patient: {id: str, type: {P1, P2}, start: Time, complete: Time}

# Resource object type
Oncologist: {id: str, name: str}
```

## Authorization (auth)

```
auth = {(Oncologist, Examination)}
# Any oncologist is eligible to execute the Examination task.
```

## Flows and Lanes

```
BPMNFlow("waiting", type=Patient)
BPMNFlow("done", type=Patient)
BPMNLane("idle_oncologist", type=Oncologist)
```

## Initial State

```
idle_oncologist.create({id: "phi1", name: "Dr. Smith"})
idle_oncologist.create({id: "phi2", name: "Dr. Johnson"})
```

## Events (E)

### Start Event: "arrival"

```
interarrival_time:
    random.expovariate(1/10)           # exp(10): exponential with mean=10

arrival_behavior:
    patient_id += 1                     # Global counter, initialized to 0
    waiting.put({id: patient_id, type: random.choice({P1, P2}), start: time})

BPMNStartEvent([], [waiting], "arrival", arrival_behavior, interarrival_time)
```

### End Event: "complete"

```
complete_behavior:
    done.update({complete: time})        # End event updates the token as it consumes it

BPMNEndEvent([done], [], "complete", complete_behavior)
```

## Tasks (T)

### Task: "Examination"

```
# Condition: any oncologist can examine any patient
cond_Examination(oncologist, patient) = true

# Processing time depends on (oncologist.id, patient.type) — matches Fig 2
ptime_Examination(oncologist, patient):
    if (oncologist.id, patient.type) == ("phi1", P1): uniform(2, 4)
    elif (oncologist.id, patient.type) == ("phi1", P2): uniform(3, 5)
    elif (oncologist.id, patient.type) == ("phi2", P1): uniform(4, 6)
    elif (oncologist.id, patient.type) == ("phi2", P2): uniform(5, 7)

# Behavior: purely a delay, no attribute updates
beh_Examination(oncologist, patient) = {}

# Control: task start is controlled by the decision variable
guard_Examination:
    X_(patient, oncologist) == 1

BPMNTask([waiting], [done], [idle_oncologist], "Examination",
         guard=guard_Examination, ptime=ptime_Examination, beh=beh_Examination)
```

> **Lifecycle (resolved):** When Examination fires, the patient is consumed from
> `waiting` and the oncologist from `idle_oncologist`. Both enter an implicit
> "busy" state during `ptime`. After `ptime` elapses, the patient is produced
> into `done` and the oncologist returns to `idle_oncologist`.

## Sequence Flows (F)

```
F = {
    (arrival, waiting),
    (waiting, Examination),
    (Examination, done),
    (done, complete)
}
# No conditions on flows (all unconditional).
```

## Gateways (G)

```
G = {}  # None in this model.
```

---

## Decision Variables (X)

```
# Decision variables are persistent: they remain set until consumed by the task guard.
# They are scoped to objects currently in their respective flows/lanes.
X_(p, o): {0, 1},  ∀ p ∈ waiting, ∀ o ∈ idle_oncologist
```

## Decision Moments (Mom)

```
# Sequential semantics: one assignment per decision epoch.
# After each assignment, the state changes (task starts, patient and oncologist
# leave their flows), and the decision moment is re-evaluated against the new state.
# This continues until no more unassigned feasible pairs exist.
#
# This ensures that:
# - Constraints are always evaluated against the current (post-assignment) state
# - State changes from one assignment can invalidate subsequent assignments
# - The action space per epoch is small (one pair, not a combinatorial set)

∃ p ∈ waiting: (¬∃ o' ∈ idle_oncologist: X_(p, o') = 1)
∧
∃ o ∈ idle_oncologist: (¬∃ p' ∈ waiting: X_(p', o) = 1)
```

## Constraints (Con)

```
# Each waiting patient assigned to at most one idle oncologist
∀ p ∈ waiting: Σ_(o ∈ idle_oncologist) X_(p, o) ≤ 1

# Each idle oncologist assigned to at most one waiting patient
∀ o ∈ idle_oncologist: Σ_(p ∈ waiting) X_(p, o) ≤ 1
```

## Objectives (Obj)

```
minimize
    Σ_(p ∈ Patient: p.complete ≠ ⊥) (p.complete - p.start)
    +
    Σ_(p ∈ Patient: p.complete = ⊥) (time - p.start)
```

> **Note:** The objective sums over all Patient objects ever created (the type),
> not just those currently in a flow. This captures completed, in-progress, and
> waiting patients.

---

## SMDP Interpretation

The sequential decision semantics induces the following SMDP structure:

**State:** `s = (O_t, X_t)` — the object valuation (patient/oncologist locations and
attributes) together with the current persistent decision variable assignments.

**Action:** A single assignment `X_(p, o) = 1` for one unassigned waiting patient `p`
and one unassigned idle oncologist `o`.

**Transition:** After the action:
1. The guard `X_(p, o) == 1` is satisfied → Examination starts for (p, o)
2. Patient `p` leaves `waiting`, oncologist `o` leaves `idle_oncologist` (both enter busy state)
3. The decision moment is re-evaluated against the new state
4. If another unassigned pair exists → new decision epoch (same simulation time)
5. If no unassigned pair exists → process evolves until next event (task completion or new arrival)
6. That event produces the next decision state `s'`

**Holding time:** The time between the last assignment in a sequence and the next
state-changing event (task completion or patient arrival).

**Reward:** Terminal reward based on the objective (total cycle time) at horizon.

---

## Open Questions Summary

1. ~~**Decision atomicity**: One or multiple assignments per epoch?~~ **RESOLVED: Sequential — one per epoch.**
2. ~~**Busy state**: Is it implicit in the BPMNTask lifecycle?~~ **RESOLVED: Yes, implicit.**
3. ~~**Decision variable lifecycle**: Persistent or ephemeral?~~ **RESOLVED: Persistent until consumed.**
4. ~~**Processing time values**: Fig 2 values or v1/v2 values?~~ **RESOLVED: Matching Fig 2.**
5. ~~**Interarrival time**: `exp(10)` meaning mean=10?~~ **RESOLVED: Yes, `expovariate(1/10)` = mean 10.**
6. ~~**Patient counter**: Where is `patient_id` initialized?~~ **RESOLVED: Global, initialized to 0.**
7. ~~**Task behavior**: Does Examination update any attributes?~~ **RESOLVED: No, purely a delay.**
8. ~~**End event behavior**: When exactly does `complete = time` get set?~~ **RESOLVED: `done.update({complete: time})` — end event updates the token as it consumes it.**
