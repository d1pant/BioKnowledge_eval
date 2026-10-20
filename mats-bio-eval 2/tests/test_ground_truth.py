"""Recompute 1EMA labels and cross-check 1GFL. Needs the analysis extra."""

import csv
from dataclasses import asdict
from pathlib import Path

import pytest

from analysis.ground_truth.barrel_orientation import (
    chromophore_labels,
    compute_labels,
    load_chain,
    radial_components,
    strand_residues,
)

CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "bio_eval"
    / "tasks"
    / "gfp_barrel"
    / "data"
    / "gfp_strand_orientation.csv"
)


def _read_csv() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.analysis
def test_1ema_matches_packaged_csv():
    rows, _axis = compute_labels("1EMA")
    packaged = _read_csv()
    assert len(rows) == len(packaged) == 107
    labels = [row.ground_truth_label for row in rows]
    assert labels.count("inward") == 53
    assert labels.count("outward") == 54
    for got, expected in zip(rows, packaged):
        payload = asdict(got)
        for key, value in payload.items():
            assert str(value) == expected[key], (got.author_resnum, key, value, expected[key])


@pytest.mark.analysis
def test_1gfl_disagrees_only_on_fragile_end_residues():
    residues = strand_residues()
    resnums = [resnum for _sid, _index, resnum in residues]
    ema, _ = compute_labels("1EMA")
    truth = {row.author_resnum: row.ground_truth_label for row in ema}
    arr = load_chain("1GFL")
    _geom, axis = radial_components(arr, resnums)
    other = chromophore_labels(arr, resnums, axis)
    disagree = [resnum for resnum in resnums if other[resnum][0] != truth[resnum]]
    assert disagree == [115, 177]
