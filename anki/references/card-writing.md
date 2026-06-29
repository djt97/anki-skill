# Flashcard writing principles

## Contents

- Keep construction and target separate
- Construction rubric: T0–T3
- Construction fixes that keep the target
- Memory aids for atomic facts
- Core principles
- Card-writing rules
- Examples

Follow these principles when creating or rewriting cards. They govern card construction; they do not decide what the user should remember.

## Keep construction and target separate

Two judgments must remain distinct:

- **Construction:** Does the card cue one stable answer over long horizons? Assess this.
- **Target or worth:** Is this fact worth remembering? The user decides this.

**Governing rule:** Never change what a card tests without asking. Improve how it tests that target unless the user explicitly chooses a re-aim or deletion.

An isolated date, capital, citation, name, or number may be exactly the target the user wants. Its arbitrariness is not proof that the target is defective.

## Construction rubric: T0–T3

Use this rubric, adapted from [memory-machines.com/report](https://memory-machines.com/report), to grade how reliably a card cues its chosen target.

### T3 — ready

The prompt reliably cues the same answer after a long gap. It is concrete, compact, and has one unambiguous answer.

Recommendation: keep it unless the user wants an encoding aid or a different target.

### T2 — needs polish

The target is right, but the card is wordy or high-friction.

Recommendation: tighten it without changing the target. If the answer bundles separately recallable facts, offer a split.

### T1 — needs refactor

The prompt looks plausible but several answers fit. It may drift over months because the cue is not univocal.

Recommendation: add scope, setup, units, timeframe, or context as givens on the front without telegraphing the answer.

Example pattern:

- Vague: “When did X begin?”
- Better: name the specific datable event the user actually means, then ask for its date.

### T0 — possible target mismatch

The card may test the wrong detail relative to the user's intent.

Do not assign T0 as a unilateral verdict. Surface it as a question. A target mismatch cannot be established from construction alone.

## Construction fixes that keep the target

- **T1:** Narrow the answer space until exactly one answer fits.
- **T2:** Remove nonessential wording and split independent targets.
- **Atomic but arbitrary fact:** Keep the question and offer a memory hook rather than rewording the target away.
- **Conceptual mastery:** Prefer generative phrasing that asks the learner to produce the mechanism, rule, or construction.

Generative phrasing is useful when the target is conceptual. It is not a mandate to convert every atomic-fact card. Dates, capitals, citations, and names can be legitimate targets.

## Memory aids for atomic facts

When the user wants to keep an arbitrary fact that resists understanding-based recall, offer one or two optional encoding aids. Do not force a contrived mnemonic.

Suitable techniques include:

- **Co-dated or co-located anchor:** Tie the value to a familiar event or place the user already associates with it.
- **Vivid image or story:** Link the cue and answer with a distinctive image.
- **Number techniques:** Use number-shape or Major System encoding for dates and figures.
- **Linking:** Connect parts of a bundled fact, such as author and year, while still offering a split where each part should be independently recalled.

Keep the original question. Put the hook in the answer, a hint field, or the confirmed annotation field, according to the user's preference and note structure.

## Core principles

1. **Atomicity:** One card tests one fact. Split independently recallable facts rather than padding the back.
2. **Univocality:** The front admits exactly one correct answer. If a tired learner could give two different but defensible answers, narrow the prompt without giving the answer away.
3. **Multiple angles without redundancy:** Forward/reverse, rule/example, and definition/application pairs may be useful; literal duplicates are not.

## Card-writing rules

1. **Match the user's style.** Preserve Basic, cloze, or mixed conventions. Do not convert note types unless asked.
2. **Avoid yes/no answers.** Ask directly for the fact.
3. **Split lists.** Do not keep “Name three…” as one card when each item is independently recallable.
4. **Give acronyms their own card.** Ask what the acronym stands for.
5. **Avoid vague prompts.** Do not use bare “What is X?”, “Explain…”, “Discuss…”, or “Describe…”. Prefer What, Which, When, Where, or Define with enough constraint to identify one answer.
6. **Constrain advantages, benefits, and reasons.** Ask for one canonical mechanism or explicitly scoped answer.
7. **Use the back-length test.** If a back exceeds about 15 words, ask whether it can become two cards. If not, seek a shorter expression without deleting needed meaning.
8. **Use a disambiguation field when available.** Put brief context in a Context or Extra field without giving away the answer.
9. **Preserve source and media structure.** Do not lose HTML, images, audio, MathJax, or unrelated fields.
10. **Preserve cloze numbering.** Do not merge or renumber `c1`, `c2`, and later clozes accidentally.

The 15-word test is a heuristic, not permission to remove a definition's load-bearing content. When concision and correctness conflict, keep the necessary meaning and ask the user whether a split is better.

## Examples

### Ambiguous advantage

**Poor:** “What is an advantage of cloud computing?”

**Better:** “Which cloud pricing model shifts capital expenditure to operating expenditure?”  
**Answer:** “Pay-as-you-go.”

### Mechanism rather than essay

**Poor:** “Explain how L2 regularization reduces overfitting.”

**Better:** “By what mechanism does L2 regularization reduce overfitting?”  
**Answer:** “It shrinks the weights, lowering variance.”

### Add scope and units

**Poor:** “Threshold for severe anemia?”

**Better:** “What is the severe-anemia threshold in g/dL for adult non-pregnant females?”  
**Answer:** “<8 g/dL.”

Treat example facts as illustrations of construction only. Do not reuse their content in a user's cards, and mark any unverified factual rewrite **⚠ confirm**.
