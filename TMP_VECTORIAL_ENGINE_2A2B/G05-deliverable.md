# G05 — Psicología y liderazgo local vectorizados (entrega)

## Base utilizada

- Repositorio: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK` (misma copia de trabajo; no se creó otra).
- HEAD `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más los cambios locales existentes, incluidos G00 (`kernel.py`, `_driver.py`) y G02 (`_types.py`, `_state.py`, `_mutations.py`).
- Dependencias de inicio comprobadas: [G00-deliverable.md](G00-deliverable.md) y [G02-deliverable.md](G02-deliverable.md) existen y su base está en disco (`CombatState` con `stupidity_failed`, `disability`, `frenzy`, `condition`, `luck_used`; `_state.initialize_fighter` y `require_characteristics`).
- No se escribió `sources/knowledge/verification/clause-contracts.csv`, no se hicieron commits ni pushes.
- SHA-256 del CSV comprobado al cierre: `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`, idéntico al de la preparación. No hubo ninguna escritura sobre el registro.
- No se editó `_types.py`, el driver, la fachada ni ningún archivo de G03/G04. `git status` muestra `_attacks.py`, `_equipment.py`, `_operators.py` y varios tests modificados por los grupos concurrentes; G05 no los tocó.

## Resumen del trabajo

Se portaron `modular/psychology.py` y `modular/leadership.py` a dos módulos de lote nuevos, propiedad de G05:

1. `vectorized/_leadership.py` porta `resolve_local_leadership` completa a una llamada por conjunto de filas: elegibilidad (Frenzy, inmunidades, reliquia, Leadership automático, Enlightened), proveedores suministrados (Leader, Relay Orders, Songster, Slave Driver, Handler, Broken Spirit, Devoted), valor propio/prestado, Mob, Enchanting Beauty, Ghostly Howl, Cold Blooded, dados propios y repeticiones (first-failed, obligatoria, suministrada, songster, `leadership-reroll`, Raise Our Insignia, `fear-reroll`).
2. `vectorized/_psychology.py` porta `causes_fear`, `fears_opponent_fire`, `resolve_stupidity` y `resolve_fear`. La puerta de Estupidez, las exenciones, la regla del Héroe para Disability 6, la exención del Héroe Skaven, los receptores de Bear-handler, la cancelación de carga y las dos fases de Fear (carga y cargado) escriben máscaras por fila.
3. Los hechos locales se leen del `PreparedDuelContext` suministrado (participantes, lados, bandas, condiciones y distancias). No se producen posiciones, no se busca una banda completa y no se amplía a psicología de grupo.
4. Los recursos de Leadership que `CombatState` no tiene (`leadership.holy-relic`, `leadership.first-failed`, `poetry-first-leadership`, `one-roll-reroll`, `ranalds-luck`) viven en `LeadershipResources`, propiedad del driver de ronda. `fear_hit_sixes` vive en `PsychologyResources`. No se editó `_types.py` (propiedad de G02).

No se tocó el driver: la conexión es de G06. Por eso **no se propone ningún estado `implemented`** en el CSV; las claves siguen pendientes de integración.

## Archivos y funciones

| Archivo | Cambio |
| --- | --- |
| `packages/python/combat-engine/mordheim_combat/vectorized/_leadership.py` (**nuevo**) | `LeadershipResources`, `leadership_resources`, `_leader_radius`, `_supplied_provider`, `_relayed_leader`, `_instructing_leader`, `undead_foes_fear_immunity`, `_personal_die`, `_leadership_dice`, `_test_total`, `resolve_local_leadership`. |
| `packages/python/combat-engine/mordheim_combat/vectorized/_psychology.py` (**nuevo**) | `PsychologyResources`, `psychology_resources`, `StupidityOutcome`, `FearOutcome`, `fears_opponent_fire`, `causes_fear`, `_charge_gate`, `resolve_stupidity`, `resolve_fear`. |
| `tests/python/combat/vectorized/test_psychology_vectorized.py` (**nuevo**) | Seis casos enfocados (detalle abajo), marcados `rule_behavior`. |
| `TMP_VECTORIAL_ENGINE_2A2B/G05-deliverable.md` | Este documento. |

