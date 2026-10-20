"""Five brackets, F64L only at position 64, and no source names in the prompt."""

from bio_eval.tasks.gfp_tolerant_site.dataset import build_dataset, load_brackets
from bio_eval.tasks.gfp_tolerant_site.prompts import SYSTEM_PROMPT

FORBIDDEN = ("sarkisyan", "1ema", "1gfl", "uniprot", "p42212", "f64l", "pdb", "65-67", "65–67")


def test_five_brackets_and_chances():
    brackets = load_brackets()
    assert [item["bracket_id"] for item in brackets] == [
        "1-50", "51-100", "101-150", "151-200", "200-238",
    ]
    assert [len(item["starts"]) for item in brackets] == [15, 7, 22, 35, 20]
    assert [item["possible"] for item in brackets] == [48, 48, 48, 48, 37]
    chances = [item["chance"] for item in brackets]
    assert chances[0] == 15 / 48
    assert chances[3] == 35 / 48
    assert chances[4] == 20 / 37
    assert abs(sum(chances) / 5 - 0.437) < 0.001
    samples = list(build_dataset())
    assert len(samples) == 5
    assert len({sample.id for sample in samples}) == 5


def test_bracket_b_uses_leucine_64_and_prompts_stay_blind():
    assert "{" not in SYSTEM_PROMPT and "}" not in SYSTEM_PROMPT
    brackets = {item["bracket_id"]: item for item in load_brackets()}
    middle = brackets["51-100"]["sequence"]
    assert middle[64 - 51] == "L"
    assert "interval" not in SYSTEM_PROMPT.lower()
    for sample in build_dataset():
        text = sample.input
        lowered = text.lower()
        for word in FORBIDDEN:
            assert word not in lowered
        assert "residue_orientation(position)" in text
        assert text.count("{") == 1
        assert "confidence" in text
        assert sample.metadata["reference_sequence"] in text
