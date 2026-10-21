### 4.4 Catálogo de obligaciones y variantes

> **Corrección de la revisión 3.** Las etiquetas «other … rules» desaparecen del
> CSV. Cada fila es un contrato admitido, no una familia ni un consumidor
> compartido. Una clave tiene una sola variante primaria; las obligaciones
> secundarias se declaran en §4.4.2. Las claves exactas están en
> `P00-results/behaviour-inventory.csv`; aquí se justifica la agrupación y se fija
> el criterio. Recuento: **1914 claves, 63 variantes, 0 genéricas**.

#### B00 — Enrutado del registro (8 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B00.1 clave registrada sin operador de ejecución | 8; consumidor solo `MODULAR_TAG_CONSUMERS`/`require_optimized_support`; no hay contrato de duelo que agrupar | Ninguna: no se ejecuta duelo | La clave existe y resuelve a un consumidor vivo; ausencia: `consumer=[]` → `unlocated`, no `PASS` | `consumer`/`clause_scope`; criterio: resuelve a un consumidor o queda `UNLOCATED` | `verification/consumers.py`; 36/37 F00 con E2E | G01 registro; 189 `unlocated` de localización |

#### B01 — Estado inicial y recursos (54 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B01.1 perfil y características | 13; `profile.*`, `mechanic.disability` (solo penalización permanente), `mechanic.inconsistency`, `hireling.dramatis.marquand`; comparten estado inicial compilado | `FighterBuild` con perfil, características, defecto o referencia de perfil | Inicio del duelo; ausencia: misma construcción sin el campo | Campos iniciales por fila (características, arma, defecto); igualdad de campos, no resultado | E2E `initial_state`; `contract_probe.py` | G00/G02 inyección; G06 campos iniciales |
| B01.2 gasto de recurso | 15; `luck`, `force-of-will`, `mark-of-the-old-ones`, `lucky-charm`, `ranalds-luck`, `snorri-lucky`, `augur-*`; todos son recursos de un solo uso | Portador con recurso y `decisions` para gastarlo | Evento que consume el recurso; ausencia: no gastar | Recurso gastado por fila (contador/booleano); no se infiere de heridas | `test_duel_replay.py` compara recursos; el oráculo por lotes no los publica | G06 publicar recursos; G02 exportar arrays |
| B01.3 condición o preparación inicial | 21; `condition.*`, `preparation.*` y `mechanic.snorri-drunk`; la condición se suministra antes del duelo | `FighterBuild`/`initial_state` con la condición; el control usa la misma construcción sin ella | La condición existe al inicio; ausencia: caso pareado sin condición | Condición/estado inicial por fila; presencia y efecto directo, no «no pasó nada» | E2E `initial_state`/`duel_context`; `mechanic.snorri-drunk` usa `snorri_drunk_result` | G00/G02; el negativo necesita control positivo |
| B01.5 carga o restricción de ataque obligatoria | 3; `mechanic.shallya-strictures`, `mandatory-charge`, `witch-finder--compulsory-charge`; son restricciones de elección suministradas, no radio de liderazgo | `FighterBuild`/`duel_context` con la restricción y el objetivo/identidad que la activa | Inicio de la carga o declaración de ataques; ausencia: objetivo permitido o sin restricción | Objetivo/orden de carga por fila; criterio: la restricción cambia la elección, no un resultado terminal | E2E initial_state; no hay operador exacto | G00/G02 entrada; G06 estado por ronda |
| B01.6 característica aleatoria o avance | 2; `profile.random-characteristics` y `advancement-lift`; ambos modifican el valor inicial antes de usarlo | Valores iniciales suministrados o tirada por turno declarada | Uso de la característica; ausencia: valor fijo equivalente | Valor inicial/por turno por fila; igualdad de campo, no resultado | E2E condemned--inconsistency | G00/G02 valores; G06 tirada por turno |