`vectorized/__init__.py` no se editó: la fachada es de G00/coordinador. Los helpers se importan desde sus módulos.

## Contrato de conexión para G06

### 1. Asignación, una vez por lote

```python
from mordheim_combat.vectorized._leadership import leadership_resources
from mordheim_combat.vectorized._psychology import psychology_resources

leadership = (leadership_resources(count), leadership_resources(count))
psychology = (psychology_resources(count), psychology_resources(count))
```

Cada array pertenece a un combatiente y a una fila; `leadership[0]`/`psychology[0]` son del primer duelo, `[1]` del segundo.

### 2. Inicio de cada ronda, antes de resolver acciones

Orden modular (`rounds.py`): productores de turno (Lunatics, Drunk) → `fear_hit_sixes=False` → `persistent-frenzy` → Estupidez → Fear (solo ronda 0) → ataques.

- Limpiar el resultado de Fear de la ronda anterior, como `rounds.py:490-491`:
  `psychology[0].fear_hit_sixes[:] = False` y `psychology[1].fear_hit_sixes[:] = False`.
- Reafirmar Frenzy persistente (`rounds.py:493-496`): `state.frenzy[rows] |= True` donde el compilado conserva `mechanic.persistent-frenzy`.
- Estupidez:

```python
stupidity = resolve_stupidity(
    first, second, state1, state2, active_rows,
    first_player_turn=first_player_turn, round_index=round_index,
    charges=first_charges if first_player_turn else second_charges,
    rng=rng, leadership=leadership[0 if first_player_turn else 1],
    decisions=decisions, context=prepared,
    lunatic_stupidity=lunatic_mask,     # productor de Lunatics, o None
    drunken_result=drunken_result,      # productor de Drunk, o None
)
first_charges, second_charges = (
    (stupidity.charges, second_charges) if first_player_turn
    else (first_charges, stupidity.charges)
)
```

`state.stupidity_failed` queda escrito en las filas probadas. `stupidity.failed` está alineado a `active_rows` y sirve de observación. Si tras cancelar cargas ninguna fila queda en contacto, se avanza de ronda como `_without_combat`.

- Fear, solo `round_index == 0`, antes de los ataques:

```python
fear = resolve_fear(
    first, second, state1, state2, active_rows, round_index=0,
    engaged=contact_mask,                 # bool por fila, tamaño count
    first_charges=first_charges, second_charges=second_charges,
    rng=rng, resources=psychology,      # hecho de Psicología: fear_hit_sixes
    leadership=leadership,              # recursos que gasta la prueba de Liderazgo
    decisions=decisions,
    context=prepared, key_prefix=f"round.{round_index}",
)
first_charges, second_charges = fear.first_charges, fear.second_charges
contact_mask = fear.engaged
```

### 3. Máscaras que consume la fase de ataques

- `state.stupidity_failed` debe poner a cero el pool de ataques de esa fila (`rounds.py:1365-1367`): `attacks1[state1.stupidity_failed] = 0`, `attacks2[state2.stupidity_failed] = 0`.
- `psychology[i].fear_hit_sixes` es «solo impacto natural 6 en melé» (`attacks.py:208`, `contexts.py:588`). **Propuesta concreta a G04/G06:** añadir a `_prepare_weapon_attack`/`resolve_attacks` un argumento `needs_sixes: np.ndarray | None` y aplicarlo como `hit_target` forzado a 6 en las filas marcadas. G05 entrega la máscara; el consumo es de la resolución de ataques.
- Frenzy ya lo consume `attack_count` con `state.frenzy`; los helpers saltan Estupidez y Fear en esas filas.

## Claves cubiertas

Familias de comportamiento portadas, agrupadas por mecanismo (el anexo del encargo conserva la asignación clave a clave):

