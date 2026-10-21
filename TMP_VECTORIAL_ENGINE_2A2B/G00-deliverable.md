# G00 — Base, admisión por backend y coordinación (entrega)

## Base utilizada

- Repositorio: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK` (misma copia de trabajo indicada por el encargo; no se creó una copia aislada nueva).
- HEAD: `c91c2a7cccd7a2bd807504f302d92d3dc1d3c340`, más los cambios locales existentes (144 entradas en `git status --short`, incluido el trabajo de verificación modular previo y `TMP_VECTORIAL_ENGINE_2A2B/` sin seguimiento). No se hizo commit ni push.
- CSV canónico intacto: SHA-256 `b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731`, idéntico al de la preparación. No se escribió el registro.
- Estado de partida relevante: el motor modular se considera implementado y validado; el encargo no reinterpreta reglas.

## Resumen del trabajo

Se separó la admisión de los dos backends optimizados. `require_optimized_support` y `compile_duel_plan` aceptan ahora `backend` (`"numpy"` o `"native"`) y cada uno consulta su propia instantánea de capacidades pendientes. La ruta NumPy queda lista para que los grupos de portado retiren entradas de su puerta sin tocar la nativa; la nativa conserva la instantánea completa y sigue rechazando lo no portado. Las llamadas antiguas sin `backend` mantienen el comportamiento conservador (puerta nativa), por lo que ningún llamador gana soporte accidental.

Todos los llamadores localizados de ambas funciones pasan el backend que realmente ejecutan:

| Llamador | Backend que pasa | Motivo |
| --- | --- | --- |
| `_driver._simulate_batch_core` | `numpy` | Núcleo por lotes NumPy. |
| `_driver.simulate_duel_parallel` | `numpy` | Partición paralela del mismo driver NumPy. |
| `_driver.simulate_duel` | backend seleccionado (`auto` resuelto antes de admitir) | La admisión corresponde al motor que se va a despachar. |
| `_driver.simulate_duel` → `compile_duel_plan` | `native` | Plan del backend nativo. |
| `verification/parity/_replay.replay_duel` | backend de reproducción | Reproducción NumPy o nativa con su propia puerta. |
| `application/settings._native_segment_eligible` | `native` | Elegibilidad de segmentos nativos. |
| `cli/calibration.run_calibration` | backend del bucle | Exclusión de parejas por la puerta del backend medido. |
| `native/_combat_compile.compile_duel` | sin argumento (puerta nativa conservadora) | Archivo no propiedad de G00; se deja la llamada histórica, que ya usa la puerta nativa. |

## Archivos y funciones modificados

- `packages/python/combat-engine/mordheim_combat/kernel.py`
  - Nuevo `OptimizedBackend = Literal["numpy", "native"]`.
  - Nuevo `PendingCapabilities` (etiquetas residuales, modificadores locales, perfiles de arma y comportamientos dinámicos).
  - `_pending_snapshot()` con el contenido exacto de las listas previas.
  - `NUMPY_PENDING`, `NATIVE_PENDING` y `_PENDING` (dos puertas independientes; misma instantánea inicial).
  - `pending_capabilities(backend)`: lectura de la puerta, error explícito para backend desconocido.
  - `require_optimized_support(first, second, *, backend=None)`: admisión por backend; sin `backend` usa la puerta nativa.
  - `compile_duel_plan(..., backend=None)`: propaga la selección; la firma pública anterior sigue siendo válida.
- `packages/python/combat-engine/mordheim_combat/vectorized/_driver.py`: los cuatro puntos de admisión indicados arriba. No se cambiaron firmas públicas ni el protocolo de estado; `_new_state`, `_refresh_random_characteristics`, `_resource_observation`, `_simulate_batch_core` conservan sus firmas.
- `apps/combat-lab/mordheim_combat_lab/application/settings.py`: selección de backend nativo al compilar el plan de elegibilidad (único cambio).
- `apps/combat-lab/mordheim_combat_lab/cli/calibration.py`: la llamada de admisión pasa el backend del bucle (único cambio).
- `apps/combat-lab/mordheim_combat_lab/verification/parity/_replay.py`: el plan se compila con el backend de reproducción (único cambio).
- `tests/python/combat/test_kernel_plan.py`: un comprobante nuevo (ver abajo).

No se modificaron `vectorized/__init__.py` (no hizo falta una exportación nueva), `_types.py`, Cython ni ningún archivo de otro propietario.

## Puntos de extensión entregados a G02/G03/G04/G05

- **Admisión:** `_driver._simulate_batch_core` admite explícitamente con `backend="numpy"`. G02 no necesita tocar la admisión al ampliar estado.
- **Estado:** las firmas históricas `_new_state(fighter, count, rng)`, `_refresh_random_characteristics(fighter, state, rows, rng)` y `_resource_observation(state)` se conservan; `CombatState` sigue siendo el punto de extensión de campos (propiedad G02, este grupo no escribe `_types.py`).
- **Avance de la puerta NumPy:** un grupo que conecte un comportamiento debe reemplazar la instantánea de forma explícita, conservando la nativa:
  ```python
  from dataclasses import replace
  from mordheim_combat import kernel
  kernel._PENDING["numpy"] = replace(
      kernel.pending_capabilities("numpy"),
      local_modifier_tags=kernel.pending_capabilities("numpy").local_modifier_tags - {"mechanic.x"},
  )
  ```
  Solo se retira una etiqueta o comportamiento cuando su ruta NumPy está conectada; `NATIVE_PENDING` no se toca. La entrega no retira ninguna entrada: no hay portado nuevo en G00.
- **Cesión del driver:** a partir de esta entrega `_driver.py` queda cedido a G02 (solo inicialización/observación) y después a G06, según el README.

## Claves principales asignadas

Las cuatro claves son referencias de admisión (`consumer` incluye `kernel.py::require_optimized_support`); no se ha portado su comportamiento en G00, por lo que su estado real sigue siendo `pending` en NumPy y nativo.

| id | clause_id | Estado real | Propuesta de CSV |
| --- | --- | --- | --- |
| `rule/mordheim/call-of-the-night-haint-mim/corpse-master--magical-void/mechanic.magical-void` | `whole` | Admisión separada; comportamiento no portado | Sin cambio (`numpy: pending`, `native: pending`) |
| `rule/mordheim/dreamwalkers-cult-of-morr-fbg/andanti--andanti-knowledge/mechanic.andanti-knowledge` | `whole` | Ídem | Sin cambio |
| `rule/mordheim/dwarf-slayer-cult-web/band--slayer-rules/profile.equipment-restrictions` | `deathwish--scope--deathwish-psychology` | Ídem; su etiqueta sigue en la puerta local | Sin cambio |
| `rule/mordheim/ghost-pirates-sar/sea-singer--beauty-of-the-sea/mechanic.beauty-of-the-sea` | `whole` | Ídem | Sin cambio |

## Claves de apoyo

| id | clause_id | Responsable | Contribución de G00 |
| --- | --- | --- | --- |
| `source/catalog/campaign/exploration-and-income.yaml/campaign.magical-artefact.count-of-ventimiglias-misericordia/unclassified` | `misericordia-injury` | G04 | `weapon.count-of-ventimiglias-misericordia` permanece en la puerta residual de ambos backends; la admisión ya distingue NumPy/nativo cuando G04 lo conecte. |
| `source/catalog/hirelings/hired-swords/grade-1c.yaml/hireling.hired-sword.pyromaniac.rule.crazed-firestarter/unclassified` | `never-charge` | G05 | `mechanic.cannot-charge` permanece en la puerta residual de ambos backends, con la misma separación por backend. |

No se propone `implemented` para ninguna de las seis: no hay conexión de comportamiento nueva, solo la base de admisión.

## Comandos ejecutados y resultados

```text
python -m pytest tests/python/combat/test_kernel_plan.py tests/python/combat/vectorized/test_backends.py -q -n 8 --tb=short
  -> 5 passed in 2.09s

