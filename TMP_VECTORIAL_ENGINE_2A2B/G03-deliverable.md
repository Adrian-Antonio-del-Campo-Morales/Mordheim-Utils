# G03 — Operadores y contextos de ataque, defensas y prioridad (entrega)

## Base y alcance de esta entrega

- Repositorio: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK`; HEAD `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más los cambios locales existentes, incluida la base integrada G00+G02 ([G02-deliverable.md](G02-deliverable.md)).
- El encargo G03 abarca 941 cláusulas principales y 309 de apoyo. La entrega tiene dos partes: el **slice inicial** (características perezosas de Inconsistency, Iniciativa ausente y modificador `+1 al impacto` de Guiding Dream) y el **port completo de los contextos modulares** a operadores vectorizados por fila (hit, fuerza, herida, armadura, salvaciones especiales, parada, lesión, ataques y prioridad). Los operadores base ya existían; lo añadido es la capa de cualificadores contextuales que el anexo pide en los puntos 1–4 y 6.
- Archivos de producción permitidos por G03 y usados: `_operators.py`. Test permitido: `test_rule_families_b.py`. No se editó `_types.py`, `_driver.py`, `_attacks.py`, `_equipment.py`, la fachada ni el Cython.
- CSV canónico intacto: SHA-256 `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. No se escribió el registro. No hay commits ni pushes.

## Qué se ha implementado

### 1. Lectura perezosa de características

`characteristic(fighter, state, rows, rng, name)` en `_operators.py`.

- Delega en `mordheim_combat.vectorized._state.require_characteristics` (base G02) y devuelve la columna de `rows` tras la posible tirada.
- Solo tira si el perfil tiene `mechanic.inconsistency` y el bit de esa característica no está fijado para la ronda; las filas fuera de `rows` no consumen dados.
- Mantiene la reutilización dentro de la misma ronda y respeta `random_modifiers`/`torture_strength_loss` del port de G02.
- `name` se valida contra `STAT_ATTRIBUTES` (`WS`, `S`, `T`, `I`, `A`).

Es el punto único que deben usar los operadores y el driver para leer una característica variable. Con un perfil fijo cuesta una lectura de atributo y ningún dado.

### 2. Iniciativa ausente

`effective_initiative(fighter, state)` ahora distingue la ausencia impresa con `state.initiative_missing` (campo de G02):

- Las filas presentes conservan el cálculo anterior (suelo, bonificadores, Crimson Shade, penalización), en `int32`.
- Las filas ausentes devuelven `ABSENT_INITIATIVE = -1_000_000`, un marcador de orden que queda por debajo de cualquier Iniciativa impresa y que **no** recibe bonificadores.
- Dos filas ausentes comparan igual, así que el desempate impreso del llamador decide; una fila impresa siempre gana a una ausente. Es la misma relación que `phases.priority_order` establece con `None` (`-inf`), sin introducir un número de característica.
- El marcador cabe en el cálculo `priority * 100 + initiative` que el driver hace en `int32`.

### 3. Modificador de Guiding Dream

`guiding_dream_hit_modifier(attacker, defender, state, rows)` y el argumento opcional `guiding_dream` de `hit_targets`.

- Solo actúa si el atacante lleva `condition.guiding-dream-target`; si el defensor no es `fighter-kind.hero`, lanza el mismo `ValueError` que `prepare_hit_context`.
- Devuelve `+1` en las filas cuyo `guiding_dream_result` es 2 o 3 y `0` en el resto.
- `hit_targets(..., guiding_dream=modifier)` resta el modificador al objetivo de impacto (un `+1` a impactar es un punto menos en la tirada), antes del `clip` que ya aplica el llamador. El caso de impacto automático contra WS 0 sigue devolviendo 0.

## Archivos y funciones

| Archivo | Cambio |
| --- | --- |
| `packages/python/combat-engine/mordheim_combat/vectorized/_operators.py` | Nuevos `ABSENT_INITIATIVE`, `characteristic`, `guiding_dream_hit_modifier`; `hit_targets` acepta `guiding_dream=`; `effective_initiative` respeta `initiative_missing`. |
| `tests/python/combat/vectorized/test_rule_families_b.py` | Un caso nuevo que cubre los tres comportamientos. |
| `TMP_VECTORIAL_ENGINE_2A2B/G03-deliverable.md` | Este documento. |

## Claves y estado real

Estas tres funcionalidades son contribuciones de apoyo a claves cuyo cierre pertenece a G02/G06; no se propone ningún cambio de estado en el CSV en esta entrega.

| Clave | clause_id | Responsable principal | Contribución G03 | Estado real |
| --- | --- | --- | --- | --- |
| `mechanic/mechanic.guiding-dream` | `whole` | G02 | `+1 al impacto` 2–3 y guardia de Héroe en un operador probado | Implementado en operador; **sin llamada desde `_attacks.py`** (G04) |
| `rule/mordheim/marauders-of-chaos/condemned--inconsistency/profile.random-characteristics` | `whole` | G02 | Accesor `characteristic` para WS/S/T/I/A perezosos | Implementado en operador; **sin llamada desde `_attacks.py`/`_driver.py`** (G04/G06) |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/0/unresolved_references/0/unclassified` | `profile` | G02 | El mismo accesor sirve al perfil variable de Belandysh | Ídem |
| Iniciativa ausente (sin clave propia; hecho de `profile.characteristics` y `phases.priority_order`) | — | G01/G06 | `effective_initiative` con marcador de orden y flag | Integrado en el operador que ya llama el driver; falta la evidencia de paridad de G07 |

