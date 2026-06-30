#!/usr/bin/env python3
"""Generate a read-only Anki collection snapshot and exact cost scores."""

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


MIN_REPS = 5  # need enough review history for a stable failure rate


def score_card(card: dict[str, Any], *, now: float | None = None) -> dict[str, Any] | None:
    """Rank cards by the review cost their *failures* impose — the part rewriting can fix.

        cost = lapse_rate / interval        where  lapse_rate = lapses / reps

    A card's ``interval`` is FSRS's own durability verdict (fit to the user's
    reviews), so ``1 / interval`` is how often the card comes back; multiplying by the
    per-review failure rate gives the rate at which the card *wastes* reviews on lapses.
    A card you never fail scores 0 — rewriting it would save nothing, and the cost of
    reviewing a card you get right is the price of remembering, not a defect. Only
    graduated cards (a real interval) with enough history are scored.
    """
    reps = int(card.get("reps", 0) or 0)
    interval = int(card.get("interval", 0) or 0)
    if reps < MIN_REPS or interval < 1:
        return None

    lapses = int(card.get("lapses", 0) or 0)
    lapse_rate = lapses / reps
    cost = lapse_rate / interval

    return {
        "card": int(card["cardId"]),
        "note": int(card["note"]),
        "cost": round(cost, 6),
        "reps": reps,
        "lapses": lapses,
        "lapse_rate": round(lapse_rate, 4),
        "interval_days": interval,
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
    scores.sort(key=lambda row: row["cost"], reverse=True)
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
    costly_threshold = scores[costly_count - 1]["cost"] if costly_count else None

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
            "cost_threshold": costly_threshold,
        },
        "score_parameters": {
            "cost": "lapse_rate / interval_days  (lapse_rate = lapses / reps)",
            "interval_note": (
                "interval_days is FSRS's own scheduling output (its durability "
                "verdict, fit to the user's reviews); 1/interval is review frequency."
            ),
            "scored_only_if": f"reps >= {MIN_REPS} and interval_days >= 1",
            "zero_lapse_note": (
                "cards you never fail score 0 — the base cost of reviewing a card you "
                "get right is the price of remembering, not a defect to fix"
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
