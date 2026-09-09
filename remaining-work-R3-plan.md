# R3 execution plan — physical monorepo restructuring (sub-task split)

Companion to [`remaining-work-plan.md`](./remaining-work-plan.md) §R3. Split
into independent, parallelizable sub-tasks, one per target package, following
the plan's recommended strategy: **physical move first, importable namespaces
kept** (zero import rewrites), renames only later if wanted.

Baseline measured 2026-09-09 on `web-repo-rework` (`0767d2c` + merge work):

| Package (current) | Import sites (src+tests+tools) | Target (plan §5) |
| --- | --- | --- |
| `mordheim_core` | 230 | `packages/python/core/` |
| `mordheim_knowledge` | 112 | `packages/python/knowledge/` |
| `mordheim_construction` | 73 | `packages/python/roster-construction/` |
| `mordheim_combat` | 425 | `packages/python/combat-engine/` |
| `mordheim_campaign` | 269 | `packages/python/campaign/` |
| `mordheim_combat_lab` | 285 | `apps/combat-lab/` |
| `mordheim_ui` | 131 | `packages/python/adapters/desktop-ui/` |

Total: 208 files carry `from mordheim_*` imports; ~1.5k import statements.

---

## Coordination rules (parallel execution)

1. **One sub-task = one package move.** Two agents never move the same
   package. Claim each sub-task in
   [`docs/decisions/web-rework-parallel-log.md`](docs/decisions/web-rework-parallel-log.md)
   before touching files.
2. **`pyproject.toml` is a shared file.** Batch its edits: each agent stages
   their `packages.find` entry and reverts nothing else; conflicts resolved
   at the (single) final commit.
3. **Namespaces stay importable.** Move the package directory *and* keep
   `packages.find` able to see it (add `where` entries per location or a
   `package-dir` mapping). Zero import-site rewrites, zero test rewrites.
4. **Regression net after each sub-task:** the moving agent runs
   `python -m pytest tests -q --ignore=tests/ui --ignore=tests/verification
   --ignore=tests/combat` (the established fast net; the two excluded suites
   carry the documented pre-existing failures) plus the TS suites if
   `packages/typescript` is affected (they are not, except S7).
5. **S1 (campaign) and S6 (UI) are coupled** — `mordheim_ui` imports
   `mordheim_campaign` heavily. Sequence them, do not parallelize.

---

## Sub-tasks

### S1 — `mordheim_campaign` → `packages/python/campaign/` *(serial, do second of the pair)*
- Move `src/mordheim_campaign` (incl. `__main__.py`, `app.py`).
- Desktop entry point stays importable: `python -m mordheim_campaign`.
- 269 import sites must keep resolving.

### S2 — `mordheim_core` → `packages/python/core/`
- 230 import sites; leaf dependency of everything else. Good first task.

### S3 — `mordheim_knowledge` → `packages/python/knowledge/`
- 112 import sites; also feeds the KB artefact generator (`tools/knowledge/`).
- Verify the artefact generator still runs after the move.

### S4 — `mordheim_construction` → `packages/python/roster-construction/`
- 73 import sites; smallest fan-out.

### S5 — `mordheim_combat` → `packages/python/combat-engine/`
- 425 import sites; largest. Run the combat suite explicitly after the move
  (it is excluded from the fast net only because of the two pre-existing
  failures — the failures themselves must not multiply).

### S6 — `mordheim_ui` → `packages/python/adapters/desktop-ui/` *(serial, do first of the pair with S1)*
- 131 import sites; this is the desktop adapter layer. `tests/ui` must be run
  explicitly (excluded from the fast net).

### S7 — `mordheim_combat_lab` → `apps/combat-lab/`
- 285 import sites; independent app. Keep its importable name for the first
  step; the plan's final shape renames it later, if at all.

### S8 — `contracts/knowledge/` decision + docs
- Decide whether the KB contract directory applies (plan §5 target list);
  if yes, move the JSON Schema(s) there and update references. Zero code.

---

## Recommended parallel schedule

| Step | Agent A | Agent B |
| --- | --- | --- |
| 1 | S2 (core) | S4 (construction) |
| 2 | S3 (knowledge) | S7 (combat-lab) |
| 3 | S6 (ui) → S1 (campaign) | S5 (combat-engine) |
| 4 | S8 + final `pyproject.toml` sweep + full net + single commit | review |

Each step ends with the fast regression net green before the next move starts.

## Out of scope (per remaining-work-plan §R3/§4)

- Importable-name renames (second step, optional, not planned here).
- Build/packaging (PyInstaller) path changes — revisit at release time.
- CI path updates beyond what `pyproject.toml`/`pytest.ini` require.
