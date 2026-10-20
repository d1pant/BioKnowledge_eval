# avGFP β-barrel inward/outward ground truth: validation

Every number here was **computed in this repo** by `python -m bio_eval.barrel_orientation` (source: `src/bio_eval/barrel_orientation.py`). The command writes the per-residue labels to `src/bio_eval/data/gfp_strand_orientation.csv` and the three figures to this folder, and it prints all validation metrics as JSON to stdout. The run is deterministic. The only numbers taken from elsewhere are the survey's RSA autocorrelations, and they are marked *(survey)*.

**Scope.** Deliberately minimal: the label CSV and three figures, no DSSP and no extra structural-biology stack. RSA was computed with `biotite`, which was already in the venv (along with numpy, scipy and matplotlib); nothing new was installed. RSA is a comparison only and never feeds into any label.

## Which label is which

The eval asks: *"does this side chain point toward the chromophore at the centre of the barrel, or away from it?"* All 107 strand residues are kept.

| CSV column | Role | Definition |
| --- | --- | --- |
| **`ground_truth_label`** | **PRIMARY answer key** | `inward` if (side-chain centroid − CA) · (chromophore centroid − CA) > 0, else `outward` |
| `chromophore_cosine` | margin for the primary label | cosine of the angle between those two vectors |
| `axial_offset_from_chromophore` | position in the barrel | CA position along the fitted barrel axis relative to the chromophore centroid (Å) |
| `cylinder_axis_label` | secondary cross-check | `inward` if (side-chain centroid − CA) · r̂ ≤ 0, where r̂ is the outward radial unit vector from the fitted barrel axis |
| `cylinder_radial_component`, `cylinder_radial_cosine` | margin for the cross-check | v · r̂ in Å, and its cosine |
| `rsa`, `rsa_label` | comparison only | RSA, and `inward` if RSA < 0.20 |
| `kd_hydrophobicity`, `hydrophobicity_prediction` | sequence-only baseline | Kyte–Doolittle value, and `inward` if KD > 0 |

## Definitions

- **Structure.** PDB 1EMA chain A (GFP S65T, 1.9 Å), without waters. 1GFL chains A and B are used only for the cross-structure check.
- **Strands.** The eleven `struct_sheet_range` rows deposited in 1EMA, sorted N→C and named β1–β11: 12–22, 25–36, 41–48, 92–100, 105–115, 118–128, 148–152, 160–170, 176–187, 199–207, 220–227. That is **107 residues**, and the code checks this list against the CIF file.
- **Side-chain vector.** v = (centroid of the heavy side-chain atoms) − CA. Side-chain atoms are all heavy atoms except N, CA, C, O and OXT. For the 6 Gly residues (G20, G31, G33, G35, G127, G160), v = virtual CB − CA, with the virtual CB built from N, CA and C using ideal geometry.
- **Chromophore centroid.** The mean of the 22 CRO atoms at author 66 in 1EMA. 1GFL models the chromophore as separate residues, so there the centroid is the mean of all Ser65, Tyr66 and Gly67 atoms.
- **Barrel axis (cross-check, and the axial offset).** A least-squares cylinder fitted to the 107 strand CAs, minimising Σ(dist(CA, axis) − R)², with 400 starting directions. Result: R = 11.58 Å, RMS residual 1.24 Å. An independent axis from the strand directions (the principal eigenvector of Σ d dᵀ over unit strand vectors d) lies 9.1° away and gives identical cylinder labels.
- **Numbering.** Author numbering is used throughout. Every residue of every loaded chain is checked against UniProt P42212 at its author number.
  - Expected deviations are allowed explicitly: 1EMA Q80R; 1GFL M1A and Q80R.
  - I checked that loading with `label_seq_id` numbering fails this check. The fused chromophore shifts label numbers by −2, which would otherwise be a silent frameshift.
