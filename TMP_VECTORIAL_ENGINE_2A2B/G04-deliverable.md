# G04 — Pools de ataques, equipo efectivo, daño y reacciones (entrega)

## Base utilizada

- Repositorio: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK`, misma copia de trabajo del encargo.
- HEAD `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` más los cambios locales existentes.
- Dependencias de inicio comprobadas: [G00-deliverable.md](G00-deliverable.md) y
  [G02-deliverable.md](G02-deliverable.md) existen y su base está en disco
  (`_state.py`, `_mutations.py`, admisión por backend en `kernel.py`).
  **No existe `G03-deliverable.md`**: `_operators.py` estaba siendo editado por G03 durante
  esta entrega (pasó de 20 KB a 68 KB y quedó transitoriamente sin compilar). No se editó
  ese archivo ni se asumió ninguna interfaz nueva de G03; la conexión con operadores
  permanece como propuesta.
- G05 también escribía `_psychology.py` y `_leadership.py` en paralelo, y G03 añadía tests
  en `test_rule_families_b.py`. Esa escritura concurrente produjo recuentos de suite
  variables; las comprobaciones de esta entrega se acotaron a los archivos propios y se
  indican abajo con su resultado real.
- CSV canónico **intacto**: SHA-256
  `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`, idéntico al de la
  preparación. No se escribió el registro compartido.
- No se tocó `_operators.py` (G03). `_types.py`/`_state.py` (G02) y `_driver.py` (G06) se
  editaron **solo** para añadir y limpiar los recursos de fase `seaguard_used` y
  `corruption_used`, por coordinación explícita del encargo; el resto del trabajo quedó en
  `_attacks.py`/`_equipment.py`. No hay commits ni pushes.

## Resumen del trabajo

Se completó la capa de ataques/equipo de G04 sobre las capas G00+G02:

1. **Equipo efectivo por fila** (`_equipment.py`): `phase_equipment` deja de ser una copia
   parcial y delega en `modular.equipment.equipment_for_state`, de modo que la pérdida de
   objetos de una mano rota, la transformación que descarta el equipo, la forma lobo del
   Cursed Hillman, la sustitución por arma de reserva, el club del Festooned with Pistols y
   el filtrado de ataques extra tienen una sola definición. Se añadió
   `equipment_for_rows`, que proyecta solo las filas con estado propio (manos rotas,
   mutación, transformación) y deja el resto con la proyección del lote.
2. **Resolución de ataques** (`_attacks.py`): se portaron comportamientos que faltaban en la
   ruta NumPy — salvación etérea, Honorable, Ravenous Onslaught, Killing Blow, Torturer,
   Titanic Strength, Hard to Rattle, Marine Hunter, fuerza y reroll del Seaguard Spear Master,
   Corrupción, empeoramiento del yelmo por Skull Busta, y la salvación de armadura que sí
   consume el Bull Charge. La resolución dejó de repetir cálculos: impacto y parada usan
   `hit_context`/`parry_context`, la herida `wound_context`, la lesión `injury_conditions` y
   la armadura `armour_targets` (operadores de G03). El seis natural se conserva en
   `PreparedAttack.natural` para que una concesión (Mark of the Old Ones) no active reglas
   de seis.
3. **Reacciones y defensas inmediatas**: la sangre ácida ya existía; se añadieron las
   reacciones de herida que faltaban (Torturer, Titanic Strength, Spectral Touch), la
   resolución de Wraith Touch (anulación contra No Muertos/Poseídos, herida automática y
   curación del Liche), el reroll de armadura de las Eshin Assassin robes y la rotura de mano
   del Sword-breaker, en el mismo punto en que el modular las aplica, antes de cerrar el
   evento de daño.
4. Cinco comprobantes nuevos, mínimos y representativos (detalle al final).

No se declara paridad: la campaña es de G07. No se propone `verified` para ninguna clave.

## Archivos y funciones

| Archivo | Cambio |
| --- | --- |
| `packages/python/combat-engine/mordheim_combat/vectorized/_equipment.py` | Reescrito: `_broken_slots`, `_row_state`, `phase_equipment` (delega en el modular y acepta `broken_hands`, `transformed`, `equipment_cast_off`, `hillman_wolf`), `equipment_for_rows`; `staff_power` sin cambios. |
| `packages/python/combat-engine/mordheim_combat/vectorized/_attacks.py` | `_parry_offer_capacity` (nuevo); `_parry_hits` (parada sin arma y a dos manos, reroll del White Tower, exclusión de Killing Blow, rotura por Sword-breaker); `_apply_hit_defences(saved_rows=)` con salvación etérea; `_prepare_weapon_attack` (Honorable por ataque, +1 F del Seaguard con lanza en la primera ronda); `_resolve_weapon_once` (Killing Blow automático, Spectral Touch, Wraith Touch, Titanic Strength, Marine Hunter, Torturer, Hard to Rattle/Skull Busta, reroll de las Eshin robes); `resolve_attacks` (filtro Honorable, siembra de la capacidad de parada, Ravenous Onslaught, salvación de armadura y limpieza de frenesí del Bull Charge). |
| `packages/python/combat-engine/mordheim_combat/vectorized/_types.py` | `PreparedAttack.natural` (cara física del impacto) y las columnas de recurso `seaguard_used` / `corruption_used` en `CombatState`. Fichero de G02; edición coordinada. |
| `packages/python/combat-engine/mordheim_combat/vectorized/_state.py` | Inicializa `seaguard_used` y `corruption_used` a `False`. Fichero de G02; edición coordinada. |
| `packages/python/combat-engine/mordheim_combat/vectorized/_driver.py` | Limpia ambos recursos al inicio de cada ronda, junto a `parry_used`. Fichero de G06; edición coordinada. |
| `tests/python/combat/vectorized/test_shared_families.py` | Seis casos nuevos (`ScriptedRng`, `synthetic`, `_resolve` como apoyo local). |
| `TMP_VECTORIAL_ENGINE_2A2B/G04-deliverable.md` | Este documento. |

No se editó `test_rule_families_a.py`: sus tres fallos actuales son de catálogo/conteo y no
de la ruta de ataque.

## Comportamientos portados

| Comportamiento | Referencia modular | Ruta NumPy | Estado real |
| --- | --- | --- | --- |
| Salvación etérea 4+ tras impactar; mágico la ignora | `attacks.py::_resolve_reference_attack_body` (ethereal), `pools.py::_resolve_prepared_defences` | `_apply_hit_defences` (ordinario) y rama Bull Charge de `resolve_attacks` | Integrado |
| Honorable no ataca a Derribado/Aturdido | `pools.py::_resolve_attack_pool_body`, `attacks.py` (por ataque) | filtro de filas en `resolve_attacks` y en `_prepare_weapon_attack` | Integrado |
| Ravenous Onslaught: seis natural da otro ataque con el mismo arma, encadenable | `pools.py::_resolve_attack_pool_body` | bucle creciente de `prepared_attacks` en `resolve_attacks` | Integrado (ver desviación) |
| Killing Blow: seis natural hiere automáticamente y no se puede parar | `attacks.py::_resolve_reference_attack_body` | `_resolve_weapon_once` + `_parry_hits` | Integrado (ver desviación) |
| Torturer: −1 F al herido en cuerpo a cuerpo, no muertos inmunes | `aftermath.py::_react_to_wound` | `_resolve_weapon_once` tras aplicar daño | Integrado |
| Titanic Strength: herida fallida derriba si falla la prueba de F | `attacks.py::_resolve_reference_attack_body` | `_resolve_weapon_once` antes de cerrar la herida | Integrado |
| Hard to Rattle: reacción de yelmo 4+, fuego excluido | `attacks.py::_resolve_wound_damage_body` | reacción de aturdimiento en `_resolve_weapon_once` | Integrado |
| Skull Busta: yelmo 6+ (no con Thick Skull) | idem | idem | Integrado (la clave es de G03; aporte de esta capa) |
| Marine Hunter: daño ×2 contra `species.aquatic` | idem | `_resolve_weapon_once` | Integrado |
| Seaguard Spear Master: +1 F con lanza y un reroll de impacto en la primera ronda | `contexts.py::_attack_strength`, `attacks.py` | `attack_strength` (G03) + `_prepare_weapon_attack` con `seaguard_used` | Integrado |
| Corrupción: el defensor fuerza el reroll del impacto que le acierta, una vez por fase | `attacks.py::_resolve_reference_attack_body` | `_prepare_weapon_attack` con `corruption_used` | Integrado |
| Guiding Dream: +1 al impacto contra el Héroe nominado | `contexts.py::prepare_hit_context` | `hit_context` (G03) → `hit_targets` | Integrado (era el defecto reportado: 4 en vez de 3) |
| Chosen of the White Tower: parada sin arma y reroll con espada/escudo | `state.py::_parry_capacity`, `contexts.py::_parry_context` | `_parry_hits`, `_parry_offer_capacity`, siembra en `resolve_attacks` | Integrado |
| Instinctive Warrior: parada con arma a dos manos | idem | `_parry_hits`, `_parry_offer_capacity`, siembra en `resolve_attacks` | Integrado |
| Spectral Touch: seis natural añade una herida de la misma tirada a través de las salvaciones | `attacks.py::_resolve_reference_attack_body` | `_resolve_weapon_once` (herida extra antes del paso de herida propio) | Integrado |
| Eshin Assassin robes: reroll gratuito de cada salvación de armadura fallida | `attacks.py::_resolve_wound_damage_body` | `_resolve_weapon_once` (bloque de salvación de armadura) | Integrado |
| Sword-breaker: una parada con éxito atrapa a 4+ y rompe la mano atacante | `attacks.py::_resolve_reference_attack_body` | `_parry_hits` (marca `broken_hands` de la fila) | Integrado; la mano rota solo cambia el arma con la proyección por fila de G06 |
| Wraith Touch: ataque anulado contra No Muertos/Poseídos, herida automática y +1 herida al Liche | `attacks.py::_resolve_reference_attack_body`, `contexts.py::prepare_wound_context` | `_prepare_weapon_attack` (anulación sin dado) y `_resolve_weapon_once` (herida automática + curación) | Integrado en la resolución; el ataque único lo elige G06 (ver propuestas) |
| Bull Charge: la salvación de armadura detiene el derribo | `attacks.py::_resolve_reference_attack_body` | rama Bull Charge de `resolve_attacks` | Integrado (corrección; ver aviso) |
| Pérdida de equipo, reserva, transformación, forma lobo, club del Festooned | `equipment.py::equipment_for_state` | `_equipment.phase_equipment` / `equipment_for_rows` | Implementado; conexión por fila pendiente de G06 |

### Aviso sobre el Bull Charge

`mechanic.bull-charge` **no** está en la puerta NumPy, así que la salvación de armadura
añadida cambia resultados de duelos hoy admitidos. Es una corrección deliberada: el modular
resuelve la armadura antes de derribar (`attacks.py`, rama `mechanic.bull-charge`) y el
motor vectorizado solo tiraba Lucky Charm. Los casos existentes siguen pasando (el defensor
de `test_bull_charge_knocks_down_on_a_successful_charge_hit` no tiene salvación). G07 debe
confirmar la corrección; si la matriz `fast`/`full` discrepa, el punto a revisar es este
dado extra.

### Desviación conocida: procedencia del seis natural

`Ravenous Onslaught` y `Killing Blow` se activan con la tirada final de impacto (`rolls == 6`),
no con la tirada original previa a un reroll. El modular usa `attacker_dice.original_roll`.
Un seis repuesto por un reroll cuenta aquí como natural; un seis original repuesto por un
fallo no. Afecta solo a portadores de esos dos rasgos (hoy rechazados por la puerta) y se
registra para G07.

## Claves principales cubiertas (propuestas para el CSV)

«Integrado» = la ruta NumPy del motor ejecuta el comportamiento en `resolve_attacks`,
`_prepare_weapon_attack` o `phase_equipment`. Ninguna se propone como `verified`.

| id | clause_id | Estado real | Propuesta |
| --- | --- | --- | --- |
| `mechanic/mechanic.ethereal-hit-save` | `four-plus-save-after-the-to-hit-roll` | Integrado (ataque ordinario y Bull Charge) | `numpy: implemented` |
| `mechanic/mechanic.ethereal-hit-save` | `magical-attacks-bypass` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/cairn-wraith--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/malignant-spirits--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/poltergeists--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/tomb-banshee--ethereal/mechanic.ethereal-hit-save` | `ethereal-save` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--haunter-of-the-dark/unimplemented.call-of-the-night-haint-mim.mourngul.haunter-of-the-dark` | `ethereal-improved` | Dato (`ethereal_hit_save` > 4) leído por la ruta; la puerta `effect-values` lo sigue rechazando | Sin cambio |
| `mechanic/mechanic.honorable` | `whole` | Integrado (pool y por ataque) | `numpy: implemented` |
| `rule/mordheim/adventurers-kaz/imperial-noble--honorable/mechanic.honorable` | `whole` | Integrado | `numpy: implemented` |
| `mechanic/mechanic.ravening-onslaught` | `whole` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/mourngul--ravening-onslaught/mechanic.ravening-onslaught` | `whole` | Integrado | `numpy: implemented` |
| `mechanic/mechanic.killing-blow` | `whole` | Integrado | `numpy: implemented` |
| `rule/mordheim/blood-dragons-mou/grave-guards--killing-blow/mechanic.killing-blow` | `whole` | Integrado | `numpy: implemented` |
| `rule/mordheim/blood-dragons-mou/wights--killing-blow/mechanic.killing-blow` | `whole` | Integrado | `numpy: implemented` |
| `mechanic/mechanic.torturer` | `torturer` | Integrado | `numpy: implemented` |
| `rule/mordheim/cursed-cavalcade/band--cursed-cavalcade-special-skills-torturer/mechanic.torturer` | `torturer` | Integrado | `numpy: implemented` |
| `mechanic/mechanic.titanic-strength` | `whole` | Integrado | `numpy: implemented` |
| `rule/mordheim/brood-of-ghurash-the-sc/band--skill-titanic-strength/mechanic.titanic-strength` | `whole` | Integrado | `numpy: implemented` |
| `mechanic/mechanic.hard-to-rattle` | `hard-to-rattle` | Integrado | `numpy: implemented` |
| `rule/mordheim/fen-guard-mim/band--hard-to-rattle/mechanic.hard-to-rattle` | `hard-to-rattle` | Integrado | `numpy: implemented` |
| `mechanic/mechanic.marine-hunter` | `whole` | Integrado | `numpy: implemented` |
| `mechanic/weapon.skull-busta` | `whole` | Integrado (yelmo 6+); el perfil es de G03 | `numpy: implemented` (coordinado con G03) |
| `mechanic/mechanic.seaguard-spear-master` | `first-round-strength-and-reroll` | F y reroll por fase integrados | `numpy: implemented` |
| `rule/mordheim/lothern-sea-patrol-sar/seaguards--spear-master/mechanic.seaguard-spear-master` | `first-round-strength-and-reroll` | F y reroll por fase integrados | `numpy: implemented` |
| `rule/catalog/warband/skill.chosen-of-the-white-tower/unclassified` | `parry-unarmed-and-reroll` | Integrado (capacidad sembrada + reroll) | `numpy: implemented` |
| `rule/catalog/warband/skill.instinctive-warrior/unclassified` | `parry-with-a-double-handed-weapon` | Integrado | `numpy: implemented` |
| `rule/mordheim/call-of-the-night-haint-mim/spirit-hosts--spectral-touch/trait.spectral-touch` | `whole` | Integrado | `numpy: implemented` |
| `mechanic/mechanic.wraith-touch` | `whole` | Resolución integrada (anulación, herida automática, curación); selector de ataque único en G06 | `numpy: implemented` |
| `rule/mordheim/restless-dead/band--restless-dead-special-skills-wraith-touch/mechanic.wraith-touch` | `whole` | Ídem | `numpy: implemented` |
| `item/spirit_knife` | `whole--scope--spectral-touch` | Integrado | `numpy: implemented` |
| `mechanic/weapon.sword-breaker` | `whole` | Integrado (rotura por fila) | `numpy: implemented` |
| `rule/mordheim/mazzalupo-web/master-of-finances--corruption/unimplemented.mazzalupo-web.master-of-finances.corruption` | `corruption--scope--attack-reroll` | Integrado con recurso de fase | `numpy: implemented` |
| `rule/mordheim/mazzalupo-web/master-of-finances--corruption/unimplemented.mazzalupo-web.master-of-finances.corruption` | `corruption--scope--psychology-immunity-limit` | Integrado (la inmunidad evita el reroll) | `numpy: implemented` |
| `item/eshin_assassin_clothes` | `behaves-as-eshin-assassin-robes` | Integrado (reroll de armadura) | `numpy: implemented` |
| `mechanic/mechanic.body-slam` | `whole` | Ya resuelto por la ruta existente (ataque completo) | Sin cambio |
| `mechanic/mechanic.bull-charge` | `whole` | Integrado con la corrección de armadura | Sin cambio de estado; nota |