#### B02 — Impacto (204 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B02.2 hatred y modificadores de primer asalto | 95; `hatred-*`, `devoted-killer-hatred`, `berserker`, `ferocious-charge`, `bestial`; todos rerollean/aciertan solo contra una identidad o primer asalto | Atacante con hatred/regla, objetivo de la identidad correcta, primer asalto o carga | Se declara el objetivo y el asalto; ausencia: objetivo no odiado o asalto posterior | `hit-modified`/`reroll-used` por ataque; no heridas ni condición terminal | E2E hatred/berserk; no hay comprobación exacta de modificadores | G03/G06 testigo por ataque |
| B02.3 reroll de impacto y defensa | 56; `_hit_reroll`, `expert-swordsman`, `duellist`, `amazon-isolationists`; todos repiten un impacto fallido | Arma/defensa que permite repetir; atacante/defensor declarados | El primer impacto falla y se repite; ausencia: sin reroll | `reroll-used` o `hit-modified` por ataque; la repetición ocurre una vez y solo con la regla | E2E parry/reroll; sin comprobación exacta | G03/G06 |
| B02.4 modificadores generales de impacto | 53; resto de impacto, incluidas armas con bonus de impacto y `command.follow-me`; comparten objetivo de impacto | WS, modificadores, cobertura/contexto y arma declarada | Aplicación del modificador; ausencia: mismo combate sin él | `hit-modified`/objetivo de impacto por ataque; diferencia en el impacto, no en heridas | Fixtures semánticos; E2E | G03/G06 |

#### B03 — Herida, fuerza y daño (217 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B03.2 veneno e inmunidad | 99; `poison.*`, `trait.poison-immune`; el veneno modifica la tirada de herida, la inmunidad la elimina | Arma envenenada o inmunidad; T del defensor | Impacto que hiere; ausencia: inmunidad o sin veneno | `wound-modified` por ataque; el veneno no se infiere de una herida terminal | E2E de veneno; fixtures semánticos | G03/G06 |
| B03.3 modificadores de fuerza | 77; `_attack_strength`, `mighty-biceps`, `iron-sinews`, `strongman`, `titanic-strength`, `monster-slayer`, armas con S+; `strongman` además B10.1 | Fuerza efectiva y arma; la regla debe estar en el build | Ataque con la bonificación; ausencia: misma arma sin la regla | `strength-modified`/objetivo de herida por ataque; cambia la fuerza, no solo el resultado | Fixtures de fuerza; la tabla exacta no ejerce modificadores | G03/G06 |
| B03.4 reroll y daño | 38; `prepare_wound_context`, `_resolve_wound_damage`, daño múltiple; todos repiten o cambian el daño | Contexto de herida/daño y arma especial | Herida que se repite o daño múltiple; ausencia: sin la regla | `wound-modified`/daño por ataque | Fixtures de herida; E2E | G03/G06 |
| B03.5 daño condicional (fuego, flammable, crítico) | 3; `trait.flammable`, `weapon.brazier-iron`, `weapon.arcane-candelabrum`, `caught-fire`; comparten disparador de fuego | Defensor `flammable` o arma de fuego; ambos materializados | Impacto de fuego; ausencia: sin fuego o sin flammable | `on-fire`/`wound-modified` por ataque; el doble daño solo con fuego | E2E flammable | G03/G06 |

#### B04 — Armadura (142 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B04.1 armadura, escudo y penetración | 78; `armour.*`, `defence.*`, armas/materiales con modificador de save; todas resuelven la tirada de armadura | Armadura/escudo, fuerza, penetración y ataque mágico | Tirada de armadura; ausencia: sin armadura o `ignore_armour` | `armour-save-rolled`/save por ataque; la rejilla base solo cubre default/light/heavy/gromril+shield | Exacta `armour`; cada efecto adicional necesita su fila | G03/G04 ampliar rejilla |
| B04.2 armadura natural: stacks, worst, unmodified | 60; `trait.natural-armour-*`; comparten el campo natural y sus modificadores | Defensor con `natural_armour_save`, `stacks`, `worst`, `unmodified`; fuerza variable | Tirada de armadura; ausencia: sin natural armour | Save natural por ataque; 6+ vs 5+, tope 6, no modificación por fuerza | 98 `shared-operator`: la rejilla `armour` no incluye estos campos | G03/G04 filas de rejilla |
| B04.3 buckler no mejora armadura | 4; `defence.buckler`, `counts-as-buckler/shield`; la mejora de armadura es distinta de la parada | Defensor con buckler y atacante | Tirada de armadura; ausencia: sin buckler | Save de armadura sin bonificación; la parada va a B06.2 | 98 `shared-operator`; no hay variante en `armour` | G03/G04 |

