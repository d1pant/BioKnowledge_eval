# Three of six

**Session.** Cursor worker `bc-ab1dde74`, 2026-10-19.
**Record.** Reconstructed from the three-of-six feasibility note. This task was not implemented.

## Question

Can a model be asked to choose any three substitutions out of six individually bright ones, and be scored on whether that triple is bright in Sarkisyan et al. (2016)?

## Verdict

Unrestricted choice assigns experimental truth to unmeasured genotypes. No set of six individually bright substitutions has all 20 of its three-of-six combinations measured. The exact maximum, counted over the whole hypergraph, is 6/20. The best set that contains both a bright and a dark measured triple covers 5/20. The other combinations were never observed.

The unique 6/20 set is `S28G`, `D117G`, `N135S`, `N149S`, `K214E`, `I229T`. All six measured triples in it are bright and single-barcode. The best mixed set (`K3R`, `N23S`, `Q80R`, `H139R`, `K140E`, `F165S`) has four bright triples and one dark triple; the other 15 combinations are unmeasured.

## What a measured menu can support

If the prompt shows a fixed list of triples that were actually measured, the labels are honest, with a replication caveat. Under a high-quality filter (each single score ≥ 3.0 with ≥ 3 barcodes, every displayed triple at least 0.5 from the cutoff, no chromophore position), an exact set packing yields:

- 13 questions with four displayed triples each (2 bright / 2 dark), no residue position reused
- or 17 non-overlapping four-candidate questions, or 11 six-candidate questions, if the candidates need not come from one six-substitution set

Among the relevant measured triples, every dark endpoint has one barcode, 21 bright endpoints have two, and none has three. Replicated triple ground truth is not available. About 7% of triples built from strong bright singles are themselves dark, so a functional-to-dark collapse is real, but it is a minority outcome and it is singly observed.

## Agentic variant that was specified and not built

The note's defensible agent shows four declared triples from the same six bright singles and allows one `assay(candidate_id)` call. The final choice has to be a different, unqueried candidate. Querying the candidate you then submit is an answer lookup. Querying an unlisted genotype returns `unmeasured` because of library sampling.

The implemented Task 2 keeps the lesson and changes the question. It asks for three consecutive positions that each tolerated a single substitution, and it gives the agent an orientation lookup rather than a fluorescence assay.
