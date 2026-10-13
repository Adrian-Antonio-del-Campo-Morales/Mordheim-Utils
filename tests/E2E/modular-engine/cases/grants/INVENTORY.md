# Grants corpus — inventory and handoff

Scope of this pass: `tests/E2E/modular-engine/cases/grants` only. Nothing outside this directory was
edited, imported or executed. Every statement below is derived from the printed sources
(`sources/knowledge/**`), the accepted rulings in `docs/decisions/design-rulings.md` and the shared
construction stage the rules compile to (`packages/python/roster-construction/mordheim_construction/compiler.py`,
`_eligibility.js` and its mirror `packages/typescript/domain/eligibility/index.ts`, read for the
*observable* a clause has, never as an oracle). No engine was run, no copy or probe was made, and no
expectation was fitted to engine output.

This pass continues the correction recorded in the previous revision and settles the question that had
been answered the wrong way:

* the earlier revisions treated **an absent binding, projection or consumer as an absent requirement**,
  so a clause whose rule the printed text fully determines was left unauthored and marked `PARTIAL`.
  That is now an explicit error: the case and its result are authored whenever the *duel contract* can
  express both, and the missing wiring is recorded as the defect the scenario is written to detect.

## 1. Corpus state (after this pass)

| Measure | Value |
| --- | --- |
| YAML authoring files | 1468 |
| `AUTHORED` | 1273 |
| `PARTIAL` | 184 |
| `REVIEWED` | 11 |
| Declared scenarios | 4002 |
| Scenarios evidencing a refusal (`expect_error`) | 377 (350 distinct fragments) |
| Files using the carried/possession channel (`owned_item_ids`) | 37 |
| Admitted `scope: YES` clause markers | 1639 |
| Files with an empty body | 73 (all `PARTIAL`) |

`authoring_status` is authoring-only and says nothing about behaviour: every scenario is
`execution_status: UNEXECUTED` and carries no behavioural result. Only manual semantic review can
promote an ID to `REVIEWED`; the 11 `REVIEWED` files predate this pass and were not changed.

## 2. The expressibility test applied in this pass

A pending refusal is **authorable** when three things hold together, and was authored whenever they did:

1. the printed clause fixes the outcome (a prohibition, a bound, a threshold, a grant) and names its
   recipient;
2. the *duel contract* can state the case: a declared input reaches the gate the clause governs —
   `owned_item_ids` for a possession bound, a loadout slot for an active-weapon rule, `mounted` for a
   mount rule, a declared roll for an in-duel effect — without inventing a field;
3. the expectation is expressed in the **established diagnostic family** of the gate that fires
   (`"${token}" is forbidden for ${band}/${profile}.`, `missile weapons are forbidden for ${band}/${profile}`,
   `blackpowder weapons are forbidden for ${band}/${profile}`, `"${item_id}" is not on any equipment list of
   ${band}/${profile}.`, `special rule is not available to ${band}/${profile}: ${rule_id}`,
   `${band}/${profile} carries ${n} missile weapons; the printed clause allows ${max}.`,
   `The equipment of ${band}/${profile} includes no ${kinds}; the printed clause obliges acquiring one.`,
   `skills are not available to ${band}/${profile}: [...]`).

A **missing binding, projection or consumer is not a reason to withhold the scenario**: it is the defect
the scenario must detect. `PARTIAL` is reserved for what is genuinely missing — a scenario that cannot be
written, an input identity the KB does not carry, an observation the runner cannot read, or a normative
decision nobody has made.

## 3. Authored in this pass

### 3.1 Savage Goblin `Master of Throwing Weapons` — the 5/6 frontier and the ordinary control

[trollheim--lustria-savage-goblins--band--savage-goblin-special-skills-ma](trollheim--lustria-savage-goblins--band--savage-goblin-special-skills-ma--8a799550314c.yaml)
(`compiler.master-of-throwing-weapons`) is now fully authored — 4 scenarios — and the three engine gaps
that had been recorded as an *adapter gap* are recorded as the **defects these scenarios detect**:

