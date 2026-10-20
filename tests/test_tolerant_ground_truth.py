"""Rebuild the tolerant-site key from the deposited assay. Needs the analysis extra.

`test_tolerant_reference.py` checks that accepted_starts.json agrees with triplet
letters transcribed from a design note. That catches a typo but not a mistake in the
derivation itself. These tests recompute the key from the released measurements.
"""

import json

import pytest

from analysis.ground_truth.tolerant_sites import (
    ASSAY_CSV,
    BRACKETS,
    CUTOFF,
    PACKAGED_KEY,
    compute_accepted_starts,
    load_singles,
    reference_sequence,
    tolerant_positions,
    verify_numbering,
)


@pytest.mark.analysis
def test_assay_matches_the_published_counts():
    """Guards against a truncated or re-curated copy of the CSV. Figures are the ones
    independently verified in results/validation/gfp-data-survey.md."""
    import csv

    with ASSAY_CSV.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 51714
    all_scores = [float(row["DMS_score"]) for row in rows]
    assert round(min(all_scores), 4) == 1.2834
    assert round(max(all_scores), 4) == 4.1231

    singles = load_singles()
    assert len(singles) == 1084
    positions = {pos for pos, _wt, _mut, _score in singles}
    assert len(positions) == 233
    assert min(positions) == 3 and max(positions) == 237
    assert sorted(set(range(1, 239)) - positions) == [1, 2, 119, 120, 238]


@pytest.mark.analysis
def test_single_mutant_bright_dark_split():
    """The survey records 993 bright and 91 dark singles at the 2.5 cutoff. This is a
    direct check that the cutoff is being applied the way the key assumes."""
    scores = [score for *_rest, score in load_singles()]
    assert sum(score >= CUTOFF for score in scores) == 993
    assert sum(score < CUTOFF for score in scores) == 91


@pytest.mark.analysis
def test_assay_numbering_matches_the_reference_fasta():
    """Every single mutant's wild-type letter must sit where the assay says it does."""
    assert verify_numbering(load_singles(), reference_sequence()) == 0


@pytest.mark.analysis
def test_packaged_key_is_reproducible_from_the_assay():
    rebuilt = compute_accepted_starts()
    packaged = json.loads(PACKAGED_KEY.read_text())
    assert list(rebuilt) == list(packaged)
    for bracket_id, info in rebuilt.items():
        assert info["starts"] == packaged[bracket_id]["starts"], bracket_id
        assert info["start"] == packaged[bracket_id]["start"]
        assert info["end"] == packaged[bracket_id]["end"]
    assert [len(info["starts"]) for info in rebuilt.values()] == [15, 7, 22, 35, 20]


@pytest.mark.analysis
def test_every_accepted_start_is_three_tolerant_positions():
    tolerant = tolerant_positions(load_singles())
    packaged = json.loads(PACKAGED_KEY.read_text())
    for bracket_id, start, end in BRACKETS:
        for value in packaged[bracket_id]["starts"]:
            assert {value, value + 1, value + 2} <= tolerant, (bracket_id, value)
            assert start <= value <= end - 2


@pytest.mark.analysis
def test_rejected_starts_have_a_reason():
    """Any start left out must have a non-tolerant position in its window, so the key
    is not merely a subset of the valid answers."""
    singles = load_singles()
    tolerant = tolerant_positions(singles)
    measured = {pos for pos, _wt, _mut, _score in singles}
    packaged = json.loads(PACKAGED_KEY.read_text())
    for bracket_id, start, end in BRACKETS:
        accepted = set(packaged[bracket_id]["starts"])
        for value in range(start, end - 1):
            if value in accepted:
                continue
            window = {value, value + 1, value + 2}
            assert not window <= tolerant, (bracket_id, value)
            # the reason is either an unmeasured position or a dark substitution
            assert window - measured or window & measured - tolerant


@pytest.mark.analysis
def test_cutoff_is_the_proteingym_binarisation_threshold():
    """2.5 is not a free parameter; it is the cutoff shipped with the assay."""
    assert CUTOFF == 2.5
    singles = load_singles()
    strict = tolerant_positions(singles, cutoff=3.0)
    assert strict < tolerant_positions(singles, cutoff=CUTOFF)