Propuesta CSV: **sin cambio** (`numpy: pending`, `native: pending` en las tres filas). La implementación existe, pero la conexión real en el bucle no; marcarlas `implemented` sería inventar soporte.

## Conexiones pendientes y propuestas concretas

### G04 — `_attacks.py`

1. Línea 197: `attacker_ws = attacker_state.weapon_skill[active]` → `attacker_ws = characteristic(attacker, attacker_state, active, rng, "WS")`. Conservar después los bonos de arma/carga.
2. Línea 210: `hit_target = hit_targets(attacker_ws_values, defender_state.weapon_skill[active], guiding_dream=guiding_dream_hit_modifier(attacker, defender, attacker_state, active))`. Guardar la WS defensora en un local y reutilizarlo en las líneas 230 y 236 (impacto automático contra WS 0) para no repetir la lectura.
3. Líneas 170/172: `attacker_state.strength[active]` → `characteristic(attacker, attacker_state, active, rng, "S")`.
4. Línea 227 (Sweep): `defender_state.initiative[active]` → `characteristic(defender, defender_state, active, rng, "I")`.
5. Líneas 466/486/498: `defender_state.toughness[…rows…]` → `characteristic(defender, defender_state, <mismas filas>, rng, "T")`.
6. Líneas 847 y 905–906 (comparaciones de fuerza en parada y agarre): usar `characteristic(..., "S")` para ambos combatientes sobre las filas implicadas.

### G06 — `_driver.py`

1. Antes de `i1, i2 = effective_initiative(...)` (línea ~295), llamar a `_state.require_characteristics(first, state1, active_rows, rng, {"I"})` y lo mismo para el segundo combatiente, si se activa la cadencia perezosa. El marcador de ausencia ya funciona sin cambio de firma.
2. En las llamadas a `attack_count` (línea ~299), pasar `base_attacks=characteristic(attacker, state, active_rows, rng, "A")` para el ataque variable.
3. Al inicializar y refrescar, cambiar a `initialize_fighter(..., lazy_inconsistency=True)` y `refresh_random_characteristics(..., lazy_inconsistency=True)` **solo después** de que (1)–(2) y los puntos de G04 estén conectados.
4. Con eso hecho, el coordinador puede retirar `mechanic.inconsistency` y `mechanic.guiding-dream` de `kernel._PENDING["numpy"]` (nunca de `NATIVE_PENDING`), y solo entonces proponer `implemented` en el CSV.

### Coordinador

