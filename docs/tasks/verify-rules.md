# Verifying rules

To consult the global status before editing specifications:

```powershell
python -m mordheim_combat_lab audit
```

The command generates `outputs/audit/rules-audit.csv`, encoded to open correctly in Excel. The output can be limited with `--scope YES`, `--status pending` and `--output <directory>`. It is a read-only operation with respect to the KB, the specifications and the code.

## Review questions and decisions

The CSV separates the work status (`review_status`) from the semantic evidence
(`semantic_status`). To see which decisions need an answer, filter
`review_status = needs_ruling`, not every `pending` row.

| review_status | Meaning |
| --- | --- |
| `needs_ruling` | There is an explicit question with no documented answer yet. |
| `blocked_by_dependency` | There is no unanswered question of its own, but a dependency still needs verification. |
| `ready` | Implementation work, source research or verification remains; there is no explicit unanswered decision or unverified dependency. It does not mean the rule already works. |
| `verified` | The required semantic evidence is approved. |
| `not_applicable` | Effect outside the active scope. |

To generate only the questions without replacing the full report:

```powershell
python -m mordheim_combat_lab audit --review-status needs_ruling --output outputs/audit/questions
```

`question` keeps the question even once it is resolved. `ruling` holds the
adopted answer and its rationale (source, section or user decision).
`interpretation` is the general explanation of the specification: it does not
imply that a question or an extra decision existed. The old explanations
exported as `ruling` now live in `interpretation`.

These data are edited in the corresponding YAML specification under
`tests/specs/semantic/`, **never manually in the generated CSV**. The status is computed;
`review_status` is not written into the YAML. Real resolved example:

```yaml
question: Does the Duelist of Hochland's Swordmaster grant re-rolling a failed
  parry in addition to matching the hit?
ruling: >-
  No. Resolved through the Hochland Bandits / Duelist / Swordmaster text: it only grants the tie and
  requires equipment that allows parrying. It does not grant a re-roll; sword plus buckler keeps its
  own independent re-roll.
```

If an answer is missing, omit `ruling` and keep `pending` with the reason for
the block. The loader rejects an unanswered question that is not marked pending.
When it is resolved, keep `question`, add `ruling` and remove or update
`pending` according to the remaining work. An answer does not verify the rule:
the scenarios, their dependencies and mutations must be updated and executed.
If the source changes, the footprint invalidates the previous evidence as before.

See `tests/specs/semantic/grants/editorial-hochland-swordmaster.yaml` for a resolved
question, and `tests/specs/semantic/rules/contextual-bonuses-and-rulings.yaml` for pending
questions. A decision history that was never documented is not automatically
rebuilt; it is incorporated while reviewing each specification.

## Procedure

1. Run `python -m mordheim_combat_lab verify --inventory`.
2. Add under `tests/specs/semantic/` the source, interpretation, category, cases, interaction and reviewed footprints.
3. Cover activation, non-activation, boundaries and consumption; use mini-sequences only for state or flow.
4. Declare exact dice and decisions; use fractions for distributions.
5. Add a mutation detected by behaviour, not only by the same compiled field.
6. Run `python -m pytest tests/verification/test_semantics.py -q` and `python -m mordheim_combat_lab verify --json`.

If a ruling is missing, mark it pending. Done when the obligation, dependencies, interactions and mutations are approved.

For equipment restrictions, `equipment_choices` runs the real compiler for every
`context.choices` construction and returns `result.accepted` and `result.rejected`
(with the exact reason). It does not compute legality by itself. See
`tests/specs/semantic/grants/editorial-savage-equipment.yaml`:
it checks legal weapons, prohibited armour and the neighbouring profile without
the restriction. A prohibition test must not pass merely because the item is not
in the warrior's list. The isolated mutation `suppress-bound-equipment-restrictions`
disables only that control and restores it on exit.

For skill choices, special rules, variants and `energy_focus_attacks`,
use `selection_choices`. It returns the accepted option lists and the exact
rejection reasons after calling the real compiler; it does not decide legality
by itself. The case must start from a valid construction and declare the
alternative selections in `context.choices`. See
`tests/specs/semantic/grants/editorial-required-initial-choices.yaml`:
it tests zero, one and two choices and temporarily removes the requirement with
`suppress-required-initial-choices` to prove the test detects its absence.

Distinguish an ambiguous source from an implementation limitation when writing
`pending`. A rule that also forbids acquiring upgrades after recruitment is not
verified by checking only its initial amount. The files
`tests/specs/semantic/grants/editorial-recruitment-and-magic-gaps.yaml` and
`tests/specs/semantic/rules/construction-verification-gaps.yaml` document those pendings;
they provide no approved evidence and do not all require a user decision.

## Interaction risk and priority

The audit separates technical risk from the current requirement:

| Field | Values |
| --- | --- |
| `risk_level` | `critical`, `high`, `medium`, `low` |
| `verification_requirement` | `required`, `recommended`, `optional`, `not_applicable` |
| `interaction_status` | `tested`, `covered_by_composition`, `independent`, `illegal`, `pending`, `needs_ruling` |

The policy lives in `tests/specs/interaction-policy.yaml`. By default, `critical` and
`high` are `required`, `medium` is `recommended` and `low` is `optional`. Only
unresolved required interactions block `semantic_complete`; the rest stay
visible to broaden coverage later.

The automatic classification starts from the concepts each rule reads and
writes. Persistent state, wounds and shared resources are critical; attacks,
priority and shared saves are high risk. A review can override the
classification through `overrides`, leaving reason and evidence:

```yaml
overrides:
- bindings: [<binding-a>, <binding-b>]
  risk_level: medium
  verification_requirement: recommended
  status: covered_by_composition
  risk_reasons: [generic_additive_operator]
  evidence: [operator:stack]
```

An override is a reviewed semantic decision, not a mechanism to make the report
pass. It must explain why a generic composition, an incompatibility or an
existing test covers the pair.
