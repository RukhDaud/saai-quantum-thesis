"""Result figures for Chapters 4-6, generated from the result files (PNG for the thesis, SVG for editing).

    python make_results_figures.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PB = os.path.join(HERE, "..", "phaseB_qubo_scenario_selection", "results")
PC = os.path.join(HERE, "..", "phaseC_simulation", "results")
OUT = os.path.join(HERE, "results_figures")
os.makedirs(OUT, exist_ok=True)

# validated categorical palette (reference instance, light mode), fixed order
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
METHODS = [("greedy", "Greedy", "o"), ("qaoa", "QAOA (p = 2)", "s"), ("exhaustive", "Exact QUBO optimum", "D"),
           ("ga", "Genetic algorithm", "^"), ("sa", "Simulated annealing", "v"), ("random", "Random", "X")]
COLOR = {m: C[i] for i, (m, _, _) in enumerate(METHODS)}
LABEL = {m: l for m, l, _ in METHODS}
MARK = {m: k for m, _, k in METHODS}

plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
                     "font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": 300})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name + ".png"), bbox_inches="tight", facecolor="white")
    fig.savefig(os.path.join(OUT, name + ".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", name)


def bar_labels(ax, bars, fmt):
    for b in bars:
        ax.annotate(fmt.format(b.get_height()), (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, color=INK)


# ---------- Fig A: alignment of the QUBO with true coverage ----------
def fig_alignment():
    d = pd.read_csv(os.path.join(PB, "alignment_eval.csv"))
    d["obj"] = d.objective.map(lambda s: "v1" if s.startswith("v1") else ("v2" if "beta=1.0" in s else None))
    d = d.dropna(subset=["obj"])
    s = d.groupby(["n", "obj"]).regret.apply(lambda r: (r < 1e-12).mean() * 100).unstack()
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    x = np.arange(len(s))
    w = 0.36
    b1 = ax.bar(x - w / 2 - 0.01, s["v1"], w, color=C[1], label="First formulation", edgecolor="white", linewidth=1)
    b2 = ax.bar(x + w / 2 + 0.01, s["v2"], w, color=C[0], label="Coverage-aligned formulation", edgecolor="white",
                linewidth=1, hatch="//")
    bar_labels(ax, b1, "{:.1f}%")
    bar_labels(ax, b2, "{:.0f}%")
    ax.set_xticks(x, [f"n = {n}" for n in s.index])
    ax.set_ylabel("Instances where QUBO optimum\n= true coverage optimum (%)")
    ax.set_ylim(0, 112)
    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.16))
    save(fig, "fig_alignment")


# ---------- Fig B: median coverage by method and size (v1 and v2 panels) ----------
def fig_coverage():
    v1 = pd.read_csv(os.path.join(PB, "runs_full.csv"))
    v2 = pd.read_csv(os.path.join(PB, "runs_v2_full.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True)
    for ax, d, title in ((axes[0], v1, "First formulation"), (axes[1], v2, "Coverage-aligned formulation")):
        g = d.groupby(["method", "n"]).pairwise_cov.median().unstack() * 100
        for m, _, _ in METHODS:
            ax.plot(g.columns, g.loc[m], color=COLOR[m], marker=MARK[m], markersize=6, linewidth=1.6, label=LABEL[m])
        ax.set_title(title, fontsize=10, color=INK)
        ax.set_xticks([12, 16, 20])
        ax.set_xlabel("Candidate scenarios (n)")
    axes[0].set_ylabel("Median pairwise coverage (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.1))
    save(fig, "fig_coverage")


# ---------- Fig C: QAOA minus greedy, per instance, v1 vs v2 ----------
def fig_qaoa_diff():
    rows = []
    for f, form in (("runs_full.csv", "First"), ("runs_v2_full.csv", "Coverage-aligned")):
        d = pd.read_csv(os.path.join(PB, f))
        p = d.pivot_table(index=["n", "seed"], columns="method", values="pairwise_cov")
        diff = ((p["qaoa"] - p["greedy"]) * 100).reset_index().rename(columns={0: "diff"})
        diff.columns = ["n", "seed", "diff"]
        diff["form"] = form
        rows.append(diff)
    d = pd.concat(rows)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    pos, data, cols, labels = [], [], [], []
    for i, n in enumerate((12, 16, 20)):
        for j, (form, col) in enumerate((("First", C[1]), ("Coverage-aligned", C[0]))):
            pos.append(i * 3 + j)
            data.append(d[(d.n == n) & (d.form == form)]["diff"].values)
            cols.append(col)
    bp = ax.boxplot(data, positions=pos, widths=0.7, patch_artist=True, showfliers=True,
                    medianprops=dict(color=INK, linewidth=1.4), flierprops=dict(marker="o", markersize=3, markerfacecolor=INK2, markeredgecolor="none"))
    for patch, col, k in zip(bp["boxes"], cols, range(len(cols))):
        patch.set_facecolor(col)
        patch.set_edgecolor("white")
        if k % 2 == 1:
            patch.set_hatch("//")
    ax.axhline(0, color=INK2, linewidth=0.9)
    ax.set_xticks([0.5, 3.5, 6.5], ["n = 12", "n = 16", "n = 20"])
    ax.set_ylabel("QAOA minus greedy\npairwise coverage (points)")
    from matplotlib.patches import Patch
    ax.legend([Patch(facecolor=C[1]), Patch(facecolor=C[0], hatch="//")], ["First formulation", "Coverage-aligned"],
              loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.15))
    save(fig, "fig_qaoa_vs_greedy")


# ---------- Fig D: QAOA simulation time and optimum-hit rate (two panels, no dual axis) ----------
def fig_qaoa_cost():
    d = pd.read_csv(os.path.join(PB, "runs_v2_full.csv"))
    q = d[d.method == "qaoa"]
    t = q.groupby("n").seconds.median()
    hit = d.groupby(["method", "n"]).energy_gap.apply(lambda s: (s.abs() < 1e-3).mean() * 100).unstack()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
    axes[0].plot(t.index, t.values, color=C[1], marker="s", markersize=7, linewidth=1.6)
    axes[0].set_yscale("log")
    for n, v in t.items():
        axes[0].annotate(f"{v:.1f} s" if v < 100 else f"{v / 60:.1f} min", (n, v), xytext=(6, -2), textcoords="offset points", fontsize=8.5, color=INK)
    axes[0].set_xticks([12, 16, 20])
    axes[0].set_xlabel("Candidate scenarios (n) = qubits")
    axes[0].set_ylabel("Median QAOA simulation time (s, log)")
    for m in ("ga", "qaoa", "sa"):
        axes[1].plot(hit.columns, hit.loc[m], color=COLOR[m], marker=MARK[m], markersize=6, linewidth=1.6, label=LABEL[m])
    axes[1].set_xticks([12, 16, 20])
    axes[1].set_ylim(-5, 105)
    axes[1].set_xlabel("Candidate scenarios (n)")
    axes[1].set_ylabel("Instances reaching QUBO optimum (%)")
    axes[1].legend(loc="center right", fontsize=8.5)
    save(fig, "fig_qaoa_cost")


# ---------- Fig E: scaling ----------
def fig_scaling():
    d = pd.read_csv(os.path.join(PB, "large_v2.csv"))
    g = d.groupby(["method", "n"]).gap_to_optimum.mean().unstack() * 100
    show = [("greedy", "Greedy", C[0], "o"), ("decomp_exact", "Decomposition, exact sub-QUBOs", C[2], "D"),
            ("decomp_qaoa", "Decomposition, QAOA sub-QUBOs", C[1], "s"), ("ga", "Genetic algorithm", C[3], "^"),
            ("sa", "Simulated annealing", C[4], "v")]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for m, lab, col, mk in show:
        ax.plot(g.columns, g.loc[m], color=col, marker=mk, markersize=6, linewidth=1.6, label=lab)
    ax.set_xticks([50, 100, 200])
    ax.set_xlabel("Candidate scenarios (n)")
    ax.set_ylabel("Mean shortfall from reference\noptimum (percentage points)")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.25), fontsize=8.5)
    save(fig, "fig_scaling")


# ---------- Fig F: change-aware re-selection ----------
def fig_change():
    d = pd.concat([pd.read_csv(os.path.join(PB, "change_rq4.csv")), pd.read_csv(os.path.join(PB, "change_rq4_part2.csv"))])
    d = d.drop_duplicates(["n", "seed", "change", "method"])
    order = [("keep_old", "Retain previous"), ("full_exact", "Full re-selection"), ("aware_exact", "Change-aware (exact)"),
             ("aware_qaoa", "Change-aware (QAOA)")]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
    for ax, metric, ylab, scale in ((axes[0], "feasible", "Changes with every obligation\nexercised (%)", 100),
                                    (axes[1], "churn", "Mean scenarios replaced", 1)):
        x = np.arange(len(order))
        for j, (n, col, hatch) in enumerate(((16, C[0], ""), (20, C[1], "//"))):
            vals = [d[(d.n == n) & (d.method == m)][metric].mean() * scale for m, _ in order]
            bars = ax.bar(x + (j - 0.5) * 0.38, vals, 0.36, color=col, hatch=hatch, edgecolor="white", linewidth=1,
                          label=f"n = {n}")
            bar_labels(ax, bars, "{:.0f}" if scale == 100 else "{:.2f}")
        ax.set_xticks(x, [l for _, l in order], rotation=20, ha="right", fontsize=8.5)
        ax.set_ylabel(ylab)
    axes[0].set_ylim(80, 103)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.07), fontsize=8.5)
    save(fig, "fig_change")


# ---------- Fig G: change sensitivity ----------
def fig_change_sens():
    s = pd.read_csv(os.path.join(PB, "change_sensitivity_summary.csv"))
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    for (m, col, mk) in ((8, C[0], "o"), (12, C[1], "s"), (14, C[2], "D")):
        g = s[s.m == m]
        ax.plot(g.mu, g.churn, color=col, marker=mk, markersize=6, linewidth=1.6, label=f"m = {m} free variables")
    ax.set_xlabel("Stability weight μ")
    ax.set_ylabel("Mean scenarios replaced")
    ax.legend(fontsize=8.5)
    save(fig, "fig_change_sensitivity")


# ---------- Fig H: kill matrix ----------
def fig_kill():
    k = pd.read_csv(os.path.join(PC, "fdm_kill_matrix.csv"), dtype={"speed_kmh": str})
    muts = [c for c in k.columns if c.startswith("M")]
    lab = k.apply(lambda r: f"{r.precipitation.replace('none', 'dry')} / {r.visibility} / {r.speed_kmh}", axis=1)
    m = k[muts].values
    fig, ax = plt.subplots(figsize=(6.4, 7.2))
    ax.imshow(m, cmap=matplotlib.colors.ListedColormap(["#f2f1ed", "#256abf"]), aspect="auto")
    ax.set_xticks(range(len(muts)), [x.split("_")[0] for x in muts])
    ax.set_yticks(range(len(lab)), lab, fontsize=8)
    ax.grid(False)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if m[i, j]:
                ax.text(j, i, "x", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
    ax.set_xlabel("Planted fault")
    ax.set_ylabel("Logical scenario (precipitation / visibility / speed km/h)")
    ax.set_xticks(np.arange(-0.5, len(muts)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(lab)), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="minor", length=0)
    save(fig, "fig_kill_matrix")


# ---------- Fig I: mutation score by method with best achievable ----------
def fig_mutation():
    r = pd.read_csv(os.path.join(PC, "fdm_scores.csv"))
    r = r[r.formulation == "v2"]
    ub = pd.read_csv(os.path.join(PC, "fdm_upper_bound.csv")).groupby("n").best.mean()
    g = r.groupby(["method", "n"]).mutation_score.mean().unstack()
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ns = [12, 16, 20]
    x = np.arange(len(ns))
    w = 0.13
    for i, (m, lab, _) in enumerate(METHODS):
        ax.bar(x + (i - 2.5) * (w + 0.01), g.loc[m, ns] * 100, w, color=COLOR[m], edgecolor="white", linewidth=0.8,
               label=lab, hatch="xx" if m == "random" else "")
    for j, n in enumerate(ns):
        ax.hlines(ub[n] * 100, j - 0.45, j + 0.45, colors=INK, linestyles="--", linewidth=1.2)
        ax.annotate(f"best achievable {ub[n] * 100:.1f}%", (j, ub[n] * 100), xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=8, color=INK)
    ax.set_xticks(x, [f"n = {n}" for n in ns])
    ax.set_ylim(70, 100)
    ax.set_ylabel("Mean mutation score (%)")
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.22), fontsize=8.5)
    save(fig, "fig_mutation_score")


# ---------- Fig J: coverage vs mutation score ----------
def fig_cov_vs_ms():
    r = pd.read_csv(os.path.join(PC, "fdm_scores.csv"))
    r = r[(r.formulation == "v2") & (r.n == 16)]
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    for m, lab, mk in METHODS:
        s = r[r.method == m]
        ax.scatter(s.pairwise_cov * 100, s.mutation_score * 100 + rng.uniform(-1.2, 1.2, len(s)), s=22, color=COLOR[m],
                   marker=mk, label=lab, edgecolors="white", linewidths=0.6, alpha=0.9)
    ax.set_xlabel("Pairwise coverage (%)")
    ax.set_ylabel("Mutation score (%, jittered)")
    ax.legend(loc="lower right", fontsize=8, ncol=2)
    save(fig, "fig_coverage_vs_faults")


# ---------- Fig K: friction sensitivity ----------
def fig_friction():
    d = pd.read_csv(os.path.join(PC, "friction_sensitivity.csv"))
    g = d.groupby(["setting", "method"]).mutation_score.mean().unstack() * 100
    order = ["lower", "midpoint", "upper"]
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    for m, lab, mk in METHODS:
        ax.plot(range(3), g.loc[order, m], color=COLOR[m], marker=mk, markersize=6, linewidth=1.6, label=lab)
    ax.set_xticks(range(3), ["Lower bound\n(wet 0.40, snow 0.24)", "Midpoint\n(wet 0.525, snow 0.32)", "Upper bound\n(wet 0.65, snow 0.40)"], fontsize=8.5)
    ax.set_ylabel("Mean mutation score (%),\naveraged over n = 12, 16, 20")
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.25), fontsize=8.5)
    save(fig, "fig_friction_sensitivity")


# ---------- Fig: scenarios by number of predicates exercised ----------
def fig_predicates():
    import itertools, sys
    sys.path.insert(0, os.path.join(HERE, "..", "phaseB_qubo_scenario_selection"))
    from qsel.odd_space import DIMENSIONS, DIM_NAMES, PREDICATES
    space = [dict(zip(DIM_NAMES, v)) for v in itertools.product(*DIMENSIONS.values())]
    cnt = np.bincount([sum(f(s) for _, _, f in PREDICATES) for s in space], minlength=9)
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    b = ax.bar(np.arange(9), cnt, 0.7, color=C[0], edgecolor="white", linewidth=1)
    bar_labels(ax, b, "{:.0f}")
    ax.set_xticks(np.arange(9))
    ax.set_xlabel("Number of boundary predicates exercised by the scenario")
    ax.set_ylabel("Scenarios (of 972)")
    ax.set_ylim(0, cnt.max() * 1.15)
    save(fig, "fig_predicates")


# ---------- Fig: per-instance coverage distribution by method ----------
def fig_cov_dist():
    v2 = pd.read_csv(os.path.join(PB, "runs_v2_full.csv"))
    order = ["random", "greedy", "sa", "qaoa", "ga", "exhaustive"]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.4), sharey=False)
    for ax, n in zip(axes, (12, 16, 20)):
        data = [v2[(v2.n == n) & (v2.method == m)].pairwise_cov.values * 100 for m in order]
        bp = ax.boxplot(data, patch_artist=True, widths=0.6, medianprops={"color": INK, "linewidth": 1.4},
                        flierprops={"marker": "o", "markersize": 3, "markerfacecolor": INK2, "markeredgecolor": INK2})
        for patch, m in zip(bp["boxes"], order):
            patch.set_facecolor(COLOR[m]); patch.set_alpha(0.55); patch.set_edgecolor(INK2)
        ax.set_xticks(range(1, 7), ["Rand.", "Greedy", "SA", "QAOA", "GA", "Exact"], rotation=45, fontsize=8.5)
        ax.set_title(f"n = {n}", fontsize=10, color=INK)
    axes[0].set_ylabel("Pairwise coverage (%)")
    save(fig, "fig_cov_dist")


# ---------- Fig: change study by clause change ----------
def fig_change_type():
    ch = pd.concat([pd.read_csv(os.path.join(PB, "change_rq4.csv")), pd.read_csv(os.path.join(PB, "change_rq4_part2.csv"))])
    ch = ch[ch.n == 16]
    ch["cid"] = ch.change.str[:3]
    strat = [("keep_old", "Retain previous", C[5]), ("full_exact", "Full re-selection (exact)", C[1]),
             ("aware_qaoa", "Change-aware (QAOA)", C[4]), ("aware_exact", "Change-aware (exact)", C[0])]
    g = ch.groupby(["cid", "method"]).feasible.mean().unstack() * 100
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    x = np.arange(len(g)); w = 0.2
    hat = ["", "//", "..", "xx"]
    for i, (m, lab, col) in enumerate(strat):
        ax.bar(x + (i - 1.5) * w, g[m], w * 0.95, color=col, label=lab, edgecolor="white", linewidth=0.8, hatch=hat[i])
    ax.set_xticks(x, g.index)
    ax.set_ylabel("Changes with every obligation\nexercised (%)")
    ax.set_ylim(60, 104)
    ax.legend(loc="lower center", ncol=2, fontsize=8.5, bbox_to_anchor=(0.5, 1.0))
    save(fig, "fig_change_type")


if __name__ == "__main__":
    for f in (fig_alignment, fig_coverage, fig_qaoa_diff, fig_qaoa_cost, fig_scaling, fig_change, fig_change_sens,
              fig_kill, fig_mutation, fig_cov_vs_ms, fig_friction, fig_predicates, fig_cov_dist, fig_change_type):
        f()
