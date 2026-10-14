# Mechanics closing conclusions

Date: 2026-10-09.

Status: evaluation pending. This document records conclusions from the author's
closing report; it does not authorize another implementation batch, certify the
engine or advance authoring statuses. The reported counts and checks have not
been independently revalidated for this document and may change during concurrent
work.

## Reported authoring snapshot

Scope: `cases/mechanics`.

| Measure | Reported value |
| --- | --- |
| Per-ID files | 306 |
| Declared scenarios | 875 |
| File status: `AUTHORED` | 288 |
| File status: `PARTIAL` | 18 |
| File status: `TODO` | 0 |
| File status: `REVIEWED` | 0 |
| Scenarios in `AUTHORED` files | 815 |
| Scenarios in `PARTIAL` files | 60 |
| Direct mechanic/rule activation through `skill_ids` | 255 scenarios |

The author reports successful engine-free structural validation of the 306
files and no engine imports or execution during that intervention. Their files
remain marked `UNEXECUTED`. Earlier executions elsewhere in the shared task do
not certify this snapshot.

This is substantial progress in scenario authoring. Zero `TODO` files does not
establish complete requirements coverage: 18 files remain partial, and none has
completed the declared semantic review. YAML validity, identity consistency and
admitted `covers` references establish structural integrity rather than the
sufficiency of a rule's scenarios.

## Source freshness requires evaluation

The closing report identifies 916 stale scaffolds across the battery, including
files outside this directory. That total is not a count of semantically incorrect
mechanics scenarios.

A whole-file hash changes when any content in that source changes. It does not
demonstrate that each rule captured from the file changed. The relevant question
is whether the printed rule, accepted interpretation, parameters, scope or other
semantic dependencies of a particular ID differ from its captured source.

Changes confined to unrelated entries may leave a scenario's reasoning valid.
Relevant normative changes may invalidate expectations or review evidence.
Current evidence does not distinguish those cases sufficiently to justify
rewriting all affected scenarios or refreshing fingerprints in bulk. Record-level
fingerprints and whole-file snapshots retain their distinct meanings.

## Direct activation through `skill_ids` requires classification

The 255 directly activated scenarios are not automatically defective. Acceptance
by the current compiler alone also does not establish their semantic validity.

Two responsibilities must remain distinct:

- `mechanics` scenarios demonstrate the behavior of a mechanic under the
  source-defined conditions. A documented isolation fixture may legitimately
  activate that mechanic directly if the accepted fixture contract permits it.
- `grants` scenarios demonstrate who obtains a mechanic, through which
  acquisition route, with which parameters and under which conditions.

Whether a direct activation is suitable depends on the accepted fixture contract
and whether it preserves the mechanic's required conditions and dependencies.
An isolated fixture must not erase a material recipient restriction, exception
or interaction. Conversely, requiring a band/profile acquisition route for every
mechanic fixture may duplicate the grant tests without improving its behavioral
coverage.

The suitability of these configurations remains an evaluation question. Neither
blanket replacement with band builds nor blanket acceptance of direct activation
is justified by the closing report.

## Partial requirements need separate conclusions

The 18 `PARTIAL` files must be assessed by the nature of each remaining
requirement:

- A missing scenario or meaningful variant is an authoring gap.
- A missing input, observation or documented request convention is an adapter
  representation gap.
- A conflict between governing sources and a recorded interpretation requires
  a semantic decision supported by evidence.
- A source-defined behavior absent from the unfinished engine is an
  implementation gap; it does not itself prevent writing its expected result.
- A normatively prohibited configuration must be distinguished from a rejection
  caused only by the current implementation.

These categories require different conclusions. A missing consumer must not be
used to claim a rule is untestable, and an unavailable observation must not be
presented as a completed assertion. The report's claim that all resolvable work
is exhausted remains subject to this classification.

## Closing assessment