- **Chromophore residues and unlabelled residues.** In 1EMA, CRO sits at author 66 and author 65/67 are absent (asserted).
  - None of 65–67 lies in a strand, so they get no label.
  - Neither do the other 119 non-strand residues of the 226 modelled (CRO counted as one).
  - CRO stays in the atom set for SASA so that it still occludes its neighbours.
- **F64L.** Residue 64 is not in a strand, so the F64L difference from the Sarkisyan reference does not affect any label.

## Results (against `ground_truth_label`)

| Check | Result |
| --- | --- |
| Class balance | **53 inward / 54 outward** (n = 107) |
| Hydrophobicity rule accuracy | **68.2 %** (73/107) |
| Coin flip, numpy seed 0 (the one plotted) | **52.3 %** (56/107) |
| Coin flip, 10,000 seeds | mean 50.0 %, 95 % interval 40.2–59.8 % |
| Majority-class baseline (always outward) | 50.5 % |
| Agreement with the cylinder-axis cross-check | **99/107 (92.5 %)** |
| Truth vs RSA (buried if RSA < 0.20) | 83.2 % (89/107); the cylinder labels reach 86.9 % |
| Same, RSA threshold sweep 0.10 / 0.15 / 0.20 / 0.25 / 0.30 | 88.8 / 88.8 / 83.2 / 81.3 / 73.8 % |
| Median RSA, inward vs outward | 0.029 vs 0.298 |
| 1EMA vs 1GFL, chain A / chain B | 105/107 on both chains (E115 and Q177 differ). The cylinder labels agree 107/107 |
| Low-margin residues (\|chromophore_cosine\| < 0.2) | 9: F114, E115, T118, R168, N170, Q177, L178, A226, A227 |

**Within-strand autocorrelation.** Pearson r over all (i, i+lag) pairs within the same strand, pooled across strands. Labels are coded inward = +1 and outward = −1.

| lag | ground truth | chromophore cosine | cylinder label | RSA (this repo) | RSA *(survey)* |
| --- | --- | --- | --- | --- | --- |
| 1 | **−0.856** | −0.902 | −0.979 | −0.556 | −0.556 |
| 2 | **+0.788** | +0.849 | +0.977 | +0.657 | +0.657 |
| 3 | −0.757 | −0.812 | −0.973 | −0.724 | −0.724 |
| 4 | +0.715 | +0.767 | +0.969 | +0.501 | +0.501 |

The RSA recipe (biotite Shrake–Rupley, 1000 points, `Single` radii, Tien 2013 theoretical max-ASA) reproduces the survey's values exactly. The ground truth shows the i/i+2 alternation clearly: 89 of the 96 within-strand adjacent pairs flip. Of the 7 pairs that do not, 6 involve one of the 8 barrel-end residues discussed below. The seventh is T186→P187 at the end of β9, which is also a non-flip under the cylinder labels.

```
β1  IoIoIoIoIoI     β5  oIoIoIoIoIo     β9   IooIoIoIoIoo
β2  ooIoIoIoIoIo    β6  oIoIoIoIoIo     β10  IoIoIoIoI
β3  oIoIoIoo        β7  IoIoI           β11  IoIoIooI
β4  IoIoIoIoI       β8  IIoIoIoIoII
```

**Known residues.** All 9 chromophore-pocket residues are inward: Q94, R96, H148, F165, I167, Q183, T203, S205 and E222. All 3 dimer-interface surface residues are outward: A206, L221 and F223.

**Where the hydrophobicity rule fails.** The rule is Kyte–Doolittle per residue, with no window, and KD > 0 means inward. Its confusion matrix is truth-inward 31 right / 22 wrong, and truth-outward 42 right / 12 wrong.
- 22 inward residues are predicted outward:
  - the six inward Gly residues, G20, G31, G33, G35, G127 and G160 (KD −0.4);
  - the polar chromophore pocket: Q94, R96, H148, T203, S205 and E222;
  - other inward His, Tyr, Asn, Gln and Thr residues.
