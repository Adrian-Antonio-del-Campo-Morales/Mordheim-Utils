# P00 — Inventario de comportamientos y contrato P01/P02

> **Alcance vigente (2026-10-21): preparación de tests con el vectorial todavía
> en implementación.** Las sondas y cifras de este documento son evidencia
> histórica, no requisitos de ejecución para aceptar P00–P03. Las llamadas,
> estados y `accepted` de §7 describen el futuro ejecutor; no obligan a ejecutarlo
> contra NumPy/nativo durante la preparación. Las dependencias de estado,
> observación, consumo o publicación se especifican y asignan sin esperar a que el
> motor las implemente. Se puede entregar la preparación terminada con esas
> dependencias explícitas, sin acreditar paridad. Rigen el plan y los prompts
> actualizados; las correcciones de diseño están en
> [la revisión de coordinación](COORDINATOR-progress-review.md).

Estado: **inventario y contrato, revisión 4** (corrección de la revisión 3 en la
misma entrega P00). No se modificó código de producción, KB, CSV canónico, corpus
ni pruebas de P01/P02; no hay commits. La batería nueva **no está construida ni
acreditada**: este documento fija qué debe existir y con qué interfaz, no declara
cobertura. No se ejecutaron NumPy, nativo ni campañas de paridad; solo lectura y
scripts estáticos sobre el registro, la reconciliación y el CSV de diseño.

Lo que cambia la revisión 4 respecto a la 3:

1. **63 variantes, ninguna «other».** §4.4 divide `Bxx.y` cuando el contrato
   difiere: miedo/psicología (B11), liderazgo local (B14) y secuelas (B15) dejan
   de compartir un cajón. Las 182 claves «other … rules» tienen decisión explícita
   y `behaviour-inventory.csv` suma 1914 claves, 63 variantes y 0 genéricas.
2. **Testigo tipado.** `Witness(kind, present, absent)` con
   `counter|flag|category|direct-result|hash` (§7.2/§7.6). `acting-order` es una
   categoría 0/1 y `equipment` un hash: no se evalúan con `> 0` ni «cero eventos».
   `condition`/`wounds` solo son testigo directo en B07/B15.
3. **Contexto existente.** `DuelContext.nearby`/`distances` y
   `LocalParticipant` son la entrada de B14; `support`/`support_distance`
   desaparecen. Se separan representación, consumo y publicación, y se admiten
   controles «sin líder» y «fuera de radio». `off_hand_id` sustituye a
   `off_weapon_id`.
4. **Cobertura por variante.** Un caso por obligación no basta: cada variante
   requerida necesita su testigo propio (o `also_covers` explícito). Las 98
   `shared-operator` se informan por separado (9 exactas/89 pendientes).
5. **NOT_ACTIVATED antes que divergencia.** Si el control positivo no activa, el
   resultado es `NOT_ACTIVATED`, no `DIVERGENCE` entre motores. El contraste de
   testigo sustituye a la multiplicidad; la comparación enfocada se admite sin
   exigir instrumentación nueva.
6. **CSV transferido.** `behaviour-inventory.csv` es la foto de diseño de P00;
   P01 importa la pertenencia una vez y pasa a ser su propietario.

Se conservan la reconciliación de §3 (3457 admitidas, 1914 `runtime`+`mixed`, 189
`unlocated`, 1256 `shared`, 98 `shared-operator`), la evidencia válida y el defecto
`injury` de §4.3.

Fecha: 2026-10-21. Raíz: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK`.

---

## 1. Base recibida

| Dato | Valor |
| --- | --- |
| Revisión | `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340` (HEAD) |
| Rama | `main` |
| Cambios locales | 143 entradas en `git status --porcelain` al recibir la copia; 150–154 durante la revisión y **369 al cerrar**, por ediciones concurrentes del propietario sobre el motor (`kernel.py`, `vectorized/_driver.py`, `vectorized/_types.py`, `parity/_replay.py`, entre otras) y por los nuevos archivos de P01/P02. P00 no escribió fuera de `TMP_VECTORIAL_ENGINE_2A2B/parity_update/` |
| Entregas dependientes | Ninguna: P00 es la primera fase |
| Registro | `sources/knowledge/verification/clause-contracts.csv`; sha256 al recibir `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`; sha256 en esta corrección `2096df6eba24ed106b03a6033b1e438793dc1bc4bec40ac02b7423a8fc4056f3` (edición concurrente del propietario, no de P00). Filas, `consumer`, `effect_id` y `relation` de las 1914 claves de ejecución no cambiaron: 4556 filas, 3457 admitidas, 189 `consumer=[]`, clasificación 1256+98+1914+189. El inventario se reconstruyó contra este archivo y salió idéntico (mismo sha256 del CSV) |
| Entorno ejecutado | Python 3.10.6, NumPy 2.2.6, Windows 10.0.19041, 16 CPU, host `PCergate` |

La copia de trabajo recibida **es la base válida**, no HEAD: los cambios locales
forman parte del material leído. No se ha descartado, reformateado ni revertido
ninguno. Este documento no depende de que el coordinador reconstruya la base
desde HEAD. La copia cambió durante la revisión (P00 no escribió fuera de su
carpeta): los símbolos citados se releyeron al cerrar, y cuando un hallazgo
depende de una línea concreta se cita la revisión de la copia, no HEAD.

Código y datos realmente usados para el inventario (lectura y ejecución):

- `sources/knowledge/verification/clause-contracts.csv` (registro canónico) y
  `tools/knowledge/clause_registry.py`.
- `TMP_VECTORIAL_ENGINE_2A2B/G00..G06_*.md`, sección `## Claves principales asignadas`.
- `apps/combat-lab/mordheim_combat_lab/verification/parity/`:
  `_vectorized.py` (`verify_vectorized_parity`, `_exact_operator_checks`),
  `_specifications.py` (`SPECIFICATION_ADAPTERS`, `verify_specification_parity`,
  `_apply_vector_state_overrides`), `_replay.py` (`replay_duel`,
  `ReplayObservation`), `_statistical.py` (`compare_statistical_parity`, puerta
  seis sigma), `_deep.py` (`DeepPair`, `deep_test_scenarios`), `_truncations.py`,
  `_report.py` (`ParityReport`, `StatisticalParityResult`,
  `SpecificationParityReport`, `parity_report_payload`).
- `apps/combat-lab/mordheim_combat_lab/cli/scenarios.py`
  (`BenchmarkScenario`, `DEEP_SCENARIOS`, `deep_test_scenarios`)
  y `cli/commands.py` (`parity_command`, opciones `--level`, `--pair-set`).
- `packages/python/combat-engine/mordheim_combat/kernel.py`
  (`compile_duel_plan`, `require_optimized_support`),
  `modular/duel.py` (`simulate_duel_reference`, `simulate_duel_observed`),
  `modular/state.py` (`FighterState`, `DuelState`),
  `vectorized/_driver.py` (`_resource_observation`, `simulate_batch_observed`,
  `batch_plan`, `_batch_seed`), `vectorized/_types.py` (`CombatState`,
  `VectorBatchObservation`), `vectorized/_state.py` (`initialize_fighter`),
  `vectorized/_driver.py` y `modular/{rounds,state,pools,attacks,psychology,leadership,aftermath}.py`.
- `packages/python/core/mordheim_core/models.py` (`FighterBuild`,
  `CompiledFighter`, `DuelContext`, `ObservedDuelResult`),
  `mordheim_core/dice.py` (`SeededDice`, `ScriptedDecisions`, `AlwaysAccept`,
  `AlwaysReject`), `mordheim_construction/compiler.py` (`compile_fighter`).
- `tests/E2E/modular-engine/{README.md,corpus.py,runner.py,cases/**}` y
  `apps/combat-lab/mordheim_combat_lab/verification/{consumers,dice}.py`.
- `tests/specs/semantic/**` (703 fixtures, cargadas con `load_fixtures`).

---

## 2. Trabajo terminado y archivos

Todo bajo `TMP_VECTORIAL_ENGINE_2A2B/parity_update/`. No hay cambios de producción.

| Archivo | Contenido |
| --- | --- |
| `P00-deliverable.md` | Este documento |
| `P00-results/reconcile_universe.py` | Reconciliación reproducible del universo admitido: registro + anexos G00–G06 + E2E |
| `P00-results/universe-reconciliation.csv` | 3457 filas, una por clave admitida (`id,clause_id`), con propietario, clase de consumidor, familia, escenarios E2E, disposición, `effect_id`, `relation` |
| `P00-results/universe-summary.txt` | Agregados usados en las tablas de §3–§4 |
| `P00-results/localize_unlocated.py` | Localización de las 189 claves con `consumer=[]`: lee `verification`/`notes` del registro y busca menciones exactas en el repositorio (excluye el propio registro) |
| `P00-results/unlocated-localization.csv` | 189 filas: referencias de `verification` por tipo, menciones fuertes, marca de bloqueo y clase propuesta (nunca un estado) |
| `P00-results/unlocated-keys.txt` | Agregados y lista de claves sin traza o solo con mención externa |
| `P00-results/contract_probe.py` | Sonda del contrato revisado: compila `FighterBuild`, ejecuta oráculo y lote, mide determinismo/forma y comprueba qué publica cada dataclass |
| `P00-results/contract-probe.txt` | Salida: `row0_equals_solo=False` (medido), `repeat_is_deterministic=True`, `shape_mismatch=none`, campos publicados |
| `P00-results/baseline_probe.py` | Sonda de línea base de las entradas de paridad existentes |
| `P00-results/spec-parity-baseline.txt` | Salida de la sonda: entorno, revisión, sha del registro, recuentos y los 60 casos no-PASS (detalle truncado a 260 caracteres; se reproduce completo reejecutando) |
| `P00-results/initialize_divergence_probe.py` | Separación `shape-only` / `shared-value` de las 35 divergencias `initialize` |
| `P00-results/initialize-divergence.txt` | Resultado: 28 `shape-only`, 7 con diferencia real en campos comunes |
| `P00-results/inventory_probe.py` | Sonda del pipeline `consumer`/`effect_id` de cada clave de ejecución; base del operador decisivo |
| `P00-results/inventory-probe.txt` | Salida de la sonda de inventario |
| `P00-results/stage_probe.py` | Clasificador del operador decisivo: último símbolo específico del pipeline con precedencia del `effect_id` |
| `P00-results/stage_report.py` | Agrupación por variante y estado; base de §4.4 |
| `P00-results/stage_effects.py`, `symbol_probe.py` | Reparto de efectos por operador y comprobación de símbolos citados |
| `P00-results/inventory_build.py` | Generador de `behaviour-inventory.csv`; decisión explícita por contrato (`SPLIT_EFFECT`, `OTHER_EFFECT`, `KEY_OVERRIDE`, `FORCED_KEYS`), no por substring. Falla si una clave genérica no tiene decisión |
| `P00-results/behaviour-inventory.csv` | **1914 filas, 63 variantes** `clave → variante → estado → referencia → dependencia`; pertenencia exacta de §4.4, sin etiquetas «other». sha256 `58beba4428b676c88393605db7c6eb51bfe7f2b8a886bd4240ce29f7b09e4955`. Foto de diseño transferida a P01; no es dependencia de ejecución |
| `P00-results/validate_inventory.py`, `inventory-validation.txt` | Validación estática de claves, pertenencias, sumas, referencias y coherencia del CSV; sin motores |
| `P00-results/behaviour-summary.txt`, `inventory-build.txt`, `stage-report.txt`, `stage-effects.txt`, `symbol-probe.txt`, `variant-effects.txt` | Agregados y comprobaciones del inventario |
| `P00-results/shared_operator_review.py` | Revisión de las 98 claves `shared-operator` contra las comprobaciones exactas |
| `P00-results/shared-operator-review.tsv`, `shared-operator-detail.txt` | Resultado: 9 con evidencia exacta (y solo para una variante), 89 pendientes |
| `P00-results/reference_check.py`, `reference-check.txt` | Validación de los 33 orígenes `e2e:` de P01 contra el corpus: 1 identidad inexistente |
| `P00-results/section4.md`, `section5.md`, `section7.md` | Borradores vigentes de las secciones 4, 5 y 7 de este documento (revisión 4) |

No se ha creado ningún registro paralelo de estados ni una segunda suite. El CSV
de reconciliación es una **foto de diseño** desechable, no una fuente canónica que
haya que mantener sincronizada (instrucción común 10).

---

## 3. Universo admitido y reconciliación

### 3.1 Método

Se unieron tres fuentes existentes, sin interpretar reglas:

1. Registro: admitido = `clause_scope == "YES"`.
2. Anexos de claves principales G00–G06: cada `(id, clause_id)` recibe **un**
   propietario, sin duplicados (el script aborta si dos anexos reclaman la misma
   clave).
3. Corpus E2E: `audit_id` + `covers` de cada escenario YAML.

La familia se asigna por el **módulo de ejecución** del consumidor (no por
etiqueta ni por nombre de función), con el orden de precedencia documentado en
`reconcile_universe.py` (`RUNTIME_FAMILIES`). La clase separa compilador
compartido (`SHARED_MARKERS`) de comportamiento ejecutado.

