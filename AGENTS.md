# Repository agent instructions

## Task-specific skills

Use an available task-specific skill when it fits the assigned work. Choose one
primary skill, read its `SKILL.md` once, and apply it to the implementation; do not
load a catalogue of skills or turn skill selection into a preparation phase.
Use the locations advertised by the current agent environment, not assumed paths.

| Task | Preferred skill | Required working behavior |
|---|---|---|
| Bug or small behavior correction | `surgical-patch` | Fix the narrowest responsible layer; preserve surrounding behavior and add only necessary regression proof. |
| New capability or missing end-to-end connection | `lean-build` | Complete the usable path across its owning layers; reuse existing operators and omit speculative infrastructure. |
| Failure with an unknown cause | `investigate-first` | Investigate only the unknown blocking the next edit; stop diagnosis once the cause is supported, then implement when authorized. |
| Explicit verification/integration check | `verify-and-stop` | Reuse valid evidence and run the smallest sufficient checks; do not expand into audits or unrelated fixes. |
| Required structural change preserving behavior | `safe-refactor` | Preserve contracts and ordering; refactor only within the assigned scope, never as optional cleanup. |
| Requested schema/data/API transition | `migration` | Preserve readers, writers and data; use conservation and compatibility checks appropriate to the transition. |

For coding, apply `ponytail` when available as a simplicity constraint: reuse the
repository or standard library before adding abstractions or dependencies. It
does not justify skipping source interpretation, validation or a complete usable
connection. Add another skill only when a concrete task phase needs it.

Announce the first application briefly. If a skill is unavailable, do not install
it or search broadly: apply the working behavior above without claiming to have
used the skill. Report its absence only if it materially blocks the task.

Skills do not authorize more tests, research, documents or scope than
the user assigned. User instructions and the modular limits below prevail over
skill defaults. A skill's stop condition applies to the capability being handled:
continue with other assigned incomplete capabilities until the package is done.
Do not create skill-specific plans, checklists or reports; use only the authorized
task completion document.

## Subagents: authorized when they accelerate delivery

The user authorizes implementation agents to launch subagents within their
assigned package. Prefer delegation when independent implementation work can
finish sooner; do not delegate merely to produce more reviews or research.
The parent assigns concrete capabilities, disjoint file ownership and completion
criteria, propagating all repository limits. One writer per shared file still
applies; the parent integrates shared changes and remains responsible for the
complete package. Reuse the subagents' source findings and valid test output
instead of repeating their investigation or checks. Subagents do not write the
shared CSV or create separate completion documents; return changes, focused
evidence and blockers to the parent, which produces the single package delivery.

## Modular engine implementation: mandatory execution rules

For modular-engine implementation, read and follow section 0 of
`docs/knowledge/2a2b/REMAINING_MODULAR_ENGINE_WORK.md` and the mandatory priority
section of `docs/guides/modular-engine-implementation.md` before starting work.

**IMPLEMENTATION IS THE PRIMARY WORK.** Research, classification, tests and CSV
updates support implementation; they do not replace it or justify stopping while
assigned executable work remains. If a capability already works, reconcile it
briefly and move to a genuinely incomplete one; never manufacture changes.

Use selected affected cases or initially at most three directly affected test files.
Expand only for a new failure or explicit uncovered consumer risk. No broad suites
before final integration, no unchanged reruns to recover output, no full HEAD
comparisons, no repeated investigation of an identified concurrent blocker.
Preserve the exact initial base of isolated work before editing. Report capabilities
implemented, not test counts as progress. Preserve source correctness, admission
controls, concurrent ownership and mandatory CSV conservation checks.

**E2E IS COMPLETELY EXCLUDED, INCLUDING FINAL INTEGRATION.** Do not execute,
collect, investigate, repair or edit E2E tests, harnesses or corpus. Do not use
umbrella commands that include them or treat their failures as blockers. This
user instruction overrides historical plan references. Cancel your own accidentally
started prohibited battery; do not wait for or investigate its results.

Select minimal affected cases; a large parametrized file is still a broad battery.
Save useful output once outside the deliverable tree; filter it instead of rerunning.
Do not repeat global inventories or close clauses from binding/status flags alone.

CSV writes require authorized ownership, a complete byte snapshot before integration,
column names and `(id, clause_id)` keys, candidate conservation validation and a final
concurrency check. No snapshot or failed validation means no write. After damage,
suspend CSV writes and notify the coordinator; never reconstruct current cells from
HEAD or historical exports. Continue independent implementation where possible.
Prompts must repeat these limits explicitly, using the contract in plan section 0.


CSV access must use `python -X utf8 tools/knowledge/t13_csv.py`: `query`,
`prepare`, then `apply` (preview by default; `--write` only for the authorized
writer). No direct CSV edits or alternative rewrite scripts. See plan section 0
for commands and proposal format. Existing damage is not repaired by this tool.

These instructions do not authorize commits, pushes, scope expansion
or edits to files owned by other agents. Subagents are authorized within the
assigned package under the ownership rules above. `tests/E2E/modular-engine/cases/grants`
retains its external owner.
