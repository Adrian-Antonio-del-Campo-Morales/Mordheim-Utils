# T06-effects — Matriz de efectos y reparto de obligaciones

Documento auxiliar de [T06](T06.md). Propiedad del agente de T06; solo el coordinador cambia estados/responsables y asigna archivos compartidos. **No marca T06 como completada** ni modifica la checklist principal.

Este documento enumera **cada efecto de 2A/2B exactamente una vez**, con mecanismo responsable, destino y criterio de aceptación. La matriz completa, fila por fila (1692 registros con `id`, familia, `binding`, mecanismo, destino, tarea de fase, clasificación y fuente), vive en el informe regenerable `build/cache/t06-matrix.{csv,json}` —ignorado por Git—; aquí se entrega el resumen suficiente para reconstruirlo y asignarlo.

> **Nota de replanificación (leer primero).** El [README](../README.md) fue replanificado por el coordinador (fila «Replanificación» del registro de decisiones, 2026-09-25, aprobada por el usuario) **después** de redactarse el prompt que originó esta tarea. El reparto vigente es de **tres fases**: `KB` (T06–T08), `Warband Manager Web` (T09–T12) y `Combat Simulator` (T13–T15); la aplicación de escritorio queda fuera de alcance. Por eso cada obligación se clasifica aquí como **`KB` · `Warband Manager Web` · `Combat Simulator` · `sistema excluido`**, y se conserva además la etiqueta `legacy_destination` (`T08`/`T09`/`T10`) para trazar contra el prompt original. Mapa: `T08` (construcción/selección) → **Warband Manager Web (T09)**; `T09` (combate) → **Combat Simulator (T13)**; `T10` (campaña) → **Warband Manager Web (T10)**; `ausente` → **sistema excluido**; `dato` → **KB (T07/T08)**.

---

## 0. Método, alcance y reproducibilidad

Entrada: `build/cache/t06-inventory.json` (1692 efectos extraídos de `sources/2A` y `sources/2B` con las herramientas existentes `report rules` y `verify`; T05 no re-ejecutada, promoción no repetida).

Clasificador: `build/cache/t06-classify.py` (determinista, auditable). Reglas:

1. `norm()` pasa a minúsculas y pliega guiones/guiones bajos a espacios, para que ids impresos como `immune-to-psychology` casen.
2. **La columna `reason` del informe NO se usa** en las tablas principales: es texto de auditoría («…before promotion», «…current engine scope») que desviaría cientos de filas. Se clasifica por **texto de efecto impreso + id de la regla**.
3. Los **68 efectos con `binding`** (los de `effect_scope YES`) se enrutan por familia de binding y se marcan `cubierto` solo si el mecanismo ejecutable del binding está confirmado (§4).
4. Reglas de id de regla primero (el propio id nombra la cláusula: `--leader`, `--immune-to-psychology`, `--large`…), después una tabla ordenada de texto. Las cláusulas de **campaña/construcción preceden a las de combate** para que una obligación de campaña no quede tapada por una cláusula de combate del mismo texto.
5. Los cuatro sistemas de batalla fuera de alcance solo reciben `sistema excluido` cuando **ninguna** cláusula de alcance (construcción/campaña/combate) también casa.
6. Residuo: solo **41 ids de regla** no los enrutan las tablas; se adjudican a mano en `HAND_ADJUDICATED` (§7).
7. Cada efecto compuesto lleva una lista `obligations` (§2.2): una entrada por obligación distinta con subsistema, destino, tarea propietaria, mecanismo, criterio y motivo cuando está excluida. El total de **efectos** no cambia (1692); las obligaciones se cuentan aparte.

Reproducir:

```bash
python build/cache/t06-classify.py            # regenera la matriz y t06-summary.json
python build/cache/t06-inventory.py           # recalcula el inventario base (si hace falta)
head -3 build/cache/t06-matrix.csv            # columnas: id,family,tree,band,owner,binding,mechanism,destination,phase_task,legacy_destination,classification,obligations,note,source_file
# (obligations es un array JSON por fila; en CSV va serializado como cadena)
```

