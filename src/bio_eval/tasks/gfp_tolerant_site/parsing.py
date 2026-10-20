"""Parse a triplet answer. A bad confidence does not change the start."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

_NUMBER = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_LETTERS = re.compile(r"[A-Za-z]{3}")


@dataclass
class ParsedTriplet:
    start: int | None
    sequence: str | None
    confidence: float | None
    error: str | None


def _first_object(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    decoder = json.JSONDecoder()
    while start != -1:
        try:
            obj, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            continue
        if isinstance(obj, dict):
            return obj
        start = text.find("{", start + 1)
    return None


def _one_number(value: Any) -> float | None:
    if isinstance(value, bool) or isinstance(value, (list, tuple, dict)):
        return None
    if isinstance(value, str):
        text = value.strip()
        if _NUMBER.fullmatch(text) is None:
            return None
        value = float(text)
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    if 0.5 <= number <= 1.0:
        return number
    return None


def _start(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _sequence(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if _LETTERS.fullmatch(text) is None:
        return None
    return text.upper()


def parse_response(text: str | None) -> ParsedTriplet:
    if text is None or not str(text).strip():
        return ParsedTriplet(None, None, None, "empty")
    obj = _first_object(str(text))
    if obj is None:
        return ParsedTriplet(None, None, None, "unparsed")
    start = _start(obj.get("start"))
    sequence = _sequence(obj.get("sequence"))
    confidence = _one_number(obj["confidence"]) if "confidence" in obj else None
    if start is None:
        return ParsedTriplet(None, sequence, confidence, "bad_start")
    if sequence is None:
        return ParsedTriplet(start, None, confidence, "bad_sequence")
    return ParsedTriplet(start, sequence, confidence, None)