#### B05 — Save especial (81 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B05.1 ward, step-aside, ethereal | 54; `ward-save`, `step-aside`, `elven-agility`, `vampire-reflexes`, `ethereal`, `warpaint`, `dance.the-shadows-coil`, `mechanic.bestial`; todas son saves especiales | Defensor con save especial y valor; ataque mágico/mundano si aplica | Herida no salvada por armadura; ausencia: sin save o ataque que lo ignora | `special-save-rolled`/resultado por herida | E2E; no hay comprobación exacta | G03/G06 |
| B05.2 regeneración y bloqueos | 27; `regeneration*`, `regeneration-four-plus-blocked-by-fire`; el save se resuelve por herida, la recuperación es B15.2 | Defensor con regeneración 5+/6+; fuego/bendito como bloqueo | Herida no salvada; ausencia: bloqueo o sin regeneración | `special-save-rolled` por herida; la recuperación va a B15.2 | E2E; sin comprobación exacta | G03/G06 |

#### B06 — Parada (125 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B06.1 intento de parada | 62; `weapon.sword`, `cutlass`, `rapier`, `buckler`, `sword-master`, armas con parada; todas ofrecen un intento | **Defensor** con arma de parada; atacante cuerpo a cuerpo | Ataque que puede pararse; ausencia: sin arma de parada, a distancia o negación | `parried` por ataque; no heridas/condición terminal | E2E `core/combat-parry::sword-parries-one-hit`; P01 q04 | G06 array `parried`; hoy solo la reproducción exacta lo expone |
| B06.2 reroll y capacidad | 34; `sword-master`, `unbeatable-warrior`, `miniath`, `shield-mastery`, `defensive-stance`, `buckler`, armas de dos paradas | Defensor con espada+buckler/maestría; varias rondas | Primera parada fallida; segunda oportunidad; ausencia: sin reroll/capacidad | `parried` y capacidad consumida por ataque/ronda | E2E `sword-and-buckler-reroll`; P01 c04 debe poner el buckler en el defensor | G06 |
| B06.3 negación y armas especiales | 29; `crushing-blow`, `beastlash`, `spiked-gauntlet`, `trident`, `sword-breaker`, `iron-fan`, `war-maul`; todas niegan la parada | Atacante con negación; defensor con parada | Ataque que niega la parada; ausencia: ataque normal | `parried=false` por ataque | E2E | G06 |

#### B07 — Lesión (222 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B07.1 tabla e inmunidades | 170; `ignore-pain`, `hard-to-kill`, `concussion-immune`, `thick-skull`, `tough-as-steel`, `injury-profile`, `fragile`, `survivor`, `veskit-no-pain`, `command.art-thou...`; todas cambian la tabla o el umbral | Defensor con la inmunidad/umbral; herida no salvada que reduce a 0 | Tirada de lesión; ausencia: sin la inmunidad | `condition` como **resultado directo** de la lesión (`direct-result`); banda 1–2/3–4/5–6 y borde exacto | E2E chart; la comprobación `injury` es defectuosa (§4.3) | P03 corregir `injury`; G06 secuencia por herida |
| B07.2 resultado más alto y heridas múltiples | 4; `core/combat-injury-states::highest-result`, `proposed.core.combat-critical-hits`, `web-of-steel`; comparten varias tiradas en la misma fase | Dos heridas no salvadas en la misma fase; estado inicial declarado | Segunda tirada de lesión; ausencia: una sola herida | `condition` final = peor resultado; se conserva el peor, no el último | E2E `highest-injury-result-applies`; **P01 c04-highest-injury cita una identidad inexistente** | G06 secuencia; P01 corrige la identidad |
| B07.3 modificadores de lesión por arma | 48; `weapon.*`, `material.*`, `dance.whirling-death`, `inured-to-pain`, `mace`; todos modifican la tirada de lesión | Arma/regla con modificación (maza/concusión, etc.) | Herida que reduce a 0; ausencia: sin el modificador | `condition` por herida; la condición terminal vale para la lesión, no para el impacto | E2E por arma; P01 c04 | G06 |