### 3.2 Resultado

| Medida | Valor |
| --- | --- |
| Filas del registro | 4556 |
| Claves admitidas | **3457** |
| Claves principales en anexos | 3457 |
| Admitidas sin propietario | **0** |
| Claves de anexo no admitidas | **0** |
| Admitidas con ≥1 escenario E2E | 1911 |
| Admitidas sin escenario E2E | 1546 |
| Filas de ejecución (`runtime` + `mixed`) | 1914 |
| De ellas con ≥1 escenario E2E | 1507 |
| De ellas sin escenario E2E | 407 |

Reconciliación completa: no hay clave huérfana ni clave inventada. Que una clave
tenga fila **no acredita nada**: acredita que su disposición está decidida.

### 3.3 Propietario y clase de consumidor

| Propietario | Claves |
| --- | --- |
| G01 compilación compartida | 1396 |
| G03 operadores y contexto | 941 |
| G05 psicología y liderazgo local | 637 |
| G04 ataques, equipo y reacciones | 280 |
| G06 rondas, recuperación e integración | 187 |
| G02 estado, recursos y mutaciones | 12 |
| G00 base de admisión | 4 |

| Clase | Claves | Disposición |
| --- | --- | --- |
| `shared` | 1256 | Compilación compartida: el mismo código produce el combatiente para ambos motores; **un duelo nuevo no añade prueba** |
| `shared-operator` | 98 | Único consumidor de ejecución `combat/phases`: **no es una clase de equivalencia**. Solo 9 tienen evidencia exacta y solo para una variante; 89 quedan pendientes (§4.6) |
| `runtime` | 1461 | Requiere caso de ejecución comparado |
| `mixed` | 453 | Requiere caso de ejecución **y** conserva traza de compilación |
| `unlocated` | 189 | El registro no nombra consumidor: **localización pendiente**, no contrato estático |
| Total | 3457 | |

Las 1256 `shared` **no** generan un duelo nuevo: el mismo código produce el
combatiente para ambos motores, y son obligación estructural de compilación. Las
98 `shared-operator` tampoco exigen un duelo genérico por clave, pero **no** se
presumen equivalentes: cada grupo se vincula a una comprobación exacta o queda
como obligación diferencial pendiente (§4.6). `runtime` + `mixed` = **1914 claves
(55 %)** que sí necesitan observación ejecutada.

`unlocated` = 189 claves (5 %) con `consumer == []`. Un consumidor vacío **no
prueba** que la cláusula sea estática: significa que el registro no sabe dónde se
consume. `localize_unlocated.py` busca la implementación en el propio registro
(`verification`, `notes`, `pending`) y en el repositorio:

| Evidencia encontrada | Claves |
| --- | --- |
| `verification` cita código (`packages/`, `apps/`, `tools/`) | 32 |
| `verification` cita solo pruebas | 27 |
| Mención fuera de código (KB, revisiones, E2E) | 128 |
| Sin ninguna traza | 2 |

Ejemplo de por qué no son estáticas: `rule/mordheim/fen-guard-mim/band--bark-skin/trait.natural-armour-save::no-save-and-fire-negation`
tiene `consumer=[]` pero su `verification` cita
`modular/contexts.py::prepare_armour_context` y
`mordheim_core/models.py::EffectSet.natural_armour_negated_by_fire`. La
disposición correcta es **pendiente de localización por el propietario**
(G01/G03/G04/G05/G06 según anexo), con la evidencia de
`P00-results/unlocated-localization.csv`; nunca «estructural» y nunca
`verified`.

### 3.4 Estado real de la evidencia en la base (medido, no citado de docs)

| Entrada | Resultado | Duración |
| --- | --- | --- |
| `verify_vectorized_parity()` | 391 obligaciones, 143 verificadas, 248 pendientes, **0 divergencias**, 7 comprobaciones exactas (`hit-targets, wound-targets, attack-pools, priority, keyed-dice-replay, armour, injury`), `complete=False` | 0,4 s |
| `verify_specification_parity()` | 3793 casos: 3733 PASS, 10 `PENDING_ADAPTER` (`round`), 50 `DIVERGENCE`, 0 `OUT_OF_SCOPE`, `complete=False` | 348,7 s |

Interpretación obligatoria para P01–P05:

- Las 248 obligaciones pendientes y los 10 adaptadores pendientes **no son
  cobertura**. `complete=False` en ambas entradas.
- Las 143 «verificadas» de `_vectorized` son estructurales: se marcan por
  presencia textual del campo/etiqueta en el código vectorizado
  (`_vectorized.py:220,228`) o por `shared-construction`, no por ejecución
  comparada. P03 debe mantenerlas separadas (su prompt lo exige explícitamente).
- Las 50 divergencias son un **resultado preexistente del candidato**, no un
  fallo de esta fase ni cobertura aceptada. Desglose por operación:

| Operación | Divergencias | Caso de ejemplo |
| --- | --- | --- |
| `initialize` | 35 | `advanced-dwarf-parries-rangers/two-parry-capacity` |
| `pool` | 5 | `editorial-tentacle-mordheim-and-trollheim/grapple-nominates-the-nominated-attack` |
| `replacement_pool` | 4 | `warpstone-troll-vomit-option/chosen-replacement` |
| `attack` | 3 | `spirit-host-spectral-touch/ordinary-wound-still-resolved` |
| `recovery` | 2 | `core-critical-hits/next-round-restores-critical` |
| `acting_order` | 1 | `weapon.first-strike-family/pike-ordinary-after-first-round` |

Hallazgo que P02 **no puede heredar**: de las 35 divergencias `initialize`, 28
son un artefacto de comparación, no una diferencia de comportamiento.
`_vector_initialize` compara el diccionario completo (`!=`) del oráculo modular
(63 campos en el primer caso) contra la proyección de 21 campos
`_plain_initial_vector_state`; los 42 campos que solo existen en el modular hacen
la desigualdad inevitable. En esas 28 no difiere **ningún campo común**
(`initialize_divergence_probe.py`). Las 7 restantes sí difieren en campos comunes:
6 son el nombre del recurso de discapacidad (`disability.6` vectorizado frente a
`disability.1..5` modular) y 1 son características aleatorias diferidas
(`condemned-inconsistency-random-characteristics/initialization-defers-unused-values`).
P00 no diagnostica la regla: solo demuestra que 28 filas no son evidencia de
divergencia y que el adaptador `initialize` no sirve como base de la batería.

Las otras 15 divergencias sí llevan detalle de campo
(`result.attacks.0.parried: vectorized=False, modular=True`,
`acting order={'first_acts': True}` frente a `False`). Tres de esas operaciones
coinciden con etiquetas que `require_optimized_support` rechaza hoy
(`trait.spectral-touch`, `fighter.vomit_attack`, `mechanic.inconsistency`), es
decir, el candidato no soporta la construcción: P02 debe clasificarlas
`INCOMPATIBLE`, no intentar emularlas.

---

## 4. Inventario de comportamientos y variantes

> **Esta sección sustituye el inventario por familia de la revisión 2.** La
> familia sigue siendo válida para **localizar** consumidores (§3.3), pero no es
> una unidad de comportamiento: una misma familia contiene operadores distintos y
> una misma clave puede actuar en más de una fase. El inventario nuevo se ancla en
> la **clave de ejecución** (`id::clause_id`) y en el **operador decisivo**. Las
> 1914 filas están en `P00-results/behaviour-inventory.csv`; este texto lleva el
> diseño de cada obligación y variante.

### 4.1 Unidad, método y denominador

- **Denominador**: 1914 claves `runtime`+`mixed` de
  `universe-reconciliation.csv`. Las 1256 `shared` se resuelven en compilación
  compartida y las 189 `unlocated` siguen fuera hasta que su propietario localice
  el consumidor (§3.3). Las 98 `shared-operator` se revisan aparte en §4.6 porque
  no son una clase de equivalencia.
- **Operador decisivo**: se toma el **último símbolo específico de ejecución** del
  pipeline `consumer`, omitiendo compilador, inicialización y orquestadores
  (`resolve_round`, `resolve_reference_attack_once`, `apply_round_*`,
  `select_attack_replacement`). Cuando el `effect_id` nombra una regla que el
  pipeline resuelve en un test compartido (`resolve_local_leadership`,
  `resolve_fear`, `resolve_stupidity`), el `effect_id` manda sobre el último
  símbolo; así `mechanic.stupidity` no se convierte en liderazgo.
- **F00 no es una conducta**: es enrutado. Sus 37 claves se reparten al operador
  que consume su cláusula; solo 8 quedan en `B00.1` porque su consumidor es
  únicamente el mapa de enrutado o una comprobación de admisión. No se les asigna
  un duelo.
- **Una clave, varias obligaciones**: la asignación primaria del CSV es el
  operador decisivo. Hay obligaciones secundarias que P01 debe declarar cuando
  autora el caso: `weapon.pike`/`spear`/`quarter-staff` (prioridad **y** recuento
  de ataques), `skill.strongman` (prioridad **y** fuerza), `weapon.beastlash`
  (miedo **y** parada), `skill.regeneration` (save especial **y** recuperación),
  `mechanic.death-blow` (decisión **y** ataque único), `weapon.starsword` (parada
  **y** excepción de dodge). El CSV registra la primaria; el catálogo de §4.4
  nombra la secundaria.
- **Estados de evidencia** usados en las tablas:
  - `operator-base`: el operador base tiene comprobación exacta; **no** acredita
    cada efecto que lo modifica.
  - `case-preparable`: la situación E2E y el observable directo permiten preparar
    un caso; la activación aún necesita testigo.
  - `pending-observable`: falta que un motor publique el observable por fila
    (G06) o que el candidato ejecute la fase (G05).
  - `pending-input`: falta inyección de estado/entrada (G00/G02).
  - `pending-rule`: no hay equivalencia demostrada; hace falta un caso dirigido o
    una fila de rejilla del operador. **No** se presume equivalencia por compartir
    consumidor.
  - `check-defect`: la comprobación existente no ejerce el operador vectorizado.
  - `structural`: solo compilación/enrutado, sin duelo.
  - `consumer-ambiguous`: el consumidor no nombra un operador decisivo.

Recuento del CSV: 1914 filas, 0 huérfanas, **63 variantes**, 0 genéricas. La suma
de variantes es exactamente 1914; cada clave tiene una sola fila primaria. La
numeración `Bxx.y` se conserva cuando el contrato sobrevive; los huecos no son
obligaciones perdidas (§4.4.1).

El `effect_id` y el consumidor solo **localizan** la clave. La pertenencia se
decide leyendo el contrato impreso y su implementación modular; las tablas
explícitas de `inventory_build.py` registran la decisión y fallan si falta, en
lugar de agrupar por substring.

### 4.2 Localización por familia (se conserva; no es el inventario)

La tabla de la revisión 2 se conserva como evidencia de **localización** y de
volumen. No se usa para agrupar obligaciones ni para decidir equivalencias.

| Familia | Claves | Ejecución | Con E2E | Lectura |
| --- | ---: | ---: | ---: | --- |
| F00 enrutado | 37 | 37 | 36 | No es conducta; se reparte al operador. |
| F03 estado y recursos | 51 | 51 | 35 | B01, más recursos y condiciones. |
| F04 contexto y operadores | 1135 | 1037 | 789 | Se reparte en B02–B08 y B10. |
| F05 pool y daño | 72 | 72 | 55 | B08 y B03; el pool ya diverge en la base. |
| F06 equipo y carga | 6 | 6 | 3 | B09. |
| F08 orquestación | 84 | 84 | 58 | B10; `round` sin adaptador. |
| F09 psicología | 269 | 269 | 219 | B11/B12; cero operación semántica. |
| F10 liderazgo | 343 | 343 | 299 | B14; cero operación semántica. |
| F11 secuelas | 15 | 15 | 13 | B15. |
| Sin familia (`shared`/`unlocated`) | 1445 | 0 | 0 | Compilación compartida o localización pendiente. |

### 4.3 Puertas exactas de operador (evidencia existente)

Estas comprobaciones son la evidencia exacta que P02/P03 pueden conservar. Su
alcance es **el operador base**, no todos los efectos que lo modifican.

| Puerta | Comprobación | Qué acredita | Qué **no** acredita |
| --- | --- | --- | --- |
| `hit-targets` | `_vectorized.py:73-87`, rejilla 11×11 | Tabla `to_hit_target`, WS 0 y borde `defender_ws == 2*attacker_ws` | Modificadores de impacto, hatred, rerolls, miedo. |
| `wound-targets` | `_vectorized.py:89-95`, rejilla 11×11 | Tabla `wound_target` | Fuerza efectiva, veneno, daño, rerolls. |
| `attack-pools` | `_vectorized.py:97-117` | Recuento base: ordinario, daga en mano torpe, pistola+espada, `frenzy`; `first_round`×`charging` | Ataques extra, red fury, carga, muerte súbita, recuentos por arma. |
| `priority` | `_vectorized.py:119-138` | Prioridad base, `strongman` con arma a dos manos, ithilmar en mano torpe; `first_round`/charged/stood | Lightning reflexes, pike/spear, strike-first, trident, danza. |
| `armour` | `_vectorized.py:149-187` | Armadura base, ligera, gromril+escudo; penetración, ignore, mágico; S1–10 | Natural armour, buckler, floor, stacks, worst/unmodified. |
| `injury` | `_vectorized.py:189-200` | **Nada del vectorial**: compara `phases.injury_condition` consigo mismo | La proyección `vectorized.injury_conditions` (`_operators.py:95`). Es un **defecto de comprobación**, no una cobertura. |
| `keyed-dice-replay` | `_vectorized.py:140-147` | Mapa de dados por clave | Ninguna regla de combate. |

