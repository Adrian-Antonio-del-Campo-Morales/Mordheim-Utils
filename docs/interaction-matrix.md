# Interaction matrix

Reference for how every required interaction pair of the verification gate is
closed — the shared-concept map of the duel rules, the case patterns each
cluster uses, and the reviewed decisions recorded as policy overrides.

## Status (2026-09-04) — implemented, gate green

- **217/217 required interactions covered, 0 required pending**;
  `semantic_complete=True`. See the audit summary in
  [`TODO.md`](../TODO.md).
- **10 pairs** closed as `illegal` overrides in
  [`tests/specs/interaction-policy.yaml`](../tests/specs/interaction-policy.yaml)
  (body-armour × body-armour, section “Cross-cutting notes” below).
- **190 pairs** closed by authored pair specs under
  [`tests/specs/semantic/interactions/`](../tests/specs/semantic/interactions/)
  (the 9 cluster files named in the cross-cutting notes; 7 earlier
  interaction files remain). The sections A–I below are the design basis
  each cluster spec was generated from — operations, context knobs, fighter
  fields, dice keys and observables grounded in how the bindings were
  already exercised.
- Vectorized/native certification: `parity` reports **0 divergences** over
  3724 specification rows; the corpus exposed and helped fix a real
  vectorized-engine defect (an extra dice draw for automatic wounds shifted
  the ward-save roll stream).

Generated 2026-09-03 from the semantic corpus: every proposal is grounded in
the operations, context knobs, fighter fields, dice keys and observables that
the involved bindings already exercise in their own single-binding specs
(stats in the per-cluster sections). Exact numeric expectations are NOT
invented here: each case value was authored from the written rules and
confirmed against the modular engine.

Sources of truth: `outputs/audit/required-pending-interactions.csv` (the 200
pairs, by pair), `outputs/audit/pending-pairs-adapter-coverage.csv` (pair →
operations), `src/mordheim_combat_lab/verification/parity/_specifications.py`
(SPECIFICATION_ADAPTERS).

## Authoring recipe (same for every cluster)

Each interaction spec is one YAML object inside
`tests/specs/semantic/interactions/*.yaml` (batch by cluster):

- `category: interaction` + `scope_digest` (current runtime-scope fingerprint)
  + `sources:` with the exact current digests of the two binding targets.
- `bindings:` = the two binding JSON strings (kind+id+parameters).
- `interpretation:` independent statement of the composed rule.
- Cases must cover roles `composition` AND `boundary`
  (REQUIRED_CASES["interaction"]). A behavioural case asserts `result.*` /
  `context.*`; dice are strict (unexpected/unconsumed rolls fail).
- ≥1 `mutation` on a passing baseline case whose path change must be
  *detected* (otherwise the spec fails as vacuous).
- One spec per pair — 200 pairs = ~200 spec objects (see triage note below
  for candidates that should instead be policy overrides).
- Verify locally: `python tools/mordheim-utils.py verify` (pair moves from
  `pending` to `tested`) and `python tools/mordheim-utils.py audit`.

Vectorized side: every operation used below already has a parity adapter (see
each cluster). The single known capability gap is the `priority` adapter's
missing `initiative_floor` (NotImplementedError → PENDING_ADAPTER); avoid that
context knob until it is implemented, or extend `_vector_priority`.

---

## A. Armour family (armour.target 52 + attack.penetration 12 + armour.allowed 11)

Bindings: the 5 body armours (`light/heavy/gromril/ithilmar/no-armour`),
`material.gromril`, weapons `axe/dagger/katar/yambiya`, `vomit-attack`,
`skill.unarmed-fighting`, compiler `bear-hug`.

Observed in their specs: op `armour` dominates (30–18 cases per sub-cluster);
`strength`/`attacks` minor; NO context knobs used; fields
`attacker.main_weapon_id` + `defender.armour_id` (and
`attacker.main_material_id`, `attacker.skill_ids`); expect
`result.target` / `result.saved` / `result.eligible` (+ compiled
`defender.armour_save`); roll key `armour`.

Proposal per pair (weapon/material vs armour — the real composition axis):

