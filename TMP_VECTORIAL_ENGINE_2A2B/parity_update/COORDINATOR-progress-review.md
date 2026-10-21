# Revisión del avance P00–P02

## Separación vigente de planes y cierre del rework

Decisión de coordinación del 2026-10-21: G07 está terminando con su batería
actual y cierra dentro del plan del motor, con los límites de esa evidencia.
El rework P00 → P01/P02 → P03 tiene cierre independiente. P00 revisión 4 +
A8–A10 siguen siendo la base aceptada de P01/P02; esta separación no reinicia
su trabajo ni altera el contrato de casos.

**P03 cierra el rework con todos los tests rápido/completo/profundo definidos y
conectados:** entradas, variantes, referencias de cláusulas, observables,
controles, criterios, comparadores, CLI e informes, con parámetros iniciales
explícitos. No deja autoría requerida para P04 y no necesita ejecutar candidatos
ni esperar a G07. Las carencias del motor se describen como requisitos externos
de ejecución, sin omitir tests ni fingir resultados.

**P04/P05 son una campaña posterior:** P03 terminado y versión fija del motor
entregado por G07 → medición/calibración P04 → aceptación P05 con la batería
renovada. P04 conserva escenarios y obligaciones; calibra parámetros, no completa
tests ausentes. P05 no es G07, no condiciona ni sustituye su cierre, y no hereda
cobertura de aquella campaña. Los defectos de preparación descubiertos al medir
o ejecutar vuelven al propietario correspondiente con su impacto documentado.

Esta decisión sustituye las formulaciones anteriores que dividían P04 en
«preparación actual» y «calibración futura» o identificaban P05 con G07. Las
entregas y notas anteriores conservan valor como evidencia de su momento, pero
esas frases no rigen la continuación. Solo se modifican documentos del rework
en `parity_update/`; los planes del motor quedan fuera de esta actualización.

---

## P00 revisión 4 — aceptación de la base de preparación, 2026-10-21

**P00 aceptado como base de preparación para corregir P01/P02**, con las tres
adendas de contrato siguientes. Sustituyen las frases contradictorias señaladas;
P01/P02 no deben volver a decidirlas. Esta aceptación no acredita comportamiento
del candidato, cobertura ejecutada ni paridad. No se ejecutaron motores ni campañas.
No hace falta devolver todo P00: se conservan inventario y contrato revisión 4
junto con estas precisiones.

### Comprobación enfocada

- `python -X utf8 TMP_VECTORIAL_ENGINE_2A2B/parity_update/P00-results/validate_inventory.py`:
  salida `OK`, exit 0; 1914 filas y claves únicas, 63 variantes; recuentos del
  catálogo y reconciliación coinciden. El script solo lee documentos/CSV y
  actualiza `P00-results/inventory-validation.txt`.
- Comprobación adicional de solo lectura contra el registro vivo, usando la
  clasificación existente: 4556 filas, 3457 admitidas, 1914 `runtime/mixed`,
  ninguna clave faltante o extra respecto al inventario.
- Hash del inventario: `58beba4428b676c88393605db7c6eb51bfe7f2b8a886bd4240ce29f7b09e4955`.
  El registro volvió a cambiar concurrentemente: hash observado
  `2096df6eba24ed106b03a6033b1e438793dc1bc4bec40ac02b7423a8fc4056f3`.
  Se verificó el universo actual; no se afirma estabilidad de todo el motor.
- Asignaciones señaladas corregidas: sangre fría → B11.5 (6 claves), liderazgo
  automático → B14.3 (18), espinas → B15.4 (2), Great Thirster y Devoted → B11.7
  (2+2). Las variantes describen ahora sus disparadores distintos y controles.
- Retirados `support` y la dependencia artificial de una firma nueva; se usa
  `DuelContext.nearby/distances` con `LocalParticipant`. Se corrigió `off_hand_id`.
- Se conserva la transferencia única al catálogo, cobertura por variante,
  requisitos propios para `also_covers` y separación de dependencias externas.

### A8 — Una entrada pendiente no excluye una obligación requerida