- La fachada `vectorized/__init__.py` no reexporta `ABSENT_INITIATIVE`, `characteristic` ni `guiding_dream_hit_modifier` porque no es propiedad de G03. G04/G06 los importan de `_operators`; si se quieren en el espacio histórico, lo aplica el coordinador al integrar.

## Comandos y resultados

```text
python -m pytest tests/python/combat/vectorized/test_rule_families_b.py -q -k lazy_characteristics
  -> 1 passed, 6 deselected

python -m pytest tests/python/combat/vectorized -q -n 8
  -> 98 passed, 14 failed (los 14 son los mismos fallos preexistentes de G02;
     ninguno pasa por los operadores nuevos: catálogo/compilación/gate y la
     aserción de spawn-of-chaos que ya fallaba con el _new_state anterior)

python -m pytest tests/python/combat/test_kernel_plan.py \
  tests/python/combat/vectorized/test_backends.py \
  tests/python/combat/vectorized/test_observations.py -q
  -> 9 passed

# Humo de la ruta admitida:
simulate_duel(DuelRequest(f, f, 20, seed=7), backend="numpy")
  -> DuelResult(first_wins=8, second_wins=12, unresolved=0, simulations=20)   # igual que G00/G02
effective_initiative(absent) -> -1000000; initiative_missing[0] -> True

sha256(clause-contracts.csv) -> b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731
```

Comprobaciones **no** ejecutadas: campaña de paridad G07, rendimiento G08, E2E completo.

## Caso nuevo y justificación

`test_lazy_characteristics_absent_initiative_and_guiding_dream_modifier` en `test_rule_families_b.py`.

Es el único hueco concreto de este slice: los tres comportamientos no tenían comprobante vectorial propio. El caso verifica, con dos filas divergentes:

- la tirada perezosa se limita a la fila pedida, se reutiliza en la misma ronda y no consume dados en la otra fila;
- la Iniciativa ausente devuelve el marcador, ordena por debajo de una impresa y conserva el flag;
- Guiding Dream 2–3 rebaja el objetivo solo en su fila, el resultado 6 no lo rebaja y un defensor no Héroe lanza `ValueError`.

No se añadieron pruebas por cláusula ni se copiaron E2E.

## Límites y trabajo restante

- **Sin integración en el bucle**: por la propiedad de archivos de G03, las llamadas de `_attacks.py` y `_driver.py` quedan como propuestas exactas. Por eso no se retira ninguna entrada de la puerta NumPy y el CSV no propone `implemented`.
- El modificador de Guiding Dream y las lecturas perezosas están implementados y probados como operadores, no como comportamiento observable de `simulate_duel` todavía.
- `ABSENT_INITIATIVE` es un marcador de orden, no una característica impresa: `initiative_missing` sigue siendo la autoridad. La observación de estado de paridad seguirá viendo `0` en la columna numérica frente al `None` modular; definir esa proyección es de G07.
- La guardia de Héroe de Guiding Dream ya existía en `validate_duel_start` (G02) para el inicio del duelo; el operador añade la misma comprobación en el punto de impacto, como el contexto modular.
- No se ha tocado el Cython: `NATIVE_PENDING` conserva su instantánea y el port nativo de estos tres comportamientos no se declara.

## Port completo de los contextos modulares (segunda entrega)

El encargo G03 pide portar los cálculos y cualificadores de los contextos modulares a los operadores, no solo los tres comportamientos del slice inicial. Esta entrega añade a `_operators.py` la capa completa de proyección por fila, reutilizando la tabla canónica de `phases` y sin duplicar reglas:

| Operador vectorizado | Referencia modular | Qué proyecta |
| --- | --- | --- |
| `combined_effect` | `_combined_effect` | Fusión arma+efectos globales, con las tres acometidas corporales que no se fusionan. |
| `weapon_against_opponent` | `weapon_against_opponent` | Contribución sin veneno contra un oponente inmune. |
| `attack_strength` | `_attack_strength` | Fuerza y fuerza de armadura: armas fijas, desarmado, Energy Focus, bonos de primera ronda, carga montada, Slay Large Creature, Foul Odour, Eagle Friend, Scorpion Tail, Wolf-rat Bite y modificador entrante. |
| `hit_reroll` | `_hit_reroll` | Odio y enemistades por identidad, Dueling Pride, Kindred Hatred, Pikewall, Berserk Charge, pericia de arma, Dagger Master, Duellist, Virtue of Valour, repeticiones por carga y por primera ronda. |
| `hit_context` | `prepare_hit_context` | WS efectiva (carga, Knife Fighting, Serpent Staff, Shallya), WS defensora, modificador contextual (Hypnotize, Ye Give Way, Djinn's Curse, Backstabber, Violent Entry, Guiding Dream, Snorri, Flesh-Peddler, Unholy Stink, Follow Me, Hellblade, Andanti, Ball and Chain, Putrid Stench, Cold Steel, Foul Odour, Symbol of Unity), repetición, impacto automático, seis necesarios y objetivo fijo. |
| `hit_targets` | `to_hit_target` + `resolve_hit` | Acepta `modifier`, `fixed_target` y `needs_sixes`, conservando el impacto automático contra WS 0 y el seis forzado por miedo. |
| `wound_context` | `prepare_wound_context` | Fuerza, dureza con Thin Flesh, herida automática (Wraith Touch), Black Lotus/Wight Blades, Monster Slayer, bendición 2+, modificador, umbral crítico (incluido Hellblade por fila), repetición, crítico disponible y en repetición, Achilles Heel, Cold Steel sin daño. |
| `armour_context` + `armour_target_values` | `prepare_armour_context` + `armour_target` | Save de armadura y natural, fuego/bendito, Daemonic Flesh, Ladle (solo escudo y habilidades), Norse Bulwark, Cutthroat, Monster Slayer, dureza efectiva, penetración, bonos de objetivo, ignorar armadura, suelo y modificador de Djinn's Curse. |
| `special_save_context` | `prepare_special_save_context` + `_supplied_ward` | Ward y regeneración con Step Aside, Excellent Reflexes, Elven Agility, Ethereal, Ghost Pirate, Shadows Coil, Gypsy Ward, Magical Void, Djinn's Luck/Curse/Ethereal y bloqueos por fuego o bendito. |
| `parry_capacity` | `modular.state._parry_capacity` | Capacidad con las dos habilidades que `_types._parry_capacity` no incluía. |
| `parry_context` | `_parry_context`, `_estalian_parry`, `_darting_steel_parry`, `_parrying_weapons` | Elegibilidad, match, Starblade, rerolls (Miniath, White Tower, espada+broquel, Sword Master, hachas enanas, hacha+espada, garras, hoja doble), parar un seis, Estalian y Darting Steel. |
| `injury_context` + `injury_results` | `_injury_context` + `injury_condition` | Modificador, umbrales, perfil, Hard to Kill, True Grit, conmoción, Shock Rod, frágil, ponzoñoso, Survivor, Head Crusher, Ignore Pain, Jump Up y Mandrake, con filas divergentes. |

Además se alinearon con `modular.rounds` los dos operadores de pool que ya existían: `round_weapon_attack_count` usa el conjunto canónico `phases.WHIPCRACK_WEAPON_TAGS` (seis etiquetas, antes cuatro) y `opposed_attack_count` incorpora `mechanic.animal-friendship`, `species.normal-animal`, la exención de demonios frente al Signo de Sigmar y el diferimiento opcional de Tentacle Grapple, con el mismo orden de aplicación que el modular.

Cobertura medida: los **204 literales de regla** que usan los contextos modulares aparecen ya en `vectorized/` (antes faltaban 115). Los 15 helpers tienen equivalente vectorial con nombre propio; las diferencias de nombre son deliberadas para no sugerir que son los mismos objetos.

**Límites de estado del motor vectorizado**: `CombatState` no modela `banter_trick_active`, `dodge_trick_active`, `charm_auto_hit` ni `fear_hit_sixes`; el port los lee con `getattr(..., False)` para no inventar soporte ni romper cuando G02 los añada. `resources_spent` de Luck se mapea al array `luck_used` ya existente.

## Verificación de esta segunda entrega

```text
python -m pytest tests/python/combat/vectorized/test_rule_families_b.py -q -k projection
  -> 4 passed
python -m pytest tests/python/combat/vectorized/test_rule_families_b.py -q
  -> 9 passed, 2 failed (los dos preexistentes: catálogo `no_scope_yes` y
     `skill.mighty-blow` no disponible para ostlanders/ogre)
python -m pytest tests/python/combat/vectorized -q -n 8
  -> 112 passed, 14 failed (los mismos 14 preexistentes de G02: catálogo,
     compilación, puerta NumPy y la aserción de spawn-of-chaos)
```

Los cuatro casos nuevos comparan contra el oráculo modular, no contra valores inventados:

- `hit_context` con odio, Hellblade, Guiding Dream 2-3 y carga.
- `wound_context` y `armour_context`/`armour_target_values` con Wraith Touch, Thin Flesh, impacto natural 6 y dos filas.
- `special_save_context` y `parry_context` con Step Aside, ataque mágico y espada.
- `injury_context`/`injury_results` con la tabla del Conde de Ventimiglia y filas con condición inicial distinta.

## Lo que sigue sin poder cerrarse desde G03

1. **Integración**: `_attacks.py` (G04) sigue calculando WS, fuerza, modificador, dureza, parada y lesión con su propia aritmética inline. Las funciones de esta entrega están probadas pero el duelo no las llama; el deliverable conserva las sustituciones exactas por línea.
2. **Puerta y CSV**: mientras no exista esa llamada real no se retira `mechanic.inconsistency` ni `mechanic.guiding-dream` de `_PENDING["numpy"]`, y ninguna clave G03 se propone `implemented`.
3. **Campos de estado ausentes** (arriba): su modelado pertenece a G02/G06, no a este grupo.

El CSV canónico sigue intacto: SHA-256 `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`. Sin commits ni pushes.

## Corrección de revisión — máscaras por simulación (2026-10-21)

Se corrigieron los dos defectos reproducidos en la revisión de G03, conservando los cambios anteriores:

- `hit_context` acepta ahora `needs_sixes=`: booleano escalar o máscara del lote completo, como `PsychologyResources.fear_hit_sixes` de G05. Selecciona únicamente `rows`, respeta su orden y desactiva el efecto fuera de melé. Si se omite, conserva la lectura opcional del campo de estado. Los campos opcionales de banter y charm siguen también la selección por fila, sin conversiones booleanas de arrays.
- `special_save_context` acepta `dodge_trick_active=` con el mismo contrato de máscara completa. El objetivo de salvación, su bloqueo y la condición de salvación inmodificable se mantienen por fila durante toda la proyección, incluidas las concesiones de Gypsy Ward y Djinn. Una esquiva no desbloquea la salvación de otras filas. La omisión conserva la lectura del campo opcional de estado.

No se añadieron columnas a `CombatState` ni se modificaron G04, G05 o el driver. Para G04/G06, la conexión explícita de miedo es `hit_context(..., rows, needs_sixes=psychology[index].fear_hit_sixes)`; el índice 0/1 identifica al combatiente atacante. Las máscaras suministradas tienen tamaño del lote completo, no del subconjunto seleccionado. La esquiva se suministra con `special_save_context(..., rows, dodge_trick_active=mask)` cuando su productor todavía no tenga una columna de estado.

Se ampliaron dos comprobantes existentes de `test_rule_families_b.py`, sin crear funciones de test nuevas: miedo y flags mixtos con selección `[2, 0]`; salvación mundane-only contra ataque mágico con esquiva distinta por fila y contraste modular, incluyendo Djinn's Luck y Gypsy Ward. Se comprueba además que las máscaras de entrada no se modifican.

```text
python -m pytest tests/python/combat/vectorized/test_rule_families_b.py -q -k 'projection or lazy_characteristics' --tb=short
  -> 5 passed, 6 deselected in 0.58s
```

Esta evidencia cierra los defectos locales revisados; las conexiones de G04/G06 descritas arriba siguen pendientes. No se ejecutó la campaña de paridad, no se modificó el CSV ni se propone `verified`.