- **Fear**: `mechanic.causes-fear`, `mechanic.fear-human`, `mechanic.fear-immunity`, `mechanic.fear-reroll`, `mechanic.fear-immunity-undead-chargers`, `mechanic.undead-foes-no-fear`, `mechanic.accustomed-to-fear`, `mechanic.ere-we-go`, `condition.impetuous-charge`, `mechanic.craven`, `mechanic.fears-fire`, `mechanic.fear-of-snakes`, `mechanic.fear-of-elves`, `mechanic.fear-beastmen`, `mechanic.morrs-servant`, `mechanic.beauty-of-the-sea`, `mechanic.wheelo-impact`, `mechanic.ghostly-howl`, `item/beastlash` + `weapon.beastlash`, `mechanic.ashamed-and-afraid`, `mechanic.slaanesh-charge-test`, `mechanic.hypnotic-musk`, `mechanic.opposite-sex-charge-test`.
- **Estupidez**: `mechanic.stupidity`, `condition.stupidity-exempt`, `condition.stupidity-failed`, `mechanic.disability` (resultado 6 y Héroe cercano), `mechanic.brood-mentality`, exención del Héroe Skaven, `mechanic.bear-handler-recipient` / `condition.bear-handler-nearby`.
- **Liderazgo local**: `mechanic.leader-six`/`leader-four`/`leader-twelve`, `mechanic.leader-fallback`, `mechanic.relay-orders`, `mechanic.songster`, `mechanic.slave-driver`, `mechanic.dim-witted-leader`, `mechanic.handler-leadership`, `mechanic.bear-handler`, `mechanic.broken-spirit`, `mechanic.devoted`, `mechanic.mob-leadership`, `defence.holy-relic`, `mechanic.automatic-leadership`, `mechanic.sigmar-enlightened`, `mechanic.own-leadership`, `mechanic.undivided-leader`, `mechanic.wizened-halfling`, `mechanic.cold-blooded-leadership`, `mechanic.cold-blooded-psychology`, `condition.enchanting-beauty`, `condition.poetry-victorious-leader`.
- **Repeticiones y recursos**: `mechanic.first-failed-leadership-reroll`, `mechanic.mandatory-leadership-reroll`, `mechanic.leadership-reroll`, `condition.command.raise-our-insignia-active`, `mechanic.ranalds-luck`, `mechanic.oracle`, `mechanic.augur-one-roll-reroll`, `skill.luck`, `mechanic.scryer`.
- **Frenzy**: `trait.frenzy`, `mechanic.persistent-frenzy`, `condition.impetuous-charge`; la consecuencia de ataques ya está en `_operators.attack_count`.

### Auditoría del anexo completo (637 principales + 42 de apoyo)

Se consultó el registro con `clause_registry.py` para los 679 pares `(id, clause_id)` del anexo y se clasificó cada par por el consumidor de su fila. `missing = 0`: ningún par del anexo falta del registro.

| Grupo | Filas | clause_id distintos | Estado real |
| --- | ---: | ---: | --- |
| Principales cuyo consumidor escalar es `modular/psychology.py` o `modular/leadership.py` | 621 | 93 | Consecuencia portada a los helpers; conexión en `_simulate_batch_core` pendiente (G06). |
| Principales sin consumidor | 16 | 13 | Revisadas una a una, tabla siguiente. |
| Apoyo cuyo consumidor escalar es psicología/liderazgo | 32 | 16 | Contribución de esta capa; cierre del dueño. |
| Apoyo sin consumidor | 10 | 5 | Identidad o estado suministrado: la capa lee la etiqueta o la máscara; sin código nuevo. |

#### Las 16 filas principales sin consumidor

