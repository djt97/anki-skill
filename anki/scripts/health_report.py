#!/usr/bin/env python3
"""Generate a read-only Anki collection snapshot and exact trouble scores."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from typing import Any

from anki_client import (
    AnkiConnectError,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_URL,
    call,
    cards_info,
    even_sample,
    notes_info,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def display_text(value: str) -> str:
    """Create a display-only plain-text copy; never write it back to Anki."""
    parser = _TextExtractor()
    try:
        parser.feed(value)
        parser.close()
        text = " ".join(parser.parts)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\[sound:[^\]]+\]", " [sound] ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def score_card(card: dict[str, Any], *, now: float | None = None) -> dict[str, Any] | None:
    """Apply the skill's unchanged trouble, weakness, and confidence formulas."""
    reps = int(card.get("reps", 0) or 0)
    if reps <= 0:
        return None

    current_time = time.time() if now is None else now
    lapses = int(card.get("lapses", 0) or 0)
    interval = int(card.get("interval", 0) or 0)
    factor = int(card.get("factor", 0) or 0)
    note_id = int(card["note"])
    age_days = max((current_time - note_id / 1000.0) / 86400.0, 1.0)

    lapse_rate = min(lapses / max(reps, 1), 1.0)
    ease_erosion = (
        max(0.0, min(1.0, 1.0 - factor / 2500.0)) if factor > 0 else 0.5
    )
    mature_failure = interval > 21 and lapse_rate > 0.15
    time_ratio = 0.0

    trouble = (
        0.35 * lapse_rate
        + 0.25 * ease_erosion
        + 0.20 * time_ratio
        + 0.20 * (1.0 if mature_failure else 0.0)
    )
    weakness = lapses / age_days
    confidence = (
        0.35 * min(reps / 25.0, 1.0)
        + 0.35 * min(interval / 90.0, 1.0)
        + 0.20 * (1.0 - lapse_rate)
        + 0.10 * min(factor / 2600.0, 1.0)
    )

    return {
        "card": int(card["cardId"]),
        "note": note_id,
        "trouble": round(trouble, 4),
        "weakness_lapses_per_day": round(weakness, 4),
        "confidence": round(confidence, 4),
        "reps": reps,
        "lapses": lapses,
        "lapse_rate": round(lapse_rate, 4),
        "interval_days": interval,
        "factor": factor,
        "ease_erosion": round(ease_erosion, 4),
        "mature_failure": mature_failure,
        "time_ratio": time_ratio,
    }


def _truncate(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit].rstrip() + "…", True


def summarize_card(
    card: dict[str, Any],
    *,
    tags_by_note: dict[int, list[str]],
    siblings_by_note: dict[int, list[int]],
    max_field_chars: int,
    score: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fields: dict[str, str] = {}
    truncated_fields: list[str] = []
    for name, field in card.get("fields", {}).items():
        text = display_text(str(field.get("value", "")))
        shown, truncated = _truncate(text, max_field_chars)
        fields[name] = shown
        if truncated:
            truncated_fields.append(name)

    output: dict[str, Any] = {
        "card": int(card["cardId"]),
        "note": int(card["note"]),
        "deck": card.get("deckName"),
        "model": card.get("modelName"),
        "display_fields": fields,
        "truncated_fields": truncated_fields,
        "tags": tags_by_note.get(int(card["note"]), []),
        "sibling_cards": siblings_by_note.get(int(card["note"]), []),
        "reps": int(card.get("reps", 0) or 0),
        "lapses": int(card.get("lapses", 0) or 0),
        "interval_days": int(card.get("interval", 0) or 0),
        "factor": int(card.get("factor", 0) or 0),
    }
    if score is not None:
        output["diagnostics"] = score
    return output


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    version = call("version", url=args.url, timeout=args.timeout)
    card_ids = call("findCards", {"query": args.query}, url=args.url, timeout=args.timeout)
    cards = cards_info(card_ids, url=args.url, timeout=args.timeout)
    card_by_id = {int(card["cardId"]): card for card in cards}

    now = time.time()
    scores = [score for card in cards if (score := score_card(card, now=now)) is not None]
    scores.sort(key=lambda row: (row["trouble"], row["weakness_lapses_per_day"]), reverse=True)
    score_by_card = {int(row["card"]): row for row in scores}

    sample_ids = even_sample(card_ids, args.sample)
    sample_cards = [card_by_id[cid] for cid in sample_ids if cid in card_by_id]
    worst_scores = scores[: args.worst]
    worst_cards = [card_by_id[row["card"]] for row in worst_scores if row["card"] in card_by_id]

    note_ids = sorted(
        {
            int(card["note"])
            for card in [*sample_cards, *worst_cards]
            if card.get("note") is not None
        }
    )
    note_rows = notes_info(note_ids, url=args.url, timeout=args.timeout)
    tags_by_note = {int(note["noteId"]): list(note.get("tags", [])) for note in note_rows}
    siblings_by_note = {
        int(note["noteId"]): [int(card_id) for card_id in note.get("cards", [])]
        for note in note_rows
    }

    costly_count = (
        max(1, math.ceil(len(scores) * args.costly_percentile / 100.0)) if scores else 0
    )
    costly_threshold = scores[costly_count - 1]["trouble"] if costly_count else None

    representative_sample = [
        summarize_card(
            card,
            tags_by_note=tags_by_note,
            siblings_by_note=siblings_by_note,
            max_field_chars=args.max_field_chars,
            score=score_by_card.get(int(card["cardId"])),
        )
        for card in sample_cards
    ]
    worst = [
        summarize_card(
            card,
            tags_by_note=tags_by_note,
            siblings_by_note=siblings_by_note,
            max_field_chars=args.max_field_chars,
            score=score_by_card.get(int(card["cardId"])),
        )
        for card in worst_cards
    ]

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "anki_connect_api_version": version,
        "query": args.query,
        "total_matching_cards": len(card_ids),
        "reviewed_matching_cards": len(scores),
        "representative_sample_size": len(representative_sample),
        "representative_sample": representative_sample,
        "worst_cards": worst,
        "costly_definition": {
            "worst_percent": args.costly_percentile,
            "reviewed_card_count": costly_count,
            "trouble_threshold": costly_threshold,
        },
        "score_parameters": {
            "trouble": (
                "0.35*lapse_rate + 0.25*ease_erosion + 0.20*time_ratio "
                "+ 0.20*mature_failure"
            ),
            "time_ratio_used": 0.0,
            "mature_failure": "interval_days > 21 and lapse_rate > 0.15",
            "fsrs_factor_fallback": 0.5,
            "weakness": "lapses / max(days_since_note_id_timestamp, 1)",
            "confidence": (
                "0.35*min(reps/25,1) + 0.35*min(interval/90,1) "
                "+ 0.20*(1-lapse_rate) + 0.10*min(factor/2600,1)"
            ),
        },
        "display_warning": (
            "display_fields are read-only plain-text previews and may be truncated. "
            "Re-fetch full raw fields before proposing or applying any edit."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="deck:*", help="Anki search query")
    parser.add_argument("--sample", type=int, default=400)
    parser.add_argument("--worst", type=int, default=25)
    parser.add_argument("--costly-percentile", type=float, default=5.0)
    parser.add_argument("--max-field-chars", type=int, default=500)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    if args.sample <= 0 or args.worst <= 0 or args.max_field_chars <= 0:
        parser.error("sample, worst, and max-field-chars must be positive")
    if not 0 < args.costly_percentile <= 100:
        parser.error("costly-percentile must be greater than 0 and at most 100")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_report(args)
    except (AnkiConnectError, KeyError, TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.compact:
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
