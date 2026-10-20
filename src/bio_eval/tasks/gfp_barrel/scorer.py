"""Score TOWARD/AWAY labels. Confidence is recorded and not graded."""

from __future__ import annotations

from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Metric,
    SampleScore,
    Score,
    Target,
    accuracy,
    grouped,
    metric,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState

from bio_eval.tasks.gfp_barrel.parsing import parse_response


@metric
def robust_accuracy() -> Metric:
    """Accuracy on residues with |chromophore cosine| >= 0.2."""

    def compute(scores: list[SampleScore]) -> float:
        kept = [s for s in scores if (s.sample_metadata or {}).get("robust")]
        if not kept:
            return float("nan")
        return sum(s.score.as_float() for s in kept) / len(kept)

    return compute


@metric
def balanced_accuracy() -> Metric:
    """Mean of the per-class mean correctness. Uses metadata ``truth``."""

    def compute(scores: list[SampleScore]) -> float:
        by_class: dict[str, list[float]] = {}
        for sample_score in scores:
            truth = (sample_score.sample_metadata or {}).get("truth")
            if truth is None:
                continue
            by_class.setdefault(str(truth), []).append(sample_score.score.as_float())
        if len(by_class) < 2:
            return float("nan")
        means = [sum(values) / len(values) for values in by_class.values()]
        return sum(means) / len(means)

    return compute


@metric(scores="unreduced")
def unparsed_rate() -> Metric:
    """Share of sample-epochs whose answer did not parse. Unreduced on purpose."""

    def compute(scores: list[SampleScore]) -> float:
        if not scores:
            return float("nan")
        return sum(s.score.answer == "UNPARSED" for s in scores) / len(scores)

    return compute


@scorer(
    metrics=[
        accuracy(),
        stderr(),
        robust_accuracy(),
        balanced_accuracy(),
        unparsed_rate(),
        grouped(accuracy(), "strand_id", all=False),
    ]
)
def orientation_scorer():
    async def score(state: TaskState, target: Target) -> Score:
        completion = state.output.completion or ""
        parsed = parse_response(completion)
        correct = parsed.label is not None and parsed.label == target.text
        return Score(
            value=CORRECT if correct else INCORRECT,
            answer=parsed.label or "UNPARSED",
            explanation=completion[:500],
            metadata={"confidence": parsed.confidence, "parse_error": parsed.error},
        )

    return score