**Consecuencia inmediata para P03**: antes de citar la tabla de lesión como
exacta, `_exact_operator_checks.injury` debe comparar
`vectorized.injury_conditions(...)` con `phases.injury_condition(...)`. Hoy la
comparación es `phases` contra `phases`; por eso B07.1 lleva `check-defect`.

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

### 4.5 Composición y sensibilidad (para `deep`)

Las interacciones no se generan por combinación: cada una existe porque dos
obligaciones comparten estado y el orden cambia el resultado observable.

1. **B11×B06**: miedo → carga → parada → herida. El testigo `fear-hit-sixes`
   cambia el pool y la parada consume capacidad; el orden se declara en el caso.
2. **B14×B11**: líder a 6" → prueba de miedo/estupidez. El modificador de
   liderazgo se aplica antes o después del retest; el caso declara
   `DuelContext.nearby` y `distances`, no un tercer duelista.
3. **B08×B06**: frenesí/ataque extra → capacidad de parada. El ataque extra no
   debe consumir la capacidad de parada del defensor.
4. **B04×B06**: armadura natural + escudo + buckler. El buckler no mejora la
   armadura, pero sí la parada; son dos obligaciones distintas.
5. **B10×B08**: muerte súbita/frenesí → ataque único vs ataque normal. La decisión
   de muerte súbita cambia el recuento y la bonificación.
6. **B15×B07**: black hunger → herida en el horizonte y espinas/ácido → daño al
   oponente. Son dos disparadores distintos: la recuperación (B15.2) y la
   reacción de daño (B15.4) no comparten testigo ni momento; el caso declara el
   orden y el destinatario.

**Sensibilidad** (misma regla, parámetro en el borde): 6+ vs 5+; S3/S4/S5;
primer asalto vs posterior; cargado vs no cargado; 1 vs 2 heridas; 6" vs 12".
`deep` añade estas escaleras y horizontes más largos, no reglas nuevas.

### 4.6 Revisión de las 98 claves `shared-operator`

La clase `shared-operator` se asignó por **forma del consumidor** (fórmula
compartida en `combat/phases.py`), no por equivalencia de comportamiento. No es
una clase de equivalencia: contiene prioridad, recuento de ataques, armadura
natural, save especial, crítica, equipo y secuelas. Se revisan contra las
comprobaciones exactas existentes (`P00-results/shared-operator-review.tsv`).

| Grupo | Claves | Evidencia exacta existente | Obligación pendiente |
| --- | ---: | --- | --- |
| Armadura natural (stacks, worst, unmodified, negated) | 9 | **Ninguna**: `armour` no incluye natural armour | B04.2, rejilla G03/G04 |
| Prioridad: lightning reflexes, strike-first, pike/spear/quarterstaff, trident, danza, strongman, ithilmar | 31 | **8**: `priority` cubre `strongman` (6) e ithilmar (2), solo la prioridad | B10.1 para las 23 restantes; `strongman` además B03.3 |
| Recuento de ataques: extra attack, red fury, charge, death blow, black hunger, web of steel, armas, unarmed | 43 | **1**: `attack-pools` cubre el ataque extra de dos armas | B08.2/B08.5 para las 42 restantes |
| Buckler | 2 | **Ninguna** | B04.3 (armadura) + B06.2 (parada) |
| Muerte súbita | 2 | **Ninguna** | B10.3 (decisión) + B08.2 |
| Black hunger | 2 | **Ninguna** | B15.1 |
| Crítica | 1 | **Ninguna** | B07.2 |
| Save especial (starsword dodge) | 1 | **Ninguna** | B05.1 |
| Armour floor (fungus) | 1 | **Ninguna** | B04.1 |
| Restricciones de equipo | 3 | **Ninguna** (son compilación) | Reclasificar a `shared`; no es duelo |
| Otras (savage fury, long-boat-hook, poisoned daggers, sword gnoblar, travel staff, stand-up) | 6 | **Ninguna** | B08.2/B06.3/B03.2/B09.3/B10.1/B10.2 según contrato |
| **Total** | **98** | **9** | **89 pendientes** |

**Conclusión**: solo 9 de las 98 claves tienen evidencia exacta, y solo para una
variante (prioridad de `strongman`/ithilmar; ataque extra de dos armas). Las otras
89 **no** se presumen equivalentes por citar `combat/phases.py`; quedan como
obligación diferencial pendiente. Las 3 claves de restricciones de equipo no son
`shared-operator`: se resuelven en compilación compartida y deben reclasificarse.

## 5. Selección de niveles dirigida por variantes

> **Sustituye la composición por recuentos de la revisión 2.** Los tamaños
> 31/125/149 quedan retirados: eran estimaciones, no cuotas ni criterios de
> aceptación. Un nivel es un **conjunto de variantes** (§4.4), no un número de
> casos ni una etiqueta de familia.

### 5.1 Principio

Cada `BatteryCase` declara `variant` (por ejemplo `B14.1`) y `level`. La
pertenencia se decide por la variante, no por el número de casos:

- **quick ⊆ complete ⊆ deep**, por `id` de caso. `battery_cases(level)` devuelve
  la unión de niveles hasta `level`.
- Un caso de `quick` es una **regresión** de una variante base; no acredita todas
  sus variantes ni la ausencia.
- `complete` incluye **todas** las variantes `required=True` y las materiales con
  observable/testigo disponible, incluidas las negativas.
- `deep` incluye `complete` y añade **composición** y **sensibilidad**; no añade
  reglas nuevas que no estén en `complete`.

### 5.2 `quick` — regresión de variantes base

Criterio: la variante tiene un **testigo publicado o preparable** y un resultado
directo observable. Se elige una representativa, no todas.

| Variante | Caso quick | Por qué |
| --- | --- | --- |
| B01.2 | gasto de un recurso (`force-of-will`/`luck`) | Estado inicial y recurso; la reproducción exacta ya los compara. |
| B06.1 | parada de espada | Situación E2E y `parried`; el defensor debe llevar el arma. |
| B07.2 | resultado más alto con dos heridas | `condition` es el resultado directo; el caso debe declarar el estado. |
| B07.3 | lesión por maza/concusión | Borde de tabla y arma; usable como regresión. |
| B10.2 | levantarse y golpear después | `condition`/orden por ronda; el caso debe declarar el derribo. |
| B10.3 | muerte súbita rechazada | Decisión explícita; sin guion es `NOT_RUN`. |
| B11.1 | minotauro causa miedo y el cargado falla | `fear-hit-sixes`; depende de G05/G06. |
| B14.1 | líder a 6" sobre el duelista | `leadership-first-failed`/`leadership-test-value`; requiere `nearby`+`distances`. |
| B15.1 | black hunger | Heridas al horizonte; la regla debe estar en el build. |
| B15.2 | recuperación del revenant | Heridas al inicio de turno; `skill.regeneration` es B05.2 (save), no esta variante. |

Las **puertas exactas** (`hit-targets`, `wound-targets`, `attack-pools`,
`priority`, `armour`, `keyed-dice-replay`) no son casos de `quick`: son
comprobaciones de operador de P03. `injury` no entra hasta corregir el defecto de
§4.3. `quick` puede ejecutarse sin ellas, pero no las sustituye.

### 5.3 `complete` — obligaciones base y variantes materiales

`complete` contiene:

1. Todas las variantes `required=True` de §4.4 (63) con al menos un caso cuando
   la variante es material; una por variante, no una por obligación ni por clave.
2. Todas las variantes **case-preparable** y **operator-base** con su testigo.
3. Las variantes **negativas** de las variantes que tienen una positiva:
   `expect="absent"`, `positive_control` y el predicado `absent` del tipo de
   testigo (contador 0, bandera falsa, categoría distinta, resultado distinto o
   hash igual). La ausencia no se acredita por «no pasó nada».
4. Las variantes **pending-observable/input/rule** se declaran y se ejecutan si el
   motor puede; salen `INCOMPATIBLE:witness`/`INCOMPATIBLE:input`/`INCOMPATIBLE:state`
   o `NOT_ACTIVATED`
   con propietario. **No se omiten** para que `complete` parezca verde.

`accepted=True` exige que el perfil esté completo y que no haya `DIVERGENCE`,
`INCOMPATIBLE`, `NOT_ACTIVATED` ni `NOT_RUN` (§7.9). Una dependencia externa
explícita (G00/G02/G05/G06) puede impedir que `accepted` sea verdadero **al
ejecutar**, pero no impide que P00 entregue la preparación: el caso está escrito,
declarado y asignado. P00 no espera a que el motor implemente la capacidad para
cerrar el inventario.

### 5.4 `deep` — composición y sensibilidad

`deep` = `complete` + las interacciones de §4.5 + las escaleras de §4.5. No se
generan combinaciones exhaustivas. Cada interacción se justifica por estado
compartido y orden observable:

- miedo → parada → herida; líder → miedo/estupidez; frenesí → ataque extra →
  capacidad de parada; armadura natural + escudo + buckler; muerte súbita →
  ataque único; black hunger → herida en el horizonte; espinas/ácido → daño, no
  recuperación.
- Sensibilidad: 6+ vs 5+, S3/S4/S5, primer asalto vs posterior, cargado vs no,
  1 vs 2 heridas, 6" vs 12".

`deep` no reserva una familia ni una variante entera; si una interacción necesita
una variante que no está en `complete`, se añade primero a `complete`.

### 5.5 Reglas de selección y presupuesto

- `battery_cases(level)` filtra por `case.level`; no hay alias con
  `--level deterministic|statistical|deep` ni con `--pair-set`.
- `rows` es el mínimo del caso; P04 puede ampliarlo y el informe guarda el `rows`
  efectivo. Ampliar la muestra no crea un caso nuevo ni cambia el nivel.
- P04 calibra **coste y muestra**, no cobertura. Si el presupuesto no alcanza para
  todo `complete`, el informe declara qué obligaciones quedaron fuera; no se
  rebaja `complete` a “lo que se pudo ejecutar”.
- Un caso nuevo entra por variante, no por familia. Si no se puede asignar a una
  variante de §4.4, el inventario está incompleto: se abre una variante nueva con
  los siete campos, no se mete en un cajón «otros».

### 5.6 Lo que no es un nivel

- **F00 enrutado** no es un caso de combate: es `structural` y se comprueba en
  `verification/consumers.py`, no en la batería.
- **Compilación compartida** (1256 `shared`) no es un duelo: se acredita con el
  compilador y los tests de construcción.
- **`unlocated`** (189) no es estructural ni está cubierto: queda `UNLOCATED`
  hasta que su propietario localice el consumidor.
- **`shared-operator`** no es una clase de equivalencia (§4.6): cada grupo se
  vincula a una comprobación exacta o queda pendiente.

## 6. Dificultad de adaptación

