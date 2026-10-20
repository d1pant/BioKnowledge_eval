# Orientation ground truth

**Session.** Cursor worker `bc-dc342b0e`, 2026-10-19.
**Record.** Reconstructed from `results/validation/gfp-strand-orientation.md` and the commits that added the labels and the mockup figures. The validation note's original command path (`python -m bio_eval.barrel_orientation`) is the pre-move location. The same code now lives at `python -m analysis.ground_truth.barrel_orientation`.

## Question

For each of the 107 β-strand residues of avGFP, does the side chain point toward the chromophore or away from it, and is that call stable enough to score?

## Label

Primary key, column `ground_truth_label`: inward when the vector from Cα to the side-chain centroid (hypothetical Cβ for glycine) has a positive dot product with the vector from Cα to the chromophore centroid. The task later maps inward/outward to TOWARD/AWAY.

Structure: PDB 1EMA chain A, the S65T variant, waters removed. Strands are the eleven deposited sheet ranges, 107 residues. The chromophore centroid is the 22 CRO atoms at author residue 66. Author numbers 65 and 67 are absent in 1EMA, and none of 65–67 lies in a strand. Author numbering matches UniProt P42212 except for the expected Q80R in 1EMA. Residue 80 is not in a strand. F64L, which distinguishes the Sarkisyan sequence, is also outside every strand.

## Checks that fixed the headline

| Check | Result |
| --- | --- |
| Class balance, all 107 | 53 inward / 54 outward |
| Hydrophobicity rule (KD > 0 → inward) | 73/107 = 68.2% |
| Always outward | 50.5% |
| Coin flip, seed 0 | 52.3% |
| Agreement with a fitted cylinder axis | 99/107 |
| Agreement with 1GFL chain A and chain B | 105/107 on each chain; exceptions E115 and Q177 |
| Residues with \|chromophore cosine\| < 0.2 | 9: F114, E115, T118, R168, N170, Q177, L178, A226, A227 |

The eight chromophore-versus-cylinder disagreements are all at the barrel ends (H25, C48, G160, N170, V176, Q177, A226, A227). Mid-barrel, the two references agree. RSA correlates with burial and is a comparison only; it is not the label. A principal-component axis through the strand Cα atoms lies about 85° from the barrel axis and was not used.

Within a strand the chromophore labels alternate: autocorrelation −0.856 at lag 1 and +0.788 at lag 2, and 89 of 96 adjacent pairs flip. That alternation is why each residue is later asked in a fresh context. A single prompt listing all 107 residues would let a model continue the pattern after the first few answers.

The robust headline, accuracy on the 98 residues with `|cosine| ≥ 0.2`, was adopted from this caveat. On those 98 the split is 50 TOWARD / 48 AWAY, and the hydrophobicity rule scores 0.684.

## Figures

`results/validation/` holds the truth, seed-0 coin-flip, and hydrophobicity panels. `results/design-mockups/` holds comparison posters. Panels named as models in those posters are label flips at fixed seeds. They are design pictures, not model results.
