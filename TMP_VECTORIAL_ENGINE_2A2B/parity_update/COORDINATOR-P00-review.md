# Revisión del coordinador — P00

> **Separación vigente de planes:** el rework termina en P03 con todos los tests
> de rápido/completo/profundo definidos y conectados. G07 termina por separado
> con su batería actual; P04/P05 son la campaña posterior con la batería renovada,
> no el cierre G07. Rige la sección inicial de
> [COORDINATOR-progress-review.md](COORDINATOR-progress-review.md). Las notas
> históricas siguientes no añaden dependencias entre esos dos cierres.

> **Nota histórica; criterio actualizado el 2026-10-21.** Para continuar, leer
> [la revisión vigente](COORDINATOR-progress-review.md) y los prompts actualizados.
> Ahora solo se preparan tests mientras se implementa el vectorial. No se exige
> ejecutar ni aprobar casos en NumPy/nativo para aceptar P00–P03 o conectar P03.
> Los resultados de candidato citados abajo no son puertas de preparación.

Fecha: 2026-10-21. Revisa `P00-deliverable.md` (revisión 2) contra la copia de
trabajo actual. Esta nota no sustituye la entrega de P00; registra la decisión
de integración y las correcciones que P01/P02 deben aplicar.

## Veredicto

La aceptación inicial de P00 queda matizada: se conserva la reconciliación y el
borrador de contrato, y se completa la relación comportamiento/variante con su
preparación y observación discriminante. P01/P02 pueden continuar las partes
independientes sobre una interfaz acordada, sin esperar a resultados del motor.

## Evidencia reproducida por el coordinador

| Comprobación | Resultado |
| --- | --- |
| `reconcile_universe.py` | 4556 filas, 3457 admitidas, 3457 claves de anexo, 0 huérfanas, 0 no admitidas; 1911 con E2E, 1546 sin; 1914 de ejecución, 407 sin E2E; 189 `unlocated`; propietarios 4/1396/12/941/280/637/187 |
| `universe-reconciliation.csv` | 3457 filas, columnas `id,clause_id,owner,consumer_count,consumer_class,behaviour_family,e2e_scenarios,e2e_example,disposition,effect_id,relation` |
| `unlocated-localization.csv` | 189 filas; `consumer=[]` confirmado en el registro |
| `contract_probe.py` | `row0_equals_solo=False`, `repeat_is_deterministic=True`, `shape_mismatch=none`; publica solo 6 arrays por motor |
| Firmas | `simulate_duel_observed(first, second, simulations, *, seed, maximum_rounds, decisions, cancel_event, context)`; `simulate_batch_observed(first, second, count, rng, maximum_rounds, decisions, *, context)`; `compile_fighter(build, root=None)` |
| `_replay.py` | `winner` del candidato se traduce `{1:0,-1:1,0:2}`; el contrato es correcto |
| Divergencias base | 50: 35 `initialize`, 5 `pool`, 4 `replacement_pool`, 3 `attack`, 2 `recovery`, 1 `acting_order`; 28 `shape-only` y 7 `shared-value` reproducidos |
| `verify_vectorized_parity` | 391 obligaciones, **296 verificadas / 95 pendientes / 0 divergencias / 7 checks exactos**, `complete=False` |

## Correcciones obligatorias al contrato (adendas)

### A1 — `knowledge_root`

El helper no está en `mordheim_construction`: vive en
`mordheim_knowledge.loader`. P02 debe usar
`from mordheim_knowledge.loader import knowledge_root` y aplicarlo cuando
`root is None`. No crear una segunda resolución de rutas.

### A2 — Clasificación de decisiones

El contrato de §7.8 mezcla dos causas distintas. Se fija así:

- `KeyError` de `ScriptedDecisions` porque la clave **no está declarada en el
  caso** → `NOT_RUN:decision-script:<clave>`, propietario **P01**. Es un defecto
  de autoría del caso, no una incompatibilidad del motor, y nunca un `PASS`.
- Una decisión que el motor necesita con **respuestas distintas por fila o por
  contexto** y que el mapa único no puede expresar →
  `INCOMPATIBLE:decision-scope`, propietario **G02/P02**.

P01 debe declarar el mapa completo de claves que su caso provoca. Puede
obtenerlas de los `decisions` del E2E reutilizado o de una ejecución de diseño
del oráculo; no puede dejar claves sin declarar y confiar en un valor por
defecto. No se añade política nueva ni se emula por fila.

### A3 — La línea base de `_vectorized` no es estable ni es cobertura

La cifra de §3.4 (143 verificadas / 248 pendientes) era válida al cerrar P00,
pero hoy es **296 / 95** porque G03 añadió literales de regla a
`vectorized/_operators.py`; `_vectorized.py` marca «verificado» por presencia
textual. Consecuencias:

- P03/P05 deben **recalcular** la cifra; no citar 143 ni 296 como cobertura.
- Ninguna de esas marcas sustituye un caso ejecutado; se informan como
  estructurales, tal como P00 ya exige.
