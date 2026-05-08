# BPMN+OPT Model — Fig 2: Simplified Resource-Assignment Fragment (v2)

## Object types

```
Oncologist: {id: str, name: str}
Patient: {id: str, type: {P1, P2}, start: Time, complete: Time}
```

## BPMN

```
BPMNFlow("waiting", type=Patient)
BPMNFlow("done", type=Patient)

BPMNLane("idle_oncologist", type=Oncologist)
idle_oncologist.create({id: "phi1", name: "Dr. Smith"})
idle_oncologist.create({id: "phi2", name: "Dr. Johnson"})

arrival_behavior:
    patient_id += 1
    waiting.put({id: patient_id, type: random.choice({P1, P2}), start: time))

interarrival_time:
    random.expovariate(10/60)

BPMNStartEvent([], [waiting], "arrival", arrival_behavior, interarrival_time)

examination_control:
    X_(waiting, idle_oncologist) == 1

examination_time:
    if (idle_oncologist, waiting.type) == ("D1", "T1"): uniform(4, 8)
    elif (idle_oncologist, waiting.type) == ("D1", "T2"): uniform(7, 11)
    elif (idle_oncologist, waiting.type) == ("D2", "T1"): uniform(8, 12)
    elif (idle_oncologist, waiting.type) == ("D2", "T2"): uniform(5, 9)

BPMNTask([waiting], [done], [idle_oncologist], "Examination", examination_control, examination_time)

complete_behavior:
    done.update({complete: time})

BPMNEndEvent([done], [], "complete", complete_behavior)
```

## Decision

### Decision variables

```
# There is a decision variable for each combination of a waiting patient and an idle oncologist
X_(p, o): {0, 1}, ∀ p ∈ waiting, o ∈ idle_oncologist
```

### Decision moment

```
# A decision can be taken each time there is a waiting patient that is not already
# assigned to an idle oncologist AND there is an idle oncologist that is not already
# assigned to a waiting patient
∃ p ∈ waiting: ¬∃ o' ∈ idle_oncologist: X_(p, o') = 1
∧
∃ o ∈ idle_oncologist: ¬∃ p' ∈ waiting: X_(p', o) = 1
```

### Constraints

```
# Each waiting patient must be assigned to at most one idle oncologist
∀ p in waiting: Σ_(o in idle_oncologist) X_(p, o) ≤ 1

# Each idle oncologist must be assigned to at most one waiting patient
∀ o in idle_oncologist: Σ_(p in waiting) X_(p, o) ≤ 1
```

### Objective

```
# We minimize the sum of cycle times, where the cycle time of an uncompleted patient
# (i.e., a patient who has no completion time) is the current time minus the patient
# start time. This is necessary to prevent 'not assigning any patients' from being
# the optimal strategy.
minimize
    Σ_(p in Patient, p.complete ≠ ⊥) p.complete - p.start
    +
    Σ_(p in Patient, p.complete = ⊥) time - p.start
```
