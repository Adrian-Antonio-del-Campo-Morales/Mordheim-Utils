# Verification

Runs `tests/specs/` against the real modular engine and stays out of the UI.
`audit_export.py` combines — without modifying its sources — the editorial
inventory, the scope and the executed evidence into a CSV. See
[Verify rules](../../../docs/tasks/verify-rules.md).

`equipment_choices` allows testing equipment, `main_poison_id`, `off_poison_id`
and `preparation_ids` through the real compiler. Category-prohibition scenarios
require the specific reason for the rejection and a legal control without the
prohibition. The isolated mutation `suppress-category-prohibitions` removes
that validator for one execution; it neither modifies the KB nor turns an
absent equipment list into evidence of an explicit prohibition.

For mutation mini-sequences, `spines` invokes the round-start handler,
`extra_attack` resolves one compiled extra attack (explicit index) and
`attack_reaction` links a real attack with its wound reaction. They do not
compute hits, damage or probabilities on their own. Fixtures check the dice
requests, the loss of wounds and the absence of criticals where it applies.
`pool` additionally checks that the extra attack is added to the ordinary one.