- **operation: `armour`**; attacker wields the weapon (axe/katar/yambiya/
  dagger/vomit/unarmed-fist) or applies `main_material_id: material.gromril`;
  defender wears the armour.
- Base case (`composition`): assert `result.target` and `result.saved`
  including the S-based modifier (vary `attacker.characteristics.strength`
  like existing `strength-modifier` cases) and the armour-penetration
  interplay. Roll key `armour`.
- Boundary cases: penetration + strength modifier pushing target past 6 →
  `result.eligible: false`, `result.saved: false` (pattern exists in
  `weapon.axe` spec `save-worse-than-six`); weapon vs armour with no armour
  allowed (vomit-attack/bear-hug ignore-armour flags → `armour.allowed`).
- Mutations: `attacker.main_weapon.armour_penetration: 0`,
  `attacker.main_weapon.target_armour_bonus: 0`, `defender.armour_save: ±1`,
  remove `material.gromril` from `attacker.main_material_id`.
- Adapters: `vectorized.armour_targets` (and `off_hand_armour` when an
  off-hand applies).

Triage (executed 2026-09-03, see `outputs/audit/interaction-triage.csv`): the
10 body-armour × body-armour pairs (all C(5,2) among
light/heavy/gromril/ithilmar/no-armour) are **overrides** (`status: illegal`)
— `FighterBuild` has a single `armour_id` slot and `armour.no-armour` is the
empty default, so they can never be granted together and opposing fighters'
armour saves resolve disjointly. Weapon/material × armour and
`no-armour × weapon/unarmed` pairs stay **specs** (cross-side reachable).
`helmet × cooking-pot-helmet` COMPILES (compile probe) → spec, but flag the
stacking ambiguity (both convert Stunned→Knocked Down) for a ruling while
authoring.

## B. Injury-condition family (injury.condition 31 + injury.total 22)

Bindings: `combat-injury-states`, `combat-critical-hits`, helmets
(`defence.helmet`, `cooking-pot-helmet`), injury skills (`hard-to-kill`,
`ignore-pain`, `jump-up`, `thick-skull`, `head-crusher`, `knife-fighting`,
`strike-to-injure`, `monstrous`), materials (`dark-elf-blade`), weapons
(`mace`, `stone-axe`).

Observed: ops `injury` (157+85), `attack` (39), `injury_reaction` (28+8),
`stun_reaction` (18); fields `defender.skill_ids` / `defender.defence_ids` /
`attacker.main_weapon_id`; expect `result.condition`,
`result.reaction.attempted`, `result.threshold`, `result.defender.condition`;
rolls `test.injury`, `test.thick-skull`, `test.helmet`, and the attack
sequence `test.attack.N.hit/wound` + `test.injury.N`. Context knobs: none
(condition flows through state, `rounds` only in recovery scenarios).

Proposals per sub-family:

1. **Helmet/condition modifier × skill** (helmet×thick-skull etc.):
   `operation: injury` with `defender.defence_ids: [defence.helmet]` +
   `defender.skill_ids: [skill.X]`; assert the resulting
   `result.condition` (composition) and a face that does NOT trigger the
   skill (`boundary`); mutation: `defender.helmet_save: false`-style path
   or skill tag removal.
2. **Weapon injury modifier × skill** (mace/stone-axe/head-crusher ×
   thick-skull/hard-to-kill/ignore-pain/jump-up): use the full
   `attack` flow (`test.attack.0.hit/wound` + `test.injury.0`) so weapon
   concussion/critical modifiers feed the injury table, then assert the
   reaction (`injury_reaction`) — the thick-skull × mace/stone-axe shapes
   are already proven for thick-skull in
   `interactions/thick-skull-injury.yaml`; mirror them for
   hard-to-kill/ignore-pain/jump-up and for head-crusher promotions.
3. **Damage-total effects** (dark-elf-blade, strike-to-injure,
   knife-fighting, critical-hits × injury states): `operation: injury` at
   `injury.total` level asserting `result.threshold` /
   `result.defender.condition`, boundary at total below/above the effect
   requirement.
