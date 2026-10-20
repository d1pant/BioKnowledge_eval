# Sources for the packaged assay data

## `GFP_AEQVI_Sarkisyan_2016.csv`

The ProteinGym release of the Sarkisyan avGFP fluorescence landscape, byte-for-byte as
downloaded. Nothing in it was filtered, renumbered or recomputed.

- Downloaded from `https://huggingface.co/datasets/ICML2022/ProteinGym/resolve/main/ProteinGym_substitutions/GFP_AEQVI_Sarkisyan_2016.csv`
- 51,714 data rows; columns `mutant`, `DMS_score`, `DMS_score_bin`
- ProteinGym dataset id `GFP_AEQVI_Sarkisyan_2016` (`DMS_index = DMS_sub_67`),
  `DMS_binarization_cutoff = 2.5`, `region_mutated = 3-237`

**Primary data.** Sarkisyan KS, Bolotin DA, Meer MV, et al. "Local fitness landscape of the
green fluorescent protein." *Nature* 533, 397–401 (2016).
DOI [10.1038/nature17995](https://doi.org/10.1038/nature17995). Deposited data:
figshare DOI [10.6084/m9.figshare.3102154](https://doi.org/10.6084/m9.figshare.3102154),
licensed **CC BY 4.0** — redistributed here with attribution.

**Curation.** Notin P, Kollasch A, Ritter D, van Niekerk L, et al. ProteinGym
(<https://github.com/OATML-Markslab/ProteinGym>), repository code MIT-licensed. The assay
values themselves remain the Sarkisyan et al. data and are attributed as above.

Mutation positions in the `mutant` column are 1-based on the 238-residue reference in
`src/bio_eval/tasks/gfp_tolerant_site/data/avgfp_sarkisyan.fasta`. That convention is not
assumed: `tests/test_tolerant_ground_truth.py` checks the wild-type letter of all 1,084
single missense mutants against that sequence and requires zero mismatches.