| Dificultad | ¿Soportado hoy? | Decisión de P00 |
| --- | --- | --- |
| Construcción (`FighterBuild` → `CompiledFighter`) | Sí | `compile_fighter(build, root)` es el compilador compartido; P02 compila **una vez por caso** y entrega el mismo `CompiledFighter` a ambos motores. `replay_duel`/`simulate_*` nunca reciben un `FighterBuild` |
| Muestra por lotes en el candidato | Sí | `vectorized.simulate_batch_observed(first, second, count, rng, maximum_rounds, decisions, context)` devuelve arrays por fila (`VectorBatchObservation`) |
| Muestra por fila en el oráculo | Sí | `modular.duel.simulate_duel_observed(first, second, simulations, seed=..., maximum_rounds=..., decisions=..., context=...)` devuelve arrays por duelo (`ObservedDuelResult`) |
| Guiones de tiradas por motor | **Eliminado del contrato** | Los casos nuevos no llevan guion: usan una semilla declarada y los dos caminos de muestreo anteriores. La reproducción exacta con `StrictDice` queda solo en las pruebas ya escritas (`test_duel_replay.py`), que P03 cita como evidencia aparte y P01 no reescribe |
| Orden de tiradas | Solo en reproducciones existentes | La batería **no** compara tirada a tirada ni exige que el orden coincida: compara distribuciones por observable (§7.7). La correspondencia de orden solo se acredita en `test_duel_replay.py`, que ya está escrito |
| Decisiones | Parcial | `decisions: Mapping[str, bool]` se traduce a `ScriptedDecisions`, idéntico para ambos motores. El candidato ya pasa contexto por fila en algunas claves (`_attacks.py:889`), pero `ScriptedDecisions` responde solo por clave. Un caso que declare `decision_scope="per-row"` es `INCOMPATIBLE:decision-scope` (adaptador P02/G02), no se emula; un `KeyError` es `NOT_RUN:decision-script` (P01) |
| Contexto de duelo | Sí | parámetro `context: DuelContext` en ambos caminos. `nearby` (con `LocalParticipant`) y `distances` representan aliados, líder, handler o relay sin un tercer duelista |
| Consumo del contexto por el candidato | **No** | el oráculo (`leadership.py`) lee `nearby` y `context.distance`; el `_driver.py` del candidato no llama a los resolutores de psicología/lideranía. Representación sí, consumo no: `INCOMPATIBLE:consumer:<variant>` (G05) |
| Horizonte/checkpoint | Sí | `maximum_rounds` en ambos caminos trunca el duelo: las filas que terminan antes aportan su terminal, las no resueltas aportan el estado en el horizonte. Un checkpoint es un caso con horizonte, no un segundo mecanismo de observación |
| Estado inicial inyectado (`initial_state` E2E) | **No** | ningún camino público acepta estado; 1534 casos E2E lo usan. Petición a G00/G02 (§9.4); hasta entonces `INCOMPATIBLE:state`, nunca ejecutar desde cero y llamarlo equivalente |
| Testigo de activación | **Parcial** | Solo los 4 terminales se publican hoy por fila y ninguno es testigo de una regla concreta. El testigo es tipado y se declara por variante (§7.2/§7.6); un observable no publicado produce `INCOMPATIBLE:witness` o una comparación enfocada declarada, nunca `PASS` por actividad |
| Observables de psicología/liderazgo | **No** | el oráculo no los publica por fila y la integración del candidato no está verificada en `_driver.py`. Se declaran y salen `INCOMPATIBLE:witness` con propietario G05/G06, no se omiten |
| Recursos (los 4 del candidato y el resto) | Parcial | `VectorBatchObservation` publica 4; el oráculo por lotes no publica ninguno. En lote: `INCOMPATIBLE:witness`; la comparación exacta de recursos solo existe en las reproducciones ya escritas |
| Doble consumo de un recurso | **No** | el estado por fila solo dice «gastado»; probar «no vuelve a usarse» exige observación por evento (G06). No se acredita con la tasa de victorias ni con el contraste de testigo |
| Rechazo de construcción | Sí | `require_optimized_support` lanza `ValueError`; se clasifica `INCOMPATIBLE:construction`, nunca se emula |
| Comparación de distribuciones | Sí, con puerta existente | misma fórmula seis sigma de `_statistical.py:19-24`, aplicada por categoría; el criterio de testigo y su límite están en §7.7–§7.8 |

---

## 7. Contrato P01 ↔ P02 (revisión 4)

> **Corrige la revisión 3.** Se mantienen la compilación única, el muestreo por
> `simulate_duel_observed`/`simulate_batch_observed`, la puerta seis sigma, los
> estados `PASS|DIVERGENCE|INCOMPATIBLE|NOT_ACTIVATED|NOT_RUN`, la ausencia de
> guiones por motor, de reintentos y de cuotas. Cambian cuatro cosas:
>
> 1. el testigo es **tipado** (contador, bandera, categoría, resultado directo o
>    hash) y cada variante declara su **predicado**; `> 0` no vale para una
>    categoría ni para un hash;
> 2. el contexto local se expresa con `DuelContext.nearby`/`distances` y
>    `LocalParticipant`, no con un campo `support`;
> 3. la cobertura se cuenta por **variante** (63), no por obligación ni por clave;
> 4. `behaviour-inventory.csv` se **transfiere** al catálogo de P01; no queda como
>    dependencia de ejecución ni como segundo registro que haya que sincronizar.

No se añade framework, lenguaje de escenarios, jerarquía de plugins ni dependencia
nueva. Se reutilizan `FighterBuild`, `CompiledFighter`, `DuelContext`,
`LocalParticipant` (`mordheim_core.models`), `compile_fighter`,
`ScriptedDecisions`, `simulate_duel_observed` y `simulate_batch_observed` sin
modificarlos.

### 7.1 Archivos y símbolos

| Módulo | Propietario | Símbolos públicos |
| --- | --- | --- |
| `verification/parity/_battery_cases.py` | P01 | `PROFILE_LEVELS`, `OUTCOMES`, `Witness`, `WITNESSES`, `OBSERVABLES`, `Variant`, `Obligation`, `OBLIGATIONS`, `battery_cases(level="complete")`, `validate_cases`, `validate_keys`, `validate_origins` |
| `verification/parity/_battery_runner.py` | P02 | `RESOURCES_OBSERVED`, `BatteryCaseResult`, `BatteryReport`, `run_battery(cases, *, profile=None, backend="numpy", rows=None, root=None)` |

`RESOURCES_OBSERVED` sigue siendo lo que el candidato publica hoy
(`lucky-charm`, `force-of-will`, `mark-of-the-old-ones`, `luck`); no es el
vocabulario completo. Lo no publicado se declara y sale `INCOMPATIBLE`, nunca se
reduce el caso.

### 7.2 Modelo de obligación, variante y testigo (P01)

`OBLIGATIONS` agrupa por bloque `Bxx`; la unidad ejecutable y contable es la
**variante** `Bxx.y` de §4.4. Una obligación con dos contratos distintos tiene dos
variantes con testigos distintos; una etiqueta o un consumidor compartido no las
funde.

```python
from dataclasses import dataclass
from typing import Literal, Mapping

WitnessKind = Literal["counter", "flag", "category", "direct-result", "hash"]
Predicate = Literal[
    "count>0", "count==0", "flag-true", "flag-false",
    "class-equals", "class-differs",
    "value-equals", "value-differs",
    "hash-changes", "hash-same",
]

@dataclass(frozen=True, slots=True)
class Witness:
    name: str
    kind: WitnessKind
    present: Predicate
    absent: Predicate

@dataclass(frozen=True, slots=True)
class Variant:
    id: str                          # "B14.1"
    title: str
    witness: Witness | None          # None = aún sin testigo admisible
    case_kind: Literal["duel", "structural", "unlocated"] = "duel"
    required: bool = True            # cuenta en el denominador de `complete`
    level: Literal["quick", "complete", "deep"] = "complete"
    owner: str = "G06"               # quién publica o implementa lo que falta
    evidence: str = ""               # comprobación exacta o hueco declarado
    secondary: tuple[str, ...] = ()  # variantes que la misma cláusula también toca

@dataclass(frozen=True, slots=True)
class Obligation:
    id: str                          # "B14"
    family: str                      # "F10-leadership"
    variants: tuple[Variant, ...]

OBLIGATIONS: Mapping[str, Obligation] = {...}
```

Reglas:

- `witness.name` pertenece a `WITNESSES` o es `None`; una cadena libre no es
  válida. El tipo y los predicados salen de la tabla de §7.6; P01 no los inventa
  por caso.
- `witness.kind="direct-result"` solo se admite en `B07.*` (la condición es el
  resultado directo de la tabla de lesión) y `B15.*` (la herida o la condición es
  el resultado directo de la recuperación o de la reacción). `condition` y
  `wounds` **no** son testigos de impacto, parada, armadura, save, recurso ni
  psicología.
- `required=True` es la variante material de §4.4 y cuenta en el denominador de
  `complete`. `required=False` documenta una variante dependiente de una entrada
  que aún no existe; no se omite del catálogo.
- `owner` es el propietario de la representación, del consumo o de la publicación
  que falta (`G00`, `G02`, `G03`, `G05`, `G06`, `P01`). No se usa para rebajar un
  estado.
- `secondary` no acredita nada por sí solo: exige que el caso declare el testigo
  de la variante secundaria en `also_covers` (§7.4).
- **Pertenencia**: `VARIANT_KEYS: Mapping[str, tuple[str, ...]]` se genera una
  sola vez importando `behaviour-inventory.csv` y se versiona con P01. A partir de
  ahí P01 es el propietario de la pertenencia; no hay lectura en tiempo de
  ejecución de `P00-results/` ni una segunda lista manual que mantener. P00
  conserva el CSV como foto de diseño y la reconciliación de §3.
- **Huecos**: una variante `required=True` con `witness=None` se declara igual y
  sus casos salen `INCOMPATIBLE:witness`; no se convierte en «cubierta por
  `winner`».

### 7.3 Modelo de caso (P01)

```python
from dataclasses import dataclass, field
from typing import Literal, Mapping
from mordheim_core.models import DuelContext, FighterBuild

PROFILE_LEVELS = ("quick", "complete", "deep")

@dataclass(frozen=True, slots=True)
class BatteryCase:
    id: str                                  # único y estable
    level: Literal["quick", "complete", "deep"]
    variant: str                             # "B14.1"; debe existir en OBLIGATIONS
    origin: str                              # "e2e:<audit_id>::<scenario>" | "spec:<fixture>#<case>"
    first: FighterBuild
    second: FighterBuild
    rows: int = 64
    seed: int = 2026
    maximum_rounds: int = 50
    context: DuelContext | None = None       # nearby/distances/contacts/charging
    decisions: Mapping[str, bool] = field(default_factory=dict)
    decision_scope: Literal["uniform", "per-row"] = "uniform"
    observables: tuple[str, ...] = ("winner", "rounds", "wounds", "condition")
    expect: Literal["present", "absent"] = "present"
    positive_control: str | None = None      # id de caso; obligatorio si expect="absent"
    witness_value: int | str | None = None   # categoría/resultado/hash esperado
    also_covers: tuple[str, ...] = ()        # variantes secundarias ejercidas
    comparison: Literal["witness", "focused"] = "witness"
    focused: str | None = None               # "winner:2" | "condition:out"; solo focused
    requires: tuple[str, ...] = ()           # ids de regla materializados en el build
    note: str = ""
```

Invariantes que P01 garantiza con `validate_cases`:

- `level in PROFILE_LEVELS`; `id` único; `variant` existe en `OBLIGATIONS`.
- `observables ⊆ OBSERVABLES`, contiene `"winner"` y contiene el nombre del
  testigo de la variante cuando no es `None`. Si el testigo es un resultado
  directo (`condition`/`wounds`), el nombre ya está en `OUTCOMES` y se admite sin
  duplicarlo en `WITNESSES`.
- `rows >= 1`, `seed >= 0`, `maximum_rounds >= 1`.
- `witness_value` es obligatorio si el testigo es `category`, `direct-result` o
  `hash`; prohibido si es `counter` o `flag`.
- `expect="absent"` exige `positive_control` no nulo, existente, de la **misma
  variante**, con `expect="present"` y declarado antes (sin ciclos). El caso
  negativo no exige activación positiva; exige el predicado `absent` del testigo
  y un control que cumpla `present`.
- `expect="present"` no admite `positive_control`.
- `comparison="focused"` exige `focused` con la forma `<outcome>:<valor>` y
  `positive_control`; `witness` debe ser `None` o no publicado (§7.6). Un caso
  `focused` no cuenta como testigo de una variante que sí tiene testigo.
- `also_covers` solo contiene variantes existentes y distintas; el nombre del
  testigo de cada una debe estar en `observables` y ser evaluable por P02. Una
  variante secundaria ya cubierta por otro caso no se duplica.
- `requires` se comprueba contra los campos reales de `FighterBuild`:
  `main_weapon_id`, **`off_hand_id`**, `armour_id`, `defence_ids`, `skill_ids`,
  `preparation_ids`, `special_rule_ids`, `condition_ids`, `main_material_id`,
  `off_material_id`, `variant_ids`, `trait_overrides` y `owned_item_ids`. Un id
  declarado que no aparece es un caso inválido, no un caso que «probablemente»
  active.
- Toda clave de `VARIANT_KEYS[variant]` existe y está admitida en el registro; se
  valida con `tools/knowledge/clause_registry.py`, sin escribir el CSV.
- **Anidamiento** por `id`: `quick ⊆ complete ⊆ deep`.
- **Origen**: `origin` resuelve a un `audit_id`/escenario E2E o a un fixture/caso
  semántico existente. P01 lo comprueba leyendo el corpus, sin importar helpers
  de `tests/` desde el módulo de producción.

P01 construye los `FighterBuild` como el corpus E2E
(`tests/E2E/modular-engine/runner.py:49-58`): `characteristics` →
`Characteristics`, tuplas para las listas de ids. No importa código de pruebas.
Un escenario E2E con `initial_state` no se convierte hoy: se declara
`INCOMPATIBLE:state` (G00/G02) y no se ejecuta desde cero como si fuera
equivalente.

### 7.4 Selección y cobertura por variante

Un nivel es un conjunto de **variantes**, no un número de casos:

- **quick**: variantes con `level="quick"`; una representativa por variante, con
  testigo admisible o comparación enfocada. Es regresión, no certificado.
- **complete**: todas las variantes `required=True` con `case_kind="duel"` (60)
  con al menos un caso, incluidas las negativas pareadas de toda variante con
  disparador/ausencia materializable. Las tres estructurales/ambiguas (B00.1,
  B09.1, B99.1) se acreditan con su comprobación propia. No incluye composición.
