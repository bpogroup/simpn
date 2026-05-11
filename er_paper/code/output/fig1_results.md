# Figure 1 — Full Outpatient Process Results

## Process Description

Full outpatient chemotherapy with **3 decision types**:
- **Scheduling**: assign appointment times (offsets 0/5/10/15/20 min)
- **Assignment**: 5 controlled tasks (Bloodwork, Examination, Drug_prep, Std/Int infusion)
- **Routing**: standard vs intensive infusion

Resources: 2 lab staff (senior+junior), 2 oncologists, 6 pharmacists, 20 chairs
Horizon: 480 minutes | Interarrival: exp(mean=6 min)

## Heuristic Policy Evaluation

| Policy | Avg Reward | Avg Cycle Time | Avg Completions | Time (s) |
|--------|-----------|----------------|-----------------|----------|
| FIFO     | -11302.77 | 8349.02 | 63.6 | 1.6 |
| SPT      | -11522.62 | 8482.17 | 64.2 | 1.7 |
| Random   | -12240.21 | 9580.70 | 56.4 | 1.6 |

## SMDP Compilation

- Episodes: 200
- States discovered: 1105
- Actions discovered: 57
- Transition triples (s,a,s'): 1523
- Compilation time: 43.2s

This confirms the state-space explosion predicted for the full model.
Tabular SMDP methods (VI, Q-learning) become intractable at this scale.
