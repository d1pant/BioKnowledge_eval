"""Scorer rules on synthetic completions. No model calls."""

import asyncio

from inspect_ai.model import ModelName, ModelOutput
from inspect_ai.scorer import CORRECT, INCORRECT, Target
from inspect_ai.solver import TaskState

from bio_eval.tasks.gfp_tolerant_site.dataset import load_brackets
from bio_eval.tasks.gfp_tolerant_site.scorer import tolerant_site_scorer


def _state(bracket: dict, completion: str) -> TaskState:
    return TaskState(
        model=ModelName("mockllm/model"),
        sample_id=f"gfp-{bracket['bracket_id']}",
        epoch=1,
        input="prompt",
        messages=[],
        target=Target(bracket["bracket_id"]),
        metadata={
            "bracket_id": bracket["bracket_id"],
            "chance": bracket["chance"],
            "accepted_starts": bracket["starts"],
            "reference_sequence": bracket["sequence"],
        },
        output=ModelOutput.from_content("mockllm", completion),
    )


def _score(bracket: dict, completion: str):
    return asyncio.run(
        tolerant_site_scorer()(_state(bracket, completion), Target(bracket["bracket_id"]))
    )


def test_accepted_start_right_and_wrong_letters():
    bracket = load_brackets()[0]
    correct = _score(bracket, '{"start": 3, "sequence": "KGE", "confidence": 0.9}')
    assert correct.value == CORRECT
    assert correct.metadata["sequence_mismatch"] is False

    wrong = _score(bracket, '{"start": 3, "sequence": "AAA", "confidence": [0.5, 1]}')
    assert wrong.value == INCORRECT
    assert wrong.metadata["sequence_mismatch"] is True
    assert wrong.metadata["confidence"] is None

    outside = _score(bracket, '{"start": 73, "sequence": "RYP"}')
    assert outside.value == INCORRECT
    assert outside.metadata["sequence_mismatch"] is False

    unparsed = _score(bracket, "no json here")
    assert unparsed.value == INCORRECT
    assert unparsed.metadata["parse_error"] == "unparsed"
