"""Circular-barcode results poster. Refuses to overwrite an existing file.

Run:
    python -m analysis.render_results_poster \\
        --predictions results/predictions/*.csv \\
        --out results/figures/gfp-orientation-results-v1.png
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from analysis.figures.barrel_posters import _glow, draw_ring_barcode  # noqa: E402
from analysis.ground_truth.barrel_orientation import coin_flip  # noqa: E402
from analysis.report import read_prediction_csv  # noqa: E402
from bio_eval.tasks.gfp_barrel.dataset import load_rows  # noqa: E402
from bio_eval.tasks.gfp_barrel.metrics import accuracy  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
AZIMUTH_PATH = Path(__file__).resolve().parent / "figures" / "strand_azimuths.json"


def strand_order() -> list[str]:
    azimuths = json.loads(AZIMUTH_PATH.read_text())
    return sorted(azimuths, key=lambda strand_id: azimuths[strand_id])


def _toward(label: str) -> str:
    if label in {"inward", "TOWARD"}:
        return "TOWARD"
    if label in {"outward", "AWAY"}:
        return "AWAY"
    return label


def _scores(labels: list[str], rows: list[dict]) -> tuple[float, float]:
    truth = [row["truth"] for row in rows]
    robust = [row["robust"] for row in rows]
    all_acc = accuracy(labels, truth)
    robust_acc = accuracy(
        [label for label, keep in zip(labels, robust) if keep],
        [label for label, keep in zip(truth, robust) if keep],
    )
    return robust_acc, all_acc


def _epoch1(prediction_rows: list[dict]) -> dict[int, str]:
    chosen = {}
    for row in prediction_rows:
        resnum = int(row["author_resnum"])
        epoch = int(row["epoch"])
        if resnum not in chosen or epoch < chosen[resnum][0]:
            chosen[resnum] = (epoch, row["label"])
    return {resnum: label for resnum, (_epoch, label) in chosen.items()}


def _labels_for(rows: list[dict], by_resnum: dict[int, str]) -> list[str]:
    return [by_resnum[row["author_resnum"]] for row in rows]


def draw_results_legend(ax, order: list[str]) -> None:
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.45, 1.45)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(0, 1.28, "How to read a panel", ha="center", va="top", fontsize=12, fontweight="bold")
    ax.text(
        0, 1.02,
        "Black cell: side chain points TOWARD the chromophore.\n"
        "White cell: side chain points AWAY.\n"
        "Dotted outline: |chromophore cosine| < 0.2 (not in the headline).",
        ha="center", va="top", fontsize=8.5,
    )
    _glow(ax, (0, -0.15), 0.16, step=0.06)
    ax.text(0, -0.48, "green chromophore", ha="center", fontsize=9, color="#0b6e1d", fontweight="bold")
    ax.text(
        0, -0.85,
        "Ground truth: side-chain direction from Cα toward the chromophore centroid.",
        ha="center", va="top", fontsize=8,
    )
    ax.text(
        0, -1.25,
        "Strand order: " + " → ".join(f"β{strand[1:]}" for strand in order),
        ha="center", va="top", fontsize=8, color="#444444",
    )


def render(
    prediction_csvs: list[Path] | None = None,
    out: Path | None = None,
    copy_media: Path | None = None,
) -> Path:
    if out is None:
        raise ValueError("out path is required")
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    rows = load_rows()
    order = strand_order()
    fragile = {row["author_resnum"] for row in rows if not row["robust"]}
    truth = [row["truth"] for row in rows]
    hydro = [_toward(row["hydrophobicity_prediction"]) for row in rows]
    random_labels = [_toward(label) for label in coin_flip(len(rows), seed=0)]
    panels: list[tuple[str, list[str], bool]] = [
        ("Ground truth (1EMA)", truth, True),
        ("Random (seed 0)", random_labels, False),
        ("Hydrophobicity rule", hydro, False),
    ]
    model_panels = []
    for path in prediction_csvs or []:
        pred_rows = read_prediction_csv(Path(path))
        if not pred_rows:
            continue
        by_resnum = _epoch1(pred_rows)
        labels = _labels_for(rows, by_resnum)
        robust_acc, _all = _scores(labels, rows)
        name = pred_rows[0].get("model") or Path(path).stem
        model_panels.append((robust_acc, name, labels))
    model_panels.sort(key=lambda item: item[0], reverse=True)
    for _robust, name, labels in model_panels:
        panels.append((name, labels, False))

    n_cells = max(9, len(panels) + 1)
    ncols = 3
    nrows = (n_cells + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(12.5, 4.2 * nrows))
    flat = list(axes.flat)
    for ax in flat:
        ax.axis("off")
    for ax, (title, labels, is_truth) in zip(flat, panels):
        draw_ring_barcode(ax, rows, labels, order, fragile_resnums=fragile)
        if is_truth:
            ax.set_title(title, fontsize=11, fontweight="bold", pad=6)
        else:
            robust_acc, all_acc = _scores(labels, rows)
            ax.set_title(
                f"{title} — {robust_acc:.3f} (robust 98)\nall 107: {all_acc:.3f}",
                fontsize=10,
                pad=6,
            )
    draw_results_legend(flat[len(panels)], order)
    fig.suptitle("GFP beta-barrel side-chain orientation", fontsize=14, fontweight="bold")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    if copy_media is not None:
        media = Path(copy_media)
        media.mkdir(parents=True, exist_ok=True)
        dest = media / out.name
        if dest.exists():
            raise FileExistsError(f"refusing to overwrite {dest}")
        shutil.copyfile(out, dest)
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", nargs="*", default=[])
    parser.add_argument("--out", required=True)
    parser.add_argument("--copy-media", default=None)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    path = render(
        [Path(item) for item in args.predictions],
        Path(args.out),
        Path(args.copy_media) if args.copy_media else None,
    )
    print(path)


if __name__ == "__main__":
    main()