#### B08 — Pool de ataques (82 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B08.1 recuento base, mano torpe y pistola | 3; `proposed.core.combat-two-weapons`, `weapon.pistol`, `weapon.sun-gauntlet`; comparten el reparto de ataques por mano | Arma principal/mano torpe/pistola; `first_round`/`charging` | Construcción del pool; ausencia: sin mano torpe o sin la pistola | `attack-count` por ronda; la rejilla exacta cubre el ataque extra de dos armas | Exacta `attack-pools` | G03/G06 recuento por ronda |
| B08.2 ataques extra y frenesí | 60; `frenzy`, `extra-attack`, `red-fury`, `frantic`, `charge-attack`, `sabretusk`, `art-of-silent-death`, `inspiring-sermon`, `web-of-steel`, `spiked-tail`, `bagh-nakh`, `shield-strike`, `centaur-trample`, `emissary-khorne`; todos añaden un ataque | Arma/skill de ataque extra; carga/primer asalto; `frenzy` | Construcción del pool; ausencia: sin la regla o sin carga | `attack-count`; +1 solo con la regla; `frenzy` ya tiene variante exacta, las demás no | 98 `shared-operator`; `attack-pools` solo cubre `frenzy` y dos armas | G03/G04 rejilla de recuento |
| B08.4 combate sin armas y ataques naturales | 6; `skill.unarmed-fighting`, `unarmed-without-penalties`, `weapon.fist`, `ogre-unarmed`, `profile.fist`, `unarmed-penalty-waiver`; comparten la ausencia de penalización y el ataque natural | Combatiente sin arma o con ataque natural; manos declaradas | Construcción del pool; ausencia: arma ordinaria | `attack-count` y fuerza sin penalización | 98 `shared-operator`; no hay fila de desarmado | G03/G04 |
| B08.5 sustitución de ataque o modificación del pool rival | 13; `weapon.vomit-attack`, `tentacle`, `giggle-juice-spray`; sustituyen un ataque propio o reducen uno rival, no añaden otro | Portador con la regla y decisión de sustituir/reducir; arma declarada | Fase de close combat; ausencia: ataque ordinario o sin la regla | `attack-count`/sustitución por ronda; el ataque sustituido no se suma | E2E vomit/tentacle/giggle-juice | G03/G04 |

#### B09 — Equipo (19 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B09.1 restricciones de equipo | 5; `profile.equipment-restrictions`, `disability` (sin dos armas/escudo), loadout variable; se resuelven en compilación | Compilación/validación del loadout | Construcción; ausencia: loadout legal | Perfil compilado; acepta/rechaza, no duelo | Tests de compilador; 3 claves de §4.6 se resuelven aquí | P01 (caso de construcción); sin duelo: `INCOMPATIBLE:construction` |
| B09.2 pérdida/transformación intra-duelo | 4; `bitten-transform`; el equipo cambia durante el duelo | Estado inicial con transformación; arma/armadura perdida | Evento de transformación; ausencia: sin transformación | `equipment` (hash) por fila; criterio: hash distinto del control, no «cero» | E2E `the-bitten--transform` | G02/G06 |
| B09.3 red, látigo y estado de arma | 10; `condition.netted`, `netter`, `beastlash`, `barbed-whip`, `duelling-pistol`, `eye-pendant`, `hillman-lycanthrope`, `ogre-unarmed`; comparten estado de arma/equipo | Portador de red/látigo; impacto | Impacto de red/látigo; ausencia: sin red | `netted`/estado de arma por fila | E2E netter/beastlash | G05/G06 |

#### B10 — Ronda y orden (108 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B10.1 prioridad y orden | 7 del denominador; `combat-order`, `pike`, `quarter-staff`, `woven-mist`, `yari-two-handed`, `shifty`; además 31 `shared-operator` en §4.6 | Iniciativa, carga/cargado/levantado; armas y skills | Inicio de ronda; ausencia: sin la regla de prioridad | `acting-order` por ronda; **categoría 0/1**, no contador: el criterio es igualdad con la categoría declarada, no `>0` | Exacta `priority`; las 98 se revisan en §4.6 | G03/G06 estado y orden por ronda |
| B10.2 levantarse y recuperación | 8; `stand-up`, `jump-up`, `helmet`, `cooking-pot-helmet`; comparten la recuperación de la condición | Defensor derribado/aturdido al inicio; ronda siguiente | Levantarse; ausencia: no derribado | `condition` como resultado directo de la recuperación; golpea después de levantarse | E2E `recovery-belongs-to-the-fighters-own-turn`; P01 c04 no declara el estado | G06 estado por ronda |
| B10.3 muerte súbita: decisión | 2; `mechanic.death-blow`; una decisión cambia el ataque | Portador con la regla y `decisions` para aceptar/rechazar | Ataque con la regla; ausencia: decisión de rechazo | `attack-count` + decisión aplicada; si falta, `NOT_RUN:decision-script` | E2E `death-blow::the-bearer-declines` | P01 declara la clave; P02 traduce `ScriptedDecisions` |
| B10.4 estado y modificadores por ronda | 91; efectos resueltos por `resolve_round` (clima, terreno, estados, `command.art-thou...` secundario); comparten el cierre de ronda | Estado por ronda, modificadores, clima/terreno | Inicio/cierre de ronda; ausencia: sin el estado | Estado/orden por ronda; el modificador aparece en la ronda declarada | E2E `expect_rounds`; no hay adaptador `round` | G06 estado por ronda |