> **Qué es y qué no es este documento.** Es una **clasificación y reparto de trabajo**, no un certificado de implementación. Una fila `cubierto` significa «mecanismo existente + al menos una spec/prueba lo ejercita (§4)», no que el efecto esté validado de extremo a extremo. El enrutado es una **propuesta revisable**: un texto que toca varios subsistemas se envía a su primer mecanismo y se marca `compound` (§6) para que la tarea propietaria lo divida.

---

## 1. Inventario contabilizado

| Familia | Registros | Fuente |
|---|---:|---|
| `band-rule` (reglas de banda/perfil) | 1330 | `sources/{2A,2B}/bands/mordheim/*/special-rules.yaml` |
| `item` (objetos de catálogo) | 144 | `sources/{2A,2B}/catalog/items/*.yaml` |
| `spell` (efectos de conjuro) | 135 | `sources/{2A,2B}/catalog/magic-2{a,b}.yaml` |
| `hireling` (perfiles y reglas propias) | 83 | `sources/2B/catalog/hirelings/*.yaml` |
| **Total** | **1692** | por árbol: 2A 469 · 2B 1223 |

`0` reglas sin efecto. La suma por familia, por destino y por clasificación cuadra con 1692 en las tres particiones (comprobado en `t06-summary.json`).

---

## 2. Taxonomía de mecanismos, destino y criterio de aceptación

| Mecanismo | Destino (fase) | N | Criterio de aceptación (resumen) |
|---|---|---:|---|
| `E01-profile-trait-binding` | Web · T09 | 39 | El compilador resuelve el binding del perfil y lo aplica **una vez**; spec + prueba de construcción; sin doble concesión. |
| `E02-skill-access` | Web · T09 | 46 | La selección rechaza habilidades fuera del acceso declarado; una elección permitida y una rechazada por lista. |
| `E03-selectable-skill` | Web · T09 | 24 | Habilidad comprable en creación/avance; su efecto alcanza el mismo mecanismo que las concesiones `runtime`; caso negativo sin la habilidad. |
| `E04-roster-composition` | Web · T09 | 181 | El compilador rechaza una banda que viola cupo/límite/unidad y acepta una legal; la cláusula (0-N, slot, líder, enjambre) es fixture. |
| `E05-equipment-list` | Web · T09 | 65 | Equipo fuera de la lista del perfil se rechaza en construcción (dominio/servicio, no solo UI). |
| `E06-hiring-eligibility` | Web · T09 | 109 | El reclutamiento rechaza una banda inelegible y acepta una elegible; la cláusula es fixture. Distinto del coste (E17). |
| `E07-characteristic-bounds` | Web · T09 | 22 | Se acota o rechaza una característica fuera del límite declarado, con el perfil exento como fixture. |
| `E08-combat-to-hit` | Combate · T13 | 30 | Mismo conteo de impactos en modular/vectorizado/nativo con semilla fija; spec de activación y ausencia. |
| `E09-combat-wound-injury` | Combate · T13 | 83 | El paso se expresa sobre el effect-set y coincide con el oráculo modular; expiración/consumo cubiertos. |
| `E10-combat-attacks-order` | Combate · T13 | 45 | Conteo de ataques/orden de golpeo idéntico entre backends; contrato de orden en spec. |
| `E11-combat-weapon-profile` | Combate · T13 | 28 | El perfil/regla del arma se resuelve en effect-set y lo reproduce el oráculo modular. |
| `E12-psychology-combat` | Combate · T13 | 161 | El modificador psicológico se aplica en la fase de combate y se reproduce entre backends; condiciones/filtros son fixtures. |
| `E13-movement-charge-action` | Combate · T13 | 129 | La regla de movimiento/carga/acción tiene caso determinista reproducido por el oráculo modular. |
| `E14-campaign-experience` | Web · T10 | 127 | El servicio concede/rechaza XP una sola vez según la fuente, lo persiste y la elección llega al servicio (no solo a un helper) en Python y TypeScript. |
| `E15-campaign-injury-recovery` | Web · T10 | 151 | El servicio posbatalla resuelve lesión/recuperación con dados inyectados, una sola vez, y persiste; excepción (Regenerate, captura) en fixture. |
| `E16-campaign-rout-morale` | Web · T10 | 28 | La regla de ruta/liderazgo se evalúa en el límite de partida, sobre el modelo correcto, y se aplica una vez. |
| `E17-campaign-hiring-costs` | Web · T10 | 0 | La transacción de reclutamiento/mantenimiento cobra/paga la cifra exacta una vez, valida recursos y no deja estado parcial. |
| `E18-campaign-trade` | Web · T10 | 117 | La transacción aplica precio/disponibilidad/rareza con dados inyectados, una vez, preservando `equipment-access` vs `trading-post`. |
| `E19-campaign-exploration` | Web · T10 | 24 | El paso de exploración/pospartida resuelve con dados inyectados y actualiza recursos/historial exactamente una vez. |
| `E20-campaign-magic-progression` | Web · T10 | 80 | La lista concedida llega al constructor/servicio como elección seleccionable y se persiste; separada de la resolución ausente. |
| `E21-campaign-mutations` | Web · T10 | 3 | La mutación es elección validada o tirada inyectada que cae en la tabla una vez y se persiste. |
| `E22-campaign-roster-lifecycle` | Web · T10 | 11 | La operación de ciclo de vida (sucesión, baja, disolución) es transacción validada que persiste y reabre con ids estables. |
| `X1-absent-deployment` | excluido | 5 | Sin implementación; **texto íntegro y esta limitación** conservados en el registro promovido. |
| `X2-absent-hiding` | excluido | 5 | Sin implementación; texto íntegro y limitación conservados. |
| `X3-absent-shooting` | excluido | 24 | Sin implementación; texto íntegro y limitación conservados. |
| `X4-absent-battle-magic` | excluido | 137 | Sin implementación; texto íntegro y limitación conservados. El acceso a listas va por E20. |
| `D0-data-only` | KB · T07 | 18 | Registro conservado verbatim y servido como dato por los cargadores/presentación; no se reclama efecto de runtime. |

