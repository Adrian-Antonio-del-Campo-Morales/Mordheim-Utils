# H03b — hireling resources and variants (9 clauses)

**Coordinator integration completed, 2026-10-18: 9/9.** Nine final rows applied
with a fresh full snapshot, prepare/preview and concurrency checks; all 4,556
keys, source texts, fingerprints and notes conserved. Previous consumers and
verification accumulated. Evidence: `%TEMP%/h03b-coordinator-imulpah6/`.
Executor results reused without rerunning tests. The register now has zero
pending rows; this does not certify integrated engine completion. Catalogue,
admission and publication limitations below remain for block 4.

**9/9 rows closed. One real implementation gap; eight reconciliations backed by
executed discriminators.** Base: `2A2B` at `a1f92653`, shared working tree.
Foole and the H03a closures were not reopened; Slayer and R01 are untouched.

## Implemented (new)

Only **Innominatus, the Tilean Gladiator** lacked an executable connection; his
whole profile was refused, so neither of his two skill clauses could run:

- his unique **Dark Elf Blade** declared no combat mapping, which aborted
  `compile_fighter` before any skill was read. The item now names a profile rule
  bound to the canonical `material.dark-elf-blade` mechanic (the KB's own printed
  properties: +1 on the critical table and 2–4 Injuries as Stunned, retaining the
  underlying weapon), the same unique-item pattern Belandysh already uses;
- **Grizzled Veteran** and **Death without a face** are now hireling-scoped
  profile rules bound to the shared `mechanic.psychology-immunity` and
  `mechanic.causes-fear` operators, and the two resolved skill references are
  gone from the profile. They apply automatically because the printed profile
  carries them (not a choice), and no other hireling receives them.

No new operator, resource, subsystem or shared skill entry was created.

## Reused and reconciled

| family | existing consumer | what was actually missing |
|---|---|---|
| Marks of Myrmidia — Oracle | `contexts.OwnedRollDice` (`mechanic.oracle`) | nothing: selection → tag → one optional personal reroll per battle, spent once; the recorded `requires` was the old promotion gap |
| Snorri — drinking table | `compiler.compile_fighter`, `contexts.prepare_hit_context`, `phases.build_attacks` | the row pointed at a non-existent `contracts.py::snorri_drunk_result`; the projection lives in the compiler and covers results 2–6 |
| Belandysh — dice profile | `compiler.compile_fighter`, `state.require_characteristics` | nothing: `mechanic.inconsistency` rolls each needed characteristic once per turn, never at duel start |
| Emissary — patron branch | shared `buildRestriction`/`buildAccess`, `compile_fighter` | the selector was untested; exclusivity and Tzeentch's academic access are now proven |
| Nurgle — poison / Fear | `contexts.prepare_wound_context`, `psychology.causes_fear` | nothing: the attack effect merges the fighter's global tags, so Black Lotus applies to his attacks; Fear is H03a's evidence |

## The nine dispositions

| id (abbreviated) | clause | disposition |
|---|---|---|
| `…war-priestess-of-myrmidia…/pending-duel` | `whole` | closed — Oracle reroll offered, optional, spent once, never re-offered |
| `…snorri-nosebiter.rule.drunk/mechanic.snorri-drunk` | `snorri-drunk--scope--drinking-table` | closed — results 2/3/4 executed here; 5/6/refusal already pinned by the admission suite |
| `…grade-1c.yaml/@/profiles/0/…/0` | `profile` | closed — D6/D3 profile compiles; rolls on demand, once per turn |
| `…grade-1c.yaml/@/profiles/2/…/1` | `grizzled-veteran` | implemented — profile rule → `mechanic.psychology-immunity` |
| `…grade-1c.yaml/@/profiles/2/…/2` | `death-without-a-face` | implemented — profile rule → `mechanic.causes-fear` |
| `…grade-2a.yaml/@/profiles/5/…/0` | `rule` | closed — exactly one exclusive patron; Tzeentch keeps academic access |
| `…emissary-of-chaos.rule.patron/…` | `patron-khorne` | closed — `mechanic.emissary-khorne`: A1+1 then Frenzy = 4, granted once |
| `…emissary-of-chaos.rule.patron/…` | `patron-nurgle-poison` | closed — Black Lotus wounds on a natural six without a wound die |
| `…emissary-of-chaos.rule.patron/…` | `patron-nurgle-fear` | closed — H03a's executed discriminator reused, not re-run |

## CSV

`prepare` produced **9 changes**, one per `(id, clause_id)`, from a complete byte
snapshot; notes are appended to, never replaced, and the conservation checks
passed. Snapshot `sha256 6d37372f28a083e1…` still matches the current CSV.

`C:\Users\PHOLTE~1\AppData\Local\Temp\h03b\package.json`

No `apply --write` and no direct CSV edit; integration belongs to the coordinator.

## Files owned by this delivery

- `sources/knowledge/catalog/hirelings/dramatis-personae/grade-1c.yaml`
  (Innominatus: item rule, two skill rules, two resolved references)
- `tests/python/construction/test_h03b_hireling_resources.py`
- this document

The other hireling catalogues in the tree (`core`, `grade-1a`, `grade-1b`,
`hired-swords/*`, `rules`) are being edited by another owner and were not touched.

## Evidence (one run each, saved in `%TEMP%/h03b/`)

- `test_h03b_hireling_resources.py`: **8 passed**, EXIT=0.
- `test_t13_hireling_admission.py`: **35 passed, 1 failed** (`admission.txt`).
  The failure is `test_a_blocked_equivalence_names_its_own_blocker`, which
  expects Drenok (a **grade-1b** profile) to still be refused for "intrinsic duel
  clauses are pending". In the current tree all his grade-1b rules are
  `implemented: YES`, so that refusal can no longer fire and his kit resolution
  reports its own blocker instead. This delivery edits only grade-1c, so the
  failure is not caused here; `grade-1b.yaml` and the admission test file both
  carry large uncommitted changes from their owner, so neither was modified or
  re-polled.
- Editorial schema of `catalog/hirelings/dramatis-personae/grade-1c.yaml`:
  **0 errors** against `hireling-profile-dramatis-personae.yaml.schema.json`.

## Exact blockers

- **Web knowledge artefact.** `tools/knowledge/generate_knowledge_web.py` still
  stops on the recorded foreign Spanish label conflict (`'No Missile Weapons'`)
  before writing, so the hireling rule additions are not in the web artefacts.
  No new web prose was added by this delivery.
- **Foreign grade-1b failure** described above: reported, not repaired, because
  the file and its test are in another owner's in-flight change.
- E2E was not executed, collected, inspected or edited.
