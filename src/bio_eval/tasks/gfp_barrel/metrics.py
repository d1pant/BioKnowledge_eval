"""Post-hoc metrics over plain lists. Not used by the Inspect scorer.

Predicted labels are ``TOWARD``, ``AWAY``, or anything else (treated as
unparsed). An unparsed prediction is an error: it counts as the wrong class
in MCC and is left out of alternation and calibration.
"""

from __future__ import annotations

import math
from collections import defaultdict

_PARSED = {"TOWARD", "AWAY"}


def accuracy(pred: list[str], truth: list[str]) -> float:
    if not truth:
        return float("nan")
    return sum(p == t for p, t in zip(pred, truth)) / len(truth)


def balanced_accuracy(pred: list[str], truth: list[str]) -> float:
    classes = sorted(set(truth))
    if len(classes) < 2:
        return float("nan")
    recalls = []
    for label in classes:
        index = [i for i, value in enumerate(truth) if value == label]
        recalls.append(sum(pred[i] == label for i in index) / len(index))
    return sum(recalls) / len(recalls)


def mcc(pred: list[str], truth: list[str], positive: str = "TOWARD") -> float:
    """Matthews correlation. Unparsed predictions count as the wrong class."""
    tp = tn = fp = fn = 0
    for true, predicted in zip(truth, pred):
        hit = predicted == true and predicted in _PARSED
        if hit and true == positive:
            tp += 1
        elif hit:
            tn += 1
        elif true == positive:
            fn += 1
        else:
            fp += 1
    denom = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    if denom == 0:
        return 0.0
    return (tp * tn - fp * fn) / math.sqrt(denom)


def per_strand_accuracy(
    strand_ids: list[str], pred: list[str], truth: list[str]
) -> dict[str, float]:
    grouped: dict[str, list[bool]] = defaultdict(list)
    for strand_id, predicted, true in zip(strand_ids, pred, truth):
        grouped[strand_id].append(predicted == true)
    return {
        strand_id: sum(hits) / len(hits) for strand_id, hits in sorted(grouped.items())
    }


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return float("nan")
    return num / (den_x * den_y)


def alternation_coherence(
    strand_ids: list[str], indices: list[int], labels: list[str]
) -> dict[str, float]:
    """Within-strand alternation of a ±1 label vector.

    ``alternation`` is the fraction of consecutive parsed pairs that differ.
    ``lag1`` and ``lag2`` are Pearson correlations of that vector.
    """
    by_strand: dict[str, dict[int, str]] = defaultdict(dict)
    for strand_id, index, label in zip(strand_ids, indices, labels):
        by_strand[strand_id][index] = label
    sign = {"TOWARD": 1.0, "AWAY": -1.0}
    differ = 0
    pairs = 0
    lags: dict[int, tuple[list[float], list[float]]] = {
        1: ([], []),
        2: ([], []),
    }
    for positions in by_strand.values():
        for index, label in positions.items():
            nxt = positions.get(index + 1)
            if label in sign and nxt in sign:
                pairs += 1
                differ += label != nxt
            for lag, (xs, ys) in lags.items():
                other = positions.get(index + lag)
                if label in sign and other in sign:
                    xs.append(sign[label])
                    ys.append(sign[other])
    return {
        "alternation": differ / pairs if pairs else float("nan"),
        "lag1": _pearson(*lags[1]),
        "lag2": _pearson(*lags[2]),
    }


def brier(
    truth: list[str], pred: list[str], confidence: list[float | None]
) -> float:
    """Mean squared error of the probability assigned to the true label.

    ``confidence`` is the model's probability that its own label is correct.
    Samples with a missing confidence or an unparsed label are left out.
    """
    terms: list[float] = []
    for true, predicted, conf in zip(truth, pred, confidence):
        if conf is None or predicted not in _PARSED:
            continue
        p_true = conf if predicted == true else 1.0 - conf
        terms.append((p_true - 1.0) ** 2)
    if not terms:
        return float("nan")
    return sum(terms) / len(terms)


def reliability_bins(
    truth: list[str],
    pred: list[str],
    confidence: list[float | None],
    n_bins: int = 5,
) -> list[dict]:
    """Five bins over confidence 0.5–1.0. Each bin records n, mean confidence, accuracy."""
    width = 0.5 / n_bins
    bins: list[dict] = []
    for i in range(n_bins):
        lo = 0.5 + i * width
        hi = 0.5 + (i + 1) * width
        chosen = []
        for true, predicted, conf in zip(truth, pred, confidence):
            if conf is None or predicted not in _PARSED:
                continue
            in_bin = lo <= conf < hi if i < n_bins - 1 else lo <= conf <= hi
            if in_bin:
                chosen.append((conf, predicted == true))
        bins.append(
            {
                "lo": lo,
                "hi": hi,
                "n": len(chosen),
                "mean_confidence": (
                    sum(c for c, _ in chosen) / len(chosen) if chosen else float("nan")
                ),
                "accuracy": (
                    sum(hit for _, hit in chosen) / len(chosen) if chosen else float("nan")
                ),
            }
        )
    return bins
