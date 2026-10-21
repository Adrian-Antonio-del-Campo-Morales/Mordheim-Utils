# P02 — Adaptador y comparador (corrección de preparación)

Base: P00-deliverable.md **revisión 4** y las adendas **A8–A10** de
`COORDINATOR-progress-review.md` (P00 aceptado como base de preparación). No se
reabre el contrato. El modular es el oráculo validado. **No se ejecutaron
NumPy, nativo ni campañas de paridad**; esta entrega es preparación y su
evidencia es estructural/sintética. No hay commits.

## 1. Archivos

| Archivo | Cambio |
| --- | --- |
| `apps/combat-lab/mordheim_combat_lab/verification/parity/_battery_runner.py` | Reescrito sobre la base revisión 3: testigos tipados, controles, cobertura por variante, `blocked_by`, sin multiplicidad |
| `tests/python/verification/test_parity_battery_runner.py` | Nuevo comprobante mínimo, solo objetos sintéticos; no compila ni muestrea motores |
| `_specifications.py` | Sin cambios: no fue necesario para la preparación |
| `_battery_keys.py` | Solo lectura: transferencia de pertenencia generada por el coordinador (63 variantes/1914 claves); P01 la importa |
| `tests/python/verification/test_duel_replay.py` | Sin cambios de autoría en esta tanda; no se ejecutaron sus ramas candidatas |

No se tocaron motores, KB, CSV canónico, corpus, `_replay.py`,
`cli/commands.py`, `_battery_cases.py` ni `_battery_keys.py`.

## 2. Contrato implementado

- `run_battery(cases, *, profile=None, backend="numpy", rows=None, root=None)`
  conserva compilación única por caso/participante, muestreo por
  `simulate_duel_observed`/`simulate_batch_observed`, normalización de ganador,
  puerta seis sigma literal de `_statistical.py:19-24`, determinismo, forma,
  tiempos separados, import perezoso del nativo y `KeyError` →
  `NOT_RUN:decision-script`.
- `BatteryCaseResult` publica `variant`, `obligation`, `witness`,
  `witness_kind`, `witness_rate`, `expect`, `expect_value`, `comparison`,
  `coupling`, `rows`, tiempos y `detail`. `BatteryReport` añade `accepted`,
  `scope`, `profile` y `missing_variants`.
- **A8**: ninguna variante se excluye por una entrada pendiente. Un caso con
  `blocked_by` sigue en el informe y sale `INCOMPATIBLE` con propietario
  (`state:*`, `consume:*`, `witness:*`, `decision:*`); no se compila ni muestrea.
- **A9**: `condition`/`wounds` son `direct-result` solo en B07/B15;
  `leadership-test-value` y `psychology-dice` son resultados medidos válidos en
  B11/B14. La pertenencia a `OUTCOMES` se admite sin exigir que el nombre esté
  además en `WITNESSES`.
- **A10**: el positivo enfocado no lleva `positive_control`; el negativo lo
  referencia. `_resolve_controls` resuelve la pareja **antes** de aprobar: un
  positivo sin negativo queda `NOT_ACTIVATED:no-negative-control`; un negativo
  sin control o con control no activado queda `NOT_ACTIVATED`; un control que no
  discrimina o una pareja sin capacidad discriminante queda
  `NOT_RUN:criterion-insensitive:<variant>` `owner=P01`.
- Predicados por tipo: contador (`count>0`/`count==0`), bandera
  (`flag-true`/`flag-false`), categoría (`class-equals`/`class-differs`, incluido
  `acting-order` 0/1), resultado directo (`value-equals`/`value-differs`) y hash
  (`hash-changes`/`hash-same`). No se aplica `>0` a categorías ni hashes.
- Multiplicidad retirada: se eliminó `_multiplicity_failure` y no se exige que
  una categoría rara del oráculo aparezca en el candidato. Solo una diferencia de
  distribución tras ejecutar ambos motores produce `DIVERGENCE`.
- Cobertura: `missing_variants = required_variants(profile) - {caso.variant ∪
  also_covers}`. `complete` exige ausencia de estados fallidos y de variantes
  faltantes; `accepted` exige además `profile` y `scope="profile"`. Sin perfil,
  `scope="provided"` y `accepted=False`.

## 3. Dependencias externas (no bloquean la preparación)

| Dependencia | Propietario | Efecto actual |
| --- | --- | --- |
| Estado inicial inyectado | G00/G02 | `INCOMPATIBLE:state`; el caso permanece |
| Consumo de `DuelContext.nearby/distances` en el candidato | G05 | `INCOMPATIBLE:consumer:<variant>` |
| Publicación por fila de recursos, banderas, psicología, liderazgo y contadores de combate | G02/G03/G05/G06 | `INCOMPATIBLE:witness:<nombre>` con propietario |
| Decisiones por fila | P02/G02 | `INCOMPATIBLE:decision-scope` antes de compilar |
| Catálogo P01 (`VARIANTS`, `VARIANT_KEYS`, `required_variants`) | P01 | interfaz importada; si cambia un nombre, falla en importación, no en silencio |

## 4. Comprobaciones preparadas (a ejecutar por el coordinador)

```text
python -m pytest tests/python/verification/test_parity_battery_runner.py -q
python -m pytest tests/python/verification/test_parity_battery_cases.py -q
python -c "import mordheim_combat_lab.verification.parity._battery_runner"
```

El comprobante no ejecuta candidatos: usa `SimpleNamespace`, arrays sintéticos y
monkeypatch del camino de ejecución. Los datos sintéticos acreditan
infraestructura, no paridad. No se declara cobertura ejecutada ni se actualiza
`status.numpy`/`status.native`.

## 5. Pendiente propio

- Verificar en integración que el catálogo P01 expone exactamente
  `VARIANTS`, `VARIANT_KEYS` y `required_variants`, y que el vocabulario de
  observables incluye los testigos usados por las variantes.
- `blocked_by="witness:<propietario>"` deriva el nombre del testigo de la
  variante; el formato `witness:<nombre>:<propietario>` también se acepta. Si P01
  usa otra forma, el caso sale `NOT_RUN:case-definition` (no se aprueba).
- La aprobación enfocada queda pendiente de que existan parejas completas en el
  catálogo; hoy el runner no la concede a un positivo aislado.