Claves de apoyo de otros grupos que esta entrega alimenta sin proponer estado:
`mechanic.festooned-with-pistols` (equipo; la mitad de melé es de G06),
`weapon.count-of-ventimiglias-misericordia` (G00/G03), `condition.guiding-dream-target`
(G05/G06), `trait.wight-blades`, `trait.concussion-immune`, `trait.poison-immune` y las
inmunidades de veneno (G03), `mechanic.great-thirster` y `mechanic.deathblow` (G06).

**Claves principales sin comportamiento que portar** (no se propone cambio):
`mechanic/poison.bloodroot` (`whole`) y `mechanic/skill.strike-to-injure` (`whole`) no tienen
consumidor en el motor modular (`grep` sobre `modular/*.py` y `phases.py` sin resultados), y
`item/black_lotus`, `item/nightshade`, etc. ya los ejecuta la ruta actual.

## Conexiones pendientes y propuestas concretas

1. **G06 — equipo por fila.** En `_simulate_batch_core`, sustituir
   `first = phase_equipment(original_first, first_round=...)` por:
   ```python
   from mordheim_combat.vectorized._equipment import equipment_for_rows
   equipment = equipment_for_rows(original_first, state1, active_rows, first_round=round_index == 0)
   ```
   y usar el `CompiledFighter` de cada fila en los bucles que agrupan filas por equipo. La
   proyección ya escribe `main_weapon`, `off_hand`, `extra_attacks`, `armour_save` y
   `global_effects` por fila; no modifica el lote.
