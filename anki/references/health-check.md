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
- show where that trouble concentrates by topic, tag, deck, or note type;
- identify construction problems such as ambiguity, bundled answers, and confusable pairs.

Do not recreate Anki's normal retention dashboard, due forecast, or basic counts unless a count is needed to explain the custom analysis.

Do not claim that the analysis finds missing syllabus content. It finds weaknesses in the cards that exist.

## Generate the read-only report

From the skill root, run:

```bash
python3 scripts/health_report.py \
  --query 'deck:*' \
  --sample 400 \
  --worst 25 \
  --costly-percentile 5 \
  > /tmp/anki-health.json
```

For a requested deck, tag, or queue, replace `deck:*` with the exact Anki search. If `costly_pctile` is saved in `conventions.local.md`, pass that value instead of `5`.

The script:

- fetches data in batches of 200;
- uses an evenly spaced representative sample of at most 400 cards;
- scores every reviewed matching card;
- returns the 25 highest-trouble cards by default;
- enriches the sample and worst cards with tags and sibling-card IDs;
- leaves `time_ratio` at `0.0`, matching the original default;
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

Sort all reviewed cards by `trouble` and inspect the highest 25. “Costly” means the worst `costly_pctile` percent, default `5`, by this custom trouble score. It is not the same as Anki's leech tag or `prop:lapses>=8`.

For each card you surface, show:

- front and back or the relevant note fields;
- deck, note type, and tags;
- reps, lapses, lapse rate, interval, and the custom trouble score;
- the annotation field, if configured;
- a concise hypothesis about why it is costly;
- whether sibling cards from the same note may share the problem.

Do not treat a high score as proof that wording is bad. A genuinely difficult but well-constructed concept can also score highly. The content scan and the user's judgment determine the response.

## Find hotspots

Group high-trouble cards by:

- topic cluster;
- deck;
- note type;
- confirmed tags;
- shared source or annotation pattern when available.

Look for disproportion rather than raw size. A useful comparison is:

```text
share of high-trouble cards in group ÷ share of all reviewed cards in group
```

Describe the underlying counts as well as the ratio. For example, a small anatomy tag might contain 6% of reviewed cards but 30% of the top trouble set.

Avoid causal claims. Say “trouble concentrates here” or “this pattern is associated with more lapses,” not “this tag causes lapses.”

## Scan card content

The model's advantage is that it can read the card content. Inspect the highest-trouble set and a representative sample for:

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

## Exact score definitions

The weights, thresholds, and formulas below are unchanged.

### Lapse rate

```text
lapse_rate = min(lapses / max(reps, 1), 1)
```

This is the fraction of recorded repetitions associated with lapses, capped at 1.

### Ease erosion

```text
ease_erosion = clamp(1 - factor / 2500, 0, 1)    when factor > 0
ease_erosion = 0.5                                when factor == 0
```

Under FSRS, the legacy `factor` may be zero. The `0.5` fallback preserves the original formula and usually contributes the same constant to all such cards; do not present it as measured FSRS difficulty.

### Mature failure

```text
mature_failure = interval > 21 days and lapse_rate > 0.15
```

This is a strong binary signal that a card with a mature interval is still failing often.

### Time ratio

```text
time_ratio = dwell time on this card / the user's typical card dwell time
```

The default implementation leaves this at `0.0`. Do not enable it merely because review logs are available. First define and validate a robust normalization, cap extreme timer values, and explain the definition to the user. Enabling it retains the same weight of `0.20`.

### Trouble

```text
trouble = (
    0.35 * lapse_rate
    + 0.25 * ease_erosion
    + 0.20 * time_ratio
    + 0.20 * mature_failure
)
```

Higher means the card merits more attention. This is a custom prioritization score, not an Anki or FSRS metric.

### Weakness

```text
weakness = lapses / max(days_since_note_id_timestamp, 1)
```

This is the transparent “lapses per day the note has existed” alternative. Treat note-ID time as an age proxy, especially for imported collections.

### Confidence

```text
confidence = (
    0.35 * min(reps / 25, 1)
    + 0.35 * min(interval / 90, 1)
    + 0.20 * (1 - lapse_rate)
    + 0.10 * min(factor / 2600, 1)
)
```

Higher suggests a healthier, better-established card. It is a separate health score, not the mathematical inverse of `trouble`. Under FSRS, a zero legacy factor lowers this score, so label that limitation.
