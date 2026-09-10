# Web Test Migration — coordination log

Shared log for the 3 agents running the web test migration plan
(`web-test-migration-plan.md`). Append entries at the top; never delete
another agent's entry. Claim a task before touching files. Shared tree:
check `git status` first, only edit files you own.

---

## 2026-09-10 — REPO REWORK 2: UI parity block 1 delivered + 2 product findings

**Delivered:** `apps/warband-manager-web/src/features/campaign/parity-gui-regressions.test.tsx`
(3 tests, all green, T1-verified). Ported from desktop
`tests/campaign/test_gui_interaction_regressions.py` (unsaved-guard family):
1. navigation never dirties the document;
2. export → reimport round-trips the campaign verbatim and lands clean;
3. dismissing the replace alert keeps the loaded campaign (cancelled-load
   branch).

**Product findings for 333333 (their files — not fixed by me):**
1. `EquipmentPanel`/`HirelingsPanel` (and likely all feature panels) call
   `useCampaignApp()` internally — a **separate service instance** from the
   slice's. Panel edits dirty the panel's own service; the slice's document
   and dirty indicator never update. Verified by probe: `service.run(
   "assignEquipment")` sets `isDirty()=true` at service level, but the slice
   shows nothing. Desktop analogue (`test_dirty_includes_battle_draft...`)
   cannot be ported until this is resolved.
2. `CampaignSlice` rename form dispatches action `__rename_warband__`, which
   is not registered in `service.run` — result: `Unknown action
   "__rename_warband__"`. The P5.2 "sample edit" path is currently broken
   against the real service.

Suggested fix for (1): panels receive the service (or a `runAction` prop)
from the slice instead of building their own — same pattern as
`TimelinePanel`'s `onSelect` prop.

My next: UI parity block 2 (file-input focus/a11y surface, error-message
quality assertions from the desktop guard family) — unchanged ownership.

---

## 2026-09-10 — Agent 0: **MATRIX DELIVERED** (`c0a495d`) — substrate ready

- `tools/make_test_manifest.py` — regenerable, deterministic. Enumerates
  via `pytest --collect-only`, classifies per file family. Current split:
  **M=1071, U=63, I=21, S=48, X=6 (PDF, reason documented), total 1209**.
  Note: 1209 not 1172 — live collection grew between sync passes (Agent A's
  desktop-side? no — parametrize expansion); gates pin total == live.
- Gates bilingual: `tests/web/parity/python_manifest_test.py` (7: regen
  identity, live-match, completeness, exclusion reasons, dupes) +
  `packages/typescript/parity-manifest.test.ts` (6: structural mirror).
  Sort comparison is code-unit (Python byte order), NOT localeCompare.
- **A (REPO REWORK 2)**: your 63 U rows map to
  `apps/warband-manager-web/src/features/campaign/<family>.test.tsx` —
  family = file basename minus `test_`/`_regressions`/`_matrix` suffixes.
  Saw your block-1 commit `29cf5fe` — rename your test files to the family
  convention or tell me the mapping and I update the generator.
- **333333**: your 1071 M rows target
  `packages/typescript/domain/campaign/<family>.test.ts`.
- **222222**: lane taken per deadline; reclaim per protocol if you land
  first. Hand-refinement passes of ambiguous rows open to anyone with a
  claim entry.

---

## 2026-09-10 — Agent 0: **TAKEOVER — matrix + vectors lane** (deadline met)

Per the deadline in my previous entry: 222222 has no claim, no artifacts,
empty thread activity across two sync passes. Taking the lane per the R3
precedent (claimant with landed work wins; 222222 may reclaim on arrival —
any uncommitted files of theirs win, mine yield).

**Claimed (exclusive until delivered):**
- `tests/web/parity/**` (manifest, gates, fixtures)
- `tools/make_test_manifest.py` (regenerable matrix generator, repo
  convention like `tools/make_v4_fixtures.py`)

**Method:** programmatic enumeration via `pytest --collect-only` (1172
cases), rule-based classification per file family with per-test overrides
(tkinter/PDF/combat exclusions detected by pattern). Gates in both
languages assert completeness: no desktop test without disposition, no web
target without source, no exclusion without reason. Hand refinement of
ambiguous rows follows in later passes — manifest is the substrate, not
the final word.

---

## 2026-09-10 — Agent 0: sync pass — 222222 silent; matrix deadline set; real counts for matrix owner

- **No `tests/web/parity/` yet, no claim entry from 222222** in this log or
  the older R3 log. Thread may be stalled (same failure mode as Agent A's
  session during the R3 merge). **Deadline: if no claim from 222222 by next
  sync pass, Agent 0 takes the matrix + vectors lane** (same protocol as
  the duplicated T3 claim in R3: claimant with landed work wins).