- **deep**: `complete` + composición/sensibilidad `D01`–`D06` de §4.5. No reserva
  ninguna variante de comportamiento: si una interacción necesita una variante
  que no está en `complete`, se añade primero a `complete`.

`battery_cases(level)` devuelve los casos con nivel igual o anterior en
`PROFILE_LEVELS`. No hay alias con `--level deterministic|statistical|deep` ni con
`--pair-set`; P03 debe rechazar la mezcla.

Cobertura:

- Se calcula sobre `OBLIGATIONS[*].variants`, no sobre claves ni sobre número de
  casos. `MISSING:<variant-id>` por cada variante requerida con `case_kind="duel"`
  sin caso que la cubra; `missing_variants` vacío es condición de
  `accepted=True`.
- Una variante queda cubierta por un caso con `variant=id`, **o** por un caso que
  la declare en `also_covers` y cuyo testigo también se evalúe y pase. Un caso
  genérico de la obligación no cubre las demás variantes.
- Las claves se adjuntan a variantes (`VARIANT_KEYS`), no a casos sueltos: varias
  claves comparten variante y no se exige un duelo por clave.
- Variantes estructurales o sin duelo: `B00.1` (enrutado), `B09.1`
  (compilación) y `B99.1` (consumidor ambiguo) llevan `case_kind="structural"` o
  `"unlocated"`; se acreditan con su comprobación propia y salen `STRUCTURAL` o
  `UNLOCATED`, nunca `PASS` de batería ni cuentan como `MISSING` de duelo.
- Las 98 `shared-operator` se informan por el grupo de §4.6: 9 con evidencia
  exacta (y solo de una variante) y 89 pendientes. No se convierten en variantes
  de duelo ni se acreditan con un caso genérico.

### 7.5 Ejecución (P02)

```python
def run_battery(cases, *, profile=None, backend="numpy", rows=None, root=None) -> BatteryReport:
    ...
```

Por caso:

```python
first, second = compile_fighter(case.first, root), compile_fighter(case.second, root)
n = case.rows if rows is None else rows
decisions = ScriptedDecisions(case.decisions)

oracle = simulate_duel_observed(
    first, second, n, seed=case.seed, maximum_rounds=case.maximum_rounds,
    decisions=decisions, context=case.context)
candidate = _candidate_sample(
    backend, first, second, n, case.seed, case.maximum_rounds, decisions,
    context=case.context)
```

- **Compilación una vez** por caso y participante; el mismo `CompiledFighter`
  alimenta ambos motores. La compilación se mide aparte y no suma a
  `modular_seconds`.
- `root` es `knowledge_root()` cuando es `None`; P04 puede fijarlo.
- `backend="native"` usa `_combat_native.simulate_batch_observed` solo si
  `CONTEXT_VERSION == 1` y el símbolo existe; si no, `NOT_RUN:native-stale`.
- **Contexto local**: los aliados, el líder, el handler o el relay viajan en
  `case.context` (`DuelContext.nearby` + `distances`) y se compilan con la misma
  conversión que los duelistas. No hay `support` ni un tercer `CompiledFighter`
  aparte. Las variantes que solo necesitan el valor propio no exigen `nearby`.
- **Tres capas separadas** para B11/B14: representación (`DuelContext` existe y el
  corpus E2E ya la usa), consumo (`leadership.py` lee `nearby`/`distance`; el
  candidato no llama a esos resolutores en `_driver.py`) y publicación
  (`ObservedDuelResult`/`VectorBatchObservation` no exportan el valor ni el flag
  por fila). La falta de consumo es `INCOMPATIBLE:consumer:<variant>` `owner=G05`;
  la de publicación es `INCOMPATIBLE:witness:<name>` `owner=G06`. No se confunden
  con una ausencia del modelo de entrada.
- **Decisiones**: `ScriptedDecisions` responde por clave, uniformemente. Si el
  caso declara `decision_scope="per-row"`, P02 devuelve
  `INCOMPATIBLE:decision-scope owner=P02/G02` antes de compilar. Un `KeyError`
  durante la ejecución es `NOT_RUN:decision-script:<clave> owner=P01`.
- Ningún caso ejecuta `replay_duel` ni transporta guiones de tiradas. Las
  reproducciones exactas existentes quedan en `test_duel_replay.py` como evidencia
  separada; P03 las cita sin fusionarlas con `PASS`.
- Un fallo de compilación es `NOT_RUN:compile:<tipo>: <mensaje>` (caso/base
  inválido, P01). Un rechazo de `require_optimized_support` es
  `INCOMPATIBLE:construction`.

### 7.6 Observables, testigos tipados y conversión del contexto

`OBSERVABLES = OUTCOMES + WITNESSES`. Un **resultado** describe cómo terminó el
duelo; un **testigo** cuenta o clasifica el evento concreto que debía activarse.

```python
OUTCOMES = ("winner", "rounds", "wounds", "condition")

WITNESSES = (
    # recursos (nombre exacto del recurso gastado)
    "lucky-charm", "force-of-will", "mark-of-the-old-ones", "luck",
    # banderas de estado
    "frenzy", "devoted-frenzy", "on-fire", "entangled", "force-of-will-active",
    "broken-hands", "hampered", "disability", "netted", "grappled", "entranced",
    # psicología y liderazgo
    "fear-hit-sixes", "fear-test-skipped", "psychology-test-skipped",
    "psychology-dice", "stupidity-failed", "animosity-failed",
    "feral-instinct-failed", "leadership-first-failed", "leadership-auto-pass",
    "leadership-test-value", "poetry-first-leadership",
    # eventos de combate
    "hit-modified", "wound-modified", "strength-modified",
    "armour-save-rolled", "special-save-rolled", "parried",
    "attack-count", "acting-order", "reroll-used", "equipment",
)
```

Tabla de tipos y predicados (contrato, no sugerencia):

| Testigo | Tipo | `present` | `absent` | `witness_value` |
| --- | --- | --- | --- | --- |
| recursos (`lucky-charm`…), `hit-modified`, `wound-modified`, `strength-modified`, `armour-save-rolled`, `special-save-rolled`, `parried`, `attack-count`, `reroll-used`, `fear-hit-sixes` | `counter` | `count>0` | `count==0` | — |
| `frenzy`, `devoted-frenzy`, `on-fire`, `entangled`, `force-of-will-active`, `broken-hands`, `hampered`, `disability`, `netted`, `grappled`, `entranced`, `fear-test-skipped`, `psychology-test-skipped`, `stupidity-failed`, `animosity-failed`, `feral-instinct-failed`, `leadership-first-failed`, `leadership-auto-pass` | `flag` | `flag-true` | `flag-false` | — |
| `acting-order` | `category` | `class-equals` | `class-differs` | `0` o `1` |
| `leadership-test-value`, `psychology-dice` | `direct-result` (valor medido) | `value-equals` | `value-differs` | valor declarado |
| `condition`, `wounds` (solo B07/B15) | `direct-result` | `value-equals` | `value-differs` | código/valor declarado |
| `equipment` | `hash` | `hash-changes` | `hash-same` | hash base |
| `poetry-first-leadership` | `flag` | `flag-true` | `flag-false` | — |

Consecuencias:

- `acting-order` **nunca** se evalúa con `> 0` ni con «cero eventos»: es una
  categoría 0/1 y el caso declara cuál satisface `present` en `witness_value`.
- `equipment` **nunca** se evalúa por conteo: es un hash; `present` significa
  distinto del hash base declarado (o del control negativo), `absent` igual.
- `condition`/`wounds` solo son testigo con `kind="direct-result"` en `B07.*` y
  `B15.*`. Para impacto, parada, armadura, save, recurso o psicología no se
  deducen de una herida o condición terminal.
- Un testigo no publicado por ambos lados es `INCOMPATIBLE:witness:<nombre>` con
  `owner`. No se reduce a `winner`, no se descarta el observable y no se declara
  `PASS`.
- `RESOURCES_OBSERVED` documenta lo que el candidato ya publica; no autoriza a
  compararlo contra un oráculo que no lo devuelve.
- Las claves de una regla no se «cubren» por estar en `VARIANT_KEYS`: la cobertura
  exige testigo (o comparación enfocada) y comparación.

#### 7.6.1 Conversión E2E → `DuelContext`

El corpus ya expresa el contexto local con los campos de `DuelContext`; P01
reutiliza la conversión de `tests/E2E/modular-engine/runner.py:100-112`:

```yaml
duel_context:
  first_id: first
  second_id: second
  nearby:
    - participant_id: leader
      side_id: second
      condition: standing
      fighter: {collection: mordheim, band_id: amazons-lustria, profile_id: serpent-priestess}
  distances: [[second, leader, 6]]
  charging: [first]
  active_participant: first
```

- `nearby` se compila con la misma función `_fighter` que los duelistas y se
  envuelve en `LocalParticipant(participant_id, side_id, fighter, condition)`.
- `distances` son pulgadas de borde a borde entre ids de participantes;
  `DuelContext` rechaza duplicados, ids desconocidos y distancias negativas.
- **Control sin líder**: se omite la entrada de `nearby` (o se deja vacía). No se
  usa `support=None` porque no hay tal campo; la variante B14.4 (liderazgo propio)
  puede incluir un líder en `nearby` y comprobar que no se adopta su valor.
- **Control fuera de radio**: el mismo proveedor con `distances` 8" para un radio
  de 6", o 13" para 12"; el corpus ya tiene ese caso
  (`...barbarian--dim-witted...::outside-the-printed-six-inches...`).
- La distancia se declara siempre que el contrato la lea; no se inventa un
  `support_distance` que el motor no consume.
- `mob-leadership` no usa `nearby`: el recuento de aliados a 3" viaja en
  `CompiledFighter.mob_allies`, suministrado por el llamador.

### 7.7 Comparación, activación y NOT_ACTIVATED

Cada observable declarado se compara por categorías sobre la muestra:

- `winner` aporta 3 categorías (0, 1, 2); `condition` 5 por participante;
  `wounds` y `rounds` una por valor entero observado en cualquiera de los dos
  motores (unión de valores, sin recortar). Los testigos de tipo contador usan la
  unión de conteos; los categóricos y los hashes, sus valores.
- Para cada categoría `c`: `p = oracle_count[c] / n`, `q = candidate_count[c] / n`.
- **Puerta existente** (`_statistical.py:19-24`):
  `|p - q| <= max(0.0025, 6·sqrt(p(1-p)/n + q(1-q)/n))`. P02 copia la expresión
  literal citando esa línea; P03 la unifica. No se inventa ni se relaja.
- `PASS` exige que todas las categorías de todos los observables declarados pasen
  y que se cumpla el criterio de testigo (o el enfocado).

Evaluación del testigo (por variante):

- `counter`: `present` = alguna fila con `count>0`; `absent` = todas con `count==0`.
- `flag`: `present` = alguna fila con la bandera; `absent` = ninguna.
- `category`: `present` = alguna fila con `value == witness_value`; `absent` =
  ninguna fila con ese valor. `acting-order` se evalúa así, no por magnitud.
- `direct-result`: `present` = el valor medido coincide con `witness_value`;
  `absent` = no coincide (p. ej. la condición no es la declarada).
- `hash`: `present` = el hash difiere de `witness_value`; `absent` = coincide.
  `equipment` no se interpreta como cero/no cero.

Estados:

- `expect="present"` y el oráculo no muestra el predicado `present`:
  `NOT_ACTIVATED:<witness>`. No se atribuye a divergencia entre motores: no hay
  activación observada.
- `expect="absent"` sin control: `NOT_ACTIVATED:no-positive-control`. Con control
  declarado pero sin activación en el control:
  `NOT_ACTIVATED:positive-control:<id>`; **no** `DIVERGENCE`.
- Contraste: el par positivo/negativo debe diferir en el oráculo (positivo cumple
  `present`, negativo cumple `absent`). Si ambos cumplen `present`, el criterio no
  discrimina: `NOT_RUN:criterion-insensitive:<variant>` `owner=P01` (defecto de
  caso), no una divergencia de motores.
- Ambos motores ejecutaron y sus distribuciones difieren: `DIVERGENCE:distribution`.
  Es el único camino que atribuye una diferencia entre motores.

**Comparación enfocada** (`comparison="focused"`): cuando el testigo no está
publicado, un par de casos puede declarar un único resultado discriminante
(`focused`, p. ej. `condition:out` o `winner:2`) y su dirección esperada. El
criterio es: el oráculo difiere entre positivo y negativo en ese resultado y el
candidato reproduce la misma diferencia. Se informa `coupling="focused"` y no
acredita activación por evento. Se admite para no exigir instrumentación nueva
automáticamente; no sustituye a un testigo ya declarado ni convierte una
diferencia de distribución en activación.

**Límite**: ni el testigo ni el contraste demuestran independencia fila a fila ni
localizan la causa de una diferencia. La independencia exige observación por
evento (G06) y se informa `coupling="unverified"`. La evidencia exacta sigue
siendo `_specifications.py` y `test_duel_replay.py`; la batería aporta amplitud y
sensibilidad, no exactitud por sí sola.