The authoring inventory has reached zero `TODO` files, with explicit partial
requirements. Complete semantic authoring is not yet established: source
freshness, fixture suitability and the remaining requirements need evaluation.

No mass configuration conversion, snapshot refresh or promotion to `REVIEWED`
is justified solely by the aggregate report. Evaluation should retain the
existing one-file-per-ID organization and the source-derived family methodology
described in the [README](README.md#author-by-semantic-family) and
[implementation plan](plan.md#family-based-data-authoring).

Engine execution remains deferred under the plan. It is a separate milestone,
not a prerequisite for evaluating the current authoring conclusions. This
document records pending judgments without selecting or dispatching the next
action.

## Cross-check by E08 (2026-10-14)

This closing document was re-measured by the static integration pass (E08) with
the engine-free validator and the pure contract tests, with identical input
hashes before and after. Nothing in this chapter rewrites cases, the register
or the baseline; it reconciles the numbers the closing snapshot reported
against the corpus as it stands now.

| Measure | Closing report | E08 re-measure |
| --- | ---: | ---: |
| Per-ID files | 306 | 306 |
| Declared scenarios | 875 | 898 |
| File status `AUTHORED` | 288 | 292 |
| File status `PARTIAL` | 18 | 14 |
| Files `TODO` / `REVIEWED` | 0 / 0 | 0 / 0 |
| Files with an empty body | — | 0 |
| Authoring metadata conflicts | — | 5 |
| Unknown audit/clause references | — | 0 |

The mechanics delta against the register snapshot is zero new requirements: no
`mechanics` identity moved scope in the working register beyond the
`scope-admitted-contract-reconciliation` batch already documented by E06's
matrix. The 14 remaining `PARTIAL` files classify, by their own `PARTIAL[...]`
note and the consolidated dependency register, into two groups:

1. Pending clause attached to a registered dependency identifier
   (dependencias.json) — 10 files: `mechanic.frustratingly-tiny`
   (`charera-mutual-exclusion`), `mechanic.mark-of-arkhar`
   (`dec-blood-father-role`), `weapon.cathayan-longsword` (`dec-cathayan-ap`),
   `weapon.starsword` (`dodge-save`), `skill.sword-master`
   (`dec-parry-six-identity`), `weapon.pike` (`pool-pre-reserva-pike`),
   `mechanic.spider-infested` and `weapon.kusara-kama` (`duracion-reset`),
   `skill.sigmar-s-sign` (`obs-pre-floor-sigmar`, E07 external),
   `skill.regeneration-blocked-by-blessed` (`src-attack-blessed`, E07 external).
2. Pending disposition documented without a register identifier — 4 files,
   candidate delta for a future dependency entry, each with its owner:
   `mechanic.curse-of-the-revenant` (the fire facet is unlocked since the E07
   contract revision; its stale note awaits the owner's second pass),
   `mechanic.wheelo-skill-modifications` and `weapon.disease-dagger`
   (source-vs-contract conflict alternatives handed to the coordinator in the
   E02 report, no chosen rule), `weapon.barbed-whip` (third-model multi-figure
   runtime documented as excluded in the E02 report).

No mechanics classification above claims a scenario is untestable because a
consumer is missing; each pending note names its exact blocked datum.

The 5 metadata conflicts, per file, for their owner (E02 list):
- `skill.elven-agility.yaml` — `AUTHORED` status without any `AUTHORED[...]` marker.
- `skill.iron-sinews.yaml` — marker `AUTHORED[whole]` names a declared clause.
- `skill.regeneration-5-plus.yaml` — `AUTHORED` without marker.
- `skill.regeneration.yaml` — `AUTHORED` without marker.
- `skill.step-aside.yaml` — `AUTHORED` without marker.

These are metadata-repair findings, not behavioral verdicts; none justifies a
mass status promotion, and no note above certifies semantic sufficiency.
Engine execution remains deferred; all scenarios stay `UNEXECUTED`.
