# G02 — Estado por simulación, recursos, características y mutaciones (entrega)

## Base utilizada

- Repositorio: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK` (misma copia de trabajo del encargo; no se creó otra copia).
- HEAD `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más los cambios locales ya existentes, incluida la base de G00 (`kernel.py` con admisión por backend y `_driver.py` con `backend="numpy"`). No se hizo commit ni push.
- Dependencia de inicio cumplida: [G00-deliverable.md](G00-deliverable.md) existe y su base está en disco.
- CSV canónico **intacto**: SHA-256 `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`, idéntico al de la preparación. No se escribió el registro compartido.
- No se retiró ninguna entrada de `NUMPY_PENDING` ni de `NATIVE_PENDING`; el motor nativo y el Cython no se tocaron.

## Resumen del trabajo

Se portó la inicialización de estado del motor modular a columnas por simulación y se congeló el esquema que consumen G03/G04/G05/G06:

1. `CombatState` conserva todos sus campos previos y añade veinte columnas para límite de heridas, ausencia impresa de Iniciativa, características variables perezosas, recursos/condiciones de inicialización y equipo/mutaciones/forma por fila.
2. `vectorized/_state.py` porta `initialize_fighter`, `require_characteristics`, `_refresh_random_characteristics` y la validación de cargas de `initialize_duel`. `maximum_wounds` se reexporta del modular para que siga habiendo una sola definición.
3. `vectorized/_mutations.py` proyecta el equipo efectivo de cada fila reutilizando `modular.mutations.fighter_for_mutations` y `apply_brand`, con una vista de fila (`MutationState`) y caché en `effective_fighter`.
4. `_driver._new_state` y `_driver._refresh_random_characteristics` conservan nombre y firma y delegan en `_state`; `_resource_observation` no cambia (su contrato de cuatro recursos lo comparten el replay y `test_observations.py`).
5. Tres comprobantes nuevos: independencia entre filas + cadencia perezosa de Inconsistency, proyección de marca por fila y validación de cargas suministradas.

No se declara paridad: la campaña es de G07 y el rendimiento de G08.

## Archivos y funciones

| Archivo | Cambio |
| --- | --- |
| `packages/python/combat-engine/mordheim_combat/vectorized/_types.py` | `CombatState`: veinte campos nuevos (ver esquema). Sin cambios en los existentes ni en su orden. |
| `packages/python/combat-engine/mordheim_combat/vectorized/_state.py` (**nuevo**) | `STATS`, `STAT_BITS`, `STAT_ATTRIBUTES`, `maximum_wounds` (reexportado), `initialize_fighter`, `require_characteristics`, `refresh_random_characteristics`, `charge_allowed`, `validate_duel_start`. |
| `packages/python/combat-engine/mordheim_combat/vectorized/_mutations.py` (**nuevo**) | `MutationState`, `read_mutation_state`, `write_mutation_state`, `fighter_for_row`, `apply_brand_row`, `refresh_effective_fighter`; `_RowDice` (adaptador de una fila al protocolo `DiceSource`). |
| `packages/python/combat-engine/mordheim_combat/vectorized/_driver.py` | Solo `_new_state` y `_refresh_random_characteristics`: delegación a `_state` conservando firmas. `_resource_observation` y el bucle de rondas quedan como estaban (G06). |
| `tests/python/combat/vectorized/test_observations.py` | Tres casos nuevos (detalle al final). |
| `TMP_VECTORIAL_ENGINE_2A2B/G02-deliverable.md` | Este documento. |

`vectorized/__init__.py` no se editó: no es propiedad de G02. Los helpers nuevos se importan desde `mordheim_combat.vectorized._state` y `._mutations`; si el coordinador quiere reexportarlos en la fachada histórica, es un cambio de G00/coordinador.

## Esquema de estado entregado (base congelada para G03–G06)

Todas las columnas tienen `count` elementos, uno por simulación, y pertenecen a **un solo combatiente**. Ningún array se comparte entre `state1` y `state2` ni entre filas.