#### B11 — Miedo y psicología (368 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B11.1 causa miedo y tirada | 211; `causes-fear`, `fear-of-*`, `undead`, `beastlash`, `trait-fact` (fear-causing/undead), `living` (psicología normal); todos alimentan la causa o la prueba | Causante de miedo y unidad cargada; liderazgo del que prueba | Carga/prueba de miedo; ausencia: sin causante | `fear-hit-sixes` por fila; el que falla impacta solo a 6; no se infiere de heridas | E2E minotaur; cero operación semántica | G05 ejecutar miedo; G06 publicar |
| B11.2 inmunidad plena a miedo | 23; `mechanic.fear-immunity`, `ere-we-go` no entra aquí; **no se toma la prueba de miedo** y las demás pruebas siguen. `mechanic.cold-blooded-psychology` **no** está aquí: la prueba se hace y se descarta el dado mayor (B11.5) | Inmune + causante de miedo; control sin inmunidad | Carga/prueba; ausencia: sin inmunidad | `fear-test-skipped` (bandera) o `fear-hit-sixes` ausente; **no** se exige ausencia de toda tirada de psicología | E2E inmunidad; no hay operador exacto | G05/G06; control positivo con el mismo causante |
| B11.3 inmunidad completa a psicología | 103; `mechanic.psychology-immunity`, `witch-finder--inquisitor-state`; **no se toma ninguna prueba de psicología** (incluye miedo, hatred, frenesí, estupidez) | Inmune y prueba de psicología aplicable; control sin inmunidad | Prueba de psicología; ausencia: sin inmunidad | `psychology-test-skipped` (bandera); no usar `fear-hit-sixes` como único testigo | E2E inmunidad; no hay operador exacto | G05/G06; control positivo |
| B11.4 inmunidad condicional a miedo | 6; `accustomed-to-fear` (solo Vampiro/Esqueleto/Espíritu), `fear-immunity-undead-chargers` (solo cargante no-muerto), `ere-we-go` (solo al cargar); **la condición forma parte del contrato** | Inmune condicional + enemigo que cumple la identidad/condición; control con enemigo que no la cumple | Carga/prueba; ausencia: enemigo fuera de la condición | `fear-test-skipped` solo con la condición; el control negativo debe seguir tirando | E2E accustomed/undead-chargers | G05/G06; dos controles: condición y fuera de condición |
| B11.5 sangre fría psicológica (3D6, conservar 2) | 6; `mechanic.cold-blooded-psychology`; **la prueba se hace**: se tiran 3D6 y se descarta el mayor | Portador con la regla y prueba individual de psicología | Prueba de psicología; ausencia: sin la regla | `psychology-dice`/`fear-test-dice` (contador o resultado de dados): 3 dados y descarte del mayor; **no** ausencia de la prueba | `leadership.py::resolve_local_leadership` aplica la convención (`discard_highest`); E2E | G05/G06; testigo de dados, no `fear-hit-sixes` |
| B11.6 reroll y modificadores de miedo | 15; `fear-reroll`, `craven`, `opposite-sex`, `slaanesh`, `ghostly-howl`; todos modifican o repiten la prueba de miedo | Regla de reroll/modificador; prueba fallida | Tirada fallida; ausencia: sin regla | `reroll-used`/`fear-test-modified` por fila | E2E | G05/G06 |

| B11.7 frenesí condicionado por evento | 4; `mechanic.devoted-to-the-vampire` (frenesí mientras el vampiro seguido está derribado o muerto; además odio contra el asesino, B02.2) y `mechanic.great-thirster` (frenesí tras sacar de acción al enemigo); ambos se pierden al quedar derribado, aturdido o fuera de acción | Portador con la regla; vampiro seguido o enemigo en el estado declarado (Devoted) o enemigo que sale de acción (Thirster) | Cambio de estado de psicología en la fase de combate o tras la baja; ausencia: vampiro en pie o enemigo no fuera de acción | Bandera `frenzy` (y `devoted_frenzy`) por fila; criterio: falsa→verdadera con el disparador y verdadera→falsa con la condición de pérdida; no es una prueba ni una recuperación | E2E devoted/great-thirster; `rounds.py:639-655`, `aftermath.py:100-103` | G02/G06: publican la bandera por fila |