En P00 §7.2 se dice que `required=False` puede documentar una entrada todavía
inexistente. **Esa excepción queda retirada.** Todas las variantes base admitidas
del inventario siguen requeridas en `complete`, aunque dependan de inyección de
estado, observaciones o consumo futuros. La preparación puede quedar terminada
con la dependencia explícita; una futura ejecución sin esa capacidad queda
incompleta/incompatible, nunca aceptada por reducir el denominador. No usar
`required=False` para ocultar soporte pendiente. Las variantes estructurales y
ambiguas mantienen su tratamiento diferenciado, sin fingir ejecución de duelo.

### A9 — Resultados directos tipados según la tabla de testigos

En §7.2 se limita todo `kind="direct-result"` a B07/B15, pero §7.6 lo usa también
para `leadership-test-value` y `psychology-dice`. **La restricción se aplica al
nombre `condition`/`wounds`, no al tipo entero.** `leadership-test-value` y
`psychology-dice` son resultados medidos válidos en sus variantes B11/B14, con
predicados y valor esperado definidos por §7.6. `condition`/`wounds` conservan
el límite B07/B15 y necesitan preparación que haga discriminante ese resultado;
no se convierten en testigos genéricos de otras reglas. Para un testigo directo
se admite pertenencia a `OUTCOMES`; los demás nombres deben estar registrados
en el vocabulario acordado. No exigir `witness.name in WITNESSES` cuando el
nombre admitido es precisamente `condition` o `wounds` de `OUTCOMES`.

### A10 — Parejas enfocadas sin controles circulares

§7.3 prohíbe `positive_control` en un caso positivo, pero lo exige para todo caso
`comparison="focused"`. **Rige la primera regla para el positivo y la segunda
solo para el negativo.** El positivo enfocado no lleva `positive_control`; debe
existir un negativo de la misma variante que lo referencie. El negativo lleva
`expect="absent"` y `positive_control=<id positivo>`. Ambos declaran el mismo
resultado enfocado y una preparación que justifique su capacidad discriminante.
P02 resuelve la pareja completa antes de emitir aprobación enfocada: no convierte
el positivo aislado en evidencia. Si falta el control o no discrimina, aplica los
estados de falta de activación/defecto del criterio de §7.7. Nunca se inventa
activación por evento ni independencia de filas a partir del contraste.

### Continuación autorizada por el plan

Corregir P01 y P02 con P00 revisión 4 + A8–A10 y archivos disjuntos, conservando
lo aprovechable. Primero autoría/materialización y comparador; después P03 conecta
las herramientas preparadas. No ejecutar candidatos durante esa preparación.
Mantener las entregas obligatorias P01/P02 y los límites de propiedad existentes.
Los trabajos G00/G02/G03/G05/G06, el check `injury` (P03), las 98 `shared-operator`
con evidencia diferenciada y las 189 `unlocated` no son certificados por este cierre.
Se registran y conservan sus obligaciones/dependencias; no se cambia el CSV canónico.

---

## Historial de revisiones anteriores (sustituido en P00 por la aceptación anterior)

## Revisión de P00, entrega revisión 3 — 2026-10-21

**Dictamen vigente sobre P00: avance válido, preparación todavía parcial.** Esta
sección revisa la nueva entrega y sustituye el diagnóstico anterior de P00 donde
corresponda. No se ejecutaron motores ni campañas; las comprobaciones siguientes
son lectura de documentos/código y reconciliación estructural.

### Confirmado y reutilizable

- Registro actual: SHA256
  `dc023c50db47776ef86b7d0a0a7c8cca4c800b69f970522981ce4e79245e7dba`, coincide
  con el cierre de P00. 4556 filas, 3457 admitidas.
- `behaviour-inventory.csv`: 1914 filas, 52 identificadores de variante,
  sin claves duplicadas, faltantes ni extra frente a las 1914 `runtime/mixed`
  según la clasificación existente. Esto confirma la reconciliación, no la
  equivalencia semántica de los grupos.