2. **Coordinador — `_types.py`.** `_parry_capacity` sigue sin leer
   `skill.chosen-of-the-white-tower` e `skill.instinctive-warrior`. Mientras siga así,
   `resolve_attacks` siembra esas paradas al abrir cada pool y marca `parry_used`, que el
   driver limpia en cada ronda; así dos pools de la misma ronda no reponen una parada
   gastada. Alternativa limpia: delegar en `_operators.parry_capacity` (ya lo hace la capa de
   ataque) también desde el driver.
3. **Coordinador — puerta NumPy.** Retirar de `kernel.NUMPY_PENDING` solo cuando G07 haya
   comparado: `mechanic.torturer`, `mechanic.titanic-strength`, `mechanic.ethereal-hit-save`,
   `mechanic.honorable`, `mechanic.ravening-onslaught`, `mechanic.marine-hunter`,
   `mechanic.hard-to-rattle`, `trait.spectral-touch`, `mechanic.weapon.sword-breaker`,
   `armour.eshin-assassin-robes`, `mechanic.wraith-touch`, `mechanic.seaguard-spear-master`,
   `mechanic.corruption` y el comportamiento `"killing-blow"`. Mantener
   `mechanic.festooned-with-pistols` (hasta G06) y `effect-values` (ethereal mejorada +
   `critical_threshold` + armadura natural ante fuego). `NATIVE_PENDING` no se toca.