| Campo | Forma / dtype | Valor inicial | Consumidor previsto |
| --- | --- | --- | --- |
| `starting_wounds` | `int16` | `maximum_wounds(fighter)` | G06 (recuperación, ataque por herida), G04 (equipo que resta heridas) |
| `initiative_missing` | `bool` | `True` si el perfil imprime Iniciativa en blanco | G03 (orden exacto: ausente nunca es un número) |
| `random_rolled` | `uint8` | máscara `0` (perezoso) o bits ya tirados (modo compatible) | `require_characteristics`, G03/G04 |
| `random_modifiers` | `(5, count) int16`, orden `WS,S,T,I,A` | delta fijo de Inconsistency respecto a la característica impresa | `require_characteristics` |
| `torture_strength_loss` | `int8` | `0` | G04/G06 (recuperación de S) |
| `guiding_dream_result` | `int8` | D6 de Guiding Dream; `0` si no aplica | G03 (`+1 al impacto` con 2–3; hoy no portado) |
| `stupidity_failed` | `bool` | tags de Estupidez fallida, exención, frenesí e inmunidad | G05 |
| `massively_built_lost_turn` | `bool` | tag `condition.massively-built-lost-turn` | G05/G06 |
| `netted` | `bool` | tag `condition.netted`; además deja `condition=KNOCKED_DOWN` | G05/G06 |
| `backley_penalties` | `object` (tupla `(stat, puntos)`) | pares de la poción de Backley; `()` si no aplica | G04 (alquimia) |
| `mutations` | `object` (tupla `MutationOption`) | `()` | G04/G06 |
| `mutation_equipment` | `object` (tupla `CarriedEquipment` o `None`) | `None` = inventario compilado | G04 |
| `mutation_weapon_limbs` | `object` (tupla `EffectSet`) | `()` | G04 |
| `mutated_hands` | `object` (tupla `str`) | `()` | G04 |
| `atrophied_arms`, `atrophied_legs` | `int8` | `0` | G04/G06 |
| `transformed`, `equipment_cast_off`, `hillman_wolf` | `bool` | tag de construcción `compiler.hillman-wolf-form` solo para `hillman_wolf` | G04/G06 |
| `mutation_tail` | `int8` | `-1` (ninguna cola elegida); `n` representa `mutation-tail.n` | G04 |
| `effective_fighter` | `object` (tupla nula) `CompiledFighter \| None` | `None`; la rellena `fighter_for_row` | G04/G06 |

Convenciones:

- `effective_fighter[row]` es una **caché** de la proyección de esa fila. `write_mutation_state` y `refresh_effective_fighter` la invalidan; nadie más debe escribirla.
- Las columnas `object` guardan valores inmutables (tuplas/`None`). No hay listas mutables compartidas.
- `random_rolled` es una máscara, no un `frozenset`: 1 WS, 2 S, 4 T, 8 I, 16 A. `random_modifiers` usa el orden fijo `("WS","S","T","I","A")` y es cero para las características no declaradas.

## Contratos y cadencia

### `initialize_fighter(fighter, count, rng, *, lazy_inconsistency=False)`

Porta `modular.state.initialize_fighter`:

- Características impresas + `toughness_bonus`; tiradas de `random_characteristics` en el orden declarado; Crimson Shade conserva su D3 en `crimson_initiative` (el motor ya lo suma en `effective_initiative`).
- Bonus de condiciones Petru/Alchemist, con `max(1, …)` salvo Inconsistency y con los pares de Backley conservados.
- Poesía (+1 WS), resultado permanente de Disability, Guiding Dream (D6; `+1 S` con 4–5 y frenesí con 6 para el objetivo nominado), heridas máximas, condición inicial por red, frenesí, Estupidez fallida, Massively Built y marcas de forma.
- Ausencia impresa de Iniciativa: columna numérica `0` como marcador de orden y `initiative_missing=True`; **no** se inventa una característica.
- `mechanic.disability` sin `condition.disability-N` **lanza `ValueError`**, como el modular. El compilador ya lo exige desde C09; la antigua tirada D6 de `_new_state` era inalcanzable con un `CompiledFighter` compilado y contradecía el resultado permanente.

