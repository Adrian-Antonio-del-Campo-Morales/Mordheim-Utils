# Project backlog

Track unresolved defects, verification work and deferred capabilities here.
Detailed procedures belong in the linked guides; affected records and live
counts belong in executable inventories and generated reports.

Statuses below describe the recorded evidence. A reported failure remains
unverified against the current tree until the relevant check is rerun; a closed
implementation queue does not establish integrated correctness.

## Work overview

| Work | Recorded status | Dependency or next step |
| --- | --- | --- |
| [Modular integration](#close-modular-integrated-verification) | Implementation queue closed; integrated verification pending | Run the scoped closure procedure on one integrated revision. |
| [Web artefacts](#regenerate-the-web-artefacts) | Generation failures reported; current tree not rechecked | Reconcile translated labels and validate freshly generated data. |
| [Combat Lab popover](#combat-lab-checklist-popover-closes-during-layout) | Failure observed; cause unknown | Reproduce the focused case and establish why the popover closes. |
| [Optimized engines](#subsequent-vectorized-and-native-engine-work) | Follow-on work to scope | Complete modular verification before defining the porting delta. |
| [Knowledge and translations](#knowledge-gaps) | Open follow-ups | Use canonical references and the live review queues. |

## Pending verification and reported defects

### Close modular integrated verification

**Status:** the implementation queue is recorded as closed; integrated
verification is still pending. Follow the
[closure procedure](docs/reference/verification.md#modular-integration-closure).

- Run the existing modular combat, construction, modular semantic and E2E
  checks together on one integrated revision. Include the E2E scenarios,
  coverage inventory and accepted-evidence non-regression checks from
  `tests/E2E/modular-engine/`.
- Verify the configuration → `compile_fighter` → `initialize_duel` →
  `resolve_round` path using existing canonical cases. Include recipients,
  equipment loss, effect composition, save ordering, resources and expiry in
  the affected cases; add only genuinely missing discriminators.
- Check TypeScript types, the generated eligibility bundle, relevant editorial
  contracts and clause-register integrity. Confirm no admitted work is pending
  and preserve the 4,556 clause keys and their traceability.
- Group failures by shared cause and fix admitted defects without weakening
  positive tests or admission controls. Earlier failures count when they prevent
  closure; record any unresolved concrete blocker here.
- Rerun affected groups after fixes, then perform one final integrated
  confirmation on the delivered revision. Reuse valid output instead of
  repeating unchanged checks.

**Close when:** the applicable integrated checks, including the modular E2E
battery, pass on the delivered revision,
all admitted consequences have a usable configuration-to-consumption path,
no known executable or composition defect remains, and register integrity is
preserved. A closed CSV alone does not certify the modular engine.

**Scope:** modular E2E validation is part of this closure. Investigate and fix
admitted defects exposed by the battery without weakening source-derived
expectations. This closure does not include optimized-backend parity, engine
coverage campaigns, statistical certification or optimized engine implementation.

### Regenerate the web artefacts

**Status:** generation failures were last reported on 2026-10-17; they have not
been rechecked against the current tree.

**Recorded failures:** conflicting Spanish rule labels in `_build_rules_prose`:

- `No Missile Weapons` in
  `sources/knowledge/bands/mordheim/knights-of-the-bitter-moors-mim/special-rules.yaml`:
  `Sin armas de proyectil` / `Sin Armas de Proyectil`.
- `Mer-Creature` in an earlier generation run.

**Next steps:** reconcile the actual conflicting labels while preserving
source-specific prose and validation. Regenerate the artefacts with
`python tools/knowledge/generate_knowledge_web.py`, then run its `--check`.
Do not hand-edit generated JSON or weaken validation.

**Close when:** generation and freshness checks pass, and Dwarf inheritance
and Aquatic Mutants are checked against the fresh artefacts. Reuse
[`mutations.test.ts`](tests/typescript/domain/campaign/mutations.test.ts)
for Aquatic Mutants. Evidence against an older artefact does not close the
current web route.

### Combat Lab checklist popover closes during layout

**Status:** last observed on 2026-10-18; no cause has been established.

**Recorded failure:**
[`test_checklist_popover.py`](tests/python/ui/test_checklist_popover.py),
case `test_popover_body_matches_the_dark_theme`, fails after `root.update()`
because `popover.scroll_frame` is already `None`. The failure occurred both
before and after the UI ownership move.

**Next step:** determine why the popover closes during layout and correct its
lifecycle or the test's focus setup as appropriate.

**Close when:** the existing focused case passes with the theme and width
assertions preserved.

## Subsequent vectorized and native engine work

**Dependency:** scope these phases after modular verification. They do not
block modular closure. Both engines already exist; extend their current paths
rather than introducing replacements.

1. **Define the porting delta:** compare the verified modular contracts with
   each backend's actual support. Identify missing state, operators and
   orchestration by usable rule family; retain explicit rejection of unsupported
   combinations. Do not reinterpret source rules already settled for the oracle.
2. **Complete the NumPy implementation:** port missing admitted consequences,
   including decisions, per-fighter resources, timing and composition. Preserve
   the canonical construction/context boundary and batch isolation; prove each
   family against existing deterministic modular cases as it becomes usable.
3. **Complete the native implementation:** port the same contracts into the
   existing Cython backend and compile/folding layer. Rebuild the extension and
   test the native path explicitly; a NumPy fallback is not native evidence.
   Independent backend families may be developed in parallel with disjoint owners.
4. **Verify and qualify the optimized backends:** use the existing deterministic
   rule and whole-duel comparisons first, then targeted interactions and the
   applicable parity/certification gates in
   [Verification](docs/reference/verification.md). Benchmark only correct, supported
   paths. Report backend-specific limits and evidence before enabling broader use.

**Close when:** each backend's admitted porting delta is implemented and its
applicable checks pass, with remaining limits and evidence stated per backend.
These phases do not expand into the deferred domains below.

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Resolve hireling `unresolved_references` | As canonical skill, prayer, rune, equipment, mount, companion or procedure catalogues become available, replace the resolved references with validated canonical links. Keep genuinely unresolved references explicit. |
| Define composite-entity schemas | Establish the schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae to the hiring catalogue. |
| Review Trading Post price differences | Review the live price-collation queue and record source-backed decisions in the maintained resolutions CSV. |
| Make unsupported item-to-engine mappings explicit | Record intentionally unsupported mappings so catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing interface messages and remove unused message keys. |

See the [knowledge-base reference](docs/reference/knowledge-base.md),
[campaign knowledge guide](docs/guides/campaign-knowledge.md) and
[web presentation conventions](docs/reference/web-presentation.md) for the owning
contracts and procedures.

## Human decisions

No unresolved human decisions are currently listed here. Record new questions
with the affected source or contract and the work they block. Move accepted
answers to [Design rulings](docs/decisions/design-rulings.md).

## Deferred product scope

These domains are deliberately outside the current duel runtime, rather than
missing requirements for modular closure. Implementation requires an approved
scope change in
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml):

- group psychology and warband-wide proximity effects;
- shooting and missile weapons;
- movement, terrain and falling;
- magic in battle;
- mounts and ridden combat;
- scenario table mechanics beyond progression rewards.

## Sources of truth

| Question | Maintained source or command |
| --- | --- |
| Which rule consequences are in scope? | Each rule's `runtime` block and the runtime-scope registry linked above. |
| Are admitted clauses pending? | `python -X utf8 tools/knowledge/clause_registry.py query --pending` |
| What semantic obligations remain? | `python tools/mordheim-utils.py verify --inventory` |
| Where is the rule-review inventory? | `python tools/mordheim-utils.py report rules` |
| Which hireling references are unresolved? | `unresolved_references` in the hireling YAML. |
| Which prices need review? | `python tools/knowledge/maintenance/price-collation.py`, its generated `outputs/knowledge/` report and the [maintained resolutions CSV](tools/knowledge/maintenance/price-collation-resolutions.csv). |
| Which decisions are binding? | [Design rulings](docs/decisions/design-rulings.md). |

When updating this backlog, keep the observed symptom, evidence date, remaining
uncertainty, next action and closure condition together. Remove resolved entries
when their evidence is available; retain permanent decisions in their owning
reference rather than turning this file into a completion log.
