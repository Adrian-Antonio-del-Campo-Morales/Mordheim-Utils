# Web Test Migration — coordination log

Shared log for the 3 agents running the web test migration plan
(`web-test-migration-plan.md`). Append entries at the top; never delete
another agent's entry. Claim a task before touching files. Shared tree:
check `git status` first, only edit files you own.

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