- Se confirma por lectura `_vectorized.py:189-200`: el check `injury` compara
  `phases.injury_condition` consigo mismo. Es un defecto del comprobante;
  prepararlo correctamente no exige resultados del candidato.
- Retiradas las cuotas y la multiplicidad por presencia de categorías. Separar
  resultado/testigo y declarar dependencias son correcciones aprovechables.
- Reutilizando solo los lectores de `reference_check.py`, sin su escritura de
  resultados: 33 orígenes E2E, uno inexistente (`c04-highest-injury`). Es una
  corrección de autoría de P01 ya identificada, no un nuevo bloqueo de P00.

### Correcciones de preparación necesarias

1. **Separar grupos que tienen contratos diferentes.** El generador todavía
   decide mediante substrings de `effect_id` y símbolos consumidores
   (`inventory_build.py:440-556`). Hay 182 claves en variantes «other … rules»
   con preparación «según efecto», sin terminar su discriminación. Ejemplos que
   ya demuestran un error, sin reinterpretar reglas:
   - P00 §4.4/B11.2 incluye `mechanic.cold-blooded-psychology` como inmunidad y
     exige ausencia de la prueba/evento. `modular/leadership.py:305-310` aplica
     su convención de dados al resolver la prueba; no elimina la prueba.
   - B14.1 obliga a radio 6/12 pulgadas y tercer aliado para
     `mechanic.automatic-leadership`; `modular/leadership.py:152-153` devuelve
     éxito automático sin esa preparación. Liderazgo por radio, automático y
     bonificaciones por aliados necesitan obligaciones/variantes propias.
   - B15.2 asigna `trait.spines` a recuperación de una herida al inicio de turno.
     El consumidor ejecuta ataques de espinas, no curación
     (`modular/rounds.py:1153-1163`). No puede heredar ese criterio.
   Conservar todas las claves reconciliadas. Corregir las pertenencias y
   documentar variantes distintas usando contratos e implementación existentes;
   las heurísticas pueden localizar trabajo, no decidir equivalencias.

2. **Hacer aplicable el contrato de testigos.** §7.2 exige `witness` dentro de
   `WITNESSES`, pero §7.6 permite `condition`/`wounds` como testigos directos y
   ambos están solo en `OUTCOMES`. Definir una regla consistente. §7.7 usa
   «evento > 0» y «cero eventos» para todo testigo, aunque `acting-order` es una
   categoría 0/1 y `equipment` un hash: cero no significa ausencia de actuación
   ni un hash mide activación. Definir por obligación un predicado o contraste
   explícito para contadores, banderas, categorías y resultados directos, sin
   imponer instrumentación innecesaria donde una prueba enfocada discrimine.
   Si el control positivo no activa, aplicar `NOT_ACTIVATED` de manera coherente:
   §7.7 también llama a ambos ceros `DIVERGENCE:witness-insensitive`, aunque no
   se haya observado diferencia del candidato. No atribuir un defecto de caso
   u oráculo no activado a una divergencia entre motores.

3. **Reutilizar el contexto existente y permitir controles negativos reales.**
   `LocalParticipant` y `DuelContext.nearby/distances` ya representan aliados
   compilados y sus distancias (`mordheim_core/models.py:207-243`), y el muestreo
   recibe `context`. Antes de pedir una entrada nueva `support` a G05, especificar
   la conversión mínima desde el origen E2E a ese contexto. Una posible falta de
   consumo/publicación futura se asigna por separado; no es ausencia del modelo
   de entrada. §7.3 exige `support` en todo B14.1, pero el propio control negativo
   requiere poder declarar «sin líder». No imponer ese invariante al caso
   negativo. Corregir además `off_weapon_id` por el campo real `off_hand_id`.

4. **Mantener la pertenencia junto a los casos y cubrir las variantes.** §7.2
   dice que el CSV auxiliar sigue siendo la pertenencia exacta clave→variante;
   §7.4 calcula cierre con al menos un caso por obligación. El CSV debe ser la
   foto de diseño de P00, transferida al catálogo ejecutable de P01, sin lectura
   permanente de `P00-results` ni segunda fuente manual sincronizada. Precisar
   cómo se adjuntan y contabilizan todas las variantes requeridas y obligaciones
   secundarias: un caso genérico no acredita automáticamente cada clave del
   grupo. Conservar la revisión diferenciada de las 98 `shared-operator`, sin
   convertir sus asignaciones por efecto en evidencia de todas sus cláusulas.

