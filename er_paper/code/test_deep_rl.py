"""Quick test: DQN and PPO on Figure 2 (sanity check) then Figure 1."""
import sys, os, json, time
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _CODE_DIR)
sys.path.insert(0, os.path.join(os.path.dirname(_CODE_DIR), ".."))

from smdp_env import SMDPEnv
from solvers import FIFOPolicy, build_heuristics
from deep_solvers import DQNSolver, PPOSolver, FeatureExtractor

N_EVAL = 30

def evaluate(spec, policy_fn, label, n_eval=N_EVAL):
    cts = []
    for ep in range(n_eval):
        env = SMDPEnv(spec_dict=spec)
        _, info = env.run_with_policy(policy_fn, seed=ep)
        cts.append(info["total_cycle_time"])
    mu = sum(cts) / len(cts)
    print(f"  {label}: avg_ct={mu:.1f}")
    return mu


def test_model(spec, label, n_train_dqn=500, n_train_ppo=500):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    feat = FeatureExtractor(spec)
    print(f"  State dim: {feat.state_dim}, Action vocab: {feat.n_actions}")
    print(f"  Actions: {feat.action_vocab[:10]}{'...' if len(feat.action_vocab) > 10 else ''}")

    fifo = FIFOPolicy()
    fifo_ct = evaluate(spec, fifo, "FIFO")

    heuristics = build_heuristics(spec)
    best_name = "FIFO"
    best_ct = fifo_ct
    for hname, hpol in heuristics.items():
        if hname == "FIFO":
            continue
        ct = evaluate(spec, hpol, hname)
        if ct < best_ct:
            best_ct = ct
            best_name = hname
    print(f"  Best heuristic: {best_name} ({best_ct:.1f})")

    print(f"\n  Training DQN ({n_train_dqn} episodes)...")
    t0 = time.time()
    dqn = DQNSolver(spec, gamma=1.0, lr=1e-3, hidden=128,
                    epsilon_start=1.0, epsilon_end=0.05, epsilon_decay=0.995)
    dqn.train(n_episodes=n_train_dqn, verbose=True)
    dqn_time = time.time() - t0
    dqn_ct = evaluate(spec, dqn.policy(), "DQN")
    dqn_pct = (dqn_ct / best_ct - 1) * 100
    print(f"  DQN vs {best_name}: {dqn_pct:+.1f}% ({dqn_time:.1f}s)")

    print(f"\n  Training PPO ({n_train_ppo} episodes)...")
    t0 = time.time()
    ppo = PPOSolver(spec, gamma=1.0, lr=3e-4, hidden=128)
    ppo.train(n_episodes=n_train_ppo, update_every=10, verbose=True)
    ppo_time = time.time() - t0
    ppo_ct = evaluate(spec, ppo.policy(), "PPO")
    ppo_pct = (ppo_ct / best_ct - 1) * 100
    print(f"  PPO vs {best_name}: {ppo_pct:+.1f}% ({ppo_time:.1f}s)")

    print(f"\n  Summary for {label}:")
    print(f"    {best_name:15s}: {best_ct:.1f}")
    print(f"    {'DQN':15s}: {dqn_ct:.1f} ({dqn_pct:+.1f}%)")
    print(f"    {'PPO':15s}: {ppo_ct:.1f} ({ppo_pct:+.1f}%)")
    return best_ct, dqn_ct, ppo_ct


if __name__ == "__main__":
    FIG2_PATH = os.path.join(os.path.dirname(_CODE_DIR), "models", "fig2_problem.json")
    FIG1_PATH = os.path.join(os.path.dirname(_CODE_DIR), "models", "fig1_problem.json")

    with open(FIG2_PATH) as f:
        fig2 = json.load(f)
    fig2["smdp"]["horizon"] = 200

    test_model(fig2, "Figure 2 (h=200)", n_train_dqn=1000, n_train_ppo=1000)

    with open(FIG1_PATH) as f:
        fig1 = json.load(f)
    fig1["smdp"]["horizon"] = 60

    test_model(fig1, "Figure 1 (h=60)", n_train_dqn=1000, n_train_ppo=1000)
