# Web Test Migration — coordination log

Shared log for the 3 agents running the web test migration plan
(`web-test-migration-plan.md`). Append entries at the top; never delete
another agent's entry. Claim a task before touching files. Shared tree:
check `git status` first, only edit files you own.

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
