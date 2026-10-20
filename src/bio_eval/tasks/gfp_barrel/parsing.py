"""Parse a TOWARD/AWAY completion. Confidence never changes the label."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

LABELS = ("TOWARD", "AWAY")
_NUMBER = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


@dataclass
class ParsedAnswer:
    label: Literal["TOWARD", "AWAY"] | None
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
    """Accept a single probability in [0.5, 1.0]. Intervals are invalid."""
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


def _bare_label(text: str) -> Literal["TOWARD", "AWAY"] | None:
    found = [lab for lab in LABELS if re.search(rf"\b{lab}\b", text, re.IGNORECASE)]
    if len(found) == 1:
        return found[0]
    return None


def parse_response(text: str | None) -> ParsedAnswer:
    """First JSON object wins. A bare TOWARD/AWAY token is the fallback.

    A missing, out-of-range, or interval confidence leaves ``confidence``
    as None and does not change ``label``.
    """
    if text is None or not str(text).strip():
        return ParsedAnswer(None, None, "empty")
    text = str(text)
    obj = _first_object(text)
    if obj is not None and "label" in obj:
        raw = obj.get("label")
        label: Literal["TOWARD", "AWAY"] | None
        if isinstance(raw, str) and raw.strip().upper() in LABELS:
            label = raw.strip().upper()  # type: ignore[assignment]
            error = None
        else:
            label = _bare_label(text)
            error = None if label else "bad_label"
        confidence = _one_number(obj["confidence"]) if "confidence" in obj else None
        return ParsedAnswer(label, confidence, error)
    label = _bare_label(text)
    if label:
        return ParsedAnswer(label, None, None)
    return ParsedAnswer(None, None, "unparsed")
