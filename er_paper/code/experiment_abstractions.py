"""
Experiment: Heuristic baselines + learning solvers across abstraction levels.
K independent replications per configuration for statistical rigor.

For each model, evaluates:
  - All applicable heuristics (FIFO, SPT, Clinical, ShortQ, Stagger+SPT, Random)
  - Q-Learning and Value Iteration at each abstraction level
  - K=5 replications, N_EVAL episodes each

Outputs: Markdown report + self-contained HTML with tables.
"""
import sys, os, time, copy, json, datetime, math
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _CODE_DIR)
sys.path.insert(0, os.path.join(os.path.dirname(_CODE_DIR), ".."))

from smdp_env import SMDPEnv, ABSTRACTION_LEVELS
from solvers import (build_heuristics, FIFOPolicy,
                     QLearningAgent, ValueIterationSolver)

K = 5             # independent replications per config
N_EVAL = 30       # eval episodes per replication
FIG2_PATH = os.path.join(os.path.dirname(_CODE_DIR), "models", "fig2_problem.json")
FIG1_PATH = os.path.join(os.path.dirname(_CODE_DIR), "models", "fig1_problem.json")
OUTPUT_DIR = os.path.join(_CODE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


T_CRIT = {
    2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
    7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 15: 2.145,
    20: 2.093, 30: 2.045, 50: 2.009, 100: 1.984,
}


def t_critical(n):
    """t-critical value for 95% CI with n-1 degrees of freedom."""
    df = n - 1
    if df <= 0:
        return float("inf")
    if n in T_CRIT:
        return T_CRIT[n]
    for k in sorted(T_CRIT):
        if k >= n:
            return T_CRIT[k]
    return 1.96


def mean_ci(values, confidence=0.95):
    """Return (mean, half-width of 95% CI) using t-distribution."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mu = sum(values) / n
    if n == 1:
        return mu, float("inf")
    var = sum((x - mu) ** 2 for x in values) / (n - 1)
    se = math.sqrt(var / n)
    hw = t_critical(n) * se
    return mu, hw


def mean_std(values):
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mu = sum(values) / n
    if n == 1:
        return mu, 0.0
    var = sum((x - mu) ** 2 for x in values) / (n - 1)
    return mu, math.sqrt(var)


def eval_heuristics(spec, horizons, label):
    """Evaluate all applicable heuristics.
    Returns dict[h][name] = (mean, ci_hw, std) where ci_hw is the 95% CI half-width
    computed over K replication means."""
    heuristics = build_heuristics(spec)
    results = {}

    for h in horizons:
        s = copy.deepcopy(spec)
        s["smdp"]["horizon"] = h
        results[h] = {}

        for hname, hpol in heuristics.items():
            rep_means = []
            for k in range(K):
                cts_k = []
                for ep in range(N_EVAL):
                    seed = 1000 * k + ep
                    env = SMDPEnv(spec_dict=s)
                    _, info = env.run_with_policy(hpol, seed=seed)
                    cts_k.append(info["total_cycle_time"])
                rep_means.append(sum(cts_k) / len(cts_k))
            mu, hw = mean_ci(rep_means)
            _, sd = mean_std(rep_means)
            results[h][hname] = (mu, hw, sd)
            print(f"  {label} h={h} {hname}: {mu:.1f} [{mu-hw:.1f}, {mu+hw:.1f}]", flush=True)

        fifo = FIFOPolicy()
        env_ref = SMDPEnv(spec_dict=s)
        env_ref.reset(seed=42)
        while not env_ref.done:
            actions = env_ref.get_actions()
            if not actions:
                break
            env_ref.step(fifo(None, actions, env_ref))
        results[h]["_n_patients"] = env_ref.model.patient_counter[0]

    return results


def run_learning(spec, horizons, label, heur_results, abstraction_levels=[0, 1, 2, 3]):
    """Run QL and VI at each abstraction level. Compare to best heuristic."""
    results = []
    fifo = FIFOPolicy()

    for h in horizons:
        s = copy.deepcopy(spec)
        s["smdp"]["horizon"] = h
        n_patients = heur_results[h]["_n_patients"]

        best_heur_name = min(
            [k for k in heur_results[h] if not k.startswith("_")],
            key=lambda k: heur_results[h][k][0])
        best_heur_mean = heur_results[h][best_heur_name][0]

        for level in abstraction_levels:
            level_name = ABSTRACTION_LEVELS[level]
            print(f"  {label} h={h} L{level} ({level_name})...", end=" ", flush=True)
            t0_total = time.time()

            # Count states at this level
            env_c = SMDPEnv(spec_dict=s, abstraction_level=level)
            env_c.reset(seed=42)
            level_states = set()
            while not env_c.done:
                actions = env_c.get_actions()
                if not actions:
                    break
                level_states.add(env_c.abstract_state())
                env_c.step(fifo(None, actions, env_c))

            # K replications of QL
            ql_means = []
            ql_times = []
            n_train_ql = min(3000, max(300, int(80 * h / 6)))
            for k in range(K):
                t0 = time.time()
                try:
                    agent = QLearningAgent(s, alpha=0.1, gamma=1.0, epsilon=0.3,
                                           epsilon_decay=0.998, min_epsilon=0.01)
                    train_env = SMDPEnv(spec_dict=s, abstraction_level=level)
                    agent.train(train_env, n_episodes=n_train_ql, verbose=False)
                    ql_times.append(time.time() - t0)
                    ql_pol = agent.policy()
                    cts = []
                    for ep in range(N_EVAL):
                        env_e = SMDPEnv(spec_dict=s, abstraction_level=level)
                        _, info_e = env_e.run_with_policy(ql_pol, seed=1000 * k + ep)
                        cts.append(info_e["total_cycle_time"])
                    ql_means.append(sum(cts) / len(cts))
                except Exception as e:
                    ql_times.append(time.time() - t0)
                    print(f"QL err k={k}: {e}", end=" ")

            # K replications of VI
            vi_means = []
            vi_times = []
            vi_state_counts = []
            n_vi_eps = min(1500, max(150, int(50 * h / 6)))
            for k in range(K):
                t0 = time.time()
                try:
                    vi = ValueIterationSolver(s, gamma=1.0, theta=1e-3, max_iter=300)
                    vi_env = SMDPEnv(spec_dict=s, abstraction_level=level)
                    vi.collect_samples(vi_env, n_episodes=n_vi_eps, verbose=False)
                    vi.solve(verbose=False)
                    vi_times.append(time.time() - t0)
                    vi_state_counts.append(len(vi.state_actions))
                    vi_pol = vi.policy()
                    cts = []
                    for ep in range(N_EVAL):
                        env_e = SMDPEnv(spec_dict=s, abstraction_level=level)
                        _, info_e = env_e.run_with_policy(vi_pol, seed=1000 * k + ep)
                        cts.append(info_e["total_cycle_time"])
                    vi_means.append(sum(cts) / len(cts))
                except Exception as e:
                    vi_times.append(time.time() - t0)
                    print(f"VI err k={k}: {e}", end=" ")

            ql_mu, ql_hw = mean_ci(ql_means) if ql_means else (None, None)
            vi_mu, vi_hw = mean_ci(vi_means) if vi_means else (None, None)
            _, ql_sd = mean_std(ql_means) if ql_means else (None, None)
            _, vi_sd = mean_std(vi_means) if vi_means else (None, None)
            ql_pct = ((ql_mu / best_heur_mean - 1) * 100) if ql_mu and best_heur_mean else None
            vi_pct = ((vi_mu / best_heur_mean - 1) * 100) if vi_mu and best_heur_mean else None

            results.append({
                "figure": label, "horizon": h, "n_patients": n_patients,
                "level": level, "level_name": level_name,
                "n_states": len(level_states),
                "best_heur": best_heur_name, "best_heur_mean": best_heur_mean,
                "ql_mean": ql_mu, "ql_ci": ql_hw, "ql_std": ql_sd, "ql_pct": ql_pct,
                "ql_time": mean_std(ql_times)[0],
                "vi_mean": vi_mu, "vi_ci": vi_hw, "vi_std": vi_sd, "vi_pct": vi_pct,
                "vi_time": mean_std(vi_times)[0],
            })

            elapsed = time.time() - t0_total
            ql_s = f"{ql_mu:.1f} [{ql_mu-ql_hw:.1f},{ql_mu+ql_hw:.1f}] ({ql_pct:+.1f}%)" if ql_mu else "FAIL"
            vi_s = f"{vi_mu:.1f} [{vi_mu-vi_hw:.1f},{vi_mu+vi_hw:.1f}] ({vi_pct:+.1f}%)" if vi_mu else "FAIL"
            print(f"|S|={len(level_states)} | best={best_heur_name}({best_heur_mean:.1f}) | QL={ql_s} | VI={vi_s} [{elapsed:.0f}s]")
            sys.stdout.flush()

    return results


def generate_report(heur_by_fig, learn_by_fig):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    md = []
    md.append(f"# BPMN+OPT → SMDP Experiment (K={K} replications)\n")
    md.append(f"_Generated: {ts} | {N_EVAL} eval episodes per replication_\n")

    for fig_label in heur_by_fig:
        md.append(f"## {fig_label}\n")

        md.append("### Heuristic Baselines\n")
        md.append("| Horizon | Patients | Heuristic | Mean CT | 95% CI |")
        md.append("|---------|----------|-----------|--------:|-------:|")
        for h, hdata in sorted(heur_by_fig[fig_label].items()):
            n_pts = hdata.get("_n_patients", "?")
            sorted_heurs = sorted([k for k in hdata if not k.startswith("_")], key=lambda k: hdata[k][0])
            for hname in sorted_heurs:
                mu, hw, sd = hdata[hname]
                ci_s = f"[{mu-hw:.1f}, {mu+hw:.1f}]"
                md.append(f"| {h} | {n_pts} | **{hname}** | {mu:.1f} | {ci_s} |")
        md.append("")

        learn_rows = learn_by_fig.get(fig_label, [])
        if learn_rows:
            md.append("### Learning Solvers vs Best Heuristic\n")
            md.append("| Horizon | Level | |S| | Best Heur | QL Mean [95% CI] | QL Δ | VI Mean [95% CI] | VI Δ |")
            md.append("|---------|-------|-----|-----------|------------------|------|------------------|------|")
            for r in learn_rows:
                if r['ql_mean']:
                    ql_s = f"{r['ql_mean']:.1f} [{r['ql_mean']-r['ql_ci']:.1f}, {r['ql_mean']+r['ql_ci']:.1f}]"
                else:
                    ql_s = "FAIL"
                if r['vi_mean']:
                    vi_s = f"{r['vi_mean']:.1f} [{r['vi_mean']-r['vi_ci']:.1f}, {r['vi_mean']+r['vi_ci']:.1f}]"
                else:
                    vi_s = "FAIL"
                ql_p = f"{r['ql_pct']:+.1f}%" if r['ql_pct'] is not None else "-"
                vi_p = f"{r['vi_pct']:+.1f}%" if r['vi_pct'] is not None else "-"
                md.append(f"| {r['horizon']} | L{r['level']} ({r['level_name']}) | {r['n_states']} "
                          f"| {r['best_heur']}({r['best_heur_mean']:.1f}) | {ql_s} | {ql_p} | {vi_s} | {vi_p} |")
            md.append("")

    md_text = "\n".join(md)
    md_path = os.path.join(OUTPUT_DIR, "experiment_results.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"\nMarkdown: {md_path}")

    html = generate_html(heur_by_fig, learn_by_fig, ts)
    html_path = os.path.join(OUTPUT_DIR, "experiment_results.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML: {html_path}")
    return md_path, html_path


def generate_html(heur_by_fig, learn_by_fig, ts):
    sections = ""
    for fig_label in heur_by_fig:
        heur_data = heur_by_fig[fig_label]

        heur_rows = ""
        for h in sorted(heur_data):
            hdata = heur_data[h]
            n_pts = hdata.get("_n_patients", "?")
            sorted_heurs = sorted([k for k in hdata if not k.startswith("_")], key=lambda k: hdata[k][0])
            best_name = sorted_heurs[0] if sorted_heurs else "?"
            for hname in sorted_heurs:
                mu, hw, sd = hdata[hname]
                cls = "best-heur" if hname == best_name else ""
                ci_s = f"<span class='ci'>[{mu-hw:.1f}, {mu+hw:.1f}]</span>"
                heur_rows += f'<tr><td>{h}</td><td>{n_pts}</td><td class="{cls}">{hname}</td><td>{mu:.1f} {ci_s}</td></tr>\n'

        learn_rows_html = ""
        learn_rows = learn_by_fig.get(fig_label, [])
        prev_h = None
        for r in learn_rows:
            if r['ql_mean']:
                ql_s = (f"{r['ql_mean']:.1f} <span class='ci'>"
                        f"[{r['ql_mean']-r['ql_ci']:.1f}, {r['ql_mean']+r['ql_ci']:.1f}]</span>")
            else:
                ql_s = "FAIL"
            if r['vi_mean']:
                vi_s = (f"{r['vi_mean']:.1f} <span class='ci'>"
                        f"[{r['vi_mean']-r['vi_ci']:.1f}, {r['vi_mean']+r['vi_ci']:.1f}]</span>")
            else:
                vi_s = "FAIL"
            def pct_cell(val):
                if val is None:
                    return '<td class="na">-</td>'
                cls = "better" if val < -1.0 else ("worse" if val > 1.0 else "neutral")
                return f'<td class="{cls}">{val:+.1f}%</td>'
            sep = ' class="sep"' if r['horizon'] != prev_h and prev_h is not None else ""
            prev_h = r['horizon']
            learn_rows_html += f"""<tr{sep}>
                <td>{r['horizon']}</td>
                <td><b>L{r['level']}</b> <span class="dim">({r['level_name']})</span></td>
                <td>{r['n_states']}</td>
                <td class="fifo">{r['best_heur']}({r['best_heur_mean']:.1f})</td>
                <td>{ql_s}</td>{pct_cell(r['ql_pct'])}
                <td>{vi_s}</td>{pct_cell(r['vi_pct'])}
            </tr>\n"""

        sections += f"""
        <h2>{fig_label}</h2>
        <h3>Heuristic Baselines</h3>
        <table class="heur-table"><thead><tr>
            <th>H</th><th>Pts</th><th>Heuristic</th><th>Mean CT [95% CI]</th>
        </tr></thead><tbody>{heur_rows}</tbody></table>

        <h3>Learning Solvers vs Best Heuristic</h3>
        <table><thead><tr>
            <th>H</th><th>Abstraction</th><th>|S|</th><th>Best Heur</th>
            <th>QL Mean [95% CI]</th><th>QL Δ</th><th>VI Mean [95% CI]</th><th>VI Δ</th>
        </tr></thead><tbody>{learn_rows_html}</tbody></table>
        """

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>BPMN+OPT SMDP Experiment</title>
<style>
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; max-width: 1400px; margin: 2em auto; padding: 0 1em; background: #fafafa; color: #222; }}
    h1 {{ border-bottom: 3px solid #2563eb; padding-bottom: 0.3em; }}
    h2 {{ color: #1e40af; margin-top: 2em; }}
    h3 {{ color: #475569; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.88em; }}
    th {{ background: #1e40af; color: white; padding: 8px 10px; text-align: left; white-space: nowrap; }}
    td {{ padding: 6px 10px; border-bottom: 1px solid #e5e7eb; }}
    tr:hover {{ background: #eff6ff; }}
    tr.sep td {{ border-top: 2px solid #93c5fd; }}
    .better {{ background: #dcfce7; color: #166534; font-weight: bold; }}
    .worse {{ background: #fee2e2; color: #991b1b; }}
    .neutral {{ background: #fef9c3; color: #854d0e; }}
    .na {{ color: #9ca3af; }}
    .dim {{ color: #6b7280; font-size: 0.85em; }}
    .sd {{ color: #9ca3af; font-size: 0.8em; }}
    .ci {{ color: #6b7280; font-size: 0.82em; }}
    .fifo {{ font-weight: bold; color: #1e40af; }}
    .best-heur {{ font-weight: bold; color: #166534; background: #dcfce7; }}
    .heur-table {{ max-width: 600px; }}
    .legend {{ display: flex; gap: 2em; margin: 1em 0; flex-wrap: wrap; }}
    .legend span {{ padding: 2px 10px; border-radius: 4px; font-size: 0.85em; }}
    .meta {{ color: #6b7280; font-size: 0.85em; }}
</style></head><body>
<h1>BPMN+OPT &rarr; SMDP Experiment</h1>
<p class="meta">Generated: {ts} &middot; K={K} replications &middot; {N_EVAL} eval episodes each &middot; 95% CI via t-distribution over K replication means</p>

<div class="legend">
    <span class="better">&#9660; &gt;1% better than best heuristic</span>
    <span class="worse">&#9650; &gt;1% worse</span>
    <span class="neutral">&#8776; within 1%</span>
</div>

{sections}

<h2>Notes</h2>
<ul>
<li>Heuristics are <b>composable</b>: each combines a scheduling, routing, and assignment sub-policy.</li>
<li>For Figure 2 (assignment only), scheduling and routing heuristics are not applicable.</li>
<li>QL/VI compare against the <b>best heuristic</b> at each horizon, not just FIFO.</li>
<li>Negative Δ = learning found a policy <b>better</b> than the best domain heuristic.</li>
</ul>
</body></html>"""


if __name__ == "__main__":
    print("=" * 80)
    print(f"BPMN+OPT SMDP Experiment (K={K} replications, {N_EVAL} eval eps)")
    print("=" * 80)

    with open(FIG2_PATH) as f:
        fig2_spec = json.load(f)
    with open(FIG1_PATH) as f:
        fig1_spec = json.load(f)

    heur_by_fig = {}
    learn_by_fig = {}

    print("\n=== Figure 2 (assignment only) ===")
    print("--- Heuristics ---")
    heur_by_fig["Figure 2"] = eval_heuristics(fig2_spec, [100, 200], "Fig2")
    print("--- Learning ---")
    learn_by_fig["Figure 2"] = run_learning(
        fig2_spec, [100, 200], "Fig2", heur_by_fig["Figure 2"],
        abstraction_levels=[0, 1, 2, 3])

    print("\n=== Figure 1 (scheduling + routing + assignment) ===")
    print("--- Heuristics ---")
    heur_by_fig["Figure 1"] = eval_heuristics(fig1_spec, [60, 120], "Fig1")
    print("--- Learning ---")
    learn_by_fig["Figure 1"] = run_learning(
        fig1_spec, [60, 120], "Fig1", heur_by_fig["Figure 1"],
        abstraction_levels=[0, 1, 2, 3])

    generate_report(heur_by_fig, learn_by_fig)
    print("\nDone!")
