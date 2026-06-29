# Anki Skill — for Claude Code & Codex

> **Talk to your flashcards.** Find the cards quietly costing you the most reviews — and fix them, with your approval at every step.

A skill that connects an AI coding agent ([Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [Codex](https://developers.openai.com/codex)) to your local [Anki](https://apps.ankiweb.net/) collection via the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on. Type `/anki` (or `$anki` in Codex) and it runs a health check, learns how *you* organise your deck, and helps you fix your worst cards one small batch at a time — **never changing anything without your approval.**

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

- **Health check** — what your collection is about, where your lapses concentrate, and the cards draining the most review time (a custom "trouble" score, not Anki's blunt 8-lapse leech rule).
- **Learns your conventions** — works out what your flags and tags mean, and which field you use for notes-to-self, instead of assuming.
- **Asks your preferences** — a quick one-time interview: for each *type* of struggling card, rewrite it, give it a memory hook, split it, or delete it?
- **Fixes collaboratively** — proposes edits in small batches, applies only what you approve, and flags any fact it hasn't verified against your source.

## Safety

The skill's first rule is to **never change a card, a source file, or its own saved state without showing you the exact change first and getting your explicit approval.** It also never touches Anki's scheduling (intervals, ease, due dates, or FSRS parameters).

## The "trouble" metric

```
trouble = 0.35·(lapse rate) + 0.25·(ease drop) + 0.20·(relative time) + 0.20·(mature failure)
```

— so a card you keep failing, take ages on, or flunk *despite* a long interval surfaces early, instead of after you've already wasted weeks on it. Full definitions are in [`anki/references/health-check.md`](anki/references/health-check.md).

## Credits

- The card-quality tiers (T0–T3) used when rewriting are adapted from the framework at [memory-machines.com/report](https://memory-machines.com/report).
- Background and a walkthrough: [Cleaning up your Anki deck with Claude Code](https://djthornton.org/blog/2026/clean-up-your-flashcards/).

## License

[MIT](LICENSE).