### `require_characteristics(fighter, state, rows, rng, needed)`

Solo actúa con `mechanic.inconsistency`. Recorre `fighter.random_characteristics` en orden declarado, tira únicamente las características de `needed` que aún no tienen bit en `random_rolled` para esas filas, aplica `random_modifiers` (y `torture_strength_loss` en S) y conserva el resultado para el resto de la ronda. Las filas fuera de `rows` no se tocan. Es el punto de llamada que deben usar G03/G04 en cada operación que lea WS/S/T/I/A.

### `refresh_random_characteristics(fighter, state, rows, rng, *, lazy_inconsistency=False)`

Limpia `random_rolled[rows]` al inicio de ronda (equivalente a `rounds.resolve_round`, que también limpia `random_rolled`). Con `lazy_inconsistency=True` un perfil Inconsistency espera la tirada de su operación; con el valor por defecto reproduce la cadencia histórica del motor (rerrollo conjunto cuando WS/S/T/A son todas variables), que es la que mantiene verde `test_vectorized_engine.py::test_random_profile_characteristics_are_rolled_per_simulation_row` (test compartido, no editable por G02).

### `charge_allowed` y `validate_duel_start`

`charge_allowed(fighter, opponent)` porta la condición de `initialize_duel`: no cargar con `mechanic.cannot-charge` ni `condition.alchemist-addicted`; Shallya Strictures solo permite cargar contra `band.carnival-of-chaos` o `identity.onogal-follower`.

`validate_duel_start(first, second, context)` lanza el mismo `ValueError` que el modular para un snapshot imposible:

- lanza con `weapon.lance`;
- Guiding Dream nominado exige un Héroe en frente;
- una carga suministrada debe ser legal, no puede contradecir un contacto base y las cargas obligatorias (`condition.impetuous-charge`, `condition.nuttaz-charge`) exigen su intento;
- Witch-finder exige la marca `mechanic.solkan-witch-finder`, la carga y un enemigo de las categorías nombradas.

Devuelve `(first_charges, second_charges)` cuando el contexto declara las cargas y `None` cuando aún deben muestrearse. **El muestreo y su llamada desde `_simulate_batch_core` pertenecen a G06** (ver propuestas).

### `_mutations`

`fighter_for_row(fighter, state, row)` devuelve el `CompiledFighter` efectivo de la fila: el compilado si no hay marcas, o la proyección cacheada. `apply_brand_row(...)` adquiere una marca en una fila con el generador de esa fila y reutiliza literalmente `modular.mutations.apply_brand`; la transición (cuándo se adquiere) es de G06. `read_mutation_state`/`write_mutation_state` son la vista de fila y su escritura, incluyendo el mapeo `mutation_tail <-> mutation-tail.n`.

## Claves principales asignadas

Estado real, no etiqueta: «integrado» = la ruta NumPy del motor lo ejecuta; «helper» = implementado y probado, pero su llamada en el bucle aún no existe.