python -m pytest tests/python/cli/test_calibrate.py -q --tb=short
  -> 5 passed in 9.65s

# Humo NumPy (ruta real del driver, sin fallback modular):
simulate_duel(DuelRequest(f,f,20,seed=7), backend="numpy")
  -> DuelResult(first_wins=8, second_wins=12, unresolved=0, simulations=20)

# Disponibilidad y registro:
available_backends() -> ('native', 'numpy')
sha256(clause-contracts.csv) -> b2d4887c03a187f119f6fdd4f581d0ea9067d31f51b34d98a465d786bacd4731
```

Comprobaciones **no** ejecutadas: campaña de paridad (fase 2, G07), suite vectorial completa, rendimiento (fase 3). No se declara paridad.

## Casos nuevos y justificación

Uno solo, en `tests/python/combat/test_kernel_plan.py::test_numpy_and_native_admission_gates_are_independent`. Es imprescindible porque las dos puertas parten de la misma instantánea y sin él no hay prueba de que sean independientes: retira `mechanic.magical-void` únicamente de la puerta NumPy y comprueba que NumPy admite, la puerta nativa sigue rechazando y la llamada histórica sin `backend` sigue rechazando. No se añadieron pruebas por cláusula ni se copiaron E2E.

## Bloqueos y limitaciones

- Ningún bloqueo para la base entregada. La ruta nativa no se modificó y mantiene sus rechazos; su comprobación de ejecución con capacidades futuras no aplica hasta que exista un portado nativo.
- La admisión NumPy sigue rechazando exactamente lo mismo que antes: G00 no adelanta soporte. Cada grupo debe retirar su entrada solo tras conectar el comportamiento; si el coordinador aplica ese cambio, debe conservar `NATIVE_PENDING`.
- El archivo `native/_combat_compile.py` no es propiedad de G00 y conserva la llamada sin `backend`; al usar la puerta nativa conservadora su comportamiento es el correcto hoy. No se propone cambio.
- `vectorized/__init__.py` no requirió cambios: no hay helper nuevo que reexportar.