**Siguiente paso:** corrección dirigida de estos puntos en la misma entrega P00,
conservando la reconciliación válida y sin ejecutar candidatos. P01/P02 pueden
avanzar en correcciones de autoría y comparador ya inequívocas; no congelar aún
la revisión 3 como interfaz final para ambos. Las dependencias G00/G02/G05/G06
siguen sin bloquear el cierre de una preparación correcta.

---

## Revisión anterior de la base P00 revisión 2 y primera tanda P01/P02

Fecha: 2026-10-21. Revisión de la copia actual, rama `main`, HEAD
`c91c2a7cccd7a2bd807504f302d92d3dc1d3c340`, con cambios locales concurrentes.
Esta revisión sustituye los veredictos de aceptación de
`COORDINATOR-P00-review.md` y `COORDINATOR-P01P02-integration.md` en los puntos
indicados abajo. Se conservan ambos documentos como evidencia histórica.
La revisión original no modificó motores, KB, CSV ni escenarios.

**Rectificación de alcance tras aclaración del usuario:** el vectorial todavía
está en implementación; ahora solo se preparan tests. Las ejecuciones de esta
revisión quedan como evidencia histórica y no son requisitos de aceptación de
P00–P03. Se retira cualquier bloqueo de preparación o P03 basado en resultados,
fallos o capacidades todavía ausentes del motor. Se conservan los hallazgos sobre
defectos propios del inventario, entradas, referencias y comparador. Un test puede
quedar preparado con una dependencia externa explícita. P04 prepara y mide el
lado modular ahora; su calibración candidata y P05 son futuros.

## Dictamen

| Fase | Avance aprovechable | Estado revisado |
| --- | --- | --- |
| P00 | Reconciliación de claves, fuentes reutilizables y borrador concreto de interfaz | Parcial: falta el inventario por comportamiento/variante y corregir criterios de prueba. No aceptado como inventario completo. |
| P01 | Catálogo importable, selección acumulativa y claves admitidas | Parcial: numerosos casos omiten la regla/preparación citada; las referencias no acreditan reutilización efectiva. |
| P02 | Compilación compartida, ejecución real de ambos motores, normalización de ganador y comparación por categorías | Preparación parcial por criterio de máscara incorrecto, contrato de testigos pendiente y entrega ausente. No se exige disponer ya del motor ni observar su activación. |
| P03 | Aún sin conexión de batería en CLI/informes | Conectar cuando interfaces y herramientas estén preparadas, con avance independiente permitido. No requiere candidato implementado ni resultados aprobados. |
| P04 | Preparación de mediciones y coste modular | Realizable ahora; calibración del candidato diferida hasta su integración. |
| P05 | Aceptación de paridad | Futura, después de G00–G06 y calibración candidata; fuera del trabajo actual. |

No deben descartarse los módulos entregados ni repetir las investigaciones válidas.
Tampoco deben completarse cuotas de casos para convertir estas fases en aceptadas.

## Hallazgos que cambian las conclusiones anteriores

### 1. P00 reconcilia claves, pero todavía no inventaría sus comportamientos

`P00-deliverable.md:105` y §4 asignan familias por módulos consumidores. §5.2
enumera dimensiones generales y §5.3 reparte cantidades por familia. No existe
la relación completa exigida por P00: comportamiento/variante → grupo de claves
con equivalencia justificada → preparación/disparador → observable discriminante
→ referencia reutilizable/hueco. `universe-reconciliation.csv` tampoco contiene
esa relación: clasifica consumidores y adjunta un ejemplo E2E por clave.

