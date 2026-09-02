# Verificar reglas

Para consultar el estado global antes de editar especificaciones:

```powershell
python -m mordheim_combat_lab audit
```

El comando genera `outputs/audit/rules-audit.csv`, codificado para abrirse correctamente en Excel. Puede limitar la salida con `--scope YES`, `--status pending` y `--output <directorio>`. Es una operación de solo lectura respecto a la KB, las especificaciones y el código.

## Preguntas y decisiones de revisión

El CSV separa el estado de trabajo (`review_status`) de la evidencia semántica
(`semantic_status`). Para ver qué decisiones necesitan respuesta, filtre
`review_status = needs_ruling`, no todas las filas `pending`.

| review_status | Significado |
| --- | --- |
| `needs_ruling` | Existe una pregunta explícita aún sin respuesta documentada. |
| `blocked_by_dependency` | No hay una pregunta propia sin resolver, pero falta verificar una dependencia. |
| `ready` | Queda trabajo de implementación, búsqueda de fuentes o verificación; no hay una decisión explícita sin respuesta ni una dependencia sin verificar. No significa que la regla funcione ya. |
| `verified` | La evidencia semántica exigida está aprobada. |
| `not_applicable` | Efecto fuera del scope activo. |

Para generar solo las preguntas sin sustituir el informe completo:

```powershell
python -m mordheim_combat_lab audit --review-status needs_ruling --output outputs/audit/questions
```

`question` conserva la pregunta aunque se haya resuelto. `ruling` contiene la
respuesta adoptada y su fundamento (fuente, sección o decisión del usuario).
`interpretation` es la explicación general de la especificación: no implica que
haya existido una pregunta o una decisión adicional. Las antiguas explicaciones
exportadas como `ruling` se conservan ahora en `interpretation`.

Estos datos se editan en la especificación YAML correspondiente dentro de
`tests/tests/specs/semantic/`, **nunca manualmente en el CSV generado**. El estado se calcula;
no se escribe `review_status` en YAML. Ejemplo real resuelto:

```yaml
question: ¿Swordmaster del Duelist de Hochland concede repetir una parada fallida?
ruling: >-
  No. Hochland Bandits / Duelist / Swordmaster solo permite igualar el impacto.
  Espada más rodela conserva su repetición independiente.
```

Si falta respuesta, omita `ruling` y mantenga `pending` con el motivo del bloqueo.
El cargador rechaza una pregunta sin respuesta que no esté marcada pendiente.
Cuando se resuelva, conserve `question`, añada `ruling` y retire o actualice
`pending` según el trabajo restante. Una respuesta no verifica la regla: hay
que actualizar y ejecutar los escenarios, sus dependencias y mutaciones.
Si la fuente cambia, la huella invalidará la evidencia anterior como hasta ahora.

Véase `tests/specs/semantic/grants/editorial-hochland-swordmaster.yaml` para una pregunta
resuelta, y `tests/specs/semantic/rules/contextual-bonuses-and-rulings.yaml` para preguntas
pendientes. No se reconstruye automáticamente un historial de decisiones que
no se haya documentado; se incorpora al revisar cada especificación.

## Procedimiento

1. Consulte `python -m mordheim_combat_lab verify --inventory`.
2. Añada en `tests/tests/specs/semantic/` fuente, interpretación, categoría, casos, interacción y huellas revisadas.
3. Cubra activación, no activación, límites y consumo; use mini-secuencias solo para estado o flujo.
4. Declare dados y decisiones exactos; use fracciones para distribuciones.
5. Añada una mutación detectada por comportamiento, no solo por el mismo campo compilado.
6. Ejecute `python -m pytest tests/verification/test_semantics.py -q` y `python -m mordheim_combat_lab verify --json`.

Si falta un ruling, marque pendiente. Terminado cuando la obligación, dependencias, interacciones y mutaciones están aprobadas.

Para restricciones de equipo, `equipment_choices` ejecuta el compilador real para cada construcción de
`context.choices` y devuelve `result.accepted` y `result.rejected` (con el motivo exacto).
No calcula por sí mismo la legalidad. Véase `tests/specs/semantic/grants/editorial-savage-equipment.yaml`:
comprueba armas legales, armaduras prohibidas y el perfil vecino sin la restricción.
Una prueba de prohibición no debe pasar simplemente porque el objeto no está en la lista del guerrero.
La mutación aislada `suppress-bound-equipment-restrictions` desactiva solo ese control y lo restaura al salir.

Para elecciones de habilidades, reglas especiales, variantes y `energy_focus_attacks`,
use `selection_choices`. Devuelve las listas de opciones aceptadas y los motivos exactos
de rechazo tras llamar al compilador real; no decide la legalidad por su cuenta.
El caso debe partir de una construcción válida y declarar las selecciones alternativas
en `context.choices`. Véase `tests/specs/semantic/grants/editorial-required-initial-choices.yaml`:
prueba cero, una y dos elecciones y elimina temporalmente el requisito con
`suppress-required-initial-choices` para demostrar que la prueba detecta su ausencia.

Distinga una fuente ambigua de una limitación de implementación al escribir `pending`.
Una regla que también prohíbe adquirir mejoras después del reclutamiento no queda
verificada por comprobar solamente su cantidad inicial. Los ficheros
`tests/specs/semantic/grants/editorial-recruitment-and-magic-gaps.yaml` y
`tests/specs/semantic/rules/construction-verification-gaps.yaml` documentan esos pendientes;
no aportan evidencia aprobada ni requieren todos una decisión del usuario.

## Riesgo y prioridad de interacciones

La auditoría separa el riesgo técnico de la exigencia actual:

| Campo | Valores |
| --- | --- |
| `risk_level` | `critical`, `high`, `medium`, `low` |
| `verification_requirement` | `required`, `recommended`, `optional`, `not_applicable` |
| `interaction_status` | `tested`, `covered_by_composition`, `independent`, `illegal`, `pending`, `needs_ruling` |

La política está en `tests/specs/interaction-policy.yaml`. Por defecto, `critical` y
`high` son `required`, `medium` es `recommended` y `low` es `optional`. Solo las
interacciones requeridas sin resolver bloquean `semantic_complete`; las demás
siguen visibles para ampliar la cobertura más adelante.

La clasificación automática parte de los conceptos leídos y escritos por cada
regla. Estado persistente, heridas y recursos compartidos son críticos; ataques,
prioridad y salvaciones compartidas son de riesgo alto. Una revisión puede
sobrescribir la clasificación mediante `overrides`, dejando motivo y evidencia:

```yaml
overrides:
- bindings: [<binding-a>, <binding-b>]
  risk_level: medium
  verification_requirement: recommended
  status: covered_by_composition
  risk_reasons: [generic_additive_operator]
  evidence: [operator:stack]
```

Un override es una decisión semántica revisada, no un mecanismo para hacer pasar
el informe. Debe explicar por qué una composición genérica, una incompatibilidad
o una prueba existente cubre la pareja.
