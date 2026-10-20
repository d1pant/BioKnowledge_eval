# avGFP benchmark data survey

Verification of the data foundations for an educational benchmark that tests per-residue recall and reasoning about avGFP structure, scored against published experimental data.

Every numeric claim below is either (a) quoted from a primary source with a URL/DOI, or (b) **recomputed by me from the primary data files** and marked `[verified locally]`. Claims I could not confirm are marked **UNCONFIRMED**.

Local verification environment: Python 3.12.15, `biotite` 2.0.0, `freesasa` 2.2.1, `biopython` 1.88, in a throwaway venv at `/tmp/gfp-survey`. Downloaded artifacts: ProteinGym `GFP_AEQVI_Sarkisyan_2016.csv`, figshare `amino_acid_genotypes_to_brightness.tsv` and `avGFP_reference_sequence.fa`, UniProt `P42212.fasta`, PDB `1EMA`/`1GFL`/`2WUR`/`1W7S`/`2Y0G`/`1QYO` mmCIF.

---

## 1. Sarkisyan et al. 2016

**Citation.** Sarkisyan KS, Bolotin DA, Meer MV, Usmanova DR, Mishin AS, Sharonov GV, Ivankov DN, Bozhanova NG, Bogatyreva NS, Vlasov PK, Egorov ES, Logacheva MD, Kondrashov AS, Chudakov DM, Putintseva EV, Mamedov IZ, Tawfik DS, Lukyanov KA, Kondrashov FA. "Local fitness landscape of the green fluorescent protein." *Nature* 533:397–401 (2016). DOI [10.1038/nature17995](https://doi.org/10.1038/nature17995). Open full text: [PMC4968632](https://pmc.ncbi.nlm.nih.gov/articles/PMC4968632/).

### 1.1 Which avGFP variant, and which residue numbering

This is the single most important finding of the survey, and it is **not** what the paper's prose implies.

The paper describes random mutagenesis of "wildtype avGFP". The deposited reference sequence (`avGFP_reference_sequence.fa` on figshare) is a codon-optimised 714-nt ORF. `[verified locally]` Translating it gives 237 aa + stop, beginning `SKGEELFTGVV...` — i.e. **the initiator Met is not part of the deposited reference**; index 0 of the reference protein is Ser2 in canonical numbering.

`[verified locally]` Diffing that translation (with Met prepended) against UniProt [P42212](https://rest.uniprot.org/uniprotkb/P42212.fasta) (GFP_AEQVI, 238 aa) gives **exactly one difference: position 64 is Leu, not Phe.** The Sarkisyan "wild type" therefore carries **F64L** relative to the canonical avGFP sequence — the classic folding/maturation mutation also present in EGFP. The eLife 2022 follow-up from the same group confirms this obliquely: "only cgreGFP and ppluGFP2 were identical to the true wildtype sequences, while avGFP and amacGFP contain one and three amino acid substitutions, respectively" ([eLife 75842](https://doi.org/10.7554/eLife.75842)).

Numbering, as three different conventions that must be reconciled:

| Source | Convention | Example |
| --- | --- | --- |
| figshare `aaMutations` | **0-based**, index 0 = Ser2 (no Met) | `SA108D` = Ala→Asp at canonical 110 |
| ProteinGym `mutant` | **1-based on the 238-aa sequence including Met1** = canonical | `A110T` |
| UniProt P42212 / PDB author numbering | 1-based, Met1 | `A110` |

So: **canonical position = figshare index + 2**, and **ProteinGym numbering = canonical numbering**. The figshare notation is documented as zero-based on the [dataset page](https://figshare.com/articles/dataset/Local_fitness_landscape_of_the_green_fluorescent_protein/3102154) (MiXCR mutation encoding).

`[verified locally]` I validated both mappings exhaustively rather than by spot-check:
- All 200,547 substitution tokens across the 51,714 ProteinGym variants have a wild-type letter matching the Sarkisyan reference at 1-based canonical positions: **0 mismatches**. Against UniProt P42212 there are **687 mismatches, all of them at position 64** (`L` expected by the data, `F` in P42212) — the F64L signature again.
- All figshare `aaMutations` tokens match the reference at `index` interpreted as 0-based into the Ser2-start translation: **0 mismatches**.

ProteinGym's reference file independently confirms this: `target_seq` is 238 aa, begins `MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYG`, and positions 64–67 are `LSYG` (not `FSYG`).

### 1.2 Single vs multi-mutant counts

`[verified locally]` from `amino_acid_genotypes_to_brightness.tsv` (54,025 rows = 1 wild-type row + 54,024 mutant genotypes):

| n mutations | figshare genotypes (incl. nonsense) | ProteinGym (missense only) | Paper, Extended Data Table 1 |
| --- | --- | --- | --- |
| 1 | 1,114 | 1,084 | 1,114 |
| 2 | 13,010 | 12,777 | 13,010 |
| 3 | 12,683 | 12,336 | 12,683 |
| 4 | 9,759 | 9,387 | 9,759 |
| 5 | 7,215 | 6,825 | 7,215 |
| 6 | 4,643 | 4,298 | 4,643 |
| 7 | 2,783 | 2,526 | 2,783 |
| 8 | 1,526 | 1,364 | 1,526 |
| 9 | 714 | 627 | 714 |
| 10 | 352 | 299 | 352 |
| 11–15 | 225 | 191 | — |
| **total mutants** | **54,024** | **51,714** | — |

The accounting closes exactly: 54,024 − 2,310 stop-containing genotypes = 51,714 missense-only mutants, + 1 wild type = **51,715 distinct protein sequences**, the figure quoted in the abstract. The paper's 56,086 is the count of unique *nucleotide* sequences.

**Single mutants: 1,114 total, of which 30 are nonsense and 1,084 are missense.** `[verified locally]` The 1,084 missense singles cover **233 positions** (canonical 3–237). Positions with no single mutant at all: **1, 2, 119, 120, 238**. Positions 1–2 are outside the mutagenised reference; 238 is the terminal residue; the 119/120 gap sits at the SpeI site (`ACTAGT` begins at reference nt index 350, i.e. codon 118) — the "scissors … restriction site" marked in the paper's Figure 1b. ProteinGym records `region_mutated = 3-237`, consistent.

### 1.3 What was measured

Error-prone PCR library of avGFP, each variant tagged with a downstream nucleotide barcode, expressed in *E. coli*, sorted by FACS into brightness gates, barcodes sequenced; per-genotype **log₁₀ fluorescence ("log-brightness")**, median across barcodes. Reported error rates: false negative 0.08%, false positive 0.24% ([PMC4968632](https://pmc.ncbi.nlm.nih.gov/articles/PMC4968632/)). Note the 2016 experiment sorted on green fluorescence only; the 2022 follow-up added an mKate2 fusion and a red-fluorescence gate to normalise for expression, which is one reason its variance is 7× lower.

`[verified locally]` Score range across the whole dataset is **1.2834 to 4.1231**; the wild-type row is **3.7192 (σ = 0.1070, 3,645 barcodes)**. The dark floor sits at ≈1.301 = log₁₀(20), i.e. an arbitrary floor rather than a measured zero. Note the paper's Figure 2a cites **2,442** wild-type sequences and σ ≈ 0.082 (eLife Table 1) against the 3,645 barcodes in the released aggregate row — different filtering stages, a minor inconsistency worth not over-interpreting.

### 1.4 Is there a clean bright/dark split?

**For the full dataset, yes. For single mutants, no — and this distinction is load-bearing for the benchmark.**

`[verified locally]` Histogram of all 51,714 scores (0.2-wide bins) is sharply bimodal: a dark mode at 1.2–1.6 (≈20,000 variants) and a bright mode at 3.2–3.8 (≈29,000), with a deep trough spanning 2.0–3.0 containing under 1,200 variants in total. ProteinGym's binarisation cutoff of 2.5 falls cleanly in that trough: min score in bin 1 = 2.50058, max in bin 0 = 2.49798. Bin counts: 30,086 bright / 21,628 dark.

Restricted to the **1,084 single missense mutants**, the distribution is overwhelmingly unimodal and near wild type:
- 993 bright (91.6%) vs 91 dark (8.4%) at the 2.5 cutoff `[verified locally]`
- **9.2% have log-fluorescence below 3.0202** (a >5-fold decrease from wild type) `[verified locally]`, reproducing the paper's stated **9.4%** essentially exactly
- the bright singles spread over ≈3.3–3.9, i.e. roughly 6× the wild-type σ

So the bimodality of the full dataset is a property of the *multi-mutant* genotypes (threshold/truncation behaviour: "half of genotypes with two mutations showing reduced fluorescence and half of genotypes with five mutations being completely non-fluorescent"). A benchmark that asks about single substitutions is asking about a continuum with a thin dark tail, not a binary.

### 1.5 Where to download

**figshare (primary, authoritative).** DOI [10.6084/m9.figshare.3102154](https://doi.org/10.6084/m9.figshare.3102154). `[verified locally]` via the figshare API (`https://api.figshare.com/v2/articles/3102154`):

| File | Size | Direct URL |
| --- | --- | --- |
| `amino_acid_genotypes_to_brightness.tsv` | 2.33 MB | https://ndownloader.figshare.com/files/4820647 |
| `nucleotide_genotypes_to_brightness.tsv` | 4.13 MB | https://ndownloader.figshare.com/files/4820650 |
| `avGFP_reference_sequence.fa` | 740 B | https://ndownloader.figshare.com/files/4820653 |
| `barcodes_to_brightness.tsv` | 5.60 MB | https://ndownloader.figshare.com/files/4820656 |
| `genotypes.tsv` | 30.1 MB | https://ndownloader.figshare.com/files/4820659 |
| `populations.zip` | 206 MB | https://ndownloader.figshare.com/files/4820662 |

Columns of the amino-acid table: `aaMutations`, `uniqueBarcodes`, `medianBrightness`, `std` (empty for single-barcode genotypes).

Raw reads: SRA BioProject [PRJNA282342](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA282342/). Supplementary PDF: [Springer Nature ESM](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fnature17995/MediaObjects/41586_2016_BFnature17995_MOESM548_ESM.pdf).

**ProteinGym — confirmed included.** Dataset ID **`GFP_AEQVI_Sarkisyan_2016`** (`DMS_index = DMS_sub_67`), one of 217 substitution assays ([GitHub](https://github.com/OATML-Markslab/ProteinGym), [proteingym.org](https://proteingym.org/download)).

- Format: CSV, columns `mutant`, `DMS_score`, `DMS_score_bin`. (Note: the per-file Hugging Face copy omits `mutated_sequence`, which the README documents for the benchmark generally.) `[verified locally]` 51,714 data rows, 1.99 MB.
- Single-file download, verified working: `https://huggingface.co/datasets/ICML2022/ProteinGym/resolve/main/ProteinGym_substitutions/GFP_AEQVI_Sarkisyan_2016.csv`
- Bulk (v1.3): `curl -o DMS_ProteinGym_substitutions.zip https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip` (1.0 GB unzipped). **UNCONFIRMED:** I did not download the 1 GB bundle, so I have not byte-compared the v1.3 copy to the ICML2022 copy. Indirect evidence that they agree: the current `reference_files/DMS_substitutions.csv` on `main` states `DMS_total_number_mutants = 51714`, `DMS_number_single_mutants = 1084`, `DMS_number_multiple_mutants = 50630`, `DMS_binarization_cutoff = 2.5` — all of which match the file I downloaded exactly.
- Reference metadata also records: `selection_assay = Fluorescence`, `selection_type = FACS`, `DMS_binarization_method = manual`, `raw_DMS_phenotype_name = mean_medianBrightness_per_aaseq`, `raw_DMS_directionality = 1`, `pdb_range = 1-238`, and a low-depth MSA (`MSA_N_eff = 13.1`, `MSA_Neff_L = 0.06`, category Low).

---

## 2. Alternative datasets and known caveats

### 2.1 Alternative fluorescent-protein mutational scans

**Gonzalez Somermeyer L, Fleiss A, Mishin AS, Bozhanova NG, Igolkina AA, Meiler J, Alaball Pujol M-E, Putintseva EV, Sarkisyan KS, Kondrashov FA.** "Heterogeneity of the GFP fitness landscape and data-driven protein design." *eLife* 11:e75842 (2022). DOI [10.7554/eLife.75842](https://doi.org/10.7554/eLife.75842). Data + code: [github.com/aequorea238/Orthologous_GFP_Fitness_Peaks](https://github.com/aequorea238/Orthologous_GFP_Fitness_Peaks).

Same lab, improved pipeline, three additional orthologues (Table 1):

| | amacGFP | cgreGFP | ppluGFP2 | avGFP (2016) |
| --- | --- | --- | --- | --- |
| Protein genotypes | 35,500 | 26,165 | 32,260 | 51,715 |
| Identity to avGFP | 82% | 41% | 18% | — |
| Median barcode replicates/genotype | 5 | 5 | 7 | **1** |
| WT log₁₀ fluorescence ± σ | 3.97 ± 0.031 | 4.50 ± 0.028 | 4.23 ± 0.027 | **3.72 ± 0.082** |
| False positive rate | 0.55% | 0.75% | 0.49% | 0.24% |
| Mutational LD50 (loss of function) | 5.8 | 3.2 | 6.2 | 4.1 |
| Genotypes with \|epistasis\| > 0.3 | 5.3% | 14.4% | 6.8% | 21.4% |

Three pipeline improvements over 2016: sequence-agnostic library sequencing, genome integration of the construct, and secondary barcodes giving internal replicates — together reducing measurement variance **7-fold**.

Also relevant:
- **Kelsic / Nilsson-lab-style encapsulation scan of the five C-terminal β-strands of GFP**, >10,000 variants, bioRxiv DOI [10.1101/274753](https://doi.org/10.1101/274753). Useful because it explicitly analyses inward- vs outward-facing strand positions (see §4).
- **Arpino et al. single-residue deletion scan of eGFP**, analysed computationally for RSA/WCN predictivity in bioRxiv DOI [10.1101/079061](https://doi.org/10.1101/079061) — deletions, not substitutions, so not directly reusable but the burial analysis is.
- **Deep indel mutagenesis across nine domains** (Beltran/Faure/Lehner), bioRxiv [2023.10.06.561180](https://www.biorxiv.org/content/biorxiv/early/2024/03/21/2023.10.06.561180.full.pdf) — not GFP, but the source for the general quantitative claim that RSA predicts *substitution* tolerance well (mode r = 0.644) and indel tolerance poorly.
- ProteinGym contains other FP-adjacent assays but **UNCONFIRMED** whether any second avGFP assay exists in it; `GFP_AEQVI_Sarkisyan_2016` was the only GFP/AEQVI hit in the 217-assay reference file `[verified locally]`.

### 2.2 Caveats with Sarkisyan

**(a) Single mutants cannot be individually resolved.** This is stated explicitly in the paper's own Supplementary Information S4.1: *"the fluorescence levels of each individual mutation cannot be statistically differentiated from the wildtype. In other words, we cannot distinguish if a specific singleton is neutral or slightly deleterious."* The authors only claim an *upper bound* on the fraction of neutral mutants (≈0.23), derived from a mixture model, not per-mutation calls. Any benchmark that grades a model's judgement about a specific near-neutral single substitution is grading noise.

**(b) Single-mutant coverage is thin and non-uniform.** `[verified locally]`
- 1,084 of 4,522 possible single substitutions = **24.0% coverage**
- 233 of 238 positions covered, mean **4.65** substitutions per covered position, median 5, range **1–8**
- **no position has more than 8 of its 19 possible substitutions**, because error-prone PCR only reaches amino acids accessible by a single nucleotide change
- 4 positions have only 1 substitution measured; 45 have ≤3

**(c) Replication is shallow for avGFP specifically.** `[verified locally]` Across the 1,114 single-mutant genotypes, barcode counts are median 4 (min 1, max 59), and **274 (24.6%) rest on a single barcode** and therefore carry no `std` at all. Across *all* genotypes the eLife Table 1 median is 1.

**(d) Stop codons.** The figshare amino-acid table **includes nonsense genotypes** (2,310 genotypes contain a stop; 30 of the 1,114 singles are nonsense) `[verified locally]`, written as `*` in the mutant token. ProteinGym has **removed all of them** — `[verified locally]` zero ProteinGym mutants contain `*`. If you build from figshare you must filter these yourself; they are effectively guaranteed-dark truncations and would inflate any bright/dark classification metric.

**(e) Floor and ceiling.** The dark mode is a censored floor at ≈log₁₀(20), not a measurement. ProteinGym's own documentation warns that DMS assays "do not have a perfect dynamic range, often imposing a restrictive ceiling and/or floor … that is not meaningful for protein function", and that for bimodal assays "rank correlations may not be the optimal choice", recommending AUC/MCC/NDCG/top-10%-recall alongside Spearman ([ProteinGym NeurIPS 2023 D&B](https://pmc.ncbi.nlm.nih.gov/articles/PMC10723403/)).

**(f) Background mismatch.** F64L (§1.1) means the assayed protein is not canonical avGFP, and no structure in the PDB of the *wild-type* protein carries F64L (1EMA and 1GFL have Phe64; 2WUR and 2Y0G have Leu64 — see §3).

---

## 3. Structure

### 3.1 Candidate PDB entries

All values `[verified locally]` from the deposited mmCIF unless cited.

| PDB | Description | Resolution | Mutations vs P42212 | Chains in ASU | Deposited assembly | Modelled range (auth) |
| --- | --- | --- | --- | --- | --- | --- |
| **[1EMA](https://www.rcsb.org/structure/1EMA)** | GFP S65T (Ormö 1996) | **1.90 Å** | **Q80R**; chromophore `CRO` at 65–67; **4× MSE** (selenomethionine at author positions 78, 88, 153, 218 — all four native Met residues) | 1 polymer (A) + 95 waters | monomeric | **2–229** |
| **[1GFL](https://www.rcsb.org/structure/1GFL)** | Wild-type GFP (Yang 1996) | **1.90 Å** | **M1A**, **Q80R**; chromophore modelled as discrete SER65/TYR66/GLY67 | 2 polymer (A, B) + 300 waters | listed as 2 × "monomeric" | **1–230** |
| **[1W7S](https://www.rcsb.org/structure/1W7S)** | Wild-type avGFP | 1.85 Å | **Q80R**; chromophore `GYS` | 4 polymer (A–D) | **tetrameric** | 2–229 |
| **[2WUR](https://www.rcsb.org/structure/2WUR)** | GFP at atomic resolution | **0.90 Å** | **F64L, Q80R, I167T, K238N**; chromophore `GYS` | 1 polymer | monomeric | 3–230 |
| **[2Y0G](https://www.rcsb.org/structure/2Y0G)** | EGFP | 1.50 Å | **F64L, H231L**, His-tag numbered −13…0 | 1 polymer | monomeric | 17–242 |
| **[1QYO](https://www.rcsb.org/structure/1QYO)** | pre-cyclisation S65G/Y66G | — | F64L, S65G, Y66G, F99S, M153T, V163A | 2 polymer | monomeric | — |

Notes and corrections to common assumptions:

- **1EMA's own `struct_ref_seq_dif` table does *not* list S65T.** It lists only the three chromophore rows. The S65T identity comes from the publication — Ormö M, Cubitt AB, Kallio K, Gross LA, Tsien RY, Remington SJ, "Crystal structure of the *Aequorea victoria* green fluorescent protein", *Science* 273:1392–1395 (1996), DOI [10.1126/science.273.5280.1392](https://doi.org/10.1126/science.273.5280.1392): *"The structure of Thr⁶⁵ GFP has been determined at 1.9 angstrom resolution."* Because residue 65 is absorbed into the `CRO` residue, **the Thr vs Ser identity at 65 is not independently recoverable from the coordinates**.

  **Correction (2026-10-20):** an earlier revision of this document stated that 1EMA has Gln80 and does not carry Q80R. That was wrong. It came from a residue-by-residue comparison run under biotite's default *label* numbering, which is frameshifted by −2 past the chromophore (the very trap described below), so the compared residue was not actually position 80. Re-run in author numbering, **1EMA chain A residue 80 is ARG: the entry does carry Q80R** `[verified locally]`. Corrected author-numbering diffs against P42212, over modelled residues only: 1EMA `Q80R`; 1GFL `M1A, Q80R`; 1W7S `Q80R`; 2WUR `F64L, Q80R, I167T`; 2Y0G `F64L`. The `struct_ref_seq_dif`-derived entries in the table (which additionally list 2WUR `K238N` and 2Y0G `H231L`) remain correct — those residues are simply not modelled in the coordinates, so a coordinate-based diff cannot see them. Q80R is a near-ubiquitous PCR artefact of the original avGFP clone and is present in essentially every wild-type-background GFP structure.
- **1GFL is the "wild-type dimer", but the deposited assembly annotation says otherwise.** The paper — Yang F, Moss LG, Phillips GN Jr, "The molecular structure of green fluorescent protein", *Nat Biotechnol* 14:1246–1251 (1996), DOI [10.1038/nbt1096-1246](https://doi.org/10.1038/nbt1096-1246) — states *"Two protomers pack closely together to form a dimer in the crystal"*. The mmCIF `pdbx_struct_assembly` lists two separate monomeric assemblies `[verified locally]`. Treat "1GFL is the dimer" as a statement about the crystal content and the paper's interpretation, not about the PDB's biological-assembly annotation. RCSB also reports "Mutation(s): 0" for 1GFL even though the coordinates contain ALA1 and ARG80 — a metadata inconsistency, not a coordinate one.
- **1W7S is the entry annotated tetrameric**, which is a crystallographic artefact of that form, not a claim about avGFP in solution.

### 3.2 Does PDB numbering match Sarkisyan numbering?

**Yes, with one structural quirk and no sequence offset.** `[verified locally]`, by comparing `auth_seq_id` against `label_seq_id` in the raw `atom_site` records:

- All of 1EMA/1GFL/1W7S/2WUR use **author numbering == canonical avGFP numbering == ProteinGym numbering**. There is **no offset**. (2Y0G is the exception: it carries an N-terminal His-tag numbered −13…0 plus an inserted Val1, so its own tag residues are negative but residues 2–238 still line up.)
- **The quirk:** in every entry where the chromophore is modelled as a single fused residue (`CRO` in 1EMA/2Y0G, `GYS` in 1W7S/2WUR), that residue has `auth_seq_id = 66`, and **author IDs 65 and 67 simply do not exist**. 1GFL is the exception — it models SER65/TYR66/GLY67 as three discrete residues, so its numbering is gapless.
- Consequently 1EMA chain A contains **226 modelled residues spanning author IDs 2–229, with 65 and 67 absent** `[verified locally]`.
- `label_seq_id` (the compressed entity numbering) **drifts by −2 after the chromophore** and must never be used for cross-referencing against the DMS data. In biotite 2.0, `pdbx.get_structure(...)` **defaults to label numbering**, which silently produces a 2-residue frameshift past residue 64 — I hit exactly this and had to pass `use_author_fields=True`. Biopython's `Bio.PDB` uses author numbering natively.

**Residue 64 mismatch.** 1EMA and 1GFL have Phe64; the Sarkisyan data has Leu64. For burial purposes this is a conservative hydrophobic→hydrophobic swap at a buried position, but any per-residue table built on 1EMA will disagree with the DMS reference on the wild-type identity at 64.

### 3.3 Computing relative solvent accessibility

Three realistic lightweight options; I tested two.

| Tool | Install | SASA | Secondary structure | Notes |
| --- | --- | --- | --- | --- |
| **freesasa** (Python bindings) | `pip install freesasa` | yes, Lee–Richards | no | `calc().residueAreas()[chain][resnum].relativeTotal` gives RSA directly. Parses PDB format cleanly; **silently drops the non-standard chromophore residue** |
| **biotite** | `pip install biotite` | `structure.sasa()`, Shrake–Rupley | `annotate_sse()` (P-SEA) — **not DSSP** | pure-Python/NumPy, no binary. Needs `use_author_fields=True` |
| **DSSP** (`mkdssp`) | **separate C++ binary** (`brew install brewsci/bio/dssp`, or conda `mkdssp`) | yes | yes, the reference 8-state assignment | `Bio.PDB.DSSP` is only a wrapper and fails without the binary. **Not available on this machine** `[verified locally]` |
| **pydssp** | `pip install pydssp` | **no** | yes (simplified, H-bond based) | `[verified locally]` installs fine but exposes only `assign` / `get_hbond_map` — secondary structure only, no SASA. Not a DSSP substitute for RSA |

`[verified locally]` Cross-check on 1EMA chain A: biotite (Shrake–Rupley, 1000 points, `vdw_radii='Single'`, normalised by Tien et al. 2013 theoretical max-ASA) vs freesasa (Lee–Richards, its built-in `relativeTotal`): **Pearson r = 0.9891 over 221 common residues, median absolute RSA difference 0.052**. The rank agreement is excellent but the absolute values are not interchangeable, because the two use different max-ASA reference scales (freesasa defaults to Sander/Rost-style; I used Tien et al. "theoretical" values). **Pick one max-ASA table and one algorithm and state it**, or burial thresholds will not be reproducible. Recommended max-ASA reference: Tien MZ, Meyer AG, Sydykova DK, Spielman SJ, Wilke CO, "Maximum allowed solvent accessibilites of residues in proteins", *PLoS ONE* 8:e80635 (2013), DOI [10.1371/journal.pone.0080635](https://doi.org/10.1371/journal.pone.0080635).

Two practical gotchas, both confirmed locally:
1. **The chromophore breaks every tool.** `CRO`/`GYS` is not a standard residue, has no max-ASA entry, and is skipped by both biotite's and freesasa's residue-wise normalisation. Residues 65–67 therefore have **no RSA value at all** from an off-the-shelf run on 1EMA. Either use 1GFL (discrete Ser65/Tyr66/Gly67) for those three positions, or define them as a special case. `[verified locally]` biotite yielded RSA for 225 residues and freesasa for 221, out of 226 modelled.
2. **Compute on the monomer.** 1GFL (2 chains) and 1W7S (4 chains) will report interface residues as buried if you pass the whole asymmetric unit. 1EMA has a single polymer chain and is the safest default.

---

## 4. Topology

### 4.1 The fold

11-stranded antiparallel β-barrel with a coaxial central α-helix carrying the chromophore. Named the **"β-can"** by Yang, Moss & Phillips, *Nat Biotechnol* 14:1246–1251 (1996), DOI [10.1038/nbt1096-1246](https://doi.org/10.1038/nbt1096-1246): *"a cylinder, comprising 11 strands of beta-sheet with an alpha-helix inside and short helical segments on the ends of the cylinder … with beta-structure on the outside and alpha-helix on the inside, represents a new protein fold, which we have named the beta-can."* Ormö et al. 1996 independently: *"an 11-stranded beta barrel with a coaxial helix, with the chromophore forming from the central helix."*

### 4.2 Strand residue ranges

`[verified locally]` from the deposited `struct_sheet_range` records (author numbering). 1EMA lists exactly 11 strands; 1GFL and 2WUR list 12 rows each because one strand is split/duplicated in their annotation.

| Strand | 1EMA | 1GFL | Notable residues (cross-check) |
| --- | --- | --- | --- |
| β1 | 12–22 | 11–22 | |
| β2 | 25–36 | 25–36 (+ dup 29–36) | |
| β3 | 41–48 | 41–48 | **F46** ("located in b3") |
| — | *central helix ≈ 56–72, chromophore at 65–67* | | |
| β4 | 92–100 | 92–100 | |
| β5 | 105–115 | 105–115 | |
| β6 | 118–128 | 118–128 | **E126** ("located in b6") |
| β7 | 148–152 | 148–155 | **N149** ("located in b7") |
| β8 | 160–170 | 160–170 | |
| β9 | 176–187 | 176–187 | **L194** ("between b9 and b10") |
| β10 | 199–207 | 199–208 | **S208** ("located in b10") |
| β11 | 220–227 | 217–227 | **F223** (interacts with S208L, V206) |

The cross-check column comes from an independent source that labels strands by number — Kim H et al., "The mechanism of folding robustness revealed by the crystal structure of extra-superfolder GFP", *FEBS Lett* (2017), DOI [10.1002/1873-3468.12534](https://doi.org/10.1002/1873-3468.12534) — and every one of its five strand assignments agrees with the table above. I consider the β1–β11 numbering confirmed.

**Boundaries differ by a few residues between entries**, most sharply at β7 (148–152 in 1EMA vs 148–155 in 1GFL) and β11 (220–227 vs 217–227). Any benchmark question of the form "which strand is residue X in?" must either avoid the ±3-residue boundary zones or commit to a single named structure.

**Do not derive the strand list algorithmically from a lightweight tool.** `[verified locally]` biotite's `annotate_sse()` (P-SEA) on 1EMA chain A returns **13** β-runs of ≥3 residues, splitting β10 into 199–203 and 205–209, inserting a spurious 192–196 run, merging 144–154, and **finding no α-helix at all of ≥4 residues** — the chromophore interrupts the chain and P-SEA loses the central helix entirely. The deposited `struct_conf` records are similarly fragmented (1EMA lists helices at 4–8, 57–60, 69–71, 83–86). Use the deposited `struct_sheet_range` plus the literature for the central helix, or run real DSSP.

### 4.3 Inward/outward side-chain alternation

**Documented in the literature, and I confirmed it quantitatively in avGFP itself.**

Literature: the encapsulation DMS of GFP's C-terminal strands (bioRxiv [10.1101/274753](https://doi.org/10.1101/274753)) states the a priori expectation and then confirms it — *"amino acid residues pointing into the core of the β-barrel should be more restricted than those pointing out … the strongest signal we observed in our assay was a selection against mutations pointing into the GFP molecule, especially for mutations to hydrophilic residues … at 14 positions pointing into the β-barrel, mutations were significantly depleted. In contrast, this was only the case for 6 positions that point into solvent."* The general mechanism is spelled out in the deep-indel paper (bioRxiv [2023.10.06.561180](https://www.biorxiv.org/content/biorxiv/early/2024/03/21/2023.10.06.561180.full.pdf)): *"in beta-strands, substitutions in every second aa have more similar effects, consistent with their side chains being on the same face of a strand"*, and this periodicity is absent for indels.

`[verified locally]` Within-strand autocorrelation across the eleven 1EMA strand ranges, using my biotite RSA values:

| lag | RSA autocorrelation | mean single-mutant brightness autocorrelation |
| --- | --- | --- |
| 1 | **−0.556** | −0.317 |
| 2 | **+0.657** | **+0.552** |
| 3 | **−0.724** | −0.311 |
| 4 | +0.501 | +0.287 |

Odd lags negative, even lags positive, in both burial and measured tolerance — exactly the i, i+2 alternation signature. Per-strand burial patterns (`I` = RSA < 0.20, `o` = exposed) are clean for most strands and ragged for two:

```
β1   12-22   IoIoIoIoIII
β2   25-36   ooIIIoIoooII     <- not alternating
β3   41-48   oIoIoIII
β4   92-100  IIIoIoIoI
β5  105-115  IIoIoIoIIIo
β6  118-128  oIIIoIoIoIo
β7  148-152  IoIoI
β8  160-170  IIoIoIoIoIo
β9  176-187  oIIIIIoIoIoI     <- not alternating
β10 199-207  IoIoIoIoI
β11 220-227  IoIoIoIo
```

β2 and β9 break the pattern, and in both cases the deposited range extends past the clean strand core (β9's 176–187 is the longest annotated strand). **The alternation is a real, usable signal for 9 of 11 strands but is not safe to assert as a universal rule.**

### 4.4 Published burial vs mutational tolerance in GFP

**Qualitatively yes; quantitatively, I could not find a published correlation coefficient specific to avGFP burial vs DMS tolerance.**

What exists:
- Sarkisyan et al. 2016 state it qualitatively in the main text: *"Mutations with a strong effect on fluorescence preferably resided at sites that coded for amino acid residues oriented internally towards the chromophore (Figure 2b,c), which is consistent with data on other proteins on the preference of deleterious mutations to target buried residues."* Figure 2b/c is illustrated on a single selected β-strand. They also report epistasis being *"more common between pairs of sites where both residues are internally oriented"* (Extended Data Fig. 4e).
- The only correlation coefficient the paper reports for a per-site property is **conservation**, not burial: Spearman **0.40** between mutational impact and site conservation (Extended Data Fig. 3a).
- The encapsulation DMS (§4.3) gives counts of significantly-depleted inward vs outward positions, not a coefficient.
- The cross-protein quantitative anchor is the deep-indel paper's **mode r = 0.644** for RSA vs substitution tolerance across 171 domains — not GFP-specific.

**So I computed it** `[verified locally]`, over the 222 positions that have both a 1EMA RSA value and ≥1 measured single missense mutant, using mean single-mutant log-fluorescence per position:

- **Spearman ρ = 0.583**, Pearson r = 0.461
- restricted to the 206 positions with ≥3 measured substitutions: **Spearman ρ = 0.560**
- **buried sites (RSA < 0.10, 87 positions, 352 substitutions): 20.2% dark** (score < 2.5)
- **exposed sites (RSA > 0.40, 45 positions, 228 substitutions): 0.9% dark**

That is a ~22-fold enrichment of dark substitutions at buried vs exposed positions, which is a strong and benchmark-usable effect. I am reporting this as my own calculation, not as a published result.

---

## 5. Chromophore and spectral variants

### 5.1 The chromophore

Formed autocatalytically from **Ser65-Tyr66-Gly67** by cyclisation, dehydration and O₂-dependent oxidation to a *p*-hydroxybenzylidene-imidazolinone. Primary source: Heim R, Prasher DC, Tsien RY, "Wavelength mutations and posttranslational autoxidation of green fluorescent protein", *PNAS* 91:12501–12504 (1994), DOI [10.1073/pnas.91.26.12501](https://doi.org/10.1073/pnas.91.26.12501) — *"a p-hydroxybenzylidene-imidazolidinone chromophore, which is generated by cyclization and oxidation of the protein's own Ser-Tyr-Gly sequence at positions 65-67 … formation of the final fluorophore requires molecular oxygen and proceeds with a time constant (approximately 4 hr at 22 °C and atmospheric pO₂) independent of dilution, implying that the oxidation does not require enzymes or cofactors."*

In the PDB the mature chromophore appears as ligand codes **`CRO`** (1EMA, 2Y0G) or **`GYS`** (1W7S, 2WUR) `[verified locally]`, at author residue 66.

### 5.2 Residues required for maturation

**Arg96 and Glu222** — both buried, both directly adjacent to the chromophore, both highly conserved.

- **Arg96.** Barondeau DP, Kassmann CJ, Tainer JA, Getzoff ED, "Defining the role of arginine 96 in green fluorescent protein fluorophore biosynthesis", *Biochemistry* 44 (2005), DOI [10.1021/bi051388j](https://doi.org/10.1021/bi051388j): R96M *"exhibits dramatically slower chromophore maturation kinetics (from hours to months)"*; of all 19 substitutions screened, **only R96K restores wild-type kinetics**; R96A can be rescued by a compensating Q183R that restores the lost positive charge — *"the importance of the presence of positive charge, rather than its exact position."*
- **Glu222.** Sniegowski JA, Phail ME, Wachter RM / Wachter lab, "Base catalysis of chromophore formation in Arg96 and Glu222 variants of green fluorescent protein", *JBC* 280 (2005), DOI [10.1074/jbc.M412327200](https://doi.org/10.1074/jbc.m412327200): in an **EGFP background**, R96M time constant 7.5 × 10³ h at pH 7 and E222Q 32 h at pH 7, versus 1 h for EGFP, which is pH-independent over pH 7–10. E222Q *accelerates* beyond EGFP at pH 9–10. Mechanistic assignment: Glu222 carboxylate as general base abstracting a proton from the Gly67 amide nitrogen or Tyr66 α-carbon; Arg96 as electrophile lowering those pKₐ values and stabilising the α-enolate. Apparent pKₐ 6.5 (Glu222 in R96M) and 9.2 (Gly67 amide N in E222Q).
- Complementary structural mechanism, with a role for the **Thr62 carbonyl oxygen** as the base initiating dehydration: Barondeau DP, Putnam CD, Kassmann CJ, Tainer JA, Getzoff ED, *PNAS* 100:12111 (2003), DOI [10.1073/pnas.2133463100](https://doi.org/10.1073/pnas.2133463100).

### 5.3 Spectral-variant mutations

The central caveat: **three of the four "standard" mutations were never characterised as isolated point mutants on wild-type avGFP.** T203Y and the bright Y66W variants exist in the literature only in combination; the commonly quoted numbers are for multi-mutant clones. Background matters and is frequently dropped in secondary sources.

| Variant | Mutation(s) actually measured | Ex (nm) | Em (nm) | ε | QY | Primary source |
| --- | --- | --- | --- | --- | --- | --- |
| wild-type avGFP | none | **395** (minor 475) | **508** | 21,000 (7,150) | 0.77 | Heim & Tsien 1996, Table 1 |
| wild-type (Tsien review) | none or Q80R | 395–397 / 470–475 | 504 | 25–30k / 9.5–14k | 0.79 | Tsien 1998, Table 1 |
| **S65T** | **S65T alone** | **489** | **511** | 39,200 | 0.66 | Heim & Tsien 1996, Table 1 |
| S65T (orig. report) | S65T alone | 490 | 510 | 39,200 @ 490 | 0.68 | Heim, Cubitt & Tsien 1995 |
| **EGFP** | **F64L + S65T** | **488** | **507** | 55–57k | 0.60 | Cormack 1996 / Tsien 1998, Table 1 |
| **Y66H (BFP, "P4")** | **Y66H alone** | **383** | **447** | 13,500 | **0.21** | Heim & Tsien 1996, Table 1 |
| Y66H (Tsien review) | Y66H alone | 384 | 448 | 21,000 | 0.24 | Tsien 1998, Table 1 |
| P4-3 | Y66H + **Y145F** | 381 | 445 | 14,000 | 0.38 | Heim & Tsien 1996 |
| **Y66W (CFP, point mutant)** | **Y66W alone** | **436** | **485** | — | — | Tsien 1998, Table 1 (citing Heim 1994) |
| W7 | Y66W + **N146I, M153T, V163A, N212K** | 433 (453) | 475 (501) | 18,000 | 0.67 | Heim & Tsien 1996, Table 1 |
| ECFP / W1B | Y66W + **F64L, S65T, N146I, M153T, V163A** | 434 (452) | 476 (505) | 32,500 | 0.40 | Tsien 1998, Table 1 |
| **T203Y (YFP "10C")** | **T203Y + S65G, V68L, S72A** | **514** | **527** | 83,400 | 0.61 | Tsien 1998, Table 1 |
| YFP 10C (FPbase/EYFP) | same, + H231L | 513 | 527 | 67,000 | 0.67 | [FPbase EYFP](https://www.fpbase.org/protein/eyfp/) |
| Topaz | T203Y + S65G, S72A, K79R | 514 | 527 | 94,500 | 0.60 | Tsien 1998, Table 1 |
| S65G/S72A/T203H | T203**H** variant | 508 | 518 | 48,500 | 0.78 | Tsien 1998, Table 1 |

Sources: Heim R, Cubitt AB, Tsien RY, *Nature* 373:663–664 (1995), DOI [10.1038/373663b0](https://doi.org/10.1038/373663b0). Heim R, Tsien RY, *Curr Biol* 6:178–182 (1996), DOI [10.1016/S0960-9822(02)00450-5](https://doi.org/10.1016/s0960-9822(02)00450-5). Cormack BP, Valdivia RH, Falkow S, *Gene* 173:33–38 (1996), GFPmut1 = F64L/S65T, excitation 488 / emission 507 (see also [US5804387A](https://patents.google.com/patent/US5804387A/en), which gives GFPmut1 488/507 measured on a SPEX fluorolog). Patterson GH, Knobel SM, Sharif WD, Kain SR, Piston DW, *Biophys J* 73:2782–2790 (1997), DOI [10.1016/S0006-3495(97)78307-3](https://doi.org/10.1016/s0006-3495(97)78307-3), [PMC1181180](https://pmc.ncbi.nlm.nih.gov/articles/PMC1181180/). Tsien RY, "The green fluorescent protein", *Annu Rev Biochem* 67:509–544 (1998), DOI [10.1146/annurev.biochem.67.1.509](https://doi.org/10.1146/annurev.biochem.67.1.509), Table 1 — the standard consolidated table. Wachter RM, Elsliger M-A, Kallio K, Hanson GT, Remington SJ, *Structure* 6:1267–1277 (1998), DOI [10.1016/S0969-2126(98)00127-0](https://doi.org/10.1016/s0969-2126(98)00127-0) — structural basis of the T203Y shift (PDB [1YFP](https://www.rcsb.org/structure/1YFP), 2.5 Å; π-stacking of Tyr203 with the chromophore, chromophore displaced ~1 Å; pKₐ 7.0).

Specific discrepancies a benchmark must not paper over:

1. **"Y66W = 433/475" is wrong for the point mutant.** 433/475 is clone **W7**, which carries four additional mutations. The Y66W point mutant is **436/485** (Tsien 1998, Table 1). Heim & Tsien 1996 did not characterise Y66W alone.
2. **T203Y has never been reported alone.** Every published T203Y number is on an S65G/S72A(/V68L) background. Wachter et al. are explicit that the companion mutations *"improve the brightness"* and that the chromophore sits ~1 Å away from its position in other structures.
3. **S65T: 489/511 vs 490/510.** Heim & Tsien 1996 Table 1 says 489/511; the original 1995 Nature report says 490/510. Both are primary; pick one and cite it.
4. **Y66H numbers drift by 1 nm** between the 1996 table (383/447) and the 1998 review (384/448) for the same clone.
5. **Wild-type avGFP has two excitation peaks** (395 major, ~475 minor) and the "395" figure is quoted variously as 395, 396 or 397. A single-number answer key for wild-type excitation is not defensible.
6. **EGFP's conventional definition includes H231L** (FPbase, and 2Y0G `[verified locally]` carries F64L + H231L), though the spectroscopy papers treat EGFP as F64L/S65T. H231L is generally regarded as spectrally neutral but it is part of the commercial construct.

---

## 6. Licensing

| Asset | Licence | Redistributable in a public repo? | Evidence |
| --- | --- | --- | --- |
| **Sarkisyan figshare dataset** (all files, incl. `amino_acid_genotypes_to_brightness.tsv`) | **CC BY 4.0** | **Yes, with attribution** | `[verified locally]` figshare API returns `{"value":1,"name":"CC BY 4.0","url":"https://creativecommons.org/licenses/by/4.0/"}` for article 3102154 |
| **PDB coordinate files** (1EMA, 1GFL, …) | **CC0 1.0** public domain | **Yes, unrestricted** | [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies); [RCSB usage policy](https://www.rcsb.org/pages/usage-policy); [advisory.txt](https://files.wwpdb.org/pub/pdb/advisory.txt) |
| **ProteinGym repository** | **MIT** | **Yes** | `[verified locally]` `LICENSE` on `main` = MIT, "Copyright (c) 2023 OATML-Markslab, Pascal Notin, Aaron Kollasch, Daniel Ritter, Lood van Niekerk" |
| **UniProt P42212 sequence** | CC BY 4.0 (UniProt terms) | Yes, with attribution | UniProt consortium licence terms |
| **eLife 2022 orthologue datasets** | CC BY 4.0 (eLife default) | Yes, with attribution | [DOI 10.7554/eLife.75842](https://doi.org/10.7554/eLife.75842) |
| **Nature 2016 article text / figures** | Springer Nature copyright | **No** | Reproduce numbers and cite; do not redistribute figures or SI PDF |
| **Tsien 1998 *Annu Rev Biochem* Table 1** | Annual Reviews copyright | **No** | Cite the values, do not reproduce the table verbatim as a file |

Practical reading:

- **Both pillars of the benchmark are freely redistributable.** The DMS data is CC BY 4.0 and the structures are CC0. Derived files (per-residue RSA tables, filtered single-mutant tables, binarised labels) are derivatives of CC BY 4.0 data, so ship them with a `DATA_LICENSE`/`SOURCES.md` crediting Sarkisyan et al. 2016 (DOI + figshare DOI) and the PDB entries. CC BY has no share-alike obligation, so your own code can stay under whatever licence you prefer.
- **Two caveats.** (i) ProteinGym's MIT licence covers the *repository*; the DMS CSVs within it are curated third-party experimental data, so attribute Sarkisyan et al. regardless of which copy you redistribute. (ii) wwPDB prohibits redistributing *modified* coordinate files **under the same filename** as the archive — if you ship a stripped or renumbered 1EMA, rename it (e.g. `1ema_chainA_monomer.cif`).
- Spectral wavelengths are facts and not copyrightable; the *tables* that collect them are. Rebuild any spectral answer key from the primary values with per-row citations rather than copying Tsien's Table 1.

---

## 7. Recommendations and open risks

### Recommendations

1. **Declare the sequence explicitly, and declare it as F64L avGFP.** Use ProteinGym's 238-aa `target_seq` (= P42212 with F64L) as the single reference, with 1-based numbering including Met1. Do not call it "wild-type avGFP" without the qualifier, and do not mix in P42212 for the wild-type identity at position 64.
2. **Use 1EMA chain A as the structural reference, computed as a monomer.** Single polymer chain, 1.90 Å, author numbering == DMS numbering, no interface artefacts. Hard-code the two numbering quirks: `CRO` at author 66, and author IDs 65 and 67 absent. In biotite, pass `use_author_fields=True`; verify by asserting that residue 110 is Ala and 96 is Arg before computing anything.
3. **Fix one RSA recipe and record it in the repo.** Recommended: biotite Shrake–Rupley with ≥1000 points, normalised by Tien et al. 2013 theoretical max-ASA, on the 1EMA monomer, with 1GFL used only to fill residues 65–67. Pin `biotite` and the max-ASA table in the dependency file. Do not use freesasa's `relativeTotal` interchangeably with a Tien-normalised value.
4. **Take strand ranges from the deposited `struct_sheet_range` of a single named entry, not from an SSE algorithm.** 1EMA gives a clean 11-strand list. Exclude the ±3-residue boundary zones from any "which strand" question, since 1EMA and 1GFL disagree at β7 and β11.
5. **Grade burial questions in bins, not in continuous RSA.** Three bins (buried < 0.10, intermediate, exposed > 0.40) are robust to the 0.052 median disagreement between SASA tools; a continuous RSA answer key is not.
6. **For per-substitution tolerance, grade only what the data can support.** Restrict to positions with ≥3 measured substitutions (206 positions), ask only about substitutions that actually appear in the data, and prefer "is this substitution tolerated or dark" over "what is its log-fluorescence". Treat the ~20% vs ~1% dark-rate contrast between buried and exposed positions as the signal; treat small differences among bright variants as noise.
7. **For spectral questions, make the genetic background part of the question and part of the answer.** "What are the excitation/emission maxima of avGFP carrying S65G/V68L/S72A/T203Y (YFP 10C)?" is answerable; "what are T203Y's maxima?" is not. Accept ±2 nm tolerance and cite a specific primary table per item.
8. **Filter stop codons explicitly if building from figshare.** 2,310 genotypes, 30 of them singles. ProteinGym has already removed them.
9. **Consider the eLife 2022 orthologue data as a held-out set.** amacGFP/cgreGFP/ppluGFP2 are CC BY, measured with 7× lower variance, and span 18–82% identity — a natural generalisation test that also guards against memorisation of the much-reused avGFP numbers.

### Open risks (things that could break the design)

1. **The biggest one: single-mutant effects in Sarkisyan are not individually resolvable.** The authors say so themselves. With 24.6% of single-mutant genotypes resting on one barcode, a wild-type σ of ~0.107, and most bright singles within ~6σ of wild type, any item whose correct answer depends on distinguishing a mildly deleterious substitution from a neutral one is scoring noise, not knowledge. **Mitigation: binary bright/dark items with a margin, restricted to positions with ≥3 substitutions; or move the per-substitution axis to the eLife 2022 datasets.**
2. **Error-prone PCR caps per-position coverage at 8 of 19 substitutions, with 24.0% overall coverage.** You cannot build a per-residue × per-amino-acid grid. Any "grid probe" framing must be sparse and explicitly data-driven, and must not ask about substitutions that were never measured. 4 positions have a single measured substitution; 45 have ≤3.
3. **Burial and tolerance are correlated at ρ ≈ 0.58, not ≈ 1.** If the benchmark asks per-residue burial and per-substitution tolerance as separate axes, a model that knows only burial will score moderately well on tolerance, and one that knows only tolerance will score moderately well on burial. The two axes are not independent, and aggregate scores will overstate structural knowledge. **Mitigation: report the axes separately, and include decorrelated items — buried-but-tolerant and exposed-but-dark positions.**
4. **The F64L background mismatch is a silent-wrong-answer generator.** Ask "what is residue 64 in avGFP?" and the defensible answer differs between UniProt (Phe) and the benchmark's own DMS reference (Leu). Either exclude position 64 or state the background in the prompt.
5. **No single structure matches the assayed protein.** 1EMA/1GFL have Phe64 and no F64L; 2WUR has F64L but also Q80R/I167T/K238N; 2Y0G is EGFP with a His-tag. Mapping DMS onto structure always involves at least one mismatched residue. This is minor for burial (all the mismatches are at positions whose burial is unlikely to change) but should be disclosed.
6. **Residues 65–67 have no RSA from a standard run**, because the chromophore is a fused non-standard residue. These are exactly the residues a GFP benchmark most wants to ask about. Special-case them deliberately rather than letting them fall out of the dataset.
7. **The dark mode is a censored floor, not a measurement.** Ranking within the dark mode is meaningless; ~14,400 variants sit in a single 0.2-wide bin at 1.4. Any metric that rewards ordering among dark variants is measuring nothing.
8. **The i, i+2 alternation holds for 9 of 11 strands, not all 11.** β2 (25–36) and β9 (176–187) do not alternate cleanly in 1EMA-derived RSA. Do not state alternation as a rule the model is expected to apply uniformly.
9. **avGFP is one of the most-reused benchmark proteins in existence** (ProteinGym, DeePEn, FLIP, and the LowNSAE/GFP_Robustness repos all use `GFP_AEQVI_Sarkisyan_2016`). Contamination of LLM training data with the exact DMS table, and with ProteinGym leaderboard discussion, is close to certain. Burial/structure items are likely safer than DMS-score items, and the eLife orthologues are safer than avGFP.
10. **Unresolved items.** (i) I did not byte-verify the ProteinGym v1.3 bulk copy against the ICML2022 per-file copy (the reference metadata matches exactly, which is strong but indirect). (ii) The wild-type barcode count differs between the released aggregate row (3,645) and the paper's Figure 2a / eLife Table 1 (2,442/2,444) — different filtering stages, unexplained in the released files. (iii) No published GFP-specific burial-vs-tolerance correlation coefficient exists; the ρ = 0.583 above is my calculation and should be labelled as such in anything user-facing. (iv) 1EMA's deposited `struct_ref_seq_dif` does not record S65T, so that identity rests on the publication text alone.

---

## Appendix: reproduction commands

```bash
# DMS data (CC BY 4.0)
curl -L -o amino_acid_genotypes_to_brightness.tsv https://ndownloader.figshare.com/files/4820647
curl -L -o avGFP_reference_sequence.fa              https://ndownloader.figshare.com/files/4820653
curl -L -o GFP_AEQVI_Sarkisyan_2016.csv \
  https://huggingface.co/datasets/ICML2022/ProteinGym/resolve/main/ProteinGym_substitutions/GFP_AEQVI_Sarkisyan_2016.csv
curl -L -o DMS_substitutions.csv \
  https://raw.githubusercontent.com/OATML-Markslab/ProteinGym/main/reference_files/DMS_substitutions.csv

# Structures (CC0)
curl -L -o 1EMA.cif https://files.rcsb.org/download/1EMA.cif
curl -L -o 1GFL.cif https://files.rcsb.org/download/1GFL.cif

# Reference sequence
curl -L -o P42212.fasta https://rest.uniprot.org/uniprotkb/P42212.fasta

# Environment
python3.12 -m venv .venv && ./.venv/bin/pip install biotite freesasa biopython
```

RSA, in the recipe recommended above:

```python
import biotite.structure.io.pdbx as pdbx, biotite.structure as struc, numpy as np

f = pdbx.CIFFile.read("1EMA.cif")
arr = pdbx.get_structure(f, model=1, use_author_fields=True)   # author numbering is mandatory
arr = arr[(arr.res_name != "HOH") & (arr.chain_id == "A")]     # monomer only
assert arr[arr.res_id == 110].res_name[0] == "ALA"             # numbering sanity check
assert 65 not in arr.res_id and 67 not in arr.res_id            # chromophore is fused at 66

sasa = struc.sasa(arr, vdw_radii="Single", point_number=1000)
per_res = struc.apply_residue_wise(arr, sasa, np.nansum)
res_ids, res_names = struc.get_residues(arr)
# divide by Tien et al. 2013 theoretical max-ASA; CRO at 66 has no entry and must be special-cased
```
