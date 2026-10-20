"""Pull per-epoch orientation answers out of Inspect logs. No API keys."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log, read_eval_log_samples

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "results" / "predictions"
ORIENTATION_TASK = "gfp_barrel_orientation"
COLUMNS = [
    "model",
    "max_tokens",
    "log_file",
    "run_id",
    "author_resnum",
    "strand_id",
    "epoch",
    "label",
    "confidence",
    "correct",
    "robust",
    "raw",
]


def _log_files(paths: list[str]) -> list[str]:
    files: list[str] = []
    for path in paths:
        candidate = Path(path)
        if candidate.is_dir():
            files.extend(info.name for info in list_eval_logs(str(candidate)))
        else:
            files.append(str(candidate))
    return files


def _assistant_text(sample) -> str:
    for message in reversed(sample.messages):
        if message.role == "assistant":
            return message.text or ""
    return ""


def extract(log_paths: list[str], out_dir: Path | None = None) -> list[dict]:
    """Read successful logs and write one CSV per log under ``out_dir``."""
    destination = Path(out_dir) if out_dir is not None else DEFAULT_OUT
    destination.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for path in _log_files(log_paths):
        header = read_eval_log(path, header_only=True)
        if header.status != "success":
            continue
        # Only the orientation task has one scored residue per sample. Agent logs
        # (gfp_tolerant_site) carry no author_resnum and belong to a different
        # scorer, so they are not summarised here. The recorded task name is
        # bare under `inspect eval path.py@name` and package-qualified
        # ("bio_eval/...") through the Python API, so match the final segment.
        if (header.eval.task or "").rsplit("/", 1)[-1] != ORIENTATION_TASK:
            continue
        model = header.eval.model or ""
        run_id = header.eval.run_id or Path(path).stem
        config = header.eval.model_generate_config
        max_tokens = "" if config is None or config.max_tokens is None else config.max_tokens
        log_rows: list[dict] = []
        for sample in read_eval_log_samples(path):
            score = (sample.scores or {}).get("orientation_scorer")
            if score is None and sample.scores:
                score = next(iter(sample.scores.values()))
            metadata = sample.metadata or {}
            answer = score.answer if score is not None else "UNPARSED"
            confidence = None if score is None else (score.metadata or {}).get("confidence")
            truth = metadata.get("truth")
            log_rows.append(
                {
                    "model": model,
                    "max_tokens": max_tokens,
                    "log_file": str(path),
                    "run_id": run_id,
                    "author_resnum": metadata.get("author_resnum"),
                    "strand_id": metadata.get("strand_id"),
                    "epoch": sample.epoch,
                    "label": answer or "UNPARSED",
                    "confidence": "" if confidence is None else confidence,
                    "correct": answer == truth,
                    "robust": bool(metadata.get("robust")),
                    "raw": _assistant_text(sample),
                }
            )
        slug = model.replace("/", "__") or "model"
        out_path = destination / f"{slug}__{run_id}.csv"
        with out_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(log_rows)
        rows.extend(log_rows)
    return rows


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        raise SystemExit("usage: python -m analysis.extract_predictions LOG [LOG ...]")
    written = extract(args)
    print(f"{len(written)} rows")


if __name__ == "__main__":
    main()