#### B12 — Estupidez (32 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B12.1 tirada de estupidez | 32; `mechanic.stupidity`, `mechanic.disability::head-injury-stupidity`; la lesión permanente usa la misma prueba, con la excepción del Héroe aliado a 6" | Portador con estupidez/lesión; liderazgo; inicio de turno; proveedor cercano si aplica | Inicio de turno; ausencia: sin la regla o con proveedor que exime | `stupidity-failed` por fila; pierde el turno solo si falla | E2E stupidity/disability; cero operación semántica | G05/G06; el proveedor cercano se suministra en `context.nearby` |

#### B14 — Liderazgo local (222 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B14.1 líder suministrado a 6" | 154; `leader-six` (151) + `poetry-victorious-leader` (3); el proveedor debe estar a 6" y puede prestar su valor. El éxito automático (B14.3), el liderazgo propio (B14.4), el handler (B14.5) y el bonus por aliados (B14.6) son variantes distintas y **no** exigen este radio | `DuelContext.nearby` con `LocalParticipant` del líder y `distances` a 6"; el duelista conserva su propia prueba | Prueba de liderazgo con proveedor elegible; ausencia: sin líder o fuera de radio | `leadership-first-failed`/valor de prueba; criterio: usa el valor del líder solo con proveedor a 6" | E2E `serpent-priestess--leader`; P01 q10 debe construir `nearby`, no un tercer duelista | G05 ya consume `nearby`/`distances`; G06 publica el valor |
| B14.2 líder suministrado a 12" | 2; `leader-twelve`/Inspiring Presence; el radio es 12", no 6" | Igual que B14.1 con distancia 12" y proveedor declarado | Prueba de liderazgo en radio de 12"; ausencia: a 13" o sin proveedor | `leadership-first-failed`/valor; el mismo proveedor a 6" y a 12" debe discriminar el radio | E2E inspiring-presence | G05/G06 |
| B14.3 éxito automático de liderazgo | 18; `automatic-leadership`; **no hay prueba que tirar** y no exige líder ni aliado | Portador con la regla; sin `nearby` obligatorio | Cualquier prueba de liderazgo; ausencia: sin la regla | `leadership-auto-pass` (bandera); la prueba no falla; no usar «cero fallos» como testigo | `leadership.py:152-153` devuelve éxito automático; E2E | G05/G06; control negativo sin la regla |
| B14.4 solo liderazgo propio | 1; `own-leadership`; prohíbe expresamente usar el líder cercano | `nearby` puede contener un líder, pero la regla prohíbe adoptarlo | Prueba con líder presente; ausencia: misma situación sin la prohibición | Valor propio en `leadership-test-value`; el líder cercano no cambia la prueba | E2E raging-peasants | G05/G06 |
| B14.5 liderazgo de cuidador/handler a 6" | 10; `handler-leadership`; usa el valor del handler y **nunca** el líder de banda | `LocalParticipant` del handler a 6"; construcción con handler elegible | Prueba; ausencia: sin handler, fuera de 6" o con líder de banda | Valor del handler en la prueba; el líder de banda no se usa | E2E handler | G05/G06 |
| B14.6 bonificación por aliados | 1; `mob-leadership`; +1 Ld por cada aliado a 3", suministrado | `CompiledFighter.mob_allies`: el llamador declara cuántos aliados Peasant hay a 3"; no se simula la banda ni se infiere de `nearby` | Prueba individual; ausencia: recuento 0 o aliados fuera de 3" | `leadership-test-value` incrementado por el recuento declarado; es un valor, no un radio | E2E raging-peasants; `leadership.py` (`mob_allies`) | G05/G06; el recuento viaja en la construcción |
| B14.7 Brood Mentality solo para estupidez | 2; `brood-mentality`; bonificación suministrada a la prueba de estupidez, no al liderazgo ordinario | Portador con estupidez y bonus suministrado | Prueba de estupidez; ausencia: sin el bonus | `stupidity-failed`/valor de prueba; el bonus no aplica a otras pruebas | E2E brood-mentality | G05/G06 |
| B14.8 sangre fría de liderazgo (3D6, conservar 2) | 3; `cold-blooded-leadership`; la prueba se hace y se descarta el mayor | Portador y prueba de liderazgo | Prueba; ausencia: sin la regla | Dados de la prueba (3D6, descarte del mayor), no ausencia de prueba | E2E cold-blooded-leadership | G05/G06 |
| B14.9 rerolls y auras de liderazgo | 17; `leadership-reroll`, `first-failed`, `mandatory`, `undivided-leader`, `wizened-halfling`, `songster`, `devoted`, `command.raise-our-insignia`; todos repiten una prueba fallida, con proveedor/radio propio | Regla de reroll + prueba fallida; `nearby`/distancia del proveedor cuando el contrato la exige | Primera prueba fallida; ausencia: sin reroll | `reroll-used` por prueba; no confundir con el valor prestado | E2E; no hay comprobación exacta | G05/G06 |
| B14.10 relay orders | 1; `relay-orders`; el relay transmite el valor del líder a 6", nunca el suyo | `LocalParticipant` del relay a 6" y del líder; distancia | Prueba; ausencia: sin relay o fuera de 6" | Valor del líder a través del relay; el valor del relay no se usa | E2E relay-orders | G05/G06 |
| B14.11 reliquia sagrada: primera prueba automática | 7; `defence.holy-relic`; solo la **primera** prueba de liderazgo del juego es automática | Portador con reliquia; primera prueba declarada | Primera prueba; ausencia: segunda prueba o sin reliquia | `leadership-auto-pass` solo en la primera; la segunda tira | E2E holy-relic | G05/G06; el caso debe distinguir primera/segunda |
| B14.12 slave driver: valor del overseer | 2; `slave-driver`; usa el valor del overseer a 3"/6" y no el líder ordinario | `LocalParticipant` del overseer y distancia 3/6; esclavo | Prueba; ausencia: sin overseer o fuera de rango | Valor del overseer; el líder de banda no se usa | E2E slave-driver | G05/G06 |
| B14.13 modificadores y penalizaciones de liderazgo | 4; `broken-spirit`, `massively-built`, `feral-instinct`, `mesmerising-dance`; modifican la prueba sin prestar valor | Modificador y prueba; estado/condición | Prueba de liderazgo; ausencia: sin modificador | `leadership-test-modified`/valor; no se infiere de heridas | E2E | G05/G06 |

