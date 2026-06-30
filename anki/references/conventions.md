# Convention discovery and saved state

## Contents

- When to run discovery
- Read-only discovery snapshot
- Interpret flags and tags
- Detect an annotation field
- Detect external authoring
- Confirm the findings
- Save the confirmed state

## When to run discovery

Run the full discovery during a general first use when `conventions.local.md` is absent. Do not rerun it on every session once the user has confirmed and saved conventions.

For a specific request, discover only what the request requires. Examples:

- A count of cards by deck does not require flag interpretation.
- “Show my fix-me queue” requires the review-flag convention if it is not saved.
- A rewrite requires the note's fields, card style, annotation field, and source-of-truth route.

All discovery is read-only. An inference is never permission to act.

## Read-only discovery snapshot

From the skill root, run:

```bash
python3 scripts/discover_conventions.py > /tmp/anki-conventions.json
```

The script reports:

- deck names;
- note types and field names;
- fields referenced by each card template when the API exposes them;
- counts for suspended, new, due, review, and learning cards;
- collection-wide average lapses from an evenly spaced sample of at most 500 cards;
- flags 1–7 that are in use and their average-lapse ratios;
- the 25 most-used tags, their average-lapse ratios, and their overlap with `prop:lapses>=8`;
- per-note-type field population and prose-like statistics from an evenly spaced sample of at most 200 cards.

The thresholds are unchanged from the original workflow: a flag or tag with average lapses greater than `1.5 ×` the collection baseline is a **difficulty-correlated candidate**. This is a clue, not a meaning.

If the script fails, fix only the read-only retrieval issue. Do not proceed by guessing conventions.

## Interpret flags and tags

Anki does not assign a universal personal meaning to colored flags or custom tags. Infer candidates from evidence, then ask the user.

### Flags

For every flag in use, consider:

- number of cards;
- average lapses relative to the collection baseline;
- decks and note types where it appears;
- a small sample of the flagged cards;
- whether the cards' content or annotation field suggests a shared purpose.

A high lapse ratio may suggest “hard,” “struggling,” or “fix me,” but it could instead mark an exam, source, topic, or temporary workflow. Never name the convention without confirmation.

### Tags

For the most-used tags, consider:

- note count and card count;
- average lapses and the `1.5 ×` difficulty-correlation signal;
- overlap with `prop:lapses>=8`;
- tag hierarchy, such as `topic::subtopic`;
- a small content sample.

A tag that closely overlaps the lapse search may be the user's leech convention. Exact overlap still requires confirmation: the user may have assigned the tag for another reason, or Anki may have added it automatically under a configuration the user no longer follows.

Keep these concepts separate in saved state:

- `leech_signal`: the user's confirmed convention, often `tag:leech`;
- costly cards: the skill's worst percentile by custom cost score;
- `prop:lapses>=8`: an Anki search condition.

## Detect an annotation field

Some users keep a note-to-self about what is wrong with a card in a field such as `Notes`, `Comment`, or `Extra`.

Use the field profile as a shortlist, then inspect representative values. A plausible annotation field is usually:

- not the main question or answer field;
- populated on a meaningful minority of notes rather than every note;
- prose-like rather than a single atomic answer;
- used to describe ambiguity, source context, or a desired fix.

Template membership is evidence, not a hard rule. An `Extra` field may render on the answer side and still contain the user's annotations.

Show the user examples or a concise description without exposing more card content than needed, then ask whether the field should be read first during card review. Save `annotation_field: none` when no such field exists.

## Detect card style

Inspect note types and actual fields rather than inferring style from names alone.

Save one of:

- `basic`: rewrites should preserve ordinary front/back construction;
- `cloze`: rewrites should preserve cloze syntax and numbering;
- `mixed`: select style per note type and do not convert types without approval.

Do not change note type or card templates as part of an ordinary rewrite.

## Detect external authoring

Ask about external authoring when:

- the user mentions Obsidian, Markdown, a vault, or a sync/import plugin;
- fields contain source markers suggesting generated notes; or
- saved state already contains an `external_source`.

If the user confirms an external workflow, ask for the specific source directory. Do not search the whole home directory.

For obsidian-to-anki style IDs, check a representative known note:

```bash
NOTE_ID='1712345678901'
SOURCE_DIR='/absolute/path/to/source'
grep -RIl --fixed-strings "<!--ID: ${NOTE_ID}-->" "$SOURCE_DIR"
```

A match establishes the external file as the source of truth for that note. A non-match does not prove that every note is Anki-native; check each proposed edit when a mixed collection is possible.

Save the confirmed absolute or home-relative source path, or `none`.

## Confirm the findings

Summarise only the actionable inferences and ask the user to correct them. For example:

> It looks as though flag 5 is your “fix me” queue, `tag:leech` is your leech signal, you put card-specific notes in `Notes`, and these cards are authored directly in Anki. Is that right?

Use the host's structured choice tool when available. Suitable choices are:

1. Yes, that is right.
2. Mostly right—let me correct one item.
3. Do not save this; use it for this session only.
4. Stop.

Apply corrections immediately to the in-memory interpretation. Do not argue from the statistical signal against the user's stated convention.

## Save the confirmed state

After confirmation, offer to save. Show the complete proposed file or an exact diff and wait for explicit approval. The state file is `conventions.local.md` beside `SKILL.md`.

Use this plain-Markdown key/value structure and preserve unknown keys when updating an existing file:

```text
# Anki conventions

review_flag: 5
leech_signal: tag:leech
annotation_field: Notes
external_source: ~/path/to/obsidian/vault
card_style: basic
costly_pctile: 5
preferences:
  isolated_date: keep+mnemonic
  citation_naming: keep+split-author-year
  ambiguous: fix-wording
  hard_concept: leave
  costly_card: ask
```

Field meanings:

- `review_flag`: the confirmed flag used to park cards for review, or `none`.
- `leech_signal`: the user's confirmed leech query, not the cost score.
- `annotation_field`: the field to read first during review, or `none`.
- `external_source`: the confirmed source directory, or `none`.
- `card_style`: `basic`, `cloze`, or `mixed`.
- `costly_pctile`: worst N percent by cost score that always require a deliberate choice; default and original value is `5`.
- `preferences`: per-card-type defaults learned in the preference interview.

Do not populate a preference that the user has not expressed. Do not silently replace corrections with newly inferred values on a later run.

After writing an approved state file, re-read it and report the exact saved values. If writing fails, retain the conventions for the current session and explain that persistence failed.