**Totales por destino: `Warband Manager Web` 1026 · `Combat Simulator` 476 · `sistema excluido` 171 · `KB` 19 = 1692.**
**Totales por clasificación: `cubierto` 78 · `ampliacion-necesaria` 1443 · `sistema-ausente` 171 = 1692.**
Por tarea de fase: **T09 (Web) 485 · T10 (Web) 541 · T13 (Combate) 476 · T07 (KB) 19 · `EXCLUDED` 171.**
La fila `trait.spectral-touch` es la única cuyo destino primario es `KB` (T07) pese a mapear al mecanismo E01: su alta en `bindings.yaml` precede a la promoción (ver §4 y §8).

Desglose por familia y destino:

| Familia | Warband Manager Web | Combat Simulator | sistema excluido | KB |
|---|---:|---:|---:|---:|
| `band-rule` (1330) | 837 | 449 | 36 | 8 |
| `item` (144) | 107 | 27 | 0 | 10 |
| `spell` (135) | 0 | 0 | 135 | 0 |
| `hireling` (83) | 82 | 0 | 0 | 1 |

### 2.1 Los 78 `cubierto`

- **67 efectos de banda con binding confirmado** (§4). Son los únicos `cubierto` de `band-rule`; el resto del staging no tiene una marca `runtime.implemented=YES` que resista evidencia (T06 no se apoya en la marca global).
- **10 `item`** con texto de catálogo descriptivo/estructural sin efecto de runtime (`D0`).
- **1 `hireling`**: perfil `name-only` sin regla propia (T04 ya lo declaró `out_of_scope` sin entrada de contratación).

### 2.2 Obligaciones separadas (efectos con varios consumidores)

Los **366 efectos `compound`** más el binding nuevo `trait.spectral-touch` (**367 filas**) llevan la lista `obligations`. Cada entrada tiene la forma:

```json
{"subsystem": "<bucket>", "destination": "KB|Warband Manager Web|Combat Simulator|sistema excluido",
 "phase_task": "T07|T09|T10|T13|EXCLUDED", "mechanism": "E0X-…|X1..X4",
 "acceptance": "<criterio concreto>", "reason": "<motivo si está excluida>"}
```

Se conserva **una sola fila por efecto**; el campo `obligations` no infla el total de efectos.