4. **G07 — comparación dirigida.** Verificar el orden de dados del Bull Charge, de la herida
   extra de Spectral Touch (antes de la herida propia), del reroll de Eshin (solo cuando la
   salvación falla) y de los rerolls de fase (Seaguard y Corrupción consumen un dado por
   fila). Ambos leen ya `not hit.rerolled` como el modular, así que un dado repetido por Odio
   o Luck no se repite. La procedencia del seis natural ya no es una desviación:
   `PreparedAttack.natural` conserva la cara física.
5. **G06 — selector de Wraith Touch.** En el driver, antes de `attack_count`, replicar
   `rounds.py::select_attack_replacement`: con `decisions.choose("<key>.wraith-touch")`,
   sustituir el arma principal por
   `EffectSet(tags=("weapon.fist", "effect.wraith-touch", "effect.no-critical"), strength_bonus=-1, target_armour_bonus=1)`
   y vaciar manos secundarias y ataques extra. La resolución ya está portada en esta capa
   (anulación contra No Muertos/Poseídos, herida automática y curación del Liche), así que el
   selector es lo único que falta para cerrar la clave.
   El mismo hook de ronda cubre `skill.shifty`, `skill.crude-belch-halfling`, `dance.*`,
   `mechanic.great-thirster`, `trait.spines` y la trampa de `mechanic.centaur-trample`: todos
   viven en `modular/rounds.py` y no en ataque individual.
