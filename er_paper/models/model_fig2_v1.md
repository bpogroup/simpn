# BPMN+OPT Model — Fig 2: Simplified Resource-Assignment Fragment

## Object types

```
Oncologist: {id: str, loc: Location, name: str}
Patient: {id: str, loc: Location, type: {P1, P2}, start: Time, complete: Time}
```

## BPMN

```
BPMNFlow("waiting")
BPMNFlow("done")

BPMNLane("Oncologist")
Oncologist.create({id: "phi1", loc: idle, name: "Dr. Smith"})
Oncologist.create({id: "phi2", loc: idle, name: "Dr. Johnson"})

arrival_behavior():
    patient_id += 1
    Patient.create({id: patient_id, loc: waiting, type: random.choice({P1, P2}), start: time))

interarrival_time():
    random.expovariate(10/60)

BPMNStartEvent([], [waiting], "arrival", arrival_behavior, interarrival_time)

examination_time(oncologist, waiting):
    if (oncologist, waiting.type) == ("D1", "T1"): uniform(4, 8)
    elif (oncologist, waiting.type) == ("D1", "T2"): uniform(7, 11)
    elif (oncologist, waiting.type) == ("D2", "T1"): uniform(8, 12)
    elif (oncologist, waiting.type) == ("D2", "T2"): uniform(5, 9)

examination_control(oncologist, waiting):
    start # This denotes that the start of the task is controlled by a decision.

BPMNTask([waiting], [done], [oncologist], "Examination", examination_time, examination_control)

complete_behavior:
    Patient.update(done, {complete: time})

BPMNEndEvent([done], [], "complete", complete_behavior)
```

## Decision

### Decision variables

```
# There is a decision variable for each combination of a waiting patient and an idle oncologist
X_(p, o): {0, 1}, ∀ p ∈ Patient, o ∈ Oncologist
```

### Decision moment

```
# A decision can be taken each time there is a waiting patient AND there is an idle oncologist
∃ p ∈ Patient, ∃ o ∈ Oncologist: p.loc = waiting ∧ o.loc = idle
```

### Constraints

```
# Each waiting patient must be assigned to at most one idle oncologist
∀ p in Patient: Σ_(o in Oncologist) X_(p, o) ≤ 1

# Each idle oncologist must be assigned to at most one waiting patient
∀ o in Oncologist: Σ_(p in Patient) X_(p, o) ≤ 1
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

## Action

```
# The decision to assign a particular patient to a particular oncologist triggers
# the start of the examination for that patient, oncologist combination
X_(patient, oncologist) = 1 triggers Examination.start(patient, oncologist)
```
