# Modular source audit remediation

Current per-finding status: [M01–M28](modular-audit-status.md).
Issues discovered afterward: [additional findings](modular-additional-findings.md).
The chronological notes below preserve research history; their older pending
lists are superseded by the current status table.

Work started 2026-09-05. This is the implementation ledger for audit findings
M01–M28. The user authorized independent source research, correction of every
substantiated error, and documentation of any unresolved case while continuing.
The original audit remains in `outputs/modular-audit-2026-09-05/`.

## Research and decision procedure

For each finding, compare the complete source clause and exceptions, incorporated
KB, actual consumers, and recorded `question`/`ruling`/`interpretation`. Preserve
explicit editorial decisions. An interpretation describing existing code is
not by itself evidence that the code matches the source. Expected results must
be written independently before repairs. Existing tests may need corrections
where their expectations embody the audited error; never refresh source digests
without reviewing the corresponding text and evidence.

## Characteristics, priority and defenses: research completed

- M04/M05: [weapons](https://mordheimer.net/docs/weapons-armour/close-combat)
  and [FAQ](https://mordheimer.net/docs/faqs), Strike Last and spear-versus-spear.
  The unconditional first-round `max` erases negative priority. Charged spears
  also receive a fabricated tier. No explicit editorial ruling authorizing
  either was found. Strongman remains an exception; equal first-strike tiers
  compare Initiative.
- M06: [Crimson Shade](https://mordheimer.net/docs/weapons-armour/miscellaneous-equipment).
  Initialization already records the preparation in state, but round priority
  reconstructs the base from the compiled fighter. Preserve static bonuses and
  substitute the actual state characteristic, without counting modifiers twice.
- M11: [Eshin](https://mordheimer.net/docs/warbands/grade-1a-warbands/skaven-eshin)
  and [Dwarf Treasure Hunters](https://mordheimer.net/docs/warbands/grade-1a-warbands/dwarf-treasure-hunters).
  Equipment rerolls are independent of the separately documented Swordmaster
  equality-only ruling. The consumer omits claws and ordinary paired axes.
- M19/M20: [Characteristics](https://mordheimer.net/docs/rules/characteristics),
  zero values and characteristic tests. WS0 is an automatic hit; a natural six
  fails a characteristic test. The current numeric hit target and helper default
  contradict these clauses. Opposed rolls and Leadership tests are different
  operations and are not changed by this conclusion.
- M26: [Fist](https://mordheimer.net/docs/weapons-armour/close-combat), maximum
  attacks; retain named unarmed exemptions. The current cap is overwritten by
  the later frenzy multiplier.
- M28: [Untiring](https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard).
  Existing KB and semantic interpretation correctly distinguish magical denial.
  An unconditional final floor erases the distinction. Ordinary magical attacks
  which do not deny armour must still retain the floor.

Regression evidence: `tests/combat/modular/test_source_corrections.py`.
Implementation and broader semantic/candidate certification are in progress;
this ledger does not assert completion of any gate yet.

## Remaining findings

M01–M03, M07–M10, M12–M18 and M21–M25/M27 remain under investigation and
implementation. In particular M18 needs the custom/Trollheim source; M07 needs
an explicit mapping of player turns to simulated phases, and M23 needs an
independently justified rescue sequence. These are not silently considered fixed.

## Phase ownership and sequential effects: research completed

- M02/M03: [Close Combat](https://mordheimer.net/docs/rules/close-combat),
  attacking stunned warriors and parrying. A same-warrior sequence retains its
  pre-attack eligibility; a natural six cannot be skipped to parry a lower hit.
  The named Blood Dragon exception is preserved.
- M07: [Recovery](https://mordheimer.net/docs/rules/recovery) and
  [The Turn](https://mordheimer.net/docs/rules/the-turn). Adopt one iteration per
  player-turn combat phase, starting with the charger's turn. Both fighters
  reset phase resources, but only the active player's fighter recovers or tests
  paralysis/fire. This is derived from the published alternating sequence;
  no explicit contrary project ruling was found. It replaces simultaneous
  recovery rather than changing the documented Black Hunger activation policy.
- M21/M22: [Spider Spittle](https://mordheimer.net/docs/weapons-armour/miscellaneous-equipment).
  The test is immediate on an undefended hit, before wound/saves. Paralysis
  grants automatic hits without knockdown's automatic elimination. A parry
  discards the blow; it therefore prevents its poison trigger.
- M23: [Force of Will](https://mordheimer.net/docs/warbands/grade-1b-warbands/pit-fighters).
  Adopt immediate rescue when OOA occurs, before later prepared attacks. The
  source's trigger and explicit second-OOA removal support this sequence;
  waiting until discarded hits cannot be resolved makes the second-removal
  clause ineffective within a multi-hit attack. This is a recorded timing
  interpretation, not a newly discovered explicit FAQ.
- M24: [Brazier Iron](https://mordheimer.net/docs/weapons-armour/close-combat).
  Burning damage is a hit, not an intentional melee finisher. The synthetic
  fire call now declares this distinction explicitly.

Targeted regression checks currently pass; full corpus migration and candidate
certification remain pending. The earlier remaining-work list is the initial
queue, not a statement that these subsequent repairs have not been started.

## Critical resolution and weapon data: research completed

M01 uses the [basic critical table](https://mordheimer.net/docs/rules/close-combat)
already referenced by the canonical core rule. The
[weapon-family tables](https://mordheimer.net/docs/optional-rules/mordheim-rulebook-optional-rules/new-critical-hit-charts)
are optional and are not silently enabled. Existing Web of Steel/interaction
interpretations collapsed critical results into an Injury modifier; the full
source does not justify that approximation. A separate result roll now governs
damage, armour denial and Injury modification. Table bonuses modify that roll.
This is a semantic correction to the documented approximation, not the addition
of an optional game mode. Multiple-damage effects use the greater result.

M08 uses [Pistol / Hand-to-hand](https://mordheimer.net/docs/weapons-armour/blackpowder):
the binding's extra penetration must exclude the modifier already contributed
by fixed Strength. M13 restores the Brass Knuckles and Cat disadvantages from
the complete [weapon entries](https://mordheimer.net/docs/weapons-armour/close-combat).
The Cat entry also contains Whipcrack, now included in M12's repair scope.
M14 follows [Dark Elf Blade](https://mordheimer.net/docs/warbands/grade-1b-warbands/dark-elves):
critical-table modification and the stun boundary are separate properties.
No explicit editorial override of these clauses was found; old local tests
reflect the truncated data rather than a documented intentional ruleset change.

M15 follows [Black Lotus](https://mordheimer.net/docs/weapons-armour/miscellaneous-equipment):
an optional critical attempt cannot remove the guaranteed wound. Default
acceptance follows the simulator's existing DecisionPolicy; explicit decline
skips the extra roll. The general critical eligibility restrictions remain.

## Stateful equipment: research completed

- M09: brace shots are limited to two. After the first combat turn, the simulator
  uses an available non-pistol hand weapon, otherwise the KB-compiled unarmed
  fallback. No undeclared spare dagger is invented. Equipment projection happens
  before priority, parry resource initialization and attack counting.
- M10: full Rapier Barrage supports repeated attempts, cumulative hit penalties
  capped at 6, ordinary Strength and enemy armour bonus. Each continuation uses
  the actual attack pipeline, including defenses, poison, saves and criticals.
- M12: Steel Whip, Beastlash and Cat share the published Whipcrack clause. A charge
  adds one whip attack after other modifiers. A charged warrior gets a separate
  first-strike bonus; ordinary attacks retain their timing. Both hands together
  receive only one Whipcrack bonus. Existing Serpent Whip support is retained.
- M16: variable damage is a generic compiled die, composed by maximum and resolved
  after saves. Ball and Chain also retains the source's incoming hit penalty.
- M17: [Disease Dagger](https://mordheimer.net/docs/warbands/grade-1b-warbands/skaven-pestilens)
  requires an immediate test on a natural hit six, with Undead/Possessed immunity.
  The additional automatic wound is separate from the normal dagger wound.
  Source interpretation: no explicit armour-denial clause exists for infection,
  so the general saving rules apply without a weapon Strength modifier. This
  timing/save interpretation is recorded here for review rather than represented
  as an explicit FAQ. Additional wound reactions resolve immediately.
- M18: the full original Spanish compilation was located in
  [Caos en las Calles, p.158](https://es.scribd.com/document/542601712/Caos-en-Las-Calles).
  The original audit probe incorrectly expected a one-Attack opponent to lose its
  last attack. Retract that expectation: the source retains a minimum of one.
  The actual defect is that the current reply count was computed before the hit
  penalty. Apply the penalty to the upcoming reply, expiring at the next combat
  phase. The source permits selecting the hampered weapon. The modular repair now
  records that choice and removes an attack of the selected hand after allocation,
  retaining the minimum of one. A dagger/axe reply regression distinguishes the
  two choices by their actual saving modifiers. Candidate certification remains open.
- M25: Trap Blade rolls after successful parries, persists the unusable hand and
  uses the surviving weapon/unarmed fallback in subsequent attack phases. Natural
  unarmed attacks have no manufactured weapon to break. Sequence interpretation:
  hits already rolled before the parry retain their original weapon for wound
  resolution; subsequent attack phases use the changed equipment. Review this
  interpretation separately from the unambiguous missing trap roll.
- M27: full Serpent Staff wording supplies the previously truncated power. Its
  optional mode is chosen before priority, uses fixed WS4/S4 and one attack,
  suppresses extra attack pools, and forfeits parries for that phase. The old
  claim that the published rule lacks details is withdrawn.

Sources for M09/M10/M12/M16/M25/M27 are the full weapon paragraphs linked above.
Source updates do not imply that every historical spec is already migrated.

## Validation checkpoint after resuming concurrent project work

Starting HEAD remains `5bffcca`. Campaign, catalogue and CLI work added concurrently
by the user is outside these engine repairs and is retained. Validation guidance
was reread after resuming; the larger statistical matrices are not used in the
per-edit loop.

- The migrated existing semantic corpus reached **617/617**, zero errors and zero
  pending obligations. This is a checkpoint, not proof of branches absent from the
  historical corpus. Further stateful regression cases are being added.
- Eleven baseline invalidated fingerprints were proved against `681dc40`: the
  rules, profiles, band and equipment data were identical except for explicit
  `price_override` fields introduced in `5bffcca`. Only those proven fingerprints
  were refreshed; evidence is in `reviewed-context-digests.json` in the audit output.
- Parity replay of individual attack cases previously invented maximum dice when
  the supplied sequence ended and ignored unused dice. It now rejects both for
  attack replay (finite enumeration permits unused suffixes, but not exhaustion).
  This exposed omitted Lotus decisions, spurious helmet rolls and omitted injury
  choices; the NumPy consumers were corrected.
- NumPy parity reached 3733 passing cases and zero divergences at that checkpoint.
  Three pre-existing pending cases concern Averlander promoted halflings and the
  missing Lad's Got Talent construction model. They are unrelated to M01–M28 and
  remain explicitly pending; the certificate is not presented as complete.
- Subsequent targeted tests reached 110 passing modular tests and 158 passing
  modular/NumPy tests at their respective checkpoints. Rerun after later edits.
- Infection now reports its extra damage and records already-resolved reactions,
  preventing duplicate acid retaliation if it kills before the normal dagger wound.
- Broadsword has an explicit Strongman exception despite not using two hands.
- Spines, acidic blood and Black Hunger backlash use hit resolution rather than
  deliberate melee finishing, following their full published hit clauses. The
  existing automatic Black Hunger activation convention is retained.

Remaining implementation/certification work includes stateful candidate ports
(equipment loss, chosen-hand penalties, Serpent Staff, split Whipcrack timing,
immediate Force of Will), native backend alignment, and final L0–L4 checks. No
completion claim follows from the passing historical corpus alone.

## Scope update: modular implementation only

At the user's request on 2026-09-05, further implementation and certification
focus on the modular engine. Candidate work is deferred to the explicit
[NumPy/native porting backlog](modular-engine-porting.md). Existing candidate
edits remain partial and must not be treated as certified.

Force of Will was rechecked against the Pit Fighters source: its OOA trigger is
not limited to ordinary melee attacks. Fire recovery previously delayed rescue
until after Spines. It now resolves rescue before returning its outcome. Both
successful and failed rescue have source-derived regressions, reproduced failing
before the correction. No contrary editorial ruling was found.

The Brazier Iron Fire clause was also rechecked: subsequent burning causes an
independent S4 hit. `_fire_recovery` used the opponent as the synthetic attacker
and consequently inherited its global wound bonuses, rerolls, armour denial and
damage. The fire source now has neutral offensive effects while retaining the
victim's real defenses. Regression coverage demonstrates a failed wound, a
successful armour save and exactly one unsaved wound. The failing pre-fix test
reached Injury because an unrelated opponent damage bonus was applied.

Latest gates before this additional fire isolation: 112 modular tests and 64
structural/architecture/phase tests passed; semantic verification reports
structural_complete and semantic_complete. The structural snapshot changed
54 to 55 specifically for the new consumed damage_die_sides field, with its
consumer verified in modular/attacks.py. This is not a blanket snapshot refresh.

Kusara/Whipcrack interaction: the one-Attack minimum is per warrior, not per
separately timed event. Reproduction with a charged A1 whip incorrectly kept
both attacks. Pools now receive the phase-level minimum and consume each
selected-hand suppression once. Whip bonus projection retains the original
hand slot. Regressions cover A1, A3 (prevent double consumption), and an off-hand
whip selected by the Kusara wielder. The stored penalties now represent pending
suppressions, while the phase reset still expires unused entries.