Compartir consumidor sirve para localizar, pero el plan excluye usarlo como
demostración de equivalencia. Se conserva la reconciliación; se retira la
conclusión «P00 completo; no se reabre». Los objetivos aproximados 31/125/149
no están respaldados por una selección identificada de casos y no son criterios
de aceptación. P01 debe terminar obligaciones demostradas, no alcanzar cuotas.

La exclusión conjunta de las 98 claves `shared-operator` también necesita
evidencia aplicable: `reconcile_universe.py:165` decide por la ruta
`combat/phases`, mientras `_operators.py:26,86,99` contiene proyecciones NumPy
propias de impactos, heridas y lesión. Puede bastar la evidencia exacta existente,
pero hay que vincularla al comportamiento y sus variantes; no exigir por ello
98 duelos nuevos ni asumir que siete checks genéricos acreditan las 98 claves.
El denominador 1914 es la clasificación de diseño actual, no un universo
definitivamente demostrado de obligaciones diferenciales.

### 2. P01 sustituye situaciones por duelos que no contienen la regla

Ejemplos contrastados con los YAML referenciados y los `FighterBuild` efectivos
en `_battery_cases.py`:

| Caso | Preparación que falta o se sustituye |
| --- | --- |
| `q04-natural-armour-six` (línea 157) | Usa armadura ligera en un combatiente genérico; el origen usa un jefe bestia con `band--beastmen-special-skills-shaggy-hide`. No prueba piel natural. |
| `q05-flammable-fire` (185) | Usa maza contra espada; el origen usa `weapon.brazier-iron` contra el perfil `scarecrows`. Faltan fuego e inflamabilidad. |
| `q11-black-hunger` (246) | El primer combatiente no lleva `skill_ids=("mechanic.black-hunger",)` que sí tiene el origen. No hay hambre negra que comparar. |
| `q00-honorable` (255) | Faltan `mechanic.honorable` y el rival inicialmente derribado. El duelo desde cero no comprueba la prohibición citada. |
| `c04-parry-reroll` (270) | El título y origen requieren espada y rodela; no se declara rodela. |
| `q10-leader-six` | No declara aliado cercano, distancia de 6 pulgadas ni decisión del origen; pone al líder como duelista. Publicar el observable no arreglaría esa preparación. |

El contrato P00 §7.2 prohíbe ejecutar desde cero un E2E que necesita estado inicial
y presentarlo como equivalente. El catálogo incumple ese límite. Las notas
«pendiente de entrada dirigida» tampoco evitan que un caso sin la regla llegue
a `PASS` si conserva solo observables terminales soportados.

Se validaron todas las identidades `e2e:` del catálogo. Una no existe:
`c04-highest-injury` referencia
`e2e:core/combat-injury-states::the-highest-of-several-injury-results-applies`.
Los dos tests actuales no comprueban referencias ni materialización de la regla.

### 3. La activación no se resuelve con la adenda A6

`_SUPPORTED` del runner solo admite `winner`, `rounds`, `wounds`, `condition`.
Ninguno pertenece a `_BOOLEAN`: `_activation` no puede obtener hoy una activación
válida. Los casos con banderas no publicadas salen antes como incompatibles;
los restantes pueden aprobar con `activation=None`.

Sonda real: `run_battery((q04-natural-armour-six,), rows=16)` devuelve
`complete=True`, `PASS`, `activation=None`, aunque la piel natural ni siquiera
forma parte de la entrada. Ese `complete` describe el éxito del subconjunto
proporcionado; no acredita el perfil ni la regla. P03 tendrá que controlar además
el universo requerido, como estaba previsto.

A6 debe sustituirse: **los impactos no se pueden deducir de heridas/condiciones
terminales**. Un impacto salvado o que no hiere no deja esa información.
`wounds-changed`/`condition-changed` pueden mostrar actividad genérica, pero no
que actuó una parada, inmunidad, recurso o regla concreta. Hace falta un testigo
específico o una comparación cuya capacidad de distinguir el comportamiento esté
justificada. Si no existe, conservar la obligación pendiente/incompatible y
pedir la observación mínima al propietario; no conceder `PASS` por actividad.
Los casos de ausencia necesitan su criterio negativo y vínculo con la variante
positiva; no exigir activación positiva a una ausencia.

