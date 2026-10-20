"""Rebuild the gfp_tolerant_site answer key from the released Sarkisyan assay.

The runtime package ships `accepted_starts.json`. Before this module existed, that
file was only checked for self-consistency against the reference FASTA, so a
mistake made while deriving it would have been transcribed rather than caught.
Here the key is recomputed from the deposited measurements instead, the same way
`barrel_orientation` recomputes the orientation labels from 1EMA.

Rule, as stated in the README: a position is tolerant when, among the measured
single missense mutants at that position, at least one is bright and none is
dark. Bright and dark are split at ProteinGym's binarisation cutoff of 2.5. A
working answer for a bracket is a start `s` with `s`, `s+1` and `s+2` all
tolerant and `s + 2` inside the bracket.

Positions in the `mutant` column are 1-based on the 238-residue reference in
`avgfp_sarkisyan.fasta`. `verify_numbering` asserts that rather than assuming it.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSAY_CSV = Path(__file__).resolve().parent / "data" / "GFP_AEQVI_Sarkisyan_2016.csv"
REFERENCE_FASTA = (
    REPO_ROOT / "src" / "bio_eval" / "tasks" / "gfp_tolerant_site" / "data" / "avgfp_sarkisyan.fasta"
)
PACKAGED_KEY = (
    REPO_ROOT / "src" / "bio_eval" / "tasks" / "gfp_tolerant_site" / "data" / "accepted_starts.json"
)

# ProteinGym `DMS_binarization_cutoff` for this assay.
CUTOFF = 2.5

# Bracket bounds are a design choice, not a measurement, so they are declared
# here rather than read back from the file this module exists to check.
BRACKETS: tuple[tuple[str, int, int], ...] = (
    ("1-50", 1, 50),
    ("51-100", 51, 100),
    ("101-150", 101, 150),
    ("151-200", 151, 200),
    ("200-238", 200, 238),
)


def reference_sequence(path: Path | None = None) -> str:
    lines = (path or REFERENCE_FASTA).read_text().splitlines()
    return "".join(line.strip() for line in lines if not line.startswith(">"))


def load_singles(path: Path | None = None) -> list[tuple[int, str, str, float]]:
    """Single missense mutants as (position, wild_type, mutant, score)."""
    rows: list[tuple[int, str, str, float]] = []
    with (path or ASSAY_CSV).open(newline="") as fh:
        for record in csv.DictReader(fh):
            mutant = record["mutant"]
            if ":" in mutant:  # multi-mutant genotype
                continue
            rows.append((int(mutant[1:-1]), mutant[0], mutant[-1], float(record["DMS_score"])))
    return rows


def verify_numbering(singles: list[tuple[int, str, str, float]], sequence: str) -> int:
    """Return the number of singles whose wild-type letter contradicts the reference."""
    return sum(1 for pos, wt, _mut, _score in singles if sequence[pos - 1] != wt)


def tolerant_positions(
    singles: list[tuple[int, str, str, float]], cutoff: float = CUTOFF
) -> set[int]:
    scores: dict[int, list[float]] = defaultdict(list)
    for pos, _wt, _mut, score in singles:
        scores[pos].append(score)
    return {
        pos
        for pos, values in scores.items()
        if any(value >= cutoff for value in values) and not any(value < cutoff for value in values)
    }


def compute_accepted_starts(
    assay_csv: Path | None = None, cutoff: float = CUTOFF
) -> dict[str, dict]:
    """The packaged key, rebuilt from the assay. Same shape as accepted_starts.json."""
    singles = load_singles(assay_csv)
    sequence = reference_sequence()
    mismatches = verify_numbering(singles, sequence)
    if mismatches:
        raise ValueError(
            f"{mismatches} single mutants disagree with the reference sequence; "
            "the position numbering of the assay and the FASTA do not match"
        )
    tolerant = tolerant_positions(singles, cutoff)
    payload: dict[str, dict] = {}
    for bracket_id, start, end in BRACKETS:
        starts = [p for p in range(start, end - 1) if {p, p + 1, p + 2} <= tolerant]
        payload[bracket_id] = {"start": start, "end": end, "starts": starts}
    return payload


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="write the rebuilt key here instead of comparing")
    args = parser.parse_args()
    rebuilt = compute_accepted_starts()
    if args.out:
        Path(args.out).write_text(json.dumps(rebuilt, indent=2) + "\n")
        print(args.out)
        return
    packaged = json.loads(PACKAGED_KEY.read_text())
    for bracket_id, info in rebuilt.items():
        theirs = packaged.get(bracket_id, {}).get("starts")
        mark = "match" if theirs == info["starts"] else "DIFFERS"
        print(f"{bracket_id:>8}  rebuilt {len(info['starts']):>3}  packaged "
              f"{len(theirs) if theirs is not None else '-':>3}  {mark}")
    identical = all(
        packaged.get(bid, {}).get("starts") == info["starts"] for bid, info in rebuilt.items()
    )
    print("packaged key reproduces from the assay" if identical else "PACKAGED KEY DOES NOT MATCH")
    raise SystemExit(0 if identical else 1)


if __name__ == "__main__":
    main()
