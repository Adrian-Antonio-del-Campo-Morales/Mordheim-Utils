# G01 — Entrega: compilación compartida, construcción y enlaces existentes

Fase 1, etapa A. Sin cambios de producción: este documento es el único artefacto creado.
Fecha: 2026-10-21.

## 1. Base y método

| Dato | Valor |
| --- | --- |
| Revisión | `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` + cambios locales presentes en el árbol |
| Registro canónico | `sources/knowledge/verification/clause-contracts.csv`, SHA-256 `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731` (coincide con la base del encargo; el fichero aparece modificado en el árbol y no se ha tocado) |
| Claves principales | 1396 (anexo del encargo), todas presentes en el CSV, `clause_scope=YES`, `status={"numpy":"pending","native":"pending"}` |
| Claves de apoyo | 6 (`trait.pit-fighter`, G03) |
| Archivos de producción modificados | ninguno |
| CSV | no escrito; solo consultas de lectura |

Consultas realizadas con `tools/knowledge/clause_registry.py query` (por id, por consumidor y por estado) y lectura del CSV con `csv.DictReader` para agrupar; la agrupación por `effect_id` y por forma del `id` es reproducible con una consulta por clave. No se ha creado otro CSV, manifiesto ni registro de estados.

El encargo exige, por clave, una explicación técnica de su reutilización o una dependencia de ejecución explícita. La unidad de explicación es el **mecanismo de compilación**: 17 clases (§4) definidas por campos que ya existen en el CSV (`effect_id` o forma del `id`), con recuento exacto y suma 1396. Una clave hereda la explicación de su clase; las claves cuya consecuencia sí llega al duelo están enumeradas una a una en §6, y las 20 que necesitan consumidor de runtime se entregan en §6.3.

## 2. Qué se ha acreditado

El motor NumPy **no compila nada**. Todas las rutas de entrada compilan antes del duelo y entregan un `CompiledFighter`:

- `apps/combat-lab/mordheim_combat_lab/application/analyses.py:72-73,124,165`
- `apps/combat-lab/mordheim_combat_lab/cli/benchmarking.py:104`
- `apps/combat-lab/mordheim_combat_lab/cli/calibration.py:119`
- `apps/combat-lab/mordheim_combat_lab/verification/parity/_replay.py:68`

`mordheim_combat/vectorized/_driver.py:418,426` recibe `CompiledFighter` y solo lee campos del contrato. Por tanto, toda cláusula resuelta en construcción está resuelta **para ambos motores** por la misma ruta, y no requiere duplicación en NumPy; y toda consecuencia que un duelo pueda observar debe viajar en un campo de `CompiledFighter` (§3.3), no en una etiqueta suelta.

Resultado por clase: **1257 claves se agotan en construcción o en datos** (prohibición, permiso, acceso, identidad de objeto, resolución de catálogo o declaración fuera de runtime) y **139 producen un hecho que el duelo puede observar**. De esas 139, **119 ya son leídas por la capa NumPy actual** (campo o etiqueta con consumidor vectorizado, §6.2) y **20 necesitan consumidor de ejecución**: se entregan con clave y función modular al propietario correspondiente (§6.3).

No se ha ejecutado la campaña de paridad (G07) ni se ha reinterpretado ninguna regla. Las comprobaciones ejecutadas están en §10; las no ejecutadas, en §11.

## 3. El límite de compilación compartida

### 3.1. `compile_fighter` (Python)

`packages/python/roster-construction/mordheim_construction/compiler.py::compile_fighter` es el embudo único. Etapas relevantes para este encargo:

| Etapa | Líneas | Qué decide |
| --- | --- | --- |
| Perfil y variantes suministradas | 316-330 | `_profile` + `prepare_source_profile` (perfil canónico o variante suministrada) |
| Reglas de banda automáticas | 330-355 | bindings `runtime.implemented=YES` con `grant=profile/band`: contratos de compilador o `PROFILE_RULE_EFFECTS` |
| Kit de hireling | 356-399 | `hirelingKit` compartido, materiales fijados, admisión de `compiler.hireling-fixed-equipment` |
| Reglas seleccionables | 400-500 | `selectedRules`, acceso/requisitos, bindings mechanic/profile/compiler/trait, `SPECIAL_RULE_EFFECTS` |
| Características | 480-506 | `profile.characteristics` y bonus de reglas, con tope/canonización |
| Contrato de ejecución | 507-509 | `validate_execution_contract`: mecánicas sin ejecución o ejecuciones sin mecánica fallan |
| Listas de habilidades inertes | 510-524 | miembros de tabla impresa sin operador de duelo salen de las listas ejecutables |
| Sustitución de arma | 572-645 | armas naturales, mano vacía, dado gratuito, `implicitWeapon`, kit impreso |
| Carga y validación de equipo | 646-757 | `validate_loadout` (manos y habilidades), armas de mano extra, Great Claw, `_validate_profile_selections`, `validateConstruction` |
| Efectos pasivos | 762-905 | validación de `TRAIT_TYPES`, `apply_execution_effects` (passive/duel_start), supresión de drogas, armadura metálica |
| Rasgos intrínsecos | 1195-1215 | `trait_*` → `EffectSet` (`frenzy`, `ward_save`, `poison_immunity`, `armour_penetration`, salvaciones naturales…) |
| Ataques extra y armas especiales | 1306-1402 | `extra_attacks`, `vomit_attack`, Great Claw, Shield Bash, Spiked Tail, Sword-Gnoblar, armas de mano extra |
| Salvaciones | 1403-1450 | `armour_save`, `natural_armour_save`, `shield_and_skill_effects`, `missile_weapon_limit` |
| Construcción final | 1458-1463 | `CompiledFighter` + `apply_item_modifiers` (runas) + `apply_maintenance` (Weaponsmith) |

