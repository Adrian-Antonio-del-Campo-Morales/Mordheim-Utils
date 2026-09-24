# Campaign modelling conventions

## Injury effects

Effects are typed operations, not free text or campaign state.

```yaml
- type: warrior.add_condition
  condition_id: campaign.condition.frenzy
  duration: permanent
- type: roster.remove_warrior
  reason: dead
- type: equipment.disposition
  scope: carried_by_subject
  disposition: lost
- type: prisoner.create
  captive: subject
  captor: opposing_warband
  equipment_policy: retained_until_resolution
- type: warrior.battle_start_check
  check_id: campaign.check.old-battle-wound
  dice: { count: 1, sides: 6 }
  failure_when: { min: 1, max: 1 }
  on_failure:
  - type: warrior.miss_games
    games: { kind: fixed, value: 1 }
- type: relationship.add_hatred
  target_selector: inflicting_warrior_or_enemy_leader_if_henchman
  duration: permanent
- type: encounter.trigger
  encounter_id: campaign.encounter.sold-to-the-pits
  subject: warrior
- type: reward.grant
  recipient: subject
  resources:
    gold_crowns: { kind: fixed, value: 50 }
    experience: { kind: fixed, value: 2 }
```

`condition_id` must exist as a canonical condition before being used. The
condition holds the persistent rule; the effect only applies it.

A sub-table uses `resolution.type: roll_table`, with `dice` and `branches`. Each
branch has `id`, `when` (inclusive interval) and its own `effects`.

## Advancement results

`advancement_tables` describes the outcome of the 2D6, not the experience
threshold. A `result` uses these forms:

```yaml
# Direct increase.
type: characteristic_increase
characteristic: weapon_skill
amount: 1

# Choice.
type: choose_one
options:
- { type: characteristic_increase, characteristic: weapon_skill, amount: 1 }
- { type: characteristic_increase, characteristic: ballistic_skill, amount: 1 }

# Sub-roll.
type: roll_table
dice: { count: 1, sides: 6 }
branches:
- when: { min: 1, max: 3 }
  result: { type: characteristic_increase, characteristic: strength, amount: 1 }
- when: { min: 4, max: 6 }
  result: { type: characteristic_increase, characteristic: attacks, amount: 1 }

# Skill or spell, where applicable.
type: choose_one
options:
- { type: choose_skill, source: hero_skill_access }
- { type: generate_spell, source: wizard_spell_list, when: subject_is_wizard }
```

`Lad's Got Talent` uses:

```yaml
type: promote_henchman
promotion: lads_got_talent
on_maximum_heroes: reroll_current_advance
preserve: [henchman_type, experience, characteristic_increases]
skill_lists: { choose: 2, source: warband_hero_skill_access }
immediate_follow_up: campaign.advance.hero
remaining_group:
  reroll_current_advance_excluding: [lads_got_talent]
```

## Rarity test

The rule receives the requested item as context and reads its rarity from the
Trading Post; it does not repeat `Rare N` in the rule.

```yaml
id: campaign.trading.rarity-test
actor: eligible_hero
attempt_limit: one_per_actor
dice: { count: 2, sides: 6 }
target_rarity:
  source: catalog_field
  catalog: campaign/trading-post
  item_id: $requested_item_id
  field: availability.rarity
success_when: greater_than_or_equal_to_target
units_per_success: 1
```

A Hero out of action is not an `eligible_hero`. `common` items do not use this
test.

## Exploration procedures

`follow_up` is a tree with `sequence`, `roll_table`, `characteristic_test`,
`choose_one`, `conditional` and `grant`.

```yaml
follow_up:
  type: sequence
  steps:
  - type: choose_one
    bind: searching_hero
    from: eligible_heroes
  - type: characteristic_test
    actor: $searching_hero
    characteristic: toughness
    dice: { count: 1, sides: 6 }
    success_when: roll_less_than_or_equal_to_characteristic
    on_success:
    - type: grant
      recipient: warband
      resources:
        wyrdstone_fragments: { kind: fixed, value: 1 }
    on_failure:
    - type: warrior.miss_games
      subject: $searching_hero
      games: { kind: fixed, value: 1 }
```

For D3/D6: `{ kind: dice, dice: { count: 1, sides: 3 } }` or `sides: 6`.
For items: `items: [{ item_id: sword, quantity: { kind: fixed, value: 1 } }]`.

Per-warband branches use `conditional`; they do not duplicate the outcome:

```yaml
type: conditional
cases:
- when: { field: context.band_id, operator: equals, value: skaven-eshin }
  then: [...]
default: [...]
```

`bind` creates a local variable of the procedure. Rolls, choices and applied
rewards are saved only in the external campaign state.