| id | clause_id | Estado real | Propuesta CSV |
| --- | --- | --- | --- |
| `mechanic/mechanic.guiding-dream` | `whole` | Parcial: D6 de inicio, `+1 S` (4–5) y frenesí (6) integrados en `_new_state`; `guiding_dream_result` disponible. El `+1 al impacto` (2–3) es de G03 y la guardia «Héroe nominado» está en `validate_duel_start` sin conectar (G06). | Sin cambio (`numpy: pending`, `native: pending`), nota de progreso |
| `mechanic/mechanic.shallya-strictures` | `whole` | `charge_allowed` + `validate_duel_start` probados; el muestreo obligatorio sigue en el bucle de G06. | Sin cambio |
| `rule/catalog/warband/skill.monstrous/skill.monstrous` | `whole` | Integrado: `maximum_wounds` compartido y heridas iniciales en `_new_state`; el motor NumPy admite y arranca con +1 herida (comprobado). | `numpy: implemented`, `native` sin cambio |
| `rule/mordheim/black-orcs/orc-nuttaz--savage/profile.equipment-restrictions` | `mandatory-charge` | `condition.nuttaz-charge` validada en `validate_duel_start`; falta el muestreo de G06. | Sin cambio |
| `rule/mordheim/marauders-of-chaos/condemned--inconsistency/profile.random-characteristics` | `whole` | Estado perezoso, refresco por ronda y reutilización probados; el motor conserva por compatibilidad la tirada conjunta de `_new_state` y los operadores aún no llaman a `require_characteristics`. | Sin cambio |
| `rule/trollheim/khemri-necromancers/band--necromantic-modification-ogre-flesh/skill.monstrous` | `whole--scope--wound-bonus` | Integrado por el mismo operador de heridas máximas que la clave de catálogo. | `numpy: implemented`, `native` sin cambio |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` | `advancement-lift` | Hecho de campaña excluido; sin consumidor de duelo. G02 no añade ruta. | Sin cambio |
| ídem | `whole--scope--equipment-ban-variable-state` | Estado variable representado en `random_rolled`/`random_modifiers`; la prohibición es de campaña y su transporte de construcción ya existe. Sin cambio de motor. | Sin cambio |
| ídem | `whole--scope--unarmed-penalty-waiver` | Resuelto en construcción: el Condemned compila `main_weapon=weapon.natural-attacks` (S+0) y `unarmed_weapon` sin penalización; ambos motores leen el compilado. G02 no necesita ruta nueva. | Sin cambio; candidato a cierre del coordinador tras G07 |
| `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` | `whole` | Acceso a lista ya resuelto en el perfil; sin consumidor de duelo nuevo. | Sin cambio |
| `source/catalog/hirelings/dramatis-personae/grade-1c.yaml/@/profiles/0/unresolved_references/0/unclassified` | `profile` | Perfil variable soportado por `initialize_fighter(lazy_inconsistency=True)` + `require_characteristics`; la conexión en el bucle es de G03/G06. | Sin cambio |
| `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan/hireling.hired-sword.priest-of-verena.rule.marks-of-solkan.pending-duel` | `witch-finder--scope--compulsory-charge` | Validación de la carga marcada y del enemigo nombrado, probada; falta el muestreo obligatorio de G06. | Sin cambio |

No se propone `verified` para ninguna: eso exige la evidencia de paridad de G07.

## Claves de apoyo (129)

No se propone estado para ellas: su cierre pertenece a G03–G06. La contribución de esta capa es la base que consumen, agrupada por mecanismo:

- **Heridas y recuperación**: `skill.monstrous` (catálogo, Khemri, disability-related heal limits), `starting_wounds` y `maximum_wounds` compartido.
- **Cargas obligatorias/limitadas**: Shallya, Nuttaz, Witch-finder, impetuosas, `mechanic.cannot-charge`, `condition.alchemist-addicted` (validación disponible; muestreo en G06).
- **Características variables**: Condemned, Belandysh, modificadores de Inconsistency (perezoso y por ronda).
- **Equipo/mutaciones/forma**: miembros mutados, armas naturales, cola prensil, pérdida de equipo, transformación, atrofia, caché de equipo efectivo por fila.
- **Recursos/condiciones de inicio**: Guiding Dream, Estupidez fallida, Massively Built, red, backley, poesía, disability permanente.

## Conexiones pendientes y propuestas concretas

1. **G03 — tiradas perezosas y orden.** Llamar a `require_characteristics(fighter, state, rows, rng, needed)` en el punto exacto en que `_operators.py`/contextos leen WS/S/I/A; los puntos modulares equivalentes son `modular/attacks.py` (211–216, 378–380, 428, 493, 538–541, 603, 680) y `modular/pools.py` (325, 486–488), más `modular/aftermath.py` (88, 148). Usar `state.initiative_missing` para el orden de Iniciativa ausente y `state.guiding_dream_result` para el `+1 al impacto` con 2–3.
2. **G04 — equipo efectivo.** Consumir `fighter_for_row(fighter, state, row)` en `_equipment.py`/`_attacks.py` en lugar del compilado fijo cuando la fila tenga marcas; `mutation_weapon_limbs` y `mutated_hands` ya son columnas. `backley_penalties` es la representación para `alchemy`.
3. **G05 — psicología.** `stupidity_failed`, `massively_built_lost_turn` y `netted` ya tienen columna; hoy no se usan en el bucle. La guardia de Disability es ahora la del modular (resultado permanente suministrado).
4. **G06 — integración de rondas.** En `_simulate_batch_core`: llamar a `validate_duel_start(first, second, context)` antes de inicializar; usar `charge_allowed` al muestrear cargas (y respetar contacto base y cargas obligatorias); cambiar a `_state.initialize_fighter(..., lazy_inconsistency=True)` y `_state.refresh_random_characteristics(..., lazy_inconsistency=True)` cuando los operadores de G03/G04 llamen a `require_characteristics`; aplicar transiciones de marca con `apply_brand_row` y refrescar la caché con `refresh_effective_fighter`.
5. **Coordinador — puerta NumPy.** Solo tras (4) pueden retirarse de `kernel._PENDING["numpy"]`, conservando `NATIVE_PENDING`: `mechanic.inconsistency`, `mechanic.guiding-dream` (requiere también el `+1` de G03), `mechanic.shallya-strictures`, `condition.nuttaz-charge`, `condition.witch-finder-charge`. `mechanic.solkan-witch-finder` tiene además consumidores de estado de G05, así que su retirada debe coordinarse con ese grupo. La puerta nativa no se toca.
6. **Coordinador — fachada.** Si G03/G04 quieren `from mordheim_combat.vectorized import ...`, la reexportación en `vectorized/__init__.py` corresponde a G00/coordinador; G02 no edita ese archivo.

## Modo compatible y por qué existe

`_new_state` y el wrapper `_refresh_random_characteristics` mantienen la cadencia **eager** histórica para un perfil Inconsistency; `initialize_fighter(..., lazy_inconsistency=True)` y el refresco con el mismo argumento implementan la cadencia modular. Motivo concreto: `tests/python/combat/vectorized/test_vectorized_engine.py::test_random_profile_characteristics_are_rolled_per_simulation_row` (test compartido, no propiedad de G02) exige valores ya variados en `_new_state` para el Condemned. Como `mechanic.inconsistency` sigue en la puerta NumPy, ningún duelo admitido ejecuta hoy esa ruta; G06 cambia la llamada cuando los operadores usen el helper y entonces la puerta puede retirarse. La desviación queda registrada aquí, no oculta.

## Comandos ejecutados y resultados

```text
python -m pytest tests/python/combat/vectorized/test_observations.py -q
  -> 4 passed