| Métrica | Valor |
|---|---:|
| Efectos (filas) | **1692** (sin cambios) |
| Filas con `obligations` | 367 (366 `compound` + `trait.spectral-touch`) |
| Obligaciones listadas | **970** |
| Efectos sin división (1 obligación implícita) | 1325 |
| **Total de obligaciones** | **2295** |

Reparto de las 970 obligaciones listadas:

| Por destino | N | Por tarea | N | Por subsistema | N |
|---|---:|---|---:|---|---:|
| `Combat Simulator` | 409 | T13 | 409 | `shooting` | 254 |
| `sistema excluido` | 316 | `EXCLUDED` | 316 | `movement` | 182 |
| `Warband Manager Web` | 244 | T09 | 125 | `battle-magic` | 127 |
| `KB` | 1 | T10 | 119 | `close-combat` | 125 |
| | | T07 | 1 | `psychology` | 107 |
| | | | | `hiding` | 75 |
| | | | | `deployment` | 38 |
| | | | | `construction` | 35 |
| | | | | `campaign` | 26 |
| | | | | `kb-registration` | 1 |

El mecanismo por obligación es el **primero de la familia del subsistema** que casa con el texto (p. ej. `campaign` → E14–E22; `construction` → E01–E07; `close-combat` → E08–E13); la obligación primaria conserva el mecanismo del efecto. La tarea propietaria debe afinar el mecanismo al dividir si la prosa lo pide.

---

## 3. Los 171 `sistema excluido` (solo los cuatro sistemas fuera de alcance)

El plan (README) excluye **crear** sistemas de despliegue, ocultación, disparo o resolución de magia de batalla. Ningún otro efecto se ha excluido por esta vía.

| Sistema | N | Familia | Ejemplos representativos |
|---|---:|---|---|
| `X1` despliegue/infiltración/scenario | 5 | `band-rule` | `noble--infiltration`, `scouts--scout`, `band--skill-infiltration`, `band--miners` |
| `X2` ocultación/spotting | 5 | `band-rule` | `waywatcher--sniper`, `waywatcher--camouflage`, `band--excellent-eyes`, `elder-scout--camouflage` |
| `X3` disparo/objetivo grande | 24 | `band-rule` | `village-ogre--large`, `abomination--large-target`, `flingers--scrap-slinger`, `gunners--wasteland-gunners` |
| `X4` resolución de magia de batalla | 137 | 135 `spell` + 2 `band-rule` | los 135 efectos de conjuro; `vim-to-mage--arcane-vim-toist`, `band--skill-fey` (4+ contra magia hostil) |

**Regla de exclusión conservada:** cada uno conserva su texto íntegro y esta limitación en el registro promovido; no se marca `runtime.implemented`. Los efectos de campaña que conviven en el mismo registro **no se desechan** (p. ej. `Cleric—Disciple of Sigmar` describe *empezar sabiendo una plegaria* → E20, no X4; `Tinker—Grifter` describe trueques → E18, no X3). Esos dos casos, inicialmente mal enrutados por el texto de auditoría, están en §7.

---

## 4. Los 68 efectos con binding — evidencia de cobertura

Los 68 `effect_scope YES` son exactamente los que declaran un `binding`. Comprobación por muestreo contra el vocabulario de la KB, las specs semánticas y el motor (no se repiten las suites completas de T02–T05). 20 de los 21 bindings ya existen en el vocabulario de la KB (261 ids); solo **`trait.spectral-touch`** es nuevo y está `pending-promotion` en [`sources/knowledge/registry/bindings.yaml`](../../../../sources/knowledge/registry/bindings.yaml).

