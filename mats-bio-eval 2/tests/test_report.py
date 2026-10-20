"""Baselines, log extraction, and the results-poster overwrite guard."""

import json
from pathlib import Path

from inspect_ai import Epochs, eval
from inspect_ai.model import ModelOutput, get_model

from analysis.extract_predictions import extract
from analysis.render_results_poster import render, strand_order
from analysis.report import hydrophobicity_baselines, render_summary
from bio_eval.tasks.gfp_barrel.task import gfp_barrel_orientation


def test_hydrophobicity_baselines_match_the_plan():
    base = hydrophobicity_baselines()
    robust = base["robust"]["hydrophobicity"]
    assert round(robust["accuracy"], 3) == 0.684
    assert round(robust["balanced_accuracy"], 3) == 0.686
    assert round(robust["mcc"], 3) == 0.380
    assert round(base["all"]["hydrophobicity"]["accuracy"], 3) == 0.682
    assert round(base["robust"]["always_away"]["accuracy"], 3) == 0.490
    assert round(base["all"]["random_seed0"]["accuracy"], 3) == 0.523
    text = render_summary()
    assert "0.684" in text
    assert "0.682" in text


def test_strand_order_is_the_measured_cycle():
    assert strand_order() == [
        "b4", "b5", "b6", "b1", "b2", "b3", "b11", "b10", "b7", "b8", "b9",
    ]


def test_extract_keeps_both_epochs(tmp_path):
    calls: dict[int, int] = {}

    def responder(messages, tools, tool_choice, config):
        user = next(message.text for message in messages if message.role == "user")
        resnum = int(user.split("Residue: ")[1].split()[1])
        calls[resnum] = calls.get(resnum, 0) + 1
        label = "TOWARD" if calls[resnum] == 1 else "AWAY"
        confidence = 0.6 if calls[resnum] == 1 else 0.7
        return ModelOutput.from_content(
            model="mockllm",
            content=json.dumps({"label": label, "confidence": confidence}),
        )

    logs = eval(
        gfp_barrel_orientation(),
        model=get_model("mockllm/model", custom_outputs=responder),
        display="none",
        limit=2,
        epochs=Epochs(2, "mean"),
        max_samples=1,
        log_dir=str(tmp_path / "logs"),
    )
    assert logs[0].status == "success"
    rows = extract([logs[0].location], out_dir=tmp_path / "predictions")
    assert len(rows) == 4
    by_epoch = {}
    for row in rows:
        by_epoch.setdefault(int(row["author_resnum"]), {})[int(row["epoch"])] = row
    for resnum, epochs in by_epoch.items():
        assert epochs[1]["label"] == "TOWARD"
        assert epochs[2]["label"] == "AWAY"
        assert float(epochs[1]["confidence"]) == 0.6
        assert float(epochs[2]["confidence"]) == 0.7
        assert epochs[1]["model"] == "mockllm/model"
    written = list((tmp_path / "predictions").glob("*.csv"))
    assert len(written) == 1


def test_poster_refuses_to_overwrite(tmp_path):
    out = tmp_path / "gfp-orientation-results-v1.png"
    render([], out)
    assert out.stat().st_size > 0
    try:
        render([], out)
    except FileExistsError:
        return
    raise AssertionError("second render overwrote the poster")


def test_extract_ignores_agent_logs(tmp_path):
    """The first provider run crashed analysis.report: extract() emitted rows for
    gfp_tolerant_site samples, which carry no author_resnum, and render_summary
    then called int('') on them."""
    from inspect_ai.model import ModelOutput as _Output

    from bio_eval.tasks.gfp_tolerant_site.task import gfp_tolerant_site

    def responder(messages, tools, tool_choice, config):
        return _Output.from_content(
            model="mockllm",
            content=json.dumps({"start": 3, "sequence": "KGE", "confidence": 0.6}),
        )

    logs = eval(
        gfp_tolerant_site(),
        model=get_model("mockllm/model", custom_outputs=responder),
        display="none",
        limit=1,
        max_samples=1,
        log_dir=str(tmp_path / "logs"),
    )
    assert logs[0].status == "success", logs[0].error
    rows = extract([logs[0].location], out_dir=tmp_path / "predictions")
    assert rows == []
    assert list((tmp_path / "predictions").glob("*.csv")) == []


def test_summary_tolerates_rows_without_a_residue():
    text = render_summary([{"model": "m", "author_resnum": "", "epoch": "1", "label": "TOWARD"}])
    assert "Model tables are empty." in text


def test_summary_separates_two_runs_of_one_model():
    """Two budgets of one model must not be averaged into a single row."""
    rows = []
    for run_id, max_tokens, label in (("a", "256", "TOWARD"), ("b", "2048", "AWAY")):
        rows.append(
            {
                "model": "together/x",
                "max_tokens": max_tokens,
                "run_id": run_id,
                "author_resnum": "12",
                "strand_id": "b1",
                "epoch": "1",
                "label": label,
                "confidence": "",
            }
        )
    text = render_summary(rows)
    body = [line for line in text.splitlines() if line.startswith("| together/x |")]
    assert len(body) == 2
    assert any("| 256 |" in line for line in body)
    assert any("| 2048 |" in line for line in body)
