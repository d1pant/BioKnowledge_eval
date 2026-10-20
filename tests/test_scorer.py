"""Scorer and post-hoc metric checks on synthetic answers."""

import asyncio

from inspect_ai.model import ModelName, ModelOutput
from inspect_ai.scorer import CORRECT, INCORRECT, SampleScore, Score, Target
from inspect_ai.solver import TaskState

from bio_eval.tasks.gfp_barrel.metrics import (
    alternation_coherence,
    balanced_accuracy,
    brier,
    mcc,
    reliability_bins,
)
from bio_eval.tasks.gfp_barrel.scorer import (
    balanced_accuracy as balanced_metric,
    orientation_scorer,
    robust_accuracy,
    unparsed_rate,
)


def _sample_score(value: float, truth: str, robust: bool, answer: str) -> SampleScore:
    # Reduced Inspect metrics see the epoch-mean float, not the letter "C".
    return SampleScore(
        score=Score(value=value, answer=answer),
        sample_id="x",
        sample_metadata={"truth": truth, "robust": robust, "strand_id": "b1"},
    )


def test_robust_and_balanced_metrics():
    scores = [
        _sample_score(1.0, "TOWARD", True, "TOWARD"),
        _sample_score(0.0, "AWAY", True, "TOWARD"),
        _sample_score(1.0, "AWAY", False, "AWAY"),
    ]
    assert robust_accuracy()(scores) == 0.5
    # TOWARD is 1/1 and AWAY is 1/2, so the class mean is 0.75.
    assert balanced_metric()(scores) == 0.75
    assert unparsed_rate()(scores) == 0.0


def test_unparsed_rate_counts_answers():
    scores = [
        _sample_score(0.0, "TOWARD", True, "UNPARSED"),
        _sample_score(1.0, "AWAY", True, "AWAY"),
    ]
    assert unparsed_rate()(scores) == 0.5


def test_scorer_records_confidence_without_using_it():
    async def run(completion: str, target: str) -> Score:
        state = TaskState(
            model=ModelName("mockllm/model"),
            sample_id="gfp-12",
            epoch=1,
            input="prompt",
            messages=[],
            target=Target(target),
            output=ModelOutput.from_content("mockllm", completion),
        )
        return await orientation_scorer()(state, Target(target))

    correct = asyncio.run(run('{"label": "TOWARD", "confidence": 0.4}', "TOWARD"))
    assert correct.value == CORRECT
    assert correct.answer == "TOWARD"
    assert correct.metadata["confidence"] is None

    missing = asyncio.run(run('{"label": "AWAY"}', "TOWARD"))
    assert missing.value == INCORRECT
    assert missing.metadata["confidence"] is None
    assert missing.metadata["parse_error"] is None

    interval = asyncio.run(run('{"label": "TOWARD", "confidence": [0.6, 0.9]}', "TOWARD"))
    assert interval.value == CORRECT
    assert interval.metadata["confidence"] is None

    unparsed = asyncio.run(run("neither label", "AWAY"))
    assert unparsed.value == INCORRECT
    assert unparsed.answer == "UNPARSED"


def test_posthoc_mcc_and_calibration():
    assert mcc(["TOWARD", "AWAY"], ["TOWARD", "AWAY"]) == 1.0
    assert mcc(["AWAY", "TOWARD"], ["TOWARD", "AWAY"]) == -1.0
    assert mcc(["AWAY", "AWAY"], ["TOWARD", "AWAY"]) == 0.0
    assert balanced_accuracy(["TOWARD", "TOWARD"], ["TOWARD", "AWAY"]) == 0.5
    # An unparsed prediction is an error, not a true negative.
    assert mcc(["UNPARSED"], ["AWAY"]) == 0.0
    score = brier(["TOWARD"], ["TOWARD"], [1.0])
    assert score == 0.0
    bins = reliability_bins(["TOWARD", "AWAY"], ["TOWARD", "AWAY"], [0.55, 0.95])
    assert len(bins) == 5
    assert bins[0]["n"] == 1
    assert bins[-1]["n"] == 1


def test_alternation_on_a_perfect_strand():
    labels = ["TOWARD", "AWAY", "TOWARD", "AWAY"]
    stats = alternation_coherence(["b1"] * 4, [0, 1, 2, 3], labels)
    assert stats["alternation"] == 1.0
    assert stats["lag1"] < 0
    assert stats["lag2"] > 0