### 3.2. El módulo compartido de reglas (TypeScript ejecutado desde Python)

Las decisiones de construcción **no viven en `compiler.py`**: viven en `packages/typescript/domain/eligibility/index.ts` (2939 líneas) y su transporte `packages/typescript/domain/eligibility/bridge.ts`, compilado a `packages/python/roster-construction/mordheim_construction/_eligibility.js` y ejecutado en Python con MiniRacer desde `mordheim_construction/eligibility.py`:

- `eligibility.py:31-40` carga el bundle; `call` (48), `desktop_call` (263) y `construction_call` (277) son el transporte.
- `compile_fighter` invoca el módulo compartido en 597, 604, 636, 737 (`validateConstruction`), 757 (`loadoutRestriction`), y a través de `selected_rules`/`validate_special_rule`/`_validate_profile_selections`.
- El bundle no es una copia manual: `tests/python/construction/test_shared_eligibility.py::test_bundle_matches_a_fresh_generation` reconstruye en memoria con `tools/web/build-eligibility.mjs --check` y falla si el artefacto difiere. Ejecutado: 27 passed (§10).

Consecuencia para el encargo: **759 de las 1396 claves tienen como consumidor declarado una función del módulo TypeScript** (`profileFactsProjection` 411, `entryReachesProfile` 254, `buildAccess` 173, `additionalEquipmentRestriction` 170, `profileEquipmentItems` 108, …). No son "sin consumidor": su decisión se ejecuta en el mismo límite compartido que usa `compile_fighter`, y su resultado es una **denegación** (`ValueError`) o un **hecho admitido** (lista de equipo/habilidades, destinatario, configuración) antes de que exista un duelo.

### 3.3. `CompiledFighter` y lo que el motor NumPy lee

`packages/python/core/mordheim_core/models.py:156-202`. Campos leídos por `vectorized/`:

| Campo | Consumidor NumPy |
| --- | --- |
| `characteristics` | `_driver.py`, `_operators.py:241-260`, `_attacks.py` |
| `main_weapon`, `off_hand`, `extra_attacks`, `unarmed_weapon` | `_operators.py`, `_attacks.py`, `_equipment.py`, `_types.py:120-150` |
| `main_weapon_without_poison`, `off_hand_without_poison` | `_attacks.py:128-152`, `_equipment.py` |
| `global_effects` (campos y `tags`) | `_attacks.py`, `_operators.py`, `_driver.py:30-44` |
| `armour_save`, `helmet_save`, `natural_armour_save`, `natural_armour_worst_save`, `natural_armour_unmodified` | `_operators.py:63-70,179-210` |
| `injury_profile`, `mounted`, `random_characteristics` | `_attacks.py:672-700`, `_driver.py` |
| `off_hand_attacks`, `main_hand_slot`, `off_hand_slot` | `_operators.py`, `_equipment.py` |

Campos que la construcción rellena y **hoy no lee** `vectorized/` (consumidor modular entre paréntesis): `shield_and_skill_effects` (`contexts.py:617`), `skill_effects_only` (`equipment.py:79`), `global_effects_without_equipment` (`equipment.py:68`), `mutation_equipment` (`equipment.py:61`), `natural_armour_stacks` (`mutations.py:265`), `extra_attacks_without_poison` (`contexts.py:118`), `vomit_attack` (`rounds.py:1902`), `stupidity_leadership` / `stupidity_leadership_bonus` / `mob_allies` / `animal_handler_leadership` (`leadership.py:173-303`, `rounds.py:900`), `missile_weapon_limit` y `ballistic_skill` (tiro, fuera del duelo), `construction_tags` (procedencia). No son consecuencia de este encargo salvo donde una clave de §6.3 los produzca; se listan para que el coordinador no los confunda con huecos de G01.

### 3.4. Regla de cierre aplicada

Una clave queda **reutilizada** si su decisión ocurre en `compile_fighter` (directamente o vía el módulo compartido) y su efecto observable, si lo hay, es un campo/etiqueta con consumidor identificado. Una clave queda **entregada** si su contrato declara una consecuencia de duelo y ese consumidor no existe todavía en `vectorized/`. Compartir compilador no se ha usado como certificado de consumo: §6 separa ambos casos.

## 4. Clases de resolución

Criterio determinista sobre el CSV; `effect_id` es el campo que ya publica el mecanismo. Suma exacta 1396.