6. **G05/G03 — sin cambios solicitados.** No se necesitó ninguna firma nueva de `_operators`;
   los perfiles de G03 (`arcane-candelabrum`, `brazier-iron`, `misericordia`, `draich`,
   `spirit-knife`) no se tocaron.

## Comandos ejecutados y resultados

```text
# Línea base antes de editar (misma base local):
python -m pytest tests/python/combat/vectorized -q --no-header -p no:randomly
  -> 14 failed, 98 passed   (los 14 ya fallaban; catálogo/compilación/puerta)

# Pasada intermedia, ignorando el archivo que G03 estaba reescribiendo en ese momento
# (test_rule_families_b.py, error de colección ajeno):
python -m pytest tests/python/combat/vectorized -q --no-header -p no:randomly \
  --ignore=tests/python/combat/vectorized/test_rule_families_b.py
  -> 12 failed, 103 passed

# Suite completa tras conectar contextos y recursos (sin --ignore):
python -m pytest tests/python/combat/vectorized -q --no-header -p no:randomly
  -> 14 failed, 114 passed
     Los 14 son ajenos a esta capa y ya fallaban en la base: 3 de test_rule_families_a,
     2 de test_rule_families_b (catálogo/construcción), test_frantic_priority_score...,
     7 de test_shared_families (catálogo, familia, black hunger, contratos de compilación)
     y test_random_profile_characteristics... . test_arms_master_censer_bearer... pasó a
     fallar por elegibilidad de skills (`skills are not available to
     pit-fighters/ogre-pit-fighter`), causado por los cambios concurrentes de catálogo en
     `sources/knowledge`; no llama a ninguna función editada aquí.

# Comprobantes nuevos:
python -m pytest tests/python/combat/vectorized/test_shared_families.py -q -p no:randomly \
  -k "phase_resources or ethereal or wound_reactions or parry_and_armour or honorable or equipment_loss"
  -> 6 passed, 16 deselected

# Corrección posterior: los rerolls de fase respetan `not hit.rerolled`.
python -m pytest tests/python/combat/vectorized/test_shared_families.py -q -k "phase_resources"
  -> 1 passed
# Con las dos máscaras antiguas restauradas a mano, el mismo comprobante falla:
  -> Seaguard repetía el dado de Odio (1 -> 1 -> 6 impactaba y gastaba el recurso).

# Núcleo del motor (sin los archivos ajenos en escritura):
python -m pytest tests/python/combat/vectorized/test_vectorized_engine.py \
  tests/python/combat/vectorized/test_runtime_regressions.py -q -p no:randomly
  -> 2 failed, 63 passed   (solo los dos fallos previos conocidos)

# Verificación directa de cada comportamiento nuevo (script puntual sobre la API vectorial):
ethereal save 6 -> sin herida; save 3 -> herida
killing blow (seis + "1" de herida) -> 3->2 heridas; sin la clave -> sin herida
torturer -> F 3->2 y torture_strength_loss=1
titanic S test 6 -> KNOCKED_DOWN; S test 1 -> STANDING
marine hunter -> daño ×2
hard to rattle -> KNOCKED_DOWN donde sin la clave queda STUNNED
seaguard lanza 1.ª ronda -> F 4 frente a 3 sin la clave
ravening onslaught -> 2 preparaciones con seis; 1 sin la clave
honorable vs Derribado -> 0 heridas, ninguna preparación
spectral touch -> herida extra automática por seis natural (aserción en test)
eshin robes -> reroll de la salvación fallida; sin robes la misma tirada hiere
sword-breaker -> parada a 4+ rompe la mano atacante; espada normal no la rompe
white tower -> dos pools en la misma ronda no reponen la parada gastada
wraith touch -> herida automática sin dado de herida; contra No Muerto el ataque es nulo
seaguard -> impacto fallido 3 rerolado a 6 y recurso gastado
corruption -> impacto 6 rerolado a 1; sin la regla el mismo 6 hiere
KB + Mark of the Old Ones, tirada física 1 -> 3 heridas (antes 2: se leía el 6 concedido)
KB, tirada física 6 -> 2 heridas (herida automática)
guiding dream (resultado 2) vs Héroe, tirada física 3 -> impacto y daño; sin el sueño, fallo
equipo: pistola 2.ª ronda -> puño; festooned -> mace con concussion;
        mano rota con reserva -> slot backup.0; fila 0 conserva main, fila 1 backup.0

sha256(sources/knowledge/verification/clause-contracts.csv)
  -> b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731  (sin cambios)
```