- **Data for the matrix owner (read-only T0, corrects plan estimate):**
  `tests/campaign` = **25 files, 1172 collected tests** (plan said ~296 —
  parametrized cases and v4/R3 additions grew it). `tests/ui` = 10 files.
  Matrix rows will be per test function incl. parametrize IDs.
- My lane idle until manifest lands or I take over the matrix. Agent A:
  your 2 untracked UI tests untouched.

---

## 2026-09-10 — Agent 0: I/S verification DONE (bidirectional green)

Executed the plan's interop checks for my lane while the matrix is pending
(all T1/T2 tier, no full nets, no shared artifacts touched):

- **TS contract side** (`adapters/campaign-file` + `domain/campaign`):
  **60/60 passed** (vitest, 634ms).
- **Python mirror of the TS round-trip**
  (`test_p32_roundtrip.py`): artefact present, **3/3 passed** — TS-emitted
  documents load through the desktop v4 reader and are semantically equal
  to the fixtures (modulo `saved_at`/`view`).
- **KB artefact determinism (`S`)**: regenerated via
  `generate_knowledge_web.py --output <tmp>` → **byte-identical** to
  `apps/warband-manager-web/public/knowledge/knowledge-web.json`
  (2315 KB, 81 bands, 534 profiles, 278 items, 75 skills). Note: that file
  is gitignored by design (build-generated, P8.1) — fresh checkouts get it
  from the build pipeline, not git.
- Transient artifacts cleaned; nothing outside my lane touched. Agent A:
  saw `probe-dirty.test.tsx` appear — carry on.

**Still blocked on 222222:** matrix manifest + parity vectors
(`tests/web/parity/`). My I/S vectors land there once it exists.

---

## 2026-09-10 — Agent 0: baseline DONE, hygiene DONE

- **Hygiene:** committed `c7d4d1e` — the missing
  `apps/warband-manager-desktop/mordheim_desktop/__init__.py` is now tracked
  (fresh-clone `import mordheim_desktop` verified, py_compile OK) and the
  transient Cython artifact `_combat_native.c` deleted. Agent A: your
  untracked `parity-gui-regressions.test.tsx` untouched.
- **T0/T2 baseline (my lane):** `tests/web` + `tests/contracts` = **79
  collected, 79 passed** (16.8s, `-p no:cacheprovider`, no full net run).
- **Next for me:** I/S parity runs against 222222's manifest
  (`tests/web/parity/`) as soon as it lands; meanwhile standing by, no
  files owned by others touched.

---

## 2026-09-10 — Agent 0 (4th thread, hygiene + interop lane): claiming hygiene commit, T0 baseline, I/S lane

Synchronizing per user order ("empieza a ejecutar el plan"). Three claims,
verified disjoint from REPO REWORK 2 (UI block), 222222 (matrix/vectors) and
333333 (TS domain):

1. **Hygiene commit (R3 leftovers, unblocks fresh clones):** commit the
   untracked `apps/warband-manager-desktop/mordheim_desktop/__init__.py`
   that `44adb00`'s message announced but did not include (a fresh clone
   would have a broken `mordheim_desktop` package); delete the transient
   Cython artifact
   `packages/python/combat-engine/mordheim_combat/native/_combat_native.c`
   (untracked, never commit). No other files touched.
2. **T0 baseline:** collect-only counts for `tests/web/` +
   `tests/contracts/` (my lane), recorded below after execution.
3. **I/S lane for this migration:** the `I` (Python↔TS interop) and `S`
   (shared KB/contract) test families under `tests/web/` +
   `tests/contracts/` — executed against 222222's vectors once the
   manifest lands; existing interop tests stay green meanwhile.

---

## 2026-09-10 — REPO REWORK 2 (this thread): plan + log created; claiming UI block

**Created:** `web-test-migration-plan.md` (approved plan) and this log.

**Claimed:** Block "UI web y adaptaciones de navegador" (owner: REPO REWORK 2):
`apps/warband-manager-web/src/**/*.test.{ts,tsx}`, web test utilities,
interaction/a11y/responsive tests — 10 sub-blocks listed in the plan §Reparto.

**Waiting on:** REPO REWORK 222222's traceability matrix (block 1/2 of mine
depend on knowing which desktop scenarios map to UI). Meanwhile I will:
1. T0 baseline of existing web tests (collect-only, no full nets).
2. Read `tests/campaign/test_gui_interaction_regressions.py` + `tests/ui/` to
   extract UI-equivalent scenarios already portable without the matrix.

**Never touched:** `packages/typescript/**` (333333), `tests/web/parity/**`
(222222), `tests/campaign/**` (desktop net stays green, T1-only runs).

## Protocol (agreed)

- Claim-first in this log, then edit. One owner per file path family.
- Test tiers T0–T3 per plan §Estrategia; T3 = claimed window, single agent.
- Transient artifacts deleted, never committed.
- No commits outside your ownership.
