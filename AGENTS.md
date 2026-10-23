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

## Testing rework: verification and parallel execution

For tasks governed by `tests/TMP_TESTING_REWORK/REWORK_PLAN.md` and
`REWORK_PLAN_TASKS.md`, use the minimum verification needed for the assigned
change. These scope limits also apply to coordinators and delegated agents.

- Do not develop new tests, expand coverage or add improvements outside the
  assigned task. Reuse and adapt existing checks.
- Moves and path/configuration edits normally need syntax/import checks and
  targeted collection or test listing, not functional suites. Codec/exporter
  changes need focused data-contract checks; engine adapters need a small
  representative sample. Benchmark wiring needs a small smoke execution, not
  a performance or statistical campaign.
- Each agent verifies only its package. The coordinator groups shared
  collection/typechecks once on the integrated state and reuses valid evidence.
  Repeat a check only when relevant code, inputs or dependencies changed, or a
  defect introduced by the rework was corrected; record that reason.
- Do not run whole component suites or the full repository just to close a
  task. Broad functional certification is separate and requires an explicit
  request. Unrelated failures are reported without investigation or repair and
  do not block delivery of the assigned change; rework-caused defects remain
  the owner's responsibility.
- Parallelize independent Python checks using the existing xdist installation:
  `python -u -m pytest <affected-files-or-nodeids> -n 2 --dist=load -q --durations=10 --tb=short`.
  With several agents, default to two workers per active agent; a single
  integrated run may use four when resources are free. Avoid `-n auto`, nested
  pools and concurrent checks that write the same files. Keep timing-sensitive
  checks and shared-resource operations serial.
- The phased launcher keeps its existing phase barriers: use `test-sequence
  --workers N`; do not combine it with raw `-n` or `--dist`, or redesign its
  scheduler as part of this rework. Collection-only runs stay serial.
- Vitest already parallelizes files. Run selected files from their workspace
  with `--maxWorkers=2` while other agents are active; do not add concurrent
  test execution inside files. Do not parallelize benchmark measurements merely
  to accelerate verification or multiply inner engine workers by xdist workers.
- Keep live output, without `| tail`. Use persistent execution sessions and
  poll them. A tool timeout is not a reason to restart the whole selection:
  check whether the original process is still active and preserve completed
  evidence. Never interrupt another agent's processes.
- Record commands, selection, relevant revision or inputs, outcome and limits
  in the existing task document; do not create additional verification reports.
  Focused checks do not certify the full functional suite.

## Pending problems and human decisions

Use `TODO.md` for concrete unresolved defects and problems.
