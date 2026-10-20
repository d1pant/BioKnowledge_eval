# Data survey

**Session.** Cursor worker `bc-70a0f1ff`, 2026-10-19.
**Record.** Reconstructed. The survey's own write-up is not in this repository. The counts below are the ones a later session recomputed from the same public tables, and they match the coordinator note that this survey ruled out a dense 20-by-leucine grid.

## Question

Can the Sarkisyan et al. (2016) avGFP fluorescence landscape support an agent that proposes edits and is scored on the measured result?

## What the tables contain

The assay is ProteinGym `GFP_AEQVI_Sarkisyan_2016`, joined to the primary figshare amino-acid table. The reference is the 238-residue Sarkisyan sequence (UniProt P42212 with F64L). Bright means `DMS_score ≥ 2.5`.

A rebuild of the one-edit graph found:

| Quantity | Value |
| --- | ---: |
| Measured missense sequences, including the reference | 51,715 |
| Bright / dark at 2.5 | 30,087 / 21,628 |
| One-edit edges | 35,092 |
| Sequences with at least one neighbor / isolated sequences | 17,604 / 34,111 |
| Mean / median degree | 1.36 / 0 |

The reference sequence is the hub, connected to the 1,084 measured single mutants. That degree is a sampling artifact. Most of the graph is empty.

Darkness also tracks mutation load: the dark fraction rises from 8.4% at one mutation to 81.3% at six. The dark scores pile up at a floor near 1.30, so ranks inside the dark class are not meaningful.

## What this ruled out

A locally dense scan is not in the release. The coordinator note for this session records that a dense 20×L grid was checked and ruled out. Later sessions confirmed the same sparsity in two other shapes: multi-step paths from dark proteins to bright ones are mostly missing (19,678 of 21,537 dark multi-mutants have no measured path to a bright sequence), and no set of six substitutions has all 20 of its triple combinations measured.

The practical consequence is that an agent rewarded for inventing the next genotype is usually rewarded, or penalized, for whether the 2016 library included that genotype. Later design sessions treated that as a property of the data, and they only scored sequences that the tables already contain.
