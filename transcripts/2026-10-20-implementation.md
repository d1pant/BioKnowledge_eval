# Implementation

**Session.** Cursor worker `bc-7bbbaaa2`, 2026-10-20.
**Record.** Reconstructed from the commit list and the offline test run on branch `cursor/gfp-strand-orientation-35e6`. The verbatim chat was not exported. No provider was called. The branch was not pushed.

## What was built

Both locked tasks, in the existing checkout. Ground-truth and figure code moved from the runtime package into `analysis/`. Runtime dependencies stayed `inspect-ai==0.3.282` and `python-dotenv`. Biotite, numpy, scipy, and matplotlib are the `analysis` extra.

Commits, oldest first, after the 2026-10-19 ground-truth work:

| Commit | Subject |
| --- | --- |
| `117a2c3` | Move ground-truth and figure code out of the runtime package |
| `72282b8` | Split pyproject deps into runtime and analysis extra |
| `991496c` | Add `gfp_barrel` dataset, prompts, and parsing |
| `4c4bc7a` | Add the orientation scorer and metrics |
| `456ea6e` | Remove placeholder modules |
| `f52e720` | Add the prediction extractor, report, and results poster |
| `6023c7a` | Move synthetic mockups to `results/design-mockups` |
| `d96998c` | Add the tolerant-site reference sequence and accepted starts |
| `d661934` | Add tolerant-site prompts, parser, dataset, and scorer |
| `8e94966` | Add the orientation tool and the tolerant-site agent task |
| `7dec667` | First README for both tasks |

Task 2's solver was frozen only after an offline smoke against Inspect 0.3.282: per-sample tool state, the system string unchanged, and the sixth `residue_orientation` call refused. The smoke script lived outside the repo.

## Tests

`.venv/bin/pytest` passed, 42 tests, including both `mockllm` pipelines. Inspect printed deprecation warnings from its own retry helper. The report regenerated `results/summary.md` from the packaged labels: hydrophobicity accuracy 0.684 on the robust 98 and 0.682 on all 107. Model tables were left empty on purpose.

## Still open after this session

Provider logs, a real agent rollout, and a submission archive were not produced. The README at `7dec667` was a task manual. A later pass on the same branch rewrote it to the LabBench2 outline and added this `transcripts/` section.