| Clave | Estado real de G05 |
| --- | --- |
| `cause-fear--scope--fear-of-fire-rider` | Cubierta: el miedo al fuego es la rama `special` de `needs_test`, que no aplica la inmunidad de psicología («Fear of Fire still applies»); la rama ya existía así en el escalar. |
| `cause-fear--scope--immunity-and-fear` | Cubierta: `causes_fear` más `mechanic.psychology-immunity`. |
| `handler-leadership--scope--stupidity` y `handler-leadership--scope--stupidity-waiver` | Cubiertas: valor `stupidity_leadership`, préstamo solo de handler y exención automática con Tamer a ≤ 6" y no fuera de acción (Knocked Down/Stunned cuentan). |
| `songster-leadership-reroll` | Cubierta: repetición Songster con `min(10, value+1)`. |
| `cause-fear` (Maximilian) y las cuatro filas `frenzy` | Etiqueta compilada: Fear/Stupidity por los helpers, ataque doble por `_operators.attack_count`, estado por G02. |
| `madness-roll` | Estado permanente suministrado por construcción/campaña (G02); los helpers consumen la etiqueta resultante. |
| `beastmen-vengeance`, `burn-the-witch`, `traitor-hatred` | **No es una consecuencia de psicología/liderazgo**: el contrato es Hatred (repetición de impacto de primer turno; en `traitor-hatred` impuesta al oponente). El motor escalar tampoco la consume: `_hit_reroll` solo lee las etiquetas propias del atacante. Propuesta: transferir estas tres claves a G03/G04 o que su propietario añada el predicado cualificado; G05 no edita `_attacks.py`. |
| `never-charge` | **No es psicología**: es la guarda de carga (`validate_duel_start`/`charge_allowed`, G02) y su muestreo (G06). Sin código nuevo en esta capa. |
| `stern-rule` | **Bloqueada**: la KB solo dice «Uses the source stern/leadership rule» sin definición canónica; implementarla exigiría inventar la regla. Causa para `notes`/`blocked`: texto fuente ausente. |

#### Las 10 filas de apoyo sin consumidor

Las 10 filas se reparten así: `undead` (5) y `animated` (1) son clasificaciones; el Fear y la inmunidad se leen de las etiquetas compiladas y `animated` no tiene consumidor asignado, así que no piden código nuevo. `psychology-immunity` (2) y `deathwish--scope--deathwish-psychology` (1) son la exención que leen los helpers. `needle-and-thread--scope--mouth-sewn` (1) es la exclusión de proveedores con `condition.mouth-sewn` que aplica `_instructing_leader`/`usable`.

**Propuesta CSV.** Para las 621 filas principales y 32 de apoyo cuyo consumidor escalar es psicología/liderazgo, la propuesta es `in_progress` si el registro las conserva en `pending`: el portado está ejecutado y comprobado, pero la conexión desde `_simulate_batch_core` sigue pendiente. De las 16 filas sin consumidor: 11 quedan cubiertas o dependen de un estado que ya suministra G02 (también `in_progress`); `beastmen-vengeance`, `burn-the-witch` y `traitor-hatred` no reciben propuesta de G05 (transferencia a G03/G04); `never-charge` tampoco (G02/G06); `stern-rule` se propone `blocked` con la causa anterior. Ninguna clave pasa a `implemented` hasta que el driver llame a los helpers; `verified` exige la evidencia de G07. El CSV no se ha escrito.

## Conexiones pendientes y propuestas concretas

1. **G06 — driver**: ejecutar el contrato anterior. Sin esas llamadas, ningún comportamiento de este grupo está integrado.
2. **G04 — `_attacks.py`**: aceptar `needs_sixes` (Fear tras ser cargado) y aplicar el impacto solo con 6 natural en melé. G05 no edita ese archivo.
3. **G06 — productores**: `lunatic_stupidity` (Lunatics, `rounds.py:481-489`) y `drunken_result` (Drunk, `rounds.py:595-611`) se suministran como máscaras por fila; no requieren columnas nuevas en `_types.py`. Si G06 prefiere persistirlas, es cambio de G02/coordinador.
4. **Coordinador — fachada**: si G06 quiere `from mordheim_combat.vectorized import resolve_fear`, la reexportación en `__init__.py` corresponde a G00/coordinador.
5. **`beauty.passed`**: el operador escalar lo gasta pero ningún consumidor lo lee; el lote no lo almacena (documentado en el código).
6. **G03/G04 — Hatred de hirelings.** `beastmen-vengeance`, `burn-the-witch` y `traitor-hatred` están en el anexo de G05 pero su contrato es Hatred, no psicología: el escalar tampoco lo consume hoy (`_hit_reroll` lee solo las etiquetas del atacante). Propuesta: transferirlas al propietario de `_attacks.py` o que este añada el predicado cualificado y el caso de Hatred impuesto al oponente.
7. **G02/G06 — `never-charge`.** La guarda ya existe en `_state.charge_allowed`/`validate_duel_start`; falta el muestreo de G06. G05 no aporta código nuevo.
8. **Coordinador — `stern-rule`.** La KB no define la regla («Uses the source stern/leadership rule»); no se puede portar sin el texto fuente. Propuesta de `blocked` con esa causa en `notes`.

