# T13.4a — Shifty semantic review dossier

> Current F005 disposition — 2026-10-04: the user accepted coexistence of the pistol and Shifty extra attacks. The modular implementation now supports pistol-only loadouts; mixed kits retain melee nomination. Earlier dated refusal/S2 limits below are historical and superseded. F026/Q151 broader pistol contracts and optimized ports remain separate. See [implementation and validation](T13-local-modifiers-defences.md#q128q013f005--accepted-contracts-implemented).

> Current ownership — 2026-10-02. The [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation) is already implemented for both products. Pilot combat tests below prove the modular mechanism at their reviewed revision; injected tags do not establish canonical legal selection or activation. After the required source decisions, reuse shared eligibility for legal access and separately prove KB binding/compiler activation before optimized ports. Historical results and later acceptance sections retain their own stated limits.

Prepared for human review on 2026-10-01. Current status, 2026-10-02:
**S1–S4 accepted by the user; F003 resolved for the modular contract**.
[Acceptance and boundaries](#human-acceptance--2026-10-02) govern subsequent work.
This is a source and implementation review of the existing
modular proposal, not canonical selection, an engine repair or backend acceptance.
The user accepted Spectral Touch R1–R4 separately; its F007 modular repair is
also independently accepted and was not executed by this dossier.

## Examined entry and scope

- Workspace: `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`.
- Branch `2A2B`, HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`, dirty tree;
  local tracking shows one commit ahead of `origin/2A2B`. No fetch occurred.
- Entry: `2026-10-01T08:40:17.613908+00:00`. Evidence is under
  `build/cache/t13-parallel/shifty-review/`; `entry.json` captures 78 input
  hashes, status and worktrees. HEAD alone does not identify the examined tree.
- The first full-diff capture hit Windows text-decoding failure. Recovery uses
  raw Git output in `entry.diff` / `entry-staged.diff` and retains stderr. The
  recovered diff includes this lot's reservation addition; the input hashes
  were captured before that addition. Do not mistake the recovered diff for
  a wholly pre-reservation snapshot.
- `rounds.py` and `test_shifty.py` match the historical Shifty delivery hashes.
  `pools.py` differs from that delivery because Spectral Touch subsequently
  added provenance transport; it matches the Spectral Touch review entry.
  `historical-comparison.json` records comparisons. Today's focused execution
  is independent of the historical 348/397-test claims.
- No applicable workspace `AGENTS.md` was found. The user-authorized scope is
  this new dossier, own evidence and pertinent coordination in README/T13/
  follow-ups. Existing code, tests, YAML, specifications and generated assets
  are read-only. No agents are launched or contacted; no commit/push occurs.
- External source/fingerprint work is separate. Shared coordination changed
  during this review to record external B's hireling/command acceptance and
  F036–F039. Those changes are preserved and not independently certified here.
- Shared TypeScript eligibility and Python embedded transport remain current
  architecture. No Python eligibility fallback is introduced; F035 stays open.
  The previous 211-test construction result is not reused as current evidence.

| Input | SHA256 |
| --- | --- |
| `modular/rounds.py` | `d444f5a37b3e43f5e0c99febb6636b1a9ad5021216ac7a4115084807a3a0c11f` |
| `modular/pools.py` | `567a9636f7ac652d404c3c6cc09e6fb3748249dd5b6ee855005c30a25f669a0a` |
| `test_shifty.py` | `09b32382bbdf127c4493bd96f06ff3fa1b155df15b06d7767aa0377d07963f9c` |

## Sources and explicit authority

| Key | Source / locator |
| --- | --- |
| H | [Original Halflings PDF](https://broheim.net/downloads/warbands/experimental/Halflings.pdf), PDF page 4, Special Skills / Shifty; pages 1–3, Heroes and equipment. Original text and page-4 screenshot consulted online. No local PDF copy/hash is claimed. |
| C | [Core rules Part 1](https://broheim.net/downloads/rules/Mordheim%20-%20Part%201%20-%20Background%20%26%20Rules.pdf), printed/PDF 18 priority, 19 two weapons, 23 Frenzy, 24 Fist, 27 double-handed weapons, 31 pistols. Original PDF copied from the earlier dossier's evidence and extracted locally. |
| E | [Rules Review / Errata](https://broheim.net/downloads/rules/Errata.pdf), PDF page 1, Page 34 priority amendment; PDF page 3, Page 85 Whipcrack. Original PDF copied and extracted locally. |
| T | [Halflings transcription](https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings), skill table / Special Skills; [weapons](https://mordheimer.net/docs/weapons-armour/close-combat), Fist, Strike Last, Serpent Staff; [pistols](https://mordheimer.net/docs/weapons-armour/blackpowder), Hand-to-hand. These clarify locators; they are not a substitute for available originals. |
| D | [Permanent rulings](../../../decisions/design-rulings.md), Duel engine: Strike Last/Strongman, shared-tier Initiative, player turns, equipment projection, immediate rescue and suppression minimum per warrior. |
| P | [Shifty proposal](T13-shifty.md#modular-contract-submitted-for-review), [T13 contracts](T13-contracts.md), [eligibility architecture](../../../reference/eligibility.md), [implementation procedure](../../../guides/implement-and-verify-rules.md). |

H expressly gives a bonus attack when charged and assigns Strike First to that
attack. The surrounding skills are choices; the wording supplies no automatic
Elder grant, battle-wide usage limit, pistol-allocation algorithm, suppression
minimum, tie-reuse algorithm or explicit replacement priority.

C/E resolve equal first-strike tiers by Initiative, and standing up imposes
Strike Last. C makes Frenzy double the Attacks characteristic; fists have a
one-attack cap, and double-handed weapons always strike last. Pistol hand-to-hand
shots have their own limits. E gives Whipcrack its own bonus, not a Shifty
equivalence. D supplies the already-adopted orchestration interpretations.

Canonical target: `halfling-elder--shifty` in
`sources/knowledge/bands/mordheim/halflings-mic/special-rules.yaml:628`.
It currently has `grant: profile`, `scope: LATER`, `implemented: NO`, a null
binding and all four Heroes in `applies_to.profile_ids` (Elder, Cook, Thief and
Youths). Coordinator correction, 2026-10-02: the previous "only Elder" statement
was inaccurate at both HEAD and the examined working tree, as independently
verified in [FIND-1](T13-shifty-independent-review.md#10-implementation-findings-decision-independent).
The profile grant and missing `kind: warband_skill` do not match the selectable
source; the legacy rule ID does not establish an Elder-only recipient restriction.
Source skill access includes Elder, Cook, Thief and Youths;
current canonical profiles also retain Special access and Youths as Heroes.
Promoted Halfling henchmen need their own advancement/recipient evidence;
neither every band member nor the Ogre gains Shifty automatically.

`origin.json` retains the ledger row:
`sources/2A/bands/mordheim/halflings-mic/special-rules.yaml#halfling-elder--shifty#unimplemented.halflings-mic.special.shifty`.
Its reviewed-text hash is
`5210bbdc9ca742db15bd81d63dc709ae3ad2227079c5cc1a74b22b08da0a51fb`.
The row has no numbered source question; F003/F005 already own the review
barriers. No competing question ledger is created.

## Decision table

Recommendations are submitted for human review, not accepted by this dossier.

| Point | Explicit / general authority | Current project interpretation | Alternative / observable consequence | Recommendation |
| --- | --- | --- | --- | --- |
| Grant and recipients | H chosen skills; T skill table. | Inject pending `skill.shifty`; canonical selection remains rejected. Current recipient IDs already cover four Heroes. | Automatic profile grant loses the source's choice; missing selectable kind/binding/status prevents supported activation. | Correct grant/access later through the shared eligibility path and reviewed canonical binding; no recipient widening or ID rename follows merely from the Elder prefix. |
| Activation, count, duration | H grants one attack on being charged. | Opponent's initial charge flag triggers one bonus, independently of turn ownership; only the initial charge phase is represented. | Own charge alone could incorrectly activate it; repeating every combat phase invents charges. | Keep current trigger. No once-per-battle cap or multi-charger generalization is inferred; future charge inputs must permit their own new events. |
| Only the bonus strikes first | H identifies the extra attack; C/E shared-tier order. | Split bonus from ordinary count; compare Initiative within Strike First; ordinary pool retains priority. | Promote the entire pool, or place the bonus above every charger regardless of Initiative. | Keep current split and general priority. Source is sufficient; mutations detect whole-pool promotion. |
| Strike Last / standing up / fists | C/D provide explicit restrictions and Strongman exception. | Negative priority is retained; Strongman removes eligible weapon penalty; fist cap keeps one attack, using bonus timing. | Shifty overrides all penalties, or grants a second bare-fist attack. | Retain penalties and cap. Choosing the surviving capped attack's bonus timing is a narrow project composition, not printed Shifty text. |
| Frenzy and generic reductions | C characteristic doubling; D minimum per warrior; H has no reduction algorithm. | Add bonus after Frenzy, before generic count reduction. Generic reduction preferentially leaves the bonus; targeted hand suppression may consume it, once across events. | Double the bonus; protect it from every reduction; retain an ordinary attack instead. | **S1:** retain current count/suppression composition, but source-specific “miss first attack” or zero-attack rules must keep their own semantics. |
| Weapon nomination | H does not nominate a hand; P projects an actual melee weapon before timing resolution. | Distinct usable melee hands require one decision; preserve clean/poisoned weapon and hand slot. Pistol plus melee uses melee. | Default always to main, choose after observing dice, or create an extra pistol shot. | **S2:** retain early melee nomination and reject extra ammunition; do not invent a fist while weapons remain. |
| Pistol-only loadout | C limits pistol attacks; H does not settle additional skill attacks with no nominated melee hand. Halfling Thief can access pistols. | Explicit ValueError, no simulated result. | Nominate an actually carried dagger/other melee weapon; waive the bonus; allocate a permitted pistol attack to bonus timing. These need a fuller allocation contract. | **S2:** retain the explicit restriction for this pilot; do not declare the tabletop skill unavailable with pistols. Coordinate future allocation with F005/F026. |
| Ties and Whipcrack | C/E establish warrior order; E grants a distinct whip bonus. | Reuse an existing equal-tier/equal-Initiative warrior tie for Shifty and Whipcrack. Do not redraw for each timed event. | Repeated ties can let events from the same warrior interleave differently. | **S3:** accept tie coherence per tier/Initiative; retain both separately earned bonuses. This does not establish canonical whip access. |
| Whole-pool replacements | T Serpent Staff replaces normal attacks/parries; D gives its existing projection. H does not define “normal” versus a skill bonus here. | Chosen Staff power removes Shifty; declining retains it. Single bonus does not repeat Bull Charge, Body Slam, Anvil Head or natural extra attacks. | Skill bonus survives Staff replacement, or duplicates a replacement/extra list. | **S4:** include Shifty in the chosen whole-pool replacement; preserve a single ordinary bonus otherwise. Synthetic replacement fixtures are not legal-loadout certification. |
| State, resources, removal | C/D ordinary combat state and immediate rescue. | Real pool/attack pipeline shares Charm/parries/criticals/resources; non-standing or burning warrior cannot attack; removal stops later pools. | Reset defenses for the bonus or resolve attacks after removal. | Retain current stateful contract; focused cases and public replay demonstrate the tested paths. |
| Weapon loss between events | D stateful equipment projection. | Trap Blade can break the bonus weapon; later ordinary hits use surviving equipment/unarmed fallback and lose a vanished second-weapon attack. Already prepared same-pool hits retain snapshot. | Keep using the broken weapon or invent another off-hand attack. | Retain current behavior; do not imply a general arbitrary re-equipping interface. |

## Representative strict cases and test mapping

All custom tagged compositions are fixtures, not canonical eligibility claims.
Unless shown otherwise every hit below is 1 (miss), no other dice or decisions
are permitted. Prefixes are full real engine request roles under `round.0`.

| Case | Ordered inputs | Derived expectation / existing test |
| --- | --- | --- |
| Charged I5 Shifty versus I3 charger | `first.shifty.attack.0.hit`, `second.attack.0.hit`, `first.attack.0.hit` | Three attacks; only bonus before charger. `test_only_bonus_precedes_charger_and_ordinary_attacks` also reverses sides. |
| Faster charger / equal-tier tie | I3 Shifty versus I5 charger: second, first.shifty, first. Equal I uses `first.shifty-priority-tie=1` or 6. | Initiative/tie controls bonus order; no privileged tier above charger. Faster-charger and explicit-tie tests. |
| No charge / own charge / absent skill / later phase | No bonus role allowed; later phase requests only ordinary hits. | Two ordinary attacks; no invented charge or repeated bonus. Activation/absence/expiry tests. |
| Frenzy A2 | Bonus miss, charger miss, four ordinary misses. | Five attacks by Shifty owner, not six. `test_frenzy_does_not_double_separate_bonus`. |
| Double-handed / stood up / Strongman | Penalty: second, first.shifty, first. Strongman: first.shifty, second, first. | Penalties retained and explicit exception honored. Strike Last, standing-up and Strongman tests. |
| Fists A3 | first.shifty, second | One total attack by fist user; bonus timing retained. `test_unarmed_one_attack_cap_is_preserved_with_bonus_priority`. |
| Weapon decision | `first.shifty.main-weapon=true/false` before hits; off-hand fixture has +1 hit modifier. | Bonus target changes 4/3; ordinary targets remain 4,3. `test_bonus_weapon_choice_is_separate_from_ordinary_allocation`. |
| Mixed pistol/melee / pistol only | Mixed: axe bonus hit4/wound3 fails, ordinary pistol hit4/wound3 succeeds; pistol only raises. | No extra S4 shot; explicit unresolved-allocation error. Mixed-pistol and two pistol-only tests. |
| Generic reduction / hand suppression | Incoming -1 leaves bonus; Kusara hit5 followed by failed wound removes nominated-hand bonus where eligible. | Reduction spent once, whole-warrior minimum retained. Incoming-count and main/off-hand suppression tests. |
| Charm / removal | Bonus hit4, Charm6, charger miss, ordinary hit4/wound1. Lethal bonus hit4/wound4/injury5. | Charm stays spent; lethal bonus stops subsequent dice. Charm, bonus-removal and charger-removal tests. |
| Whip tie / Staff mode | One whip tie reused; Staff choice true gives one replacement attack, false retains Shifty plus normal attack. | No extra tie or duplicated replacement. Whip-tie, distinct-whip-bonus and Staff accept/decline tests. |
| Trap Blade | Bonus hit4/parry5/trap4; charger miss; ordinary hit4/wound4. | Broken main hand replaced before ordinary hit; surviving off-hand variant loses extra allocation. Both Trap Blade tests. |
| Canonical boundary / public replay | Normal Elder compilation; selected Shifty rejected. Injected replay bonus hit4/wound4/injury5. | Pending grant remains absent; actual modular replay yields first winner, one round, W(1,0), conditions(standing,OUT). Canonical and public-replay tests. |

The isolated `reproducer.py` additionally combines pending Shifty and Spectral
Touch tags on a mace fixture: bonus natural hit6, ordinary wound1, charger miss,
ordinary-owner miss. Expected/observed: three outcomes, bonus damage1, defender
W3→W2. This checks the shared pool's physical-six transport and continuation,
not a legal Halfling/Spirit Host composition. No Rapier/Barrage is involved and
this does not prove the unimplemented accepted R4 repair.

## Real consumer trace and findings

Locations refer to the captured tree, under
`packages/python/combat-engine/mordheim_combat/` unless stated otherwise.

- `modular/rounds.py:36` is reached by both production duel functions in
  `modular/duel.py`, scenario/integration adapters and public modular replay.
  Explicit context preparation binds charge direction independently of turn.
- `rounds.py:161–190` detects charge/tag, adds after the existing count operator,
  applies combined reductions and removes unavailable attacks. `phases.py:115`
  supplies existing priority; `phases.py:176` supplies ordinary attack counts.
- `rounds.py:219–259` nominates the weapon, computes bonus priority and inserts
  one timed event, reusing warrior ties. `select_shifty_weapon` at line 326
  retains original hand and clean weapon while clearing off-hand/extra lists.
- `rounds.py:261–307` resolves actual stateful pools. `single_bonus` in
  `modular/pools.py:160–205,341` prevents repeating whole-pool replacement,
  charge expansion and natural-extra lists. Shared hit defenses, attack
  resolution and aftermath are executed normally, not reimplemented.
- Broken equipment is projected before later ordinary pools; per-warrior
  suppression minimum and pending hand bookkeeping span timed events.
  Conditions/resources travel through actual immutable fighter states.
- `StrictDice` / `StrictDecisions` validate ordered keys, values, die sizes and
  full consumption. Both negative mutations were detected: remove Shifty tag;
  incorrectly raise the whole ordinary pool's priority. They act in isolated
  fixture/process memory, not by editing shared sources.

**No new unambiguous engine defect was reproduced in this pilot's checked
contract.** Known canonical grant/recipient and pistol-allocation deficiencies
remain F004/F005. They are not repaired by the passing mechanism tests.

Evidence gaps and narrowly routed future work:

1. Canonical selectable binding/access must cover actual eligible recipients
   and absence controls. Correct `grant: profile`/missing selectable representation
   through reviewed sources and shared eligibility; retain supported-effect
   refusal separately from legality. This review does not certify extraction.
2. Pistol-only ValueError is an implementation limitation, not a printed ban.
   An actually carried dagger is an alternative allocation input, not equivalent
   to fabricating an unarmed attack. F005/F026 retain source-backed allocation,
   ammunition and hand-to-hand proof requirements.
3. Generic reductions do not prove every named reduction. H's Crude Belch says
   to miss the first attack even if there is only one; the generic minimum-one
   count fixture cannot certify that clause. Its future source-specific
   implementation must target the appropriate timed attack, potentially zero.
4. No source-linked executable Shifty specification or optimized consumer was
   located. Shared tests prove selected compositions, not all save/reaction,
   weapon-specific priority or replacement interactions. Tests check clean-hand
   transport partly by inspection; poisoned-hand behavior still needs an exact
   source-linked case if included in canonical activation.
5. A future multiple-opponent or later-charge context needs its own recipient,
   charge-event and count contract. Both charged flags in a two-fighter fixture
   do not simulate several chargers and imply no once-per-battle limit.

## Commands and evidence

From the repository root, Python 3.10 with `PYTHONDONTWRITEBYTECODE=1`:

```powershell
python -X utf8 -m pytest tests/python/combat/modular/test_shifty.py tests/python/combat/modular/test_spectral_touch.py -q -p no:cacheprovider --tb=short --junitxml=build/cache/t13-parallel/shifty-review/focused.xml
python -X utf8 build/cache/t13-parallel/shifty-review/reproducer.py
python -X utf8 -m pytest tests/python/architecture/test_documentation.py -q -p no:cacheprovider --junitxml=build/cache/t13-parallel/shifty-review/documentation.xml
```

- Focused: **93 passed** (44 Shifty + 49 Spectral Touch), no errors/failures/
  skips, exit0, 15.41s. Real XML, log and exit code are retained.
- Isolated composition reproducer: exit0; exact requests and results retained
  in `reproducer.json` / `.log`. No shared-source mutation or temporary edit.
- Documentation and final input checks are recorded in `final.json` after
  this dossier is complete. `commands.json` retains reproducible test commands.
- Source manifest and copied original core/errata PDFs are in own evidence;
  SHA256s: core `3e52536563ff3d67885278a298b66242e391fad2bb35f968cc6918e2de205b4c`,
  errata `7ed58b766c9539ba78e4ef502b43c775b764483a58e59fd7725075ff5dbd336b`.
- No wider suite was justified by a product-code change. No 211-test reuse,
  broad eligibility certification, complete semantic/parity/coverage gate,
  native build or optimized Shifty support is claimed. The 49 Spectral Touch
  tests still encode pre-repair Barrage behavior despite human R4 acceptance.

## Human decision package and follow-up status

Established source/general rules above require no new factual decision.
The following table retains the submitted review wording. The user accepted
all four recommendations on 2026-10-02, with the boundaries recorded below:

| ID | Decision to review | Recommendation |
| --- | --- | --- |
| S1 | Add after Frenzy and before generic reductions; retain bonus timing for the surviving fist-capped attack; consume hand suppression once across events. | Accept this composition, with source-specific first-attack/zero-attack exceptions preserved. |
| S2 | Nominate a usable melee hand before dice; mixed pistol/melee uses melee; keep an explicit pistol-only limitation pending an actual carried-weapon/allocation contract. | Accept the pilot restriction; do not interpret it as a tabletop prohibition or close F005/F026. |
| S3 | Reuse warrior order for equal priority/Initiative events, including Whipcrack, while retaining each distinct bonus. | Accept; do not redraw ties per event. |
| S4 | Active Serpent Staff mode replaces the Shifty bonus as well as normal attacks; declining retains it; single bonus does not repeat other pool replacements/extra lists. | Accept, with source-specific legal-loadout review still required. |

F003 is **resolved for the reviewed modular contract** after human acceptance.
F004 remains **open** for canonical activation/specifications and F006 stays
**blocked** pending that source-linked contract and optimized execution.
F005/F026 stay **blocked** by pistol-only/allocation semantics;
accepting S2's interim limitation does not resolve the full allocation question.
F035 remains **open**. Current status, 2026-10-02: Spectral Touch F007 is resolved
for its independently accepted modular repair; its activation/ports remain
separate. No unrelated follow-up is closed by this Shifty review.

After a human answer, record its exact scope in the authorized coordination
documents. Reserve any necessary correction and source-linked cases separately;
do not activate canonical Shifty or start backend ports on this dossier alone.

## Independent review integrated by coordinator — 2026-10-02

The [external review](T13-shifty-independent-review.md) is accepted as an
evidence-backed human decision package, not acceptance of S1–S4 or closure of
F003. Its original report and evidence remain unchanged. The coordinator checked
all 19 manifest pairs and the incoming report hash, independently parsed current
recipient/grant/binding facts, and reproduced 101 focused passes plus all 12
isolated probes. Full observations equal the retained results; explicit assertions
check poison direction, shared parry, minimum-one, single-bonus gates, pre-roll
pistol refusal, nomination mutation, tie reuse and Staff accept/decline.
Evidence: `build/cache/t13-parallel/shifty-coordinator-review/`.

The poisoned-hand evidence gap above is now covered for the tested Spider
Spittle compositions; maintained regressions are routed to F060. The generic
minimum-one clamp remains correct for its own contract and cannot certify the
Halfling Crude Belch first-attack loss, routed to F061. That variant is distinct
from other similarly named source rules. F004 records the corrected four-Hero
framing. At integration F003 still required explicit S1–S4 acceptance; the
subsequent user decision is recorded below.
No canonical activation, optimized support, broad gate or F035 certificate is
created by these checks.

## Human acceptance — 2026-10-02

The user replied **"la acepto"** to the coordinator's explicit S1–S4 package,
including the stated limits. All four recommendations in the
[independent review §11](T13-shifty-independent-review.md#11-decisions-ready-for-human-acceptance)
are accepted: count/one-survivor/suppression composition; early carried-melee
nomination with the provisional pistol-only refusal; a single pair-order tie
decision retaining distinct bonuses; and Staff/single-bonus replacement scope.
The complete durable contract lives in
[design rulings](../../../decisions/design-rulings.md#shifty-s1s4).

F003 is resolved at the reviewed modular boundary. The 19 incoming manifest
pairs/report hash were rechecked unchanged; the coordinator's retained 101 focal
passes and 12 explicit probe assertions are reusable without a code change.
Evidence: `build/cache/t13-parallel/shifty-coordinator-review/acceptance-basis.json`
and `human-acceptance.json`. The original external report remains unchanged as
pre-acceptance evidence.

F004's canonical grant/kind/binding and source-linked specifications remain
unimplemented; relevant F035 evidence precedes repairs. F005/F026's full pistol
allocation, F006's optimized execution, F060's maintained poison witnesses and
F061's source-specific Halfling Crude Belch implementation remain separate.
No canonical promotion, source pin edit, engine/test change, new agent, commit
or push is authorized or performed by recording this acceptance.
