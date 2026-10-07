# T13 effect routing — current assignments

Companion to [T13-effect-routing.yaml](T13-effect-routing.yaml). The register is a maintained input; audit and consolidation generators do not consume it yet.

This correction keeps the retained inventory as its basis and adds the construction/access work executed since. Assignment, implementation work and evidence are independent; these counts are not a certified T14 base. Nothing was committed or pushed.

## Coverage

94 groups assign all **7,339 retained input rows**: 3,394 original origins, 1,240 T13-traceable incorporations and 2,705 other examined rows. The latter include 1,114 YES, 376 LATER and 1,215 NO rows. No row is selected for membership using `t13_origin`; it preserves lineage only. The source-checked condition runtime update replaces eight retained identities with nine successors, producing a **7,340-identity bounded view**. This is not a fresh full inventory; unrelated live-source changes are not inferred.

The 51 F073 renamed origins retain their original ID and explicit successor. Seven condition origins now also have `current_id`, and Cold-Blooded has two `current_ids`; each keeps `retained_id` for comparison with the original snapshot. There are 58 one-to-one renames and one split. Fingerprints are compared with the retained inventory and clarification inputs; only the eight condition successions are additionally checked against live source text/runtime IDs. Neither comparison is behavioral verification.

The construction and access restrictions of the flagged set are implemented in this revision. Legality stays in the shared decision (`packages/typescript/domain/eligibility/index.ts`): an equipment entry's `applies_to` gained a conjunctive `variants` gate and a named `excluded_profile_ids` denial, `configuredProfile` carries the build's selection facts and `entryReachesProfile` reads them. The same owner gained the whole-set contracts: `EquipmentLimits.item_copy_limit` (how many copies of one item a member may possess, with the printed exempt bearers), `RequiredEquipment` (an obligation to *acquire* one item of a family, with the printed items that never satisfy it, satisfiable by kind or by a named canonical item/mechanic id) and `PoisonApplication`/`poisonApplicationIssue` (which weapon kinds a governed poison may coat for a bearer); the profile facts also gained `active_weapon_permits` (a printed permitted active-weapon set, read by `tokenPermits`) and `MissileWeaponLimit` (a profile-scoped missile bound with its exempt item and mechanic ids). The Knowledge Base publishes the facts: the 142 profile-restriction origins (the seven last ones resolved with their own rule or with a recorded metadata resolution), the printed recipients (Brood dagger, Crooked Moon daggers, pirate variants, Forest Bosspole, Mare lance, Underworld Man Catcher, Lizardman Sacred Markings) and the House Guard and Silent Brotherhood selection gates. The Python transport supplies the chosen House in `build_facts`; the Sniper Modus Operandi travels in `variant_ids`. The Warband Manager transport publishes the same facts on the generated artefact (`profile.required_equipment`, `profile.poison_application`, the band `equipment_limits` copy bound) and the campaign domain decides them through `memberEquipmentIssuesFor`/`equipmentIssueFor`. Executed evidence: `tests/python/construction/test_t13_canonical_choices.py` (the shared decision through the real Combat Lab adapter), `tests/python/construction/test_t13_construction_recipients.py` (18 recipient cases), `tests/typescript/domain/campaign/t13-construction-restrictions.test.ts` (12 Warband Manager transport cases), the KB schema/staging gate and the bundle freshness check.

## Profile-restriction reconciliation

