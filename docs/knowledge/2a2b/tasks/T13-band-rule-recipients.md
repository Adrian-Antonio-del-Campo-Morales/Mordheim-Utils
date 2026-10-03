# T13 — F017 band-rule recipient filtering

Execution report for **T13-F017 — Automatic band grants can ignore profile
recipient filters**, reserved in the
[initiative checklist](../README.md). It repairs the shared predicate once in
TypeScript, regenerates the desktop bundle with the maintained builder and
proves the canonical recipients through both consumers. It does not accept or
close F017, does not enable F016's named-skill route, does not implement F019
and does not certify T13.2. It is delivered for independent review.

Entry: branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, working
tree with 271 modified/untracked entries owned by other lots. Closing revision:
same branch and HEAD (274 entries; this lot added the four untracked files
below: three test/fixture files plus this report). **No `AGENTS.md` exists** in the repository or its
parent directories; the dispatch is the instruction set. The checklist
reservation "F017 — shared band-rule recipient filtering" was confirmed before
editing, including its exclusive ownership of the shared
`index.ts`/`bridge.ts`/bundle paths.

Input hashes were captured before any edit in
`build/cache/t13-parallel/band-rule-recipients/entry/inputs.sha256.txt`. After
the repair, only the two authorized files differ from that capture
(`entry/drift-after.txt`): `index.ts` (`06d89426…` → `b02f33bb…`) and the
generated `_eligibility.js` (`cfee7612…` → `b80e8050…`). Every other input —
`bridge.ts`, the Python adapters, the fixture, the existing tests, the
canonical YAML, the register/report/plan documents, the F035 reproducer and the
coordinator evidence — still matches its entry hash. The
`packages/typescript/domain/eligibility/` directory is currently untracked in
this working tree (concurrent extraction work not yet committed), so the
recorded hashes and the before/after logs are the attributable record, not a
`git diff`.

## 1. Problem, sources and contract

