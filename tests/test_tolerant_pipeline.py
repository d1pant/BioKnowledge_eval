"""Offline agent runs. mockllm calls the orientation tool; nothing is paid."""

import json
import re
import subprocess
import sys
from pathlib import Path

from inspect_ai import eval
from inspect_ai.log import read_eval_log
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.util import Store
from inspect_ai.util._store import init_subtask_store

from bio_eval.tasks.gfp_tolerant_site.dataset import load_brackets, reference_sequence
from bio_eval.tasks.gfp_tolerant_site.prompts import SYSTEM_PROMPT
from bio_eval.tasks.gfp_tolerant_site.task import gfp_tolerant_site
from bio_eval.tasks.gfp_tolerant_site.tools import CALL_LIMIT, LIMIT_ERROR, residue_orientation

_RANGE = re.compile(r"Residues (\d+)-(\d+)")
SEQUENCE = reference_sequence()
BRACKETS = {(item["start"], item["end"]): item for item in load_brackets()}
LEAK = ("cosine", "rsa", "hydrophobic", "dms", "sarkisyan", "inward", "outward")


def _bracket(messages):
    user = next(message.text for message in messages if message.role == "user")
    start, end = (int(value) for value in _RANGE.search(user).groups())
    return BRACKETS[(start, end)]


def _correct_responder(messages, tools, tool_choice, config):
    names = {tool.name for tool in tools}
    assert names == {"residue_orientation"}
    assert "position" in tools[0].parameters.properties
    bracket = _bracket(messages)
    n_tools = sum(message.role == "tool" for message in messages)
    if n_tools < 1:
        return ModelOutput.for_tool_call(
            model="mockllm",
            tool_name="residue_orientation",
            tool_arguments={"position": bracket["start"]},
        )
    start = bracket["starts"][0]
    sequence = SEQUENCE[start - 1 : start + 2]
    return ModelOutput.from_content(
        model="mockllm",
        content=json.dumps({"start": start, "sequence": sequence, "confidence": 0.8}),
    )


def _capped_responder(messages, tools, tool_choice, config):
    n_tools = sum(message.role == "tool" for message in messages)
    if n_tools < CALL_LIMIT + 1:
        return ModelOutput.for_tool_call(
            model="mockllm",
            tool_name="residue_orientation",
            tool_arguments={"position": 12},
        )
    return ModelOutput.from_content(
        model="mockllm",
        content='{"start": 3, "sequence": "KGE", "confidence": 0.8}',
    )


def _metric(log, name: str) -> float:
    for score in log.results.scores:
        if name in score.metrics:
            return score.metrics[name].value
    raise AssertionError(name)


def test_tool_cap_does_not_reveal_a_label():
    init_subtask_store(Store())
    tool = residue_orientation()
    import asyncio

    first = asyncio.run(tool(position=12))
    assert "orientation: TOWARD" in first
    assert "b1" in first
    for word in LEAK:
        assert word not in first.lower()
    loop = asyncio.run(tool(position=1))
    assert loop == "in_strand: false"
    for _ in range(3):
        asyncio.run(tool(position=12))
    refused = asyncio.run(tool(position=12))
    assert refused == LIMIT_ERROR
    assert "TOWARD" not in refused and "AWAY" not in refused


def test_mock_agent_answers_every_bracket(tmp_path):
    logs = eval(
        gfp_tolerant_site(),
        model=get_model("mockllm/model", custom_outputs=_correct_responder),
        display="none",
        max_samples=1,
        log_dir=str(tmp_path / "logs"),
    )
    log = logs[0]
    assert log.status == "success", log.error
    assert _metric(log, "accuracy") == 1.0
    assert _metric(log, "1-50") == 1.0
    assert abs(_metric(log, "lift_1-50") - (1 - 15 / 48)) < 1e-9
    assert abs(_metric(log, "lift_151-200") - (1 - 35 / 48)) < 1e-9
    for sample in log.samples:
        assert sample.messages[0].text == SYSTEM_PROMPT
        tool_msgs = [message for message in sample.messages if message.role == "tool"]
        assert len(tool_msgs) == 1
        text = tool_msgs[0].text.lower()
        for word in LEAK:
            assert word not in text
        assert sample.scores["tolerant_site_scorer"].value == "C"


def test_sixth_call_is_refused_inside_the_agent(tmp_path):
    logs = eval(
        gfp_tolerant_site(),
        model=get_model("mockllm/model", custom_outputs=_capped_responder),
        display="none",
        limit=1,
        max_samples=1,
        log_dir=str(tmp_path / "cap"),
    )
    assert logs[0].status == "success"
    sample = logs[0].samples[0]
    tool_msgs = [message.text for message in sample.messages if message.role == "tool"]
    assert len(tool_msgs) == CALL_LIMIT + 1
    assert "orientation:" in tool_msgs[0]
    assert tool_msgs[-1] == LIMIT_ERROR
    assert "TOWARD" not in tool_msgs[-1] and "AWAY" not in tool_msgs[-1]


def test_cli_mockllm(tmp_path):
    inspect = Path(sys.executable).parent / "inspect"
    log_dir = tmp_path / "cli"
    completed = subprocess.run(
        [
            str(inspect),
            "eval",
            "src/bio_eval/tasks/gfp_tolerant_site/task.py@gfp_tolerant_site",
            "--model",
            "mockllm/model",
            "--limit",
            "5",
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
    assert read_eval_log(logs[0], header_only=True).status == "success"