| Binding | N | Evidencia (spec / motor) | Veredicto |
|---|---:|---|---|
| `trait.poison-immune` | 22 | `grants/editorial-poison-immunity.yaml`, `editorial-rotten-body`, `editorial-undead-band-poison`, `nurgle-blessings-and-rot`; `EffectSet.poison_immunity` | cubierto |
| `skill.ignore-pain` | 8 | `grants/editorial-no-pain`, `editorial-pestilens-ignore-pain`, `editorial-band-no-pain`, +10 specs | cubierto |
| `profile.skill-access` | 6 | `rules/construction-access`, `grants/editorial-special-skill-access`, `remaining-profile-access`; compilador | cubierto |
| `trait.natural-armour-save` | 5 | `grants/editorial-natural-armour`, `-cold-one-skin`, `-kroxigor-scaly-skin`, `-lustria-scaly-skin`; `natural_armour_save` | cubierto |
| `skill.hard-to-kill` | 4 | 12 specs (`editorial-monster-slayer*`, `-no-injury-roll`, `-tough-as-steel`…) | cubierto |
| `trait.concussion-immune` | 4 | `grants/editorial-hard-head`, `-khemri-injury`, `-pit-hard-head`; `EffectSet.concussion` | cubierto |
| `skill.regeneration` | 3 | `grants/editorial-strigoi-regeneration`, `-troll-regeneration`; `interactions/damage-mitigation`; `regeneration_save` | cubierto |
| `trait.frenzy` | 2 | `rules/skills-frenzy-and-armour-floor`; motor frenzy en `phases.py`, `modular/rounds.py`, `vectorized`, `native` | cubierto |
| `compiler.lizardmen-scaly-skin` | 2 | 1 spec + 4 módulos Python | cubierto |
| `skill.unbeatable-warrior` | 1 | 2 specs + 9 módulos | cubierto |
| `skill.sword-master` | 1 | 2 specs + 5 módulos | cubierto |
| `skill.ferocious-charge` | 1 | 3 specs + 11 módulos | cubierto |
| `skill.monster-slayer` | 1 | 4 specs + 5 módulos | cubierto |
| `skill.berserker` | 1 | 2 specs + 5 módulos | cubierto |
| `trait.poisonous-injury` | 1 | `grants/editorial-spider-poisonous` | cubierto |
| `compiler.bite-attack` | 1 | 1 spec + 4 módulos | cubierto |
| `compiler.saurus-skill-prohibitions` | 1 | 1 spec + 4 módulos | cubierto |
| `skill.bellowing-battle-roar` | 1 | 2 specs + 5 módulos | cubierto |
| `skill.always-strikes-first` | 1 | 3 specs + 5 módulos | cubierto |
| `weapon.vomit-attack` | 1 | `rules/vomit-attack`, `grants/editorial-vomit-attack`; motor | cubierto |
| `trait.spectral-touch` | 1 | **sin** spec ni módulo; registrado `pending-promotion` | **ampliación · KB (T07) → consume Web (T09) y Combate (T13)** |

Cobertura medida: **67 cubiertos, 1 ampliación**. El único no cubierto (`spirit-hosts--spectral-touch`, `call-of-the-night-haint-mim`) tiene **tres obligaciones** (§2.2): el alta en `sources/knowledge/registry/bindings.yaml` pertenece a **T07/coordinador** durante la fase KB, **antes** de promover la banda; T09 lo consume como contrato ejecutable del compilador y T13 implementa el paso de daño (herida adicional con 6 natural al impactar). **T09 no es prerrequisito de T07.**

---

## 5. Reconciliación con T02–T05

La matriz **reutiliza** las decisiones de identidad ya aceptadas; no las reabre. Cada registro transformado queda contabilizado una vez en su destino:

- **Variantes conservadas** (dos ids, dos registros): `repeater_pistol_moh`, `society_familiar`, `shield_of_sigmar`, `wolf_cloak`, `lore.prayers-of-taal-and-rhya`. Su efecto se clasifica en el mecanismo de su texto (p. ej. `shield_of_sigmar` → E09/E11; la lore de Taal → E20 + X4).
- **Fusiones** (`horsemans_hammer`, `hunting_arrows`): un solo registro promovido; una sola fila en la matriz.
- **Fusiones-re-dirección** (`rope_and_hook`→`rope_hook`, `elven_bow`→`elf_bow`) y **7 re-direcciones documentadas** (`dueling_pistol`, `throwing_axe_sar`, `throwing_knife`, `wardog`, `dragon_cloak`, +2 de T04): el `source_ref` hereda el ítem de la KB; la matriz conserva el id **de staging** como origen y anota el destino.
- **Sacerdotes `-miracle-workers`** (`priest-of-morr`, `warrior-priest-of-sigmar`, `wolf-priest-of-ulric`): 3 perfiles + 12 reglas + 3 entradas de campaña se contabilizan **bajo el id re-direccionado**; el `id` de staging y el promovido aparecen como origen/destino, sin doble conteo. Sus reglas (plegarias, strictures, protección) van a E20 (acceso) y X4 (resolución).
- **Taal & Rhya** como **variante** (no espejo): su lore se contabiliza como alta propia (E20) y sus 6 bloques de prosa se preservan.
- **`warplock_pistol` y su entrada `-mim`**: el ítem se contabiliza como variante; su entrada de mercado `…-mim` es una fila de `trading-post` (E18) distinta del `campaign.trading-post.warplock-pistol` ocupado por `warp_pistol`.
- **26 ids históricos de mercado**: no se derivan por convención `campaign.trading-post.<item_id>`; la matriz los trata como registros propios (E18) y remite a la tabla de T05, no a una regla de nombre.

