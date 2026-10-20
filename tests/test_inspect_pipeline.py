"""Offline mockllm runs. No API keys and no provider calls."""

import json
import re
import subprocess
import sys
from pathlib import Path

from inspect_ai import Epochs, eval
from inspect_ai.log import read_eval_log
from inspect_ai.model import ModelOutput, get_model

from bio_eval.tasks.gfp_barrel.dataset import load_rows
from bio_eval.tasks.gfp_barrel.prompts import SYSTEM_PROMPT
from bio_eval.tasks.gfp_barrel.task import gfp_barrel_orientation

ROWS = {row["author_resnum"]: row for row in load_rows()}
_RESIDUE = re.compile(r"Residue: [A-Z]{3} (\d+)")


def _resnum(messages) -> int:
    user = next(message.text for message in messages if message.role == "user")
    return int(_RESIDUE.search(user).group(1))


def _output(label: str, confidence: float) -> ModelOutput:
    return ModelOutput.from_content(
        model="mockllm",
        content=json.dumps({"label": label, "confidence": confidence}),
    )


def _responder(mode: str, calls: dict[int, int] | None = None):
    def responder(messages, tools, tool_choice, config):
        resnum = _resnum(messages)
        truth = ROWS[resnum]["truth"]
        other = "AWAY" if truth == "TOWARD" else "TOWARD"
        if mode == "perfect":
            return _output(truth, 0.9)
        if mode == "inverted":
            return _output(other, 0.9)
        if mode == "toward":
            return _output("TOWARD", 0.9)
        if mode == "malformed":
            return ModelOutput.from_content(model="mockllm", content="not json")
        assert calls is not None
        calls[resnum] = calls.get(resnum, 0) + 1
        if calls[resnum] == 1:
            return _output(truth, 0.6)
        return _output(other, 0.7)

    return responder


def _run(responder, tmp_path: Path, name: str, epochs: int = 1):
    logs = eval(
        gfp_barrel_orientation(),
        model=get_model("mockllm/model", custom_outputs=responder),
        display="none",
        epochs=Epochs(epochs, "mean") if epochs > 1 else None,
        max_samples=1,
        log_dir=str(tmp_path / name),
    )
    assert len(logs) == 1
    assert logs[0].status == "success", logs[0].error
    return logs[0]


def _metric(log, name: str) -> float:
    found = []
    for score in log.results.scores:
        if name in score.metrics:
            found.append(score.metrics[name].value)
    assert found, name
    return found[0]


def test_scripted_accuracy(tmp_path):
    perfect = _run(_responder("perfect"), tmp_path, "perfect")
    assert _metric(perfect, "accuracy") == 1.0
    assert _metric(perfect, "robust_accuracy") == 1.0
    assert _metric(perfect, "unparsed_rate") == 0.0
    assert "stderr" in perfect.results.scores[0].metrics
    assert "b1" in {key for score in perfect.results.scores for key in score.metrics}

    inverted = _run(_responder("inverted"), tmp_path, "inverted")
    assert _metric(inverted, "accuracy") == 0.0
    assert _metric(inverted, "robust_accuracy") == 0.0

    constant = _run(_responder("toward"), tmp_path, "toward")
    assert _metric(constant, "robust_accuracy") == 50 / 98
    assert _metric(constant, "balanced_accuracy") == 0.5

    malformed = _run(_responder("malformed"), tmp_path, "malformed")
    assert _metric(malformed, "accuracy") == 0.0
    assert _metric(malformed, "robust_accuracy") == 0.0
    assert _metric(malformed, "unparsed_rate") == 1.0
    assert all(
        sample.scores["orientation_scorer"].answer == "UNPARSED"
        for sample in malformed.samples
    )


def test_epochs_keep_both_answers(tmp_path):
    calls: dict[int, int] = {}
    log = _run(_responder("epochs", calls), tmp_path, "epochs", epochs=2)
    assert _metric(log, "accuracy") == 0.5
    by_id: dict[str, dict[int, object]] = {}
    for sample in log.samples:
        by_id.setdefault(sample.id, {})[sample.epoch] = sample
        assert [message.role for message in sample.messages] == [
            "system",
            "user",
            "assistant",
        ]
        assert sample.messages[0].text == SYSTEM_PROMPT
    first = by_id["gfp-148"][1].scores["orientation_scorer"]
    second = by_id["gfp-148"][2].scores["orientation_scorer"]
    assert first.metadata["confidence"] == 0.6
    assert second.metadata["confidence"] == 0.7
    assert first.answer != second.answer
    assert first.answer == ROWS[148]["truth"]


def test_cli_mockllm_limit(tmp_path):
    inspect = Path(sys.executable).parent / "inspect"
    log_dir = tmp_path / "cli"
    completed = subprocess.run(
        [
            str(inspect),
            "eval",
            "src/bio_eval/tasks/gfp_barrel/task.py@gfp_barrel_orientation",
            "--model",
            "mockllm/model",
            "--limit",
            "3",
            "--log-dir",
            str(log_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    logs = list(log_dir.glob("*.eval"))
    assert len(logs) == 1
    header = read_eval_log(logs[0], header_only=True)
    assert header.status == "success"
