"""Parser cases from the validation plan. Confidence never flips the label."""

from bio_eval.tasks.gfp_barrel.parsing import parse_response


def test_clean_json():
    parsed = parse_response('{"label": "TOWARD", "confidence": 0.8}')
    assert parsed.label == "TOWARD"
    assert parsed.confidence == 0.8
    assert parsed.error is None


def test_fenced_lowercase():
    text = '```json\n{"label": "away", "confidence": 1}\n```'
    parsed = parse_response(text)
    assert parsed.label == "AWAY"
    assert parsed.confidence == 1.0


def test_confidence_out_of_range_keeps_label():
    parsed = parse_response('{"label": "TOWARD", "confidence": 0.2}')
    assert parsed.label == "TOWARD"
    assert parsed.confidence is None


def test_confidence_interval_is_not_a_number():
    parsed = parse_response('{"label": "AWAY", "confidence": [0.6, 0.9]}')
    assert parsed.label == "AWAY"
    assert parsed.confidence is None


def test_missing_confidence():
    parsed = parse_response('{"label": "TOWARD"}')
    assert parsed.label == "TOWARD"
    assert parsed.confidence is None
    assert parsed.error is None


def test_edges_of_confidence_scale():
    low = parse_response('{"label": "TOWARD", "confidence": 0.5}')
    high = parse_response('{"label": "AWAY", "confidence": 1.0}')
    assert low.confidence == 0.5
    assert high.confidence == 1.0


def test_extra_prose():
    parsed = parse_response('I think so. {"label": "TOWARD", "confidence": 0.7} thanks')
    assert parsed.label == "TOWARD"
    assert parsed.confidence == 0.7


def test_bare_token_when_exactly_one_label():
    parsed = parse_response("The side chain points AWAY.")
    assert parsed.label == "AWAY"
    assert parsed.confidence is None


def test_both_labels_without_json_is_unparsed():
    parsed = parse_response("It could be TOWARD or AWAY.")
    assert parsed.label is None
    assert parsed.error == "unparsed"


def test_empty_and_non_json():
    assert parse_response("").label is None
    assert parse_response("   ").error == "empty"
    assert parse_response("hello").label is None
    assert parse_response("hello").error == "unparsed"