Ningún efecto de T02–T05 se pierde ni se cuenta dos veces como trabajo independiente: los transformados aparecen una vez, con su acción declarada.

---

## 6. Efectos compuestos (obligaciones con consumidores distintos)

**366 filas** tocan más de un subsistema. Cada fila lleva su mecanismo primario y el campo `compound`, y una lista `obligations` con la división por consumidor (§2.2); la tarea propietaria **debe** aplicarla. Los focos de mayor solape por mecanismo:

| Mecanismo primario | Compuestas | División típica |
|---|---:|---|
| `X4-absent-battle-magic` | 80 | el conjuro es resolución de magia (excluida) **pero** su prosa toca combate/psicología: la parte de batalla no se implementa y el texto se conserva; cualquier obligación de acceso va por E20 |
| `E13-movement-charge-action` | 44 | desplazamiento (T13) + regla de campaña (T10), p. ej. «montado y sin experiencia» |
| `E15-campaign-injury-recovery` | 31 | tabla de lesión (T10) + condición de combate (T13) |
| `E18-campaign-trade` | 30 | precio (T10) + efecto del objeto al usarlo (T13) |
| `E05-equipment-list` | 28 | acceso (T09) + interacción en combate (T13) |
| `E10-combat-attacks-order` | 20 | ataques (T13) + acceso/límite (T09) |
| `E02-skill-access` | 20 | acceso (T09) + efecto de la habilidad (T13) |
| `E11-combat-weapon-profile` | 17 | perfil de arma (T13) + disponibilidad (T09/T10) |
| `E06-hiring-eligibility` | 17 | elegibilidad (T09) + coste (T10) |
| `E04-roster-composition` | 15 | cupo (T09) + consecuencia de campaña (T10) |
| `E14-campaign-experience` | 13 | XP (T10) + efecto desbloqueado (T09/T13) |
| `E20-campaign-magic-progression` | 10 | acceso a lista (T10) + resolución del conjuro (excluida) |

`E17-campaign-hiring-costs` queda en **0**: todas las cláusulas de coste de contratación detectadas comparten registro con su cláusula de elegibilidad (`E06`) o de composición (`E04`); al dividir esas filas, T09/T10 deben separar coste (T10, E17) de elegibilidad (T09, E06).

Ejemplos explícitos que **no** deben excluirse por el simulador de duelo: `band--slow-witted` (media XP → T10), `band--regenerate` (tabla de lesiones → T10), `mother-knows-best` (pruebas de ruta → T10), `band--brood-mentality` (estupidez → T13 **y** contratación vetada → T09/T10), `corpse-master--gofer` (visitas a asentamientos → T10). La lista completa está en `build/cache/t06-matrix.csv` (filtrar `compound`).

---

## 7. Residuo adjudicado a mano (41 ids de regla)

Estas 41 reglas no las enrutan las tablas por su texto/id (texto vacío o prosa peculiar) y se adjudicaron una a una:

