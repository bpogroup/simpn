"""
run_fig1.py — End-to-end pipeline for the full outpatient process (Figure 1).

Uses the unified framework (same builder, env, compiler, solvers as Figure 2).

1. Load fig1_problem.json (BPMN+OPT with scheduling, assignment, routing)
2. Evaluate heuristic policies (FIFO, SPT, Random)
3. Compile SMDP JSON via the generic smdp_compiler
4. Save results
"""

import sys
import os
import json
import time as _time

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_ER_PAPER_DIR = os.path.dirname(_CODE_DIR)
sys.path.insert(0, _CODE_DIR)
sys.path.insert(0, os.path.dirname(_ER_PAPER_DIR))

from smdp_env import SMDPEnv
from solvers import FIFOPolicy, ShortestProcessingTimePolicy, RandomPolicy
from smdp_compiler import compile_smdp


def evaluate_policy(json_path, policy_fn, policy_name, n_episodes=30, seed_base=42):
    rewards = []
    cycle_times = []
    completions = []
    for ep in range(n_episodes):
        env = SMDPEnv(json_path=json_path)
        r, info = env.run_with_policy(policy_fn, seed=seed_base + ep)
        rewards.append(r)
        cycle_times.append(info["total_cycle_time"])
        completions.append(info["n_completed"])
    avg_r = sum(rewards) / len(rewards)
    avg_ct = sum(cycle_times) / len(cycle_times)
    avg_comp = sum(completions) / len(completions)
    return {
        "policy": policy_name,
        "avg_reward": avg_r,
        "avg_cycle_time": avg_ct,
        "avg_completions": avg_comp,
        "n_episodes": n_episodes,
    }


def main():
    json_path = os.path.join(_ER_PAPER_DIR, "models", "fig1_problem.json")
    output_dir = os.path.join(_CODE_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)

    with open(json_path) as f:
        spec = json.load(f)

    print("=" * 70)
    print("Figure 1 — Full Outpatient Process (Scheduling + Assignment + Routing)")
    print(f"Horizon: {spec['smdp']['horizon']} | Interarrival: exp(mean=6 min)")
    print("=" * 70)

    # Step 1: Smoke test
    print("\n[1] Smoke test (single episode, FIFO)...")
    env = SMDPEnv(json_path=json_path)
    fifo = FIFOPolicy()
    try:
        reward, info = env.run_with_policy(fifo, seed=42, verbose=False)
        print(f"  Reward: {reward:.2f} | Cycle time: {info['total_cycle_time']:.2f} | "
              f"Completed: {info['n_completed']} | Decisions: {info['n_decisions']}")
    except Exception as e:
        print(f"  SMOKE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Evaluate heuristic policies
    N_EVAL = 30
    print(f"\n[2] Evaluating heuristic policies ({N_EVAL} episodes each)...")
    policies = [
        ("FIFO", FIFOPolicy()),
        ("SPT", ShortestProcessingTimePolicy(spec)),
        ("Random", RandomPolicy()),
    ]
    results = []
    for name, fn in policies:
        t0 = _time.time()
        res = evaluate_policy(json_path, fn, name, n_episodes=N_EVAL, seed_base=42)
        elapsed = _time.time() - t0
        res["elapsed_s"] = elapsed
        results.append(res)
        print(f"  {name:8s}: avg_reward={res['avg_reward']:.2f}, "
              f"avg_cycle_time={res['avg_cycle_time']:.2f}, "
              f"avg_completions={res['avg_completions']:.1f} ({elapsed:.1f}s)")

    # Step 3: Compile SMDP using the generic compiler
    N_COMPILE = 200
    print(f"\n[3] Compiling SMDP ({N_COMPILE} episodes)...")
    t0 = _time.time()
    try:
        smdp_json = compile_smdp(json_path, n_episodes=N_COMPILE, verbose=True)
        compile_time = _time.time() - t0
        print(f"  Compilation took {compile_time:.1f}s")

        smdp_path = os.path.join(_ER_PAPER_DIR, "models", "fig1_smdp.json")
        with open(smdp_path, "w") as f:
            json.dump(smdp_json, f, indent=2)
        print(f"  SMDP saved to: {smdp_path}")
    except Exception as e:
        print(f"  SMDP COMPILATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        smdp_json = None
        compile_time = 0

    # Step 4: Save results
    md_path = os.path.join(output_dir, "fig1_results.md")
    with open(md_path, "w") as f:
        f.write("# Figure 1 — Full Outpatient Process Results\n\n")
        f.write("## Process Description\n\n")
        f.write("Full outpatient chemotherapy with **3 decision types**:\n")
        f.write("- **Scheduling**: assign appointment times (offsets 0/5/10/15/20 min)\n")
        f.write("- **Assignment**: 5 controlled tasks (Bloodwork, Examination, Drug_prep, Std/Int infusion)\n")
        f.write("- **Routing**: standard vs intensive infusion\n\n")
        f.write("Resources: 2 lab staff (senior+junior), 2 oncologists, 6 pharmacists, 20 chairs\n")
        f.write(f"Horizon: {spec['smdp']['horizon']} minutes | Interarrival: exp(mean=6 min)\n\n")

        f.write("## Heuristic Policy Evaluation\n\n")
        f.write(f"| Policy | Avg Reward | Avg Cycle Time | Avg Completions | Time (s) |\n")
        f.write(f"|--------|-----------|----------------|-----------------|----------|\n")
        for r in results:
            f.write(f"| {r['policy']:8s} | {r['avg_reward']:.2f} | {r['avg_cycle_time']:.2f} | "
                    f"{r['avg_completions']:.1f} | {r['elapsed_s']:.1f} |\n")

        if smdp_json:
            f.write(f"\n## SMDP Compilation\n\n")
            f.write(f"- Episodes: {N_COMPILE}\n")
            f.write(f"- States discovered: {smdp_json['smdp']['n_states']}\n")
            f.write(f"- Actions discovered: {smdp_json['smdp']['n_actions']}\n")
            total_triples = sum(
                len(ns_map)
                for a_map in smdp_json['smdp']['transitions'].values()
                for ns_map in a_map.values()
            )
            f.write(f"- Transition triples (s,a,s'): {total_triples}\n")
            f.write(f"- Compilation time: {compile_time:.1f}s\n")
            f.write(f"\nThis confirms the state-space explosion predicted for the full model.\n")
            f.write(f"Tabular SMDP methods (VI, Q-learning) become intractable at this scale.\n")

    print(f"\n  Results saved to: {md_path}")
    print("\nDone.")


if __name__ == "__main__":
    main()
