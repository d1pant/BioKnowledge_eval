"""Triplet parser. Confidence is one number and does not change the start."""

from bio_eval.tasks.gfp_tolerant_site.parsing import parse_response


def test_clean_json():
    parsed = parse_response('{"start": 3, "sequence": "kge", "confidence": 0.8}')
    assert parsed.start == 3
    assert parsed.sequence == "KGE"
    assert parsed.confidence == 0.8
    assert parsed.error is None


def test_fenced_and_missing_confidence():
    parsed = parse_response('```json\n{"start": 73, "sequence": "RYP"}\n```')
    assert parsed.start == 73
    assert parsed.sequence == "RYP"
    assert parsed.confidence is None
    assert parsed.error is None


def test_confidence_interval_and_out_of_range():
    interval = parse_response(
        '{"start": 101, "sequence": "KDD", "confidence": [0.6, 0.9]}'
    )
    low = parse_response('{"start": 101, "sequence": "KDD", "confidence": 0.2}')
    assert interval.start == 101 and interval.confidence is None
    assert low.confidence is None
    assert interval.error is None


def test_bad_sequence_and_unparsed():
    bad = parse_response('{"start": 3, "sequence": "KG"}')
    assert bad.start == 3 and bad.sequence is None and bad.error == "bad_sequence"
    empty = parse_response("")
    assert empty.error == "empty"
    prose = parse_response("I choose residues 3-5.")
    assert prose.error == "unparsed"