| id de regla | Mecanismo | Motivo |
|---|---|---|
| `band--choosen-of-morr` | D0 | ritual de narrativa, sin efecto de runtime |
| `band--halfling-items` | E05 | «no obtienen bonificaciones de objetos Halfling» |
| `shinobi--loner` | E04 | «nunca puede ser líder» |
| `cleric--disciple-of-sigmar` | E20 | empieza sabiendo una plegaria (acceso, no resolución) |
| `bullied-goblin--the-rigors-of-leadership` | E16 | modificadores de liderazgo de grupo |
| `petru--necromancy` | E20 | elige conjuro aleatorio en vez de habilidad |
| `band--incomparable-miners` | E04 | composición de mineros |
| `dwarf-troll-slayers--deathwish` | E12 | inmunidad psicológica |
| `fanatics--addict` | E19 | disponibilidad de champiñones antes de la batalla |
| `cave-squigs--minderz` | E04 | composición de unidad |
| `troll--dumb-monster` | E12 | estupidez |
| `troll--always-hungry` | E12 | comportamiento psicológico |
| `prophet--corrupting-influence` | E22 | efecto sobre la plantilla |
| `questing-knights--corruption` | E16 | prueba de Ld tras la batalla |
| `squires--oath-of-servitude` | E06 | al contratar escuderos |
| `rememberer--hard-to-find` | E06 | tirada al reclutar |
| `band--ghutani-scholar-fields` | E04 | campos de estudio (perfil) |
| `band--slaves-can-lead` (×3 bandas) | E04 | los esclavos pueden ser líderes |
| `gyrocopter--space` | E04 | asientos del vehículo |
| `band--honorable` | E05 | nunca usa veneno/drogas |
| `band--houses` | E04 | elección de casa al crear la banda |
| `band--martial-finesse` | E03 | empieza con la habilidad 'Web of Steel' |
| `band--battle-seasoned` | E03 | empieza con la habilidad 'Battle Tongue' |
| `band--khorne-raider-rules` | E06 | alistar tripulación |
| `band--cold-blooded` | E12 | 3D6 en pruebas de liderazgo |
| `fimir-warriors--monstrous` | E15 | tabla de lesiones de secuaces (+ cuenta como 2 modelos → E04) |
| `band--teetotalers` | D0 | nunca bebe alcohol (sabor) |
| `band--skurvey-alliance` | E06 | hospitalidad/alianza al contratar |
| `band--muzil-scholars` | E04 | hasta 2 eruditos |
| `abomination--unnatural-life` | D0 | «cuenta como vivo» (clasificación) |
| `goblin-enjuneer--glass-ceiling` | E04 | nunca líder |
| `band--foreign-but-human` | E04 | composición de piratas cathayanos |
| `band--countless`, `giant-rats--countless`, `skaven-slaves--numerous` | E04 | aumentan el número de la banda hasta 20 |
| `band--power-grab` | E16 | ±1 Ld por mayoría de raza |
| `boglars--bicker` | E10 | comportamiento aleatorio al inicio del turno |
| `skavenslaves--all-races`, `strigany--living`, `bats--living` | D0 | clasificación de raza/sin reglas no-muertas |
| `band--secretariat` | E13 | comandar un barco antes de la batalla |

---

## 8. Mapa de conflictos de propiedad y orden de sincronización

Tareas de fase (README replanificado): **T06** clasifica, **T07** fusiona/promueve en la KB, **T08** valida y cierra la KB; **T09** construcción/selección Web, **T10** campaña Web, **T11** interfaz Web, **T12** artefactos/validación Web; **T13** reglas del Combat Simulator, **T14** paridad, **T15** cierre.

Escrituras compartidas que necesitan **propietario exclusivo** (un dueño por archivo; los consumidores esperan a que la ampliación común se acepte):

| Escritura compartida | Consumidores | Propuesta de dueño | Orden |
|---|---|---|---|
| `sources/knowledge/registry/bindings.yaml` (alta de `trait.spectral-touch`) | T07 (promoción), T09 (contrato Web), T13 (resolución) | T07 o el coordinador | fase 1, **antes** de promover `call-of-the-night-haint-mim`; T09/T13 consumen después |
| `sources/knowledge/**` (registros promovidos, esquemas, i18n) | T07/T08 | T07; nadie más escribe KB durante la promoción | fase 1, serial |
| `packages/python/roster-construction/**` + `tests/python/construction/**` | T09/T10/T13 | T09 | primero de la fase 2 (fija contratos Web) |
| `packages/python/core/mordheim_core/{effects,models}.py` (campos de `EffectSet`) | T09/T10/T13 | T09 fija, T13 congela antes de repartir backends | antes de T13 |
| `packages/typescript/domain/campaign/**`, `packages/typescript/application/campaign/**` | T10/T11 | T10 (T11 solo presenta) | tras T09 |
| `packages/python/combat-engine/mordheim_combat/**` (modular/vectorized/native) | T13/T14 | T13 (mecanismo modular primero) | fase 3, tras T12 |
| `tests/specs/semantic/**` (rules/grants/interactions) | T09/T13 | un dueño por archivo; el primero que lo toque | durante cada fase |
| manifiestos/digests y generados web | T12 | T12 o el coordinador | cierre de fase |

