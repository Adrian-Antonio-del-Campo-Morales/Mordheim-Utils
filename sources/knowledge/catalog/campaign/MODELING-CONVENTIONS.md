# Convenciones de modelado de campaña

## Efectos de heridas

Los efectos son operaciones tipadas, no texto libre ni estado de campaña.

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

`condition_id` debe existir como condición canónica antes de usarse. La
condición contiene la regla persistente; el efecto solo la aplica.

Una subtabla usa `resolution.type: roll_table`, con `dice` y `branches`. Cada
rama tiene `id`, `when` (intervalo inclusivo) y sus propios `effects`.

## Resultados de avances

`advancement_tables` describe el resultado del 2D6, no el umbral de experiencia.
Un `result` usa estas formas:

```yaml
# Aumento directo.
type: characteristic_increase
characteristic: weapon_skill
amount: 1

# Elección.
type: choose_one
options:
- { type: characteristic_increase, characteristic: weapon_skill, amount: 1 }
- { type: characteristic_increase, characteristic: ballistic_skill, amount: 1 }

# Subtirada.
type: roll_table
dice: { count: 1, sides: 6 }
branches:
- when: { min: 1, max: 3 }
  result: { type: characteristic_increase, characteristic: strength, amount: 1 }
- when: { min: 4, max: 6 }
  result: { type: characteristic_increase, characteristic: attacks, amount: 1 }

# Habilidad o hechizo, cuando proceda.
type: choose_one
options:
- { type: choose_skill, source: hero_skill_access }
- { type: generate_spell, source: wizard_spell_list, when: subject_is_wizard }
```

`Lad's Got Talent` usa:

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

## Test de rareza

La regla recibe el objeto solicitado como contexto y lee su rareza del Trading
Post; no repite `Rare N` en la regla.

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

Un Hero fuera de combate no es `eligible_hero`. Los objetos `common` no usan
este test.

## Procedimientos de exploración

`follow_up` es un árbol con `sequence`, `roll_table`, `characteristic_test`,
`choose_one`, `conditional` y `grant`.

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

Para D3/D6: `{ kind: dice, dice: { count: 1, sides: 3 } }` o `sides: 6`.
Para objetos: `items: [{ item_id: sword, quantity: { kind: fixed, value: 1 } }]`.

Las ramas por banda usan `conditional`; no duplican el resultado:

```yaml
type: conditional
cases:
- when: { field: context.band_id, operator: equals, value: skaven-eshin }
  then: [...]
default: [...]
```

`bind` crea una variable local del procedimiento. Tiradas, opciones y
recompensas aplicadas se guardan solo en el estado externo de campaña.