Comprobaciones **no** ejecutadas: campaña de paridad G07, matrices `fast`/`full`, benchmark
G08, E2E completo, y lint (`ruff` no está instalado en el entorno; `python -m ruff check`
responde `No module named ruff`). La suite completa de `tests/python/combat` no se usó como
evidencia por la escritura concurrente de G03/G05 en la misma copia.

## Casos nuevos y justificación

1. `test_ethereal_hit_save_and_killing_blow_intercept_the_hit` — la defensa etérea y la
   herida automática de Killing Blow no tenían comprobante vectorial; el caso distingue
   «salvado» de «herido» y «sin tirada de herida» de «tirada fallida».
2. `test_wound_reactions_weaken_and_knock_down_their_own_row` — agrupa las reacciones
   portadas en el mismo punto del código (Torturer, Titanic Strength, Hard to Rattle,
   Spectral Touch y Wraith Touch); cada aserción compara contra el mismo escenario sin la
   clave, y Wraith Touch añade el caso No Muerto en el que el ataque debe ser nulo.
3. `test_parry_and_armour_corrections_follow_the_modular_contract` — el reroll de las Eshin
   robes, la rotura del Sword-breaker y la parada sin arma del White Tower son correcciones
   silenciosas (no cambian el daño esperado, sí el dado que lo decide); el caso fija las tres
   con un RNG guionizado y añade el segundo pool de la misma ronda para probar que la parada
   concedida no se repone.
4. `test_honorable_skips_helpless_targets_and_onslaught_extends_the_pool` — la composición
   del pool (Honorable y Ravenous Onslaught) no se distingue por el daño final; se cuenta la
   preparación de ataques, como ya hace el test existente de Body Slam.
