# Locked pair

**Session.** Cursor coordinator `bc-3b8eca37`, 2026-10-19, after the survey, the repair note, the three-of-six note, the window counts, and the orientation labels.
**Record.** Reconstructed from the build brief and the Inspect 0.3.282 implementation plan. Those notes were the source of truth for the build. The brief overrides earlier prompt text in the plan wherever they differ.

## What was locked

Two tasks, one package.

**Task 1, `gfp_barrel_orientation`.** 107 samples, one residue each, one fresh context, no tools. Headline: accuracy on the 98 residues with `|chromophore cosine| ≥ 0.2`. Also report all-107 accuracy, balanced accuracy, per-strand accuracy, and the unparsed rate. MCC, lift over the hydrophobicity rule, alternation, and calibration stay post-hoc, because they need every epoch's label or confidence. The system prompt is the structural-biologist instruction with no braces. The user prompt is rendered into `Sample.input` before Inspect sees it.

**Task 2, `gfp_tolerant_site`.** Five brackets (1–50, 51–100, 101–150, 151–200, 200–238). The model names three consecutive positions that are each tolerant under the single-mutant rule. Headline: mean accuracy. Each bracket is also scored against its own chance (mean chance 43.7%). The agent may call `residue_orientation` at most five times. There is no fluorescence tool and no web search. The sixth call returns an error and no label.

`confidence` is one optional number from 0.5 to 1.0. An interval, a missing value, or a value outside that range does not change correctness.

## Prompt lock

The plan's first prompt draft named PDB 1EMA, the S65T variant, UniProt P42212, and chromophore residues 65–67. The brief removed those from every model-facing string. The README and these transcripts are where they belong. The brief also requires the README to say that `Q157L:K158R:N159T` is the only measured consecutive triple mutant, and to keep that sentence out of the prompt.

## Harness checks done before implementation

The plan was read against the installed `inspect-ai==0.3.282`. Points that the build then followed: `HeadlineMetric` is an object; the system prompt must not contain `{` or `}`; Task 2 uses `react` with `AgentPrompt(instructions=..., assistant_prompt=None, handoff_prompt=None, submit_prompt=None)` and `submit=False`, so the locked system text is not wrapped in Inspect's default assistant prompt; temperature is `--temperature` on the CLI.
