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

## Pending problems and human decisions

Use `TODO.md` for concrete unresolved defects and problems.
