# Repair design

**Session.** Cursor worker `bc-3760c252`, 2026-10-19.
**Record.** Reconstructed from the measured-GFP-repair design note. This task was specified and then not implemented. The implemented pair is the orientation task plus the tolerant-site task.

## Question

Given a measured dark mutant, can a model say which single edit restores fluorescence, using only deposited scores as labels?

## Recommendation

Use a 24-question, one-shot reversion-choice task. Each item starts from a measured dark double mutant and asks which single reversion repairs fluorescence: A, B, both, or neither. Every label is a Sarkisyan score. No unmeasured sequence receives a fluorescence value.

Interactive search was set aside in the same note. Among 21,537 dark multi-mutants, 19,678 have no measured path to any bright sequence, and 19,666 have no measured one-edit neighbor at all. After a chromophore filter and a cutoff margin, only 248 distance-two and 12 distance-three starts remain, with weak replication along the path. Difficulty on a "keep editing until bright" task would mostly reflect library coverage.

## The 24-question panel

Restrict to dark double mutants whose two constituent single mutants were also measured (11,954 of 12,777 doubles). Keep items whose endpoints are at least 0.5 log10 units from 2.5, whose single-mutant endpoints have at least three barcodes, and which avoid stops and chromophore positions 65–67. The filtered pool is 725 items: 555 exactly-one, 142 both, 28 neither. A seed-24,939 draw of 24 items balances 6 both, 6 neither, and 12 exactly-one, uses 48 distinct positions, and keeps a minimum margin of 0.921 from the cutoff.

The dark starts in that draw have one barcode. A fully replicated, class-balanced 24-item set does not exist in this table: requiring every displayed node to have three barcodes leaves zero starts. The note says to put that limitation on the dataset card.

Chance on the four-way item is 25%. On the selected 24, "revert the more buried site" and a proline/glycine rule also score 25%. "Revert the larger Kyte–Doolittle disruption" scores 37.5%.

## Tools

The only tool in the recommendation is an unlimited editor, `apply_reversion`, which checks the reference allele and returns the resulting sequence. An assay tool was left out of the scored task, because looking up both candidates would reveal the four-way answer. An unscored tutorial could assay exactly the two declared sequences and would return `unmeasured` for anything else.

## Why it stayed a design

The panel is an honest classification task. It was not the task that was built. The locked eval asks for structural orientation and for sites that tolerated substitution, rather than for a choice among pre-listed reversions of one double mutant. The sparsity finding from this session is what carried forward: do not score an agent on a path the experiment did not measure.