### 4. La comprobación de multiplicidad confunde muestreo con fallo de máscara

`_battery_runner.py:272` exige que cada categoría de ganador que aparezca en el
oráculo aparezca también en el candidato con frecuencia intermedia. Los motores
no comparten tiradas fila a fila. Una categoría rara puede aparecer en una
muestra y no en la otra aunque ambas tengan la misma distribución.

Reproducción mínima del comparador: oráculo con 63 ceros y un uno; candidato con
64 ceros. `_compare(..., 64)` acepta con la puerta estadística vigente, mientras
`_multiplicity_failure(..., 64)` declara fallo de máscara. No hay justificación
para atribuir ese resultado a un estado compartido entre filas.

Los **cuatro** `DIVERGENCE` reproducidos del rápido con 16 filas son precisamente
`DIVERGENCE:batch-mask`. Por ello se retira la atribución de esas cuatro salidas
a defectos de reglas del motor. Esto no demuestra que el motor sea correcto:
demuestra que esa evidencia no localiza ni acredita esos defectos.

También se repitieron los tres casos citados con 64 filas por la integración
anterior: `q04-injury-chart`, `q04-parry-attempt`, `q11-black-hunger` dan ahora
`PASS`. Es una sonda diagnóstica de la revisión, no un reintento de aceptación ni
una calibración que cambie muestras. En una copia concurrente las cifras
históricas necesitan su versión de código; no se reutilizan como evidencia
actual. La prueba de lote debe discriminar acoplamiento con una observación o
criterio válido, sin imponer coincidencia de presencia de categorías aleatorias.
Este defecto nace también del contrato P00 §7.7.3: no es solo un incumplimiento P02.

### 5. Entregas y evidencia de P02 incompletas

No existen en esta copia `P01-deliverable.md` ni `P02-deliverable.md`, ambos
obligatorios incluso ante bloqueo/parcialidad. La nota del coordinador no los
sustituye. No hay comprobante específico del runner entre los archivos entregados.

La suite existente de reproducción, ejecutada en la revisión anterior bajo un
criterio que ya no se exige para preparar P02, dio **45 passed, 1 failed**. Falló
`test_disability_initialization_marker_is_not_a_spent_resource[numpy]`:
construye `mechanic.disability` sin resultado permanente y espera una tirada
durante el duelo; `_state.py:148` rechaza esa entrada con
`Disability requires a permanent supplied result, not a duel-time table roll`.
El mismo test suministra una condición permanente para su rama modular.
Este resultado histórico no bloquea P02 ni P03, ni exige repetir o corregir ahora
la rama candidata. Si se reutiliza la situación, su autoría debe conservar el
contrato aceptado; comprobarla contra el motor corresponde a la aceptación
futura. No cambiar el motor ni la expectativa para volver verde la suite.
No se revalida el modular.

La clasificación anunciada `INCOMPATIBLE:decision-scope` tampoco tiene camino
específico en el runner actual: no hay representación ni detección de la
necesidad de respuestas por fila; los `KeyError` se clasifican siempre como
guion ausente. Sigue siendo una limitación declarada, no capacidad ejercitada.

## Evidencia comprobada en esta revisión

| Comprobación | Resultado |
| --- | --- |
| Lectura del registro y unión con anexos reutilizando helpers P00, sin regenerar resultados | 4556 filas, 3457 admitidas, 0 admitidas sin propietario; 1914 `runtime/mixed` según clasificación P00 |
| Hash actual del registro | `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`, coincide con P00 |
| `python -m pytest tests/python/verification/test_parity_battery_cases.py -q` | 2 passed, 0.25 s; evidencia estructural únicamente |
| `python -m pytest tests/python/verification/test_duel_replay.py -q` | 45 passed, 1 failed, 1.04 s |
| `run_battery(battery_cases("quick"), rows=16)` | `complete=False`: 5 PASS, 4 DIVERGENCE por `batch-mask`, 2 INCOMPATIBLE por observable |
| Tres casos históricos con `rows=64` | 3 PASS; no acredita activación ni cierre de reglas |
| Referencias `e2e:` del catálogo contra YAML actuales | Una identidad inexistente: `c04-highest-injury` |
| CLI e informes | Sin conexión de `_battery_cases`/`_battery_runner` en CLI, `parity/__init__.py` ni `_report.py`; corresponde a P03 pendiente |