## Comandos ejecutados y resultados

Todas las cifras siguientes corresponden a la versión final de los archivos de esta entrega.

```text
python -m pytest tests/python/combat/vectorized/test_psychology_vectorized.py -q
  -> 6 passed

python -m pytest tests/python/combat/vectorized -q \
    --ignore=tests/python/combat/vectorized/test_psychology_vectorized.py
  -> 14 failed, 107 passed
python -m pytest tests/python/combat/vectorized -q
  -> 14 failed, 113 passed
# Repetido tras las correcciones de la revisión: mismos 14 fallos, 113 pasados.
# La lista de fallos es idéntica con y sin el archivo nuevo (diff vacío, 14 = 14).
# El árbol es compartido: los totales ajenos pueden mover unos pocos tests;
# el conjunto de fallos y el delta de +6 tests nuevos se mantuvo en cada pasada.
#   fallos preexistentes/ concurrentes de catálogo, familias compartidas,
#   proyecciones de _operators/_attacks y un test compartido de perfil aleatorio.
#   Ninguno importa _psychology/_leadership ni pasa por los helpers nuevos.

python -m pytest tests/python/combat/modular/test_hireling_psychology.py \
                 tests/python/combat/modular/test_dreamwalkers_undead_foes_fear.py -q
  -> 14 passed   (referencias modulares intactas)

sha256(sources/knowledge/verification/clause-contracts.csv)
  -> b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731
```

### Comparación directa escalar/lote (sonda de una fila, dados guionizados)

Se ejecutó una sonda temporal (no añadida al repositorio) que llama a
`modular.leadership.resolve_local_leadership` con un `DiceSource` guionizado y a
`vectorized._leadership.resolve_local_leadership` con un rng guionizado, sobre los
mismos hechos. Resultado: **8 de 8 coincidencias**.

| Escenario | Escalar | Lote |
| --- | --- | --- |
| Prueba normal que pasa (3+4 ≤ Ld 7) | True | True |
| Prueba normal que falla (5+5 > Ld 5) | False | False |
| Cold Blooded descarta el mayor (6+6+1 → 7 ≤ Ld 8) | True | True |
| Reliquia sagrada: pase automático | True | True |
| `mechanic.fear-immunity` con `fear=True` | True | True |
| `first-failed-leadership-reroll`: 12 y luego 2 | True | True |
| Proveedor `leader-six` a 6" (Ld prestado 9) | True | True |
| Proveedor a 7" (sin préstamo, Ld propio 3) | False | False |

La misma sonda comparó `modular.psychology.resolve_fear` con el lote sobre el
estado resultante, con dados fijos a 6: **2 de 2 coincidencias**.

| Escenario | Escalar | Lote |
| --- | --- | --- |
| Causante de Fear carga a una víctima de Ld 3: la víctima queda a 6s, la carga se mantiene | `charged=True/False`, `sixes=False/True`, `failed=[]` | idéntico |
| Portador de `fears-fire` falla su prueba de carga contra llamas: pierde carga y contacto | `charged=False/False`, `engaged=False`, `failed=['first']` | idéntico |

### Correcciones de la revisión

