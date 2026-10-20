"""Write ``strand_sequences.json`` from the 1EMA author sequence.

Run as ``python -m analysis.ground_truth.build_strand_sequences``.
The runtime task reads the JSON and never opens a structure.
"""

from __future__ import annotations

import json

import biotite.structure as struc

from analysis.ground_truth.barrel_orientation import (
    DATA_DIR,
    STRAND_IDS,
    STRANDS_1EMA,
    THREE_TO_ONE,
    load_chain,
)


def strand_sequences() -> dict[str, dict]:
    arr = load_chain("1EMA")
    res_ids, res_names = struc.get_residues(arr)
    aa = {
        int(rid): THREE_TO_ONE[name]
        for rid, name in zip(res_ids, res_names)
        if name in THREE_TO_ONE
    }
    out: dict[str, dict] = {}
    for strand_id, (start, end) in zip(STRAND_IDS, STRANDS_1EMA):
        out[strand_id] = {
            "start": start,
            "end": end,
            "sequence": "".join(aa[i] for i in range(start, end + 1)),
        }
    return out


def main() -> None:
    payload = strand_sequences()
    path = DATA_DIR / "strand_sequences.json"
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(path)


if __name__ == "__main__":
    main()
