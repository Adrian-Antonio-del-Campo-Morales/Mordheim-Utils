# Additional findings outside the original M01–M28 list

These were discovered while implementing the original audit. They are recorded
separately at the user's request. They do not change the original finding IDs or
serve as substitutes for closing their acceptance criteria. No further search
for additional issues is part of the current work.

| ID | Additional issue | Current state | Evidence |
| --- | --- | --- | --- |
| A01 | Broadsword Strongman exception was missed because it is not two-handed. | Corrected | `test_broadsword_strongman_exception_does_not_require_two_hands`. Source explicitly grants the exception. |
| A02 | Disease Dagger secondary damage reporting could lose infection damage or repeat acid reactions. | Corrected | Lethal infection and combined infection/dagger regressions verify aggregate damage and exactly-once retaliation. |
| A03 | Fire delayed Force of Will rescue until after later phase events. | Corrected | Successful/failed rescue regressions fail before the fix and pass afterward. |
| A04 | Burning inherited the opponent's offensive bonuses, armour denial and multiple damage. | Corrected | `test_burning_hit_does_not_inherit_opponents_offensive_effects` checks failed wound, armour save and one unsaved wound. |
| A05 | Kusara's minimum applied separately to Whipcrack and ordinary events. | Corrected | A1/A3 and selected off-hand whip cases verify phase-wide minimum, one-time suppression and original hand identity. |
| A06 | Spines and other synthetic hits could invoke the deliberate stunned finisher. | Corrected for the changed callers | Spines regression and explicit incidental-hit flags for Spines, acid blood and Black Hunger backlash. This does not certify every synthetic-effect interaction. |
| A07 | Guaranteed Lotus wound was treated as a failed wound for rerolls. | Corrected | Dark Steel/Sure Strike regressions retain the guaranteed wound without an extra failure reroll. |

Sources and interpretation history remain in the
[research ledger](modular-remediation.md). Tests are in
[test_source_corrections.py](../tests/combat/modular/test_source_corrections.py).
Required NumPy/native alignment is tracked in the
[candidate backlog](modular-engine-porting.md).
