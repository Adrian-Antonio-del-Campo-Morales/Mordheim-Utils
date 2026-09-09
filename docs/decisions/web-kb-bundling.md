# Decision: bundling the KB artefact for the web app

**Status:** accepted (Agent A, 2026-09-09) — coordination entry in
`web-rework-parallel-log.md` (update 10). Affects Agent B's P5.2 fake
knowledge reader and any P8 CI work.

## Context

P5.2 still uses a fake `KnowledgeReader` because nobody decided how
`build/generated/knowledge-web/knowledge-web.json` reaches the browser.
P7.5 (this thread) measured the artefact and pin the budget; the numbers
settle the decision.

## Measurements (ruleset `mordheim`, 2026-09-09)

| metric | value |
|---|---|
| raw JSON | 2 176 kB (2.12 MB) |
| gzip -9 | **209 kB** |
| index build from parsed JSON | < 50 ms (budget 2 s) |
| app bundle today (without KB) | 240 kB → 75 kB gzip |

Delivery budget pinned by `tests/web/test_kb_artefact_performance.py`:
**< 300 kB gzip**.

## Decision

1. **Ship the artefact as a separate static asset**, not a JS module:
   copy it into the app's `public/knowledge/knowledge-web.json` at build
   time and `fetch()` it once at startup. Reasons:
   - 209 kB gzip would otherwise **triple** the JS bundle (JSON parses
     faster than JS evaluates a 2 MB object literal, and Vite would inline
     it into the main chunk);
   - browsers cache the asset across deploys of the app code;
   - `KnowledgeReaderError` on fetch failure maps cleanly to the existing
     error panel — the slice already renders reader failures.
2. **No partitioning for now.** 209 kB gzip is within budget with headroom;
   per-collection splitting adds a loader state machine for no user-visible
   win. Revisit only if the budget test starts failing (the test message
   says exactly that).
3. **Load path:** `createArtefactKnowledgeReaderFromUrl(url)` should wrap
   Agent A's P4.3 `ArtefactKnowledgeReader.from()` with a `fetch` + one
   validation pass; the app shows a KB loading state until resolved. The
   `KnowledgeReader` port is unchanged — this is a new adapter constructor,
   not a contract change.
4. **P8.1 (CI) must run `python tools/knowledge/generate_knowledge_web.py
   --check` and copy the artefact to `public/knowledge/` before
   `npm run build`.** The artefact stays gitignored (generated, 2 MB).

## What this unblocks

Agent B: swap the fake knowledge reader in `default-deps.ts` for the URL
constructor above and P5.2's acceptance is fully met (display with *real*
resolved ids). Nothing else changes.
