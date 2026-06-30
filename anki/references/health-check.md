# Collection health check

## Contents

- Purpose and boundaries
- Generate the read-only report
- Explain what the collection is about
- Rank costly cards
- Find hotspots
- Scan card content
- Present the result and hand back
- Exact score definitions

## Purpose and boundaries

The health check is the skill's core read-only analysis. It should add what Anki's built-in statistics do not:

- read the cards and explain the collection's subject matter;
- identify specific cards likely to be consuming disproportionate review effort;
- show where that cost concentrates by topic, tag, deck, or note type;
- identify construction problems such as ambiguity, bundled answers, and confusable pairs.

Do not recreate Anki's normal retention dashboard, due forecast, or basic counts unless a count is needed to explain the custom analysis.

Do not claim that the analysis finds missing syllabus content. It finds weaknesses in the cards that exist.

## Generate the read-only report

First choose the scope. Unless the user has already named a deck or queue, ask whether to focus on a single deck or exclude one before ranking — a large deck (a language or geography deck, for instance) can otherwise dominate the costliest cards and hide problems elsewhere. Default to the whole collection when they have no preference. Translate the answer into the `--query` value:

| scope | `--query` |
| --- | --- |
| whole collection (default) | `deck:*` |
| focus on one deck (includes subdecks) | `deck:"Deck Name"` |
| exclude a deck | `deck:* -deck:"Deck Name"` |

Then, from the skill root, run:

```bash
python3 scripts/health_report.py \
  --query 'deck:*' \
  --sample 400 \
  --worst 25 \
  --costly-percentile 5 \
  > /tmp/anki-health.json
```

For a tag or queue instead, replace `deck:*` with the exact Anki search. If `costly_pctile` is saved in `conventions.local.md`, pass that value instead of `5`.

The script:

- fetches data in batches of 200;
- uses an evenly spaced representative sample of at most 400 cards;
- scores every reviewed matching card;
- returns the 25 highest-cost cards by default;
- enriches the sample and worst cards with tags and sibling-card IDs;
- scores by `cost = lapse_rate / interval_days`, so cards the user never fails score `0`;
- makes no changes to Anki.

Its `display_fields` are plain-text, potentially truncated previews. Never use them as write input. Re-fetch complete raw fields before proposing an edit.

## Explain what the collection is about

Read the representative sample and infer roughly 5–12 natural topic clusters. Use card content, deck names, tags, and note types as evidence, but let content override misleading organizational names.

For each cluster, report:

- a short, concrete description of what the cards cover;
- card count, exact when the whole collection was read and approximate when sampling was used;
- average card lapse rate among reviewed sampled cards in the cluster;
- one sentence about the dominant construction pattern or difficulty signal.

Calculate topic health as:

```text
mean(lapses / max(reps, 1)) across reviewed sampled cards in the topic
```

Do not call average lapses per card a “lapse rate.” Keep the units explicit.

When the collection exceeds 400 cards, mark topic counts and proportions with `~` or “approximately.” Do not present sample-derived totals as exact. If a topic is too small in the sample to support a stable comparison, say so.

A useful opening has this shape:

> You have about 7,200 cards across roughly ten areas. Most are economics and languages. Pharmacology has the highest sampled lapse rate, so that is where review effort appears to concentrate.

Use the user's actual data; never copy the example's topics or numbers.

## Rank costly cards

Sort all reviewed cards by `cost` and inspect the highest 25. “Costly” means the worst `costly_pctile` percent, default `5`, by this custom cost score. It is not the same as Anki's leech tag or `prop:lapses>=8`.

For each card you surface, show:

- front and back or the relevant note fields;
- deck, note type, and tags;
- reps, lapses, lapse rate, interval, and the custom cost score;
- the annotation field, if configured;
- a concise hypothesis about why it is costly;
- whether sibling cards from the same note may share the problem.

Do not treat a high score as proof that wording is bad. A genuinely difficult but well-constructed concept can also score highly. The content scan and the user's judgment determine the response.

## Find hotspots

Group high-cost cards by:

- topic cluster;
- deck;
- note type;
- confirmed tags;
- shared source or annotation pattern when available.

Look for disproportion rather than raw size. A useful comparison is:

```text
share of high-cost cards in group ÷ share of all reviewed cards in group
```

Describe the underlying counts as well as the ratio. For example, a small anatomy tag might contain 6% of reviewed cards but 30% of the top cost set.

Avoid causal claims. Say “cost concentrates here” or “this pattern is associated with more lapses,” not “this tag causes lapses.”

## Scan card content

The model's advantage is that it can read the card content. Inspect the highest-cost set and a representative sample for:

- **ambiguous or non-univocal fronts:** several defensible answers fit;
- **list-style cards:** “Name 3…” or a back containing several independently recallable items;
- **over-long or padded backs:** the target is buried in explanation;
- **near duplicates:** substantially the same cue and answer;
- **confusable pairs:** similar cues with different answers and insufficient distinguishing context;
- **yes/no prompts:** recognition rather than production;
- **vague prompts:** “Explain,” “Discuss,” “What is X?” without enough scope;
- **cloze hazards:** excessive deletion size, missing context, or accidental multiple targets;
- **source mismatch:** an annotation says the card is wrong, outdated, or externally managed.

Use [references/card-writing.md](card-writing.md) only as the rubric. Do not start rewriting during the health check.

If a factual correction seems necessary, mark it **⚠ confirm** unless it is verified against a source the user supplied or explicitly authorized you to research.

## Present the result and hand back

Keep the report decision-oriented:

1. **Collection map:** 5–12 topics and their sampled health.
2. **Where effort concentrates:** the strongest hotspot comparisons.
3. **Costliest cards:** a short table or numbered list, not a wall of 25 full cards unless the user asks.
4. **Construction patterns:** the recurring card-design issues found by reading content.
5. **Next choice:** costliest cards, a deck/note type, or the user's confirmed review queue.

After a general first-run health check and preference calibration, stop. Reassure the user that nothing will change without approval and ask where they would like to start. Do not flow automatically into edits.

For a health-check-only request, also stop after the report unless the user explicitly asks to proceed to proposals.

## Exact score definition

The skill ranks cards by the review cost their *failures* impose — the part rewriting can actually fix.

```text
lapse_rate = lapses / reps
cost       = lapse_rate / interval_days
```

Scored only for graduated cards with enough history: `reps >= 5` and `interval_days >= 1` (`is:review`). A card the user never fails scores `0`.

**Why this form (so it can be explained honestly):**

- `interval_days` is **FSRS's own scheduling output** — its durability verdict for the card, fit to the user's review history. So `1 / interval` is how often the card keeps coming back. We read FSRS's verdict; we do not re-derive or out-measure it.
- `lapse_rate` is the per-review failure probability. Multiplying gives the rate at which the card *wastes* reviews on lapses.
- We deliberately do **not** rank by total `reps` (a sunk cost), nor by the base review frequency of cards the user gets right (reviewing a card you remember is the price of memory, not a defect). Only the failure-driven excess is fixable by rewriting.

**What this is not.** Standard AnkiConnect does not expose FSRS's per-card difficulty, stability, or retrievability — and Anki already lets the user sort by those in the Browser. This `cost` is a simple, opinionated *triage ranking* of rewrite candidates: not a difficulty measure, and not a reimplementation of FSRS. The legacy SM-2 `ease` factor is frozen (stale) under FSRS, so it is intentionally unused.
