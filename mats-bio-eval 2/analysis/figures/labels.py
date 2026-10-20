"""Read the packaged orientation CSV for figure code."""

from __future__ import annotations

import csv

from analysis.ground_truth import barrel_orientation as bo


def load_rows() -> list[dict]:
    with open(bo.DATA_DIR / "gfp_strand_orientation.csv") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row["index_in_strand"] = int(row["index_in_strand"])
        row["author_resnum"] = int(row["author_resnum"])
        row["truth"] = row["ground_truth_label"]
        row["pred"] = row["hydrophobicity_prediction"]
    return rows
