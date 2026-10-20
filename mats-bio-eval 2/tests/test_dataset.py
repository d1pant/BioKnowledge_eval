"""Dataset size, robust split, and prompt-leakage checks."""

import re

from bio_eval.tasks.gfp_barrel.dataset import ROBUST_COS_THRESHOLD, build_dataset, load_rows
from bio_eval.tasks.gfp_barrel.prompts import SYSTEM_PROMPT, render_user_prompt

FORBIDDEN = (
    "inward",
    "outward",
    "alternat",
    "1EMA",
    "1GFL",
    "S65T",
    "UniProt",
    "P42212",
    "PDB",
    "65-67",
    "65–67",
)


def test_system_prompt_has_no_braces():
    assert "{" not in SYSTEM_PROMPT and "}" not in SYSTEM_PROMPT


def test_size_balance_and_ids():
    rows = load_rows()
    samples = list(build_dataset("all"))
    assert len(samples) == 107
    assert sum(row["truth"] == "TOWARD" for row in rows) == 53
    assert sum(row["truth"] == "AWAY" for row in rows) == 54
    assert sum(row["robust"] for row in rows) == 98
    assert len({sample.id for sample in samples}) == 107
    robust = [row for row in rows if row["robust"]]
    assert sum(row["truth"] == "TOWARD" for row in robust) == 50
    assert sum(row["truth"] == "AWAY" for row in robust) == 48
    assert all(sample.metadata["strand_id"] for sample in samples)
    assert all(sample.metadata["truth"] == sample.target for sample in samples)


def test_robust_subset_and_threshold():
    assert ROBUST_COS_THRESHOLD == 0.2
    subset = list(build_dataset("robust"))
    assert len(subset) == 98
    assert all(sample.metadata["robust"] for sample in subset)
    assert all(abs(sample.metadata["chromophore_cosine"]) >= 0.2 for sample in subset)


def test_strand_context_matches_csv_and_example_shape():
    rows = load_rows()
    his = next(row for row in rows if row["author_resnum"] == 148)
    assert his["aa"] == "H"
    assert his["strand_id"] == "b7"
    assert his["strand_context"] == "[H]NVYI"
    prompt = render_user_prompt(his)
    assert "Residue: HIS 148 (H)" in prompt
    assert "Beta-strand: b7 (of b1-b11), residues 148-152" in prompt
    assert "[H]NVYI" in prompt


def test_prompts_do_not_leak_labels_or_sources():
    rows = load_rows()
    for row in rows:
        text = render_user_prompt(row)
        lowered = text.lower()
        for word in FORBIDDEN:
            assert word.lower() not in lowered, word
        assert text.count("TOWARD") == 3
        assert text.count("AWAY") == 3
        assert "confidence" in text
        assert "interval" not in lowered
        assert re.search(r"\{\s*[a-z_]+\s*\}", text) is None
