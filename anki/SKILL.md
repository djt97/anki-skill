---
name: anki
description: Searches, reviews, triages, and safely rewrites a user's Anki cards through AnkiConnect without changing scheduling. Runs collection health checks, identifies costly cards, and learns the user's flags, tags, fields, external-source conventions, and card-writing preferences. Use when the user mentions Anki or AnkiConnect, asks about an Anki deck or collection, or requests work on suspended cards, leeches, lapses, Anki card rewrites, or collection health. Do not use for unrelated generic flashcard advice.
compatibility: Requires local Anki Desktop with AnkiConnect reachable at 127.0.0.1:8765.
---

# Anki collection assistant

Use AnkiConnect to inspect and improve the user's Anki collection. Treat this file as the control plane: keep its safety rules active, and load the detailed references only when the current task needs them.

## Non-negotiable rules

1. **Preview every mutation and obtain explicit approval.** Read-only inspection may proceed after the user's request, but do not modify Anki, an external source file, or `conventions.local.md` until the user has seen the exact proposed operation and clearly approved it. Silence is not consent. Approval applies only to the displayed batch.
2. **Never touch scheduling.** Do not change intervals, ease, due dates, learning state, review history, deck scheduling options, or FSRS parameters, and do not answer cards or run a rescheduler. Suspension and unsuspension are allowed only after approval. A filtered-deck workflow must have rescheduling disabled.
3. **Separate construction from target.** Assess whether a card reliably cues its chosen answer. Never decide what the user should remember, re-aim a card, suspend it permanently, or delete it without the user's decision.
4. **Find weaknesses, not missing knowledge.** Collection data can reveal weak, redundant, confusable, costly, or poorly worded cards. Do not claim to detect syllabus gaps without a syllabus or another source defining expected coverage.
5. **Adapt instead of assuming.** Do not assign meanings to flags, tags, suspension, fields, or card styles until the user's conventions have been loaded or discovered and confirmed.
6. **Respect the source of truth.** If a note is externally authored, edit the external source only; never update the Anki note directly. If it is Anki-native, edit Anki only. Confirm the route before proposing a write.
7. **Use Anki terminology.** Say lapses, leeches, intervals, ease, retrievability, difficulty, and stability where applicable. Do not invent marketing-style metrics. Clearly label the skill's own `trouble`, `weakness`, and `confidence` scores as custom diagnostics.
8. **Keep one dependency.** Use AnkiConnect and Python's standard library only. Do not install databases, packages, or other services.

## Interaction rules

- Use the host's structured multiple-choice or question interface whenever it is available.
- If the host has no clickable-choice interface, present a short numbered list and ask the user to reply with a number. Use free text for “something else” or when choices would be artificial.
- Offer choices rather than forcing a path. The user may stop, skip, or jump to a different task at any decision point.
- Keep guided steps short and end each one with a clear next choice.

## Skill state

Set `SKILL_ROOT` to the directory containing this `SKILL.md`. The state file is:

```text
SKILL_ROOT/conventions.local.md
```

Load it when present. Do not hard-code a Claude- or Codex-specific installation path. Before creating or updating it, show the proposed contents or diff and obtain explicit approval. If the directory is not writable, keep the confirmed conventions in the current session and explain that they were not persisted.

## Route the request

### Specific request

When the user asks for a specific result—such as showing suspended cards, searching for a topic, counting cards, reviewing a named deck, or rewriting a particular card—do that task rather than forcing the full guided flow.

1. Read [references/ankiconnect.md](references/ankiconnect.md), then verify connectivity.
2. Load saved conventions when relevant.
3. Load only the task-specific references listed below.
4. If the request depends on an unknown convention, perform only the relevant discovery, confirm the inference, and continue.
5. For any mutation, use the approval workflow below.

### Bare invocation or general request

For a bare invocation, “help me with my flashcards,” or another general request, drive this sequence yourself:

1. **Connect.** Verify AnkiConnect. If unavailable, explain that Anki must be running with AnkiConnect installed, then stop.
2. **Conventions.** Load `conventions.local.md`. If it does not exist, run the discovery in [references/conventions.md](references/conventions.md), confirm the inferences, and offer to save them.
3. **Health check.** Run [references/health-check.md](references/health-check.md): explain what the collection is about, where trouble concentrates, and which cards are costliest.
4. **Calibrate.** If no saved `preferences` exist, run the preference interview in [references/fixing-and-triage.md](references/fixing-and-triage.md). Offer to save the resulting profile; do not write it without approval.
5. **Hand back and stop.** Do not begin fixing cards. Reassure the user that nothing will change without explicit approval, then ask where they want to start. Offer choices such as the costliest cards, a deck or note type, or their confirmed review-flag queue.

On later general invocations, skip discovery and calibration that are already saved, run the health check, and perform the same hand-back.

## Approval workflow for every mutation

1. **Inspect.** Read the current card, its note, all sibling cards generated by that note, tags, deck, note type, lapse signals, and the annotation field if one is configured.
2. **Resolve the destination.** Check whether the note is Anki-native or externally authored.
3. **Propose a batch.** Show 1–4 proposed edits at once; use one card for a heavy rewrite. For each item, show:
   - card and note identifiers for traceability;
   - current Front/Back or affected fields, tags, deck, and relevant trouble signals;
   - the exact before/after change or operation;
   - all sibling cards or files that will be affected;
   - the reason for the recommendation and its T0–T3 construction grade;
   - **⚠ confirm** beside any factual content not verified against the user's source.
4. **Stop for approval.** Let the user approve all, some, none, or revised versions. Do not write yet.
5. **Apply only approved items.** Use the source-of-truth route. Do not add a “changed” tag unless the user has approved the exact tag; otherwise skip tagging.
6. **Verify.** Re-read each changed note or source file and report whether the applied content exactly matches the approved preview. For `multi`, inspect every sub-result because batching is not transactional.
7. **Finish.** Summarise what changed and what did not. Suggest a manual AnkiWeb sync when appropriate; never trigger sync without explicit approval.

Deletion requires a separate, explicit confirmation after showing every card generated by the note. Re-aiming a target also requires a separate, explicit choice.

## Load the relevant reference

- **Connection, API calls, IDs, search syntax, external sources, mutation hazards:** [references/ankiconnect.md](references/ankiconnect.md)
- **Discover and save flags, tags, fields, external-source rules, and style:** [references/conventions.md](references/conventions.md)
- **Collection orientation, trouble scoring, hotspots, and content scan:** [references/health-check.md](references/health-check.md)
- **Preference discovery, costly-card decisions, fix batches, and triage:** [references/fixing-and-triage.md](references/fixing-and-triage.md)
- **T0–T3 rubric and card-writing rules:** [references/card-writing.md](references/card-writing.md)

Use the bundled read-only scripts where their reference says to run them. Execute utility scripts rather than copying their source into the conversation.
