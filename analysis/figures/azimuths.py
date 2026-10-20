"""Barrel-axis azimuths. The results figure reads the cached JSON.

``strand_azimuths()`` refits the 400-start cylinder. Call it only to refresh
``strand_azimuths.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from analysis.ground_truth import barrel_orientation as bo

CACHE = Path(__file__).with_name("strand_azimuths.json")


def strand_azimuths() -> dict[str, float]:
    """Mean azimuth (deg) of each strand's CAs around the fitted barrel axis in 1EMA."""
    arr = bo.load_chain("1EMA")
    residues = bo.strand_residues()
    ca = bo.strand_cas(arr, [resnum for *_, resnum in residues])
    axis, _, _ = bo.fit_barrel_axis(ca)
    direction = axis.direction
    e1 = np.cross(direction, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(direction, e1)
    offset = ca - axis.center
    ang = np.arctan2(offset @ e2, offset @ e1)
    out = {}
    for strand_id in bo.STRAND_IDS:
        values = ang[[i for i, (sid, _, _) in enumerate(residues) if sid == strand_id]]
        out[strand_id] = float(
            np.degrees(np.arctan2(np.sin(values).mean(), np.cos(values).mean())) % 360
        )
    return out


def cached_azimuths() -> dict[str, float]:
    payload = json.loads(CACHE.read_text())
    return {strand_id: float(angle) for strand_id, angle in payload.items()}
