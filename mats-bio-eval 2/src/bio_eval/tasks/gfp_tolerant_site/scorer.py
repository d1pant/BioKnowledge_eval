"""Score a consecutive triplet. Many starts are accepted; the letters must match."""

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

from bio_eval.tasks.gfp_tolerant_site.dataset import reference_sequence
from bio_eval.tasks.gfp_tolerant_site.parsing import parse_response


@metric
def bracket_lift() -> Metric:
    """Hit minus that bracket's chance. Keys are prefixed so they do not collide."""

    def compute(scores: list[SampleScore]) -> dict[str, float]:
        lifts: dict[str, float] = {}
        for sample_score in scores:
            meta = sample_score.sample_metadata or {}
            bracket_id = meta.get("bracket_id")
            chance = meta.get("chance")
            if bracket_id is None or chance is None:
                continue
            lifts[f"lift_{bracket_id}"] = sample_score.score.as_float() - float(chance)
        return lifts

    return compute


@scorer(
    metrics=[
        accuracy(),
        stderr(),
        grouped(accuracy(), "bracket_id", all=False),
        bracket_lift(),
    ]
)
def tolerant_site_scorer():
    sequence = reference_sequence()

    async def score(state: TaskState, target: Target) -> Score:
        del target
        completion = state.output.completion or ""
        parsed = parse_response(completion)
        meta = state.metadata or {}
        accepted = {int(value) for value in meta.get("accepted_starts", [])}
        start_ok = parsed.start is not None and parsed.start in accepted
        letters = None
        if parsed.start is not None and 1 <= parsed.start <= len(sequence) - 2:
            letters = sequence[parsed.start - 1 : parsed.start + 2]
        letters_ok = parsed.sequence is not None and parsed.sequence == letters
        correct = start_ok and letters_ok
        mismatch = bool(start_ok and parsed.sequence is not None and not letters_ok)
        return Score(
            value=CORRECT if correct else INCORRECT,
            answer=None if parsed.start is None else str(parsed.start),
            explanation=completion[:500],
            metadata={
                "start": parsed.start,
                "sequence": parsed.sequence,
                "confidence": parsed.confidence,
                "parse_error": parsed.error,
                "sequence_mismatch": mismatch,
            },
        )

    return score