- 12 outward residues are predicted inward. These are surface hydrophobics, including A206, L221 and F223 at the dimer interface.

## Cross-check: cylinder-axis labels

The cylinder-axis label asks whether the side chain points toward the barrel *axis*, rather than toward the chromophore *point*. The chromophore centroid is **1.77 Å from the fitted axis**, and 0.63 Å along the axis from the centre of the strand CAs, so the two references nearly coincide in the middle of the barrel.

The two label sets **agree on 99/107 residues**. **All 8 disagreements are at the barrel ends.**
- Strand CAs span −18.8 to +12.0 Å along the axis, measured from the chromophore.
- The end zone, defined as at least 10 Å from the chromophore along the axis, holds 24 residues, and all 8 disagreements are among them. None is mid-barrel.
- Each disagreement is within two residues of a strand terminus.
- There the CA→chromophore vector tilts 42–55° from the inward radial direction, toward the axis. A side chain can therefore point into the barrel lumen while pointing away from a chromophore 10–19 Å further along.

| Residue | Strand, index | Axial offset (Å) | Ground truth (chromophore) | Cylinder | chromophore_cosine | RSA |
| --- | --- | --- | --- | --- | --- | --- |
| H25 | β2, 0 | −18.8 | outward | inward | −0.32 | 0.48 |
| C48 | β3, 7 | −12.5 | outward | inward | −0.23 | 0.04 |
| G160 | β8, 0 | +11.6 | inward | outward | +0.37 | 0.01 |
| N170 | β8, 10 | −14.3 | inward | outward | +0.09 | 0.22 |
| V176 | β9, 0 | −15.1 | inward | outward | +0.39 | 0.45 |
| Q177 | β9, 1 | −14.4 | outward | inward | −0.02 | 0.03 |
| A226 | β11, 6 | +10.4 | outward | inward | −0.15 | 0.04 |
| A227 | β11, 7 | +11.2 | inward | outward | +0.06 | 0.21 |

Using RSA as an independent tie-breaker, the cylinder label is consistent with burial on 6 of these 8 residues and the chromophore label on 2 (H25 and G160).

**Caveat for the answer key.** Four of the 8 (N170, Q177, A226, A227) have |chromophore_cosine| < 0.16. Their side chains are nearly perpendicular to the chromophore direction, so the answer to "toward or away" is close to a coin toss physically. The two 1EMA-vs-1GFL disagreements (E115 at cos −0.05, Q177 at cos −0.02) are of this kind. Consider accepting either answer for the 9 low-margin residues listed in the results table, or reporting accuracy with and without them.

## Figures

All three figures use the same unrolled layout: rows are β1–β11, columns are the index within the strand (N→C), and each cell shows the one-letter residue and its author number. All three are scored against `ground_truth_label`.
- `gfp-truth.png`: the chromophore-referenced ground truth.
- `gfp-random.png`: the coin flip (seed 0), 52.3 %. Cells that disagree with the truth have a thick border and a ✗.
- `gfp-hydrophobicity.png`: the Kyte–Doolittle prediction, 68.2 %, with the same disagreement markers.

## Deviations from the original design and from the survey

1. **The PCA axis does not work.** The strand-CA variances are 75 / 70 / 49 Å², so the cloud is nearly isotropic, and PC1 lies **84.8° from the barrel axis**. Labels from the PCA axis agree with the cylinder labels only 77.6 % of the time, with autocorrelation of −0.589 at lag 1 and +0.317 at lag 2. The cylinder fit is used for the cross-check and for the axial offsets.
2. **The survey is wrong that 1EMA has Gln80.** The 1EMA entity sequence reads `…H(MSE)KRHDFF…`, so 1EMA carries **Q80R**, like 1GFL. The numbering assertion caught this. Residue 80 is not in a strand, so no label is affected.
3. **Ground-truth definition changed** from the cylinder axis to the chromophore point, to match the eval wording exactly. The cylinder-axis set is kept as a cross-check column.