* **Five admitted**: a Tracker carrying `short_bow ×3` + `javelin ×2` constructs and the engagement runs
  to the horizon. Both ids are on the profile's own hero equipment list; `bolas` (catalogue
  `kind: out-of-scope`, no ranged tag) and `shrunken_head`/`blowpipe` are not counted by the shared
  missile reading.
* **Six refused**: one unit above the printed allowance, asserted against the shared excess-weapons
  refusal — `lustria-savage-goblins/trackers carries 6 missile weapons; the printed clause allows 5.`
* **Ordinary control, no ability**: the same profile with three counted units is refused —
  `lustria-savage-goblins/trackers carries 3 missile weapons; the printed clause allows 2.` This is the
  printed "usual two" the clause replaces, so the admission of five is shown to be an enlargement rather
  than a vacuous allowance.
* **Recipient boundary** (already authored): `big-boss`, the band's own non-Tracker hero, is refused the
  rule by the shared recipient stage.

The three defects, all recorded in the file: the rule's own binding carries **no `parameters`**
(`sources/knowledge/bands/trollheim/lustria-savage-goblins/special-rules.yaml`); `profileFactsProjection`
reads `max_missile_weapons` only inside its `binding.id === "profile.equipment-restrictions"` branch; and
the ordinary baseline of two is published nowhere (`bandEquipmentLimits` reads band-grant rules only and
this rule's grant is `selectable`), so the value exists today only as
`CompiledFighter.missile_weapon_limit`. The bound is nonetheless decided by the rule, the violating
inputs are declarable through `owned_item_ids`, and the refusal family is established.

### 3.2 Druchii `Disdain` — the blackpowder prohibition

[mordheim--druchii-mic--band--disdain](mordheim--druchii-mic--band--disdain--unimplemented.druchii-mic.band.dis--641411a4798c.yaml)
(`compiler.no-blackpowder-weapons`) is authored as the refusal plus its acceptance control, mirroring the
identical dark-elves clause: `blackpowder weapons are forbidden for druchii-mic/noble` for a member
carrying `weapon.pistol`, and the same member without it constructs. The recipient is the whole warband
(`applies_to: {band: true}`), so this file's earlier reason — "the recipient profile id of this band is
not recorded in this origin" — is withdrawn: a band-granted rule needs no per-profile list, and the
band's printed Noble is its mandatory leader. Defects recorded: the band's row binds only the placeholder
`unimplemented.druchii-mic.band.disdain` with `binding: null`, and the same row's own runtime block still
says `scope: LATER / implemented: 'NO'` while the semantic register admits the clause.

### 3.3 Mourngul `Haunter of the Dark` — the improved Ethereal threshold

[mordheim--call-of-the-night-haint-mim--mourngul--haunter-of-the-dark](mordheim--call-of-the-night-haint-mim--mourngul--haunter-of-the-dark--un--a0fa48cd062f.yaml)
is authored — 3 scenarios — with the printed **3+** threshold: the save discards the hit on a declared
ethereal face of three (which the canonical 4+ lets through), one face below lets the wound resolve, and
the same faces on the sibling Ethereal bearer (`cairn-wraith`, canonical 4+) do not save, so the increase
belongs to this bearer. The case, the observation (`attacks.0.saved` / `damage` / `state.second.wounds`)
and the dice key (`round.0.first.attack.0.ethereal`) are all established by the sibling origin's authored
file, so nothing is invented. Defect recorded: `mechanic.ethereal-hit-save` is hard-coded to 4+ in
`modular/pools.py` and `modular/attacks.py` and the granted rule's binding is the placeholder
`unimplemented...` with `implemented: 'NO'`.

## 4. False blockers corrected (no scenario was written, the reason was wrong)

Three files had withheld authoring behind a claim that turned out to be factually false. The clauses stay
`PARTIAL` on a **narrower, accurate** datum:

* [snotlings-web/small-hands](mordheim--snotlings-web--band--small-hands--unimplemented.snotlings-web--4c4c0b60df86.yaml):
  the claim that the five named weapons "match no catalogue tag the fixture could supply" is wrong —
  `blunderbuss`, `elf_bow`, `handgun` and `long_bow` are catalogue rows and the shared token reader
  matches a token equal to the item id (only the printed "Long Rifles" has no plain row). The real blocker
  is **gate order plus the recipient's own list**: the offered-set gate runs before the printed forbids
  gate, no non-excepted recipient list carries a named weapon, and the only list that does (the Shoota
  Equipment List) belongs to the profile the register itself records as this clause's exception.
* [halflings-mic/too-big](mordheim--halflings-mic--band--too-big--unimplemented.halflings-mic.band--1beddbc52c1a.yaml):
  the same false catalogue claim. The only `long_bow` row belongs to the **Village Ogre** list, and a
  Village Ogre is outside the printed Halfling recipient set, so the clause has no legal construction
  input either.
* [gunnery-school-of-nuln/proud-to-a-fault](mordheim--gunnery-school-of-nuln--band--proud-to-a-fault--compiler.proud--a9f49ae25bff.yaml):
  "no non-blackpowder ranged item in the executable catalogue" is corrected — the catalogue has them; the
  band's own two lists do not (every ranged row there is blackpowder, and `pigeon_bombs` is an
  out-of-scope row, not a ranged weapon). The origin's only accepted observable is a construction tag, and
  the duel runner exposes no channel for `construction_tags`.

