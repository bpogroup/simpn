"""
run_fig2.py — End-to-end demo for the BPMN+OPT -> SMDP pipeline.

Loads the Figure 2 problem definition (fig2_problem.json), builds the SMDP
environment, and solves it using three methods:
  1. Heuristic solvers (FIFO, SPT, Random)
  2. Approximate solver (Q-Learning)
  3. Exact solver (Value Iteration)

Compares results across all methods.
"""

import sys
import os
import time
import random
import json
from datetime import datetime

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_ER_PAPER_DIR = os.path.dirname(_CODE_DIR)
sys.path.insert(0, _CODE_DIR)
sys.path.insert(0, os.path.dirname(_ER_PAPER_DIR))

from smdp_env import SMDPEnv
from solvers import (
    FIFOPolicy, ShortestProcessingTimePolicy, RandomPolicy,
    QLearningAgent, ValueIterationSolver
)


def evaluate_policy(env, policy_fn, n_episodes=100, label="Policy"):
    """Evaluate a policy over n_episodes and return statistics."""
    rewards = []
    cycle_times = []
    for ep in range(n_episodes):
        reward, info = env.run_with_policy(policy_fn, seed=1000 + ep)
        rewards.append(reward)
        cycle_times.append(info["total_cycle_time"])
    avg_reward = sum(rewards) / len(rewards)
    avg_ct = sum(cycle_times) / len(cycle_times)
    std_ct = (sum((ct - avg_ct)**2 for ct in cycle_times) / len(cycle_times)) ** 0.5
    print(f"  {label:30s} | avg cycle time: {avg_ct:8.2f} +/- {std_ct:6.2f} | "
          f"step reward: {avg_reward:10.2f} | {n_episodes} episodes")
    return {"avg_reward": avg_reward, "avg_cycle_time": avg_ct, "std_cycle_time": std_ct}