Cobertura **declarada**, nunca ejecutada/acreditada por estos recuentos:

| Perfil | Casos | Claves únicas adjuntas | Claves `runtime/mixed` adjuntas | Faltan sobre las 1914 de diseño | Casos sin `activation` |
| --- | --- | --- | --- | --- | --- |
| quick | 11 | 11 | 11 | 1903 | 9 |
| complete | 34 | 33 | 32 | 1882 | 28 |
| deep | 40 | 34 | 33 | 1881 | 32 |

Hay una clave de ejecución adicional declarada solo en profundo. Debe trasladarse
su obligación base a completo si no está demostrada su cobertura allí; profundo
añade composición/sensibilidad, no reserva comportamientos enteros.

No se ha reejecutado `verify_specification_parity` ni la campaña E2E. Las 50
divergencias y las cifras estructurales de las notas anteriores siguen siendo
fotografías históricas. Ya existen módulos `_psychology.py` y `_leadership.py`,
pero en el `_driver.py` inspeccionado no hay llamada a sus resolutores: separar
implementación de operadores, integración de fase y publicación de observables.
No asumir ausencia total de implementación ni integración completa por su existencia.

Hashes SHA256 de los archivos principales inspeccionados (la revisión no congela
ni certifica el resto del motor concurrente):

| Archivo | SHA256 |
| --- | --- |
| `parity/_battery_cases.py` | `b821efd262b455c348e6d949e29888764fbb58c650438ad24903d0ecae998416` |
| `parity/_battery_runner.py` | `dbaa11b93935fa7995386d6240286893ee3209d41a656b724bf6e757b0f670e1` |
| `vectorized/_driver.py` | `2b9f7a4c8412b696933560fc7a3634ff6396f294b0c4677c04b583751eecb716` |
| `tests/python/verification/test_duel_replay.py` | `8d566ad8f7201a10ad72955b3c4f462f9b184f1b623a6331b60fc3ce3e8517b2` |

## Orden de continuación y aceptación

1. **P00/coordinación:** completar el inventario discriminante reutilizando la
   reconciliación; revisar grupos compartidos y corregir el contrato de
   activación/multiplicidad. Definir testigos y preparaciones requeridas con
   dependencias externas explícitas, sin esperar a su implementación. No duplicar el registro.
2. **P01:** corregir primero los casos ya escritos: materializar sus reglas,
   preservar contexto/decisiones y estado requerido, reparar la referencia rota
   y declarar la dependencia cuando falte entrada/observación. Después completar
   comportamientos/variantes faltantes del inventario demostrado, sin cuotas.
   Crear su entrega obligatoria con alcance y evidencia.
3. **P02:** corregir el criterio de máscaras y preparar la comparación y testigos
   aplicables. Comprobar únicamente la infraestructura con mecanismos existentes
   y el mínimo caso enfocado necesario, sin ejecutar el candidato. Crear su
   entrega con dependencias externas. Puede trabajar en paralelo con P01.
4. **Coordinación:** aceptar catálogo y runner por preparación de entradas,
   observables, criterios, interfaces y sus comprobaciones propias. Los datos
   sintéticos de infraestructura no acreditan paridad. Verificar denominador y
   cobertura de diseño; no exigir resultados NumPy ni observaciones publicadas.
5. **P03:** conectar selección, CLI e informes de preparación y futura ejecución.
   No esperar al motor ni a un perfil aprobado. P04 prepara/mide el modular ahora;
   tras G00–G06 completa calibración candidata y P05 acepta sobre base fija.

Se mantienen las cesiones y límites previos; esta revisión no autoriza ediciones
adicionales de motores ni cambia `status.numpy`/`status.native`.