## 5. Status review: `PARTIAL` is not for missing wiring

Seven IDs whose clauses already carry scenarios and whose only remaining item is engine wiring were held
at `PARTIAL` for that reason. That conflates a defect with a missing requirement, so they are now
`AUTHORED`, with the pending item retained verbatim as the recorded defect:

| File | Wiring the authored scenarios detect |
| --- | --- |
| [black-orcs/let-the-goons-do-the-work](mordheim--black-orcs--band--let-the-goons-do-the-work--unimplemented.bla--314a14e637d6.yaml) | the mount-eligibility contract that emits the printed refusal |
| [haint-mim/malignant-spirits--violent-entry](mordheim--call-of-the-night-haint-mim--malignant-spirits--violent-entry--52c2fefec596.yaml) | the operator marking the charge as the summoning turn's charge |
| [carnival-of-chaos/blessings-of-nurgle--mark-of-nurgle](mordheim--carnival-of-chaos--band--blessings-of-nurgle-mark-of-nurgle--s--2b83c387c442.yaml) | the compiled poison-immunity projection |
| [gunnery-school-of-nuln/marksmen--quick-reload](mordheim--gunnery-school-of-nuln--marksmen--quick-reload--compiler.quick--201a2ed1f844.yaml) | the compiled grant projection supplying the granted skill |
| [halflings-mic/village-ogre--skills](mordheim--halflings-mic--village-ogre--skills--unimplemented.halflings-m--ef47eef2cc1f.yaml) | the compiled access projection for the promoted recipient |
| [outlaws-of-stirwood-forest/band--bow-discipline](mordheim--outlaws-of-stirwood-forest--band--bow-discipline--mechanic.bow--57e56638b9a8.yaml) | the kit-route projection feeding `equipmentSetIssues` |
| [outlaws-of-stirwood-forest-redux-fbg/band--bow-restrictions](mordheim--outlaws-of-stirwood-forest-redux-fbg--band--bow-restrictions--94516727588a.yaml) | the same kit-route projection |

## 6. Positive controls (unchanged from the previous revision, re-verified here)

* [crooked-moon-kep/snotling-mob--equipment-restrictions](mordheim--crooked-moon-kep--snotling-mob--equipment-restrictions--profil--06047bed410b.yaml)
  and [khemri-cursed-of-karak-zorn/cannibal-dwarfs--equipment-restrictions](trollheim--khemri-cursed-of-karak-zorn--cannibal-dwarfs--equipment-restr--58029b9b5391.yaml)
  keep their printed acceptances (the free kit) beside the refusals.
* [hochland-bandits/powders-expensive](mordheim--hochland-bandits--band--powders-expensive--compiler.powder-s-e--6ea5c57dd9eb.yaml)
  keeps the printed hero scope as the reachable face; the scoped prohibition has no reachable input.