#### B15 — Secuelas y recuperación (23 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B15.1 black hunger | 7; `mechanic.black-hunger`; reacción al inicio de turno | Portador con la regla; heridas iniciales | Inicio de turno; ausencia: sin la regla | Heridas al horizonte; la reacción quita la herida y no la armadura | E2E `black-hunger::the-backlash-ignores-armour`; P01 q11 | P01 inyecta la regla; G06 testigo |
| B15.2 recuperación revenant | 2; `curse-of-the-revenant`; una tirada 5+ al inicio del turno propio recupera como máximo una herida y no supera el total inicial | Portador con la regla y herida perdida | Inicio del turno propio; ausencia: sin la regla o sin herida perdida | `wounds` como resultado directo de la recuperación; exactamente una, con tope | E2E curse-of-the-revenant; `skill.regeneration` es B05.2 (save por herida), **no** esta recuperación; el daño reactivo es B15.4 | G06 heridas por turno |
| B15.3 incremento del máximo de heridas | 3; `skill.monstrous`; +1 Herida al empezar, no curación | `FighterBuild` con la skill; heridas iniciales | Inicio del duelo; ausencia: sin la skill | `wounds` inicial y máximo recuperable; no es una reacción de curación | E2E skill.monstrous | G00/G02 estado inicial |
| B15.4 reacción de daño por perder herida o contacto | 7; `trait.spines`/`spines` (inicio de fase, S1 automático) y `trait.acid-blood`/`acid_blood` (al perder herida, S3 automático); **disparador, destinatario y momento distintos** | Portador con la mutación; oponente en contacto; estado de herida | Espinas: inicio de cada fase de close combat. Ácido: después de perder una herida. Ausencia: sin mutación o sin contacto/herida | Ataque automático (`attack-count`/daño) contra el oponente, sin crítico; el testigo debe distinguir inicio de fase de reacción a herida | E2E acid/blood/spines; `rounds.py:1153-1163` ejecuta espinas, no curación | G03/G06; no reutilizar el criterio de B15.2 |
| B15.5 reacción al quedar fuera de acción (contagious) | 2; `trait.contagious`; tras una lesión de close combat que saca de acción, el atacante prueba T; fallo = una herida automática; no-muertos/poseídos exentos | Portador con la regla y atacante elegible; resultado de lesión ya establecido | Salida de acción confirmada; ausencia: sin salir de acción o atacante exento | Una reacción, prueba de T y herida automática; el testigo es la reacción, no la herida terminal del portador | E2E contagious | G03/G06 |
| B15.6 pérdida de característica por herida (torturer) | 2; `mechanic.torturer`; cada herida no salvada en close combat reduce 1 Fuerza al defensor vivo, acumulativo hasta 1; no-muertos exentos | Portador con la regla; defensor vivo; herida no salvada | Herida no salvada; ausencia: sin herida, no-muerto o salvada | `strength-modified` del defensor por herida; no es daño ni recuperación | E2E torturer | G02/G06 |

