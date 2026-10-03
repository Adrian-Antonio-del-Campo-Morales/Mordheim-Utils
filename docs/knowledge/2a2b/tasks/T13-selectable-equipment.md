# T13.2d — Traceability and coverage of selectable rules and equipment

L05 construction checkpoint — 2026-10-03: [current delivery](T13-canonical-choices.md) supersedes the historical missing named-table/access routes, eight false markers and incomplete Runt active-equipment binding below. Seven pending recipient channels and configured Bloodline access are corrected; remaining source/effect gates are explicit. The retained CSV is entry evidence, not a current implementation claim.

Current partition update — 2026-10-03: [L04 canonical Shifty activation](T13-shifty.md#l04-canonical-activation--2026-10-03)
adds the existing Shifty origin to this live selection partition: **55 origins /
54 canonical rules**, of which 11 origins / 10 rules are implemented; 44 remain
pending. The 95 equipment origins are unchanged. The maintained matrix includes
Shifty, with its canonical selection and combat evidence in the L04 suite. The
historical CSV and original 54-origin counts below retain their entry meaning.

> Current ownership — 2026-10-02. This is an accepted historical traceability/test delivery, not a current inventory of unimplemented validators. Both products now use the existing [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation); Python decision references below identify the examined adapter revision. The companion CSV retains that historical snapshot. Before dispatching any old availability, recipient or restriction finding, [F035 in the follow-up register](T13-execution-follow-ups.md) must classify current canonical facts, the shared decision, transport and the separate runtime-support/compiled-effect gate. Accepted observations and counts are preserved; no finding is closed by this note.

Scope: legal selection and compilation of the **selectable rules** and **equipment**
already wired to the runtime. This lot traces availability → prerequisite →
selection → binding → compiled property and pins acceptance, recipient
exclusion and the refusal of all 44 pending selectable rules; equipment origins
are traced individually, without claiming runtime-refusal tests for all items.
It implements no new
mechanics, resolves no open T13-Q question and promotes no implementation flag.
Accepted by the coordinator on 2026-10-01 as a traceability and construction-test
lot only; T13.2 is **not** certified as a whole.

- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`.
- The tree was dirty with parallel T13.1 / T13.2a / T13.2b, Shifty, Spectral
  Touch and Combat Lab work; none of it was touched.
- Reservation checked before writing: the active-reservation table in
  [README.md](../README.md) **does** carry the T13.2d row (external agent B,
  reserved 2026-10-01, "sin cambios de producción"). `README.md` was read, not
  edited.
- `compiler.py`, `contracts.py`, `selection.py`, the models, engines, KB,
  existing specs and both languages are read-only for this lot.

## Sources

| Source | Use |
| --- | --- |
| [T13-obligations.csv](T13-obligations.csv) | register paper: read as UTF-8 **with BOM**, `lots` parsed as JSON |
| `sources/2A/…`, `sources/2B/…` | staging origins (`origin_key`, provenance) |
| `sources/knowledge/…` | canonical rules, items, mappings, execution parameters |
| `docs/knowledge/2a2b/tasks/T13.md` | phase contract and T13-Q register |
| [T13-implementation-plan.md](T13-implementation-plan.md), [T13-inventory.md](T13-inventory.md) | partition definitions |
| [T13-contracts.md](T13-contracts.md), [T13-characteristic-bonuses.md](T13-characteristic-bonuses.md), [T13-bloated-foulness.md](T13-bloated-foulness.md) | accepted decisions reused as evidence |
| [implement-and-verify-rules.md](../../../guides/implement-and-verify-rules.md), [design-rulings.md](../../../decisions/design-rulings.md) | governing rules |

Expected values and recipients in the tests come from these sources — canonical
KB plus accepted decisions — **not** from compiler output.

## Partition (recomputed)

Selection rule (per the dispatch): T13.2 origins of `family=band-rule` whose
canonical `runtime.grant == "selectable"`, plus every `family=item` origin.

| Metric | Value |
| --- | --- |
| T13.2 register origins (all families) | 1,045 |
| T13.2 `band-rule` origins | 883 (grants: profile 636, band 193, **selectable 54**) |
| T13.2 `item` origins | 95 |
| **This partition** | **54 selectable origins + 95 equipment origins** |
| Selectable origins sharing a canonical rule | 1 (Master of Blades: `skill.unbeatable-warrior` + `skill.sword-master`) → 53 unique canonical rules |

The 54/95 figures match the orientation in the dispatch. The remaining T13.2
origins — hireling 62, spell 5 and the 829 non-selectable `band-rule` grants —
are **excluded**: automatic grants belong to another agent's partition and
T13.0 was not rebuilt.

Selectable kinds: `warband_skill` 52, `profile_ability` 2.
Selectable dispositions: `included` 47, `mixed` 7.

### KB ↔ register reconciliation

**Selectable.** The canonical KB publishes 437 selectable (file, id) pairs; only
53 have a T13.2 register row. Classification of the 437: `partition` 53,
`no_register_row` 322, `other_file` 37, `other_lot` 25 (all `implemented=NO`).
Of the 53 rules inside the partition, 9 are `implemented=YES` and 44 are `NO`.
The coverage test resolves every T13.2 `band-rule` register row (883) against
its canonical YAML file and rule node; all of them resolve.

**Equipment.** The KB publishes 470 item nodes; the register holds 144 items,
95 of them with T13.2. The 375 KB item nodes without a T13.2 row split into 254
`out_of_scope` and 121 `implemented`. Every one of the 144 register items has a
KB node (0 orphans).

## Selectable rules

### Runtime marked implemented (9 rules, 10 origins)

Eight rules have the compiled properties below. Vomit Attack has recipient-routing
evidence only and remains a projection discrepancy despite its implementation flag.

| Rule (canonical id) | Recipient proved | Compiled property |
| --- | --- | --- |
| `band--special-skill-hardy-constitution` | grave-robbers-sylv / graver | `global_effects.poison_immunity=True`, tag `poison_immune` |
| `band--dwarf-special-skills-master-of-blades` *(2 origins)* | clan-angrund-kep / dwarf-noble | tags `skill.unbeatable-warrior`, `skill.sword-master`, `rule.dwarf-axe-parry-reroll` |
| `band--dwarf-special-skills-true-grit` | clan-angrund-kep / dwarf-noble | `out_of_action_threshold=6`, already band-wide; **no double application** |
| `band--dwarf-special-skills-thick-skull` | clan-angrund-kep / dwarf-noble | tag `concussion_immune`, already band-wide; **no double application** |
| `band--slayer-special-skills-ferocious-charge` | clan-angrund-kep / dwarf-troll-slayers | tag `skill.ferocious-charge` |
| `band--slayer-special-skills-monster-slayer` | clan-angrund-kep / dwarf-troll-slayers | tag `skill.monster-slayer` |
| `band--slayer-special-skills-berserker` | clan-angrund-kep / dwarf-troll-slayers | tag `skill.berserker` |
| `band--lizardmen-special-skills-saurus-only-bellowing-battle-roar` | lizardmen-lus / saurus-totem-warriors | tag `skill.bellowing-battle-roar` |
| `warpstone-troll--vomit-attack` | underworld-alliance-mim / warpstone-troll | **discrepancy** — `weapon.vomit-attack` binding accepted but not projected |

**Control choice.** Every selectable rule in this partition is an *optional*
choice, so the neutral control is the same fighter compiled **without** the
optional `special_rule_ids` entry (never the absence of a mandatory pick, which
is not a legal roster). For True Grit and Thick Skull the control also holds
the band-wide grant, which is why the compiled `global_effects` must be
identical with and without the selectable copy.

### Pending with an availability channel (35 origins) — pendiente de implementación

`available_special_rules` really offers each of these (the band publishes the
`special` skill access and/or the rule names its recipient), but
`compile_fighter` refuses them with:

`special rule is outside the executable duel runtime: <rule>: <published runtime reason>`

The suite asserts that exact prefix, the canonical rule id and the rule's own
published reason for: `dreamwalkers-cult-of-morr-fbg` (inspiring-presence,
fanatical, inured-to-horror); `grave-robbers-sylv` (darkstalker,
instinctual-violence, de-animator); `necrarchs-the-soul-stealers-lotd1`
(pull-of-undeath); `vampire-hunters-of-sylvania-lotd5` (iron-will,
righteous-aura, thirst-for-vengeance, blessing-of-morr);
`wood-elves-of-athel-loren-web` (elven-luck); `brood-of-ghurash-the-sc`
(the-terror, ground-pounder, titanic-strength, hurl);
`call-of-the-night-haint-mim` (wight-walk); `clockworkers-sc` (puppeteer,
rogue-control, gift-of-sentience); `high-elves-lus` (miniath, unerring-strike,
fey-quickness); `knights-of-the-bitter-moors-mim` (virtue-of-valour,
virtue-of-discipline, virtue-of-noble-disdain, virtue-of-the-impetuous);
`lizardmen-lus` (saurus-only-toughened-hide); `silent-brotherhood-sc`
(cutthroat, hit-and-run, backstabber); `skaven-of-clan-pestilens-lus`
(cloud-of-flies); `skaven-of-clan-pristekk-sc` (thing-handler);
`underworld-alliance-mim` (wyrdstone-addict, stuff-em-with-green).

Two of these carry an **open T13-Q question** (blocked by source, not by the
runtime): `band--skill-wyrdstone-addict` (T13-Q101) and
`band--skill-stuff-em-with-green` (T13-Q102). The runtime refusal is asserted;
both semantic questions stay open.

### Pending without an availability channel (9 origins) — discrepancia

These origins are `grant: selectable` but absent from the current
`available_special_rules` API. Eight are warband skills without a published
access/eligibility route in that API. The ninth, `vampire--bloodline`, explicitly
names `vampire` in `applies_to.profile_ids` but has `kind=profile_ability`; the API
enumerates only `warband_skill` entries. This does not adjudicate their legality
under the source or establish the absence of every possible selection route.
The runtime refusal is still real and is asserted:

`band--special-skill-unshakeable-faith`, `band--special-skill-utter-determination`,
`band--special-skill-rousing-sermon` (protectorate-of-sigmar-lotd3);
`band--skill-pious-fury` (araby-smugglers-sar); `band--dance-whirling-death`,
`band--dance-storm-of-blades`, `band--dance-the-shadows-coil`,
`band--dance-woven-mist` (sea-ghosts-mim); `vampire--bloodline` (strigoi-kaz —
`kind=profile_ability`, `applies_to.profile_ids: vampire`).

Two of these carry an open T13-Q question — `band--dance-woven-mist`
(T13-Q081) and `vampire--bloodline` (T13-Q095) — so all four selectable
questions of the partition are accounted for: Q101/Q102 in the channeled group
and Q081/Q095 here. None was resolved.

## Equipment

95 item origins, all in `sources/knowledge/catalog/items`. Real state:

| Item | `combat_status` | Mapping | Construction route | Disposition |
| --- | --- | --- | --- | --- |
| `duelling_pistol` | implemented | implemented | equipment list of the Mercenaries | **probado** (selection + compilation only; T13-Q151 open) |
| `sea_dragon_cloak` | implemented | implemented | reachable from dark-elves | **bloqueado por fuente** (T13-Q128) |
| 93 others | `out_of_scope` | out_of_scope or absent | list / trading post / none | pendiente de implementación / bloqueado por fuente |

Only **4 of the 95** items have any simulation-mapping row (`duelling_pistol`,
`sea_dragon_cloak` implemented; `rope_hook`, `warhound` `out_of_scope`). 74
items appear in an equipment list yet have no mapping. For **17 items**, this
audit found a trading-post entry but no warband equipment-list or simulation-mapping
route. This is a bounded catalogue finding, not proof that every possible caller
is absent. They are recorded individually:
`angel_wings`, `arcane_candelabrum`, `bear_of_the_hunt`, `corpse_liquor`,
`great_eagle`, `great_stag`, `hunting_hounds`, `runic_attlas_plate_mail`,
`runic_builders_boots`, `runic_eye_of_izril`,
`runic_redbeards_belt_of_rage`, `runic_sword_of_snorri_elfbane`,
`sabre_toothed_tiger`, `scuttling_hand`, `wicker_man`, `wolf_pelt_cloak`,
`wolf_rat_mount`.

**Compiled evidence.** `duelling_pistol` in the main hand → tags
`weapon.duelling-pistol`, `fixed_strength=4`, `armour_penetration=1`,
`hit_modifier=1`; the off hand works with `off_hand_attacks=True`. A band that
does not publish the item (`skaven-clan-pestilens`) is refused with
`equipment is not available to …`. The supported material route is checked
through `material.gromril` (tags `material.gromril`,
`armour_penetration=1`) as a comparator so the pending item cannot silently
borrow it. The CSV carries all 95 item rows individually (`origin_key`,
canonical object, kind/`combat_status`, mapping/binding, real path, status and
blocker), so every pending item is enumerated there even when no test could be
built for it.

## New tests

[test_t13_selectable_equipment_matrix.py](../../../../tests/python/construction/test_t13_selectable_equipment_matrix.py)
— exercised through `FighterBuild` → `available_special_rules` →
`compile_fighter` (no mocks of the layers under test). **56 passed.**

- Partition coverage: recomputes `(54, 53, 95)` from the register + canonical
  YAML and asserts the test tables cover exactly the partition set.
- Availability: Master of Blades / True Grit / Thick Skull offered to the Dwarf
  Noble, Slayer-only rules offered to the Slayer and **not** to the noble, roar
  offered to the Saurus.
- 35 `PENDING` origins: visible for selection **and** refused with the exact
  gate prefix plus the published reason.
- 9 `PENDING_WITHOUT_AVAILABILITY_CHANNEL` origins: refusal asserted; the
  missing channel is reported as a discrepancy, not papered over as a fixture.
- Plus the nine implemented-rule tests and the equipment tests (pistol
  main/off-hand + foreign refusal, gromril material + foreign refusal).

## Reused evidence (not duplicated)

- [test_selectable_bindings.py](../../../../tests/python/construction/test_selectable_bindings.py)
  — berserker / ferocious-charge interplay.
- [test_native_virtues.py](../../../../tests/python/construction/test_native_virtues.py).
- [test_characteristic_bonus_contract.py](../../../../tests/python/construction/test_characteristic_bonus_contract.py)
  — `weapon.vomit-attack` used there as a *host* rule.
- [test_savage_equipment.py](../../../../tests/python/construction/test_savage_equipment.py),
  [test_source_corrections.py](../../../../tests/python/combat/modular/test_source_corrections.py).
- T13.2a / T13.2b evidence (Bloated Foulness movement, characteristic-bonus
  contract) reused as accepted evidence, not re-derived.

## Reproducible findings and discrepancies

1. **`weapon.vomit-attack` is not projected.** `selected_special_mechanics`
   feed `global_ids`, but the binding has trigger/application `attack`/`attack`.
   Compilation applies `passive`/`fighter` and `duel_start`/`fighter`, so the
   binding reaches neither global effects nor the main weapon. The coordinator's
   direct probe confirms the selected compiled fighter equals its unselected
   control. Selection and recipient routing are proved; attack replacement remains
   a separate implementation task.
2. **Nine selectables are absent from the current availability API** (list
   above), including one profile ability excluded by its kind. Source legality
   and alternative selection routes have not been adjudicated.
3. **`darksteel_blade` has no simulation-mapping row** even though the
   `material.dark-steel` mechanic exists; the item is `out_of_scope`. No alias
   was added. `thing_catcher` and `thingcatcher` are two distinct KB items from
   different sources, not a resolution bug.
4. **Iron Sinews provenance.** The name is selectable only in Trollheim
   (`band--strigoi-power-iron-sinews` → `skill.iron-sinews`); its legacy
   `SPECIAL_RULE_EFFECTS.stats` entry is unreachable for mechanic bindings
   (T13.2a decision). The legacy route was **not** activated, deleted or
   doubled — only recorded.
5. **`sea_dragon_cloak` (T13-Q128)** stays blocked: the printed source lists an
   explicit disagreement on armour composition (body armour / helmet / shield
   are refused with "Sea Dragon cloak cannot be combined with other armour").
6. **`spirit_knife` (T13-Q146)** stays pending; the Spectral Touch
   interpretation was **not** adopted.
7. **`duelling_pistol` (T13-Q151)** — selection and compilation proved; the
   full pistol H2H / reload / save contract stays open.
8. **47 equipment item rows carry an open question** (46 unique ids, T13-Q110 …
   T13-Q157, with T13-Q154 on both `stone_dagger` and `stone_hammer`) and 4
   selectable questions (T13-Q081, T13-Q095, T13-Q101, T13-Q102) remain open.
   No question was resolved.

## Deliverables

- [T13-selectable-equipment.csv](T13-selectable-equipment.csv) — 151 rows, 11
  columns, UTF-8 with BOM and retained CRLF row endings; **151 unique `origin_key`s**. Columns: `origin_key`,
  `canonical_object`, `kind`, `recipients_configuration`, `prerequisite`,
  `binding`, `real_path`, `compiled_property`, `test_or_case`, `status`,
  `blocker`. Status spread: probado 10, pendiente de implementación 80,
  discrepancia 13, bloqueado por fuente 48. Rows: 54 selectable origin rows
  (including both Master-of-Blades origins) + 95 item rows + 2 adjacent Iron
  Sinews provenance rows = 151.
- New suite (above) and this document.
- Evidence under `build/cache/t13-parallel/selectable-equipment/`
  (`partition.*`, `trace.*`, `reconcile*.*`, `probe*.*`, `equipment-access.*`,
  `build_csv.py`, run logs and pytest logs/XML).

## Limits

- **Selection and compilation only.** A compiled weapon or skill does not
  certify its rolls, criticals, parries or resolution effects; T13.3 / T13.4
  and T14 own those.
- No new mechanic, no implementation flag promoted, no T13-Q resolved, no
  allowlist added, no detector or expectation edited.
- The absence of a mandatory choice was never used as a control.
- The partition stays inside selectable rules + equipment: automatic
  profile/band grants, hirelings and spells are out of scope, and T13.0 was not
  rebuilt.
- This lot's acceptance does not close the phase or resolve its discrepancies.

## Coordinator review — 2026-10-01

- Accepted as traceability and construction-test coverage; reservation released.
  No production, KB or semantic-contract change was made by this lot or review.
- Independently reconciled 149 assigned origins (54 selectable + 95 items) with
  the CSV: 151 unique origin keys, no assigned origin missing, and exactly two
  additional Iron Sinews provenance rows. Both Master of Blades origins remain.
- Focused coordinator run: **57 passed** (56 matrix tests + documentation links),
  retained in `build/cache/t13-parallel/selectable-equipment/coordinator-review.xml`.
  External logs for **259 construction** and **50 catalogue/reference** tests were
  inspected and reused; those broader suites were not rerun by the coordinator.
- A direct probe checked the nine API omissions across each band's available
  fighter profiles. Explicitly excluded non-fighter profiles remain excluded and
  their reasons are retained in `coordinator-findings.json`, alongside the Vomit
  Attack selected/control comparison. The probe does not certify source legality.
- Documentation and test comments were narrowed to match the evidence: no claim
  of universal equipment refusal, source illegality, or functioning Vomit Attack.
  No implementation of the missing projection or backend port was started.

## L02 follow-up — 2026-10-03

The Vomit projection discrepancy above is historical. [L02](T13-vomit-attack.md)
now compiles a separate optional attack for the canonical Warpstone Troll and
resolves acceptance/rejection through the modular round policy. F010 is resolved
for that canonical/modular boundary; the original matrix is retained as the
T13.2d entry trace. Optimized choice remains explicitly refused until L19/L20.
The maintained selectable case now asserts the compiled option and retains its
foreign-recipient control.