5. `test_equipment_loss_and_festooned_pistols_are_projected_per_row` — el módulo de equipo
   es nuevo en su forma actual; comprueba reserva, club del Festooned y que la mano rota de
   una fila no altera la otra.
6. `test_phase_resources_reroll_one_hit_per_row` — Seaguard y Corrupción gastan un recurso
   de fase cada uno; el caso fija el dado y comprueba el gasto. Se prefirió un escenario
   propio a esconderlo en el de paradas porque aquí el resultado depende del recurso, no del
   arma. Se amplió con un dado ya repetido por Odio (`skill.hatred`): 1 → 1 no habilita el
   reroll del Seaguard y 1 → 6 no habilita el de Corrupción, porque el modular exige
   `not hit.rerolled` en ambos. Antes de la corrección, el motor NumPy repetía el dado una
   tercera vez e impactaba (o gastaba la Corrupción), gastando el recurso que el modular
   conserva.

No se añadieron pruebas por cláusula, no se copiaron E2E y no se ejecutó una matriz de
paridad.

## Bloqueos y limitaciones

- **Recursos de fase (Seaguard y Corrupción)**: resueltos añadiendo `seaguard_used` y
  `corruption_used` a `CombatState` (`_types.py`), inicializados en `_new_state` (`_state.py`)
  y limpiados por ronda en `_simulate_batch_core` (`_driver.py`). Esos tres ficheros eran de
  G02/G06; se editaron por coordinación explícita del encargo para poder conectar el consumo.
  El coordinador debe revisar el diff de esos tres ficheros al integrar la tanda.
- **Chosen of the White Tower / Instinctive Warrior**: el driver sigue sembrando
  `parry_remaining` con `_types._parry_capacity`, que no conoce estas dos skills; por eso la
  siembra se hace al abrir cada pool en `resolve_attacks` y se marca en `parry_used`. El
  marcador se reutiliza como «concedido en esta fase», no como «gastado»: si el coordinador
  prefiere mantener el contrato en `_types.py`, esta rama puede retirarse.
- **Equipo por fila**: la proyección y la regla son reutilización literal del modular y están
  probadas, pero el driver aún llama `phase_equipment` una vez por lote. Hasta la propuesta 1,
  una mano rota, una transformación o una marca no cambian el ataque de esa fila.
- **`trait.spectral-touch`**: portado reutilizando `_prepare_weapon_attack` con
  `effect.automatic-wound` + `automatic_hit` (sin tirada de impacto nueva) y resolviéndolo
  antes del paso de herida propio, como el modular. No se construyó una segunda ruta de
  resolución. El ataque extra comparte el `cannot_be_parried` del modular; si G07 encuentra
  un caso con parada previa que sobrevive al seis, el punto a revisar es el filtro `alive`.
- **Reacciones de G06**: Great Thirster (frenesí al sacar de acción), Deathblow, Shifty,
  Crude Belch, las danzas y Spines pertenecen al encargo de rondas; no se tocaron.
- **Contextos de G03 conectados**: `hit_context`/`hit_targets`/`hit_reroll` (impacto),
  `wound_context` (herida), `parry_context`/`parry_capacity` (parada) y `injury_conditions`
  (lesión) sustituyen los cálculos duplicados. `armour_targets` ya era el operador de G03.
  Con ello llegan Guiding Dream, Estalian/Darting Steel, Cold Steel, Hellblade y los
  modificadores de impacto que la copia propia no tenía.
- **Procedencia del seis natural**: `PreparedAttack.natural` conserva la cara física antes de
  que Mark of the Old Ones sustituya la tirada por el número objetivo; Killing Blow, Black
  Lotus, Wight Blades, Spectral Touch, Ravenous Onslaught y el seis imparable de la parada
  leen ese valor, no el sustituido.
- **`poison.bloodroot` y `skill.strike-to-injure`**: sin consumidor modular; no hay
  comportamiento que portar sin reinterpretar reglas.
- **`mechanic.wraith-touch`**: la resolución está portada y probada; el ataque único sigue
  esperando el selector de G06 (propuesta 5).
- No se ha escrito el CSV ni se han hecho commits/pushes.

## Anexo — cobertura real del anexo de claves (no es paridad)

Recuento del propio fichero G04: **280 filas principales** (260 `id` distintos) y 57 de
apoyo. Esta entrega **no** cierra las 280. Triaje sobre las filas con etiqueta derivable del
`id` (181 filas, 57 etiquetas distintas):

- 74 filas cuya etiqueta ya aparece en la ruta vectorizada (antes de esta entrega, más las
  portadas aquí).
