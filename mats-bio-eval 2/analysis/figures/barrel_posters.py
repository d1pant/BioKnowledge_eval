"""Poster-style multi-panel comparisons of predictions vs the chromophore ground truth.

Run as ``python -m analysis.figures.barrel_posters``. Panels are the X-ray truth, a
coin flip, the Kyte-Doolittle hydrophobicity rule, and five SYNTHETIC
"models" made by flipping an exact number of truth labels with fixed seeds.
The synthetic panels are design mockups, not model runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle, Wedge  # noqa: E402

from analysis.figures.azimuths import cached_azimuths  # noqa: E402
from analysis.figures.labels import load_rows  # noqa: E402
from analysis.ground_truth import barrel_orientation as bo  # noqa: E402

SYNTHETIC_TARGETS = [0.60, 0.75, 0.85, 0.93, 0.98]
SYNTHETIC_SEED_BASE = 100
INK, PAPER, EDGE = "#111111", "#ffffff", "#9a9a9a"
GREEN, RED = "#2ecc40", "#d62728"
MAX_LEN = max(e - b + 1 for b, e in bo.STRANDS_1EMA)
NOTE_LINES = (
    "Synthetic model predictions are design mockups (X-ray labels flipped at random, "
    "fixed seeds) — not real model runs.",
    "Truth: PDB 1EMA, does the side chain point toward the chromophore?  "
    "n = 107 β-strand residues.  Random and hydrophobicity panels are real baselines.",
)


@dataclass
class Panel:
    title: str
    labels: list[str]
    accuracy: float
    kind: str


def flip_to_accuracy(truth: list[str], target: float, seed: int) -> list[str]:
    n = len(truth)
    k = round((1 - target) * n)
    idx = np.random.default_rng(seed).choice(n, size=k, replace=False)
    out = list(truth)
    for i in idx:
        out[i] = "outward" if out[i] == "inward" else "inward"
    return out


def build_panels(rows: list[dict]) -> dict[str, Panel]:
    truth = [r["truth"] for r in rows]

    def acc(labels):
        return float(np.mean([a == b for a, b in zip(labels, truth)]))

    panels = {"truth": Panel("X-ray truth (1EMA)", truth, 1.0, "truth")}
    rnd = bo.coin_flip(len(rows), seed=0)
    panels["random"] = Panel("Random coin flip", rnd, acc(rnd), "baseline")
    hyd = [r["pred"] for r in rows]
    panels["hydrophobicity"] = Panel("Hydrophobicity rule", hyd, acc(hyd), "baseline")
    for i, t in enumerate(SYNTHETIC_TARGETS):
        lab = flip_to_accuracy(truth, t, SYNTHETIC_SEED_BASE + i)
        panels[f"syn{round(t * 100)}"] = Panel(
            f"Synthetic model {chr(ord('A') + i)}", lab, acc(lab), "synthetic")
    return panels


GRID_ORDER = ["truth", "random", "hydrophobicity", "syn60", "syn75", "syn85", "syn93", "syn98"]


def panel_heading(ax, p: Panel, size: float = 11.5) -> None:
    color = {"truth": "#0b6e1d", "baseline": "#444444", "synthetic": "#6a3d9a"}[p.kind]
    acc = "reference" if p.kind == "truth" else f"{p.accuracy:.1%} correct"
    ax.set_title(f"{p.title}\n{acc}", fontsize=size, color=color, fontweight="bold",
                 pad=5, linespacing=1.2)


def draw_grid(ax, rows: list[dict], labels: list[str], gap: float = 0.08) -> None:
    for r, lab in zip(rows, labels):
        y = bo.STRAND_IDS.index(r["strand_id"])
        x = r["index_in_strand"]
        ax.add_patch(Rectangle((x + gap / 2, y + gap / 2), 1 - gap, 1 - gap,
                               facecolor=INK if lab == "inward" else PAPER,
                               edgecolor=EDGE, lw=0.6))
    ax.set_xlim(0, MAX_LEN)
    ax.set_ylim(len(bo.STRAND_IDS), 0)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([i + 0.5 for i in range(len(bo.STRAND_IDS))])
    ax.set_yticklabels([f"β{i + 1}" for i in range(len(bo.STRAND_IDS))], fontsize=7.5)
    ax.tick_params(length=0, pad=2)
    for s in ax.spines.values():
        s.set_visible(False)


def draw_barcode(ax, rows: list[dict], labels: list[str]) -> None:
    strip_h, pitch = 0.5, 1.0
    for sid_i, sid in enumerate(bo.STRAND_IDS):
        y = sid_i * pitch
        cells = [(r, lab) for r, lab in zip(rows, labels) if r["strand_id"] == sid]
        ax.add_patch(Rectangle((0, y), len(cells), strip_h, facecolor=PAPER,
                               edgecolor=INK, lw=0.8))
        for r, lab in cells:
            if lab == "inward":
                ax.add_patch(Rectangle((r["index_in_strand"], y), 1, strip_h,
                                       facecolor=INK, lw=0))
    ax.set_xlim(-0.2, MAX_LEN + 0.2)
    ax.set_ylim(len(bo.STRAND_IDS) * pitch, -0.3)
    ax.set_xticks([])
    ax.set_yticks([i * pitch + strip_h / 2 for i in range(len(bo.STRAND_IDS))])
    ax.set_yticklabels([f"β{i + 1}" for i in range(len(bo.STRAND_IDS))], fontsize=7)
    ax.tick_params(length=0, pad=2)
    for s in ax.spines.values():
        s.set_visible(False)


def draw_ring(ax, rows: list[dict], labels: list[str], truth: list[str], order: list[str],
              mark_errors: bool) -> None:
    ring, gap, spoke = 1.0, 0.05, 0.3
    slot = 360.0 / len(order)
    ax.add_patch(Circle((0, 0), ring + gap + spoke + 0.06, facecolor="#eef4f9",
                        edgecolor="none"))
    ax.add_patch(Circle((0, 0), ring - gap - spoke - 0.06, facecolor="#fffaf2",
                        edgecolor="none"))
    for k, a in enumerate(np.linspace(0.6, 0.05, 7)):
        ax.add_patch(Circle((0, 0), 0.07 + 0.045 * k, facecolor="#39ff14", alpha=a * 0.4,
                            edgecolor="none"))
    ax.add_patch(Circle((0, 0), 0.09, facecolor=GREEN, edgecolor="#0b6e1d", lw=1))
    by_strand = {}
    for r, lab, t in zip(rows, labels, truth):
        by_strand.setdefault(r["strand_id"], []).append((lab, t))
    for k, sid in enumerate(order):
        centre = 90.0 - k * slot
        res = by_strand[sid]
        step = slot * 0.86 / MAX_LEN
        half = step * (len(res) - 1) / 2
        ax.add_patch(Wedge((0, 0), ring + 0.03, centre - half - 1.5, centre + half + 1.5,
                           width=0.06, facecolor="#8c8c8c", edgecolor="none"))
        for j, (lab, t) in enumerate(res):
            th = np.radians(centre + half - j * step)
            sign = -1 if lab == "inward" else 1
            r0, r1 = ring + sign * gap, ring + sign * (gap + spoke)
            col = RED if (mark_errors and lab != t) else INK
            ax.plot([r0 * np.cos(th), r1 * np.cos(th)], [r0 * np.sin(th), r1 * np.sin(th)],
                    color=col, lw=1.6, solid_capstyle="round")
        lr = ring + gap + spoke + 0.2
        ax.text(lr * np.cos(np.radians(centre)), lr * np.sin(np.radians(centre)),
                f"β{sid[1:]}", ha="center", va="center", fontsize=7, color="#555555")
    lim = ring + gap + spoke + 0.33
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_explainer(ax) -> None:
    """Tiny schematic: one strand, side chains alternating toward/away from the chromophore."""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.add_patch(Circle((5, 1.6), 0.95, facecolor=GREEN, edgecolor="#0b6e1d", lw=1.2))
    for k, a in enumerate(np.linspace(0.5, 0.05, 5)):
        ax.add_patch(Circle((5, 1.6), 1.0 + 0.35 * k, facecolor="#39ff14", alpha=a * 0.35,
                            edgecolor="none"))
    ax.text(5, 1.6, "chromophore", ha="center", va="center", fontsize=7.5, color="#0b3d12",
            fontweight="bold")
    xs = np.linspace(1.4, 8.6, 7)
    ys = 5.4 + 0.35 * np.array([1, -1] * 4)[:7]
    ax.plot(xs, ys, color="#8c8c8c", lw=3, solid_capstyle="round", zorder=1)
    for i, (x, y) in enumerate(zip(xs, ys)):
        toward = i % 2 == 0
        y2 = y - 1.5 if toward else y + 1.5
        ax.plot([x, x], [y, y2], color=INK, lw=1.6, zorder=2)
        ax.add_patch(Circle((x, y2), 0.36, facecolor=INK if toward else PAPER, edgecolor=INK,
                            lw=1.2, zorder=3))
    ax.text(5, 9.3, "One β-strand, side view", ha="center", fontsize=9, fontweight="bold")
    ax.text(5, 8.35, "side chains alternate: ● toward chromophore,  ○ away",
            ha="center", fontsize=8)
    ax.text(5, 0.05, "black cell = toward,  white cell = away", ha="center", va="bottom",
            fontsize=8.5, fontweight="bold")


def _poster(title: str, figsize=(13, 14.2)):
    """Title plus the two-line synthetic disclaimer, positioned in inches from the top."""
    fig = plt.figure(figsize=figsize)
    h = figsize[1]
    fig.text(0.5, 1 - 0.2 / h, title, ha="center", va="top", fontsize=22, fontweight="bold")
    for i, line in enumerate(NOTE_LINES):
        fig.text(0.5, 1 - (0.78 + 0.24 * i) / h, line, ha="center", va="top", fontsize=10.5,
                 color="#6a3d9a", fontweight="bold" if i == 0 else "normal")
    return fig


def _top(fig, inches: float) -> float:
    return 1 - inches / fig.get_figheight()


def poster_grid(rows, panels, path: Path) -> None:
    fig = _poster("How blind models see inside GFP")
    axes = fig.subplots(3, 3, gridspec_kw=dict(left=0.04, right=0.98, top=_top(fig, 1.85),
                                                bottom=0.03, hspace=0.32, wspace=0.12))
    for ax, key in zip(axes.flat, GRID_ORDER):
        draw_grid(ax, rows, panels[key].labels)
        panel_heading(ax, panels[key])
    draw_explainer(axes.flat[8])
    fig.savefig(path, dpi=110)
    plt.close(fig)


def poster_rings(rows, panels, path: Path) -> None:
    order = sorted(bo.STRAND_IDS, key=cached_azimuths().get)
    truth = panels["truth"].labels
    fig = _poster("How blind models see a protein barrel")
    axes = fig.subplots(3, 3, gridspec_kw=dict(left=0.02, right=0.98, top=_top(fig, 1.85),
                                                bottom=0.02, hspace=0.22, wspace=0.05))
    for ax, key in zip(axes.flat, GRID_ORDER):
        draw_ring(ax, rows, panels[key].labels, truth, order, mark_errors=key != "truth")
        panel_heading(ax, panels[key])
    ax = axes.flat[8]
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.text(5, 9.2, "Looking down the barrel", ha="center", fontsize=12, fontweight="bold")
    items = [
        (Line2D([], [], color=INK, lw=2), "black spoke = predicted side-chain direction:\n"
         "into the ring = toward chromophore,\nout of the ring = away (solvent)"),
        (Line2D([], [], color=RED, lw=2), "red spoke = prediction disagrees with X-ray"),
        (Line2D([], [], color="#8c8c8c", lw=6), "grey arc = one β-strand"),
        (Line2D([], [], marker="o", ls="", markersize=12, markerfacecolor=GREEN,
                markeredgecolor="#0b6e1d"), "green = chromophore at barrel centre"),
    ]
    ax.legend([h for h, _ in items], [t for _, t in items], loc="center", frameon=False,
              fontsize=9.5, handlelength=2.2, labelspacing=1.1)
    ax.text(5, 0.6, "Strand ring order from 1EMA coordinates:\n"
            + " → ".join(f"β{s[1:]}" for s in order), ha="center", fontsize=8.5,
            color="#555555")
    fig.savefig(path, dpi=110)
    plt.close(fig)


def poster_barcode(rows, panels, path: Path) -> None:
    fig = _poster("Do models know which residues face the chromophore?", figsize=(13, 11.5))
    axes = fig.subplots(3, 3, gridspec_kw=dict(left=0.04, right=0.98, top=_top(fig, 1.85),
                                                bottom=0.03, hspace=0.42, wspace=0.12))
    for ax, key in zip(axes.flat, GRID_ORDER):
        draw_barcode(ax, rows, panels[key].labels)
        panel_heading(ax, panels[key])
    ax = axes.flat[8]
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.add_patch(Rectangle((1.5, 6.2), 1.2, 0.9, facecolor=INK))
    ax.text(3.1, 6.65, "faces the chromophore", va="center", fontsize=11)
    ax.add_patch(Rectangle((1.5, 4.6), 1.2, 0.9, facecolor=PAPER, edgecolor=INK))
    ax.text(3.1, 5.05, "faces away (solvent)", va="center", fontsize=11)
    ax.text(5, 2.6, "One strip per β-strand, residues N→C left to right.\n"
            "The true barrel alternates: a fine black/white stripe.", ha="center",
            fontsize=9.5, color="#444444")
    fig.savefig(path, dpi=110)
    plt.close(fig)


def poster_progression(rows, panels, path: Path) -> None:
    order = sorted(GRID_ORDER, key=lambda key: panels[key].accuracy)
    assert order[-1] == "truth"
    fig = _poster("When did language models learn protein structure?", figsize=(16, 11))
    axes = fig.subplots(2, 4, gridspec_kw=dict(left=0.035, right=0.985, top=_top(fig, 2.0),
                                                bottom=0.08, hspace=0.62, wspace=0.34))
    for k, (ax, key) in enumerate(zip(axes.flat, order)):
        p = panels[key]
        draw_grid(ax, rows, p.labels)
        panel_heading(ax, p, size=12)
        ax.text(-1.4, -1.0, f"{k + 1}", fontsize=17, fontweight="bold", color="#aaaaaa",
                ha="right", va="bottom")
        bar_y = len(bo.STRAND_IDS) + 0.5
        ax.add_patch(Rectangle((0, bar_y), MAX_LEN, 0.55, facecolor="#e6e6e6", lw=0,
                               clip_on=False))
        ax.add_patch(Rectangle((0, bar_y), MAX_LEN * p.accuracy, 0.55, clip_on=False, lw=0,
                               facecolor=GREEN if key == "truth" else "#6a3d9a"))
        if key == "truth":
            for s in ax.spines.values():
                s.set_visible(True)
                s.set_edgecolor(GREEN)
                s.set_linewidth(3)

    def arrow(start, end, rad=0.0):
        fig.patches.append(FancyArrowPatch(
            start, end, transform=fig.transFigure, arrowstyle="-|>", mutation_scale=24,
            color="#6a3d9a", lw=2.4, connectionstyle=f"arc3,rad={rad}"))

    flat = list(axes.flat)
    for a, b in zip(flat[:-1], flat[1:]):
        pa, pb = a.get_position(), b.get_position()
        if abs(pa.y0 - pb.y0) < 1e-3:
            y = pa.y0 + pa.height / 2
            arrow((pa.x1 + 0.006, y), (pb.x0 - 0.03, y))
    top_row, bottom_row = flat[3].get_position(), flat[4].get_position()
    band = (top_row.y0 + bottom_row.y1) / 2 + 0.004
    arrow((top_row.x0 + top_row.width / 2, band), (bottom_row.x0 + bottom_row.width / 2, band))
    fig.text(0.5, band + 0.008, "continue", ha="center", va="bottom", fontsize=9.5,
             color="#6a3d9a", style="italic")
    fig.text(0.5, 0.025, "Black = side chain toward the chromophore, white = away.  "
             "Bar = fraction correct vs X-ray.  The true barrel is a fine alternating "
             "checkerboard; emergence = the checkerboard appearing.",
             ha="center", fontsize=11)
    fig.savefig(path, dpi=110)
    plt.close(fig)


RING_R = 1.0
CELL_H = 0.27
CELL_W = 2 * RING_R * np.sin(np.pi / len(bo.STRAND_IDS)) * 0.94 / MAX_LEN


def _glow(ax, centre, core: float, rings: int = 7, step: float = 0.05) -> None:
    for k, a in enumerate(np.linspace(0.6, 0.05, rings)):
        ax.add_patch(Circle(centre, core * 0.8 + step * k, facecolor="#39ff14",
                            alpha=a * 0.4, edgecolor="none"))
    ax.add_patch(Circle(centre, core, facecolor=GREEN, edgecolor="#0b6e1d", lw=1))


def _tangent_bar(ax, theta: float, labels: list[str], radius: float = RING_R,
                 w: float = CELL_W, h: float = CELL_H,
                 fragile: list[bool] | None = None) -> None:
    """Straight barcode tangent to the ring at angle theta; cells run N->C clockwise."""
    normal = np.array([np.cos(theta), np.sin(theta)])
    tangent = np.array([np.sin(theta), -np.cos(theta)])
    centre = radius * normal
    n = len(labels)
    for j, lab in enumerate(labels):
        mid = centre + tangent * (j - (n - 1) / 2) * w
        corners = [mid + tangent * sx * w / 2 + normal * sy * h / 2
                   for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        toward = lab in {"inward", "TOWARD"}
        ax.add_patch(Polygon(corners, closed=True, lw=0,
                             facecolor=INK if toward else PAPER))
        if fragile and fragile[j]:
            ax.add_patch(Polygon(corners, closed=True, fill=False, edgecolor="#333333",
                                 lw=0.7, linestyle=(0, (0.8, 0.9))))
    ends = [centre + tangent * sx * n * w / 2 + normal * sy * h / 2
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ax.add_patch(Polygon(ends, closed=True, fill=False, edgecolor=INK, lw=0.9))


def draw_ring_barcode(ax, rows: list[dict], labels: list[str], order: list[str],
                      fragile_resnums: set[int] | None = None) -> None:
    by_strand: dict[str, list[str]] = {}
    fragile_by_strand: dict[str, list[bool]] = {}
    for r, lab in zip(rows, labels):
        by_strand.setdefault(r["strand_id"], []).append(lab)
        if fragile_resnums is not None:
            fragile_by_strand.setdefault(r["strand_id"], []).append(
                int(r["author_resnum"]) in fragile_resnums
            )
    slot = 2 * np.pi / len(order)
    ax.add_patch(Circle((0, 0), RING_R + 0.2, facecolor="#eef4f9", edgecolor="none"))
    ax.add_patch(Circle((0, 0), RING_R - 0.2, facecolor="#fffaf2", edgecolor="none"))
    _glow(ax, (0, 0), 0.13)
    for k, sid in enumerate(order):
        theta = np.pi / 2 - k * slot
        _tangent_bar(
            ax, theta, by_strand[sid],
            fragile=fragile_by_strand.get(sid) if fragile_resnums is not None else None,
        )
        lr = RING_R + 0.3
        ax.text(lr * np.cos(theta), lr * np.sin(theta), f"β{sid[1:]}", ha="center",
                va="center", fontsize=10, color="#444444", fontweight="bold")
    lim = RING_R + 0.38
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")


def draw_ring_barcode_legend(ax, order: list[str]) -> None:
    ax.set_xlim(-1.38, 1.38)
    ax.set_ylim(-1.38, 1.38)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(0, 1.34, "How to read a panel", ha="center", va="top", fontsize=12,
            fontweight="bold")
    ax.text(0, 1.1, "Top-down view. Each mini-bar is one β-strand:\n"
            "one cell per residue, N→C clockwise.", ha="center", va="top", fontsize=9.2)
    _glow(ax, (0, -0.62), 0.2, step=0.07)
    ax.text(0, -0.98, "green chromophore", ha="center", va="top", fontsize=9.2,
            color="#0b6e1d", fontweight="bold")
    demo = ["inward", "outward"] * 3 + ["inward"]
    w, h, y = 0.2, 0.24, 0.12
    xs = (np.arange(len(demo)) - (len(demo) - 1) / 2) * w
    for x, lab in zip(xs, demo):
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, lw=0,
                               facecolor=INK if lab == "inward" else PAPER))
        if lab == "inward":
            ax.annotate("", xy=(x * 0.25, -0.38), xytext=(x, y - h / 2 - 0.02),
                        arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2))
        else:
            ax.annotate("", xy=(x, y + h / 2 + 0.3), xytext=(x, y + h / 2 + 0.02),
                        arrowprops=dict(arrowstyle="-|>", color="#888888", lw=1.2))
    ax.add_patch(Rectangle((xs[0] - w / 2, y - h / 2), len(demo) * w, h, fill=False,
                           edgecolor=INK, lw=1.2))
    ax.text(xs[-1] + 0.2, y + 0.3, "white cell:\npoints away\n(solvent)", ha="left",
            va="center", fontsize=9, color="#555555", fontweight="bold")
    ax.text(xs[0] - 0.2, y - 0.3, "black cell:\npoints toward\nchromophore", ha="right",
            va="center", fontsize=9, fontweight="bold")
    ax.text(0, -1.36, "Strand ring order measured in 1EMA:\n"
            + " → ".join(f"β{s[1:]}" for s in order), ha="center", va="bottom", fontsize=8,
            color="#555555")

def poster_ring_barcodes(rows, panels, path: Path) -> None:
    order = sorted(bo.STRAND_IDS, key=cached_azimuths().get)
    fig = _poster("How blind models see a protein barrel, strand by strand")
    axes = fig.subplots(3, 3, gridspec_kw=dict(left=0.01, right=0.99, top=_top(fig, 1.85),
                                                bottom=0.01, hspace=0.16, wspace=0.02))
    for ax, key in zip(axes.flat, GRID_ORDER):
        draw_ring_barcode(ax, rows, panels[key].labels, order)
        panel_heading(ax, panels[key], size=12.5)
    draw_ring_barcode_legend(axes.flat[8], order)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main() -> None:
    rows = load_rows()
    panels = build_panels(rows)
    out = bo.VALIDATION_DIR
    poster_grid(rows, panels, out / "poster-1-unrolled-grid-v1.png")
    poster_rings(rows, panels, out / "poster-2-barrel-rings-v1.png")
    poster_barcode(rows, panels, out / "poster-3-barcode-v1.png")
    poster_progression(rows, panels, out / "poster-4-progression-v2.png")
    poster_ring_barcodes(rows, panels, out / "poster-5-circular-barcodes-v1.png")
    for key in GRID_ORDER:
        p = panels[key]
        print(f"{key:15s} {p.title:28s} {p.accuracy:.3f}")


if __name__ == "__main__":
    main()
