"""One structural lookup. Fluorescence labels are not in this tool."""

from __future__ import annotations

import csv
from pathlib import Path

from inspect_ai.tool import Tool, tool
from inspect_ai.util import store

CSV_PATH = (
    Path(__file__).resolve().parents[1] / "gfp_barrel" / "data" / "gfp_strand_orientation.csv"
)
CALL_LIMIT = 5
LIMIT_ERROR = "residue_orientation is limited to 5 calls. No orientation is available."
_STORE_KEY = "orientation_calls"
_TO_LABEL = {"inward": "TOWARD", "outward": "AWAY"}


def _orientation_table() -> dict[int, tuple[str, str]]:
    table: dict[int, tuple[str, str]] = {}
    with CSV_PATH.open(newline="") as fh:
        for row in csv.DictReader(fh):
            table[int(row["author_resnum"])] = (
                row["strand_id"],
                _TO_LABEL[row["ground_truth_label"]],
            )
    return table


_ORIENTATION = _orientation_table()


@tool
def residue_orientation() -> Tool:
    async def execute(position: int) -> str:
        """Say whether a GFP side chain points toward the chromophore or away from it.

        The result does not say whether a change at this position fluoresced.

        Args:
            position: Residue number in the 238-amino-acid sequence.
        """
        state = store()
        used = int(state.get(_STORE_KEY, 0))
        if used >= CALL_LIMIT:
            return LIMIT_ERROR
        if isinstance(position, bool) or not isinstance(position, int) or not 1 <= position <= 238:
            return "residue_orientation: position must be an integer from 1 to 238."
        state.set(_STORE_KEY, used + 1)
        found = _ORIENTATION.get(position)
        if found is None:
            return "in_strand: false"
        strand_id, label = found
        return f"in_strand: true; strand_id: {strand_id}; orientation: {label}"

    return execute
