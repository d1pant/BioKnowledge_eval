"""Geometric inward/outward labels for the 11 beta-barrel strands of avGFP.

Run as ``python -m analysis.ground_truth.barrel_orientation`` to regenerate
``src/bio_eval/tasks/gfp_barrel/data/gfp_strand_orientation.csv`` and the
three figures under ``results/validation/``; validation metrics are printed
as JSON.

Ground truth (``ground_truth_label``)
-------------------------------------
Matches the eval question "does this side chain point toward the chromophore
at the centre of the barrel, or away from it": ``inward`` if
``v . (CRO centroid - CA) > 0``, else ``outward``, with ``v`` as in step 3
below and the CRO centroid the mean of all CRO atoms at author 66.

Cross-check (``cylinder_axis_label``)
-------------------------------------
1. Barrel axis: a least-squares cylinder (axis point ``c``, unit direction
   ``u``, radius ``R``) fitted to the CA atoms of every residue in the 11
   deposited 1EMA strands, minimising sum((dist(CA, axis) - R)^2), with
   multi-start over 400 seed directions. The first principal axis of the
   same CAs is NOT usable: the strand-CA cloud is nearly isotropic
   (variances 75/70/49 A^2) and PC1 lies ~85 deg off the barrel axis. The
   fit is cross-checked against an independent axis, the principal
   eigenvector of sum(d d^T) over strand direction vectors d.
2. For each strand residue with CA position ``p``, the outward radial unit
   vector is ``r = perp(p - c) / |perp(p - c)|``, where ``perp`` removes the
   component along ``u``.
3. Side-chain vector ``v = centroid(heavy side-chain atoms) - CA``; side-chain
   atoms are all heavy atoms except N, CA, C, O, OXT. For Gly (or any residue
   with no modelled side-chain atoms) ``v = CB_virtual - CA``, with the
   virtual CB placed from N, CA, C using ideal tetrahedral geometry.
4. ``radial_component = v . r`` (Angstrom). ``> 0`` -> ``outward``,
   ``<= 0`` -> ``inward``. No solvent accessibility is used.

Numbering
---------
Author numbering (``use_author_fields=True``) everywhere; it equals canonical
UniProt P42212 numbering (Met1 = 1) and ProteinGym numbering. Every loaded
chain is asserted residue-by-residue against P42212 so a label_seq_id
frameshift (which drifts by -2 after the fused chromophore) fails loudly.

Chromophore
-----------
1EMA models Ser65-Tyr66-Gly67 as one fused residue ``CRO`` at author 66;
author 65 and 67 do not exist. None of 65-67 lies in a deposited strand
(beta3 ends at 48, beta4 starts at 92), so they receive no label. CRO is kept
in the atom set for SASA so it still occludes its neighbours, but it gets no
RSA of its own.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import biotite.structure as struc
import biotite.structure.io.pdbx as pdbx
import numpy as np
from scipy.optimize import least_squares

PKG_DIR = Path(__file__).resolve().parent
STRUCT_DIR = PKG_DIR / "structures"
REPO_ROOT = PKG_DIR.parent.parent
VALIDATION_DIR = REPO_ROOT / "results" / "validation"
# Labels are packaged with the Inspect task. Structures stay here.
DATA_DIR = REPO_ROOT / "src" / "bio_eval" / "tasks" / "gfp_barrel" / "data"

# Deposited 1EMA struct_sheet_range rows, sorted N->C; asserted against the CIF.
STRANDS_1EMA: list[tuple[int, int]] = [
    (12, 22), (25, 36), (41, 48), (92, 100), (105, 115), (118, 128),
    (148, 152), (160, 170), (176, 187), (199, 207), (220, 227),
]
STRAND_IDS = [f"b{i}" for i in range(1, 12)]

# Deviations from P42212 found in the coordinates. 1EMA carries Q80R (its
# entity sequence reads ...HMKRHDFF...), contrary to the data survey. 1EMA is
# also S65T, but residue 65 is fused into CRO so it cannot be checked.
EXPECTED_DIFFS: dict[str, dict[int, str]] = {"1EMA": {80: "R"}, "1GFL": {1: "A", 80: "R"}}
FUSED_CHROMOPHORE = {"CRO", "GYS"}

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V", "MSE": "M",
}

# Tien et al. 2013, PLoS ONE 8:e80635, "theoretical" max ASA (A^2).
MAX_ASA_TIEN2013 = {
    "A": 129.0, "R": 274.0, "N": 195.0, "D": 193.0, "C": 167.0, "Q": 225.0,
    "E": 223.0, "G": 104.0, "H": 224.0, "I": 197.0, "L": 201.0, "K": 236.0,
    "M": 224.0, "F": 240.0, "P": 159.0, "S": 155.0, "T": 172.0, "W": 285.0,
    "Y": 263.0, "V": 174.0,
}
RSA_BURIED_THRESHOLD = 0.20

# Kyte & Doolittle 1982, J Mol Biol 157:105. Rule: KD > 0 -> inward.
KYTE_DOOLITTLE = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5,
    "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8,
    "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}
KD_THRESHOLD = 0.0

BACKBONE = {"N", "CA", "C", "O", "OXT"}


@dataclass
class ResidueLabel:
    position: int
    author_resnum: int
    aa: str
    strand_id: str
    index_in_strand: int
    ground_truth_label: str
    chromophore_cosine: float
    axial_offset_from_chromophore: float
    cylinder_axis_label: str
    cylinder_radial_component: float
    cylinder_radial_cosine: float
    direction_source: str
    rsa: float | None
    rsa_label: str | None
    kd_hydrophobicity: float
    hydrophobicity_prediction: str


def reference_sequence() -> str:
    lines = (STRUCT_DIR / "P42212.fasta").read_text().splitlines()
    seq = "".join(line.strip() for line in lines if not line.startswith(">"))
    assert len(seq) == 238, len(seq)
    return seq


def load_chain(pdb_id: str, chain: str = "A") -> struc.AtomArray:
    cif = pdbx.CIFFile.read(STRUCT_DIR / f"{pdb_id}.cif")
    arr = pdbx.get_structure(cif, model=1, use_author_fields=True)
    keep = (arr.chain_id == chain) & np.isin(
        arr.res_name, list(THREE_TO_ONE) + list(FUSED_CHROMOPHORE)
    )
    arr = arr[keep & (arr.element != "H")]
    assert_author_numbering(arr, pdb_id)
    return arr


def assert_author_numbering(arr: struc.AtomArray, pdb_id: str) -> None:
    """Fail unless every residue matches P42212 at its author number."""
    ref = reference_sequence()
    diffs = EXPECTED_DIFFS[pdb_id]
    res_ids, res_names = struc.get_residues(arr)
    for rid, name in zip(res_ids, res_names):
        rid = int(rid)
        if name in FUSED_CHROMOPHORE:
            assert rid == 66, f"{pdb_id}: chromophore {name} at {rid}, expected 66"
            assert 65 not in res_ids and 67 not in res_ids, f"{pdb_id}: 65/67 present"
            continue
        expected = diffs.get(rid, ref[rid - 1])
        got = THREE_TO_ONE[name]
        assert got == expected, f"{pdb_id} author {rid}: {name} != expected {expected}"
    # Spot checks from the survey's recommended recipe.
    lookup = dict(zip(res_ids.tolist(), res_names.tolist()))
    assert lookup[96] == "ARG" and lookup[110] == "ALA" and lookup[222] == "GLU"


def deposited_strands(pdb_id: str = "1EMA", chain: str = "A") -> list[tuple[int, int]]:
    sheet = pdbx.CIFFile.read(STRUCT_DIR / f"{pdb_id}.cif").block["struct_sheet_range"]
    beg = sheet["beg_auth_seq_id"].as_array(int)
    end = sheet["end_auth_seq_id"].as_array(int)
    asym = sheet["beg_auth_asym_id"].as_array()
    return sorted((int(b), int(e)) for b, e, a in zip(beg, end, asym) if a == chain)


def strand_residues() -> list[tuple[str, int, int]]:
    """(strand_id, index_in_strand, author_resnum) for every strand residue."""
    assert deposited_strands("1EMA") == STRANDS_1EMA
    return [
        (sid, i, r)
        for sid, (b, e) in zip(STRAND_IDS, STRANDS_1EMA)
        for i, r in enumerate(range(b, e + 1))
    ]


def _atom(res: struc.AtomArray, name: str) -> np.ndarray:
    sel = res[res.atom_name == name]
    assert sel.array_length() == 1, f"{res.res_name[0]}{res.res_id[0]} missing {name}"
    return sel.coord[0]


def virtual_cb(n: np.ndarray, ca: np.ndarray, c: np.ndarray) -> np.ndarray:
    b = ca - n
    cvec = c - ca
    a = np.cross(b, cvec)
    return -0.58273431 * a + 0.56802827 * b - 0.54067466 * cvec + ca


def sidechain_vector(res: struc.AtomArray) -> tuple[np.ndarray, str]:
    ca = _atom(res, "CA")
    sc = res[~np.isin(res.atom_name, list(BACKBONE))]
    if sc.array_length() > 0:
        return sc.coord.mean(axis=0) - ca, "sidechain_centroid"
    return virtual_cb(_atom(res, "N"), ca, _atom(res, "C")) - ca, "virtual_cb"


@dataclass
class Axis:
    center: np.ndarray
    direction: np.ndarray


def pca_axis(points: np.ndarray) -> Axis:
    center = points.mean(axis=0)
    _, _, vt = np.linalg.svd(points - center, full_matrices=False)
    return Axis(center, vt[0] / np.linalg.norm(vt[0]))


def radial_distances(points: np.ndarray, axis: Axis) -> np.ndarray:
    d = points - axis.center
    perp = d - np.outer(d @ axis.direction, axis.direction)
    return np.linalg.norm(perp, axis=1)


def cylinder_axis(points: np.ndarray, start: Axis) -> tuple[Axis, float]:
    """Least-squares cylinder fit seeded from ``start``; returns (axis, radius)."""
    u0 = start.direction
    e1 = np.cross(u0, [1.0, 0.0, 0.0])
    if np.linalg.norm(e1) < 1e-3:
        e1 = np.cross(u0, [0.0, 1.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(u0, e1)

    def unpack(x):
        u = u0 + x[0] * e1 + x[1] * e2
        u /= np.linalg.norm(u)
        return Axis(start.center + x[2] * e1 + x[3] * e2, u), x[4]

    def resid(x):
        ax, radius = unpack(x)
        return radial_distances(points, ax) - radius

    r0 = radial_distances(points, start).mean()
    fit = least_squares(resid, np.array([0.0, 0.0, 0.0, 0.0, r0]))
    return unpack(fit.x)


def _fibonacci_sphere(n: int) -> np.ndarray:
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - i / n)
    theta = np.pi * (1 + 5**0.5) * i
    return np.c_[np.cos(theta) * np.sin(phi), np.sin(theta) * np.sin(phi), np.cos(phi)]


def fit_barrel_axis(points: np.ndarray, n_starts: int = 400) -> tuple[Axis, float, float]:
    """Global cylinder fit; returns (axis, radius, rms residual)."""
    best = None
    for u in _fibonacci_sphere(n_starts):
        axis, radius = cylinder_axis(points, Axis(points.mean(axis=0), u))
        cost = float(np.sum((radial_distances(points, axis) - radius) ** 2))
        if best is None or cost < best[0]:
            best = (cost, axis, radius)
    cost, axis, radius = best
    return axis, float(radius), float(np.sqrt(cost / len(points)))


def strand_direction_axis(arr: struc.AtomArray, center: np.ndarray) -> Axis:
    """Principal eigenvector of sum(d d^T) over unit strand vectors (sign-free)."""
    tensor = np.zeros((3, 3))
    for b, e in STRANDS_1EMA:
        d = _atom(arr[arr.res_id == e], "CA") - _atom(arr[arr.res_id == b], "CA")
        d /= np.linalg.norm(d)
        tensor += np.outer(d, d)
    return Axis(center, np.linalg.eigh(tensor)[1][:, -1])


def strand_cas(arr: struc.AtomArray, resnums: list[int]) -> np.ndarray:
    return np.array([_atom(arr[arr.res_id == r], "CA") for r in resnums])


def radial_components(
    arr: struc.AtomArray, resnums: list[int], axis: Axis | None = None
) -> tuple[dict[int, tuple[float, float, str]], Axis]:
    """Map resnum -> (radial_component, cosine, direction_source)."""
    cas = strand_cas(arr, resnums)
    axis = axis or fit_barrel_axis(cas)[0]
    out = {}
    for r, ca in zip(resnums, cas):
        v, source = sidechain_vector(arr[arr.res_id == r])
        d = ca - axis.center
        perp = d - (d @ axis.direction) * axis.direction
        rhat = perp / np.linalg.norm(perp)
        comp = float(v @ rhat)
        out[r] = (comp, comp / float(np.linalg.norm(v)), source)
    return out, axis


def relative_solvent_accessibility(arr: struc.AtomArray) -> dict[int, float]:
    """Shrake-Rupley (biotite, 1000 points, 'Single' radii) / Tien 2013 max ASA."""
    sasa = struc.sasa(arr, vdw_radii="Single", point_number=1000)
    per_res = struc.apply_residue_wise(arr, sasa, np.nansum)
    res_ids, res_names = struc.get_residues(arr)
    return {
        int(rid): float(area) / MAX_ASA_TIEN2013[THREE_TO_ONE[name]]
        for rid, name, area in zip(res_ids, res_names, per_res)
        if name in THREE_TO_ONE
    }


def label_of(component: float) -> str:
    return "outward" if component > 0 else "inward"


def chromophore_centroid(arr: struc.AtomArray) -> np.ndarray:
    """Centroid of the fused CRO residue, or of residues 65-67 where unfused (1GFL)."""
    cro = arr[np.isin(arr.res_name, list(FUSED_CHROMOPHORE))]
    if cro.array_length() > 0:
        assert set(cro.res_id) == {66}
    else:
        cro = arr[np.isin(arr.res_id, [65, 66, 67])]
        assert list(struc.get_residues(cro)[1]) == ["SER", "TYR", "GLY"]
    return cro.coord.mean(axis=0)


def chromophore_labels(
    arr: struc.AtomArray, resnums: list[int], axis: Axis
) -> dict[int, tuple[str, float, float]]:
    """Ground-truth rule: inward if (side-chain centroid - CA) . (CRO centroid - CA) > 0.

    Returns resnum -> (label, cosine of that angle, CA position along the
    barrel axis relative to the chromophore centroid in A).
    """
    cro = chromophore_centroid(arr)
    cro_z = (cro - axis.center) @ axis.direction
    out = {}
    for r in resnums:
        res = arr[arr.res_id == r]
        ca = _atom(res, "CA")
        v, _ = sidechain_vector(res)
        w = cro - ca
        cosine = float(v @ w / (np.linalg.norm(v) * np.linalg.norm(w)))
        out[r] = (
            "inward" if cosine > 0 else "outward",
            cosine,
            float((ca - axis.center) @ axis.direction - cro_z),
        )
    return out


def compute_labels(pdb_id: str = "1EMA", chain: str = "A") -> tuple[list[ResidueLabel], Axis]:
    arr = load_chain(pdb_id, chain)
    residues = strand_residues()
    resnums = [r for _, _, r in residues]
    geom, axis = radial_components(arr, resnums)
    chrom = chromophore_labels(arr, resnums, axis)
    rsa = relative_solvent_accessibility(arr)
    names = dict(zip(*[x.tolist() for x in struc.get_residues(arr)]))
    rows = []
    for sid, idx, r in residues:
        aa = THREE_TO_ONE[names[r]]
        comp, cosine, source = geom[r]
        chrom_label, chrom_cos, axial = chrom[r]
        res_rsa = rsa.get(r)
        kd = KYTE_DOOLITTLE[aa]
        rows.append(ResidueLabel(
            position=r,
            author_resnum=r,
            aa=aa,
            strand_id=sid,
            index_in_strand=idx,
            ground_truth_label=chrom_label,
            chromophore_cosine=round(chrom_cos, 3),
            axial_offset_from_chromophore=round(axial, 2),
            cylinder_axis_label=label_of(comp),
            cylinder_radial_component=round(comp, 3),
            cylinder_radial_cosine=round(cosine, 3),
            direction_source=source,
            rsa=None if res_rsa is None else round(res_rsa, 4),
            rsa_label=None if res_rsa is None else (
                "inward" if res_rsa < RSA_BURIED_THRESHOLD else "outward"),
            kd_hydrophobicity=kd,
            hydrophobicity_prediction="inward" if kd > KD_THRESHOLD else "outward",
        ))
    return rows, axis


def coin_flip(n: int, seed: int = 0) -> list[str]:
    rng = np.random.default_rng(seed)
    return ["inward" if x else "outward" for x in rng.random(n) < 0.5]


def accuracy(pred: list[str], truth: list[str]) -> float:
    return float(np.mean([p == t for p, t in zip(pred, truth)]))


def within_strand_autocorrelation(
    rows: list[ResidueLabel], values: list[float], lag: int
) -> tuple[float, int]:
    """Pearson r over all (i, i+lag) pairs that lie in the same strand."""
    by_key = {(r.strand_id, r.index_in_strand): v for r, v in zip(rows, values)}
    xs, ys = [], []
    for (sid, idx), v in by_key.items():
        w = by_key.get((sid, idx + lag))
        if v is not None and w is not None:
            xs.append(v)
            ys.append(w)
    return float(np.corrcoef(xs, ys)[0, 1]), len(xs)


# Chromophore-cavity residues whose side chains contact the chromophore
# (Ormo et al. 1996; Tsien 1998) and dimer-interface residues on the barrel
# surface (A206, L221, F223; Zacharias et al. 2002, Science 296:913).
KNOWN_INWARD = [94, 96, 148, 165, 167, 183, 203, 205, 222]
KNOWN_OUTWARD = [206, 221, 223]
# Strand CAs span roughly -19 to +12 A along the axis relative to the chromophore.
END_ZONE_A = 10.0


def _sign(labels: list[str]) -> list[float]:
    return [1.0 if lab == "inward" else -1.0 for lab in labels]


def validate(rows: list[ResidueLabel], axis: Axis) -> dict:
    truth = [r.ground_truth_label for r in rows]
    cyl = [r.cylinder_axis_label for r in rows]
    n = len(rows)
    metrics: dict = {
        "n_labelled": n,
        "ground_truth_rule": "inward if (side-chain centroid - CA) . (CRO centroid - CA) > 0",
    }
    metrics["class_balance"] = {
        "inward": truth.count("inward"), "outward": truth.count("outward"),
    }

    with_rsa = [(r, t) for r, t in zip(rows, truth) if r.rsa_label is not None]
    metrics["truth_vs_rsa"] = {
        "threshold": RSA_BURIED_THRESHOLD,
        "n": len(with_rsa),
        "agreement": accuracy([r.rsa_label for r, _ in with_rsa], [t for _, t in with_rsa]),
        "sweep": {
            str(thr): accuracy(
                ["inward" if r.rsa < thr else "outward" for r, _ in with_rsa],
                [t for _, t in with_rsa],
            )
            for thr in (0.10, 0.15, 0.20, 0.25, 0.30)
        },
        "median_rsa_inward": float(np.median([r.rsa for r, t in with_rsa if t == "inward"])),
        "median_rsa_outward": float(np.median([r.rsa for r, t in with_rsa if t == "outward"])),
        "cylinder_label_agreement": accuracy(
            [r.rsa_label for r, _ in with_rsa], [r.cylinder_axis_label for r, _ in with_rsa]),
    }

    metrics["autocorrelation"] = {}
    for name, vals in (
        ("ground_truth_label", _sign(truth)),
        ("chromophore_cosine", [r.chromophore_cosine for r in rows]),
        ("cylinder_axis_label", _sign(cyl)),
        ("cylinder_radial_component", [r.cylinder_radial_component for r in rows]),
        ("rsa", [r.rsa for r in rows]),
    ):
        metrics["autocorrelation"][name] = {
            str(lag): dict(zip(("r", "n_pairs"), within_strand_autocorrelation(rows, vals, lag)))
            for lag in (1, 2, 3, 4)
        }
    strict = {}
    for sid in STRAND_IDS:
        labs = [t for r, t in zip(rows, truth) if r.strand_id == sid]
        strict[sid] = {
            "pattern": "".join("I" if lab == "inward" else "o" for lab in labs),
            "adjacent_flips": sum(a != b for a, b in zip(labs, labs[1:])),
            "adjacent_pairs": len(labs) - 1,
        }
    metrics["per_strand_pattern"] = strict

    hyd = [r.hydrophobicity_prediction for r in rows]
    metrics["hydrophobicity_rule"] = {
        "scale": "Kyte-Doolittle 1982, per residue, no window",
        "rule": f"KD > {KD_THRESHOLD} -> inward",
        "accuracy": accuracy(hyd, truth),
        "accuracy_vs_cylinder_label": accuracy(hyd, cyl),
        "confusion": {
            f"truth_{t}_pred_{p}": sum(1 for a, b in zip(truth, hyd) if a == t and b == p)
            for t in ("inward", "outward") for p in ("inward", "outward")
        },
    }
    flips = coin_flip(n, seed=0)
    sims = [accuracy(coin_flip(n, seed=s), truth) for s in range(1, 10001)]
    metrics["coin_flip"] = {
        "seed": 0,
        "accuracy": accuracy(flips, truth),
        "expected": 0.5,
        "simulated_10000": {
            "mean": float(np.mean(sims)),
            "p2.5": float(np.percentile(sims, 2.5)),
            "p97.5": float(np.percentile(sims, 97.5)),
        },
    }
    majority = max(metrics["class_balance"], key=metrics["class_balance"].get)
    metrics["majority_class_baseline"] = {"class": majority, "accuracy": accuracy([majority] * n, truth)}

    resnums = [r.position for r in rows]
    arr = load_chain("1EMA")
    ca = strand_cas(arr, resnums)
    _, radius, rms = fit_barrel_axis(ca)
    rad = radial_distances(ca, axis)
    proj = (ca - axis.center) @ axis.direction

    def angle(a: Axis, b: Axis) -> float:
        return float(np.degrees(np.arccos(min(1.0, abs(a.direction @ b.direction)))))

    def alt_labels(alt: Axis) -> list[str]:
        geom, _ = radial_components(arr, resnums, axis=alt)
        return [label_of(geom[p][0]) for p in resnums]

    pca = pca_axis(ca)
    strand_ax = strand_direction_axis(arr, axis.center)
    pca_labels = alt_labels(pca)
    metrics["axis"] = {
        "method": "global least-squares cylinder fit to strand CA atoms (400 starts)",
        "cylinder_radius": radius,
        "cylinder_rms_residual": rms,
        "ca_radial_distance_sd": float(rad.std()),
        "strand_extent_along_axis": float(proj.max() - proj.min()),
        "strand_direction_axis": {
            "angle_to_cylinder_deg": angle(strand_ax, axis),
            "agreement_with_cylinder_label": accuracy(alt_labels(strand_ax), cyl),
        },
        "pca_axis_rejected": {
            "ca_variances": (np.linalg.svd(ca - ca.mean(axis=0), compute_uv=False) ** 2
                             / len(ca)).tolist(),
            "angle_to_cylinder_deg": angle(pca, axis),
            "ca_radial_distance_sd": float(radial_distances(ca, pca).std()),
            "agreement_with_cylinder_label": accuracy(pca_labels, cyl),
            "autocorrelation_lag1": within_strand_autocorrelation(rows, _sign(pca_labels), 1)[0],
            "autocorrelation_lag2": within_strand_autocorrelation(rows, _sign(pca_labels), 2)[0],
        },
        "n_virtual_cb": int(sum(r.direction_source == "virtual_cb" for r in rows)),
    }

    cro = chromophore_centroid(arr)
    d = cro - axis.center
    end_zone = [abs(r.axial_offset_from_chromophore) >= END_ZONE_A for r in rows]
    disagree = [r for r in rows if r.ground_truth_label != r.cylinder_axis_label]
    metrics["cylinder_cross_check"] = {
        "cro_distance_from_axis_A": float(np.linalg.norm(d - (d @ axis.direction) * axis.direction)),
        "cro_axial_offset_from_axis_center_A": float(d @ axis.direction),
        "n_agree": n - len(disagree),
        "n_disagree": len(disagree),
        "end_zone_definition": f"|axial offset from chromophore| >= {END_ZONE_A} A",
        "n_end_zone": int(sum(end_zone)),
        "n_disagree_in_end_zone": int(sum(
            abs(r.axial_offset_from_chromophore) >= END_ZONE_A for r in disagree)),
        "disagreements": [
            {"resnum": r.position, "aa": r.aa, "strand": r.strand_id,
             "index_in_strand": r.index_in_strand,
             "ground_truth": r.ground_truth_label, "cylinder": r.cylinder_axis_label,
             "axial_offset_from_chromophore_A": r.axial_offset_from_chromophore,
             "chromophore_cosine": r.chromophore_cosine, "rsa": r.rsa}
            for r in disagree
        ],
        "n_abs_chromophore_cosine_below_0.2": int(sum(abs(r.chromophore_cosine) < 0.2 for r in rows)),
    }

    cross = {}
    for chain in ("A", "B"):
        arr_gfl = load_chain("1GFL", chain)
        geom_gfl, axis_gfl = radial_components(arr_gfl, resnums)
        chrom_gfl = chromophore_labels(arr_gfl, resnums, axis_gfl)
        other = [chrom_gfl[p][0] for p in resnums]
        other_cyl = [label_of(geom_gfl[p][0]) for p in resnums]
        cross[f"1GFL_{chain}"] = {
            "ground_truth_agreement": accuracy(other, truth),
            "ground_truth_disagreeing_resnums": [
                p for p, o, t in zip(resnums, other, truth) if o != t],
            "cylinder_label_agreement": accuracy(other_cyl, cyl),
        }
    metrics["cross_structure"] = cross

    lookup = dict(zip(resnums, truth))
    metrics["known_residues"] = {
        "inward_expected": {f"{r.aa}{r.position}": lookup[r.position]
                            for r in rows if r.position in KNOWN_INWARD},
        "outward_expected": {f"{r.aa}{r.position}": lookup[r.position]
                             for r in rows if r.position in KNOWN_OUTWARD},
    }
    return metrics


def write_labels(rows: list[ResidueLabel]) -> None:
    with open(DATA_DIR / "gfp_strand_orientation.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(asdict(rows[0])))
        writer.writeheader()
        writer.writerows(asdict(r) for r in rows)


def main() -> None:
    from analysis.figures.barrel_figures import draw_all

    rows, axis = compute_labels()
    metrics = validate(rows, axis)
    write_labels(rows)
    draw_all(rows, metrics, VALIDATION_DIR)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