Accepted F035 reproduced that `applicableRules`' band branch honours
`runtime.grant === "band"`, `applies_to.band` and `eligibility` but ignores
`applies_to.profile_ids` ([F035 acceptance](T13-shared-eligibility-reconciliation.md#12-coordinator-acceptance-and-governing-dispositions--2026-10-02),
[register](T13-execution-follow-ups.md)). All four `adventurers-kaz` skill
tables therefore reached every profile; the retained reproducer reported 20
wrong recipients across wizard, elf, barbarian, imperial-noble, dwarf and
imperial-captain, while `dwarf--hard-to-kill` and the band-wide controls behaved
correctly. The defect is latent while the named skills still fail the compiler's
`skill_lists` gate, and becomes an illegal selection once F016's route exists.

Sources used, never the implementation under test:

- `sources/knowledge/bands/mordheim/adventurers-kaz/special-rules.yaml` —
  `band--dwarf-special-skills` (line 441), `band--elf-special-skills` (310),
  `band--barbarian-special-skills` (353), `band--noble-special-skills` (399),
  each `grant: band`, `applies_to.band: true` and one `profile_ids` recipient;
  genuine band-wide controls `band--no-fixed-leader` (4) and
  `band--hired-swords` (515); profile grant `dwarf--hard-to-kill` (258).
- `sources/knowledge/bands/mordheim/adventurers-kaz/profiles.yaml` — dwarf's
  `rule_ids` (lines 184–186), seven profiles in total.
- `sources/knowledge/bands/mordheim/black-dwarfs/special-rules.yaml` — the
  canonical `band--hard-to-kill` band grant restricted only by `eligibility`.
- The accepted F035 register and §12 governing disposition.

Contract applied, without a new interpretation:

1. A band grant reaches a profile when `applies_to.band` is true **and** its
   recipient list is absent/empty or contains the profile **and** its
   `eligibility` list is absent/empty or contains the profile. Both filters are
   conjunctive; disjoint lists reach nobody.
2. Absent and empty lists keep the current convention (`!(list?.length)` →
   unrestricted), as `specialRuleOptions` already did for `profile_ids`.
3. Profile grants, explicit `rule_ids` references, result order and
   de-duplication are untouched; the whole `applicableRules` union is not
   filtered, only the band branch gains the missing conjunction.

## 2. Attributable change

One condition added to the band branch of
`packages/typescript/domain/eligibility/index.ts` (`applicableRules`, line 230):

```ts
// before
&& rule.applies_to?.band === true && (!(rule.eligibility?.length) || rule.eligibility.includes(profile.id))
// after
&& rule.applies_to?.band === true
  && (!(rule.applies_to?.profile_ids?.length) || rule.applies_to.profile_ids.includes(profile.id))
  && (!(rule.eligibility?.length) || rule.eligibility.includes(profile.id))
```

(The edit keeps the file's CRLF endings; the rendered snippet wraps for
readability.) The bundle was regenerated **only** through
`npm run build:eligibility`; its `Source SHA256` marker changed from
`10f91ed7…` to `2df1e73a1faab7423e34b308bd64f39567a809175d03fa3a19a7947685a6b035`,
which matches an independent recomputation over `index.ts` + `bridge.ts`.
`bridge.ts` was read only. No other production file was touched.

New tracked-output files:

- `tests/fixtures/eligibility/band-rule-recipients.json` — 12 shared contract
  cases (canonical shapes/IDs plus clearly-labelled `band--contract-*` reduced
  cases; provenance in the file header).
- `tests/typescript/domain/band-rule-recipients.test.ts` — 13 direct-export
  tests: the 12 fixture cases plus the canonical seven-profile table.
- `tests/python/construction/test_band_rule_recipients.py` — 26 embedded
  tests: 12 fixture cases through the real MiniRacer adapter, 7 canonical
  profiles through the adapter and 7 through the maintained
  `selection._applicable_rules` route.

## 3. Before / after evidence

All logs under `build/cache/t13-parallel/band-rule-recipients/validation/` and
`.../reproducers/logs/`; the reproducer was re-run unchanged from its original
path with its original hash `563523de…`.

| Check | Before repair | After repair |
| --- | --- | --- |
| `repro_f017_recipients.py` (retained) | exit 1 — 20 recipient violations | **exit 0 — "F017 expectation holds"** |
| New TS suite | exit 1 — 4 failed / 13 | exit 0 — 13 passed |
| New Python suite | exit 1 — 17 failed / 26 | exit 0 — 26 passed |
| Existing TS `shared-eligibility` (18 fixture + 9 F035) | exit 0 — 27 passed | exit 0 — 27 passed |
| `npm run check:eligibility` | exit 0 — current | exit 0 — current |
| `npm run typecheck --workspace campaign-web-core` | — | exit 0 |
| Python focused `test_shared_eligibility.py` + new file | — | exit 0 — 47 passed |
| `tools/mordheim-utils.py tests --scope construction -q` | 455 passed (F035 run) | **481 passed** (455 + 26 new) |
| `tests/python/architecture/test_documentation.py` | 1 passed | 1 passed |

The before-runs are not weakened expectations: the same suites that fail on the
defect pass on the fix, and the reproducer count (20) matches the independent
F035 direct and embedded witnesses.

## 4. Consumers and bundle

- **Direct TypeScript export (web consumer import).** The regression imports
  `@domain/eligibility/index`, the same module the Warband Manager consumes;
  13 tests pass, including the canonical seven-profile expectation
  (dwarf keeps `dwarf--hard-to-kill` first and its own table; elf, barbarian
  and imperial-noble keep exactly their table; wizard, imperial-captain and
  cannon-fodder keep only the two band-wide grants).
- **Embedded Python runtime (Combat Lab transport).** The fixture and the live
  canonical package run through `mordheim_construction.eligibility.call`, i.e.
  the generated `_eligibility.js` inside the real MiniRacer adapter: 26 tests
  pass. The maintained `selection._applicable_rules` route returns the same
  recipient-correct rule objects.
- **Bundle identity.** `npm run check:eligibility` reports the bundle is
  current; the embedded suite's freshness test compares the bundle marker with
  the maintained TypeScript sources and passes (47 focused tests include it).

## 5. Preservation of the existing contract

- **Genuine band-wide grants** (`band--no-fixed-leader`, `band--hired-swords`)
  still apply to every one of the seven profiles, including the two
  `implemented: NO` controls — applicability is asserted separately from
  combat support, as required.
- **Eligibility-only filters** keep working (canonical black-dwarfs
  `band--hard-to-kill`: sorcerer in, informers out).
- **Profile grants and explicit references** keep working
  (`dwarf--hard-to-kill` reaches dwarf without a `rule_ids` entry;
  an explicit `rule_ids` reference still wins outside the recipient filter).
- **Order and no duplicates**: profile-branch rules are listed first in pack
  order, band additions follow in pack order, and a rule referenced by both
  paths appears once; every canonical profile result is duplicate-free.
- **Legal selection vs combat support**: the fix changes only which rules are
  applicable; it touches no `implemented` gate, compiler binding, mechanic or
  engine behaviour. Shifty, F016 and F019 were not activated or implemented.
- **No unrelated filtering**: only the band branch gained the conjunction;
  `specialRuleOptions`' pre-existing `profile_ids` filter and the profile
  branch are unchanged.

## 6. Regression-detection proof

`build/cache/t13-parallel/band-rule-recipients/mutation/detect_filter_removal.py`
(exit 0, log beside it) removes only the newly added clause from the maintained
bundle text **in memory** and evaluates both texts in private MiniRacer
instances — no live file is mutated:

```
maintained bundle: 0 maintained regression expectations fail
filter removed:    4 maintained regression expectations fail
 - recipient-scoped band table reaches its named profile only
 - non-recipient receives only the genuine band-wide grants
 - empty lists keep the band-wide convention for one profile
 - canonical adventurers-kaz/wizard receives ['band--barbarian-special-skills',
   'band--dwarf-special-skills', 'band--elf-special-skills', 'band--noble-special-skills']
PROOF HOLDS: removing the new filter is detected by the maintained regression expectations
```

The same detection is visible in the retained before-logs: the direct TS suite
failed exactly on the recipient cases and the embedded suite on the recipients
and the canonical profiles, and the retained reproducer reported its 20
violations, all of which disappear after the repair.

## 7. Commands, exit codes and limits

| Command (repository root, `python -X utf8`) | Exit |
| --- | --- |
| `npm run build:eligibility` | 0 |
| `npm run check:eligibility` (before and after, plus final) | 0 |
| `npm run test --workspace campaign-web-core -- band-rule-recipients` | 0 (13) |
| `npm run test --workspace campaign-web-core -- shared-eligibility` | 0 (27) |
| `npm run test --workspace campaign-web-core -- t13-shared-eligibility-reconciliation` | 0 (9) |
| `npm run typecheck --workspace campaign-web-core` | 0 |
| `python -X utf8 -m pytest tests/python/construction/test_shared_eligibility.py tests/python/construction/test_band_rule_recipients.py -q` | 0 (47) |
| `python -X utf8 tools/mordheim-utils.py tests --scope construction -q` | 0 (481) |
| `python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q` | 0 (1) |
| `python -X utf8 build/cache/.../reproducers/repro_f017_recipients.py` | 0 |
| `python -X utf8 build/cache/.../mutation/detect_filter_removal.py` | 0 |

Limits: F016's named-skill route and F019's Combat Lab stage were **not**
implemented or activated; no KB/staging source, compiler, contract, adapter,
UI, engine, semantic spec, pin or coverage file was written; `bridge.ts` was
not modified; no commit or push was made; no full T14 certification was run.
No live desktop/web session was driven — the direct export exercised is the
import the web consumer uses, and the embedded adapter is the real transport.
The F057 parity-count blocker (`3758 != 3743`, owned by F057) is inherited,
outside this scope and was not re-run.

## 8. Follow-ups proposed for the coordinator

1. **F016 named-skill route may now resume.** Reproducer: the retained F017
   reproducer plus the new suites. Impact: named Adventurers skills become
   selectable for source-correct recipients only. Owner: Combat Lab
   construction (T13.2), with KB mechanics for `skill.fey`/`skill.taunt`.
   Resume: the next F016 route/reconciliation lot. Close criterion: supported
   named skills have source-correct recipient/selection proof; unsupported
   members keep precise limitations.
2. **F019 shared-file serialization.** Reproducer: `repro_f019_silence.py`.
   Impact: any F019 repair that needs `index.ts`/`bridge.ts`/the bundle is an
   exclusive writer over paths this lot changed; the new F017 suites must be
   re-run with it. Owner: coordinator scheduling; F019's own consumer work is
   independent until then. Resume: when F019's stage/fact integration is
   scoped. Close criterion: the Combat Lab boundary refuses the same tokens the
   shared decision refuses.
3. **Browser projection re-check (optional).** Reproducer: regenerate the web
   knowledge artefact and re-run `skillIssue` on the projected recipient facts.
   Impact: confirms the browser path stays recipient-correct while F016's route
   is built. Owner: web artefact/consumer owner. Resume: with the next
   artefact revision.   Close criterion: projected `skill_lists` reach exactly
   the canonical recipients.

## 9. Reproducible evidence

`build/cache/t13-parallel/band-rule-recipients/`

- `entry/` — `head.txt`, `date.txt`, `git-status.txt`,
  `inputs.sha256.txt` (23 entry hashes), `drift-after.txt` (only the two
  authorized files changed).
- `validation/` — before/after logs for the new suites, the check/build logs,
  the shared and F035 TS suites, typecheck, focused Python, construction scope
  and documentation.
- `reproducers/logs/` — `repro_f017_before.log` (20 violations, exit 1) and
  `repro_f017_after.log` (exit 0).
- `mutation/detect_filter_removal.py` + `.log`.
- `checks/` — `postedit.sha256.txt` and `manifest.json` with the deliverable,
  test, fixture and evidence hashes.

Status: **delivered for independent review**; F017 remains open, F016/F019
remain open and untouched.

## 10. Independent coordinator acceptance — 2026-10-02

**Accepted; F017 resolved and reservation released.** This appendix supersedes
the delivery's pending-review status. F016/F019 and T13.2 remain open.

Independent evidence: `build/cache/t13-parallel/band-rule-recipients-coordinator-review/`.

- All seven delivered source/test/fixture/report hashes match. Across the 23
  captured entry inputs, only `index.ts` and the generated bundle differ.
  Removing the single added source clause reconstructs the earlier accepted
  `index.ts` byte-for-byte (SHA-256 `06d89426…`). The bridge is unchanged.
- The source marker was independently recomputed as
  `2df1e73a1faab7423e34b308bd64f39567a809175d03fa3a19a7947685a6b035`;
  fresh `check:eligibility` confirms the generated bundle is current.
  Broader protected F035 inputs also remain unchanged apart from the two
  authorized files. Fourteen copied canonical fixture rule occurrences match
  their live recipient, eligibility and runtime facts.
- Fresh direct suites: **40 passed** (13 new, 18 shared, 9 F035).
  Fresh actual embedded/selection suites: **47 passed** (26 new, 21 shared).
  The retained unchanged reproducer returns exit 0 with no recipient violations.
  The submitted isolated removal witness was also rerun successfully.
- Thirty independent in-memory decision witnesses cover both filters, their
  conjunction, absent/empty lists and the required band flag. All pass on the
  maintained bundle. Removing the recipient filter fails five witnesses;
  replacing the conjunction with OR fails eleven. No live file was mutated.
- The delivered **481 construction** result and TypeScript typecheck are
  retained evidence, not fresh coordinator reruns. No visible product-flow,
  named-skill activation, full T14 or F057 measurement was performed.

F016 may resume its separately scoped named-skill fact/compilation work because
the recipient prerequisite is now satisfied. This does not prove named skills
are already selectable or executable; Knights' Feats and missing mechanics keep
their own gates. F019 still needs its specialized-stage/fact integration repair.
The shared-file reservation is released; each next writer must reserve the
affected paths and preserve/re-run these recipient regressions.

Proposal 3 is not a new standalone regeneration task: F016 owns any required
current consumer/projection proof when its facts change. F017 did not change KB
or generated Web data, so regenerating that artefact alone would not certify
recipient correctness. No new follow-up ID is assigned for existing handoffs.

The incoming report is retained as `incoming-report.md` in the coordinator
evidence directory (SHA-256 `4e81dc30…`); its body, fixture, tests, code and
executor evidence were preserved during acceptance. Only coordination documents
and this appendix were edited. No commit, push or agent launch occurred.
