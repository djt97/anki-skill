# Anki Skill for Claude Code

> **Talk to your flashcards.** Find the cards quietly costing you the most reviews — and fix them, with your approval at every step.

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill that connects to [Anki](https://apps.ankiweb.net/) via the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on. Type `/anki` and it runs a health check on your collection, learns how *you* organise it, and helps you fix your worst cards one small batch at a time — **never changing anything without your say-so.**

## What it does

- **Health check** — what your collection is about, where your lapses concentrate, and the cards draining the most review time (by a custom "trouble" score, not Anki's blunt 8-lapse leech rule).
- **Learns your conventions** — works out what your flags and tags mean, and which field you use for notes-to-self, instead of assuming.
- **Asks your preferences** — a quick one-time interview: for each *type* of struggling card, do you want it rewritten, given a memory hook, split, or deleted?
- **Fixes collaboratively** — proposes edits in small batches and applies only what you approve. It also flags any fact it isn't sure of, so it won't quietly hallucinate into your deck.

## Requirements

- **Anki**, running, with the **AnkiConnect** add-on (add-on code `2055492159`).
- **Claude Code** (or Codex — see below).

## Install (Claude Code)

Paste this into Claude Code:

> Install the Anki skill from `https://github.com/djt97/anki-skill`: download the raw `SKILL.md` and save it to `~/.claude/skills/anki/SKILL.md`.

Or, in a terminal:

```bash
mkdir -p ~/.claude/skills/anki && \
curl -fsSL https://raw.githubusercontent.com/djt97/anki-skill/main/SKILL.md \
  -o ~/.claude/skills/anki/SKILL.md
```

Then open Claude Code with Anki running and type:

```
/anki
```

## Install (Codex — experimental)

The same `SKILL.md` is intended to work as a Codex skill (invoked with `$anki`). The install location/command differs from Claude Code — **this path is still being verified**; check back or open an issue.

## Usage

Just type `/anki`. It walks itself through: connect → discover your conventions → health check → a short preferences interview → then it **hands back and asks where you'd like to start.** Nothing is written to your deck until you've seen it and said yes.

You can also ask for specific things directly, e.g. `/anki show me my most-lapsed cards`, `/anki find duplicates in my Biology deck`, `/anki rewrite this card`.

## The "trouble" metric

Cards are ranked by:

```
trouble = 0.35·(lapse rate) + 0.25·(ease drop) + 0.20·(relative time) + 0.20·(mature failure)
```

— so a card you keep failing, that takes you ages, or that you flunk *despite* a long interval surfaces early, instead of after you've already wasted weeks on it. Weights are a sensible default you can tune.

## Safety

The skill is under strict instructions to **never change a card or a file without showing you the proposed edit first and getting your explicit approval.** Discovery and analysis never slide into editing on their own.

## Credits

- The card-quality tiers (T0–T3) used when rewriting are adapted from the framework at [memory-machines.com/report](https://memory-machines.com/report).
- Background and a walkthrough: [Cleaning up your Anki deck with Claude Code](https://djt97.github.io/).

## License

[MIT](LICENSE).
