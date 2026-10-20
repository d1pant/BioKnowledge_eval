"""Five bracket samples. The prompt carries that bracket's own sequence."""

from __future__ import annotations

import json
from pathlib import Path

from inspect_ai.dataset import MemoryDataset, Sample

from bio_eval.tasks.gfp_tolerant_site.prompts import render_user_prompt

DATA_DIR = Path(__file__).resolve().parent / "data"
BRACKET_ORDER = ("1-50", "51-100", "101-150", "151-200", "200-238")


def reference_sequence() -> str:
    lines = (DATA_DIR / "avgfp_sarkisyan.fasta").read_text().splitlines()
    seq = "".join(line.strip() for line in lines if not line.startswith(">"))
    if len(seq) != 238:
        raise ValueError(f"Sarkisyan reference is {len(seq)} residues, expected 238")
    return seq


def load_brackets() -> list[dict]:
    payload = json.loads((DATA_DIR / "accepted_starts.json").read_text())
    sequence = reference_sequence()
    brackets = []
    for bracket_id in BRACKET_ORDER:
        info = payload[bracket_id]
        start, end = int(info["start"]), int(info["end"])
        starts = [int(value) for value in info["starts"]]
        possible = end - start + 1 - 2
        if possible <= 0:
            raise ValueError(f"{bracket_id} has no triplets")
        bracket_sequence = sequence[start - 1 : end]
        if len(bracket_sequence) != end - start + 1:
            raise ValueError(f"{bracket_id} sequence length {len(bracket_sequence)}")
        for triplet_start in starts:
            if not start <= triplet_start <= end - 2:
                raise ValueError(f"{triplet_start} is not inside {bracket_id}")
        brackets.append(
            {
                "bracket_id": bracket_id,
                "start": start,
                "end": end,
                "starts": starts,
                "chance": len(starts) / possible,
                "possible": possible,
                "sequence": bracket_sequence,
            }
        )
    return brackets


def record_to_sample(bracket: dict) -> Sample:
    return Sample(
        input=render_user_prompt(bracket["start"], bracket["end"], bracket["sequence"]),
        target=bracket["bracket_id"],
        id=f"gfp-{bracket['bracket_id']}",
        metadata={
            "bracket_id": bracket["bracket_id"],
            "start": bracket["start"],
            "end": bracket["end"],
            "chance": bracket["chance"],
            "accepted_starts": bracket["starts"],
            "reference_sequence": bracket["sequence"],
        },
    )


def build_dataset() -> MemoryDataset:
    return MemoryDataset([record_to_sample(bracket) for bracket in load_brackets()])
