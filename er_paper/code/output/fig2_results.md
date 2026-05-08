# Evaluation Results: fig2_resource_assignment

**Generated:** 2026-05-07 20:41:06  
**Horizon:** 200  
**Discount:** 1.0  
**Evaluation episodes:** 100 per method  
**Q-Learning training episodes:** 1000  
**Value Iteration sample episodes:** 1000  

## Comparison Summary

| Method | Avg Cycle Time | Std | Avg Reward |
|--------|---------------:|----:|-----------:|
| FIFO | 82.88 | 21.11 | -85.40 |
| SPT | 82.73 | 20.81 | -85.22 |
| Random | 94.55 | 22.50 | -97.15 |
| Q-Learning | 85.47 | 23.11 | -88.44 |
| Value Iteration | 85.48 | 23.29 | -88.53 |

**Best method:** SPT (avg cycle time: 82.73)

## Method Details

### 1. Heuristic Solvers

- **FIFO** — Assign the longest-waiting patient to the first available resource.
- **SPT** — Assign the (patient, resource) pair with shortest expected processing time.
- **Random** — Uniformly random assignment.

### 2. Q-Learning (Approximate)

- Alpha: 0.05, Gamma: 1.0, Epsilon: 0.5 → 0.0248 (decayed)
- Q-table size: 42 entries
- Training time: 1.8s

### 3. Value Iteration (Exact)

- Abstract states discovered: 21
- State-action pairs: 29
- Convergence: 1000 max iterations, theta=1e-06
- Solve time: 2.8s

## Reward Semantics

Step reward = −∫ n(t) dt over the holding interval between decision epochs,
where n(t) is the number of patients in the system at time t.
This equals the cycle-time contribution of each interval.
