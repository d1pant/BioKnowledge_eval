"""Post-hoc tables for the orientation task. Reads CSVs only; no model calls."""

from __future__ import annotations

import csv
from pathlib import Path

from analysis.ground_truth.barrel_orientation import coin_flip
from bio_eval.tasks.gfp_barrel.dataset import load_rows
from bio_eval.tasks.gfp_barrel.metrics import (
    accuracy,
    alternation_coherence,
    balanced_accuracy,
    brier,
    mcc,
    per_strand_accuracy,
    reliability_bins,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _toward(label: str) -> str:
    if label in {"inward", "TOWARD"}:
        return "TOWARD"
    if label in {"outward", "AWAY"}:
        return "AWAY"
    return label


def hydrophobicity_baselines(rows: list[dict] | None = None) -> dict:
    """Kyte–Doolittle and the seed-0 coin flip, on the robust 98 and on all 107."""
    rows = rows if rows is not None else load_rows()
    truth = [row["truth"] for row in rows]
    hydro = [_toward(row["hydrophobicity_prediction"]) for row in rows]
    random_labels = [_toward(label) for label in coin_flip(len(rows), seed=0)]
    robust = [row["robust"] for row in rows]

    def pack(pred: list[str], mask: list[bool] | None = None) -> dict[str, float]:
        if mask is None:
            picked_pred, picked_truth = pred, truth
        else:
            picked_pred = [p for p, keep in zip(pred, mask) if keep]
            picked_truth = [t for t, keep in zip(truth, mask) if keep]
        return {
            "accuracy": accuracy(picked_pred, picked_truth),
            "balanced_accuracy": balanced_accuracy(picked_pred, picked_truth),
            "mcc": mcc(picked_pred, picked_truth),
        }

    return {
        "robust": {
            "hydrophobicity": pack(hydro, robust),
            "random_seed0": pack(random_labels, robust),
            "always_away": pack(["AWAY"] * len(rows), robust),
        },
        "all": {
            "hydrophobicity": pack(hydro),
            "random_seed0": pack(random_labels),
            "always_away": pack(["AWAY"] * len(rows)),
        },
    }


def truth_alternation(rows: list[dict] | None = None) -> dict[str, float]:
    rows = rows if rows is not None else load_rows()
    return alternation_coherence(
        [row["strand_id"] for row in rows],
        [row["index_in_strand"] for row in rows],
        [row["truth"] for row in rows],
    )


def _fmt(value: float) -> str:
    if value != value:
        return "nan"
    return f"{value:.3f}"


def render_summary(prediction_rows: list[dict] | None = None) -> str:
    """Markdown tables. Model rows are optional; baselines always appear."""
    rows = load_rows()
    base = hydrophobicity_baselines(rows)
    alt = truth_alternation(rows)
    if prediction_rows:
        intro = "Model rows are the mean of the per-epoch scores in the prediction CSVs."
    else:
        intro = (
            "No scored model run is included yet. "
            "Baselines below are computed from the packaged 1EMA labels."
        )
    lines = [
        "# Results summary",
        "",
        intro,
        "",
        "## Baselines",
        "",
        "| Set | Predictor | Accuracy | Balanced accuracy | MCC |",
        "| --- | --- | --- | --- | --- |",
    ]
    for subset in ("robust", "all"):
        label = "robust 98" if subset == "robust" else "all 107"
        for name, stats in base[subset].items():
            lines.append(
                f"| {label} | {name} | {_fmt(stats['accuracy'])} | "
                f"{_fmt(stats['balanced_accuracy'])} | {_fmt(stats['mcc'])} |"
            )
    lines.extend(
        [
            "",
            "## Truth alternation",
            "",
            f"Within-strand ±1 autocorrelation of the chromophore labels: "
            f"lag 1 {_fmt(alt['lag1'])}, lag 2 {_fmt(alt['lag2'])}, "
            f"adjacent-flip fraction {_fmt(alt['alternation'])}.",
            "",
        ]
    )
    if not prediction_rows:
        lines.append("Model tables are empty.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "## Models",
            "",
            "| Model | max_tokens | Epochs | Robust accuracy | All accuracy | Balanced accuracy | MCC | Unparsed |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    grouped: dict[tuple[str, str, str], list[dict]] = {}
    for row in prediction_rows:
        if not str(row.get("author_resnum") or "").strip():
            # Not an orientation row; the models table is scored per residue.
            continue
        key = (row["model"], str(row.get("max_tokens") or ""), str(row.get("run_id") or ""))
        grouped.setdefault(key, []).append(row)
    if not grouped:
        lines.append("Model tables are empty.")
        lines.append("")
        return "\n".join(lines)
    truth_by_res = {row["author_resnum"]: row for row in rows}
    for (model, max_tokens, _run_id), model_rows in grouped.items():
        epochs = sorted({int(row["epoch"]) for row in model_rows})
        by_epoch: dict[int, list[dict]] = {}
        for row in model_rows:
            by_epoch.setdefault(int(row["epoch"]), []).append(row)
        robust_acc = []
        all_acc = []
        balanced = []
        coeffs = []
        unparsed = []
        for epoch_rows in by_epoch.values():
            ordered = sorted(epoch_rows, key=lambda item: int(item["author_resnum"]))
            pred = [item["label"] for item in ordered]
            truth = [truth_by_res[int(item["author_resnum"])]["truth"] for item in ordered]
            mask = [truth_by_res[int(item["author_resnum"])]["robust"] for item in ordered]
            robust_acc.append(accuracy(
                [p for p, keep in zip(pred, mask) if keep],
                [t for t, keep in zip(truth, mask) if keep],
            ))
            all_acc.append(accuracy(pred, truth))
            balanced.append(balanced_accuracy(pred, truth))
            coeffs.append(mcc(pred, truth))
            unparsed.append(sum(p not in {"TOWARD", "AWAY"} for p in pred) / len(pred))
        def mean(values: list[float]) -> float:
            return sum(values) / len(values)
        lines.append(
            f"| {model} | {max_tokens or 'task default'} | {len(epochs)} | "
            f"{_fmt(mean(robust_acc))} | {_fmt(mean(all_acc))} | "
            f"{_fmt(mean(balanced))} | {_fmt(mean(coeffs))} | {_fmt(mean(unparsed))} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_summary(path: Path, prediction_rows: list[dict] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_summary(prediction_rows))


def read_prediction_csv(path: Path) -> list[dict]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


TOLERANT_TASK = "gfp_tolerant_site"


def tolerant_site_rows(log_dir: Path) -> list[dict]:
    """Per-run tolerant-site results, scored strictly and by start only.

    The task scorer requires both an accepted start and a quoted triple that
    matches the reference sequence there. ``start_only`` drops the second
    requirement, which separates knowing a tolerant site from being able to
    index the sequence. ``expected`` is the number of accepted starts a uniform
    random guess would hit, summed over brackets.
    """
    from inspect_ai.log import read_eval_log

    runs: list[dict] = []
    for path in sorted(log_dir.glob("*.eval")):
        header = read_eval_log(str(path), header_only=True)
        # Task names are bare under `inspect eval path.py@name` and
        # package-qualified through the Python API; match the final segment.
        if header.status != "success":
            continue
        if (header.eval.task or "").rsplit("/", 1)[-1] != TOLERANT_TASK:
            continue
        log = read_eval_log(str(path))
        config = header.eval.model_generate_config
        strict = start_only = 0
        expected = 0.0
        brackets: list[str] = []
        for sample in log.samples or []:
            meta = sample.metadata or {}
            score = next(iter((sample.scores or {}).values()), None)
            smeta = (score.metadata or {}) if score is not None else {}
            accepted = smeta.get("start") in (meta.get("accepted_starts") or [])
            strict += int(score is not None and score.value == "C")
            start_only += int(accepted)
            expected += float(meta.get("chance") or 0.0)
            if accepted and not (score is not None and score.value == "C"):
                brackets.append(str(meta.get("bracket_id")))
        n = len(log.samples or [])
        runs.append(
            {
                "model": header.eval.model or "",
                "max_tokens": "" if config is None or config.max_tokens is None else config.max_tokens,
                "samples": n,
                "strict": strict,
                "start_only": start_only,
                "expected": expected,
                "indexing_losses": brackets,
            }
        )
    return runs


def render_tolerant_section(runs: list[dict]) -> str:
    if not runs:
        return ""
    lines = [
        "## Task 2: gfp_tolerant_site",
        "",
        "| Model | max_tokens | n | Strict | Start only | Expected by chance |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for run in runs:
        lines.append(
            f"| {run['model']} | {run['max_tokens'] or 'task default'} | {run['samples']} | "
            f"{run['strict']}/{run['samples']} | {run['start_only']}/{run['samples']} | "
            f"{run['expected']:.2f}/{run['samples']} |"
        )
    lines.append("")
    for run in runs:
        if run["indexing_losses"]:
            lines.append(
                f"`{run['model']}` named an accepted start but quoted a triple that does not "
                f"match the reference there in {len(run['indexing_losses'])} bracket(s): "
                + ", ".join(run["indexing_losses"])
                + ". Those count as incorrect under the task scorer."
            )
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    prediction_rows: list[dict] = []
    pred_dir = REPO_ROOT / "results" / "predictions"
    if pred_dir.exists():
        for path in sorted(pred_dir.glob("*.csv")):
            prediction_rows.extend(read_prediction_csv(path))
    out = REPO_ROOT / "results" / "summary.md"
    write_summary(out, prediction_rows or None)
    log_dir = REPO_ROOT / "results" / "logs"
    if log_dir.exists():
        section = render_tolerant_section(tolerant_site_rows(log_dir))
        if section:
            with out.open("a") as fh:
                fh.write("\n" + section)
    print(out)


if __name__ == "__main__":
    main()


__all__ = [
    "brier",
    "hydrophobicity_baselines",
    "per_strand_accuracy",
    "read_prediction_csv",
    "reliability_bins",
    "render_summary",
    "render_tolerant_section",
    "tolerant_site_rows",
    "write_summary",
]