- El informe debe registrar la revisión y el código usados, no solo HEAD.

### A4 — Correcciones de citas

- `deep_test_scenarios` está en `cli/scenarios.py`, no en `_deep.py`. Los
  conjuntos son `full=42`, `fast=30`, `mini=10`; `_deep.py` contiene
  `DeepPair`, `escalation_plan` y `certify_deep`.
- El adaptador `round` **sí existe** (`SPECIFICATION_ADAPTERS["round"]`), pero es
  restringido: solo acepta casos terminales de estado y devuelve
  `PENDING_ADAPTER` en los 10 casos de refresco. P00 lo describe como «sin
  adaptador»; la petición a G06 sigue siendo válida, la redacción no.

### A5 — Perfil rápido con familias aún no soportadas

`quick` conserva las obligaciones F09/F10 y sus observables reales
(`fear-hit-sixes`, `leadership-*`). Su disponibilidad futura se declara como
dependencia, sin reducir los casos a `winner`. Esto no impide entregar el perfil
preparado ni conectar P03. Cuando se ejecute la aceptación, la ausencia de una
capacidad producirá incompatibilidad/incompletitud y no un aprobado; no se
relaja `--require-complete`.

## Cesiones y propiedad registradas

| Archivo | Escritor autorizado |
| --- | --- |
| `parity/_battery_cases.py` | P01 |
| `tests/python/verification/test_parity_battery_cases.py` | P01 (opcional, mínimo) |
| `parity/_battery_runner.py` | P02 |
| `parity/_specifications.py` | P02 |
| `tests/python/verification/test_duel_replay.py` | P02 |
| `tests/python/verification/test_parity_battery_runner.py` | P02 (opcional, mínimo) |
| `parity/_replay.py` | Solo lectura; cualquier edición requiere cesión expresa del coordinador |
| `parity/_statistical.py` | P03 (unificación de la puerta); P02 copia la fórmula citando la línea |
| `cli/commands.py` | P03, tras esta cesión registrada; no tocar en P01/P02 |
| `_battery_cases.py` desde P02 | Solo lectura/import diferido; no editar |

P01 y P02 escriben archivos disjuntos. P02 **no importa `_battery_cases` en
tiempo de importación**: acepta los casos por atributos (duck typing) para que su
módulo sea importable antes de que P01 termine. P03 conecta ambos.

## Instrucciones de lanzamiento

- P01: implementar §7.2 y §5 con las adendas A2 y A5; entregar
  `P01-deliverable.md`; sin ejecutar la campaña.
- P02: implementar §7.4–§7.8 con A1–A3; entregar `P02-deliverable.md`; sin
  modificar el motor ni `_replay.py`.
- Ambos: leer este documento además de `PROMPTS_AGENTES.md`; no escribir el CSV.

## A6 — `activation` no cubre actividad de combate (hallazgo tras ejecutar P01/P02)

El vocabulario de `activation` solo admite banderas booleanas de recurso o
psicología, y ninguna se publica hoy; el runner la rechaza antes de ejecutar. Un
caso F03–F08 puede por tanto aprobar con `winner`/`wounds`/`condition` idénticos
sin que el comportamiento se haya activado, sobre todo con `maximum_rounds=1`.
P00 ya prohíbe aprobar por incomparecencia, pero el contrato no ofrece el
observable para evitarlo.

**Decisión corregida:** definir para cada comportamiento un testigo específico
o una comparación discriminante justificada. No derivar `hits` de arrays de
heridas/condiciones terminales: esa información no existe en ellos. Actividad
genérica tampoco prueba una regla concreta. Si falta publicación de un testigo,
preparar su contrato y asignar la dependencia al motor; no exigir que se publique
ahora ni ejecutar el candidato para aceptar el test. La futura aceptación
distinguirá activación, ausencia y dependencia no disponible sin aprobar en vacío.

## A7 — Alcance real de P01 en esta tanda

El catálogo entregado declara 11/34/40 casos (quick/complete/deep) y no adjunta
todas las obligaciones de ejecución identificadas. Completar el diseño y sus
referencias por comportamiento, sin exigir 31/125/149 casos ni resultados del
candidato. P03 puede conectar el catálogo y mostrar sus huecos de autoría y sus
dependencias externas por separado. El estado de preparación es independiente
del `complete` de una futura ejecución; no se declara cobertura por familia.

## Huecos que siguen abiertos (no bloquean P01/P02)

Los huecos de §9 son una fotografía de capacidades que debe consultarse en las
entregas de sus propietarios, sin ejecutar el candidato para actualizarla. Entre
las dependencias identificadas para la batería están:
oráculo sin recursos/estado por fila (G06), `VectorBatchObservation` sin los
arrays de estado (G02), psicología/liderazgo no ejecutados (G05), estado inicial
inyectado (G00/G02) y decisiones por fila (G02/P02). Los casos afectados se
preparan con su dependencia explícita; no se emulan. La preparación puede
aceptarse con estas dependencias; los estados `INCOMPATIBLE`/`NOT_RUN` pertenecen
a la ejecución futura.
