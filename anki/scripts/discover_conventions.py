#!/usr/bin/env python3
"""Produce a read-only JSON snapshot for convention discovery."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
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
    quote_search_value,
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def display_text(value: str) -> str:
    """Create a display-only plain-text copy of an Anki field."""
    parser = _TextExtractor()
    try:
        parser.feed(value)
        parser.close()
        text = " ".join(parser.parts)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\[sound:[^\]]+\]", " [sound] ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def query_difficulty_stats(
    query: str,
    *,
    sample_limit: int,
    url: str,
    timeout: float,
) -> dict[str, Any]:
    ids = call("findCards", {"query": query}, url=url, timeout=timeout)
    sampled_ids = even_sample(ids, sample_limit)
    rows = cards_info(sampled_ids, url=url, timeout=timeout)
    average = (
        sum(int(row.get("lapses", 0) or 0) for row in rows) / len(rows)
        if rows
        else 0.0
    )
    return {
        "query": query,
        "card_count": len(ids),
        "sample_size": len(rows),
        "average_lapses": round(average, 4),
        "card_ids": ids,
    }


def field_profile(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    counts: Counter[str] = Counter()
    total_chars: Counter[str] = Counter()
    prose_counts: Counter[str] = Counter()
    for card in rows:
        for name, field in card.get("fields", {}).items():
            text = display_text(str(field.get("value", "")))
            if not text:
                continue
            counts[name] += 1
            total_chars[name] += len(text)
            if len(text.split()) >= 4 or re.search(r"[.!?;:]", text):
                prose_counts[name] += 1

    denominator = max(len(rows), 1)
    output: dict[str, dict[str, Any]] = {}
    for name in sorted({*counts.keys()}):
        filled = counts[name]
        output[name] = {
            "filled_cards": filled,
            "filled_percent": round(100.0 * filled / denominator, 1),
            "average_text_characters_when_filled": round(total_chars[name] / filled, 1),
            "prose_like_percent_when_filled": round(100.0 * prose_counts[name] / filled, 1),
        }
    return output


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    version = call("version", url=args.url, timeout=args.timeout)
    decks = call("deckNames", url=args.url, timeout=args.timeout)
    models = call("modelNames", url=args.url, timeout=args.timeout)

    model_rows: list[dict[str, Any]] = []
    fields_by_model: dict[str, Any] = {}
    for model in models:
        fields = call(
            "modelFieldNames", {"modelName": model}, url=args.url, timeout=args.timeout
        )
        try:
            template_fields = call(
                "modelFieldsOnTemplates",
                {"modelName": model},
                url=args.url,
                timeout=args.timeout,
            )
        except AnkiConnectError:
            template_fields = None

        ids = call(
            "findCards",
            {"query": f"note:{quote_search_value(model)}"},
            url=args.url,
            timeout=args.timeout,
        )
        sampled = even_sample(ids, args.field_sample)
        cards = cards_info(sampled, url=args.url, timeout=args.timeout)
        profile = field_profile(cards)
        fields_by_model[model] = {
            "cards_in_model": len(ids),
            "sample_size": len(cards),
            "fields": profile,
        }
        model_rows.append(
            {
                "name": model,
                "field_names": fields,
                "fields_on_templates": template_fields,
            }
        )

    state_queries = ["is:suspended", "is:new", "is:due", "is:review", "is:learn"]
    counts = {
        query: len(call("findCards", {"query": query}, url=args.url, timeout=args.timeout))
        for query in state_queries
    }
    all_card_ids = call("findCards", {"query": "deck:*"}, url=args.url, timeout=args.timeout)
    counts["total"] = len(all_card_ids)

    baseline = query_difficulty_stats(
        "deck:*", sample_limit=args.difficulty_sample, url=args.url, timeout=args.timeout
    )
    baseline_average = float(baseline["average_lapses"])
    baseline.pop("card_ids", None)

    flags: list[dict[str, Any]] = []
    for number in range(1, 8):
        stats = query_difficulty_stats(
            f"flag:{number}",
            sample_limit=args.difficulty_sample,
            url=args.url,
            timeout=args.timeout,
        )
        stats.pop("card_ids", None)
        if not stats["card_count"]:
            continue
        ratio = (
            float(stats["average_lapses"]) / baseline_average
            if baseline_average > 0
            else None
        )
        stats.update(
            {
                "flag": number,
                "difficulty_ratio_to_collection": round(ratio, 3) if ratio is not None else None,
                "difficulty_correlated_candidate": bool(ratio is not None and ratio > 1.5),
            }
        )
        flags.append(stats)

    all_note_ids = call("findNotes", {"query": "deck:*"}, url=args.url, timeout=args.timeout)
    note_rows = notes_info(all_note_ids, url=args.url, timeout=args.timeout)
    tag_counts = Counter(tag for note in note_rows for tag in note.get("tags", []))
    leech_card_ids = set(
        call("findCards", {"query": "prop:lapses>=8"}, url=args.url, timeout=args.timeout)
    )

    tags: list[dict[str, Any]] = []
    for tag, note_count in tag_counts.most_common(args.max_tags):
        query = f"tag:{quote_search_value(tag)}"
        stats = query_difficulty_stats(
            query,
            sample_limit=args.difficulty_sample,
            url=args.url,
            timeout=args.timeout,
        )
        tag_card_ids = set(stats.pop("card_ids"))
        overlap = tag_card_ids & leech_card_ids
        ratio = (
            float(stats["average_lapses"]) / baseline_average
            if baseline_average > 0
            else None
        )
        stats.update(
            {
                "tag": tag,
                "note_count": note_count,
                "difficulty_ratio_to_collection": round(ratio, 3) if ratio is not None else None,
                "difficulty_correlated_candidate": bool(ratio is not None and ratio > 1.5),
                "leech_overlap_cards": len(overlap),
                "leech_precision": round(len(overlap) / len(tag_card_ids), 4)
                if tag_card_ids
                else 0.0,
                "leech_recall": round(len(overlap) / len(leech_card_ids), 4)
                if leech_card_ids
                else 0.0,
            }
        )
        tags.append(stats)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "anki_connect_api_version": version,
        "decks": decks,
        "models": model_rows,
        "counts": counts,
        "difficulty_baseline": baseline,
        "flags_in_use": flags,
        "top_tags": tags,
        "field_profiles": fields_by_model,
        "notes_scanned_for_tags": len(note_rows),
        "interpretation_warning": (
            "These are signals, not meanings. Confirm all inferred flag, tag, and field "
            "conventions with the user before acting on them."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--difficulty-sample", type=int, default=500)
    parser.add_argument("--field-sample", type=int, default=200)
    parser.add_argument("--max-tags", type=int, default=25)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    if args.difficulty_sample <= 0 or args.field_sample <= 0 or args.max_tags <= 0:
        parser.error("sample sizes and max-tags must be positive")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_report(args)
    except (AnkiConnectError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.compact:
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
