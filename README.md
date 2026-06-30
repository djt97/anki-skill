# Anki Skill — for Claude Code & Codex

> **Clean up your flashcards.** Find the cards that are eating up your review time, and fix them.

This skill lets [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [Codex](https://developers.openai.com/codex) talk to your local [Anki](https://apps.ankiweb.net/) collection via the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on. Almost all other Anki skills for LLMs are built around generating cards. The problem is that [LLMs are reliably bad at this](https://memory-machines.com/). This skill is instead built around fixing bad cards.

Type `/anki` (or `$anki` in Codex), and the LLM runs a health check on your deck, identifies the cards costing you the most reviews/time (using a custom metric), and helps you fix them. It won't change anything in your collection without your explicit approval.

Everything after this point is AI-generated.

## Install

The easy way: open a fresh chat in Claude Code or Codex, and simply paste
```bash
Install this skill: https://github.com/djt97/anki-skill
```
Both are capable of cloning the repo and copying the `anki/` folder into the right place on their own.

If you want to do it manually:

**Claude Code**

```bash
git clone https://github.com/djt97/anki-skill.git
cp -R anki-skill/anki ~/.claude/skills/anki
```

Then, with Anki running, start Claude Code and type `/anki`.

**Codex**

```bash
git clone https://github.com/djt97/anki-skill.git
# copy the anki/ folder into Codex's skills directory, then invoke with $anki
```

`anki/agents/openai.yaml` carries Codex invocation metadata.

> The skill is the self-contained **`anki/`** folder — `SKILL.md` plus its `references/` and read-only `scripts/`. Installing means dropping that whole folder into your agent's skills directory.

## Requirements

- **Anki**, running, with the **AnkiConnect** add-on (add-on code `2055492159`).
- **Claude Code** or **Codex**.

## What it does

- **Health check** — what your collection is about, where your lapses concentrate, and the cards draining the most review time (a custom "cost" score, not Anki's blunt 8-lapse leech rule).
- **Learns your conventions** — works out what your flags and tags mean, and which field you use for notes-to-self, instead of assuming.
- **Asks your preferences** — a quick one-time interview: for each *type* of struggling card, rewrite it, give it a memory hook, split it, or delete it?
- **Fixes collaboratively** — proposes edits in small batches, applies only what you approve, and flags any fact it hasn't verified against your source.

## Safety

The skill's first rule is to **never change a card, a source file, or its own saved state without showing you the exact change first and getting your explicit approval.** It also never touches Anki's scheduling (intervals, ease, due dates, or FSRS parameters).

## The cost metric

```
cost = lapse_rate / interval        (lapse_rate = lapses / reviews)
```

A card surfaces when you keep *failing* it and FSRS keeps bringing it back on a short interval. The interval is FSRS's own durability verdict, fit to your reviews, so the skill leans on it instead of reinventing difficulty. A card you never fail scores zero, so reset or imported cards with no real lapse history don't clutter the list. Full definitions are in [`anki/references/health-check.md`](anki/references/health-check.md).

## Credits

- The card-quality tiers (T0–T3) used when rewriting are adapted from the framework at [memory-machines.com/report](https://memory-machines.com/report).
- Background and a walkthrough: [Cleaning up your Anki deck with Claude Code](https://djthornton.org/blog/2026/clean-up-your-flashcards/).

## License

[MIT](LICENSE).
