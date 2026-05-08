# BPMN+OPT → SMDP Pipeline

This project implements the formal compilation of **BPMN+OPT** (Business Process Model and Notation with Optimization extensions) into **Semi-Markov Decision Processes** (SMDPs), as described in the accompanying ER paper.

## Directory Structure

```
er_paper/
├── models/          # BPMN+OPT problem definitions (JSON) and model specs
│   ├── fig2_problem.json        # Figure 2 resource assignment problem
│   ├── bpmnopt_schema.json      # JSON Schema for BPMN+OPT problems
│   ├── final_model_fig2.md      # Annotated BPMN+OPT model specification
│   ├── model_fig2_v1.md         # Model draft v1
│   └── model_fig2_v2.md         # Model draft v2
├── docs/            # Papers, figures, and LaTeX source
│   ├── er_paper.tex             # LaTeX source of the ER paper
│   ├── ER Paper Running Example.pdf
│   ├── outpatient_small.pdf     # Figure 2 diagram
│   └── SMDP_Sutton.pdf          # Sutton et al. SMDP reference paper
├── code/            # Python implementation
│   ├── bpmnopt_builder.py       # BPMN+OPT JSON → SimPN model builder
│   ├── smdp_env.py              # SMDP environment (gym-like interface)
│   ├── solvers.py               # Heuristic, Q-Learning, and Value Iteration solvers
│   ├── smdp_compiler.py         # BPMN+OPT → general SMDP JSON compiler
│   ├── run_fig2.py              # End-to-end demo script
│   └── debug_vi.py              # VI debugging/tracing script
└── README.md
```

## Pipeline Overview

```
BPMN+OPT JSON  →  SimPN Model  →  SMDP Environment  →  Solvers
(declarative)     (executable)     (states/actions)     (policies)
                                        ↓
                                   SMDP JSON
                                 (compiled model)
```

1. **Define** a BPMN+OPT problem in JSON (`models/fig2_problem.json`)
2. **Build** a SimPN simulation model (`bpmnopt_builder.py`)
3. **Wrap** in an SMDP environment with step rewards (`smdp_env.py`)
4. **Compile** to a general SMDP JSON for analysis (`smdp_compiler.py`)
5. **Solve** using heuristics, RL, or exact methods (`solvers.py`)

## Quick Start

```bash
cd er_paper/code
python run_fig2.py
```

## Solution Methods

| Method | Type | Description |
|--------|------|-------------|
| FIFO | Heuristic | Assign longest-waiting patient first |
| SPT | Heuristic | Assign pair with shortest expected processing time |
| Random | Heuristic | Uniform random assignment |
| Q-Learning | Approximate (RL) | Tabular SMDP Q-learning with ε-greedy exploration |
| Value Iteration | Exact (DP) | Monte Carlo transition estimation + Bellman iteration |