The 142 `KB-PROFILE-RESTRICTIONS` origins were re-checked one by one against the current canonical facts and consumers (the origin's profile prose plus the rule whose `effect` is that prose, and the binding that reaches the profile):

| Outcome | Origins | Registered in |
| --- | ---: | --- |
| Covered by a canonical binding the shared decision consumes | 118 | `KB-PROFILE-RESTRICTIONS-COVERED` |
| Covered by grounded facts (list membership, `fixed_equipment`, declared-list note, named bearer) | 12 | `KB-PROFILE-RESTRICTIONS-COVERED` |
| Vacuously covered: the profile declares no equipment list, so no item can be selected | 6 | `KB-PROFILE-RESTRICTIONS-COVERED` |
| Out of the construction boundary (warband slot/presentation, campaign recruitment, casting permission, campaign variable-characteristic state) | 6 | `KB-PROFILE-RESTRICTIONS-EXCLUDED` |
| Still open | 0 | — |

136 origins moved to `-COVERED` (382 rows with the 246 already there), 6 to `-EXCLUDED` (15 rows with the 9 already there) and none stayed pending. Ids, `sha256` and clauses are untouched; every count is derived from the rows. `KB-PROFILE-RESTRICTIONS` is now a declaration-only tombstone (`pending_work: ninguno`, no rows) whose `resolution:` names, per origin, its disposition, its covering rule and the transport that decides it:

| Origin (original id kept) | Disposition | Covering rule / fact | Transport that decides it |
| --- | --- | --- | --- |
| `high-elves-lus/loremaster` — Tower-of-Hoeth whitelist | clause implemented | `loremaster--tower-of-hoeth`: `profile.active-weapon-restrictions` with `parameters.allowed_kinds` (`weapon.sword`, `weapon.dagger`, `mage_staff_of_hoeth`) and `applies_to.profile_ids` (`loremaster`) | `tokenPermits`/`activeWeaponIssues` admits the printed set and refuses another active main/off/extra weapon with `equipment_forbidden`; ownership stays legal because the clause bounds *use* (an owned axe that is never wielded is admitted) |
| `mootlanders/moot-elder` — Halfling list plus pistol | clause implemented | `moot-elder--halfling-list`: a `mechanic`-bound `weapon.pistol` effect for `moot-elder`; the list itself stays the declared `mootlander-equipment-list`, whose published name is already "Halfling Equipment List" | the concession is one additional item, never a copy of the list rows: the decision admits the pistol for the elder, refuses it for the master-chef and keeps the list restrictions (an off-list `axe` stays refused); the printed 15 gc price stays creation data |
| `order-of-the-mare-web/dame-of-the-mare` — ancient armour | clause implemented | `dame-of-the-mare--ancient-armour`: `trait.natural-armour-save` 5, `trait.natural-armour-unmodified` true, `trait.natural-armour-negated-by-magic` true; `profiles.yaml` `fixed_equipment` `dame_ancient_armour` plus the new out-of-scope catalogue item | the compiler folds the traits once and `armour_target` keeps the better of `armour_save`/`natural_armour_save`, so the constant 5+ save reaches the warrior exactly once; she has no armour access, so nothing substitutes the intrinsic item; never removed/traded/stolen, casting and robbery/trade stay outside the 1v1 boundary |
| `ghutani-rel/flagellants` — "Restricted to Townsmen." | metadata resolution | the note names the bearer of the list, not a Flagellants prohibition: the profile declares `townsmen-equipment-list`, the same list the Townsmen profile uses, and `band--ghutani-flagellants` already prints the access in its effect | both profiles carry an identical `equipment_access` set and publish no `forbids` token, so the declared access satisfies the source (sword and sling admitted, bow refused) and no profile restriction is invented |
| `snotlings-web/shoota-teams` — one missile weapon | clause implemented | `shoota-teams--one-missile-weapon`: `profile.equipment-restrictions` with `parameters.max_missile_weapons` 1 and `parameters.exempt_item_ids` (`small_pebble`, `slingshot`) for `shoota-teams` | the bound counts units (two copies of one weapon are two) and exempts by item id or mechanic id; purchase and possession stay separate from the active slots and no shooting resolution is added |
| `skaven-of-clan-pestilens-mou/plague-priest` and `plague-champion` — robes as light armour | clause implemented, one shared contract | `plague-priest--plague-monk-robes`: `trait.natural-armour-save` 6 with `applies_to.profile_ids` (`plague-priest`, `plague-champion`) | the robes are soft leather (6+) and, combined with the stated pieces, count as light armour; the equivalence lives in the compilation and the modular engine, never in the legality decision, and the engine keeps the better save (6,6) instead of adding a second one |

## Condition-runtime reconciliation

The `KB-CONDITIONS-RUNTIME` and `FACT-CONDITION-MAPPING` origins were re-checked against the current code (not against the group text): the eight canonical condition ids now declare their operator in `catalog/rules/conditions.yaml` (`runtime.effects[].binding`, the same contract band rules use) and the caller supplies the canonical id through `FighterBuild.condition_ids`; `mordheim_construction.conditions.resolve_supplied_conditions` reads that catalogue from the caller's root and refuses an unknown id, an unimplemented condition or a missing printed variant instead of guessing.

| Origin (original id kept) | Disposition | Binding declared in the KB | Route that decides it |
| --- | --- | --- | --- |
| `campaign.condition.causes-fear` — Horrible Scars | clause implemented | `trait.causes-fear` (`parameters.value` true) → `mechanic.causes-fear` | `condition_ids` → `compile_fighter` → `psychology.causes_fear` → `resolve_fear`; the injury result shares this id |
| `campaign.condition.frenzy` — Madness (4-6) | clause implemented | `trait.frenzy` | `condition_ids` → compiled `global_effects.frenzy` → modular duel state (Fear/Stupidity exemptions) |
| `campaign.condition.immune-to-fear` — Hardened | clause implemented | `mechanic.fear-immunity` | `condition_ids` → tag → `leadership.resolve_local_leadership` (fear tests) and `psychology.needs_test`; not widened to psychology |
| `campaign.condition.stupidity` — Madness (1-3) | clause implemented | `trait.stupidity` → `mechanic.stupidity` | `condition_ids` → tag → `psychology.resolve_stupidity` on the duelist's own turn |
| `condition.cold-blooded` | clause implemented, both printed variants | `mechanic.cold-blooded-psychology` (variant `lizardmen`) and `mechanic.cold-blooded-leadership` (variant `fimir`), selected by the supplied `cold_blooded_origin` fact | `condition_ids` + the declared fact selects one variant; a missing or unknown origin is refused, so no universal variant is invented and the Lizardmen/Fimir band bindings are unchanged |
| `condition.fear` | rules definition, exact disposition | scope `NO`, `implemented: NO`, unbound effect with its reason | the printed general Fear rule already executed by `resolve_fear`/`causes_fear`; it is not a per-warrior state and supplying it is refused by name — the fact that makes a model cause Fear is `campaign.condition.causes-fear` |
| `condition.hatred` | clause implemented | `skill.hatred` | `condition_ids` → tag → `contexts._hit_reroll` (first combat round only), with the existing psychology-immunity gate still cancelling it |
| `condition.immune-to-psychology` | clause implemented | `mechanic.psychology-immunity` | `condition_ids` → tag; the existing operator keeps every interaction (Fear and Stupidity tests, Frenzy/Hatred benefits, automatic Leadership) and is not reduced to fear immunity |
| `serious-injuries` 62-63 Hardened note | clause mapped to the same operator | `campaign.condition.immune-to-fear` → `mechanic.fear-immunity` | `warrior.add_condition` carries the id into the same `condition_ids` route; no separate injury mapping table exists |
| `serious-injuries` 64 Horrible Scars note | clause mapped to the same operator | `campaign.condition.causes-fear` → `mechanic.causes-fear` | the same route as the rulebook condition, so the two injury results share one connection and no consequence is implemented twice |

No origin stayed pending: both groups carry `pending_work: ninguno` with a `resolution:` block. Original IDs, printed-text `sha256` and clauses remain unchanged, but runtime addition **does change generated audit IDs**. The eight condition origins now have seven one-to-one successions and one split, declared in their `current_id`/`current_ids` fields; Cold-Blooded maps to `mechanic.cold-blooded-psychology` and `mechanic.cold-blooded-leadership`. Fear's successor is `rule.fear`, with its rules-definition disposition. The two serious-injury note origins stay unchanged. Campaign persistence, injury generation and condition acquisition stay outside this batch: an already-acquired result is supplied as a warrior fact. A duplicate id, or the same condition granted by a second route, applies its effect once (tags are merged once and the state flags are boolean).

Executed evidence for these two groups: `build/probe/probe_t13c.py` (exit 0), the condition cases of `tests/python/construction/test_t13_canonical_choices.py`, the supplied-condition cases of `tests/python/combat/modular/test_local_modifier_variants.py` and the editor round-trip in `tests/python/ui/test_editors_catalogue_sweep.py`. Combat Lab passes ids through (`CombatCatalogue.conditions()` and the editor checklist) and keeps no second interpretation table; the workbook payload round-trips `condition_ids`.

## Clarifications and clause boundaries

All 15 clarifications (35 origins) have separate clause-specific groups, exact decisions and remaining-work criteria. Resolved meaning no longer carries current `decision_pending` evidence; historical `status` remains identifiable as a snapshot.

- Halfling culinary names introduce no bearer restriction. Presentation is optional, not a mandatory modular task.
- Reptile Venom and Mare mount equipment are explicit exclusions with separate criteria.
- Pirate qualifiers use warband variants; House and Sniper use their selected facts. They are not arbitrary profile restrictions. House and Sniper are implemented in the shared decision: the printed lines carry `applies_to.variants` (`house.fierezza`/`house.halcon`/`house.baluardo`, `modus-operandi.sniper`) plus the named `excluded_profile_ids` denial, and the shared decision reads the build's selection fact. Combat Lab transports the real House and specialisation; Warband Manager cannot configure one yet (see the product-access boundary below).
- Bosspole and Sacred Markings include their individual spear/immunity and bite consequences, respectively. Eligibility alone does not close those effects.
- Mare armour and Wood Elf Ithilmar retain the already-applied local recipient decisions; this does not certify combat behavior.
- Unclarified equipment-note targets remain unresolved rather than receiving invented bearer restrictions.

## Counts

The tables count retained input rows, so Cold-Blooded remains one historical origin. Its two current identities are recorded separately; the retained totals are 7,339 rows and the bounded successor view is 7,340 identities.

| Primary layer | Rows |
| --- | ---: |
| `A` | 1,120 |
| `B` | 32 |
| `C` | 103 |
| `D` | 1,129 |
| `E` | 401 |
| `F` | 66 |
| `G` | 4,488 |

| Pending action | Rows |
| --- | ---: |
| `comportamiento` | 111 |
| `conexion` | 82 |
| `dato` | 98 |
| `decision` | 548 |
| `ninguno` | 6,443 |
| `proyeccion` | 57 |

| Implementation state | Rows |
| --- | ---: |
| `decision_pending` | 66 |
| `deferred` | 482 |
| `excluded` | 4,012 |
| `gap_identified` | 348 |
| `no_gap_identified` | 830 |
| `not_assessed` | 1,601 |

| Available evidence | Rows |
| --- | ---: |
| `binding_metadata` | 1,596 |
| `clarification_resolved` | 35 |
| `decision_pending` | 172 |
| `inspected` | 1,106 |
| `review_classification` | 4,430 |
| `unassessed` | 0 |

`ninguno` names no identified action, not completion. In particular, `not_assessed` explicitly preserves metadata-only uncertainty. Source-review evidence and clarified scope also do not certify execution.

## Executable groups and order

Start independent groups without a global decisions phase. Follow only the local `dependencies` recorded for the selected group. Deferred scope does not automatically require user input. Optional presentation is not a prerequisite. Finish each admitted effect through its required data, projection, compiler and modular consequences.

1. Shared canonical restrictions and the clarified Brood/Crooked Moon/Mare/Underworld routes; preserve source-specific exceptions.
2. Variant, House and specialization projection; preserve existing shared legality ownership.
3. Existing-operator connections and individual Bosspole/bite effects; canonical access and actual consequences close together.
4. Hireling reference/admission/kit families, respecting their recorded admission dependencies.
5. Remaining modular attack, defence, psychology and recovery contracts, grouped by the responsible consumer.
6. Resolve only the decisions or source blocks that gate the selected group. Supplied magic, equivalence questions and LATER reviews are local follow-ups.

These are scheduling families, not claims that every historical missing operator is still absent. Metadata-only groups require an implementation assessment before deciding to build or verify them.

### Actionable group inventory

| Group | Layer | Action | Rows | Local dependencies |
| --- | --- | --- | ---: | --- |
| `KB-EQUIP-ACCESS-RECIPIENTS` | A | `ninguno` | 6 | — |
| `KB-PROFILE-RESTRICTIONS` | A | `ninguno` | 0 | — |
| `KB-PROFILE-RESTRICTIONS-COVERED` | A | `ninguno` | 382 | — |
| `KB-PROFILE-RESTRICTIONS-EXCLUDED` | A | `ninguno` | 15 | — |
| `KB-TRADING-POST-SCOPE` | A | `dato` | 32 | T13-F028 |
| `KB-HIRELING-REFERENCES` | A | `dato` | 40 | CB-HIRELING-ADMISSION, T13-F036, T13-F037, T13-F038 |
| `KB-ITEM-MECHANIC-MAPPING` | A | `conexion` | 0 | — |
| `KB-SKILL-EQUIVALENCE-DECISION` | A | `decision` | 3 | KB-SKILL-RUNTIME-METADATA |
| `KB-CONDITIONS-RUNTIME` | A | `ninguno` | 8 | — |
| `KB-SHARED-RULE-DIVERGENCE` | A | `dato` | 9 | KB-SHARED-RULE-COVERED |
| `KB-SHARED-RULE-IMPLEMENTATION` | E | `comportamiento` | 2 | — |
| `KB-CAMPAIGN-MAGIC-COMMAND` | A | `conexion` | 3 | T13-F039 |
| `KB-CAMPAIGN-ARTEFACT-RECORD` | A | `dato` | 0 | — |
| `DECISION-CONSTRUCTION-CONTRACT` | F | `ninguno` | 5 | — |
| `DECISION-MIXED-CLAUSE-SPLIT` | D | `comportamiento` | 23 | — |
| `CB-HIRELING-ADMISSION` | C | `proyeccion` | 0 | T13-F036 |
| `CB-HIRELING-RULE-BINDING` | A | `conexion` | 62 | CB-HIRELING-ADMISSION, KB-SHARED-RULE-DIVERGENCE |
| `CB-HIRELING-PARTIAL` | E | `comportamiento` | 8 | CB-HIRELING-ADMISSION |
| `CB-BAND-EQUIPMENT-NOTE` | E | `comportamiento` | 5 | KB-ITEM-MECHANIC-MAPPING |
| `CB-CAMPAIGN-ARTEFACT-IMPLEMENTATION` | E | `comportamiento` | 4 | KB-CAMPAIGN-ARTEFACT-RECORD |
| `CB-CAMPAIGN-MAGIC-SUPPLIED` | F | `decision` | 51 | KB-CAMPAIGN-MAGIC-COMMAND |
| `CB-BINDING-MISSING` | A | `conexion` | 10 | — |
| `CB-MODULAR-OPERATOR-MISSING` | E | `comportamiento` | 4 | CB-BINDING-MISSING |
| `CB-SKILL-IDENTITY-GAP` | A | `dato` | 7 | KB-SKILL-EQUIVALENCE-DECISION |
| `CB-REL-DANGLING-ITEM` | A | `decision` | 2 | — |
| `CB-SOURCE-BLOCKED` | A | `decision` | 1 | — |
| `CB-PARTIAL-CLAUSE` | A | `comportamiento` | 2 | — |
| `CB-DECISION-REQUIRED` | F | `decision` | 5 | T13-F001, T13-F036 |
| `FACT-TRAIT-CAMPAIGN-ONLY` | C | `proyeccion` | 50 | — |
| `FACT-INJURY-UNTYPED` | A | `dato` | 6 | — |
| `FACT-CONDITION-MAPPING` | A | `ninguno` | 2 | KB-CONDITIONS-RUNTIME, T13-F070 |
| `FACT-LEADERSHIP-REROLL-BINDING` | A | `conexion` | 2 | T13-F036 |
| `FACT-COMMAND-CHANNEL` | D | `conexion` | 1 | T13-F039, CB-CAMPAIGN-MAGIC-SUPPLIED |
| `FACT-BLESSED-WEAPON` | E | `comportamiento` | 1 | T13-F064 |
| `FACT-GRANTED-HATRED` | A | `conexion` | 1 | — |
| `FACT-IENH-KHAIN-ITEMS` | A | `comportamiento` | 3 | T13-F036, CB-HIRELING-ADMISSION |
| `INC-BAND-RULE-IMPLEMENTATION` | E | `comportamiento` | 14 | — |
| `INC-BAND-RULE-QUESTION` | A | `decision` | 4 | — |
| `INC-BAND-RULE-DEFERRED` | G | `decision` | 106 | — |
| `KB-BAND-RULE-UNTRACKED-DEFERRED` | G | `decision` | 376 | — |
| `CB-HIRELING-KIT-WEAPON` | E | `comportamiento` | 12 | CB-HIRELING-ADMISSION |
| `CB-HIRELING-KIT-DEFENCE` | E | `comportamiento` | 4 | CB-HIRELING-ADMISSION |
| `CB-HIRELING-KIT-ATTACK` | E | `comportamiento` | 8 | CB-HIRELING-ADMISSION |
| `CB-HIRELING-KIT-PSYCHOLOGY` | E | `comportamiento` | 8 | CB-HIRELING-ADMISSION |
| `CB-HIRELING-KIT-OTHER` | E | `comportamiento` | 13 | CB-HIRELING-ADMISSION |
| `CLARIFIED-BROOD-DAGGER` | A | `dato` | 1 | — |
| `CLARIFIED-CROOKED-MOON-DAGGERS` | A | `dato` | 1 | — |
| `CLARIFIED-PIRATE-VARIANTS` | C | `proyeccion` | 7 | — |
| `CLARIFIED-FOREST-BOSSPOLE` | D | `conexion` | 1 | — |
| `CLARIFIED-MARE-LANCE` | A | `dato` | 1 | — |
| `CLARIFIED-HOUSE-EQUIPMENT` | C | `ninguno` | 6 | — |
| `CLARIFIED-LIZARD-POISONS` | B | `ninguno` | 2 | — |
| `CLARIFIED-LIZARD-SACRED-MARKS` | D | `conexion` | 2 | — |
| `CLARIFIED-SNIPER-EQUIPMENT` | C | `ninguno` | 2 | — |
| `CLARIFIED-UNDERWORLD-LEADERS` | A | `dato` | 1 | — |

## Result of the construction/access delivery

Separated by what actually changed, with the original origin IDs and their current successors:

- **Legality implemented.** The shared decision (`entryReachesProfile`, `configuredProfile`, `equipmentSetIssues`, `poisonApplicationIssue`) decides the House Guard lines (6 origins of `CLARIFIED-HOUSE-EQUIPMENT`; `house-guard-sc` list 0 items 4, 7, 9, 10, 12, 15) and the Silent Brotherhood Sniper lines (2 origins of `CLARIFIED-SNIPER-EQUIPMENT`; `silent-brotherhood-sc` list 0 items 7, 9), including the named denial of the Silent Master. The 142 `KB-PROFILE-RESTRICTIONS` origins (136 moved to covered, 6 excluded, none open) and the printed recipients (`KB-EQUIP-ACCESS-RECIPIENTS`: Brood, Crooked Moon, pirates, Mare lance, Underworld; plus the Bosspole and Sacred Marking recipients) are already published.
- **Per-clause contracts closed with this batch.** The Sigmarite two-hammer clause as `band--sigmarite-hammer-pair` (`max_item_id weapon.sigmarite-hammer`, `max_item_copies 1`, `exempt_profile_ids [sigmarite-matriarch, sister-superior]`, `exempt_max_item_copies 2`), decided by `equipmentSetIssues` as a possession bound, distinct from the active slots; the Knights Errant compulsory hand-to-hand weapon as `knights-errant--hand-to-hand-weapon` (`required_kinds [close-combat-weapon]`, `required_excludes [weapon.dagger]`), an obligation to acquire the weapon and never an obligation to attack with it; the Lizardman poison application as `band--skink-poison-application` / `band--skink-henchman-poison-application` (ranged weapons) and `band--saurus-poison-application` (close-combat weapons), decided per bearer; and the compulsory Chaos Dwarf Blunderbuss as `blunderbuss-chaos-dwarfs--equipment-restrictions` (`required_kinds` naming the canonical item). `KB-EQUIP-ACCESS-RECIPIENTS`, `CLARIFIED-LIZARD-POISONS` and `DECISION-CONSTRUCTION-CONTRACT` now carry `pending_work: ninguno` with a `resolution:` block recording what landed, as does `KB-PROFILE-RESTRICTIONS` after this batch's five profile rules (`loremaster--tower-of-hoeth`, `moot-elder--halfling-list`, `dame-of-the-mare--ancient-armour`, `shoota-teams--one-missile-weapon` and the single `plague-priest--plague-monk-robes` for two profiles) and the Ghutani metadata resolution.
- **Transport verified.** Combat Lab: the real adapter (`CombatCatalogue.validate_configuration` / `equipment_decisions`) returns the clauses above, with the first/second hammer split, the `variant_ids` House and Modus Operandi decisions and the Silent Master refusal. Warband Manager: the generated artefact publishes `profile.required_equipment`, `profile.poison_application` and the band `equipment_limits.item_copy_limit`, and the campaign domain decides them through `memberEquipmentIssuesFor`/`equipmentIssueFor` (see the executed cases below).
- **Product access (not delivered, documented).** Neither `house-guard-sc` nor `silent-brotherhood-sc` publishes a warband variant, and Warband Manager carries a selection only in `identity.mercenary_variant`, which names a published variant. The campaign therefore cannot configure the House or the Modus Operandi; `profileFactsOf` carries no selection fact and the artefact answers for the canonical profile with none, so a conditional line is offered to nobody rather than to the wrong bearer. This is a product-input boundary, not a rule defect: the predicate is implemented and Combat Lab transports the real selection. The visible editing of the remaining supplied facts still belongs to L18.
- **Executed evidence.** `tests/python/construction/test_t13_canonical_choices.py` (shared decision through the real Combat Lab adapter; the six clause discriminators pass), `tests/python/construction/test_t13_construction_recipients.py` (18 cases: a printed recipient reaches its profile and no peer; the House/Sniper gate allows the selected fact and refuses the others; a prohibited direct selection is `equipment_forbidden`/`equipment_not_permitted`; the Mare and Wood Elf controls survive), `tests/typescript/domain/campaign/t13-construction-restrictions.test.ts` (17 cases over the generated artefact: one hammer, two for the ordinary bearer, the exempt bearer; dagger refused and a real weapon accepted; a Skink melee application refused and the Saurus melee one admitted; the compulsory named Blunderbuss; the House/Sniper predicate and the recorded product boundary; the Loremaster whitelist, the Moot Elder pistol, the Shoota Team missile bound and the Dame intrinsic armour through the web transport), `tsc --noEmit`, `build:eligibility`/`check:eligibility`, the regenerated artefact (`generate_knowledge_web.py --check`), the KB editorial schema gate and the 2B staging gate. The naming normalizer gate found the four Spanish names this batch added and they were normalized, after which the artefact was regenerated.
- **Pending combat behaviour.** The Forest Bosspole spear contribution and the Lizardman Sacred-Marking bite consequences still affect the duel and remain recorded as pending. The Dame-of-the-Mare constant save is no longer among them: the profile rule now publishes its traits, the compiler folds them onto the fighter (5+, unmodified, negated by magic) and `armour_target` reads them, so no second save is added.
- **Justified exclusion.** `KB-EQUIP-ACCESS-RECIPIENTS` 5 of 6: the Gromril conversion and the Khemri price note are purchase-price clauses, the Pestilens note is a price/reference typo, and the Chaos-streets-greenskins rows are a warband-composition condition whose drug mechanics are stated out of scope. `DECISION-CONSTRUCTION-CONTRACT`: the Thaggi row is a roster-count rule outside the 1v1 boundary; the three Feather Headdress rows are covered by the published `witch-doctor` recipient fact (the mandatory leader), with the "unless this model becomes leader" clause a campaign leadership-transfer rule.
- **Resolved clauses (7).** Every profile-restriction clause now has its consumer, recorded per origin in the reconciliation table above: five Knowledge Base rules (`loremaster--tower-of-hoeth`, `moot-elder--halfling-list`, `dame-of-the-mare--ancient-armour`, `shoota-teams--one-missile-weapon`, `plague-priest--plague-monk-robes`) and one metadata resolution (`ghutani-rel/flagellants`, whose note names the bearer of the list). No clause is closed by resemblance of text or by an incidental list block.

## Structural checks and limits

Run `python build/audit/effect-routing/check_register.py` against the retained inputs. The checker requires exact retained-ID coverage, unique original/successor ownership, matching fingerprints, applied decisions/scopes, independent per-row states, consistent counts, valid consumer references and acyclic local dependencies. It additionally derives the nine current condition identities from the live runtime entries and checks the eight explicit successions, including both Cold-Blooded branches. It does not execute combat behavior or establish a fresh full-inventory baseline.

Executed: the structural checker passed with zero failures (94 groups, 7,339 rows); an isolated omission of a YES row without `t13_origin` was refused, leaving maintained bytes unchanged; the documentation-link check passed (1 test). Register encoding is UTF-8/LF, without BOM or trailing whitespace. The register's group counts, states and evidence are derived from the rows, and every per-origin decision was re-checked against the current canonical facts rather than by resemblance of text.

The consumer symbols and historical status claims remain inspection/metadata evidence. This task does not re-fetch external sources, reassess every historical claim or refresh the inventory. The register's retained-inventory hash identifies the basis for these assignments.

Correction verified on 2026-10-07: the checker passes for 7,339 retained rows and 7,340 bounded successor identities; an isolated removal of the Leadership Cold-Blooded successor is refused without changing the maintained register. `profile.active-weapon-restrictions` now declares its construction observable in `tests/specs/structural/phase-verification.yaml`, referencing the existing Loremaster use-versus-ownership case. The two focused construction/evidence checks pass. The structural audit's missing-profile-evidence and missing-observable errors are removed (7 evidenced profile bindings; all 266 canonical bindings have observables). It still reports the two unrelated automatic-compiler projection errors for `night-goblins-mic/snotling-mob-consists-of-5-snotlings` and `khemri-cursed-of-karak-zorn/cannibal-dwarfs`; this correction does not claim a green full structural gate or refresh unrelated snapshot pins.

The 2A staging gate is repaired (2026-10-06): its validator now accepts an explicit band grant with a known-profile recipient filter, matching the shared decision. The focused staging module passes all 8 cases, including rejection of unknown recipients and band grants missing their band declaration; no KB rule was changed. The editorial `unused_enum_value` gate is also repaired: member-specific justifications retain the entry recipients and Vampire bloodlines accepted by existing consumers. Six focused checks pass, including the strictness/staleness gates, compiler acceptance/rejection and detection of a new unjustified recipient value. No schema vocabulary or KB data was changed for that repair. Concurrent construction/KB-sweep failures were not re-run and remain recorded limitations.
