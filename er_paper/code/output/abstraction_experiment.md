# State-Space Abstraction Experiment (K=5 replications)

_Generated: 2026-05-11 11:42 | 30 eval episodes per replication_

## Abstraction Levels

| Level | Name | State | Action | What it captures |
|-------|------|-------|--------|------------------|
| L0 | counts | queue lengths + resource counts | (assign, task) | System load only |
| L1 | resource_ids | queue lengths + idle resource IDs | (assign, task, rid) | + which resources |
| L2 | full_cpn | patient attrs + resource IDs | (assign, task, rid) | + patient attributes |

## Figure 2

| Horizon | Patients | Level | States | FIFO CT | QL CT | QL vs FIFO | VI CT | VI vs FIFO |
|---------|----------|-------|--------|---------|-------|------------|-------|------------|
| 100 | 9 | L0 (counts) | 4 | 46.2±15.9 | 50.6±2.2 | +9.5% | 50.8±2.5 | +9.8% |
| 100 | 9 | L1 (resource_ids) | 4 | 46.2±15.9 | 45.6±2.8 | -1.3% | 45.7±2.8 | -1.2% |
| 100 | 9 | L2 (full_cpn) | 4 | 46.2±15.9 | 45.6±2.8 | -1.3% | 45.7±2.8 | -1.2% |
| 200 | 20 | L0 (counts) | 4 | 86.8±22.7 | 93.9±5.1 | +8.1% | 93.9±5.1 | +8.2% |
| 200 | 20 | L1 (resource_ids) | 5 | 86.8±22.7 | 95.2±3.0 | +9.7% | 85.7±3.3 | -1.3% |
| 200 | 20 | L2 (full_cpn) | 5 | 86.8±22.7 | 95.2±3.0 | +9.7% | 85.7±3.3 | -1.3% |

## Figure 1

| Horizon | Patients | Level | States | FIFO CT | QL CT | QL vs FIFO | VI CT | VI vs FIFO |
|---------|----------|-------|--------|---------|-------|------------|-------|------------|
| 30 | 7 | L0 (counts) | 24 | 110.8±39.0 | 113.5±8.4 | +2.5% | 112.8±5.9 | +1.8% |
| 30 | 7 | L1 (resource_ids) | 24 | 110.8±39.0 | 114.4±4.8 | +3.2% | 111.4±9.0 | +0.6% |
| 30 | 7 | L2 (full_cpn) | 24 | 110.8±39.0 | 114.5±6.3 | +3.3% | 111.6±10.1 | +0.7% |
| 60 | 12 | L0 (counts) | 50 | 368.9±101.0 | 371.8±14.0 | +0.8% | 382.3±24.5 | +3.6% |
| 60 | 12 | L1 (resource_ids) | 50 | 368.9±101.0 | 370.1±15.1 | +0.3% | 367.4±31.7 | -0.4% |
| 60 | 12 | L2 (full_cpn) | 50 | 368.9±101.0 | 378.4±7.8 | +2.6% | 366.5±23.6 | -0.6% |
| 90 | 19 | L0 (counts) | 90 | 771.7±183.9 | 789.6±44.5 | +2.3% | 776.6±35.7 | +0.6% |
| 90 | 19 | L1 (resource_ids) | 90 | 771.7±183.9 | 795.7±15.8 | +3.1% | 767.4±57.7 | -0.6% |
| 90 | 19 | L2 (full_cpn) | 90 | 771.7±183.9 | 795.6±25.3 | +3.1% | 789.8±38.1 | +2.3% |
| 120 | 25 | L0 (counts) | 125 | 1285.7±277.6 | 1296.3±60.7 | +0.8% | 1347.3±30.3 | +4.8% |
| 120 | 25 | L1 (resource_ids) | 125 | 1285.7±277.6 | 1325.8±47.3 | +3.1% | 1322.7±81.1 | +2.9% |
| 120 | 25 | L2 (full_cpn) | 125 | 1285.7±277.6 | 1329.0±67.1 | +3.4% | 1300.7±111.3 | +1.2% |

## Key Observations

- Each QL/VI cell is mean ± std over K=5 independent train+eval replications.
- **Negative % = better than FIFO** (lower cycle time); **positive % = worse**.
- The CPN marking defines the exact Markov state; any abstraction introduces non-Markovianity.