python -m pytest tests/python/combat/test_kernel_plan.py \
  tests/python/combat/vectorized/test_backends.py \
  tests/python/cli/test_calibrate.py \
  tests/python/construction/test_condemned_source_profile.py \
  tests/python/construction/test_hireling_resources.py -q
  -> 26 passed

python -m pytest tests/python/combat/vectorized -q -n 8
  -> 97 passed, 14 failed (los 14 ya fallaban antes de G02; detalle abajo)

python -m pytest tests/python/combat -q -n 8
  -> 1573 passed, 37 failed (los 37 en archivos no editados por G02; detalle abajo)

# Humo real de la ruta NumPy:
simulate_duel(DuelRequest(f, f, 20, seed=7), backend="numpy")
  -> DuelResult(first_wins=8, second_wins=12, unresolved=0, simulations=20)   # igual que la base G00
_new_state(monstrous, 2, rng).wounds -> [2, 2]
simulate_duel(DuelRequest(monstrous, f, 20, seed=7), backend="numpy")
  -> DuelResult(first_wins=15, second_wins=5, unresolved=0, simulations=20)

# Comparación directa modular/vectorizado (initialize_fighter y require_characteristics):
Guiding Dream 4 -> S=4, frenzy=False, result=4 en ambos
Guiding Dream 6 -> S=3, frenzy=True,  result=6 en ambos
Inconsistency perezoso -> WS=3, A=1, sin tiradas en ambos; tras pedir WS con un 5 -> WS=5 en ambos
maximum_wounds -> idéntico (monstrous 2, petru-fortitude 2)

