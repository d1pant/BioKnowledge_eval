"""107 one-residue samples. The user prompt is rendered into ``Sample.input``."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from inspect_ai.dataset import MemoryDataset, Sample

from bio_eval.tasks.gfp_barrel.prompts import (
    ONE_TO_THREE,
    render_user_prompt,
    strand_context,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
ROBUST_COS_THRESHOLD = 0.2
_TO_LABEL = {"inward": "TOWARD", "outward": "AWAY"}


def load_rows() -> list[dict]:
    """Join the packaged CSV with the 1EMA strand sequences.

    The strand-sequence letter at each index must match the CSV ``aa`` column.
    """
    strands = json.loads((DATA_DIR / "strand_sequences.json").read_text())
    with (DATA_DIR / "gfp_strand_orientation.csv").open(newline="") as fh:
        raw = list(csv.DictReader(fh))
    rows: list[dict] = []
    for rec in raw:
        strand_id = rec["strand_id"]
        info = strands[strand_id]
        index = int(rec["index_in_strand"])
        sequence = info["sequence"]
        if sequence[index] != rec["aa"]:
            raise ValueError(
                f"{strand_id} index {index}: sequence {sequence[index]!r} "
                f"!= CSV aa {rec['aa']!r}"
            )
        author = int(rec["author_resnum"])
        cosine = float(rec["chromophore_cosine"])
        start, end = int(info["start"]), int(info["end"])
        context = strand_context(sequence, start, author)
        if context[context.index("[") + 1] != rec["aa"]:
            raise ValueError(f"bracketed residue in {context} is not {rec['aa']}")
        rows.append(
            {
                "author_resnum": author,
                "aa": rec["aa"],
                "aa_three": ONE_TO_THREE[rec["aa"]],
                "strand_id": strand_id,
                "strand_start": start,
                "strand_end": end,
                "strand_context": context,
                "index_in_strand": index,
                "truth": _TO_LABEL[rec["ground_truth_label"]],
                "chromophore_cosine": cosine,
                "robust": abs(cosine) >= ROBUST_COS_THRESHOLD,
                "hydrophobicity_prediction": rec["hydrophobicity_prediction"],
                "cylinder_axis_label": rec["cylinder_axis_label"],
            }
        )
    return rows


def record_to_sample(row: dict) -> Sample:
    return Sample(
        input=render_user_prompt(row),
        target=row["truth"],
        id=f"gfp-{row['author_resnum']}",
        metadata={
            "author_resnum": row["author_resnum"],
            "aa": row["aa"],
            "strand_id": row["strand_id"],
            "index_in_strand": row["index_in_strand"],
            "truth": row["truth"],
            "chromophore_cosine": row["chromophore_cosine"],
            "robust": row["robust"],
            "hydrophobicity_prediction": row["hydrophobicity_prediction"],
            "cylinder_axis_label": row["cylinder_axis_label"],
        },
    )


def build_dataset(subset: str = "all") -> MemoryDataset:
    samples = [record_to_sample(row) for row in load_rows()]
    if subset == "robust":
        samples = [sample for sample in samples if sample.metadata["robust"]]
    elif subset != "all":
        raise ValueError(f"subset must be 'all' or 'robust', got {subset!r}")
    return MemoryDataset(samples)
