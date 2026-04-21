# DMiME 保守用ツール
# Copyright (C) 2026 colloid
# Licensed under GPL-2.0-only

"""Bucket resolver: maps a yomi's leading character to one of 16 bucket names.

Buckets preserve 五十音 row structure while keeping 濁音/半濁音 independent so
each source file stays well under GitHub's 1MB preview threshold.
"""

from __future__ import annotations

BUCKET_ORDER: tuple[str, ...] = (
    "a", "ka", "ga", "sa", "za", "ta", "da", "na",
    "ha", "ba", "pa", "ma", "ya", "ra", "wa", "_ascii",
)

_BUCKETS: dict[str, str] = {}

def _register(bucket: str, chars: str) -> None:
    for ch in chars:
        _BUCKETS[ch] = bucket

_register("a",  "あいうえおぁぃぅぇぉゔ")
_register("ka", "かきくけこ")
_register("ga", "がぎぐげご")
_register("sa", "さしすせそ")
_register("za", "ざじずぜぞ")
_register("ta", "たちつてとっ")
_register("da", "だぢづでど")
_register("na", "なにぬねの")
_register("ha", "はひふへほ")
_register("ba", "ばびぶべぼ")
_register("pa", "ぱぴぷぺぽ")
_register("ma", "まみむめも")
_register("ya", "やゆよゃゅょ")
_register("ra", "らりるれろ")
_register("wa", "わゐゑをんゎ")


def bucket_for(yomi: str) -> str:
    if not yomi:
        return "_ascii"
    return _BUCKETS.get(yomi[0], "_ascii")
