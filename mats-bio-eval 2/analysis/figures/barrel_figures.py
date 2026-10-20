"""Unrolled-barrel figures: strands as rows, index within strand as columns."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

from analysis.ground_truth.barrel_orientation import (  # noqa: E402
    STRAND_IDS,
    STRANDS_1EMA,
    ResidueLabel,
    accuracy,
    coin_flip,
)

COLORS = {"inward": "#d95f02", "outward": "#7fb3d5"}
MAX_LEN = max(e - b + 1 for b, e in STRANDS_1EMA)


def draw_unrolled(
    rows: list[ResidueLabel],
    labels: list[str],
    title: str,
    subtitle: str,
    path: Path,
    truth: list[str] | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 7.4))
    for r, lab, k in zip(rows, labels, range(len(rows))):
        y = STRAND_IDS.index(r.strand_id)
        x = r.index_in_strand
        wrong = truth is not None and truth[k] != lab
        ax.add_patch(Rectangle((x, y), 0.94, 0.88, facecolor=COLORS[lab],
                               edgecolor="black" if wrong else "white",
                               linewidth=2.6 if wrong else 0.5))
        if wrong:
            ax.text(x + 0.86, y + 0.14, "✗", ha="center", va="center",
                    fontsize=10, fontweight="bold")
        ax.text(x + 0.47, y + 0.36, r.aa, ha="center", va="center",
                fontsize=12, fontweight="bold")
        ax.text(x + 0.47, y + 0.70, str(r.author_resnum), ha="center",
                va="center", fontsize=7.5)
    ax.set_xlim(-0.1, MAX_LEN + 0.1)
    ax.set_ylim(len(STRAND_IDS) + 0.05, -0.15)
    ax.set_yticks([i + 0.44 for i in range(len(STRAND_IDS))])
    ax.set_yticklabels([f"β{i + 1}  ({b}–{e})" for i, (b, e) in enumerate(STRANDS_1EMA)],
                       fontsize=10)
    ax.set_xticks([i + 0.47 for i in range(MAX_LEN)])
    ax.set_xticklabels([str(i) for i in range(MAX_LEN)], fontsize=9)
    ax.set_xlabel("Residue index within strand (N → C, author numbering shown in cell)")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    handles = [Patch(facecolor=COLORS["inward"], label="inward (toward chromophore)"),
               Patch(facecolor=COLORS["outward"], label="outward (away from chromophore)")]
    if truth is not None:
        handles.append(Patch(facecolor="white", edgecolor="black", linewidth=2.6,
                             label="✗ disagrees with ground truth"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.09),
              ncol=len(handles), frameon=False, fontsize=10)
    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.97)
    ax.set_title(subtitle, fontsize=10.5, pad=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def draw_all(rows: list[ResidueLabel], metrics: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    truth = [r.ground_truth_label for r in rows]
    bal = metrics["class_balance"]
    n = len(rows)
    paths = []

    p = out_dir / "gfp-truth.png"
    draw_unrolled(
        rows, truth,
        "avGFP β-barrel: side chain toward or away from the chromophore (PDB 1EMA)",
        f"Inward if (side-chain centroid − CA) · (chromophore centroid − CA) > 0; "
        f"n = {n}: {bal['inward']} inward / {bal['outward']} outward",
        p,
    )
    paths.append(p)

    flips = coin_flip(n, seed=0)
    p = out_dir / "gfp-random.png"
    draw_unrolled(
        rows, flips,
        "avGFP β-barrel: random coin-flip assignment",
        f"Fair coin per residue (numpy seed 0) — accuracy vs chromophore-referenced "
        f"truth = {accuracy(flips, truth):.1%} ({sum(a == b for a, b in zip(flips, truth))}/{n})",
        p, truth=truth,
    )
    paths.append(p)

    hyd = [r.hydrophobicity_prediction for r in rows]
    p = out_dir / "gfp-hydrophobicity.png"
    draw_unrolled(
        rows, hyd,
        "avGFP β-barrel: sequence-only hydrophobicity prediction",
        f"Kyte–Doolittle per residue, KD > 0 → inward — accuracy vs chromophore-referenced "
        f"truth = {accuracy(hyd, truth):.1%} ({sum(a == b for a, b in zip(hyd, truth))}/{n})",
        p, truth=truth,
    )
    paths.append(p)
    return paths