**Sin reintentos**: no se cambia la semilla ni se amplía `rows` tras un fallo. La
sensibilidad se mide antes de fijar presupuestos, con la escalera
`(case.rows, 4·case.rows)`.

### 7.8 Comprobación de lote

Por cada caso con `rows > 1`:

1. **Determinismo**: dos ejecuciones con el mismo caso, semilla y ancho producen
   arrays idénticos (`repeat_is_deterministic=True`, `contract_probe.py`). Un
   fallo es `DIVERGENCE:batch-nondeterministic`.
2. **Forma**: cada array mide `rows` (`shape_mismatch=none`). Si no,
   `DIVERGENCE:batch-shape`.
3. **Contraste**: el de §7.7, evaluado entre el caso y su `positive_control`, con
   el predicado tipado de la variante o el resultado enfocado. Es la única
   comprobación de lote que atribuye una diferencia al disparador.
4. **Alcance de decisión**: `decision_scope="per-row"` se rechaza antes de
   ejecutar; un `KeyError` es `NOT_RUN:decision-script`, no una decisión tomada
   por defecto.

**Multiplicidad retirada** (revisión 2 §7.7.3): no se exige que una categoría con
`0 < count < rows` en el oráculo aparezca también en el candidato. Los motores no
comparten tiradas fila a fila y una categoría rara puede faltar en una muestra
independiente aunque las distribuciones coincidan. Reproducción del defecto:
oráculo con 63 ceros y un uno, candidato con 64 ceros; la puerta seis sigma
acepta (`p=1/64`, `q=0`, `tol≈0.093 > 0.0156`) y la regla declaraba
`batch-mask`. Por eso los cuatro `DIVERGENCE` históricos por `batch-mask` no se
cuentan como defectos de reglas del motor: esa evidencia no localiza ni acredita
tales defectos.

**Lo que el contrato no afirma** (medido): la fila 0 de un lote no coincide con una
ejecución individual de la misma semilla. Con `seed=11`, `rows=16` frente a
`rows=1` difieren `rounds` (3 vs 2), `first_wounds` (-1 vs 0) y `second_wounds`
(0 vs 1); ver `contract-probe.txt`. Por tanto no se exige correspondencia fila a
fila con el oráculo, repetir una sola fila no es evidencia de lote y detectar qué
fila gastó qué recurso exige observación por evento (G06). `first_wounds` puede
ser negativo; se trata como una categoría más, sin recortar.

### 7.9 Resultado, estados y alcance

```python
@dataclass(frozen=True, slots=True)
class BatteryCaseResult:
    case: str
    level: str
    variant: str
    obligation: str
    backend: str                  # "numpy" | "native"
    status: str                   # PASS | DIVERGENCE | INCOMPATIBLE | NOT_ACTIVATED | NOT_RUN
    keys: tuple[str, ...]         # derivadas de VARIANT_KEYS
    observables: tuple[str, ...]
    rows: int
    witness: str | None = None
    witness_kind: str | None = None
    witness_rate: float | None = None
    expect: str = "present"
    expect_value: int | str | None = None
    comparison: str = "witness"   # "witness" | "focused"
    coupling: str = "unverified"  # "contrast" | "focused" | "unverified"
    detail: str = ""
    modular_seconds: float = 0.0
    candidate_seconds: float = 0.0

@dataclass(frozen=True, slots=True)
class BatteryReport:
    complete: bool
    accepted: bool                # complete, scope == "profile" and variants covered
    scope: str                    # "profile" | "provided"
    profile: str | None
    results: tuple[BatteryCaseResult, ...]
    passed: tuple[str, ...]
    divergences: tuple[str, ...]
    incompatible: tuple[str, ...]
    not_activated: tuple[str, ...]
    not_run: tuple[str, ...]
    missing_variants: tuple[str, ...]
```

| Estado | Significado | ¿Aceptable? |
| --- | --- | --- |
| `PASS` | Ambos ejecutaron, el testigo o el contraste enfocado cumple y todas las categorías pasan | Sí |
| `DIVERGENCE` | Ambos ejecutaron y sus distribuciones difieren; o falla determinismo/forma | No |
| `INCOMPATIBLE` | Construcción rechazada, observable/testigo no publicado, consumo ausente, decisión per-row o backend sin capacidad | No |
| `NOT_ACTIVATED` | El testigo esperado no apareció en el oráculo, o el control positivo de una ausencia no activó | No |
| `NOT_RUN` | No se ejecutó: backend ausente/obsoleto, compilación inválida, guion de decisión ausente, caso o criterio mal definido | No |

`accepted=True` exige `scope="profile"`, `missing_variants` vacío y ausencia de
`DIVERGENCE`, `INCOMPATIBLE`, `NOT_ACTIVATED` y `NOT_RUN`. `scope="provided"`
puede ser `complete=True` en el sentido interno del subconjunto, pero nunca
`accepted=True`: es diagnóstico, no acreditación del perfil. P03 traduce
`--require-complete` sobre `accepted`.

Clasificación de excepciones, sin silenciar ninguna:

- `ValueError` de `require_optimized_support` o del runtime uno-contra-uno →
  `INCOMPATIBLE:construction`.
- `KeyError` de `ScriptedDecisions` → `NOT_RUN:decision-script:<clave> owner=P01`.
- `AttributeError`/`TypeError` al leer un observable o testigo no publicado →
  `INCOMPATIBLE:witness:<nombre>` (G02/G03/G05/G06), nunca `PASS`.
- Consumo de `nearby` no implementado en el candidato →
  `INCOMPATIBLE:consumer:<variant> owner=G05`.
- `decision_scope="per-row"` → `INCOMPATIBLE:decision-scope owner=P02/G02`.
- Testigo no registrado o caso sin variante → `NOT_RUN:case-definition:<detalle>
  owner=P01`.
- Cualquier otra excepción → `DIVERGENCE:exception:<tipo>: <mensaje>`.

### 7.10 Evaluación solo-lectura de P01 y P02

P00 no ha modificado `_battery_cases.py` ni `_battery_runner.py`. Esta evaluación
fija qué conservar y qué corregir; la corrección es de P01/P02.

#### P01 — `_battery_cases.py`

**Conservar**:

- Módulo de datos sin importar el runner; separación catálogo/ejecución.
- `PROFILE_LEVELS`, `OBSERVABLES`, `BatteryCase`, `battery_cases`,
  `validate_cases`, `validate_keys`.
- Selección acumulativa por `id` y comprobación de claves admitidas contra el
  registro.
- `_fighter` como conversión explícita a `FighterBuild` (sin importar helpers de
  `tests/`).
- `OUTCOME_OBSERVABLES` como semilla de la separación resultado/testigo.

**Corregir**:

| # | Hallazgo | Corrección exigida |
| --- | --- | --- |
| 1 | `BatteryCase` no tiene `variant`, `expect`, `positive_control`, `witness_value`, `also_covers`, `decision_scope`, `comparison`, `requires` | Añadirlos con los invariantes de §7.3. `activation` se retira. |
| 2 | `_fighter` solo acepta `weapon`, `armour`, `collection`, `band`, `profile` y características | Exponer `skill_ids`, `preparation_ids`, `special_rule_ids`, `condition_ids`, `defence_ids`, materiales y `trait_overrides`, ya soportados por `FighterBuild`. |
| 3 | `q04-natural-armour-six` usa armadura ligera en un combatiente genérico; no lleva `band--beastmen-special-skills-shaggy-hide` | Materializar piel natural con el perfil/regla del origen y declarar `requires`; si falta entrada, `INCOMPATIBLE:input`, no sustituir por armadura. |
| 4 | `q05-flammable-fire` usa maza contra espada; faltan `weapon.brazier-iron` y `flammable` | Materializar fuego e inflamabilidad; el testigo es `on-fire`/`wound-modified`, no la herida terminal. |
| 5 | `q11-black-hunger` no lleva `skill_ids=("mechanic.black-hunger",)` | Añadir la regla al build; `requires=("mechanic.black-hunger",)`. |
| 6 | `q00-honorable` no lleva `mechanic.honorable` ni el rival derribado | Materializar regla y estado inicial; si el estado no se puede inyectar, `INCOMPATIBLE:state`. |
| 7 | `c04-parry-reroll` no declara la rodela en el defensor | Poner la rodela en el defensor y declarar B06.2; el atacante no lleva el arma de parada. |
| 8 | `q10-leader-six` no declara proveedor ni 6"; el líder es duelista | Construir `DuelContext(nearby=(LocalParticipant(...),), distances=((second, leader, 6),))`; el líder no sustituye al segundo combatiente. Sin líder: omitir `nearby`; fuera de radio: la misma entrada a 8". |
| 9 | `q08-death-blow-optional` no declara la decisión del origen | Declarar `decisions` y `decision_scope="uniform"`; sin guion, `NOT_RUN:decision-script`. |
| 10 | `c04-highest-injury` cita `e2e:core/combat-injury-states::the-highest-of-several-injury-results-applies`, que no existe | Usar `highest-injury-result-applies`; la identidad correcta está en el YAML actual. |
| 11 | Hay una clave de ejecución declarada solo en `deep` | Trasladar su variante base a `complete`; `deep` añade composición/sensibilidad, no reserva comportamientos. |
| 12 | Varios casos solo declaran observables terminales y pueden aprobar sin la regla | Declarar el testigo tipado de la variante; si no está publicado, `INCOMPATIBLE:witness` o comparación enfocada declarada, nunca `PASS` por actividad genérica. |
| 13 | No hay variantes negativas pareadas | Añadir `expect="absent"` + `positive_control` para toda variante con disparador/ausencia materializable, con el predicado `absent` de su tipo. |
| 14 | `validate_cases` no comprueba materialización ni `origin` | Validar `requires` contra el build (con **`off_hand_id`**) y resolver `origin` en la prueba de catálogo. |
| 15 | La cobertura se calcula por obligación | Contarla por variante, con `also_covers` y `MISSING:<variant-id>`; importar `VARIANT_KEYS` una vez y no leer `P00-results` en ejecución. |

#### P02 — `_battery_runner.py`

**Conservar**:

- Compilación única por caso y participante; el mismo `CompiledFighter` para
  ambos motores.
- `simulate_duel_observed`/`simulate_batch_observed`, normalización de ganador y
  comparación por categorías.
- Puerta seis sigma copiada literalmente de `_statistical.py:19-24`.
- Determinismo (`_same_sample`), forma (`_shape_mismatch`), timings separados,
  import perezoso del nativo, `knowledge_root()`, `backend` validado.
- `KeyError` → `NOT_RUN:decision-script`.
- `BatteryCaseResult`/`BatteryReport` y los cinco estados.

**Corregir**:

| # | Hallazgo | Corrección exigida |
| --- | --- | --- |
| 1 | `_multiplicity_failure` y su llamada aplican la regla retirada | Eliminarla. Sustituirla por el contraste de §7.7/§7.8. |
| 2 | `_activation` exige `name in _SUPPORTED` y `name in _BOOLEAN`; la intersección es vacía | Leer el testigo tipado de `OBLIGATIONS[variant]`; aplicar el predicado de su tipo, `expect` y `positive_control`. |
| 3 | `_SUPPORTED` solo contiene los 4 terminales | Ampliarlo con los testigos publicados; lo no publicado sale `INCOMPATIBLE:witness:<nombre>` con `owner`. |
| 4 | `_BOOLEAN` mezcla recursos y banderas y no decide nada válido | Retirarlo o limitarlo a la comparación; no decide activación. |
| 5 | No se evalúa `DuelContext.nearby` para B11/B14 | Consumir el contexto en el camino candidato cuando exista; si no, `INCOMPATIBLE:consumer:<variant> owner=G05`. No introducir `support`. |
| 6 | `INCOMPATIBLE:decision-scope` no tiene camino | Rechazar `case.decision_scope="per-row"` antes de compilar; documentar el adaptador P02/G02. |
| 7 | `run_battery` calcula `complete` sobre los casos recibidos | Añadir `profile`, `missing_variants`, `scope`, `accepted`; sin `profile`, `accepted=False`. |
| 8 | No hay criterio de ausencia ni control positivo | Evaluar `expect="absent"` con el predicado tipado y `positive_control`; si el control no activa, `NOT_ACTIVATED`. |
| 9 | `activation=None` se interpreta como «sin comprobación» y permite `PASS` | Un caso sin testigo admisible ni comparación enfocada es `INCOMPATIBLE:witness`, no `PASS`. |
| 10 | El informe no expone variante, testigo, tipo, expectativa ni cobertura | Añadir `variant`, `witness`, `witness_kind`, `witness_rate`, `expect`, `expect_value`, `comparison`, `coupling`, `missing_variants`. |
| 11 | No hay contraste entre caso positivo y negativo | Implementar la comprobación cruzada en `run_battery` (post-proceso del conjunto), no dentro de un único caso. |
| 12 | No hay comparación enfocada | Aceptar `comparison="focused"` con un único outcome y su dirección declarada; informar `coupling="focused"`. |

#### Entregas

`P01-deliverable.md` y `P02-deliverable.md` no existen en esta copia. Son
obligatorios incluso si la fase queda parcial. P00 no los crea: pertenecen a sus
propietarios y deben declarar alcance, archivos, evidencia y dependencias
externas.

