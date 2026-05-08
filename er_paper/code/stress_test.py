"""Stress test: push Q-Learning and VI to the extreme (10x episodes)."""
import sys, os, time, json, random

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_ER_PAPER_DIR = os.path.dirname(_CODE_DIR)
sys.path.insert(0, _CODE_DIR)
sys.path.insert(0, os.path.dirname(_ER_PAPER_DIR))

from smdp_env import SMDPEnv
from solvers import (
    FIFOPolicy, ShortestProcessingTimePolicy, RandomPolicy,
    QLearningAgent, ValueIterationSolver
)

json_path = os.path.join(_ER_PAPER_DIR, "models", "fig2_problem.json")
with open(json_path) as f:
    spec = json.load(f)

N_EVAL = 500

def evaluate(env, pol, label):
    rewards, cts = [], []
    for ep in range(N_EVAL):
        r, info = env.run_with_policy(pol, seed=2000 + ep)
        rewards.append(r)
        cts.append(info["total_cycle_time"])
    avg_ct = sum(cts) / len(cts)
    std_ct = (sum((c - avg_ct)**2 for c in cts) / len(cts)) ** 0.5
    avg_r = sum(rewards) / len(rewards)
    print(f"  {label:35s} | ct={avg_ct:7.2f} +/- {std_ct:5.2f} | reward={avg_r:8.2f}")
    return avg_ct

print(f"Evaluation episodes: {N_EVAL}\n")

# Baselines
print("=== Heuristics ===")
env = SMDPEnv(json_path=json_path)
spt_ct = evaluate(env, ShortestProcessingTimePolicy(spec), "SPT")
evaluate(env, FIFOPolicy(), "FIFO")

# Q-Learning: 1k, 5k, 10k episodes
print("\n=== Q-Learning (scaling episodes) ===")
for n_ep in [1000, 5000, 10000]:
    t0 = time.time()
    agent = QLearningAgent(spec, alpha=0.02, gamma=1.0, epsilon=0.5,
                           epsilon_decay=0.9995, min_epsilon=0.005)
    train_env = SMDPEnv(json_path=json_path)
    agent.train(train_env, n_episodes=n_ep, verbose=False)
    dt = time.time() - t0
    eval_env = SMDPEnv(json_path=json_path)
    evaluate(eval_env, agent.policy(), f"Q-Learning ({n_ep} ep, {dt:.1f}s)")

# Value Iteration: 1k, 5k, 10k sample episodes
print("\n=== Value Iteration (scaling samples) ===")
for n_ep in [1000, 5000, 10000]:
    t0 = time.time()
    vi = ValueIterationSolver(spec, gamma=1.0, theta=1e-8, max_iter=5000)
    vi_env = SMDPEnv(json_path=json_path)
    vi.collect_samples(vi_env, n_episodes=n_ep, verbose=False)
    vi.solve(verbose=False)
    dt = time.time() - t0
    n_states = len(vi.state_actions)
    n_sa = sum(len(a) for a in vi.state_actions.values())
    eval_env = SMDPEnv(json_path=json_path)
    ct = evaluate(eval_env, vi.policy(), f"VI ({n_ep} ep, {n_states}s/{n_sa}sa, {dt:.1f}s)")

print(f"\nSPT baseline: {spt_ct:.2f}")