Reglas de serialización del README: ningún trabajo de escritura de una fase comienza antes del commit de cierre de la anterior; T10/T11 solo escriben en paralelo tras estabilizar T09 sus contratos; T13 se reparte por backend solo después de fijar el mecanismo modular y con archivos disjuntos; las pruebas que mutan datos compartidos corren aisladas.

**Dependencia dura detectada:** ninguna. El binding nuevo no detiene lotes independientes.

---

## 9. Dudas de fuente y bloqueos exactos

Se conservan las limitaciones ya declaradas por T02–T05 (no se resuelven aquí, son del coordinador) y se añaden las de T06:

1. **PDFs KEP sin capa de texto** (`clan-angrund-kep`, `crooked-moon-kep`, `slave-uprising-kep`): 48 nombres de regla, 54 de equipo y 23 de perfil no verificables por extracción (T03). Afecta a la confianza de clasificación de las reglas de esas 3 bandas, no a su inclusión.
2. **`rule-effect-condensed` 64 / `rule-name-editorial` 12 / `rule-effect-absent` 1** (T03 §6.D): prosa condensada; el texto es más corto que la fuente y puede ocultar matices de activación. Decisión del coordinador.
3. **`source-row-other-document` 197 / `source-row-documented` 8**: renglones de tablas propias; su modelado se confirma en T08/T12.
4. **Cotejo de mercenarios de la KB con cobertura 0/0** (T04 §6, sin snapshots en caché): la cobertura de los 83 registros `hireling` se apoya en T04, no en una comprobación nueva.
5. **Extras por árbol, no por banda** (T04 §5): la reducción de `item-name-missing` de 8 a 3 no es evidencia por banda.
6. **`page_sha256` de 2A no reproducible** (T02 §2): los hashes quedan como declaración, no como comprobación.
7. **Verificador semántico no verde en la revisión de partida:** `verify_semantics()` devuelve **30 errores `source changed`** (digests de spec desincronizados de la KB, p. ej. `rule/mordheim/sons-of-hashut/band--hard-to-kill/skill.hard-to-kill`) y **82 `pending`**; `semantic_complete=False`. Es **previo** (T06 no tocó KB ni specs) y afecta a la fuerza probatoria de §4: el mecanismo está ejercitado, pero la certificación verde es de T08/T14. `verify --structural` sí pasa (`structural_complete=True; 531 profiles`).
8. **Cambio de plan durante la tarea:** el README fue replanificado (destinos `KB`/`Web`/`Combat Simulator`) después del prompt original (destinos T08/T09/T10). Este documento usa el vocabulario vigente y conserva `legacy_destination` para trazar. El coordinador alineó después el contrato inicial de T06 con este reparto.
9. **Clasificador heurístico:** el enrutado es por texto/id y primer mecanismo ganador. Un texto multi-subsistema se marca `compound` y **debe dividirse**; el residuo de 41 reglas es explícito (§7). Ninguna fila queda en «pendiente» sin motivo.

---

## 10. Limitaciones de lo que esta matriz demuestra

- Contabiliza y **reparte** los 1692 efectos en mecanismos y destinos; **no** demuestra que ninguno esté implementado de extremo a extremo.
- `cubierto` se apoya en la existencia del mecanismo + al menos una spec/prueba, con la suite semántica en el estado del punto 7.
- El enrutado es **revisable** por la tarea propietaria; el campo `compound`/`obligations` y la §7 son los puntos de mayor riesgo de interpretación. El mecanismo asignado a cada obligación es un **valor por defecto de su subsistema**, afinable al dividir.
- No se ejecutaron las suites completas de T02–T05, la promoción de T05, `npm`/TypeScript ni la generación web.
