#!/usr/bin/env python3
"""Small standard-library AnkiConnect client used by the Anki skill.

The module is safe to import from other bundled scripts. Its CLI performs one
explicit AnkiConnect action and prints the JSON result.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections.abc import Iterator, Sequence
from typing import Any, TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_VERSION = 6
DEFAULT_URL = os.environ.get("ANKI_CONNECT_URL", "http://127.0.0.1:8765")
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_BATCH_SIZE = 200

T = TypeVar("T")


class AnkiConnectError(RuntimeError):
    """Raised when AnkiConnect cannot be reached or returns an API error."""


def call(
    action: str,
    params: dict[str, Any] | None = None,
    *,
    url: str = DEFAULT_URL,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> Any:
    """Call one AnkiConnect action and return its result."""
    if not action:
        raise ValueError("action must be a non-empty string")

    payload = json.dumps(
        {"action": action, "version": API_VERSION, "params": params or {}},
        ensure_ascii=False,
    ).encode("utf-8")
    request = Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raise AnkiConnectError(
            f"AnkiConnect returned HTTP {exc.code}: {exc.reason}"
        ) from exc
    except URLError as exc:
        raise AnkiConnectError(
            "Could not reach AnkiConnect at "
            f"{url}. Open Anki and verify that AnkiConnect is installed."
        ) from exc
    except TimeoutError as exc:
        raise AnkiConnectError(
            f"AnkiConnect did not respond within {timeout:g} seconds."
        ) from exc

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AnkiConnectError(
            f"AnkiConnect returned invalid JSON: {raw[:200]!r}"
        ) from exc

    if not isinstance(envelope, dict) or "result" not in envelope or "error" not in envelope:
        raise AnkiConnectError(
            "Unexpected AnkiConnect response shape; expected result and error fields."
        )
    if envelope["error"] is not None:
        raise AnkiConnectError(f"AnkiConnect {action!r} failed: {envelope['error']}")
    return envelope["result"]


def batched(values: Sequence[T], size: int = DEFAULT_BATCH_SIZE) -> Iterator[list[T]]:
    """Yield stable list batches without changing input order."""
    if size <= 0:
        raise ValueError("batch size must be positive")
    for start in range(0, len(values), size):
        yield list(values[start : start + size])


def cards_info(
    card_ids: Sequence[int],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    url: str = DEFAULT_URL,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    """Fetch cardsInfo in bounded batches and omit missing-card placeholders."""
    output: list[dict[str, Any]] = []
    for batch in batched(card_ids, batch_size):
        rows = call("cardsInfo", {"cards": batch}, url=url, timeout=timeout)
        output.extend(row for row in rows if isinstance(row, dict) and row.get("cardId"))
    return output


def notes_info(
    note_ids: Sequence[int],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    url: str = DEFAULT_URL,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    """Fetch notesInfo in bounded batches and omit missing-note placeholders."""
    output: list[dict[str, Any]] = []
    for batch in batched(note_ids, batch_size):
        rows = call("notesInfo", {"notes": batch}, url=url, timeout=timeout)
        output.extend(row for row in rows if isinstance(row, dict) and row.get("noteId"))
    return output


def even_sample(values: Sequence[T], limit: int) -> list[T]:
    """Return at most limit evenly spaced values, preserving their order."""
    if limit <= 0:
        return []
    if len(values) <= limit:
        return list(values)
    step = max(1, math.ceil(len(values) / limit))
    return list(values[::step][:limit])


def quote_search_value(value: str) -> str:
    """Quote a value for an Anki search term."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _parse_params(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"params must be JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError("params JSON must be an object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Call one AnkiConnect action.")
    parser.add_argument("action", help="AnkiConnect action, for example version or deckNames")
    parser.add_argument(
        "params",
        nargs="?",
        default="{}",
        type=_parse_params,
        help='JSON object of parameters (default: "{}")',
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--compact", action="store_true", help="Print compact JSON")
    args = parser.parse_args(argv)

    try:
        result = call(args.action, args.params, url=args.url, timeout=args.timeout)
    except (AnkiConnectError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.compact:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