- Adapters: `injury` → injury_conditions; `injury_reaction` →
  injury_conditions+stun_reaction_outcomes; `attack` → _resolve_weapon.

## C. Damage-mitigation family (damage.unsaved 26)

Bindings: `trained-bear--bear-hug` (compiler), `combat-injury-states`,
`enchanted-skins`, `poison.bloodroot`, `elven-agility`, `regeneration`,
`regeneration-5-plus`, `step-aside`.

Observed: ops `attack` (41), `special_save` (23), `wound`, `injury`; context
`hit_roll`; fields `attacker.main_weapon_id` + `attacker.main_poison_id`,
`defender.skill_ids` / `defender.preparation_ids`; expect `result.damage`,
`result.defender.condition`, `result.saved`, `result.regeneration_roll`,
`result.target`; rolls `test.hit`, `test.wound`, `test.injury.0/.1`,
`special.ward`.

Proposal:

- Damage-source × mitigation (bloodroot/enchanted-skins/bear-hug ×
  regeneration/regeneration-5-plus/step-aside/elven-agility):
  `operation: attack` (or `special_save`) with the damage source on the
  attacker (`main_poison_id`, weapon or bear-hug special rule) and the
  mitigation skill on the defender; assert whether the unsaved damage is
  prevented (`result.saved`, `result.regeneration_roll`,
  `result.defender.condition`), boundary at the save threshold.
- Bear-hug × mitigation: check whether the compiler's damage is
  “unsaved” at all before regen/step-aside applies (likely the true
  interaction ruling); composition case via `bear_hug` +
  `special_save`-capable op.
- Mutations: `defender.global_effects.regeneration: false`,
  defender save value ±1, remove the poison from `attacker.main_poison_id`.
- Adapter: `special_save` → special_save_targets; `bear_hug` →
  bear_hug_wins; `attack` → _resolve_weapon.

## D. Parry family (state.parries 15 + hit.success 2)

Bindings: `combat-parry`, `weapon.sword`, `shield-mastery`, `axe-master`,
`crushing-blow`, `defensive-stance` (+ `vomit-attack`, bear-hug on
hit.success).

Observed: op `parry` (22+6); context knob `hit_roll`; fields
`defender.main_weapon_id` (31) / `defender.off_hand_id` (10) /
`defender.skill_ids` (15) and `attacker.main_weapon_id`;
expect `result.attempted`, `result.blocked`,
`result.defender.parries_remaining`, `result.attacks.N.parried`.

Proposal (parry-relevant skills are DEFENDER-side — the defender wields the
parrying weapon):

- `operation: parry`, defender holds sword (+ optional
  `defender.skill_ids: [skill.shield-mastery]` etc.), attacker's hit roll set
  via `rolls: [{key: hit, ...}]` or `hit_roll` context; assert
  `result.blocked`/`result.attempted`; boundary: roll above/below the parry
  requirement, natural 6 not parried, and the “one parry per phase”
  resource (parries_remaining).
- Skill pairs among themselves (shield-mastery×defensive-stance etc.) are
  same-fighter: one spec per pair with both skills on the defender and a
  weapon in hand.
- Attackers that cannot be parried (vomit-attack/bear-hug on hit.success)
  use `operation: attack`/`pool` asserting `result.attacks.N.parried: false`
  via `attacker.main_weapon.cannot_be_parried`.
- Mutations: `defender.main_weapon.parry: false`,
  `defender.global_effects.parry: false`, remove the skill tag.
- Adapter: `parry` → parry_outcomes; `attack` → _resolve_weapon.

## E. Attack-count family (attack.count 15)

Bindings: `combat-two-weapons`, `extra-attack`, `ferocious-charge`,
`red-fury`, `unarmed-fighting`, `vomit-attack`.

Observed: op `attacks` (16; `weapon_attack_count` 4); context `first_round`
and `charging`; fields `attacker.main_weapon_id`, `attacker.off_hand_id`,
`attacker.skill_ids`; expect `result.attacks`, `result.weapons.N.concussion`
(allocation observables), `attacker.off_hand_attacks`; a few `armour`/`wound`
follow-ups.