| Clase | Criterio | Nº | Consecuencia | Runtime |
| --- | --- | ---: | --- | --- |
| C1 | `effect_id = profile.equipment-restrictions` | 502 | Admisión/prohibición de equipo y destinatario | no |
| C2a | `effect_id ∈ {weapon.natural-attacks, profile.natural-attacks}` | 38 | `main_weapon` de ataques naturales | sí, leída |
| C2b | `effect_id = profile.characteristics` | 13 | `characteristics` | sí, leída |
| C3 | `profile.skill-access`, `profile.active-weapon-restrictions`, `compiler.promoted-hero-skill-access`, `compiler.promoted-hero-no-strength-access`, `compiler.forbid-skill-categories`, `compiler.saurus-skill-prohibitions`, `compiler.slayer-skill-options`, `compiler.sister-special-skills` | 45 | Listas y acceso de habilidades | no |
| C5 | `effect_id` empieza por `trait.` | 14 | Rasgo → campo de `EffectSet` | sí, leída |
| C6 | `effect_id` empieza por `special-rule.` | 13 | Efecto/trazo/estadística de regla seleccionable | sí, leída |
| C7 | `effect_id` empieza por `mechanic.` | 22 | Mecánica → `EffectSet`/etiqueta | 20 sí / 2 no (construcción) |
| C8 | `effect_id` empieza por `proposed.` | 10 | Enlace histórico ya materializado o límite de alcance | no |
| C9 | `effect_id` empieza por `compiler.` | 103 | Contrato de compilador (restricción o hecho) | 14 sí / 89 no |
| C10 | Resto de `effect_id` (arma/armadura/defensa/condición/habilidad) | 44 | Identidad y perfil del objeto o regla | 18 sí / 26 no |
| N1 | `source/.../equipment-access.yaml` sin `effect_id` | 335 | Entrada de lista: destinatario, alias, nota | no |
| N2 | `source/catalog/hirelings` sin `effect_id` | 117 | Datos de hireling: referencia, kit, rasgo | no (1 excepción, §6.3) |
| N3 | `source/.../profiles.yaml` sin `effect_id` | 53 | Restricción/permiso de perfil | 5 sí |
| N4 | `source/catalog/{campaign,rules}` sin `effect_id` | 33 | Datos de campaña/mercado/mutación | 2 sí |
| N5 | `item/*` sin `effect_id` | 22 | Identidad, alias o texto impreso | no |
| N6 | `unimplemented.` en id o cláusula | 21 | Declaración fuera de runtime o restricción de construcción | no |
| N7 | `rule/*` sin `effect_id` | 8 | Binding de regla (acceso/requisito/restricción) | no |
| N8 | `mechanic/*` sin `effect_id` | 3 | Mecánica declarada como dato | 1 sí |
| **Total** | | **1396** | | **139** |

## 5. Detalle por clase

### C1 (502) — Elegibilidad de equipo y prohibiciones

- **Dónde**: `eligibility.py::call("loadoutRestriction")` desde `compiler.py:757`, `validate_loadout` (manos) en 683 y `_validate_profile_selections`/`restrictions.py::_validate_bound_equipment_restrictions`; el cuerpo es `index.ts::profileFactsProjection` (2388), `additionalEquipmentRestriction` (2769), `equipmentSetIssues` (505) y `bandEquipmentForbids` (2594).
- **Qué produce**: o un `ValueError` que impide compilar, o una lista de equipo admitida que `compile_fighter` usa para resolver armas por defecto (604-645). No hay estado de duelo que portar; el build ilegal nunca llega a NumPy. Evidencia ejecutada: `norse-explorers-btb/wulfen` con `weapon.sword` → `"weapons" is forbidden for norse-explorers-btb/wulfen`; el mismo perfil sin arma compila `main_weapon.tags == ('weapon.natural-attacks','material.normal')` (§10).
- **NumPy**: nada que consumir; la prohibición precede a ambos motores.
- **Propuesta**: `implemented` para las 502 (comportamiento conectado por la ruta compartida que NumPy ya atraviesa).

### C2a (38) — Ataques naturales y C2b (13) — Características

- **Dónde**: `compile_fighter:572-645` selecciona `weapon.natural-attacks` cuando el perfil no admite arma; las características se suman en 480-506.
- **Qué produce**: `CompiledFighter.main_weapon` / `characteristics`, exactamente los campos leídos en `_operators.py:241-260` y `_driver.py`.
- **NumPy**: leídos; no requieren port.
- **Propuesta**: `implemented`.

### C3 (45) — Acceso a habilidades

- **Dónde**: `index.ts::buildAccess` (1517), `profileSkillLists` (2616), `skillIssue` (475), `specialRuleRestriction` (2631); en Python `eligibility.py::context` (162) y `restrictions.py::_validate_profile_selections`.
- **Qué produce**: admisión o rechazo de la habilidad, y la lista desde la que se elige. La habilidad seleccionada, si tiene contrato ejecutable, entra por `effect_index` (C10) y sigue su propio camino.
- **NumPy**: sin consecuencia propia.
- **Propuesta**: `implemented`.

### C5 (14) — Rasgos que llegan a `CompiledFighter`

Las 14 claves, con hecho compilado:

| Clave | Hecho |
| --- | --- |
| `item/mad_cap_mushrooms::frenzy` | `global_effects.frenzy=True` |
| `mechanic/preparation.head-splitter-mushrooms::frenzy` | `global_effects.frenzy=True` |
| `mechanic/preparation.mad-cap-mushrooms::frenzy` | `global_effects.frenzy=True` |
| `rule/mordheim/black-dwarfs/band--hard-head/trait.concussion-immune::bearer-scope` | tag `concussion_immune` |
| `rule/mordheim/carnival-of-chaos/nurglings--daemonic-aura/trait.natural-armour-save::magical-attacks` | tag `magical-attacks` → `attack.magical` |
| `rule/mordheim/carnival-of-chaos/plague-bearers--daemonic-aura/trait.natural-armour-save::magical-attacks` | idem |
| `rule/mordheim/marauders-of-chaos/band--mark-of-onogal/trait.mark-of-onogal-the-crow::mark-admitted-effects` | `poison_immunity`, tag `mark_of_onogal_the_crow` |
| `rule/trollheim/lustria-lizardmen/kroxigor--scaly-skin-4plus/trait.natural-armour-save::stacks-with-armour-but-not-hardened-leather` | `natural_armour_save` 4, `natural_armour_stacks` |
| `…/trait.natural-armour-stacks::…` | idem |
| `…/trait.natural-armour-worst-save::…` | `natural_armour_worst_save=6` |
| `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/hireling.dramatis.dijin-katal-the-renegade-assassin.rule.perfect-killer/unclassified::perfect-killer` | `armour_penetration=1` |
| `…/grade-2a.yaml/hireling.dramatis.aksho-akhash…rule.daemonic-flesh/unclassified::daemonic-five-plus-save` | `ward_save=5` |
| `…/daemonic-flesh/unclassified::magical-attacks` | `attack.magical` |
| `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.dark-elf-assassin.rule.perfect-killer/unclassified::perfect-killer` | `armour_penetration=1` |