* Both Saurus files keep the **printed** expectation, so the recipient-list defect stays visible.
* The Extra Arm control stays on the legal `off_hand_id` slot (see §8).

## 7. `owned_item_ids`: possession versus active equipment (unchanged)

37 files use the carried channel; every conversion serves a *selection / carrying / possession* clause on
a mechanic-less item, and the carried channel also supplies contextual identity where a clause needs it.
The one file that combines it with active-weapon text
([high-elves-lus/loremaster--tower-of-hoeth](mordheim--high-elves-lus--loremaster--tower-of-hoeth--profile.active-wea--de64eb1e85f2.yaml))
keeps its refusal and acceptance on the active slot and uses possession only for the ownership-only
variant. The three new cases above use the channel the same way (possession bound, kit bound, declared
roll), and none of them narrows a recipient, changes a permission or substitutes a refusal for an
acceptance.

## 8. Fixture defect repaired (unchanged)

The Extra Arm control had been moved onto `defence_ids: [defence.shield]`, which `compiler.py` refuses
outright (`hand-held defences belong in off_hand_id`); it now wears the shield as `off_hand_id`. A
directory-wide slot-prefix scan reports **0** wrong-slot declarations in `grants`.

## 9. Empty bodies and the remaining `PARTIAL` dispositions

73 empty bodies, all `PARTIAL`, each carrying an accepted scope disposition or a named pending datum — an
empty body is never a pass.

* **53** record an accepted scope disposition (roster succession, warband/campaign state, the mount
  subsystem, post-battle injury, group Rout/Ld auras, promotion and advancement-time choice, casting
  producers, and similar). An empty body is the correct artefact for these.
* **20** name a concrete pending datum. Two of the previous revision's 22 were **authored in this pass**
  (the Mourngul threshold and the Druchii prohibition). The remainder are the classes below.

## 10. Remaining blockers (concrete, outside this directory)

These stay `PARTIAL` because the missing piece is neither a scenario this pass could write nor engine
wiring:

1. **An input identity the KB does not carry** — the three band special-skill tables
   ([amazons-lustria](mordheim--amazons-lustria--band--amazon-special-skills--profile.skill-ac--636fb3e08319.yaml),
   [arabian-tomb-raiders](mordheim--arabian-tomb-raiders--band--arabian-tomb-raiders-special-skill--2084e44c7a61.yaml),
   [cursed-cavalcade](mordheim--cursed-cavalcade--band--cursed-cavalcade-special-skills--profi--17be81684201.yaml)):
   their `profile.skill-access` binding declares `{category: special}` with **no members**, and the shared
   branch answers the informational `skill_pending_special_list` for every special skill, so no admitted
   member id exists to name. The members are published as the band's own `warband_skill` rule rows
   (`band--amazon-special-skills-skink-hunter`, …), so the missing datum is the member-id list on the
   binding, not a new operator.
2. **Possession-bound projection** — the Savage Goblin case above; authored, and the standing defect.
3. **Free-kit exemption scope** — `tokenForbids("equipment"/"weapons")` matches the profile's own free kit
   while `equipmentIssue()`'s exemption matches only a literal `fixed_equipment` id. The two acceptances
   are authored as standing future acceptances.
4. **Blackpowder prohibition with no reachable input** — no Bandit Henchman row offers a blackpowder weapon
   (Hochland).
5. **Gate-order binders with no legal input** — small-hands and too-big (§4): the printed token refusal
   cannot be reached because the offered-set gate answers first and no recipient list carries a named
   weapon.
6. **Construction tags with no observation channel** — [gunnery-school-of-nuln/proud-to-a-fault](mordheim--gunnery-school-of-nuln--band--proud-to-a-fault--compiler.proud--a9f49ae25bff.yaml).
7. **Saurus recipient list** — the shared stage's Saurus ids omit `saurus-totem-warriors`; the printed
   expectation is kept so the defect stays visible.