| Fallo | Causa | Corrección | Comprobación |
| --- | --- | --- | --- |
| Miedo + reliquia sagrada lanzaba `AttributeError` | `resolve_fear` pasaba el registro de Psicología a `resolve_local_leadership`, que indexa columnas de `LeadershipResources` | `resolve_fear` acepta `leadership=(L0, L1)` y lo usa en sus tres llamadas de Liderazgo; `resources` queda solo como hecho de Psicología (`fear_hit_sixes`) | sonda: portador de `defence.holy-relic` probado por Fear → pase automático, `holy_relic` gastado, `fear_hit_sixes=False`, sin excepción |
| Scryer repetía solo el primer dado (modular `[1,2]`, lote `[1,6]`) | la marca `rerolled` era una sola por prueba y el segundo dado la veía activa | cada dado de `_leadership_dice` lleva su propia marca (como `OwnedRollDice` la reinicia en cada `roll`); la marca acumulada del conjunto queda solo para vetar la repetición final de Liderazgo | sonda con dados 1 y 6 y repeticiones 1 y 2: total 3 ≤ Ld 3 → `True` y los cuatro dados consumidos; el lote anterior sumaba 1+6=7 → `False` |

La sonda no es evidencia de la campaña de paridad de G07: solo comprueba que el
lote reproduce la decisión del operador escalar en sus ramas principales.

No ejecutadas: campaña completa de paridad (G07), rendimiento (G08), E2E.

## Casos nuevos y justificación

1. `test_stupidity_failure_stays_on_its_row_and_cancels_that_rows_charge` — única prueba de la puerta de Estupidez: fila con Frenzy exenta frente a filas que fallan, escritura de `stupidity_failed` y cancelación de la carga propia en ronda 0; segunda llamada con `rows=[2]` demuestra que no toca otras filas.
2. `test_a_failed_fear_test_after_being_charged_marks_only_the_charged_rows` — Fear de la fase «cargado»: la víctima cargada por un causante de Fear falla y queda a 6s; el cargador no se modifica.
3. `test_a_failed_fear_test_cancels_the_chargers_contact_on_its_own_rows` — la otra rama: el cargador teme el fuego del oponente, falla su prueba de carga, pierde la carga y el contacto.
4. `test_local_leadership_borrows_the_supplied_providers_value_within_its_radius` — proveedor suministrado, banda y distancia: 8 supera el Ld propio 3 pero entra en el 9 prestado a 6"; a 7" no se presta.
5. `test_the_holy_relic_passes_once_and_the_next_test_rolls_normally` — recurso persistente: la reliquia pasa sin tirada una vez y la segunda prueba ya tira contra el Ld propio.
6. `test_causes_fear_matches_the_scalar_operator_on_the_supplied_facts` — comprobante de referencia del port de elegibilidad (seis pares de hechos suministrados); no es evidencia de paridad de fase 2.

No se añadieron pruebas por cláusula ni se copiaron E2E.

## Bloqueos y limitaciones

- **Integración pendiente**: los helpers no están llamados desde `_simulate_batch_core`; el criterio de entrega se cumple como helpers implementados y comprobados, con contrato explícito, no como comportamiento integrado.
- **Decisiones por lote**: las elecciones de proveedor y de recursos de tirada se toman una vez por conjunto de filas, convención ya usada por `staff_power` y los operadores. Con `decisions=None` se usa `AlwaysAccept`, igual que `resolve_round` hace `decisions or AlwaysAccept()`; una política que varíe por fila no se modela.
- **`opponent_charges`**: la exención `fear-immunity-undead-chargers` necesita la máscara de carga del oponente; G06 debe pasarla (Fear ya lo hace).
- **`fear_hit_sixes`** no tiene columna en `CombatState`; vive en `PsychologyResources` y su consumo en ataques es de G04/G06.
- **`lunatic_stupidity`/`drunken_result`** no tienen columna; se suministran como máscaras. Sin ellas, el lote reproduce la Estupidez ordinaria.
- **`beauty.passed`**: hecho de escritura sin lector en el motor aceptado; no se almacena.
- **Sin paridad declarada**: la comparación estadística y la puerta de backend son de G07; el rendimiento, de G08.
- `_types.py` y el driver no se editaron (propiedad de G02 y G06).
