# Project backlog

Track unresolved defects, verification work and deferred capabilities here.
Procedures belong in the linked guides; current counts and execution details
belong in maintained inventories and generated reports. Historical passes do
not certify the current tree, and unverified reports are not confirmed defects.

## Work overview

| Work | Current disposition | Next step |
| --- | --- | --- |
| Modular integration | Implementation received; strict E2E completeness remains unconfirmed | Check the live coverage inventory before claiming global closure. |
| Optimized engines | Both backends pass the full 43-scenario campaign at 100k duels against the stored modular references (NumPy 43/43 on 2026-11-02; native 43/43 on 2026-11-03 after five corrections) | Investigate the sub-gate shared offsets below with a fresh oracle sample before the next certification. |
| E2E statistical parity (modular vs NumPy) | 2,678 of 2,678 executable deliveries compared at 100k duels from the stored weekend samples; 2,625 approved, 53 divergent (2026-11-03) | Root-cause the 27 divergent mechanic groups listed below, worst gaps first. |

## Modular integration and E2E coverage

The user reports the modular checks green after removal of obsolete assertions
that optimized backends must reject supported rules. Construction expectations
were also updated for the native port. Neither result establishes full E2E
coverage or optimized-engine equivalence.

The last recorded strict E2E inventory (2026-10-21) had 27 identities with no
scenario and 44 with uncovered clauses. These are historical counts, not a
current measurement. Check `tests/integration/e2e/` and
`MORDHEIM_E2E_REQUIRE_COMPLETE=1` before closing that verification work.
Preserve the accepted-evidence non-regression baseline and clause identities;
read current pending clauses through `clause_registry.py query --pending`.

