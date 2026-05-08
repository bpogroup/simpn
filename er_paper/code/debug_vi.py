"""Debug script to trace VI decisions vs SPT."""
import sys, os
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_ER_PAPER_DIR = os.path.dirname(_CODE_DIR)
sys.path.insert(0, _CODE_DIR)
sys.path.insert(0, os.path.dirname(_ER_PAPER_DIR))

import json, random
from smdp_env import SMDPEnv
from solvers import ShortestProcessingTimePolicy, FIFOPolicy, ValueIterationSolver

json_path = os.path.join(_ER_PAPER_DIR, "models", "fig2_problem.json")
with open(json_path) as f:
    spec = json.load(f)

vi = ValueIterationSolver(spec, gamma=1.0, theta=1e-6, max_iter=1000)
vi_env = SMDPEnv(json_path=json_path)
vi.collect_samples(vi_env, n_episodes=1000, verbose=False)
vi.solve(verbose=False)

print("=== VI Value Table ===")
for state in sorted(vi.V.keys(), key=str):
    actions = vi.state_actions.get(state, set())
    print(f"  State {state}: V={vi.V[state]:.4f}")
    for a in sorted(actions, key=str):
        trans = vi.transitions.get((state, a), {})
        n_samples = sum(len(s) for s in trans.values())
        total_samples = max(n_samples, 1)
        q_val = 0.0
        for ns, samples in trans.items():
            prob = len(samples) / total_samples
            avg_r = sum(r for r, t in samples) / len(samples)
            avg_tau = sum(t for r, t in samples) / len(samples)
            q_val += prob * (avg_r + vi.V[ns])
        print(f"    Action {a}: Q={q_val:.4f} (n={n_samples})")

print("\n=== Side-by-side comparison (seed=1000) ===")
spt = ShortestProcessingTimePolicy(spec)
vi_pol = vi.policy()
fifo = FIFOPolicy()

for label, pol in [("SPT", spt), ("FIFO", fifo), ("VI", vi_pol)]:
    env = SMDPEnv(json_path=json_path)
    env.reset(seed=1000)
    decisions = []
    step_n = 0
    while not env.done:
        actions = env.get_actions()
        if not actions:
            break
        si = env.get_state_info()
        action = pol(env.get_state(), actions, env)

        abs_state = vi._abstract_state(env)
        abs_action = vi._abstract_action(action, env)

        _, reward, done, info = env.step(action)
        step_n += 1
        decisions.append((si["time"], action, abs_action, abs_state, reward, info.get("same_time", False)))

    ct = env.model.compute_total_cycle_time()
    print(f"\n{label}: cycle_time={ct:.2f}, total_decisions={len(decisions)}")
    print(f"  First 15 decisions:")
    for t, a, abs_a, abs_s, r, same in decisions[:15]:
        flag = " [same_time]" if same else ""
        print(f"    t={t:7.2f} | concrete={a} | abstract={abs_a} | state={abs_s} | r={r:8.2f}{flag}")