- 107 filas cuya etiqueta no aparece literalmente en `vectorized/`. La mayoría **no es un
  hueco**: el compilador normaliza `trait.poison-immune` (63 filas), `trait.thick-skull`
  (15), `trait.flammable`, `trait.injury-profile`, `defence.helmet`,
  `defence.wolf-pelt-cloak`, etc. a campos numéricos/booleanos del `EffectSet`
  (`poison_immunity`, `thick_skull`, `helmet_save`, `ward_save`, `acid_blood`,
  `wight_blades`) que la ruta sí consume.
### Revisión de las filas sin etiqueta literal (antes «99 sin revisar»)

Se agruparon **todas** las filas del anexo por el binding compilado (`effect_id` del CSV) y
por el consumidor modular, no por el texto del `id`. Resultado del agrupamiento (una fila
puede repetir binding; los recuentos son filas):

| Familia de reutilización | Filas | Justificación |
| --- | ---: | --- |
| `poison_immunity` (compilado) | 72 | `trait.poison-immune`, `preparation.tears-of-shallaya` → campo booleano; `wound_context` lo lee |
| `skill.thick-skull` (compilado) | 16 | `thick_skull` + `helmet_save`; reacción de yelmo en `_resolve_weapon_once` |
| `frenzy` (compilado) | 13 | `trait.frenzy`/`campaign.condition.frenzy` → `frenzy` de `CombatState` |
| `helmet_save` / `ward_save` (compilado) | 12 | `defence.helmet`, `cooking-pot-helmet`, `wolf-pelt-cloak` → campos numéricos |
| `mechanic.undead`, `psychology-immunity`, `fear-immunity` | 10 | Etiquetas consumidas por `hit_context`/`wound_context` y por las inmunidades |
| `strike-to-injure`, `injury_profile`, `flammable`, `acid_blood`, `wight_blades`, `concussion_immune`, `survivor`, `critical_injury_bonus`, `characteristics`, `bear_hug`, `caught-fire`, `injury_reroll_out`, `ethereal` mejorada | 26 | Campos del `EffectSet`/`CombatState` leídos por la ruta (varios ya lo eran antes de esta entrega) |
| `rounds.py` (Shifty, Crude Belch, danzas, Great Thirster, Spines, trample, Wall of Steel, rememberer) | 24 | Fuera de G04: hooks de ronda de G06 (propuesta 5) |
| `equipment.py` (transformación, restricciones de perfil) | 5 | Regla ya reutilizada por `_equipment.py`; la proyección por fila espera G06 |
| `weapon.*` de perfil (spirit-knife, arcane-candelabrum, brazier-iron, misericordia, draich, barbed-whip) | 8 | Perfiles compilados de G03/G00; el ataque los consume cuando la puerta los admite |
| `proposed.*` | 6 | Filas de contrato sin binding ejecutable; no son comportamiento |

Bindings residuales **sin consumidor en la copia** tras la revisión: `poison.bloodroot` y
`skill.strike-to-injure` (sin consumidor ni en el modular), `defence.eye-pendant` (G06,
`prepare_special_save_context`), `defence.magic-acorn` y `mechanic.mantle-of-crows`
(soporte de G05/G03), `condition.rememberer-*` (G06) y `mechanic.veskit-no-pain`
(mapeo de catálogo a `skill.ignore-pain`, no a un tag ejecutable). Ninguna de ellas es una
regla de ataque, equipo o reacción de esta capa.

En resumen: **no quedan filas del anexo sin justificar**; las que no ejecuta esta capa
tienen dueño explícito o son datos compilados. La entrega de G04 está completa en sus
ficheros y ninguna clave se propone `verified` (eso es G07).

## Distinción implementado / integrado / comprobado

- **Implementado**: equipo por fila, salvación etérea, Honorable, Ravenous Onslaught,
  Killing Blow, Spectral Touch, Torturer, Titanic Strength, Hard to Rattle, Marine Hunter,
  Skull Busta, fuerza y parada del Seaguard, capacidad/reroll del White Tower e Instinctive
  Warrior, reroll de las Eshin robes, rotura del Sword-breaker, Wraith Touch y salvación de
  armadura del Bull Charge.
- **Integrado en la ruta NumPy**: todo lo anterior salvo la proyección de equipo por fila
  (espera la llamada de G06) y el selector de ataque único de Wraith Touch (G06).
- **Comprobado**: los seis casos nuevos, la verificación directa de cada comportamiento
  (incluidos los dos escenarios reportados: Guiding Dream y Killing Blow con Mark of the Old
  Ones) y las suites enfocadas sin regresiones nuevas. **No comprobado**: paridad modular
  (G07).