sha256(clause-contracts.csv) -> b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731
```

Fallos preexistentes observados en `tests/python/combat/vectorized` (14), ninguno en las funciones editadas:

- 12 fallan en compilación/catálogo/gate antes de llegar a `_new_state`: conteos de familias (998/964/101), binding `mechanic.netter`, `attacks_bonus` de Black Hunger, mensajes de contrato de compilación, `skill.mighty-blow` no disponible, mensaje de gate de Frantic y el rechazo de modificadores locales (orden de comprobaciones de G00 en `kernel.require_optimized_support`).
- `test_disability_guardian…` falla en `compile_fighter` (`Disability requires one permanent supplied result`), antes de la inicialización; es la comprobación de C09, no de G02.
- `test_random_profile_characteristics_are_rolled_per_simulation_row` falla en su segunda mitad porque `spawn-of-chaos` imprime A=2 y no tiene `random_characteristics`; el antiguo `_new_state` también producía `[2]*200` (verificado: `spawn printed attacks 2 random ()`). G02 conserva la primera mitad (Condemned) verde.

En `tests/python/combat` (37 fallos), los 23 restantes están en `modular/` y `native/` y fallan en el orden de mensajes de la puerta de G00 (`test_spectral_touch_activation`, `test_vomit_attack`) o en ELF/extensiones y catálogo (`test_native_*`); ninguno pasa por `_state`/`_mutations`.

Comprobaciones **no** ejecutadas: campaña de paridad G07, batería de rendimiento G08, E2E completo.

## Casos nuevos y justificación

1. `test_initialised_rows_keep_independent_state_and_lazy_characteristics` — cubre el hueco concreto de independencia entre filas y la cadencia perezosa: `_new_state`/`initialize_fighter` no tiran al inicio, solo la característica pedida y una vez por ronda, sin tocar otras filas.
2. `test_brand_projection_stays_on_its_own_simulation_row` — `_mutations.py` es un módulo nuevo sin cobertura; comprueba que una marca en la fila 1 no altera la fila 0, que la proyección se cachea y que la fila sin marca conserva el compilado.
3. `test_supplied_duel_start_facts_follow_the_modular_charge_contract` — cubre las tres cláusulas de carga admitidas (Shallya, Nuttaz, Witch-finder) sin conectar el muestreo, que es de G06.

No se añadieron pruebas por cláusula ni se copiaron E2E.

## Bloqueos y limitaciones

- **Inconsistency**: el motor mantiene la tirada eager por compatibilidad con un test compartido; la ruta perezosa está implementada y probada pero solo se activa con `lazy_inconsistency=True`. La puerta NumPy sigue rechazando `mechanic.inconsistency`.
- **Iniciativa ausente**: la columna numérica usa `0` como marcador de orden y `initiative_missing` conserva la ausencia. G03 debe consultar el flag para el orden exacto (dos ausentes empatan; una ausente va después de cualquier valor impreso). El motor anterior fallaba al inicializar un perfil con Iniciativa en blanco; ahora inicializa.
- **`_resource_observation`**: sigue informando solo `lucky-charm`, `force-of-will`, `mark-of-the-old-ones` y `luck` (contrato de replay). Recursos como `mutation-tail.n`, `poetry-inspiration-active` o `disability.n` no se informan ahí; ampliar la observación es de G07 y rompería expectativas existentes si se hace sin acuerdo.
- **Cargas**: validación de hechos suministrados y helper de permisos, sin muestreo. Un duelo con contexto que no declare cargas sigue muestreando como antes.
- **Mutaciones**: proyección y adquisición por fila disponibles; la transición no está conectada y la paridad de consumo de dados de `apply_brand_row` en lote es de G06/G07.
- **Disability**: `initialize_fighter` ahora rechaza `mechanic.disability` sin resultado permanente, como el modular; el compilador ya lo exigía. La anterior tirada D6 de `_new_state` era inalcanzable con un compilado y se retiró.
- **Native**: sin cambios. `NATIVE_PENDING` conserva todas sus entradas.
- No se ha escrito el CSV ni se han hecho commits/pushes.