def main():
    json_path = os.path.join(_ER_PAPER_DIR, "models", "fig2_problem.json")

    with open(json_path) as f:
        spec = json.load(f)

    print("=" * 80)
    print("BPMN+OPT -> SMDP Pipeline Demo")
    print(f"Problem: {spec['name']}")
    print(f"Horizon: {spec['smdp']['horizon']}")
    print("=" * 80)

    # ------------------------------------------------------------------
    # 1. HEURISTIC SOLVERS
    # ------------------------------------------------------------------
    print("\n--- 1. Heuristic Solvers ---\n")

    env = SMDPEnv(json_path=json_path)
    results = {}

    fifo = FIFOPolicy()
    results["FIFO"] = evaluate_policy(env, fifo, n_episodes=100, label="FIFO")

    spt = ShortestProcessingTimePolicy(spec)
    results["SPT"] = evaluate_policy(env, spt, n_episodes=100, label="Shortest Processing Time")

    rand_pol = RandomPolicy()
    results["Random"] = evaluate_policy(env, rand_pol, n_episodes=100, label="Random")

    # ------------------------------------------------------------------
    # 2. APPROXIMATE SOLVER — Q-Learning
    # ------------------------------------------------------------------
    print("\n--- 2. Approximate Solver (Q-Learning) ---\n")

    print("  Training Q-learning agent...")
    t0 = time.time()
    agent = QLearningAgent(spec, alpha=0.05, gamma=1.0, epsilon=0.5,
                           epsilon_decay=0.997, min_epsilon=0.01)
    train_env = SMDPEnv(json_path=json_path)
    agent.train(train_env, n_episodes=1000, verbose=True)
    t_train = time.time() - t0
    print(f"  Training time: {t_train:.1f}s | Q-table entries: {len(agent.q_table)}")

    print("\n  Evaluating learned policy...")
    eval_env = SMDPEnv(json_path=json_path)
    results["Q-Learning"] = evaluate_policy(eval_env, agent.policy(), n_episodes=100,
                                            label="Q-Learning (greedy)")

    # ------------------------------------------------------------------
    # 3. EXACT SOLVER — Value Iteration
    # ------------------------------------------------------------------
    print("\n--- 3. Exact Solver (Value Iteration) ---\n")

    t0 = time.time()
    vi_solver = ValueIterationSolver(spec, gamma=1.0, theta=1e-6, max_iter=1000)
    vi_env = SMDPEnv(json_path=json_path)
    vi_solver.collect_samples(vi_env, n_episodes=1000, verbose=True)
    vi_solver.solve(verbose=True)
    t_vi = time.time() - t0
    print(f"  Value iteration time: {t_vi:.1f}s")

    print("\n  Evaluating VI policy...")
    vi_eval_env = SMDPEnv(json_path=json_path)
    results["Value Iteration"] = evaluate_policy(vi_eval_env, vi_solver.policy(),
                                                  n_episodes=100,
                                                  label="Value Iteration (greedy)")

    # ------------------------------------------------------------------
    # COMPARISON
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    method_order = ["FIFO", "SPT", "Random", "Q-Learning", "Value Iteration"]
    print(f"\n  {'Method':30s} | {'Avg Cycle Time':>15s} | {'Std':>8s} | {'Avg Reward':>12s}")
    print("  " + "-" * 74)
    for name in method_order:
        r = results[name]
        print(f"  {name:30s} | {r['avg_cycle_time']:15.2f} | {r['std_cycle_time']:8.2f} | {r['avg_reward']:12.2f}")

    best = min(results.items(), key=lambda x: x[1]["avg_cycle_time"])
    print(f"\n  Best method: {best[0]} (avg cycle time: {best[1]['avg_cycle_time']:.2f})")
    print("=" * 80)

    # ------------------------------------------------------------------
    # SAVE RESULTS TO MARKDOWN
    # ------------------------------------------------------------------
    output_dir = os.path.join(_CODE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, "fig2_results.md")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Evaluation Results: {spec['name']}",
        "",
        f"**Generated:** {timestamp}  ",
        f"**Horizon:** {spec['smdp']['horizon']}  ",
        f"**Discount:** {spec['smdp']['discount']}  ",
        f"**Evaluation episodes:** 100 per method  ",
        f"**Q-Learning training episodes:** 1000  ",
        f"**Value Iteration sample episodes:** 1000  ",
        "",
        "## Comparison Summary",
        "",
        "| Method | Avg Cycle Time | Std | Avg Reward |",
        "|--------|---------------:|----:|-----------:|",
    ]
    for name in method_order:
        r = results[name]
        lines.append(
            f"| {name} | {r['avg_cycle_time']:.2f} | {r['std_cycle_time']:.2f} | {r['avg_reward']:.2f} |"
        )
    lines += [
        "",
        f"**Best method:** {best[0]} (avg cycle time: {best[1]['avg_cycle_time']:.2f})",
        "",
        "## Method Details",
        "",
        "### 1. Heuristic Solvers",
        "",
        "- **FIFO** — Assign the longest-waiting patient to the first available resource.",
        "- **SPT** — Assign the (patient, resource) pair with shortest expected processing time.",
        "- **Random** — Uniformly random assignment.",
        "",
        "### 2. Q-Learning (Approximate)",
        "",
        f"- Alpha: 0.05, Gamma: 1.0, Epsilon: 0.5 → {agent.epsilon:.4f} (decayed)",
        f"- Q-table size: {len(agent.q_table)} entries",
        f"- Training time: {t_train:.1f}s",
        "",
        "### 3. Value Iteration (Exact)",
        "",
        f"- Abstract states discovered: {len(vi_solver.state_actions)}",
        f"- State-action pairs: {sum(len(a) for a in vi_solver.state_actions.values())}",
        f"- Convergence: {vi_solver.max_iter} max iterations, theta={vi_solver.theta}",
        f"- Solve time: {t_vi:.1f}s",
        "",
        "## Reward Semantics",
        "",
        "Step reward = −∫ n(t) dt over the holding interval between decision epochs,",
        "where n(t) is the number of patients in the system at time t.",
        "This equals the cycle-time contribution of each interval.",
        "",
    ]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Results saved to: {md_path}")


if __name__ == "__main__":
    main()
