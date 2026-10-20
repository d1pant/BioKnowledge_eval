# Session: first provider runs and the two bugs they exposed

Tool: Claude Science (agentic session, `4d7c557d-1886-454b-87a4-5763bad5fc06`). Date: 2026-10-20.
Status: written by the agent at the end of the session. It is a session record, not a
verbatim chat export. Commands, model ids and every number below were produced by tool
calls in the session and are reproducible from `results/logs/`.

## Purpose

The repo had both Inspect tasks, offline tests and baselines, but `results/logs/` and
`results/rollouts/` were empty placeholders and no language model had ever been scored.
The submission brief requires at least one real agent rollout. This session was asked to
assess how far along the submission was and to close that gap.

## Choosing a model

The brief suggests open-weight models. Together was the available provider. Five candidates
were probed with a direct chat-completion call before any eval was run, checking two things:
whether the model emits parseable content inside Task 1's locked 256-token budget, and
whether it emits tool calls.

| Model | JSON within 256 tokens | Tool calls |
| --- | --- | --- |
| `meta-llama/Llama-3.3-70B-Instruct-Turbo` | yes, 0 reasoning tokens | yes |
| `openai/gpt-oss-120b` | yes on a short prompt, 167 reasoning tokens | yes |
| `moonshotai/Kimi-K3` | no, all 256 tokens spent reasoning | yes |
| `zai-org/GLM-5.3-Flash` | no, all 256 tokens spent reasoning | yes |
| `Qwen/Qwen2.5-72B-Instruct-Turbo` | not serverless on this account | — |

Llama-3.3-70B and gpt-oss-120b were taken forward. Kimi-K3 and GLM-5.3-Flash were rejected
*on measurement grounds, not capability grounds*: at the locked budget they would have been
recorded as scoring zero for a formatting reason.

## What was run

Five runs, all logged to `results/logs/` and listed in the README. Task 1 is 107 samples,
Task 2 is 5 agent trajectories. The third run is the control for the second: same model,
same prompt, larger completion budget.

## Finding 1: the token budget zeroes reasoning models

On the full orientation task gpt-oss-120b at the task default returned empty completions on
96 of 107 samples: 89.7% unparsed, robust accuracy 0.071, `stop_reason: max_tokens`. At
`--max-tokens 2048` the same model scored 0.694 with 0% unparsed. The first number measures
the harness. Both logs are kept as the paired evidence.

## Finding 2: strict scoring hides a correct answer

The Task 2 scorer requires an accepted start *and* a quoted triple matching the reference
sequence at that start. Auditing all ten trajectories against `accepted_starts.json`
directly, rather than trusting the headline:

| Model | Strict | Start only | Expected by chance |
| --- | --- | --- | --- |
| Llama-3.3-70B | 0/5 | 3/5 | 2.19/5 |
| gpt-oss-120b (2048) | 2/5 | 2/5 | 2.19/5 |

Llama named a correct tolerant start in three brackets and scored zero in all three, because
it misquoted the sequence at that start every time. `analysis.report` now prints both
columns. Strict remains the headline; the conclusion does not depend on the choice, because
neither model beats chance under either rule.

## Two bugs in the analysis code

Both were exposed by the first real logs, not by the test suite.

1. `analysis.extract_predictions` emitted rows for `gfp_tolerant_site` samples, which carry
   no `author_resnum`. `analysis.report` then crashed on `int('')`. The documented command
   `python -m analysis.report` did not run to completion on a realistic log directory.
2. `analysis.report` grouped by model name alone, so the two gpt-oss runs at different token
   budgets collapsed into one averaged row — the single most misleading output the pipeline
   could have produced, given finding 1.

Fixed, with three regression tests in `tests/test_report.py`. The task-name filter matches
the final path segment, because Inspect records a bare `gfp_barrel_orientation` under
`inspect eval path.py@name` and a package-qualified `bio_eval/gfp_barrel_orientation`
through the Python API; the first version of the filter used equality and broke an existing
test.

## Other changes

- `openai>=3.4.0` added to runtime dependencies. Without it `inspect eval --model together/...`
  exits immediately; this was the first thing that blocked a provider run.
- `TOGETHER_API_KEY` added to `.env.example`.
- `analysis/export_rollout.py` added; four rollouts exported to `results/rollouts/`.
- `results/validation/gfp-data-survey.md` brought into the repo. It had been sitting one
  directory above the repo root and would not have been in the submission ZIP.

## Not done

- `transcripts/` still holds reconstructed session records rather than verbatim exports, for
  the earlier Cursor sessions and for this one.
- Single epoch per run, so no variance estimate.

## Addendum: the Task 2 key was then made reproducible

Closed in the same session, after the above was written. `accepted_starts.json` had been
verified only against triplet letters transcribed into `tests/test_tolerant_reference.py`
from a design note outside the repo, so a mistake in the original derivation would have been
copied into both the key and its test. The ProteinGym release of the assay is now packaged
under `analysis/ground_truth/data/` (CC BY 4.0, attributed in `SOURCES.md`), and
`analysis.ground_truth.tolerant_sites` reapplies the bright/no-dark rule at the 2.5 cutoff to
rebuild the key from the measurements.

The packaged key reproduces exactly: 15, 7, 22, 35 and 20 accepted starts, every position
identical. Independent checks against the figures in `gfp-data-survey.md` also pass — 51,714
genotypes, 1,084 single missense mutants over 233 positions spanning 3-237 with gaps at 1, 2,
119, 120 and 238, a 1.2834-4.1231 score range, and a 993/91 bright-dark split among the
singles. The position numbering is asserted rather than assumed: all 1,084 singles agree with
the wild-type letter in the packaged FASTA, zero mismatches. One further test requires every
rejected start to have a reason in its window, so the key cannot pass by being a conservative
subset. Seven tests, `analysis`-marked; suite is 52 passing.

The original derivation was therefore correct. What changed is that a reviewer can now check
it instead of trusting it.