Proposal:

- `operation: attacks` with context `{charging: true, first_round: true}` +
  `attacker.skill_ids`/`off_hand_id` to compose two weapons × skill bonuses;
  assert `result.attacks` (composition) and the base count without the
  second effect (boundary).
- `weapon_attack_count` for the per-round weapon allocation when two weapons
  differ (which weapon takes the bonus attack).
- Mutations: `attacker.global_effects.attacks_bonus: 0`, remove skill tag,
  remove `attacker.off_hand_id`.
- Adapter: `attacks` → attack_count; `weapon_attack_count` →
  round_weapon_attack_count.

## F. Priority family (priority.tier 10 + state.stood_up 2)

Bindings: `combat-order`, `always-strikes-first`, `lightning-reflexes`,
`strongman`, `double-handed-weapon` (+ `combat-injury-states` for stood_up).

Observed: op `acting_order` (16) and `priority` (1); context knobs
`first_round`, `charging`, `charged`, `stood_up`; fields
`attacker.main_weapon_id`/`attacker.skill_ids`, rarely defender-side; expect
`result.first_acts`, `result.priority`, no dice.

Proposal:

- `operation: acting_order` with both contenders configured on opposite
  sides (attacker vs defender each with their skill/weapon); context picks
  `first_round`, `charging`/`charged`, `stood_up`; assert `result.first_acts`
  (composition) and the same duel with one effect removed (boundary).
- Strongman/double-handed-weapon lower initiative: assert ordering inverts
  when combined with always-strikes-first/lightning-reflexes.
- ⚠ `initiative_floor` context must NOT be used until `_vector_priority` is
  extended (currently PENDING_ADAPTER).
- Mutations: remove the skill tag, change
  `attacker.characteristics.initiative`, flip `charging`/`stood_up`.
- Adapter: `acting_order` → vectorized.priority; `priority` →
  vectorized.priority.

## G. Hit-reroll family (hit.reroll 10)

Bindings: `axe-expert`, `blessed-sight`, `crack-shot`, `expert-swordsman`,
`weapons-of-the-north`.

Observed: op `hit` (26) + `characteristic_test` (4); context `first_round`
(18) and `charging` (12), `value` for characteristic tests; fields
`attacker.skill_ids` + `attacker.main_weapon_id`; expect `result.success`,
`result.rerolled`, `result.passed`; rolls `hit`, `hit.reroll`,
`test.characteristic`, `test.characteristic.reroll`.

Proposal: complete reroll clique (5 bindings = 10 pairs) — one spec per pair
with BOTH skills on the same attacker (`attacker.skill_ids`) plus
`main_weapon_id`, exercising `operation: hit` twice: `composition` (miss then
reroll passes, `result.rerolled: true`, `result.success: true`) and
`boundary` (second roll also fails or reroll not granted when a condition is
off, e.g. not charging when the skill requires it). `characteristic_test`
only when a skill is a stat test (blessed-sight), not the default.
Mutations: remove one skill tag → reroll must disappear
(`result.rerolled: false`). Adapter: `hit` → attack-preparation.

## H. Wound-success family (wound.success 2 + wound.roll 1 + state.critical_available 3)

Bindings: `material.dark-steel` × `poison.black-lotus` × `skill.sure-strike`
(wound.success); `combat-critical-hits` × `poison.devil-s-toxin` /
`wolfsbane` / (`wound.roll` on devil-s-toxin).

Observed: op `wound` (53/23/33); context `hit_roll`; fields
`attacker.main_weapon_id`, `attacker.main_poison_id`,
`attacker.main_material_id`, `defender.preparation_ids`; expect
`result.success`, `result.critical`, `result.rerolled`, `result.target`,
`result.attacker.critical_available`; rolls `wound`, `wound.reroll`.

Proposal:

- dark-steel/black-lotus/sure-strike: `operation: wound`, attacker with
  material + poison or skill, rolls `wound`; composition = reroll or
  +-to-wound stacking observable (`result.success`); boundary when the
  second source is absent.
