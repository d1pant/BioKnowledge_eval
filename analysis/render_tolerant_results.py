"""Figure for the gfp_tolerant_site results. Reads Inspect logs; no model calls.

One message: neither model clears the chance rate of the brackets it was given,
and the strict scorer hides the sites Llama did identify correctly.

    python -m analysis.render_tolerant_results \
        --logs results/logs --out results/figures/gfp-tolerance-results-v1.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

REPO_ROOT = Path(__file__).resolve().parents[1]
TOLERANT_TASK = "gfp_tolerant_site"
BRACKET_ORDER = ("1-50", "51-100", "101-150", "151-200", "200-238")

# Outcome codes. "misquoted" is an accepted start whose quoted triple does not
# match the reference there: correct site, wrong citation, scored incorrect.
CORRECT, MISQUOTED, WRONG = "correct", "misquoted", "wrong"


def chance_distribution(rates: list[float]) -> list[float]:
    """Exact Poisson-binomial P(X = k) for independent brackets of unequal chance."""
    dist = [1.0]
    for rate in rates:
        nxt = [0.0] * (len(dist) + 1)
        for k, value in enumerate(dist):
            nxt[k] += value * (1 - rate)
            nxt[k + 1] += value * rate
        dist = nxt
    return dist


def at_least(dist: list[float], k: int) -> float:
    return sum(dist[k:])


def collect(log_dir: Path) -> list[dict]:
    """Per-run, per-bracket outcomes from the tolerant-site logs."""
    from inspect_ai.log import read_eval_log

    runs: list[dict] = []
    for path in sorted(log_dir.glob("*.eval")):
        header = read_eval_log(str(path), header_only=True)
        if header.status != "success":
            continue
        if (header.eval.task or "").rsplit("/", 1)[-1] != TOLERANT_TASK:
            continue
        log = read_eval_log(str(path))
        config = header.eval.model_generate_config
        outcomes: dict[str, str] = {}
        chance: dict[str, float] = {}
        for sample in log.samples or []:
            meta = sample.metadata or {}
            bracket = str(meta.get("bracket_id"))
            chance[bracket] = float(meta.get("chance") or 0.0)
            score = next(iter((sample.scores or {}).values()), None)
            smeta = (score.metadata or {}) if score is not None else {}
            accepted = smeta.get("start") in (meta.get("accepted_starts") or [])
            if score is not None and score.value == "C":
                outcomes[bracket] = CORRECT
            elif accepted:
                outcomes[bracket] = MISQUOTED
            else:
                outcomes[bracket] = WRONG
        runs.append(
            {
                "model": (header.eval.model or "").rsplit("/", 1)[-1],
                "max_tokens": None if config is None else config.max_tokens,
                "outcomes": outcomes,
                "chance": chance,
            }
        )
    return runs


def render(runs: list[dict], out: Path) -> Path:
    if not runs:
        raise ValueError("no tolerant-site runs found")
    out = Path(out)
    brackets = [b for b in BRACKET_ORDER if b in runs[0]["chance"]]
    chance = [runs[0]["chance"][b] * 100 for b in brackets]
    expected = sum(runs[0]["chance"][b] for b in brackets)
    y = list(range(len(brackets)))[::-1]  # first bracket at the top

    colours = ["#1b6ca8", "#c2651a"]
    model_colour = {run["model"]: colours[i % len(colours)] for i, run in enumerate(runs)}

    # Role-mapped ladder: titles/axis labels, then annotations, then ticks.
    plt.rcParams.update({
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.direction": "out", "ytick.direction": "out", "figure.dpi": 300,
    })
    fig = plt.figure(figsize=(10.0, 3.5))
    grid = fig.add_gridspec(1, 3, width_ratios=[2.5, 1.2, 2.0], wspace=0.55)
    ax_chance = fig.add_subplot(grid[0, 0])
    ax_grid = fig.add_subplot(grid[0, 1], sharey=ax_chance)
    ax_total = fig.add_subplot(grid[0, 2])

    # -- chance context -------------------------------------------------
    ax_chance.barh(y, chance, height=0.55, color="#d9d9d9", edgecolor="#9c9c9c", linewidth=0.6)
    for yi, value in zip(y, chance):
        ax_chance.text(value + 2, yi, f"{value:.0f}%", va="center", ha="left", fontsize=6)
    ax_chance.set_yticks(y)
    ax_chance.set_yticklabels(brackets)
    ax_chance.set_xlim(0, 100)
    ax_chance.set_xlabel("tolerant triples in bracket (%)")
    ax_chance.set_ylabel("residue bracket")
    ax_chance.set_title("The brackets are very unequal", loc="left", pad=8)
    ax_chance.margins(y=0.12)

    # -- per-bracket outcomes -------------------------------------------
    marker = {CORRECT: "o", MISQUOTED: "o", WRONG: "o"}
    for col, run in enumerate(runs):
        colour = model_colour[run["model"]]
        for yi, bracket in zip(y, brackets):
            outcome = run["outcomes"].get(bracket, WRONG)
            if outcome == CORRECT:
                ax_grid.plot(col, yi, marker[outcome], ms=9, color=colour, zorder=3)
            elif outcome == MISQUOTED:
                ax_grid.plot(col, yi, marker[outcome], ms=9, markerfacecolor="white",
                             markeredgecolor=colour, markeredgewidth=2.0, zorder=3)
                ax_grid.plot(col, yi, ".", ms=3, color=colour, zorder=4)
            else:
                ax_grid.plot(col, yi, marker[outcome], ms=9, markerfacecolor="white",
                             markeredgecolor="#c0c0c0", markeredgewidth=1.0, zorder=2)
    ax_grid.set_xlim(-0.6, len(runs) - 0.4)
    ax_grid.set_xticks(range(len(runs)))
    ax_grid.set_xticklabels([r["model"].replace("-Instruct-Turbo", "") for r in runs],
                            rotation=30, ha="right", fontsize=6)
    ax_grid.set_title("Outcome per bracket", loc="left", pad=8)
    ax_grid.tick_params(labelleft=False)
    for spine in ("top", "right", "left"):
        ax_grid.spines[spine].set_visible(False)
    ax_grid.tick_params(axis="y", length=0)

    # -- totals against chance ------------------------------------------
    rows, labels, cols = [], [], []
    for run in runs:
        strict = sum(v == CORRECT for v in run["outcomes"].values())
        start_only = strict + sum(v == MISQUOTED for v in run["outcomes"].values())
        rows.append((strict, start_only))
        labels.append(run["model"].replace("-Instruct-Turbo", ""))
        cols.append(model_colour[run["model"]])
    ypos = list(range(len(rows)))[::-1]
    for yi, (strict, start_only), colour in zip(ypos, rows, cols):
        if start_only != strict:
            ax_total.plot([strict, start_only], [yi, yi], color=colour, lw=1.2, alpha=0.5, zorder=1)
            ax_total.plot(start_only, yi, "o", ms=9, markerfacecolor="white",
                          markeredgecolor=colour, markeredgewidth=2.0, zorder=3)
            ax_total.plot(start_only, yi, ".", ms=3, color=colour, zorder=4)
        ax_total.plot(strict, yi, "o", ms=9, color=colour, zorder=3)
    dist = chance_distribution([runs[0]["chance"][b] for b in brackets])
    ax_total.axvline(expected, color="#444444", lw=1.1, ls=(0, (4, 2)), zorder=2)
    ax_total.annotate(f"chance\nmean {expected:.2f}", xy=(expected, 0.02),
                      xycoords=("data", "axes fraction"), xytext=(3, 0), textcoords="offset points",
                      fontsize=6, va="bottom", ha="left", color="#444444")
    for yi, (strict, start_only), colour in zip(ypos, rows, cols):
        best = max(strict, start_only)
        ax_total.annotate(f"a guesser reaches {best} in {at_least(dist, best) * 100:.0f}% of runs",
                          xy=(0.985, yi), xycoords=("axes fraction", "data"),
                          xytext=(0, 10), textcoords="offset points",
                          fontsize=6, color=colour, va="bottom", ha="right")
    ax_total.set_yticks(ypos)
    ax_total.set_yticklabels(labels)
    ax_total.set_xlim(-0.35, 5.35)
    ax_total.set_xticks(range(6))
    ax_total.set_xlabel("brackets solved (of 5)")
    ax_total.set_title("Both scores sit inside the chance range", loc="left", pad=8)
    ax_total.margins(y=0.42)

    handles = [
        Line2D([], [], marker="o", ls="", ms=8, color="#555555", label="scored correct"),
        Line2D([], [], marker="o", ls="", ms=8, markerfacecolor="white",
               markeredgecolor="#555555", markeredgewidth=2.0,
               label="tolerant site found, sequence misquoted\n(scored incorrect)"),
        Line2D([], [], marker="o", ls="", ms=8, markerfacecolor="white",
               markeredgecolor="#c0c0c0", label="wrong site"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               fontsize=6, bbox_to_anchor=(0.5, -0.26), handletextpad=0.4)
    fig.suptitle("Locating substitution-tolerant sites in avGFP (n = 5 brackets per model)",
                 x=0.012, y=1.06, ha="left", fontsize=9)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")
    return fig, out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", default=str(REPO_ROOT / "results" / "logs"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    _fig, out = render(collect(Path(args.logs)), Path(args.out))
    print(out)


if __name__ == "__main__":
    main()