#### B99 — Consumidor ambiguo (7 claves)

| Variante | Claves y justificación | Preparación/contexto/decisiones | Disparador/ausencia | Observable y criterio | Referencia o hueco | Dependencia/propietario |
| --- | --- | --- | --- | --- | --- | --- |
| B99.1 consumidor sin operador decisivo | 7; `contexts/attacks/pools` genéricos, `OwnedRollDice`; el consumidor no nombra operador | No se puede preparar hasta localizar el consumidor | No aplica | `consumer`/`clause_scope`; localizar o `UNLOCATED` | `unlocated-localization.csv` | Propietario del anexo (G01) |

#### 4.4.1 Pertenencia, variantes requeridas y obligaciones secundarias

- **Pertenencia exacta**: una clave del CSV tiene una variante primaria. Las 182
  claves que la revisión 3 dejaba en «other» están asignadas por contrato; no se
  agrupan por substring. La justificación está en la columna «Claves y
  justificación» y la lista exacta en el CSV.
- **Variantes requeridas**: `required=True` en una obligación no basta para
  acreditar todas sus variantes. El catálogo de P01 declara `variant_id` y
  `coverage` por variante. Una variante material (las 63 filas de §4.4) exige al
  menos un caso con su testigo propio; un caso genérico de la obligación **no**
  cubre automáticamente las demás variantes.
- **Obligaciones secundarias**: se declaran por variante en el catálogo, no en
  una nota suelta. Como mínimo: `weapon.pike`/`spear`/`quarter-staff` → B10.1 +
  B08.2/B08.5 (prioridad y recuento); `skill.strongman` → B03.3 + B10.1;
  `weapon.beastlash` → B11.1 + B06.3; `skill.regeneration` → B05.2 (el save por
  herida; **no** es la recuperación de B15.2); `mechanic.death-blow` → B10.3 +
  B08.2; `weapon.starsword` → B06.1 + B05.1; `mechanic.devoted-to-the-vampire`
  → B11.7 + B02.2; `trait.spines`/`trait.acid-blood` → B15.4; `skill.monstrous`
  → B15.3; `mechanic.cold-blooded-psychology` → B11.5 (nunca B11.2, que es
  inmunidad). La evidencia de una variante no acredita la secundaria: cada una
  necesita su propio testigo y su propio caso o `also_covers` explícito.
- **Huecos de numeración**: `Bxx.y` se conserva cuando el contrato sobrevive; los
  números ausentes (p. ej. B01.4, B03.6, B04.5, B05.3, B06.4, B07.4, B12.3) no
  son obligaciones perdidas: agrupaban reglas residuales y sus claves están
  reasignadas a la variante cuyo contrato cumplen. El denominador es la suma de
  las 63 variantes, no el mayor sufijo.
- **Sin decisiones por script**: `effect_id` y `consumer` solo localizan la clave.
  La pertenencia se decide leyendo el contrato impreso y su implementación
  modular; las tablas explícitas de `inventory_build.py` registran esa decisión
  (`SPLIT_EFFECT`, `OTHER_EFFECT`, `KEY_OVERRIDE`, `FORCED_KEYS`) y fallan si una
  clave genérica no tiene decisión.
- **Transferencia a P01**: `behaviour-inventory.csv` es la foto de diseño de P00.
  P01 lo importa una vez a su catálogo ejecutable y pasa a ser el propietario de
  la pertenencia; no hay lectura permanente de `P00-results` ni un segundo
  registro manual que se sincronice. El CSV conserva la reconciliación y la
  evidencia, no se convierte en dependencia de ejecución.