- devil-s-toxin/wolfsbane × combat-critical-hits: the poison grants crits on
  a lower threshold (`state.critical_available`): assert a wound roll at the
  poison threshold is `result.critical: true` only while the poison is on
  (composition) and that without it the same roll is not critical
  (boundary). Rolls `wound`; expect `result.critical`/
  `result.attacker.critical_available`.
- Mutations: remove `main_poison_id`, change poison parameters,
  `attacker.main_weapon.damage`.
- Adapter: `wound` → wound_outcomes.

## I. Small clusters (1–2 pairs each)

- **state.wounds** (`combat-injury-states` × `skill.monstrous`): `operation:
  injury` on a monster with extra Wounds — assert the condition table is
  entered only after all Wounds are lost (composition) and the multi-Wound
  case below threshold (boundary); expect `result.condition` /
  `result.attacker.wounds`.
- **attack.strength** (`unarmed-fighting` × `vomit-attack`): both are weapon
  replacers — compose on the attacker (`attacker.skill_ids` +
  `main_weapon_id: weapon.vomit-attack`), ops `strength`/`attacks`/`armour`;
  the interesting question is which source's Strength/flags win for the
  attack (fixed_strength vs skill bonuses) — ruling likely needed.
- **state.stood_up × combat-order/strongman**: already covered by F's
  acting_order template with `stood_up: true`.

## Cross-cutting notes

1. **Triage result (2026-09-03)**: exactly **10 of the 200 pairs are
   overrides** — the body-armour × body-armour family (single `armour_id`
   slot per `FighterBuild`; `armour.no-armour` is the empty default).
   **Applied** in `tests/specs/interaction-policy.yaml` (each with
   `status: illegal`, risk reasons and construction evidence); classification
   per pair in `outputs/audit/interaction-triage.csv`. Everything else —
   including all bear-hug pairs (cross-side attacker vs defender) and
   `helmet × cooking-pot-helmet` (compiles) — is spec-needed and was closed
   by authored pair specs (190 specs). Bear-hug × mitigation/armour pairs
   are real duel compositions, not illegal combinations.
2. **File layout** (implemented): the authored specs live in
   `tests/specs/semantic/interactions/armour-target.yaml`,
   `injury-conditions.yaml`, `damage-mitigation.yaml`, `parry-skills.yaml`,
   `attack-count.yaml`, `priority-order.yaml`, `hit-rerolls.yaml`,
   `wound-criticals.yaml` and `small-clusters.yaml`; one spec object per
   pair.
3. **Digests**: after any KB text edit, refresh the spec `sources[].digest`
   and `scope_digest` (verify reports the exact mismatch otherwise).
4. Every op proposed has a vectorized adapter; the only blocker is
   `priority` + `initiative_floor` (section F).


## Deep probe of skill×skill and weapon×weapon pairs (2026-09-03)

Follow-up on the 190 spec-needed pairs (`outputs/audit/triage-deep-probe.csv`):

- **35 skill×skill pairs** and **6 weapon×weapon pairs** were compile-probed on
  a single fighter (both skills together; both weapons as main+off and
  off+main). **All COMPILE** — no engine-level mutual exclusion exists.
- Catalogue flags confirm the weapon pairs are all `hands: 1`,
  `off_hand: true` (axe/dagger/katar/yambiya/mace/stone-axe), so
  main+off-hand co-grantability is real, not an artifact.
- Compiler-level exclusivity rules that DO exist do not touch these pairs:
  main-only weapons (`morning-star`, `natural-attacks`, `fist`), no-shield
  mains (`spear`, `broadsword`, `boar-spear`, `squig-prodder`), restricted
  armours (`toughened-leathers`, `ninja-robes`, `wizard-s-robe`,
  `eshin-assassin-robes` × shields), and `Berserker × Ferocious Charge` —
  none of those bindings appear in the 190.
- Remaining boundary: these probes use a generic fighter, so
  profile/warband **skill-list access** disjointness (e.g. a skill only
  learnable by one warband vs another) is not covered; a per-profile access
  scan would be needed to rule that out, but it would only matter for
  same-fighter stacking pairs such as the hit.reroll clique.