### 7.11 Invariantes que P03 puede comprobar sin reejecutar

- `battery_cases("quick") ⊆ battery_cases("complete") ⊆ battery_cases("deep")` por
  `id`.
- Toda variante `required=True` con `case_kind="duel"` tiene al menos un caso en
  `complete`, propio o vía `also_covers` con su testigo; `missing_variants` vacío
  para `accepted=True`; las estructurales/ambiguas informan `STRUCTURAL` o
  `UNLOCATED`.
- Cada caso declara una variante registrada y un testigo evaluable por su tipo, o
  una comparación enfocada declarada; si no, `INCOMPATIBLE:witness`/
  `NOT_RUN:case-definition`.
- Cada `expect="absent"` tiene un `positive_control` de la misma variante y ambos
  aparecen en el informe.
- Un control positivo que no activa produce `NOT_ACTIVATED`, nunca `DIVERGENCE`.
- `run_battery(..., profile=...)` informa `scope="profile"`; un subconjunto informa
  `scope="provided"` y `accepted=False`.
- `VARIANT_KEYS` suma 1914 claves y 63 variantes; no hay una lista de claves a
  mano ni lectura de `P00-results` en ejecución.
- Las 1256 `shared` se informan `STRUCTURAL`; las 189 `unlocated`, `UNLOCATED`;
  las 98 `shared-operator`, por el grupo de §4.6 (9 exactas/89 pendientes), nunca
  como `PASS` genérico.
- El informe separa declarado (clave), ejecutado (caso), activado (testigo),
  observado (comparación) y pendiente/incompatible/divergente. Las 143
  «verificadas» estructurales de `_vectorized` no se mezclan con `PASS`.
- `levels` del payload es un recuento medido de casos por perfil, no una cuota.

## 8. Conexión con P03 y primeras medidas de P04

### 8.1 P03

- `--profile quick|complete|deep` selecciona `battery_cases(profile)`;
  `--backend numpy|native|all` selecciona candidato. Sin `--profile`, el
  comportamiento histórico (`--level`, `--pair-set`) queda intacto.
- Sección nueva y aditiva en `parity_report_payload`, compatible con
  `"schema": "mordheim-combat-parity/v2"`:

```python
"battery": {
    "profile": "complete",
    "scope": "profile",              # "profile" | "provided"
    "backend": "numpy",
    "complete": False,
    "accepted": False,               # complete and scope == "profile"
    "levels": {"quick": 0, "complete": 0, "deep": 0},  # recuento MEDIDO, no cuota
    "obligations": {"B06": "PASS|DIVERGENCE|INCOMPATIBLE|NOT_ACTIVATED|NOT_RUN|MISSING"},
    "variants": {"B06.1": "PASS|DIVERGENCE|INCOMPATIBLE|NOT_ACTIVATED|NOT_RUN|MISSING|STRUCTURAL|UNLOCATED"},
    "missing_obligations": tuple(...),      # agregado: obligaciones con alguna variante MISSING
    "missing_variants": tuple(...),         # 63 variantes requeridas
    "rows": {"<case id>": 64},
    "cases": tuple({...BatteryCaseResult...}),
    "by_key": {"<id>::<clause_id>": "PASS|DIVERGENCE|INCOMPATIBLE|NOT_ACTIVATED|NOT_RUN|UNLOCATED|STRUCTURAL"},
    "denominator": {"executed_required": 1914, "structural": 1256, "shared_operator": 98, "unlocated": 189},
}
```

- El informe debe separar: declarado (clave), ejecutado (caso), activado
  (testigo), observado (comparación) y pendiente/incompatible/divergente.
  Las 143 «verificadas» estructurales de `_vectorized` no se mezclan con `PASS`.
- `UNLOCATED` es un estado de clave, no de caso: no hay caso que ejecutar
  mientras el consumidor no esté localizado.
- Sin datos nuevos de formato obligatorios: no hace falta cambiar
  `deterministic`/`statistical`/`specifications`; la sección es aditiva y cita
  las reproducciones exactas existentes como evidencia aparte.
- `--require-complete` debe fallar con
  `INCOMPATIBLE`/`NOT_ACTIVATED`/`NOT_RUN`/`DIVERGENCE`, si `missing_variants` no
  está vacío, y si el denominador recalculado no está cubierto por `by_key`.
- Riesgo de cesión: `cli/commands.py` ya tiene cambios locales; el coordinador
  debe registrarla antes de que P03 lo edite. `_replay.py` solo se lee.

### 8.2 P04 — casos a medir primero (ejes de coste)

| Eje | Caso de partida | Reutilización |
| --- | --- | --- |
| Barato | duelo básico a 1 ronda | `DEEP_SCENARIOS["basic"]` |
| Medio | parada + escudo + armadura ligera | `DEEP_SCENARIOS["defences"]` |
| Medio | multiataque con hacha + daga | `DEEP_SCENARIOS["multiattack"]` |
| Alto | 75 rondas de desgaste | `DEEP_SCENARIOS["heavy-grind"]` |
| Suceso infrecuente | regeneración 5+ en el borde | fixture `mordheim-boglars-regeneration` |
| Estado compartido | miedo en carga con `fear_hit_sixes` | E2E `...minotaur--fear/mechanic.causes-fear` |
| Liderazgo | líder a 6" (`nearby`+`distances`) | E2E `...serpent-priestess--leader/mechanic.leader-six` |
| Checkpoint | horizonte 1 frente a N | `expect_rounds` del E2E |

P04 debe medir por separado: compilación (`compile_fighter`, una vez por caso),
oráculo modular por lotes (`simulate_duel_observed`) y candidato
(`simulate_batch_observed`), y la escalera de `rows` de §7.7. No hay presupuesto
prometido en este documento.

---

## 9. Bloqueos, huecos y peticiones a propietarios

| # | Hueco | Propietario | Ejemplo concreto | Entrada/salida mínima pedida |
| --- | --- | --- | --- | --- |
| 1 | El oráculo por lotes no publica recursos ni testigos por fila | **G06** (`modular/duel.py`, `mordheim_core/models.py:314`) | `simulate_duel_observed` devuelve 6 arrays; `resources_spent` no viaja | añadir `first_resources`/`second_resources` y los testigos de §7.6 a `ObservedDuelResult`, o un argumento `observed_fields=(...)`; sin cambiar el conteo de `DuelResult` |
| 2 | `VectorBatchObservation` exporta 8 campos (6 arrays y 2 tuplas de recursos) aunque `CombatState` ya lleva más | **G02** (`vectorized/_types.py`, `_driver.py:139`) | `frenzy`, `on_fire`, `entangled`, `force_of_will_active`, `broken_hands`, `hampered_main/off`, `disability`, `netted` existen y no se exportan | añadir esos arrays a `VectorBatchObservation`; es aditivo y no cambia el motor |
| 3 | El candidato no integra psicología ni liderazgo | **G05** (`vectorized/`) | existen `_psychology.py`/`_leadership.py`, pero `_driver.py` no llama a sus resolutores; no hay publicación por fila | integrar la fase y publicar los testigos, o declarar F09/F10 fuera del candidato; hasta entonces `INCOMPATIBLE:witness` |
| 4 | Estado inicial inyectado no disponible en ningún camino público | **G00** (firma) + **G02** (constructor de `CombatState`) | 1534 casos E2E con `initial_state`; p. ej. `condition.netted` al inicio | parámetro `initial_state=` en `simulate_duel_observed`/`simulate_batch_observed` o constructor público; sin emulación en el adaptador |
| 5 | Decisiones por fila no declarables con `ScriptedDecisions` | **P02** (adaptador) + **G02** (contrato de contexto) | `_attacks.py:889` ya pasa `{"row": row}`, pero `ScriptedDecisions` responde solo por clave | una política determinista que reciba el contexto o un mapa `{clave: {fila: bool}}`; hoy el caso que declare `decision_scope="per-row"` es `INCOMPATIBLE:decision-scope` |
| 6 | Doble consumo de un recurso no observable | **G06** / **G02** | `force-of-will` gastado una vez frente a dos no se distingue en el terminal | observación por evento o contador por fila; no se acredita con tasas |
| 7 | `require_optimized_support` rechaza etiquetas residuales | **G00** (admisión) | `mechanic.fear-beastmen`, `mechanic.hatred-*`, `weapon.kanabo`, `fighter.vomit_attack` | el rechazo ya es correcto: P02 lo clasifica `INCOMPATIBLE:construction`; el cierre es de G00–G06 |
| 8 | `round` sin adaptador vectorizado (10 casos) | **G06** | `condemned-inconsistency-random-characteristics/minimum-values` | implementar `_refresh_random_characteristics` o declarar el límite |
| 9 | 28 de 35 divergencias `initialize` son artefacto de comparación | **G02/G03** (adaptador) + P03 | `advanced-dwarf-parries-rangers/two-parry-capacity` (63 vs 21 campos, 0 diferencias comunes) | P02 no reutiliza ese adaptador; P03 no cuenta esas 28 como divergencia de comportamiento |
| 10 | Recursos de discapacidad con nombre distinto | **G02/G04** | `mechanic-disability/lame`: `disability.6` vs `disability.1` | decidir el nombre canónico; no lo decide P00 |
| 11 | 407 claves de ejecución sin escenario E2E | **P01** (autoría) | `F09`/`F10` sin E2E para 94 claves | cubrirlas con casos de batería agrupados y declaradas |
| 12 | 189 claves con `consumer=[]`: localización pendiente | **G01** (registro) + propietario del anexo (G03 8, G04 24, G05 16, G06 5) | `.../fen-guard-mim/.../trait.natural-armour-save::no-save-and-fire-negation`: `verification` cita `contexts.prepare_armour_context` | localizar el consumidor y corregir `consumer`; 32 tienen referencia de código, 27 solo de pruebas, 2 sin traza (`P00-results/unlocated-localization.csv`) |
| 13 | Cesión de archivos compartidos antes del paralelo | **Coordinador** | `_replay.py` (solo lectura), `cli/commands.py` (ya modificado localmente) | registrar la cesión efectiva antes de P03 |
| 14 | El candidato no consume `DuelContext.nearby`/`distances` | **G05** (consumo) + **G06** (publicación) | el modelo existe (B14.1/B14.2/B14.5/B14.9/B14.10/B14.12 lo usan en el oráculo) y `leadership.py` ya lee `nearby`/`distance`; el `_driver.py` del candidato no llama a esos resolutores | integrar el consumo y publicar el valor/flag por fila; hasta entonces `INCOMPATIBLE:consumer:<variant>`. No se requiere `support` ni un tercer `CompiledFighter` |
| 15 | La comprobación exacta `injury` no ejerce el operador vectorizado | **P03** (comprobación) + G03 | `_vectorized.py:189-200` compara `phases.injury_condition` consigo mismo; no usa `vectorized.injury_conditions` (`_operators.py:95`) | antes de citar la tabla de lesión como exacta, comparar `phases.injury_condition` con `vectorized.injury_conditions`; B07.1 queda `check-defect` |
| 16 | Una referencia `e2e:` del catálogo P01 no existe | **P01** (autoría) | `c04-highest-injury` cita `core/combat-injury-states::the-highest-of-several-injury-results-applies`; la identidad correcta es `highest-injury-result-applies` | corregir la identidad y validar los 33 orígenes `e2e:` en la prueba de catálogo |
| 17 | Varias variantes no publican su testigo tipado por fila | **G06** (oráculo) + **G02/G03/G05** | `acting-order` es categoría 0/1; `equipment` es hash; recursos, banderas y contadores de combate no viajan en los arrays | publicar el testigo con su tipo, o aceptar comparación enfocada declarada; nunca interpretar `0`/«sin eventos» como ausencia para categoría o hash |

Ninguno de estos bloqueos impide lanzar P01 y P02 en paralelo con el contrato de
§7. Los casos afectados se declaran y salen como `INCOMPATIBLE`/`NOT_ACTIVATED`/
`NOT_RUN` con su propietario; no se emulan. Las 189 `unlocated` no bloquean casos:
salen `UNLOCATED` en el informe hasta que el registro las localice.

---

## 10. Comandos ejecutados

Todos desde la raíz del repositorio. `spec-parity-baseline.txt` guarda entorno,
revisión y sha del registro de la ejecución; `initialize-divergence.txt` guarda
el resultado del sondeo de §3.4.

### 10.1 Estático (sin motores)

