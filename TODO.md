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
| [Test classification](#test-classification-coverage) | Every maintained Python suite classified and guarded; TypeScript/web pending | Give the TypeScript and web suites a runner-supported category; validate the new executor separately. |
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
- Reconcile the two reported `a-band-mate-without-the-immunity-is-tested-for-stupidity`
  E2E scenarios (Mordheim and Trollheim Grizzled Veteran): the external delivery
  reproduces their failures both before and after its patch. Check the supplied
  Stupidity state and source-derived expectations; do not weaken the assertions.
- Review Grizzled Veteran in
  `sources/knowledge/bands/trollheim/chaos-streets-pit-fighters/special-rules.yaml`:
  it still uses `grant: band` although its printed origin presents a selectable
  Hero skill. Reconcile its construction and E2E recipients, as done for the
  Mordheim origin, with focused proof.
- Reconcile Battle Tongue's general runtime exclusion and the deferred
  `norse-explorers-lustria` copy with the executable Norse special-skill variant;
  preserve source-specific recipients and source-backed scope decisions.
- Replace stale verification references to the absent
  `test_t13_psychology_leadership.py` in the clause register using the maintained
  registry utility and current executed evidence. Keep clause identities intact.
- Reconcile the semantic scope/source digests of
  `access-nagarythe-already-strength` after the construction-scenario integration.
  The focused coordinator selection passes 39 checks; only
  `test_redundant_access_mutation_is_justified_not_counted_as_detected` fails,
  reporting stale scope and Powerful Build source digests. Review the actual
  scope/source changes with the verifier work before updating the pins; do not
  bypass provenance validation or infer global semantic closure.
- Reconcile the wider semantic corpus against the maintained scope and sources.
  The verifier integration improves stale-pin diagnostics but deliberately does
  not renew evidence. Review scope changes, changed rule rows, band-context-only
  changes and revised catalogue mechanics separately; update pins only after
  the affected interpretations and witnesses have been checked. In particular,
  preserve the reviewed dispositions for Inconsistency, Spectral Touch, Netter,
  Energy Focus and Sea Dragon Cloak. Do not use a corpus-wide digest refresh as
  semantic acceptance. The four focused verifier controls pass after integration;
  the full semantic audit remains unresolved and was not rerun by the coordinator.
- Complete the published warband-skill table route through `skill_ids` for
  Amazons Lustria, Battle Monks of Cathay and Arabian Tomb Raiders
  (E2E_0027, E2E_0032 and E2E_0031). The first two still fail with unknown
  band-member mechanic IDs after their independent fixture corrections.
  Reconcile table membership, canonical resolution and execution support in
  the maintained TypeScript eligibility source and Python construction path;
  regenerate the eligibility bundle instead of editing it directly. Preserve
  the positive list-route scenarios and their out-of-table rejection controls.

- Resolve the Noble special-skill admission contract (E2E_0022): its positive
  scenario selects campaign-only `skill.trading-flair`, whereas construction
  deliberately rejects legal named skills without a duel operator. Decide how
  out-of-duel selections are represented before changing the scenario or
  construction contract; do not add a fictitious close-combat no-op or turn the
  positive admission claim into an incidental-error assertion.

- Review the remaining Knights Feats members Combat Charge, Lancer and Armour
  Specialist against their own source-specific contracts before admitting their
  execution. The Sword Master list route is verified; it does not certify the
  other feats, and partial placeholder operators were not integrated.
- Complete the remaining E2E_0355 assignment: its two excluded Netter scenarios
  are archived, while seven other scenarios remain active and were not verified
  as a package here. Preserve their independent queue ownership.
- Resolve admitted E2E coverage gaps under `MORDHEIM_E2E_REQUIRE_COMPLETE=1`
  before global closure. Passing ordinary inventory checks after justified
  exclusions does not establish completeness or positive semantic evidence.
- Carry the modular whipcrack priority correction into optimized-backend parity
  work. The vectorized proposal was deferred; this integration verifies only
  the modular path and does not establish optimized parity.

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

### Test classification coverage

**Status:** the eighteen primary categories are registered as pytest markers in
`pyproject.toml` (with `--strict-markers`), per
[the sequence contract](docs/reference/test-sequence.md#implementation), and
`tests/conftest.py` rejects a
collected item under a classified root that carries no primary category, several,
or a marker that is not a category. The classified roots are
`tests/python/{architecture,contracts,knowledge,construction,application,persistence,ui,cli,web,combat,verification}`
and `tests/E2E/modular-engine`. On 2026-10-20 the full suite collected 12,959
items, none outside those roots and none with zero or several categories; a
temporary probe confirmed the guard rejects a missing and a doubled category and
that `--strict-markers` rejects an unregistered marker. No functional test was
executed for the annotations.

An ordered entry point now exists (`tools/verification/test_sequence.py`, invoked
as `python tools/mordheim-utils.py test-sequence`), added by a concurrent slice.
Its seven self-tests under `tests/python/cli/test_test_sequence.py` are collected
as `test_infrastructure`; the plugin itself lives under `tools/` and is therefore
not a collected suite (`testpaths = ["tests"]`). Its ordering has not been
validated here.

The E2E corpus reconciles today: 1,779 case files declare 5,171 scenarios, all
with unique `audit_id::id` identities, the loader collects 5,171 parameters, and
`HEAD` declares the same 5,171. The readings of 5,183 and 5,174 reported by the
concurrent delivery, and the 5,174 measured here mid-session, were transient
working-tree states: the three declarations that existed then and are gone now
are the carnival-of-chaos plague-cart `the-same-face-leaves-a-stunned-result-
without-the-modifier` scenario and the ogre-hunting-party-web
`a-declared-net-charge-knocks-the-enemy-down-and-the-charge-strikes-home` and
`without-the-netter-rule-the-charge-asks-for-no-net-die` scenarios. No mechanism
produces a nine-identity offset (no duplicate ids, no loader skip).

**Pending:**

- Classify the TypeScript and web suites executably, or keep the limitation
  stated where they run. The installed runners have no per-test category tag
  (`vitest --help` exposes `--testNamePattern`, `--project` and `--dir`;
  `node:test` exposes `--test-name-pattern`), so a category has to live in the
  file name or the test name. Native `test.projects` with wildcard `include`
  selects cleanly (verified: 518 + 275 + 118 = 911 of 961 TypeScript items across
  three directory projects). The minimal real change is a
  `<name>.<category>.test.ts` token plus eighteen `**/*.<category>.test.ts`
  projects, splitting only the five mixed files; it renames 158 files and changes
  every Vitest report identity, so its consumers need a reviewable mapping first.
- Keep the web suite invoked from `apps/warband-manager-web`: `tests/web/**`
  resolves the generated artefacts from `process.cwd()`, so a repository-root
  invocation collects with `ENOENT` one directory above the checkout even though
  `outputs/web-public/knowledge/`, `build/generated/knowledge-web` and
  `contracts/campaign-file-v5/fixtures` exist.
- Re-collect after any concurrent edit that adds tests to a classified root: a
  new test without a marker fails collection by design, and the guard covers
  only the roots listed above.
- Review the mixed files that are classified per function when a split would
  improve selection. This pass moved no file, so several construction and
  knowledge files carry four or five categories by case.
- Validate the executor's ordering and failure policy on an integrated revision.
  That belongs to the slice that added it; annotations and a plan printout do not
  establish that a prerequisite runs before its consumers.

**Close when:** every maintained executable test carries exactly one primary
category and a runner-supported selection key, collection over the full suite
reports no unclassified item in a classified root, and any remaining runner
limitation is stated where it applies.

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
