# L06 — canonical local weapon profiles

**Status: weapon block, Killing Blow and Shock Rod implemented and verified, 2026-10-03.**
Skull Busta's reachable canonical clauses are also delivered. Knight's Helm
was classified as a source erratum by the user on 2026-10-04; pending KB cleanup,
not counterpart implementation, is recorded as [F063](T13-execution-follow-ups.md#t13-f063--skull-busta-knights-helm-counterpart-is-absent-from-the-kb).
Eight registered item origins now have source-backed mappings, shared recipient
decisions, Combat Lab catalogue access and actual modular attack consumption.
L06 remains in progress for the other admitted hit/wound/critical/poison/parry
families. This delivery does not certify optimized engines or close T13.

## Subsequent L06 milestone: Long Daggers and Knuckledusters

Delivered and verified on 2026-10-03: `long_daggers` maps to
`weapon.long-daggers`, and `knuckledusters` to `weapon.knuckledusters`.
Both use normal Strength and the existing Pair operator for exactly one extra
Attack. Pair occupies both active hands. Long Daggers additionally use ordinary
sword-style Parry, without the reroll of Fighting Claws. Their dagger family
tag does not add the ordinary dagger's enemy armour-save bonus. Knuckledusters
do not inherit Brass Knuckles' +1 Strength or -2 Initiative, or Concussion.
No modular resolver change was needed.

Sources consulted:

- [Silent Brotherhood](https://broheim.net/downloads/warbands/supplement/sealedcity/Silent%20Brotherhood.pdf),
  PDF pp. 3 and 5: Brotherhood equipment list marks Long Daggers Heroes-only;
  the equipment entry specifies Pair and Parry. The shared TypeScript decision
  applies the recipient restriction to catalogue offerings and compilation,
  including supplied Hero promotion. Unpromoted Agents/Novices are refused.
- [Low Kings](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Low%20Kings.pdf),
  PDF p. 5: normal Strength, Pair and Concealable. Canonical Racketeer access
  now reaches the actual paired profile.

The canonical item text remains complete. Knuckledusters' mapping certifies
the local paired attack only: Concealable's carried-weapon exemption and use
in weapon-ban scenarios are still admitted, pending the missing shared carry
and scenario contracts under [F065](T13-execution-follow-ups.md#t13-f065--knuckledusters-concealable-has-no-carry-or-scenario-consumer).
It is not a complete-item or scenario certificate. Cutthroat remains a distinct
L06 selectable skill; this item mapping does not activate its armour modifier.

Seven cases were added to the existing
[local item suite](../../../../tests/python/construction/test_local_weapon_items.py).
They exercise canonical whole-round attack counts (Silent Master 2+1 and
Racketeer 1+1), a single successful/failed parry, normal Strength/armour/injury,
real catalogue access, Hero promotion, hand occupancy and foreign-band refusal.
The maintained execution inventory now runs 201 mechanisms (two added).
Validation: 59 affected Python cases and 26 existing shared TypeScript cases
passed; workspace typechecks, bundle freshness, catalogue checks, schemas,
generated artefact freshness and documentation links passed. The initial two
test failures were a test assertion comparing the empty result tuple to a list;
the assertion now checks absence of issues.

Evidence and entry backups: `build/cache/t13-parallel/paired-weapons/`.
Optimized execution explicitly refuses these new profiles pending L19/L20.
No new spec/mutation/review battery or full T14 gate was introduced for this
reused operator. L06 remains open.

### Hellblade dependency discovered in the same continuation

The [Khorne Raiders source](https://broheim.net/downloads/warbands/supplement/sartosa/Khorne%20Raiders.pdf),
PDF p. 2, excludes Undead and Daemons from Soulseeking's +1 hit and allows
Deadly's critical 5/6 only when the ordinary wound target is 4 or better.
The current `undead_or_possessed` bit cannot represent that exact exception:
it conflates categories and is missing on many canonical Undead profiles.
No Hellblade effect was activated using that bit, Poison immunity or No Pain.
[F064](T13-execution-follow-ups.md#t13-f064--hellblade-needs-exact-undead-and-daemon-target-facts)
routes the classification prerequisite to L11 and the dependent weapon
implementation back to L06. The critical target limit must also be implemented
when the weapon resumes; the generic critical-on-five path alone is insufficient.

## Subsequent L06 milestone: Blood Dragon Killing Blow

The [Blood Dragons source](https://broheim.net/downloads/warbands/supplement/mousillon/Blood%20Dragons.pdf),
Wights p. 4 and Grave Guards p. 6, specifies automatic wounding on a natural
hit six, no parry of that strike, and ordinary armour/special saves. Both
canonical rules and their exact 2B mirror now bind automatically to the one
new `mechanic.killing-blow` operator. Original origin keys remain in
`T13-obligations.csv`; current runtime effect identity is `mechanic.killing-blow`.
The generic bloodline-choice route is not activated by these profile grants.

The existing attack resolver uses physical hit provenance, including prepared
pool hits, to suppress the parry and replace the ordinary wound step. It creates
no wound die or critical face. A non-six/automatic hit retains the ordinary
wound path. The shared pool, phase algorithms and construction code are unchanged.
Black Lotus retains its existing explicit critical attempt and guaranteed-wound
fallback; poison immunity removes that poison contribution without removing
Killing Blow. This free-selection composition is not advertised as canonical
Blood Dragon access to poison.

The single new maintained [test_killing_blow.py](../../../../tests/python/combat/modular/test_killing_blow.py)
has **10 cases**: both canonical recipients, absence/adjacent controls, armour,
ward/regeneration, Lucky Charm, automatic-hit provenance, poison composition
and a mixed 6/4 pool against an exceptional six-parrying defender. Its exact
request tapes detect unwanted parry/wound/critical rolls and per-pool trigger
leakage. No additional test hierarchy or mutation/specification battery was added.

The final affected run is **226 passed**, reusing Spectral Touch, Shifty, source
corrections and the existing every-mechanism scalar consumer (**197 = 196 + one
operator**). Three maintained schemas, the real band loader, exact 2B mirror
and Combat Lab profile-rule status pass. The publication is regenerated and
checked; optimized execution is explicitly refused until L19/L20. Evidence:
`build/cache/t13-parallel/killing-blow/`, including frozen entry inputs and logs.
Final semantic-spec/origin reconciliation remains L21 and independent
certification L22; these tests establish modular behavior, not a T14 certificate.

## Subsequent L06 milestone: Shock Rod

The [Clan Pristekk primary source](https://broheim.net/downloads/warbands/supplement/sealedcity/Clan%20Pristekk.pdf),
special equipment (PDF page 5; printed page 4), specifies normal Strength,
First Strike, two hands and stunned Injury results 1–4. The canonical
`shock_rod` item now maps to `weapon.shock-rod`; the existing shared equipment
decision admits Chieftain/Packmasters and refuses the Clanrat-list profiles
and foreign bands. No shared eligibility code or band data needed changing.
The printed equipment-list/description price discrepancy (10/15 gc) is retained.

The weapon uses the existing priority and hand operators. Its local `shock`
injury-context flag applies the printed 1–4 replacement at the existing
weapon-injury replacement stage, independently of Concussion immunity.
Defender-specific injury profiles and subsequent No Pain, survivor and stun
reactions retain their existing ordering; this is not a new global warrior trait.
No Pain and a successful helmet still turn stunned into knocked down.
Optimized execution explicitly refuses the profile until L19/L20.

Seven focused cases extend the existing [item suite](../../../../tests/python/construction/test_local_weapon_items.py):
1/2/4/5 boundaries, ordinary-mace absence and defensive reactions, a real
round before a faster enemy, canonical access and two-hand/optimized refusals.
The affected run passes **153 cases**, reusing existing injury/interaction/source-correction
suites and the every-mechanism round consumer (**198 operators**).
Nine catalogue/execution checks, three maintained schemas, publication freshness
and documentation links also pass.
Evidence: `build/cache/t13-parallel/shock-rod/`. Publication/schema/catalogue
checks accompany this milestone; source-spec/origin reconciliation remains L21
and independent certification L22. L06 is still in progress.

## Subsequent L06 milestone: Skull Busta

The [Karak Azgal primary source](https://broheim.net/downloads/campaigns/karakazgal/Karak%20Azgal.pdf),
printed page 59, specifies +1 Strength in the first combat turn, ordinary hammer
behavior thereafter, Concussion/2–4 stunned and Basha (ordinary helmet stun saves
only on six). The independent Feelin' wobbly/Basha clauses remain attached to
the weapon in later rounds; only the ordinary first-turn Strength bonus expires.
`skull_busta` now maps to `weapon.skull-busta`, reusing the existing first-turn
Strength and Concussion operators. Its mace tag retains hammer-family behavior.

The shared decision excludes Savage Gobbo Boyz from the otherwise common list.
One shared active-loadout predicate refuses mounted use, another weapon or use
in an off/extra hand, and permits shields (including the existing Kite Shield);
a buckler is not a shield. Both the specialist compiler entry and the batch
proposal/final entry reuse it. `mounted` is a supplied fact, defaulting to false;
the Python transport supplies the existing build value without interpreting it.
Owning a holstered Skull Busta while another weapon is active does not trigger
its use restrictions. No campaign mount service or ownership limit is invented.

Basha modifies only this attack's available helmet reaction to 6+. No Pain
converts the injury before the helmet step, and Thick Skull keeps its existing
replacement reaction and helmet improvement. The user classified the source's
Knight's Helm reference as an erratum on 2026-10-04. Its 4+ counterpart is no
longer an admitted implementation obligation; no replacement item is invented.
[F063](T13-execution-follow-ups.md#t13-f063--skull-busta-knights-helm-counterpart-is-absent-from-the-kb)
tracks the pending KB removal and dependent reference cleanup. Item metadata
enables the supported canonical profile; optimized engines remain separate.

Six cases extend the existing item suite, covering first/later wound thresholds,
helmets, ordinary-mace controls, No Pain/Thick Skull, actual catalogue access,
shared restrictions and optimized refusal. One direct TypeScript case covers
batch aliases, proposals, extra-hand exclusion and holstered ownership. Existing
shared transport/source-correction/operator cases are reused. Evidence:
`build/cache/t13-parallel/skull-busta/`. L19/L20 own ports; L21 owns final
source-spec/origin reconciliation and L22 independent certification.
Validation: **190 affected Python cases**, **30 TypeScript cases**, nine
catalogue/execution checks and three maintained schemas pass. The shared bundle,
workspace typechecks, publication freshness and documentation links also pass.
The existing every-mechanism round consumer now exercises **199 operators**.

## Implemented items and consulted sources

| Canonical item | Executable mapping and printed clauses | Primary source |
| --- | --- | --- |
| `darksteel_blade` | Existing `material.dark-elf-blade`: +1 to the critical table and Injury faces 2–4 stunned. Druchii Heroes only. No wound reroll. | [Druchii, Darksteel Blade](https://mordheimer.net/docs/warbands/grade-2a-warbands/druchii) |
| `pry_bar` | New `weapon.pry-bar`: ordinary Strength, Concussion, Parry; one hand. | [Grave Robbers, special equipment](https://mordheimer.net/docs/warbands/grade-2a-warbands/grave-robbers) |
| `kanabo` | New `weapon.kanabo`: +1 Strength, Concussion, two hands. | [Nipponese Expedition, special equipment](https://mordheimer.net/docs/warbands/grade-2a-warbands/nipponese-expedition) |
| `wizards_staff` | New `weapon.wizards-staff`: ordinary Strength, Concussion, Parry, two hands. | [Sorcerous Society, special equipment](https://mordheimer.net/docs/warbands/grade-2a-warbands/sorcerous-society) |
| `katana` | New `weapon.katana`: +1 Strength, Parry, two hands. The Cathayan Pirate list restricts it to Heroes; Nippon's lists admit Henchmen. | [Cathayan Pirates, equipment and profiles](https://broheim.net/downloads/warbands/supplement/sartosa/Pirates%20of%20the%20Cathayan%20Sea.pdf), [Nipponese Expedition](https://mordheimer.net/docs/warbands/grade-2a-warbands/nipponese-expedition) |
| `spirit_knife` | New `weapon.spirit-knife`: ordinary Strength, +1 enemy armour save; natural hit six adds an immediate wound before the ordinary wound roll. Ethereal Heroes only. | [Call of the Night Haint, printed pp. 080–082](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Call%20Of%20The%20Night%20Haint.pdf) |
| `spear_stave` | Existing `weapon.halberd`, as the source explicitly specifies. | [Sea Ghosts, special equipment](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Sea%20Ghosts.pdf) |
| `wrench` | Existing `weapon.mace`, using the printed club equivalence. | [Metal Mongers, special equipment](https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Metal%20Mongers.pdf) |

The exact original identities remain in [T13-obligations.csv](T13-obligations.csv):
four `sources/2A/catalog/items/…` and four `sources/2B/catalog/items/…` origins,
one unique `origin_key` per item above. Their source prose and prices are preserved.
Maintained loaders derive the item mappings from canonical item metadata; no
new explicit simulation-mapping rows or staging prose edits were needed.

Darksteel Blade does not map to similarly named `material.dark-steel`, whose
wound-reroll behavior is different. Wizard's Staff does not borrow Quarter
Staff's Initiative bonus. Katana does not borrow the Elven Greatsword's Strength
or strike-last behavior. Five distinct profiles are added to the existing
mechanics and effect-set contract; all hit/wound/parry/injury operators are reused.

## Spirit Knife: separate Q146 disposition

The item source was reviewed separately from Spirit Hosts. Its natural-six
trigger and additional-then-ordinary wound wording justify reusing the accepted
[Spectral Touch Q019 composition](../../../decisions/design-rulings.md#spectral-touch-q019)
and [R1–R4 modular implementation](T13-spectral-touch.md). The effect is attached
to the weapon, not the warrior's global effects. An ordinary other-hand mace
does not gain the additional wound. Automatic hits do not fabricate a six;
accepted parry, save, injury/reaction and interruption handling remains intact.
The knife's own +1 enemy armour save applies to both damage contributions.

This resolves Q146's relationship question for the item on the modular engine;
it does not inherit a certificate from the Spirit Host pilot. Canonical
construction and real attack witnesses establish this separate activation.
No source exception to saves/parries or new composition ruling was introduced.

The shared eligibility decision permits Cairn Wraith, Tomb Banshee and
Malignant Spirits, which are printed Ethereal Heroes, and Revenants configured
with the existing local `promotion.hero` fact and printed Spectral Ascension.
It refuses the human Corpse Master and ordinary Henchman Revenants. This is
local construction, not a campaign advance or promotion service. The source's
general Ethereal combat behavior still belongs to its psychology/defense/movement
owners; equipping a knife does not implement every Ethereal clause.

The PDF has a pre-existing price discrepancy (list 25 gc, equipment prose 20 gc).
This lot preserves both source facts; no campaign price or purchase ruling is
made. Its data reconciliation belongs to L21's source/catalogue owner.

## Shared construction and runtime boundary

Recipient filtering lives in the maintained TypeScript eligibility module's
existing equipment projection. The generated Python bundle is rebuilt through
`npm run build:eligibility`. Combat Lab and Warband Manager consume the same
decision; no Python eligibility table or alternate constructor was added.
See the [shared ownership contract](../../../reference/eligibility.md).

The public Combat Lab catalogue offers the mapped weapons/material to canonical
eligible profiles and rejects the forbidden recipients. Two-hand validation
uses the existing slot contract. The generated browser knowledge publication
is refreshed through its maintained generator, with a successful `--check`.
Visible editor/analysis integration of all final families remains L18; this
delivery proves the actual catalogue, compiler and modular attack routes.

The four new ordinary profiles and Spirit Knife explicitly refuse optimized
execution in `require_optimized_support`. Their applicable ports remain L19/L20.
The three existing aliases reuse their existing operators; this lot adds no
new optimized certification claim. The modular attack implementation and the
NumPy/native engines were not edited.

## Proportional validation

The single new maintained suite is
[test_local_weapon_items.py](../../../../tests/python/construction/test_local_weapon_items.py),
with **15 collected cases**. It uses canonical compilation and the public
`resolve_reference_attack` with strict dice tapes, plus the real Combat Lab
catalogue/shared validation. Expectations come from the consulted source clauses.

It observes Strength wound thresholds and Injury face 2, actual parries, the
Darksteel critical-table boundary against an ordinary sword, legal/illegal
recipients, two-hand refusal, explicit optimized refusal, and Spirit Knife's
hand-local additional damage and inherited armour handling. Existing Spectral
cases supply the accepted sequencing/reaction contract; no duplicate mutation,
integration or semantic-spec battery was added for these reused operators.

| Check | Result |
| --- | --- |
| New suite, final catalogue assertions included | 15 passed |
| New suite + selectable/equipment matrix + accepted Spectral suite + existing every-mechanism modular consumer | 129 passed |
| Existing catalogue execution/mechanic/mapping checks | 9 passed, 38 deselected |
| Existing direct shared eligibility, canonical choices, recipients and transport suites | 42 TypeScript cases passed |
| Workspace typecheck / generated eligibility bundle freshness | Exit 0 / exit 0 |
| Maintained editorial schemas and loader mappings | Six documents valid; eight mappings and eight unique origins resolved |
| Browser knowledge generator / `--check` | Publication regenerated / exit 0 |

The 129-case affected run precedes the final catalogue-offering assertions;
the final 15-case rerun verifies those assertions. Production inputs are the
same; unaffected suites were not repeated solely for that test refinement.

The existing every-mechanism scalar test now expects **196 = 191 + five weapon
profiles**, retaining its independent traversal and execution assertions. Only
that concrete count and an obsolete Gromril comparator comment were updated.
F057's reserved parity files, source pins, scope flags and coverage budgets
were not changed. No full semantic/parity/coverage/CI certificate is claimed;
the broad gates remain at the stable milestones in the
[proportional-validation policy](T13-T15-remaining-plan.md#6-proportional-validation-and-progress).

## Remaining L06 scope and subsequent owners

This is a completed weapon block, not completion of L06. Continue in L06 with
the admitted source-specific weapons, hit/wound/critical modifiers and rerolls,
natural-six auto-wounds, material/target filters, poison/immunity and parry
variants from the original origin register. This includes remaining Hellblade,
other admitted local item profiles,
conditional parries and the L05 dispositions for `corpse_liquor` and
`runic_sword_of_snorri_elfbane`. Resolve each existing source gate in that family.
Related sequence/resource clauses remain L08/L09, defenses L07, psychology L11,
movement L14 and composite participants L17. These are existing owners, not
new microtasks or exclusions.

F023's item mapping/recipient gap and F025's separate Q146 activation are
resolved for this canonical modular boundary. Broader product/backend closure
remains L18–L22, with the original source identities retained for L21.

Evidence is retained under `build/cache/t13-parallel/local-weapons/`: frozen
entry bytes/hashes, command logs, focused schema/mapping/origin checks and
closing hashes. Entry HEAD remains `1b7f7cf`; no commit, push or agent launch.
## L06 / F072 — Woodsmen Quarterstaff variant (2026-10-04)

The canonical Woodsmen `quarter_staff` selection now compiles its printed
Strength +1, Two-handed and Parry, without the generic Balanced staff's
Initiative +1. The automatic `compiler.woodsmen-quarterstaff` binding qualifies
the existing weapon selection by its band source; it does not grant the bonus
to swords, fists or other weapons. The generic and Cathayan staff remain
unchanged. The Woodsmen variant does not inherit the Cathayan Freestyle bonus
bare-hand attack. Material and poison contributions are retained, including
the poison-free weapon projection used by the modular pipeline.

Sources: [Woodsmen rule and printed text](../../../../sources/knowledge/bands/mordheim/woodsmen-de-artois-mou/special-rules.yaml),
[canonical equipment list](../../../../sources/knowledge/bands/mordheim/woodsmen-de-artois-mou/equipment-access.yaml),
[Cathayan comparison source](../../../../sources/knowledge/bands/mordheim/pirates-of-the-cathayan-sea-sar/special-rules.yaml).
The existing 2B mirror is aligned; printed prose, translations, item identity
and equipment access are preserved. The shooting-only shield clause is outside
the duel scope, rather than an omitted melee permission.

Validation: two focused cases in the maintained
`test_local_modifier_variants.py` module pass through canonical compilation and
real modular attacks: the S4/T3 wound boundary versus the Cathayan S3 control,
an unaffected Woodsmen sword, a successful parry and refusals for a second
weapon, shield and buckler. The structural catalogue snapshot passes:
751 implemented rule records, 212 canonical bindings, 37 automatic compiler
bindings; execution mechanics remain 239. The family register now has
97 families / 316 members (43 compiler families). No new resolver or engine
state, optimized port, full-suite run or source-pin refresh is part of this lot.