| Comando | Resultado |
| --- | --- |
| `python -X utf8 TMP_VECTORIAL_ENGINE_2A2B/parity_update/P00-results/reconcile_universe.py` | 3457/3457 claves con propietario; 0 huérfanas; 0 extra; 189 `unlocated`; salida `universe-reconciliation.csv` + `universe-summary.txt` (≈ 2 s) |
| `python -X utf8 .../P00-results/localize_unlocated.py` | 189 claves con `consumer=[]`: 32 con referencia de código, 27 solo de pruebas, 128 mención fuera de código, 2 sin traza; salida `unlocated-localization.csv` + `unlocated-keys.txt` (≈ 21 s) |
| `python -X utf8 .../P00-results/initialize_divergence_probe.py` | 28 `shape-only`, 7 `shared-value`; salida `initialize-divergence.txt` (ejecución interactiva, sin medida de tiempo) |
| `python -X utf8 .../P00-results/inventory_probe.py` | Reparto de las 1914 claves de ejecución por `consumer`/`effect_id`; salida `inventory-probe.txt` |
| `python -X utf8 .../P00-results/stage_probe.py` y `stage_report.py` | Operador decisivo y agrupación por variante; salida `stage-report.txt` |
| `python -X utf8 .../P00-results/inventory_build.py` | Genera `behaviour-inventory.csv`: 1914 filas, 1914 claves únicas, 63 variantes, 0 genéricas, 0 duplicadas; recuento en `behaviour-summary.txt` |
| `python -X utf8 .../P00-results/validate_inventory.py` | Valida claves contra la reconciliación, una fila por clave, prefijo `Bxx`, sumas 1914/63, referencias y dependencias no vacías; salida `inventory-validation.txt` (solo lectura, sin motores) |
| `python -X utf8 .../P00-results/shared_operator_review.py` | Revisa las 98 `shared-operator` contra las comprobaciones exactas; salida `shared-operator-review.tsv` + `shared-operator-detail.txt`: 9 exactas, 89 pendientes |
| `python -X utf8 .../P00-results/reference_check.py` | Valida los 33 orígenes `e2e:` del catálogo P01: 1 inexistente (`c04-highest-injury`); salida `reference-check.txt` |

### 10.2 Ejecutado contra modular y candidato (sonda, **no certifica paridad**)

| Comando | Resultado | Duración |
| --- | --- | --- |
| `python -X utf8 .../P00-results/baseline_probe.py` | `verify_vectorized_parity`: 391/143/248/0, `complete=False`; `verify_specification_parity`: 3793 casos, 3733 PASS, 10 pendientes, 50 divergencias, `complete=False` | 0,4 s + 348,7 s (total ≈ 349 s) |
| `python -X utf8 .../P00-results/contract_probe.py` | Compila `FighterBuild`→`CompiledFighter`; 16 filas de oráculo y candidato; `repeat_is_deterministic=True`, `shape_mismatch=none`, `row0_equals_solo=False` (el ancho del lote cambia el flujo); salida `contract-probe.txt` | ≈ 1 s |

Ambas entradas se ejecutaron **sin modificarlas**. No son campaña de la batería:
no hay casos de batería todavía.

### 10.3 Ejecutado contra el modular únicamente

- Los 5163 casos E2E no se ejecutaron en P00 (no es su encargo); se leyeron
  `corpus.py` y los YAML para extraer `audit_id`, `covers`, `initial_state`,
  `duel_context`, `expect_rounds` y `expect_error`.
- No se ejecutó ninguna prueba nueva.

### 10.4 Pendiente (no ejecutado, no acreditado)

- Batería quick/complete/deep: no existe.
- Cualquier comparación de comportamiento F09/F10 (psicología/liderazgo): el
  candidato no integra la fase en `_driver.py`, así que hoy no hay nada que
  comparar en lote.
- Verificación de paridad de recursos y testigos por lotes: el oráculo no los
  publica (G06). Solo existe la comparación de recursos en las reproducciones
  exactas ya escritas.
- Estado inicial inyectado (`initial_state`): no hay camino público (G00/G02).
- Consumo de `DuelContext.nearby`/`distances` en el candidato y publicación de
  los testigos de psicología/liderazgo por fila: sin camino (G05/G06). El
  oráculo ya consume el contexto; la representación existe.
- Doble consumo de recursos y eventos intra-ronda: sin observación (G06).
- `--backend native`: no se ejercitó; el candidato nativo puede estar obsoleto
  (`CONTEXT_VERSION`) y eso debe salir como `NOT_RUN`.

---

## 11. Decisiones, interfaces y cesiones

1. **Clasificación por consumidor**, no por tag: `shared`, `shared-operator`,
   `runtime`, `mixed`, `unlocated`. Las 1256 `shared` son obligación estructural
   de compilación. Las 98 `shared-operator` **no** son una clase de equivalencia:
   solo 9 tienen evidencia exacta y solo para una variante; 89 quedan como
   obligación diferencial pendiente (§4.6). `unlocated` (189) es localización
   pendiente, nunca «estructural».
2. **La familia localiza, la variante inventaría.** F00–F11 y
   `RUNTIME_FAMILIES` se conservan para localizar consumidores y para el informe;
   la unidad de comportamiento es la variante `Bxx.y` respaldada por
   `behaviour-inventory.csv`. El CSV de reconciliación no se mantiene después.
3. **Dos evidencias separadas**: exactitud por operador (`_specifications.py`) y
   reproducciones existentes (`test_duel_replay.py`); amplitud y sensibilidad por
   la batería de muestras. La batería no se presenta como exacta y no reescribe
   las reproducciones.
4. **Sin guiones por motor**: `BatteryCase` no contiene tiradas. El caso declara
   semilla, filas, decisiones y testigo; P02 usa `simulate_duel_observed` y
   `simulate_batch_observed`. Una semilla igual no implica tiradas iguales, y la
   comparación es de distribución, no fila a fila.
5. **El lote se comprueba como lote**: determinismo, forma y **contraste de
   testigo** positivo/negativo (§7.8). La multiplicidad de la revisión 2 se
   retira: una categoría rara ausente de una muestra independiente no prueba
   fallo de máscara. Se midió que la fila 0 de un lote no reproduce una ejecución
   individual con la misma semilla (el ancho cambia el flujo de tiradas), así que
   repetir una fila no se acepta como evidencia de lote.
6. **Compilar una vez**: P02 compila `FighterBuild` con `compile_fighter` antes
   de muestrear y reutiliza ese `CompiledFighter`; nunca pasa un build al motor.
7. **Checkpoints = horizontes**, no un segundo mecanismo de observación.
8. **`INCOMPATIBLE` es un resultado de primera clase**, no un aprobado:
   construcción rechazada, observable o testigo no publicado, consumo del
   contexto ausente, decisión per-row o backend sin capacidad. `NOT_ACTIVATED`
   tampoco aprueba, y un control positivo que no activa nunca se convierte en
   `DIVERGENCE`.
9. **`NOT_RUN` no es aprobado**; `complete` exige además cobertura de las
   **63 variantes** del perfil y `accepted` exige `scope="profile"`. Un
   subconjunto puede ser `complete` en sentido interno pero nunca `accepted`.
10. **P00 no diagnostica las 50 divergencias** ni las reinterpreta: solo separa
    las 28 que son artefacto de comparación y deja las 22 restantes como
    resultado preexistente del candidato para P02/P03 y los propietarios.
11. **Sin cesiones nuevas de P00.** P01 escribe solo `_battery_cases.py` y su
    comprobante opcional; P02 solo `_battery_runner.py`, `_specifications.py` y su
    comprobante. `_replay.py` se reutiliza en lectura; `cli/commands.py` requiere
    cesión del coordinador antes de P03.
12. **Denominador sin registro paralelo**: P03 recalcula las claves de ejecución
    portando `consumer_class` de `reconcile_universe.py`; P01 adjunta claves a
    variantes (`VARIANT_KEYS`, importado una vez de `behaviour-inventory.csv`).
    Las 189 `unlocated` se cuentan aparte y no se suman a cobertura. No queda una
    lectura permanente de `P00-results/` ni una segunda lista manual.
13. **Testigo tipado, no actividad.** La actividad genérica no acredita
    activación. Cada variante declara `Witness(kind, present, absent)`:
    `counter|flag|category|direct-result|hash`. `condition`/`wounds` solo son
    testigos directos en `B07.*`/`B15.*`; `acting-order` es categoría 0/1 y
    `equipment` un hash. Sin testigo ni comparación enfocada, la variante queda
    pendiente y el caso sale `INCOMPATIBLE:witness`, nunca `PASS`.
14. **Defecto propio de P03 localizado**: la comprobación `injury` de
    `_vectorized.py:189-200` compara `phases.injury_condition` consigo mismo y no
    ejerce `vectorized.injury_conditions` (`_operators.py:95`). B07.1 queda
    `check-defect` hasta corregirla (§4.3).
15. **Contexto existente, sin `support`.** `DuelContext.nearby` y `distances` con
    `LocalParticipant` son la entrada de B14; se separan representación (existe),
    consumo (el candidato no lo hace: G05) y publicación (G06). «Sin líder» y
    «fuera de radio» son controles válidos. `off_hand_id` es el campo real.
16. **Una variante no acredita sus secundarias.** `skill.regeneration` (save)
    no acredita B15.2 (recuperación del revenant); `mechanic.devoted-to-the-vampire`
    toca B11.7 y B02.2; cada una exige su testigo o `also_covers` explícito.

---

## 12. Propuestas para el CSV

Ninguna clave pasa a `verified` por este documento. P00 no ha ejecutado la
batería; las claves admitidas siguen con `status.numpy` y `status.native` en
`pending`, como estaban.

Propuestas concretas y mínimas, para que el coordinador decida **después** de que
P02/P03 aporten ejecución real:

| Clave | Campo | Propuesta | Motivo |
| --- | --- | --- | --- |
| `core/combat-parry::parry-attempt` | `evidence` | referenciar el caso de batería que la cubra, cuando exista y pase | hoy tiene 7 escenarios E2E modulares y 0 comparación |
| `mechanic/mechanic.causes-fear::cause-fear` | `evidence` | ídem, con testigo `fear-hit-sixes` | sin operación semántica; el candidato no integra la fase (G05) |
| `.../mechanic.leader-six::leader-six` | `evidence` | ídem, con `DuelContext.nearby`/`distances` y control a 8" | B14.1 usa el contexto local existente; el consumo/publicación del candidato es G05/G06 |
| `.../band--mutations-tentacle/special-rule...::whole` | notas | declarar que `tentacle-grapple` no se publica por fila en ninguno de los dos caminos (G02/G06) | evita confundir incompatibilidad con divergencia |
| las 189 con `consumer=[]` | `consumer` | localizar el consumidor real o marcarlo explícitamente como no consumido; no cambiar `clause_scope` | 32 citan código en `verification`, 27 solo pruebas, 2 sin traza; «estático» no está probado |
| las 3 `shared-operator` de restricciones de equipo | `consumer_class` | reclasificar a `shared` (compilación compartida) | no son duelo; §4.6 |
| `core/combat-injury-states::chart` (B07.1) | notas | señalar que la comprobación exacta `injury` no ejerce el operador vectorizado hasta corregir `_vectorized.py:189-200` | hoy la tabla de lesión no está acreditada por esa comprobación |

No se propone ningún cambio masivo por etiqueta o por familia: una etiqueta
compartida no demuestra equivalencia semántica. Ninguna propuesta toca
`status.numpy`/`status.native`: eso exige ejecución de P02/P03.

---

## Anexo — Cómo continuar

- P01: implementar §7.2–§7.4 en `_battery_cases.py`: `OBLIGATIONS` con 63
  variantes, `Witness` tipado por variante, caso con `variant`/`expect`/
  `positive_control`/`witness_value`/`also_covers`/`requires`, y `_fighter` con
  todos los campos de `FighterBuild` (incluido `off_hand_id`). Importar una vez
  `behaviour-inventory.csv` a `VARIANT_KEYS` y pasar a ser el propietario de la
  pertenencia. Corregir los casos de §7.10 (materializar reglas, referencia rota,
  rodela en el defensor, líder en `nearby` a 6", decisión declarada) y añadir las
  variantes negativas pareadas. Declarar el testigo real de cada variante: lo no
  publicado sale `INCOMPATIBLE:witness` o comparación enfocada declarada, nunca
  `PASS` por actividad.
- P02: implementar §7.5–§7.9 en `_battery_runner.py`: compilar una vez, muestrear
  con `simulate_duel_observed`/`simulate_batch_observed`, comparar por categorías
  con la puerta seis sigma, comprobar determinismo/forma/contraste (§7.8), aplicar
  el predicado tipado con `expect`/`positive_control`, consumir `DuelContext`
  (o declarar `INCOMPATIBLE:consumer`), rechazar `decision_scope="per-row"` y
  calcular `complete`/`accepted` con `profile`/`missing_variants`. Eliminar
  `_multiplicity_failure`. No tocar `_replay.py` ni añadir guiones.
- P01/P02: crear sus entregas obligatorias (`P01-deliverable.md`,
  `P02-deliverable.md`) con alcance, archivos, evidencia propia y dependencias
  externas, incluso si la fase queda parcial.
- P03: conectar §8.1; recalcular el denominador (1914 ejecución, 1256
  estructurales, 98 `shared-operator`, 189 `unlocated`); informar por variante
  (`missing_variants`) y no heredar las 28 divergencias `initialize` ni las 143
  verificadas estructurales como `PASS`; corregir la comprobación `injury`
  (§4.3).
- P04: medir §8.2 antes de fijar los perfiles y la escalera de `rows`; medir la
  compilación aparte.
- P05: aceptar solo con `accepted=True` de la batería y con los bloqueos de §9
  cerrados por sus propietarios.
