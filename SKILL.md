---
name: anki
description: Talk to your Anki flashcards with Claude Code via AnkiConnect — search, review, rewrite, and triage cards, run a collection health check, and find & fix the cards costing you the most reviews. Adapts to your own flags/tags/conventions instead of assuming them. Use whenever the user asks anything about their Anki collection.
user_invocable: true
---

# Anki Skill for Claude Code

> **Talk to your flashcards.** Search, review, rewrite, and triage your Anki cards in natural language — and find the cards quietly costing you the most reviews, then fix them.

This is a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that connects to [Anki](https://apps.ankiweb.net/) via the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on. Drop it into your skills folder and you can ask Claude to work with your flashcards directly.

## When the user invokes this skill

If they ask for something specific ("show my suspended cards", "find cards about X", "rewrite this one"), just do that. Otherwise — a bare `/anki`, "help me with my flashcards", or first use — **drive this guided flow yourself; don't make the user know the steps.** At every decision point ask with the host's built-in multiple-choice prompt (so they click, not type), and *offer* rather than force — they can stop or jump anywhere. **Make no changes to cards or files until the user approves a specific fix.**

1. **Connect.** Verify AnkiConnect (below); if it's down, say so and stop.
2. **Conventions.** Load `~/.claude/skills/anki/conventions.local.md` if it exists; otherwise run *Step 0* discovery, confirm what you inferred, and offer to save it.
3. **Health check.** Run it (*Health check* section): what the collection is about, where the trouble concentrates, the costliest cards.
4. **Calibrate.** If no saved `preferences`, run *Preference discovery* — the short multiple-choice interview — and save the profile.
5. **Hand back — do NOT start fixing.** After calibration, **stop.** Reassure the user that **nothing will change in Anki without their explicit approval**, then ask *where they'd like to start* — via multiple-choice, with suggestions (e.g. the costliest cards, a particular deck or card-type, or their review-flag queue). Only once they choose do you proceed — and then you **print** a small batch of proposed edits (see *Calibrate, then fix*) for approval before touching anything.

First run is the full sequence; on later runs, skip what's already saved and go straight to the health check and the same hand-back. Keep each step short and end it with a clear on-screen choice of what to do next.

## How this skill behaves (read first)

A few principles keep this useful and trustworthy. Follow them:

- **Never change anything without explicit approval — the cardinal rule.** Always *print* the proposed edits to screen and get a clear "yes" before applying anything, to Anki **or** to any source file. Default to preview; silence is never consent. After discovery and calibration, do **not** start editing — stop, reassure the user that nothing will change without their go-ahead, and ask where they want to start. A user must never watch the AI reach into their deck unbidden.
- **Speak Anki's language.** Use the vocabulary the user already sees in Anki: lapses, leeches, intervals, ease, and (under FSRS) retrievability, difficulty, stability. Don't invent AI-marketing metrics.
- **Never touch scheduling.** Do not change intervals, ease, due dates, or run reschedulers — Anki warns against add-ons that affect FSRS scheduling. Your actions are limited to: search, tags, filtered decks, suspend/unsuspend, moving decks, and editing card *content*.
- **Weaknesses, not gaps.** From review data you can find *weak*, *redundant*, *confusable*, or *poorly-worded* cards. You cannot know what's *missing* without a syllabus — never claim "gap detection" from deck data alone.
- **Adapt, don't assume.** Different users flag, tag, and suspend differently. Discover the user's conventions (see *Step 0*) before acting on them. Don't assume field names, flag meanings, or tags.
- **Decide nothing about *what* to remember.** You assess card *construction*; whether a fact is worth keeping (and whether to delete) is the user's call. Learn their preferences (see *Preference discovery*) rather than imposing yours.
- **Ask on screen, not by typing.** When you need a decision — preference discovery, per-card choices, confirmations — use the host's built-in multiple-choice prompt (Claude Code's question tool / Codex's equivalent) so options render as clickable choices. Fall back to free text only when the user picks "something else."
- **One dependency.** AnkiConnect is the only thing required. Keep it that way — no databases, no extra installs.

## Setup

### 1. Install AnkiConnect

In Anki: **Tools > Add-ons > Get Add-ons...** → enter code `2055492159` → restart Anki.

### 2. Install this skill

Save this file to:

    ~/.claude/skills/anki/SKILL.md

### 3. Use it

With Anki running, ask Claude Code anything about your cards:

    /anki                                         # just this — it walks you through discovery, a health check, and fixes
    /anki show me my suspended cards
    /anki how many cards do I have in each deck?
    /anki run a health check on my collection
    /anki find the cards costing me the most reviews and let's fix them
    /anki walk me through my leech cards one at a time

## Core API Pattern

All AnkiConnect calls follow the same shape. Always use this Python helper:

    import json, urllib.request

    def anki(action, **params):
        req = json.dumps({'action': action, 'version': 6, 'params': params}).encode()
        resp = json.loads(urllib.request.urlopen(
            urllib.request.Request('http://localhost:8765', req)
        ).read())
        if resp['error']:
            raise Exception(resp['error'])
        return resp['result']

Define this at the top of every Python script that talks to Anki.

**Verify connectivity first:**

    curl -s localhost:8765 -X POST -d '{"action":"version","version":6}'

If this fails, tell the user: "Anki doesn't seem to be running, or AnkiConnect isn't installed. Please open Anki and try again."

---

## Step 0 — Learn the user's conventions (run first)

Before triaging, fixing, or interpreting flags/tags, find out how *this* user organises their collection. Anki has no fixed meaning for flags or tags — `flag:1` might mean "hard" for one person and "exam" for another.

**First, check for saved conventions.** If `~/.claude/skills/anki/conventions.local.md` exists, load it and use it — the user has already been through this. Otherwise, run the discovery below and, at the end, **offer to save** what you found to that file so future sessions skip this step.

### Discover the structure

    # Decks, note types, and the fields on each note type
    print('Decks:', anki('deckNames'))
    for model in anki('modelNames'):
        print(f'  {model}: {anki("modelFieldNames", modelName=model)}')

    # Card counts by state
    for q in ['is:suspended', 'is:new', 'is:due', 'is:review', 'is:learn']:
        print(f'  {q}: {len(anki("findCards", query=q))}')
    print('  Total:', len(anki('findCards', query='*')))

### Infer what their flags and tags *mean*

The trick: cross-tabulate each flag/tag against a difficulty signal (lapses). A flag whose cards lapse far more than average is probably "hard/struggling"; a tag that perfectly overlaps `prop:lapses>=8` is their leech convention.

    def avg_lapses(query):
        ids = anki('findCards', query=query)[:500]
        if not ids: return (0, 0.0)
        info = anki('cardsInfo', cards=ids)
        return (len(ids), sum(c.get('lapses', 0) for c in info) / len(info))

    base_n, base = avg_lapses('deck:*')
    print(f'collection-wide avg lapses: {base:.2f}')

    # Flags in use, and whether each looks correlated with difficulty
    for n in range(1, 8):
        cnt, al = avg_lapses(f'flag:{n}')
        if cnt:
            tag = '  <-- looks like "hard/struggling"' if al > base * 1.5 else ''
            print(f'flag {n}: {cnt} cards, avg lapses {al:.2f}{tag}')

    # Most-used tags, flagged if they concentrate difficulty
    notes = anki('notesInfo', notes=anki('findNotes', query='deck:*'))
    from collections import Counter
    tag_counts = Counter(t for nt in notes for t in nt['tags'])
    for tag, cnt in tag_counts.most_common(25):
        _, al = avg_lapses(f'tag:{tag}')
        flag = '  <-- difficulty-correlated' if al > base * 1.5 else ''
        print(f'tag "{tag}": {cnt} cards, avg lapses {al:.2f}{flag}')

### Detect a self-annotation field

Some users write a note-to-self about *what's wrong with a card* into a dedicated field (commonly called `Notes`, `Comment`, or `Extra`). If a non-core field is populated on a meaningful fraction of cards with prose, treat it as the user's "what to fix" field and **read it first** when reviewing a card.

    # Heuristic: which fields carry free-text annotations vs. core Q/A?
    for model in anki('modelNames'):
        ids = anki('findCards', query=f'"note:{model}"')[:200]
        if not ids: continue
        info = anki('cardsInfo', cards=ids)
        from collections import defaultdict
        filled = defaultdict(int)
        for c in info:
            for f, d in c['fields'].items():
                if d['value'].strip(): filled[f] += 1
        print(model, {f: f'{100*n//len(info)}%' for f, n in filled.items()})

### Detect externally-authored cards (sync safety)

Some users author cards *outside* Anki and sync them in — most commonly with the **obsidian-to-anki** plugin, which writes the Anki note ID back into the source file as `<!--ID: 1712345678901-->`. **For those cards the external file is the source of truth: editing them in Anki gets silently overwritten on the next sync.** If the user mentions Obsidian / external authoring, ask for the vault/notes path and check before editing:

    # A note is externally-managed iff its ID appears in the source files:
    #   grep -rl "<!--ID: <NOTE_ID>" "<USER_SOURCE_DIR>"
    # Match  -> edit the source file, then have the user re-sync. Do NOT updateNoteFields.
    # No match -> safe to edit directly in Anki.

### Confirm and save

Summarise what you inferred ("Looks like flag 5 is your 'fix me' queue, tag `leech` is your leeches, and you annotate problems in the `Notes` field — right?"), let the user correct it, then offer to save. The saved file is plain markdown the skill reads next time:

    # ~/.claude/skills/anki/conventions.local.md
    review_flag: 5            # the flag the user parks "to fix" cards under
    leech_signal: tag:leech   # how the user marks leeches (Anki's tag; NOT our trouble metric)
    annotation_field: Notes   # field holding the user's note-to-self about a card
    external_source: ~/path/to/obsidian/vault   # or: none
    card_style: basic         # basic | cloze | mixed — match this when rewriting
    costly_pctile: 5          # "always ask me" threshold: worst N% by our trouble score
    preferences:              # learned once via the preference-discovery phase, by card type
      isolated_date: keep+mnemonic
      citation_naming: keep+split-author-year
      ambiguous: fix-wording
      hard_concept: leave
      costly_card: ask

---

## Health check — find the cards costing you reviews

This is the skill's core loop: **show what the collection is about, surface the cards that are quietly draining review time and why, then fix them one at a time.** Anki's built-in stats screen already shows retention %, the due forecast, and counts — so don't reproduce that. Add what the dashboard can't: it can't *read* the cards, can't rank specific problem cards, and can't tell the user what their deck is *about*.

### 1. The front door — what is this collection about?

A quick, delightful orientation that doubles as the entry point. Pull a representative sample (or the whole collection if small), read the fronts/backs, and group them into a handful of natural topics — then colour each by health. This needs no embeddings or extra tools; just read and reason.

    ids = anki('findCards', query='deck:*')
    sample = ids if len(ids) <= 400 else ids[::len(ids)//400]   # even sample
    info = anki('cardsInfo', cards=sample)
    # Read the fields, infer 5-12 topic clusters, and for each cluster report:
    #   what it's about, how many cards, and its avg lapse rate.

Present it as: *"You have ~7,200 cards across roughly 10 areas. Most are economics and languages; your highest-lapse area is Pharmacology (≈40% lapse rate) — that's where your reviews are going. Want to start there?"* This is both the "neat!" moment and the on-ramp to fixing.

### 2. Rank the worst cards — the trouble score

Score every reviewed card by how much attention it needs, then sort. Higher = more likely a struggling or badly-written card worth fixing. (Formula defined in *The trouble score* below.)

    import time
    def card_trouble(query='deck:*'):
        ids = anki('findCards', query=query)
        info = anki('cardsInfo', cards=ids)
        now = time.time()
        rows = []
        for c in info:
            reps = c.get('reps', 0) or 0
            if reps <= 0:                      # never reviewed -> no signal yet
                continue
            lapses = c.get('lapses', 0) or 0
            ivl    = c.get('interval', 0) or 0           # current interval, days
            factor = c.get('factor', 0) or 0             # SM-2 ease x1000 (0 under FSRS)
            age_days = max((now - c['note'] / 1000.0) / 86400.0, 1.0)  # note id = creation ts

            lapse_rate      = min(lapses / max(reps, 1), 1.0)
            ease_erosion    = max(0.0, min(1.0, 1.0 - factor / 2500.0)) if factor > 0 else 0.5
            mature_failure  = ivl > 21 and lapse_rate > 0.15

            trouble = (0.35 * lapse_rate
                       + 0.25 * ease_erosion
                       + 0.20 * 0.0                      # time_ratio (optional, see note)
                       + 0.20 * (1.0 if mature_failure else 0.0))
            rows.append({'card': c['cardId'], 'note': c['note'],
                         'trouble': round(trouble, 4), 'reps': reps, 'lapses': lapses,
                         'lapse_rate': round(lapse_rate, 3),
                         'lapses_per_day': round(lapses / age_days, 4)})
        rows.sort(key=lambda r: r['trouble'], reverse=True)
        return rows

    worst = card_trouble()[:25]   # the cards to look at first

*Optional 4th signal:* `time_ratio` = how long the user dwells on a card vs. their typical card, from `getReviewsOfCards` review logs. It sharpens ranking but needs an extra call; the score works fine without it (left at 0 above).

### 3. Hotspots and content problems

- **Hotspots:** group the high-trouble cards by tag / deck / note-type to find *where* the pain concentrates ("your `Anatomy` tag is 6% of cards but 30% of your lapses").
- **Content scan (the LLM's edge — it can read the cards):** flag likely **ambiguous fronts**, **list-style** cards ("Name 3..."), **over-long backs**, and **near-duplicate / confusable** pairs (same-ish question, different answers). These often *are* the reason a card lapses.

### 4. Calibrate the user's preferences (once), then fix

**Don't rewrite blind — different users want different things** (some reframe everything for understanding; some keep deliberate trivia and just want it to stick; some delete aggressively). Learn it once, right after the health check, then apply it.

**Preference discovery (run once; save the result).** Pick 3–5 struggling cards that span *different types* — e.g. an isolated date, a naming/citation card, an ambiguous (non-univocal) card, a bundled-answer card, a genuinely-hard concept. For each, **show one of the user's own cards** (never an example from this file) and ask — **using the host's built-in multiple-choice prompt** so options appear on screen. The shape, with ⟨placeholders⟩ standing in for their real card:

> One card you struggle with —
> Front: *"⟨one of their isolated-date cards⟩"* · Back: *"⟨the year⟩"*
> How would you like cards like this handled?
> (a) Rewrite it around a different fact
> (b) Keep the fact — give me a memory hook / mnemonic
> (c) Delete it
> (d) Something else

Record the answer **by card type**, not just for that one card, so it generalises — e.g. *dates → keep + mnemonic; citations → keep but split author|year; ambiguous → fix wording; costly cards → ask each time*. Save it to the conventions file (`preferences:` block). From then on the fix loop applies these defaults automatically and only stops on genuine edge cases (and on *costly* cards — see below).

**Then fix in small batches — preview first, always.** Only after the user has chosen a starting point. Work in batches of **1–4 cards** (fewer when the edits are heavy; a single big rewrite stands alone).

1. **Compose the batch.** For each card, show its trouble signals + the user's annotation field (if any) and Front/Back/tags, then the **proposed change** — chosen from the saved preference for that card's *type*: **construction fix** (T1/T2, keeps the target) · **memory hook** (a wanted atomic fact) · **split** · **re-aim** (only if the preference or an explicit choice says so) · **delete** (only with consent). Grade construction T0–T3 to guide it; mark **⚠ confirm** on any fact you haven't verified against the user's source. **Never re-aim the target or delete without the user's say-so.**
2. **Print the whole batch and stop for approval. Make no edits yet.** The user approves all, some, or none — and can tweak any.
3. **Apply only what they approved**, in the right place: Anki-native → `updateNoteFields`; externally-authored → edit the source file (never AnkiConnect; see *Externally-authored cards*), then remind them to re-sync.
4. Tag what you changed, then offer the next batch — or stop if they're done.

**Nothing is ever written before the user has seen it on screen and said yes.**

**Costly cards get asked, every time.** "Costly" = the **worst ~5% by trouble score** (our metric — *not* Anki's `lapses>=8` leech rule; tune via `costly_pctile` in conventions). For those, surface the data and a full menu (encode · split · re-aim · suspend · delete · keep) and let the user choose — they're expensive enough to deserve a deliberate call.

### The trouble score (exact definitions)

Ported from a tested implementation. All signals come from `cardsInfo` (`reps`, `lapses`, `interval`, `factor`) plus the note's creation time (its ID).

- `lapse_rate = lapses / reps` — how often the user fails this card.
- `ease_erosion = clamp(1 − factor/2500, 0, 1)` — how far the card's ease has fallen below Anki's 250% default. Under **FSRS**, `factor` is often 0; fall back to `0.5` (as above) or use FSRS `difficulty` if you fetch it.
- `mature_failure = (interval > 21 days) and (lapse_rate > 0.15)` — a card that *should* be learned but still fails. The strongest "this card is broken" signal.
- **`trouble = 0.35·lapse_rate + 0.25·ease_erosion + 0.20·time_ratio + 0.20·mature_failure`** (higher = needs attention).
- **`weakness = lapses / days_since_created`** — a simpler, transparent alternative ("lapses per day this card has existed"). Good when you want one number with no weights.
- **`confidence = 0.35·min(reps/25,1) + 0.35·min(interval/90,1) + 0.20·(1−lapse_rate) + 0.10·min(factor/2600,1)`** (0–1, *higher = healthier*) — the inverse view, useful for "which cards are solid."

---

## Flashcard Writing Principles

**Follow these when creating or rewriting cards.** They are good SRS practice, not optional.

### Card quality vs. what's worth remembering — keep them separate

Two different judgments. Conflating them is the classic failure mode:

- **Construction** — does the card cue *one stable answer* over long horizons? Yours to assess.
- **Target / worth** — is this the fact the user actually wants to remember? The **user's** call — never decide it for them.

**Governing rule: never change _what_ a card tests without asking. Only improve _how_ it tests it — unless the user invites a re-aim or a delete.** An isolated date, a capital, or a citation is a *target the user chose*, not a defect.

**Construction rubric (T0–T3)** — adapted from [memory-machines.com/report](https://memory-machines.com/report). Grade *how well the card cues its chosen target*:
- **T3 — ready.** Reliably cues the *same* answer after long gaps. Concrete, compact, one unambiguous answer.
- **T2 — needs polish.** Right target, but wordy / high-friction. Tighten it.
- **T1 — needs refactor (the dangerous one).** Plausible-looking but ambiguous — *several* answers fit — so it drifts over months. **Insidious:** invisible until much attention is wasted. Most genuinely bad cards in a mature collection are T1.
- **T0 — off-target.** Looks like it may test the wrong detail — but "wrong" is a claim about the user's intent. **Don't assign T0 unilaterally; surface it as a question** (see *Preference discovery*).

**Fixing construction (keeps the target):**
- **T1** → pin the answer to exactly one: add scope/setup/units as *givens* in the front, without telegraphing it (e.g. a vague "when did X *begin*?" — where several dates defensibly qualify — becomes a specific, datable event the user actually has in mind).
- **T2** → cut to the load-bearing idea; **split bundled answers** into separate cards (e.g. author | year, when the user struggles to recall both at once).
- For an arbitrary fact the user *wants* to keep (a date, a name, a number) → don't reword the target; **add a memory hook** (see below).

**Generative phrasing** helps when the goal is *conceptual mastery* — ask the learner to *produce* the idea rather than recognise a name (not "name of the base built from a countable dense set?" but "Given a countable dense set, how do you build a countable base?" → "rational-radius balls"). It is **not** a mandate to convert every atomic-fact card; capitals and dates are legitimate targets.

### Memory aids for atomic facts

When the user wants to keep an arbitrary fact that resists understanding-based recall, help them *encode* it — don't reword the question. Offer 1–2 options and let them pick; never force a contrived peg:
- **Co-dated / co-located anchor** — tie the value to a well-known event the user already associates with that year (a famous invention, war, birth, or premiere from the same year).
- **Vivid image or story** linking the cue to the answer.
- **Number techniques** (number-shape, Major System) for dates and figures.
- **Linking** a bundled answer (split author | year, or anchor the year to the author).

The original question stays put; the hook lives in the answer, a hint field, or the annotation field.

### Core Principles

### Core Principles

1. **Atomicity** — One card = one fact. If the back contains two facts, split into two cards. Don't pad the back with detail.
2. **Univocality** — Every front must admit exactly one correct answer. If a tired learner at 11pm could give two correct-but-different answers, **rewrite the front** to narrow the answer space (add scope, units, timeframe, context) — without giving away the answer.
3. **Multiple angles without redundancy** — Forward/reverse, rule/example, definition/application are good; literal duplicates are not.

### Card Writing Rules

1. **Match the user's card style.** If they use cloze, keep cloze; if Basic, keep Basic. Don't convert card types unless asked. (Check `card_style` in their saved conventions.)
2. **No yes/no answers.** Rephrase to ask for the fact directly.
3. **Lists must be split.** One item per card. Never "Name 3 things..." as a single card.
4. **Acronyms get their own card** asking what they stand for.
5. **Avoid vague prompts.** Never "What is X?", "Explain...", "Discuss...", "Describe...". Prefer **What / Which / When / Where / Define** with enough constraint to pin down a unique answer.
6. **Avoid "advantages/benefits/reasons"** unless constrained to one canonical answer (e.g., "primary mechanism").
7. **Back-length test:** if the back exceeds ~15 words, can it split into two cards? If not, find a shorter phrasing.
8. **Use a disambiguation field** (e.g. a Context/Extra field) for brief cues — without giving away the answer.

### Examples

**Bad:** "What is an advantage of cloud computing?"
**Better:** "Which pricing model shifts CapEx to OpEx?" → "Pay-as-you-go."

**Bad:** "Explain how L2 regularization reduces overfitting."
**Better:** "What is the mechanism by which L2 reduces overfitting?" → "It shrinks the weights, lowering variance."

**Bad:** "Threshold for severe anemia?"
**Better:** "What is the severe anemia threshold (g/dL) for adult non-pregnant females?" → "<8 g/dL."

---

## Operations Reference

### 1. Search

    anki('findCards', query='is:suspended')
    anki('findCards', query='tag:leech')
    anki('findCards', query='-tag:marked')                 # NOT tagged
    anki('findCards', query='deck:"My Deck"')              # quote names with spaces
    anki('findCards', query='"note:Basic (and reversed card)"')
    anki('findCards', query='"mitochondria"')              # full-text
    anki('findCards', query='added:7')                     # added in last 7 days
    anki('findCards', query='rated:3')                     # reviewed in last 3 days
    anki('findCards', query='prop:lapses>=8')              # leeches
    anki('findCards', query='prop:ivl<7')                  # interval under 7 days
    anki('findCards', query='is:suspended tag:leech deck:"Biology"')   # combine

### 2. Read card content

`cardsInfo` returns card-level data where `note` is an **integer** (the note ID), not a nested object. Get tags via a separate `notesInfo` call.

    card_ids = anki('findCards', query='is:suspended')
    cards = anki('cardsInfo', cards=card_ids)

    import re
    def strip_html(s): return re.sub(r'<[^>]+>', '', s).strip()

    for c in cards:
        print(f"Card {c['cardId']} | {c['modelName']} | {c['deckName']} | lapses={c.get('lapses',0)}")
        for fname, fdata in c['fields'].items():
            val = strip_html(fdata['value'])
            if val: print(f"  {fname}: {val[:200]}")

    note_ids = list({c['note'] for c in cards})
    tags_by_note = {n['noteId']: n['tags'] for n in anki('notesInfo', notes=note_ids)}

### 3. Edit / rewrite fields

Use `updateNoteFields` with the **note ID**. Only include fields you want to change.

    cards = anki('cardsInfo', cards=[card_id])
    note_id = cards[0]['note']
    anki('updateNoteFields', note={'id': note_id,
        'fields': {'Front': 'New question', 'Back': 'New answer'}})

For cloze, edit the cloze field with `{{c1::answer::hint}}` syntax.

### 4. Tags

    anki('addTags', notes=[note_id_1, note_id_2], tags='reviewed rewritten')
    anki('removeTags', notes=[note_id], tags='leech')

### 5. Suspend / unsuspend (take **card IDs**)

    anki('suspend', cards=[card_id])
    anki('unsuspend', cards=[card_id_1, card_id_2])

### 6. Delete notes — **permanent.** Show what will be deleted and confirm first.

    anki('deleteNotes', notes=[note_id])

### 7. Move decks · 8. Create · 9. Filtered deck · 10. Batch

    anki('changeDeck', cards=[card_id], deck='New Deck')
    anki('addNote', note={'deckName': 'My Deck', 'modelName': 'Basic',
        'fields': {'Front': 'Q', 'Back': 'A'}, 'tags': ['my-tag']})
    # Make a study deck of exactly the weak cards (does NOT reschedule existing cards):
    anki('createFilteredDeck', name='Fix these', search='tag:to-fix', ...)  # check params for your AnkiConnect version
    # Atomic multi-action:
    anki('multi', actions=[
        {'action': 'unsuspend', 'params': {'cards': [id1, id2]}},
        {'action': 'addTags', 'params': {'notes': [nid1, nid2], 'tags': 'reviewed'}}])

---

## Card ID vs Note ID — when to use which

A **note** is the content (fields + tags). A **card** is a review item generated from a note; one note can make several cards (e.g. a reversed card). This is the #1 source of errors.

| Operation | Takes |
| --- | --- |
| `findCards`, `cardsInfo`, `suspend`/`unsuspend`, `changeDeck` | **card IDs** |
| `updateNoteFields`, `deleteNotes`, `addTags`/`removeTags`, `notesInfo` | **note IDs** |

Go from card to note: `note_id = anki('cardsInfo', cards=[card_id])[0]['note']`

---

## Externally-authored cards (sync safety)

If the user authors cards outside Anki and syncs them in (most commonly the **obsidian-to-anki** plugin, which stamps `<!--ID: 1712345678901-->` into the source file), **the source file is the source of truth.** Editing such a card in Anki is silently overwritten on the next sync.

- Detect: a note is externally-managed iff its ID appears in the source files —
  `grep -rl "<!--ID: <NOTE_ID>" "<source_dir>"`
- **Match** → edit the source file, then ask the user to re-run their sync. **Never** `updateNoteFields`.
- **No match** → Anki-native; safe to edit directly.

Most users have no external source — the check simply finds nothing and editing proceeds normally. Only run it if the user's saved conventions list an `external_source`, or they mention Obsidian/external authoring.

---

## Triage workflow

When asked to triage cards (suspended, leeches, the high-trouble list):

1. **Survey** — find and group the target cards by deck/note-type; show a summary count.
2. **Review in batches** of 5–10. For each: front, back, tags, deck/type, and lapse count (`c['lapses']`).
3. **Recommend** one of: **Unsuspend** (fine) · **Rewrite + unsuspend** (poorly worded → improve, then return) · **Delete** (redundant/unfixable) · **Keep suspended** (decide later).
4. **Execute** the user's decisions. Confirm before any deletion.

---

## Tips

- **HTML in fields:** content often contains HTML (`<br>`, `<b>`, `<img>`). Strip for display; preserve when editing unless reformatting.
- **Cloze numbering:** `{{c1::...}}` and `{{c2::...}}` create separate cards from one note — don't merge or renumber accidentally.
- **FSRS vs SM-2:** newer collections use FSRS, where the legacy ease `factor` may be 0. Lapse-based signals (lapse_rate, lapses/day, leeches) always work; treat `ease_erosion` as optional and prefer FSRS `difficulty`/`retrievability` if you fetch them.
- **Large collections:** use targeted queries, batch `cardsInfo` (~100–300 at a time), and page in Python (`ids[:50]`) rather than fetching everything.
- **Targeting:** rank by our **trouble score** — the worst ~5% are "costly" and always worth a deliberate call. Anki's own `tag:leech` / `prop:lapses>=8` is a coarser, separate signal: useful, but the trouble score is the skill's primary lens.
- **Sync reminder:** after changes, suggest the user sync (`Cmd+Shift+Y`, or Tools → Sync) if they use AnkiWeb.