8. **Operators the source itself still owes** — [crude-belch](mordheim--maneaters--band--ogres-special-skills-crude-belch--unimplement--e58d2a3b1873.yaml)
   (a Leadership-test operator plus a turn-scoped −1 to-hit term with its per-engagement reuse guard) and
   [ghostly-howl](mordheim--call-of-the-night-haint-mim--tomb-banshee--ghostly-howl--unimp--e17825947b2c.yaml)
   (a new `resolve_round` branch, with the printed −D6 leadership sentence and the recorded charm contract
   disagreeing, so a normative choice is needed as well).
9. **A loadout choice the vocabulary lacks** — [nipponese-expedition-web/ashigaru--wall-of-steel](mordheim--nipponese-expedition-web--ashigaru--wall-of-steel--unimplement--60d9c4eda4a4.yaml):
   the printed option to wield a spear two-handed has no declaring field, so the case itself is
   unstatable.
10. **An item that is not a record** — [snotlings-web/band--pointy-stick](mordheim--snotlings-web--band--pointy-stick--unimplemented.snotlings-web--c77076bbdeb1.yaml):
    the weapon exists only as a prose arm of the band's "Dagger/Pointy Stick" row, so no build can carry it
    even though `effect.target_armour_bonus` already resolves the printed 6+.
11. **Normative decisions** — the [Andanti inverted-target parry](mordheim--dreamwalkers-cult-of-morr-fbg--andanti--estalian-tecnique--uni--18de162ea6de.yaml),
    the Clan Angrund effective-Strength binding (no accepted source binds this band's recipient to the
    armour variant, and the tape must declare exactly the armour die the engine asks for), and the
    [House Guard relay](mordheim--house-guard-sc--adjutant--relay-orders--unimplemented.house-gu--8c4d410e5ddf.yaml)
    (an accepted duel-context shape for a relayed borrow is still owed).
12. **Next authorable set, not written in this pass** — the remaining `[B]`-marked pendings whose own notes
    say the vocabulary exists and only a binding/declare is missing:
    [ogre-hunting-party-web/ogre-hunting-skills `netter`](mordheim--ogre-hunting-party-web--band--ogre-hunting-skills--unimplement--1f2dd9eac976.yaml)
    (the `mechanic.netter` tape is authored at its own origin), and the two Swabbie-rabble list-bound files
    ([pirates](mordheim--pirates--swabbies--rabble--compiler.swabbie-rabble-loadout--6a63c523f7d1.yaml),
    [trollheim-lustria-pirates](trollheim--lustria-pirates--swabbies--rabble--compiler.swabbie-rabble-lo--14db1ad2c193.yaml)),
    which need the resolved list ids read from
    `sources/knowledge/bands/*/pirates/equipment-access.yaml` before the accepted and refused loadouts can
    be declared. They are named here so the next pass starts from a worklist, not a search.

None of these is reported as a pass, an exclusion substitute, or a weakened expectation.

## 11. Static verification performed (engine-free, proportional)

* **YAML parse of all 1468 files** — 0 failures; every document is a list.
* **Structural invariants** — 0 problems across 4002 scenarios: each scenario's `audit_id` matches its file
  header, every `covers` reference is one of the file's declared clause ids, every scenario id is unique
  within its file, and every scenario asserts exactly one kind (observations xor `expect_error`).
* **`expect_error` sweep** — 350 distinct fragments; none asserts engine-internal vocabulary (`duel`,
  `unimplemented`, `operator`, `not implemented`, `compiler.`, `implementation`); the previously recorded
  engine-internal string now appears only inside header comments that record the gap.
* **Status coherence** — 1273 `AUTHORED` / 184 `PARTIAL` / 73 empty bodies, and the `PARTIAL` reasons were
  re-read for the wiring-only class (§5); 0 files remain `PARTIAL` solely on a missing binding, projection
  or consumer.
* **`owned_item_ids`** — 37 files, all on a selection/carrying/possession clause (§7).
* **Slot legality** — 0 wrong-slot declarations in `grants` (§8).

Not run, deliberately: any import or execution of the combat pipeline, the compiler, the runner, or the
static-checker's semantic model. A `covers` label and a passing structural check do not demonstrate a
clause, and an unexecuted scenario is neither a pass nor a failure; the boundary and threshold cases added
here are written to fail against the current implementation, which is their purpose.