Completion requires the applicable integrated checks and strict E2E coverage
on the delivered revision. Follow the
[verification reference](docs/reference/verification.md#modular-integration-closure).
Do not rerun unaffected suites solely to refresh this backlog.

## Web projection verification

Verify Dwarf inheritance in the generated web projection. Close with
artefact-level evidence for `outputs/web-public/knowledge/knowledge-web.json`.
Generate the artefact with `python tools/knowledge/generate_knowledge_web.py`
if absent; do not hand-edit generated JSON.

## Combat Lab checklist popover closes during layout

Reproduce the unverified report of `TclError: bad window path name` after
`root.update()` in `tests/applications/combat_lab/ui/test_checklist_popover.py`:

- `test_popover_body_matches_the_dark_theme`;
- `test_popover_shows_a_visible_scrollbar`.

Determine whether widget lifecycle or test focus setup destroys the popover.
Close when both cases pass with theme, width and scrollbar assertions preserved.

## Optimized-backend verification

The vectorized implementation is integrated; do not reopen its completed port
from the obsolete October admission counts. Native implementation exists on
`native-engine-implmentation`, but its statistical acceptance is pending.
Implementation, focused rule tests and large-sample parity are distinct claims.

The seven native stored-sample divergences recorded here on 2026-10-28 were
root-caused and corrected on 2026-11-03 (see "Resolved native divergences"
below). Both backends now pass the full catalogue at 100,000 duels per
scenario against the stored modular references. Keep tolerances and reference
provenance intact. Qualify NumPy and native separately; native was ported
from the NumPy engine, so agreement between the two candidates never
exonerates a deviation they share — only the modular oracle does.

The renewed statistical catalogue still has explicit input limits:
`c03-petru-potion` needs out-of-scope campaign preparation, and
`v01-restriction` needs a charge rejected by construction. Keep these visible
as incompatible rather than substituting runnable scenarios. Do not treat
unexecuted profiles as accepted. Use the
[verification reference](docs/reference/verification.md) for campaign procedures.

### Vectorized findings awaiting focused confirmation

These findings were recorded on 2026-10-22. They have not been functionally
rechecked during this cleanup. Old source line numbers and percentages were
removed because the implementation has moved; reproduce the specific contract
before fixing it or declaring it resolved.

| Finding | Remaining check |
| --- | --- |
| Netted recovery stance (`v09-netted`) | Compare the victim's stance after cutting free and own-turn recovery; the current vectorized path excludes newly freed rows from standing. |
| Wounds after a helpless melee kill | Confirmed on 2026-11-02: NumPy subtracts wounds that the modular leaves unchanged. The deviation is confined to the wounds ledger (winner rates are unaffected), but it is also what keeps NumPy's damage-to-injury run alignment correct — a fix must restore the alignment the way the corrected native capture does (skip zero-damage entries), not merely stop subtracting. |
| Black Hunger backlash (`q11-black-hunger`) | Confirm that later backlash hits stop for inactive rows and that Force of Will is offered at the same stage as the modular. The current loop still uses the initial active-row set. |

## Knowledge gaps

| Follow-up | Completion condition |
| --- | --- |
| Resolve hireling `unresolved_references` | Replace references as canonical catalogues become available; keep genuinely unresolved links explicit. |
| Define composite-entity schemas | Establish schemas before admitting multi-warrior, mounted or multi-persona Dramatis Personae. |
| Make unsupported item-to-engine mappings explicit | Ensure catalogue presence cannot be mistaken for executable support. |
| Complete interface translations | Translate missing messages and remove unused keys. |
| Publish the remaining Knights Feats, if admitted to scope | Combat Charge, Lancer and Armour Specialist lack canonical executable records; keep them unavailable until their contracts and consumers exist. |

See the [knowledge-base reference](docs/reference/knowledge-base.md),
[campaign knowledge guide](docs/guides/campaign-knowledge.md) and
[web presentation conventions](docs/reference/web-presentation.md).

Scope changes are governed by
[`runtime-scope.yaml`](sources/knowledge/registry/runtime-scope.yaml);
accepted decisions belong in [Design rulings](docs/decisions/design-rulings.md).

## E2E statistical divergences, modular vs NumPy (2026-11-03)

Decided from the stored weekend sample stores (`outputs/parity-numpy-e2e`,
`outputs/parity-modular-e2e`; seed 2026, 100,000 duels per scenario, 50
rounds, six-sigma winner gate; report `reports/parity-final/parity-campaign.json`).
Totals: 2,678 compared, 2,625 approved, 53 divergent. The 13 formerly
unsampleable deliveries were repaired and integrated (11 approved, 2 joined
the divergent set). The modular oracle is authoritative.

The 53 scenarios are grouped below by the suspected root cause, from a static
comparison of `modular/` + `phases.py` against `vectorized/` (2026-11-03).
Hypotheses are code-reading conclusions, not confirmed fixes; reproduce each
before correcting.

### RC1 — attack path uses the legacy armour-save helper (11 scenarios)

`vectorized/_attacks.py:948` and `:1389` call the old `armour_targets`
(`_operators.py:247`) instead of the faithful ports `armour_context` /
`armour_target_values` (`_operators.py:1083/1156`), which are never called.
Ladle's shield-only override, Cutthroat's +1 armour penetration, Norse
Bulwark's axe-and-shield improvement, the fist save-bonus exception and
knocked-down armour ignoring are all dropped. One call-site swap is the
candidate fix.

- `e2e/mechanic/weapon.ladle/ladle-denies-a-worn-suit-its-save`
- `e2e/mechanic/weapon.ladle/ladle-leaves-the-shields-own-save-available`
- `e2e/mechanic/weapon.ladle/ladle-shield-save-fails-on-five`
- `e2e/mechanic/skill.cutthroat/cutthroat-dagger-pair-worsens-the-save`
- `e2e/rule/mordheim/silent-brotherhood-sc/band--skill-cutthroat/skill.cutthroat/cutthroat-dagger-pair-worsens-the-save`
- `e2e/mechanic/mechanic.norse-bulwark/an-axe-and-shield-save-holds-on-five`
- `e2e/mechanic/mechanic.norse-shieldmaster/the-shield-parries-the-blow`
- `e2e/mechanic/mechanic.norse-shieldmaster/the-same-shield-still-contributes-its-save-throw`
- `e2e/mechanic/weapon.disease-dagger/disease-dagger-improves-a-worn-save-by-one`
- `e2e/mechanic/weapon.disease-dagger/disease-dagger-worn-save-fails-one-below-the-improved-target`
- `e2e/mechanic/weapon.misericordia/misericordia-keeps-the-dagger-penalty-against-a-standing-opponent`

### RC2 — injury roll rebuilt inline instead of using `injury_context` (4 scenarios)

`vectorized/_attacks.py:1188-1205` rebuilds the injury context by hand; the
faithful port `_operators.injury_context` (`_operators.py:1425`) has no call
sites. The inline copy misses the squishy gate on No Pain, Blessing of
Morr's +1 against undead, and inured-to-pain.

- `e2e/mechanic/rule.squishy/no-pain-cannot-quiet-the-stun-under-squishy`
- `e2e/rule/mordheim/ghost-pirates-sar/the-bloated--squishy/rule.squishy/no-pain-cannot-quiet-the-stun-under-squishy`
- `e2e/mechanic/mechanic.blessing-of-morr/the-bonus-lifts-the-injury-roll-to-a-stun`
- `e2e/rule/mordheim/vampire-hunters-of-sylvania-lotd5/band--special-skill-blessing-of-morr/mechanic.blessing-of-morr/the-blessing-lifts-the-injury-roll-to-a-stun`

### RC3 — Wheelo impact hits are unported (3 scenarios)

`modular/rounds.py:1081-1110` resolves impact hits before any blow, with the
spear/morning-star/axe/club fittings; nothing in `vectorized/` implements the
step (`wheelo` appears only in `_psychology.py:461`).

- `e2e/mechanic/mechanic.wheelo-impact/a-charging-wheelo-resolves-its-impact-hits-before-any-blow`
- `e2e/mechanic/mechanic.wheelo-skill-modifications/the-spear-fitted-wheelo-still-hits-a-charger-once`
- `e2e/mechanic/mechanic.wheelo-skill-modifications/the-morning-star-first-impact-resolves-at-strength-five`

### RC4 — special-event scheduling diverges (whip split, bite gating) (4 scenarios)

`vectorized/_driver.py:2266` splits the whip bonus on `charge | charged`
(modular splits only when charged, `modular/rounds.py:1417`), and uses a
fixed priority tier (`_driver.py:2470`) instead of `max(1, whip.priority)`.
The strikes-last bite (`_driver.py:2660-2678`) skips the attack-count gate
and the `main_hand_slot='natural'` / poison-stripping of
`modular/rounds.py:1379-1389`. `_tentacle_forfeit` (`_driver.py:656`) reuses
the whip rows and marks one forfeit per battle instead of per phase.

- `e2e/mechanic/weapon.serpent-whip/serpent-whip-bonus-strikes-first-when-its-bearer-is-charged`
- `e2e/rule/mordheim/shallows-beasts-mim/mutant-priest--bite-attack/compiler.strikes-last-bite/the-bite-is-an-extra-attack-that-strikes-after-the-weapon-attacks`
- `e2e/rule/mordheim/shallows-beasts-mim/mutant-priest--bite-attack/compiler.strikes-last-bite/the-bite-uses-the-priests-own-strength-not-the-weapons-bonus`
- `e2e/rule/trollheim/trollheim-cult-of-the-possessed/band--mutations-tentacle/special-rule.band--mutations-tentacle/without-the-mutation-the-attacker-keeps-both-attacks`

### RC5 — Centigor Drunken shared-ledger expiry bug (3 scenarios)

NumPy stores one `ledger.drunken_result` array for both sides
(`_driver.py:779/818`) and its expiry step (`_driver.py:1832-1839`) clears a
fresh roll on the owner's own turn, so a roll of 1 never forces Stupidity
and the round-0 charge cancel never happens — which is why modular leaves
~15% unresolved and NumPy 0%. The expiry also resets the wrong side's state.

- `e2e/mechanic/mechanic.centigor-drunken/results-two-to-five-do-nothing`
- `e2e/mechanic/mechanic.centigor-drunken/a-roll-of-six-grants-frenzy`
- `e2e/mechanic/mechanic.centigor-drunken/a-roll-of-one-forces-the-stupidity-test`

### RC6 — ad-hoc test rolls instead of the shared test helpers (9 scenarios)

Tranquil Fauna rolls one D6 against Leadership (`_driver.py:438-439`) where
modular rolls 2D6 (`modular/rounds.py:902`, `phases.py:908`). Force of Will
and Contagious use `_characteristic_test` without the `require_characteristics`
guard or the Blessed Sight reroll, and Contagious also drops the
`reactive_damage > 0` trigger condition (`_attacks.py:1286` vs
`modular/aftermath.py:81-95`). Audit every inline `rng.integers(1, 7, ...)`
test in `vectorized/` against the modular helper it shadows.

- `e2e/mechanic/mechanic.taal-tranquil-fauna/a-handled-animal-attacks-only-on-its-handlers-passed-test`
- `e2e/mechanic/mechanic.taal-tranquil-fauna/a-handled-animal-that-fails-its-handlers-test-cannot-attack`
- `e2e/mechanic/mechanic.force-of-will/a-failed-test-leaves-him-out`
- `e2e/mechanic/mechanic.force-of-will/the-toughness-test-stands-him-back-up`
- `e2e/rule/mordheim/pit-fighters/band--pit-fighter-skill-force-of-will/mechanic.force-of-will/a-failed-test-leaves-him-out`
- `e2e/rule/mordheim/pit-fighters/band--pit-fighter-skill-force-of-will/mechanic.force-of-will/the-toughness-test-stands-him-back-up`
- `e2e/rule/trollheim/chaos-streets-pit-fighters/band--pit-fighter-skill-force-of-will/mechanic.force-of-will/a-failed-test-leaves-him-out`
- `e2e/rule/trollheim/chaos-streets-pit-fighters/band--pit-fighter-skill-force-of-will/mechanic.force-of-will/the-toughness-test-stands-him-back-up`
- `e2e/rule/mordheim/skaven-clan-pestilens/band--clan-pestilens-special-skills-contagious/unimplemented.skaven-clan-pestilens.band.clan-pestilens-special-skills-contagious/the-same-selection-with-rotten-body-is-accepted`

### RC7 — control-power and compulsion qualifiers dropped or mis-ordered (5 scenarios)

NumPy's seduction (`_driver.py:518-548`) ignores `male_only`, the Khemrian
`own_test` pre-test, and copy-specific exemption lists
(`modular/rounds.py:130-137, 1018-1027`) — both seduction cases converge on
the no-effect baseline (0.800). The addicted Alchemist loses his attacks in
modular (`modular/rounds.py:1258, 1365`) but still fights in NumPy.
Enchanting Beauty's -1 tag is applied after the Stupidity test
(`_driver.py:2017` vs modular `rounds.py:425/674`), so the penalty misses
the test it should flip. The transform residual (~1.4pp) is unexplained; the
cast-off itself is ported — check the Madness Stupidity on `bitten_result == 1`.

- `e2e/rule/trollheim/chaos-streets-undead-bloodlines/band--lahmia-power-seduction/unimplemented.band-lahmia-power-seduction/a-female-target-is-outside-the-printed-recipient`
- `e2e/rule/trollheim/khemri-lahmian-brotherhood/band--lahmian-special-skills-seduction/unimplemented.khemri-lahmian-brotherhood.band.lahmian-special-skills-seduction/a-failed-own-test-leaves-the-victim-unbarred`
- `e2e/rule/trollheim/chaos-streets-undead-bloodlines/lahmia-vampire--enchanting-beauty/unimplemented.chaos-streets-undead-bloodlines.lahmia-vampire.enchanting-beauty/the-printed-penalty-turns-a-passing-total-into-a-failure`
- `e2e/rule/mordheim/masters-of-horror-sylv/mad-scientist--alchemist/unimplemented.masters-of-horror-sylv.special.alchemist/the-supplied-addicted-scientist-takes-no-action-of-its-own`
- `e2e/rule/mordheim/masters-of-horror-sylv/the-bitten--transform/unimplemented.masters-of-horror-sylv.the-bitten.transform/transforming-casts-off-the-worn-armour`

### RC8 — cause not yet located by static reading (14 scenarios)

The ported predicates compared equal line for line; the deviation is
upstream of them. Candidates: which enemy tags reach the compiled hatred
qualifier, NumPy's whole-batch scalar `being-charged` for Pikewall
(`_operators.py:741` cannot vary per row when charges are cancelled),
`ledger.animosity_failed` cleared every round for Fungus Brew
(`_driver.py:1851`), and the callers of the identical `leader-six` aura
check (`vectorized/_leadership.py:86-128`). Trace these before fixing.

- `e2e/rule/mordheim/crooked-moon-kep/band--hate-stunties-and-skaven/mechanic.hatred-dwarfs-skaven/a-first-round-miss-is-rerolled-against-a-qualifying-dwarf`
- `e2e/rule/mordheim/crooked-moon-kep/band--hate-stunties-and-skaven/mechanic.hatred-dwarfs-skaven/the-printed-exempt-profile-receives-no-reroll`
- `e2e/rule/mordheim/crooked-moon-kep/band--hate-stunties-and-skaven/mechanic.hatred-dwarfs-skaven/the-same-miss-stands-without-the-qualifying-dwarf`
- `e2e/rule/mordheim/night-goblins-mic/band--hate-stunties/unimplemented.night-goblins-mic.band.hate-stunties/a-first-round-miss-is-rerolled-against-a-qualifying-dwarf`
- `e2e/rule/mordheim/night-goblins-mic/band--hate-stunties/unimplemented.night-goblins-mic.band.hate-stunties/the-printed-exempt-profile-receives-no-reroll`
- `e2e/rule/mordheim/night-goblins-mic/band--hate-stunties/unimplemented.night-goblins-mic.band.hate-stunties/the-same-miss-stands-without-the-qualifying-dwarf`
- `e2e/mechanic/mechanic.pikewall/the-charged-pikeman-rerolls-a-failed-hit`
- `e2e/rule/mordheim/house-guard-sc/pikemen--pikewall/mechanic.pikewall/the-charged-pikeman-rerolls-a-failed-hit`
- `e2e/rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew/a-supplied-rowdy-result-suppresses-the-affected-warriors-attacks-on-a-rolled-two`
- `e2e/rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew/the-widened-rowdy-band-stops-at-two-so-a-rolled-three-leaves-the-attack-standing`
- `e2e/rule/mordheim/night-goblins-web/shaman--fungus-brew/unimplemented.night-goblins-web.shaman.fungus-brew/the-supplied-numbed-result-gives-the-printed-six-plus-save-against-a-strength-six-blow`
- `e2e/rule/mordheim/night-goblins-mic/big-boss--leader/mechanic.leader-six/a-leader-beyond-the-printed-radius-supplies-nothing`
- `e2e/rule/mordheim/night-goblins-mic/big-boss--leader/mechanic.leader-six/a-supplied-leader-on-the-other-side-supplies-nothing`
- `e2e/rule/mordheim/night-goblins-mic/big-boss--leader/mechanic.leader-six/a-supplied-leader-that-is-not-standing-supplies-nothing`
