# Triplet windows

**Session.** Design note, 2026-10-19. No separate worker id was recorded on the note.
**Record.** Reconstructed from the triplet-window count. These counts are the Task 2 answer key.

## Question

Inside a residue bracket of avGFP, how many runs of three consecutive positions each tolerated substitution, and how many of those runs were measured as one triple mutant?

## Definitions

Source tables: ProteinGym `GFP_AEQVI_Sarkisyan_2016` and figshare barcode counts. Reference: 238-residue Sarkisyan avGFP (F64L). Bright: `DMS_score ≥ 2.5`.

A position is tolerant when at least one measured single missense mutant is bright and none is dark. A working triplet is three consecutive tolerant positions. Requiring a bright single with at least two barcodes did not change the set: every tolerant position already has one.

## Counts

| Bracket | Tolerant positions | Working / possible |
| --- | ---: | ---: |
| 1–50 | 33 | 15/48 |
| 51–100 | 27 | 7/48 |
| 101–150 | 39 | 22/48 |
| 151–200 | 44 | 35/48 |
| 189–238 | 41 | 28/48 |

The locked task uses 200–238 rather than 189–238, so the last bracket does not overlap 151–200. That slice has 20 working starts out of 37 possible triplets (positions 202, 208–210, 214, and 221–235).

Chance if a triplet is drawn uniformly is 31.3%, 14.6%, 45.8%, 72.9%, and 54.1%. The mean is 43.7%. Bracket 151–200 is the easy one.

## Simultaneous triples

Measured genotypes with exactly three substitutions at three consecutive positions: one. It is `Q157L:K158R:N159T`, bright, score 3.777, one barcode. It sits inside 151–200 and inside a working triplet. The answer key is therefore the single-mutant rule. The README states the one measured consecutive triple; the prompt does not.