- **Dónde**: `compile_fighter:1195-1215` (`intrinsic_effects` desde `traits`), `compiler.py:900` (`trait_tags`).
- **NumPy**: leídos (`_driver.py:44`, `_operators.py:63,184-210`, `_attacks.py:566-568,678`).
- **Propuesta**: `implemented`.

### C6 (13) — Reglas especiales seleccionables

| Clave | Hecho compilado | Consumo NumPy |
| --- | --- | --- |
| `band--shield-bash` (Bretonnia) | `extra_attacks` (maza S-1) | genérico de ataques extra |
| `band--blessings-of-nurgle-bloated-foulness` | `+1 T`, `+1 W`, `-1 M` | `characteristics` |
| `band--blessings-of-nurgle-mark-of-nurgle` | `+1 W`, `poison_immune` | `characteristics`, `global_effects` |
| `band--mutations-extra-arm` (Cult of the Possessed) | mano extra + ataque/defensa | `extra_attacks`, `global_effects` |
| `band--mutations-great-claw` | `extra_attacks` S+1 | genérico |
| `band--mutations-tentacle` | `incoming_attacks_modifier=-1` | `_driver.py:324-327` |
| `band--skaven-special-skills-tail-fighting` | ataque extra o `+1` salvación | `extra_attacks` |
| `band--strigoi-power-monstrosity` | `+1 W` | `characteristics` |
| `band--necromantic-modification-multiple-limbs` | `attacks_bonus=1` | `_operators.py:241-260` |
| `band--sacred-mark-venom-glands` | `main_weapon` sustituida | `_attacks.py` |
| `band--mutations-extra-arm` (Trollheim) | idem | idem |
| `band--mutations-great-claw` (Trollheim) | idem | idem |
| `band--skaven-special-skills-tail-fighting` (Trollheim) | idem | idem |

- **Dónde**: `contracts.py::SPECIAL_RULE_EFFECTS` (stats/effects/traits) y ramas explícitas de `compile_fighter` para las cuatro reglas cuyo diccionario está vacío (extra arm, great claw, tail fighting, shield bash: 1306-1402).
- **Propuesta**: `implemented`.

### C7 (22) — Mecánicas

20 con consecuencia de duelo y 2 de construcción (`construct-drug-immunity` ×2: `compile_fighter:846-849` filtra las drogas del propio constructo). El detalle de hechos y consumidores está en §6.2/§6.3. Las claves son las que el CSV etiqueta `mechanic.*`; su hecho se obtiene de `effect_index` sin interpretar la regla.

### C8 (10) — Referencias `proposed.*`

Pistas históricas, no mandatos. Los enlaces ya existen en datos o en ramas de compilación, comprobados uno a uno:

- `proposed.item-printed-alias-melee-profile` (2): `load_simulation_mappings` publica `shovel → weapon.halberd` (`status: implemented`).
- `proposed.item-printed-alias-armour-profile` (1): `bronze_breastplate → armour.light-armour`.
- `proposed.rememberer-racial-profile` (1): `source_profiles.py::_supplied_rememberer`.
- `proposed.starting-skill-choice` (1): `VETERAN_TRACKER_SKILLS` en `contracts.py`; la elección se registra y no se simula (417-427).
- `proposed.required-starting-mutation` (1): `compiler.mutant-requires-mutation-at-recruitment`.
- `proposed.single-model-accounting` (2): cada `FighterBuild` es un duelista y un estado; es el contrato de `_driver`, no una mecánica pendiente.
- `proposed.charnel-guard-weapons-training` (1): `compiler.weapons-training-exception`.
- `proposed.falconer-equipment-prerequisite` (1): requisito de destinatario resuelto en `resolveHirelingKit`/`additionalEquipmentRestriction`; el ataque del halcón es otra regla y no se certifica aquí.

- **Propuesta**: `implemented` para los ocho enlaces enumerados; los dos de proyección de una miniatura no cambian (ya son el contrato del motor). Sin mecánica nueva.

### C9 (103) — Contratos de compilador

89 son restricciones, permisos o selecciones resueltas por el contrato compartido (`COMPILER_CONTRACTS` + `profileFacts`/`loadoutRestriction`): no-missile-weapons (20), no-blackpowder-weapons (17), forbid-item-categories (9), forbid-skill-categories (4), promoted-hero-skill-access (4), saurus-skill-prohibitions (5), swabbie-rabble-loadout (2), ignore-difficult-to-use-restrictions (2), weapon-knowledge (2), bow-discipline (2), etc. No producen hecho de duelo; su efecto es que el build ilegal no compila.

14 sí producen hecho, y los 14 son leídos por NumPy:

| Contrato (nº de claves) | Hecho | Consumidor |
| --- | --- | --- |
| `compiler.censer-bearer-loadout` (2) | `frenzy` (757-759) | `_driver.py:44` |
| `compiler.lizardmen-scaly-skin` (4) | salvación natural y `stacks` (659-676) | `_operators.py:188-197` |
| `compiler.bite-attack` (4) | `extra_attacks` | genérico |
| `compiler.strikes-last-bite` (1) | `extra_attacks` | genérico |
| `compiler.woodsmen-quarterstaff` (1) | `main_weapon` S+1 | `_attacks.py` |
| `compiler.knighthood` (2) | tags `promotion.knight-errant`, `rule.knight`, `rule.vain`, `rule.impetuous` | **no leído** → §6.3 |

- **Propuesta**: `implemented` para 101; `in_progress` para las 2 de `knighthood` (psicología de G05).

### C10 (44) — Identidad y perfil de objeto/regla

De las 44, 26 son construcción: restricciones o resoluciones de identidad (boar spear aristócrata, hellblade material/destinatario, lance no-Questing, skull busta ×2, sword héroes, town-crier ×2, pistol del Moot Elder, notas de lista del Ogre Pit Fighter, resoluciones de hireling, etc.); `implemented`.

Las otras 18 producen un perfil ejecutable o una estadística y están enumeradas en §6.2/§6.3 con su consumidor (man-catcher, pointy stick ×2, +1 salvación del House Guard, Attlas ×2, Executioner's Hood, Ienh-Khain ×2, ceremonial scythe, Righteous Fury, Art of Silent Death ×2, Centigors Trample, Hard to Kill, Fanatics Frantic, Poison Daggers ×2). Todas viajan como `main_weapon`, `global_effects` o `characteristics`.

### N1 (335) y N7 (8) — Entradas de lista y bindings de regla

Notas de `equipment-access.yaml` y bindings sin `effect_id`. Su contenido es: etiqueta descriptiva, alias impreso, destinatario, alias de objeto o prohibición. La decisión la toma `entryReachesProfile`/`profileEquipment`/`profileFactsProjection`; el resultado es oferta admitida o rechazo. Ninguna añade estado de duelo. `implemented`.

### N2 (117) — Datos de hireling

Referencias no resueltas, kits fijos y rasgos declarados de `catalog/hirelings`. Se resuelven en `campaign.py::load_hirelings` (79 claves) y en el kit compartido (`resolveHirelingKit`). Son datos de construcción: el hireling compilado es un `CompiledFighter` normal. Excepciones con consecuencia de duelo: `undead-construct` del Bone Goliath (§6.3) y los modos del Wizard's Staff, que son datos de arma (`alternate_mechanic_ids`) resueltos por catálogo; el resto, `implemented`.

### N3 (53), N4 (33) — Restricciones de perfil y datos de campaña

Restricciones de perfil (equipo fijo, listas, armadura permitida, variantes de transfondo), notas del mercado (`market_recipients`/`market_band_scope`), magia, mutaciones y heridas. 5 claves de N3 y 2 de N4 producen ataques naturales (Machine-Ogre, Sabretusks, Plague Rat, Rat Ogres, Companion Filly) o mutaciones con ataque/mano extra; el resto es construcción. `implemented` salvo las 7 con runtime, que ya son leídas (§6.2).

### N5 (22) — Identidad de objeto

Alias y procedencia: los Bone Helmet / Mage Robes / Wizard Robe / Eshin Assassin Clothes remiten a `defence.helmet`, `armour.wizard-s-robe` o `armour.eshin-assassin-robes`; el contrato dice expresamente "provenance error, not a grant". Ninguno adquiere un efecto nuevo. `implemented`.

### N6 (21) — Declaradas fuera de runtime

`unimplemented.*`: monturas, constructos de Clockworkers, herencia de listas, listas de habilidades ya existentes, `not-a-slayer`, etc. Su contrato admite solo la parte de construcción y excluye el subsistema (montura, arco, campaña). No deben convertirse en mecánica nueva; `implemented` donde la parte admitida está conectada, y nota de alcance donde el resto queda fuera.

### N8 (3) — Mecánicas declaradas como dato

`mechanic/defence.wolf-pelt-cloak` ×2 (prohibiciones del Wolf-Priest, construcción) y `mechanic/mechanic.mark-of-arkhar::bloodfather-role` (rol + acceso + efecto de combate ya cubierto por la clave de frenesí). `implemented` / `in_progress` según §6.3.

## 6. Consecuencias de runtime

### 6.1. Cómo leer esta sección

Los hechos se agrupan por **campo de `CompiledFighter`**. Una clave de C2/C5/C6/C7 se localiza por su `effect_id` (está en el CSV); las de C9/C10/N3/N4/N8 están enumeradas. "Leída" significa que `vectorized/` usa ese campo o etiqueta en la línea citada; no es una prueba de paridad.

### 6.2. Hechos ya consumidos por NumPy (119 claves)

| Hecho compilado | Claves | Consumidor NumPy |
| --- | --- | --- |
| `global_effects.frenzy` | `item/mad_cap_mushrooms::frenzy`; `mechanic/preparation.head-splitter-mushrooms::frenzy`; `mechanic/preparation.mad-cap-mushrooms::frenzy`; `mechanic/mechanic.mark-of-arkhar::whole--scope--frenzy`; `rule/mordheim/marauders-of-chaos/band--mark-of-arkhar/mechanic.mark-of-arkhar::whole--scope--frenzy`; `compiler.censer-bearer-loadout` ×2 | `_driver.py:44` |
| `extra_attacks` | C6: shield-bash, great-claw ×2, tail-fighting ×2, Venom Glands; C9: bite-attack ×4, strikes-last-bite; C10: Centigors Trample; N3/N4: ataques naturales de Machine-Ogre/Sabretusks/Plague Rat/Rat Ogres/Companion Filly | bucle de `extra_attacks` en `_attacks.py` |
| `main_weapon` = ataques naturales | C2a (38) | `_attacks.py:149-176`, `_operators.py:262-312` |
| `main_weapon` = perfil de objeto | `item/man_catcher::whole`; pointy stick ×2; `house-guard +4`; `weapon.ienh-khain` ×2; `weapon.ceremonial-scythe`; Poison Daggers ×2; `weapon.attlas-plate-mail` | `_attacks.py`, `_equipment.py` |
| `characteristics` | C2b (13); Bloated Foulness; Mark of Nurgle; Monstrosity; Multiple Limbs (`attacks_bonus`); `armour.attlas-plate-mail` (herida extra); `condition.executioners-hood` (+1 S); Snorri resultados 2 y 5 | `_driver.py`, `_operators.py:241-260` |
| `armour_save` / `natural_armour_save` / `natural_armour_worst_save` | Kroxigor ×3; Companion Filly; `compiler.lizardmen-scaly-skin` ×4 | `_operators.py:188-210` |
| `global_effects.ward_save` | Daemonic Flesh (Aksho) | `_operators.py:63-70` |
| `global_effects.armour_penetration` | Perfect Killer ×2 | `_operators.py:184-196` |
| `global_effects.poison_immunity` | Mark of Onogal; Mark of Nurgle | `_attacks.py:131-137,456,811` |
| tag `concussion_immune` | Hard Head | `_attacks.py:678` |
| tag `attack.magical` | Nurglings/Plague Bearers/Aksho (3) | `_attacks.py:566-568` |
| `incoming_hit_modifier` | Frustratingly Tiny | `_attacks.py:211` |
| `incoming_attacks_modifier` | Tentacle | `_driver.py:324-327` |

Las claves de C2a, C2b, C5, C6 y las 14 de C9 consumidas son exactamente las que el CSV etiqueta con su `effect_id`; las de C10 son las 18 enumeradas arriba; las de N3/N4 son las 7 enumeradas.

### 6.3. Claves entregadas a otros propietarios (20)

Todas tienen contrato aceptado y hecho compilado; falta el consumidor NumPy. Se entrega **clave + función modular real** para que el coordinador asigne; G01 no las implementa (sin propiedad de archivos de motor).

| # | Clave | Hecho compilado | Consumidor modular | Propietario |
| ---: | --- | --- | --- | --- |
| 1 | `mechanic/mechanic.flesh-peddler::whole` | tag `mechanic.flesh-peddler` (+1 a impactar a la marca) | `contexts.py` (marca suministrada) | G03 |
| 2 | `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.halfling-pimp.rule.flesh-peddler/mechanic.flesh-peddler::rule` | idem | idem | G03 |
| 3 | `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.clan-skryre-rat-ogre.rule.bio-machinery/unclassified::psychology-immunity` | tag `mechanic.psychology-immunity` | `psychology.py` | G05 |
| 4 | `source/catalog/hirelings/hired-swords/grade-1a.yaml/hireling.hired-sword.beast-hunter.rule.skull-rack/unclassified::causes-fear-vs-beastmen` | tag `mechanic.causes-fear` (vs Beastmen) | `psychology.py` | G05 |
| 5 | `rule/mordheim/watchmen-mim/band--fanatical/unimplemented.watchmen-mim.band.fanatical::fanatical-advance--scope--automatic-leadership` | tag `mechanic.automatic-leadership` | `leadership.py` | G05 |
| 6 | `source/catalog/hirelings/hired-swords/grade-1b.yaml/hireling.hired-sword.chaos-centaur.rule.drunken/unclassified::drunken-turn-roll` | estado por turno (`condition`/frenesí) | `rounds.py` | G06 |
| 7 | `source/catalog/hirelings/dramatis-personae/grade-1b.yaml/@/profiles/8/unresolved_references/0/unclassified::rule` | tag `mechanic.mesmerising-dance` | `rounds.py` | G06 |
| 8 | `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priest-of-morr-miracle-workers.rule.morrs-servant/mechanic.morrs-servant::rule` | tag `mechanic.morrs-servant` | `psychology.py` | G05 |
| 9 | `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priestess-of-shallya.rule.strictures/mechanic.shallya-strictures::rule` | tag `mechanic.shallya-strictures` | `state.py` | G02 |
| 10 | `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.priestess-of-shallya.skill.tranquil-aura/mechanic.shallya-tranquil-aura::rule--scope--weapon-skill-penalty` | penalización de WS al atacante | `contexts.py` | G03 |
| 11 | `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers.skill.enlightened/mechanic.sigmar-enlightened::rule` | tag `mechanic.sigmar-enlightened` | `leadership.py` | G05 |
| 12 | `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers.skill.symbol-of-unity/mechanic.sigmar-symbol-of-unity::rule` | tag `mechanic.sigmar-symbol-of-unity` | `contexts.py` | G03 |
| 13 | `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.whaler.rule.marine-hunter/mechanic.marine-hunter::rule` | tag `mechanic.marine-hunter` | `attacks.py` | G04 |
| 14 | `rule/mordheim/dreamwalkers-cult-of-morr-fbg/dreamer--guiding-dream/mechanic.guiding-dream::whole--scope--guiding-dream-table` | resultado suministrado de la tabla | `state.py` | G02 |
| 15 | `mechanic/mechanic.curse-of-the-revenant::requires-great-thirster` | tag `mechanic.great-thirster` (recuperación) | `aftermath.py` | G06 |
| 16 | `mechanic/mechanic.snorri-drunk::snorri-drunk` | tag `condition.snorri-stench` (−1 a impactar) | `contexts.py:516` | G03 |
| 17 | `rule/mordheim/bretonnian-chapel-guard/squires--knighthood/compiler.knighthood::whole--scope--knight-errant-construction` | tags `rule.knight`, `rule.vain`, `rule.impetuous` | psicología (`vain`/`impetuous`) | G05 |
| 18 | `rule/mordheim/bretonnian-chapel-guard/squires--knighthood/compiler.knighthood::whole--scope--squire-construction` | idem | idem | G05 |
| 19 | `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.bone-goliath.rule.undead-construct/unclassified::undead-construct-ignores-injuries-on-four` | tag `mechanic.undead-construct` | `attacks.py:832` | G04 |
| 20 | `source/catalog/hirelings/dramatis-personae/core.yaml/@/profiles/1/unresolved_references/0/unclassified::whole` | `skill.righteous-fury` (reroll de impactos contra enemigos nombrados) | `contexts.py:245` | G03 |

Nota fuera de recuento: `source/catalog/rules/special-rules.yaml/shared-rule.living/unclassified::living` no produce hecho (no hay exención de Psicología). Se entrega a G05 para que registre la ausencia; no requiere código.

Notas de entrega:

- La clave 5 declara una **ausencia** (no hay regla de psicología que aplicar): el consumidor no debe inventar un efecto. La nota `living` se entrega por el mismo motivo.
- La 16 ya consume el frenesí por `global_effects.frenzy`; la parte pendiente es solo el estorbo a impactar (`condition.snorri-stench`).
- La 19 es la única clave de N2 con ejecución propia; el resto de datos de hireling no la necesita.
- `mechanic/mechanic.frustratingly-tiny::cannot-combine-with-big-bully` **no** se entrega: su efecto `incoming_hit_modifier=-1` ya es leído; la exclusión con Big Bully es construcción.
- `mechanic.drug-immunity` (2 claves) es construcción: `compile_fighter:846-849` suprime las drogas del constructo; no hay estado que portar.

## 7. Claves sin `consumer` (136)

Recuento real del CSV: **136** claves principales con `consumer=[]` (el anexo marca "consumer vacío" en más filas; la diferencia son filas cuyo consumidor es una función del módulo compartido). Se explican por su enlace, sin reabrir la regla:

| Grupo | Nº | Enlace recuperado |
| --- | ---: | --- |
| Alias/procedencia de objeto (Bone Helmet, Mage Robes, Wizard Robe, Eshin, Katana, Knuckledusters, Long Daggers, Shock Rod) | 22 | `catalog/items/*` `mechanic_id`/`mapping`; el alias no concede efecto |
| Notas de lista con solo etiqueta o destinatario | ~95 | `entryReachesProfile`/`profileEquipment` sobre datos de la propia lista |
| Constructos Clockworkers / Big Bully / Frustratingly Tiny | 4 | `compile_fighter` (in-built equipment, `drug-immunity`, exclusión) y `unimplemented.*` de alcance |
| Hireling: modos del Wizard's Staff, perfil del Horseman, Ulli, rasgo `living`, Bone Goliath | 6 | Catálogo (`alternate_mechanic_ids`, perfiles normalizados) y `load_hirelings`; el Bone Goliath se entrega (§6.3, #19) |
| Sun Gauntlet, Attlas Plate Mail, Executioner's Hood, armas de lista | 6 | `mechanic_id` del catálogo consumido por `compile_fighter` (§6.2) |
| Resto (etiquetas de perfil, armadura permitida, etc.) | 3 | `profileFactsProjection` |

Ninguna de las 136 queda "oculta bajo compilación compartida": o su enlace es dato de catálogo ya resuelto por el compilador, o es una consecuencia de runtime enumerada en §6.

## 8. Claves de apoyo (6)

| Clave | Contribución G01 | Estado |
| --- | --- | --- |
| `rule/mordheim/pit-fighters/dwarf-troll-slayer--pit-fighter/trait.pit-fighter::whole` | El rasgo se acepta en `TRAIT_TYPES` y se materializa como etiqueta `pit_fighter` en `global_effects.tags` (`compiler.py:900,1203`). Ejecutado: `pit-king` compila `tags=['pit_fighter','band.pit-fighters']`. | Sin consumidor en modular ni en NumPy (grep global). El contrato de la fila lo declara deliberadamente inerte: el efecto impreso es +1 WS/+1 A dentro de edificio/ruina y el terreno queda fuera del duelo aislado. No procede portar un bono incondicional. |
| Las otras 5 (`ogre-pit-fighter`, `pit-fighters`, `pit-king`, `pit-veterans`, `pursuers`) | Idéntico: misma ruta, mismo tag, mismo contrato. | G03 cierra; la contribución de esta capa es la aceptación de construcción y la etiqueta de procedencia, sin efecto de duelo. |

Propuesta: `implemented` para las 6 si el coordinador acepta que la totalidad admitida es la concesión de construcción (así lo dice su contrato); si exige un consumidor de ejecución, el estado correcto sería `blocked` por alcance (terreno fuera del duelo), nunca `pending` por falta de código.

## 9. Cambios propuestos al CSV (por claves)

No se ha escrito el registro. Propuestas, conservando `status.native` y el resto de campos:

| Clase | Claves | `status.numpy` propuesto | Nota propuesta |
| --- | ---: | --- | --- |
| C1, C3, C9 (89), C10 (26), C8, N1, N2 (116), N3 (48), N4 (31), N5, N6, N7, N8 (2) | 1257 | `implemented` | "Resuelto en la compilación compartida que consume NumPy; sin consecuencia de duelo que duplicar." |
| C2a, C2b, C5, C6, C9 (14), C10 (18), N3 (5), N4 (2), N8 (1) | 119 | `implemented` | "Hecho compilado leído por vectorized en <campo>; paridad pendiente de G07." |
| §6.3 (20) | 20 | `in_progress` | "Hecho compilado; falta consumidor NumPy. Entregado a <grupo>; consumidor modular <archivo:línea>." |
| Claves de apoyo (6, ya contadas en las filas anteriores) | — | `implemented` (o `blocked` por alcance) | "Construcción + etiqueta `pit_fighter`; sin efecto de duelo por contrato." |

Las 6 claves de apoyo (`skill.pit-fighter`, una por banda con el rasgo) están dentro de C10 y ya suman en las 1257; se listan aparte solo porque su disposición es discutible. El recuento cierra: **1257 + 119 + 20 = 1396**.

Ninguna fila se propone `verified`: eso exige la comparación de G07 sobre la versión integrada. Las 527 filas con rutas de verificación inexistentes (§11) conservan su estado actual hasta que el coordinador decida.

## 10. Comandos ejecutados y resultados

1. Consultas del registro (muestreo y agrupación):
   `python -X utf8 tools/knowledge/clause_registry.py query --id "rule/mordheim/pit-fighters/pit-king--pit-fighter/trait.pit-fighter" --fields …`
   → fila con `consumer=[]`, verificación por inspección y nota de disposición C10. Sin escritura.
2. Frescura del bundle compartido + paridad de decisiones de construcción:
   `python -X utf8 -m pytest tests/python/construction/test_shared_eligibility.py -q` → **27 passed** (incluye `test_bundle_matches_a_fresh_generation`, que regenera con `tools/web/build-eligibility.mjs --check`).
3. Suites de construcción citadas como consumidor:
   `python -X utf8 -m pytest tests/python/construction/test_equipment_restrictions_offer.py tests/python/construction/test_equipment_restrictions_verdicts.py tests/python/construction/test_skill_concessions.py -q` → **89 passed**.
4. Compilación de extremo a extremo (script de inspección, sin archivo de test):
   - `pit-king` con `band--pit-fighter-skill-force-of-will` → `global_effects.tags` contiene `pit_fighter`.
   - `preparation.mad-cap-mushrooms` → `global_effects.frenzy=True`.
   - `norse-explorers-btb/wulfen` → `main_weapon.tags == ('weapon.natural-attacks','material.normal')`, `strength_bonus=0`, `target_armour_bonus=0`; con `weapon.sword` → `ValueError: "weapons" is forbidden for norse-explorers-btb/wulfen`.
5. Integración NumPy mínima: `simulate_batch(f1, f2, 64, default_rng(7), 50)` con `f1` compilado con Mad Cap Mushrooms → `(46, 18, 0)`, sin excepción; confirma que el campo compilado por una clave de G01 atraviesa la ruta vectorizada.

No se ha ejecutado la matriz de paridad, ni la suite modular completa, ni la suite TypeScript directa.

Pruebas nuevas: **ninguna**. Este encargo no añade comportamiento; las comprobaciones 2 y 3 ejecutan pruebas mantenidas que ya cubren el límite compartido, y la 4-5 es inspección puntual, no una suite. Un test nuevo aquí duplicaría cobertura existente sin acreditar nada que el coordinador no pueda leer en §10.

### 10.1. Implementación, integración y verificación

| Plano | Estado | Evidencia |
| --- | --- | --- |
| Implementación | Ninguna, por alcance: no hay archivos de producción modificados | §1 |
| Integración | Ninguna: el único artefacto nuevo es este documento | `git status` |
| Verificación | Recuento del registro (1396 claves, 17 clases, sumas 1257+119+20), bundle compartido fresco, suites de construcción verdes y paso mínimo por `simulate_batch` | §10 |

## 11. Limitaciones y discrepancias

- **Cobertura de lectura, no de paridad.** "Leída" significa que `vectorized/` accede al campo/etiqueta; no acredita que el resultado coincida con el modular. Eso es G07. Por eso no se propone `verified`.
- **Rutas de verificación obsoletas en el CSV**: 527 de las 1396 claves citan al menos una ruta inexistente (216 referencias a `docs/knowledge/2a2b/tasks/T13-effect-routing.yaml`, 70 a `test_c01c_natural_variants.py`, 60 a `test_t13_construction_recipients.py`, 58 a `test_c01a_intrinsic_attacks.py`, 46 a `%TEMP%/c03b-evidence-final.txt`, etc.). No se han corregido: el registro lo escribe el coordinador. Las suites reales siguen existiendo con otro nombre (`test_equipment_restrictions_offer.py`, `test_skill_concessions.py`).
- **Etiqueta "consumer vacío" del anexo**: el CSV tiene 136 filas con `consumer=[]`, no más. Las filas que el anexo marca así pero tienen consumidor TypeScript no son un hueco: su decisión se ejecuta en el módulo compartido. Conviene alinear la nota al preparar el cierre.
- **Discrepancia concreta, sin corregir**: `sources/knowledge/catalog/items/combat-equipment.yaml:729` describe el `shovel` como "Counts as an axe in close combat", mientras el contrato de su cláusula y `load_simulation_mappings` lo resuelven como `weapon.halberd` (`{'item_id':'shovel','status':'implemented','mechanic_id':'weapon.halberd'}`). El enlace ejecutable es el halberd; el texto del catálogo es el que diverge. Se comunica para que su propietario decida; no se ha tocado.
- **Tags sin consumidor que no se entregan**: `rule.venom-glands`, `rule.shield-strike`, `rule.spiked-tail`, `rule.bite-attack`, `rule.great-claw` no se referencian por nombre en `vectorized/`, pero el ataque viaja en `extra_attacks` y lo consume el bucle genérico; la etiqueta es procedencia. No son huecos.
- **Campos de `CompiledFighter` no leídos** (§3.3): son alcance de otros grupos, no de G01; se listan para que el coordinador no los lea como consecuencias ocultas de estas claves.
- **Sin archivos de producción**: cualquier conexión que exigiera editar motor o tests queda fuera de este encargo y se ha formulado como propuesta (§6.3, §9). No hay, por tanto, bloqueos de código: los únicos bloqueos son de asignación (las 20 claves de §6.3 esperan dueño) y de decisión (disposición de las 6 de apoyo, §8).

## 12. Trabajo restante

1. Coordinador: asignar las 20 claves de §6.3 a G02–G06 y aplicar las propuestas de §9 preservando `status.native`.
2. G03: cerrar las 6 claves de apoyo con la disposición inerte ya contratada (terreno fuera del duelo), no con un bono incondicional.
3. G07: comparar los hechos de §6.2 en la versión integrada; solo entonces `verified`.
4. Propietario del catálogo: resolver la discrepancia del `shovel` (§11).
5. Coordinador del registro: sustituir las rutas de verificación obsoletas.
