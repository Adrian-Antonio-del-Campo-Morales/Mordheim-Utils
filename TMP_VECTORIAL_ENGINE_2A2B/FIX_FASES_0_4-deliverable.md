# FIX fases 0–4 — entregable

## Revisión y base utilizada

- Repositorio: `D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK`
- Rama: `2A2Bvectorial`, HEAD `03cc8ffe`
- Fecha del pase: 2026-10-21
- Alcance ejecutado: fases 0, 1, 2, 3 y 4, en ese orden. No se ejecutaron fases 5+, campañas de paridad, benchmarks ni categorías adicionales.
- Cambios locales y concurrentes conservados: el rework de paridad siguió editando `TMP_VECTORIAL_ENGINE_2A2B/parity_update/*`, `apps/combat-lab/.../parity/_battery_*.py` y `tests/python/verification/test_parity_battery_cases.py`. No se revirtieron ni se sobrescribieron.
- Cambio local previo incluido en la base: `_operators.py` calcula una sola vez `strength_penetration` en `armour_targets` (misma aritmética, sin cambio de comportamiento).

### Cambio de infraestructura necesario para poder ejecutar

`tests/conftest.py` exige exactamente una marca de fase por test clasificado y aborta la sesión completa cuando falta. `tests/python/verification/test_parity_battery_runner.py` tenía 19 tests sin marca, de modo que **cualquier** `test-sequence` fallaba en colección con `19 collected test(s) lack exactly one phase category`.

Se añadió una sola línea, `pytestmark = pytest.mark.phase5_vectorized`, coherente con el archivo hermano `test_parity_battery_cases.py`. No contiene lógica ni datos de paridad y solo afecta a la selección de la fase 5. El archivo pertenece al rework de paridad: se registra aquí la petición al coordinador para que lo asuma o reclasifique; sin la marca no arranca ninguna fase.

## Comandos

Un proceso por fase, con marca temporal real y sin sobrescribir informes:

```text
python .\tools\mordheim-utils.py test-sequence -stepN --workers 10 -q --output reports/stepN-TIMESTAMP.txt
```

## Resultado final por fase

| Fase | Informe | Resultado |
| --- | --- | --- |
| 0 — Arquitectura e infraestructura | `reports/step0-2108.txt` | **90 passed — passed** |
| 1 — KB y contratos (inicial) | `reports/step1-2103.txt` | 828 passed, 6 skipped |
| 1 — KB y contratos (tras retirar los tests de fuente) | `reports/step1-fix-215604.txt` | **828 passed, 0 skipped — passed** |
| 2 — Construcción (inicial) | `reports/step2-2108.txt` | 2712 passed, 19 failed |
| 2 — Construcción (tras corrección) | `reports/step2-fix-211552.txt` | **2731 passed — passed** |
| 3 — Reglas y operadores modulares (inicial) | `reports/step3-2108.txt` | 3482 passed, 3 failed |
| 3 — Reglas y operadores modulares (tras corrección) | `reports/step3-fix-212702.txt` | **3485 passed — passed** |
| 4 — Motor modular | `reports/step4-2126.txt` | **5425 passed — passed** |

Total final de las cinco fases: **12 559 passed, 6 skipped, 0 failed**.

Los informes `step0`, `step1`, `step2`, `step3` y `step4` fueron ejecutados por el usuario; los dos informes `*-fix-*` los ejecuté yo para confirmar las correcciones. La fase 4 se ejecutó mientras se editaban pruebas de fase 2/3; ninguna de esas pruebas pertenece a la selección `phase4_modular`, por lo que su resultado no queda invalidado.

## Causas corregidas

### Fase 2 — 19 pruebas de puerta describían una conexión ya aceptada

Los fallos estaban en `test_shifty_activation.py`, `test_spectral_touch_activation.py` y `test_vomit_attack.py`: exigían que las entradas optimizadas rechazaran Shifty, Spectral Touch y Vomit por «no portados». El commit `e6308ce7` declaró los tres en `NUMPY_CONNECTED_BEHAVIOURS` sin actualizar esas pruebas.

Diagnóstico con selección mínima:

- **Shifty:** `simulate_duel(..., backend='numpy')` ejecuta; `auto`/`native` rechazan, pero el Elder nombra antes su contrato Leader (`Local modifier`). El Cook sin ese contrato produce el rechazo específico `Shifty` en `compile_duel_plan`/`compile_duel`.
- **Spectral Touch:** la puerta NumPy admite el behaviour (`require_optimized_support(..., backend='numpy')` pasa), pero el Spirit Host canónico arrastra otro modificador local pendiente, así que todas las entradas rechazan nombrando ese contrato primero.
- **Vomit:** NumPy ejecuta la petición; `auto`/`native` rechazan nombrando el modificador local pendiente del Troll.
- **Entradas de bajo nivel:** `compile_duel_plan`/`compile_duel` usan la puerta nativa y rechazan; `simulate_batch`/`simulate_duel_parallel` usan la puerta NumPy y ejecutan los tres comportamientos conectados.

Corrección en las propias pruebas de puerta, sin tocar reglas, contratos ni el gate:

- NumPy: se afirma la ejecución real (una simulación resuelta) en lugar del rechazo obsoleto.
- Nativo/auto: se mantiene la afirmación de rechazo con `match='modular engine'`, porque la puerta nombra la primera capacidad pendiente y en estos guerreros no es la del behaviour.
- Se conserva el rechazo específico de Shifty en el Cook, el de Spectral Touch en la prueba sintética, y se añade la admisión NumPy de esa puerta sintética.
- La petición NumPy de Vomit usa Leadership explícita: la prueba de miedo al cargar la exige en ambos motores (el modular lanza el mismo `ValueError`).

### Fase 3 — mensaje de puerta fijado a una capacidad que no es la primera pendiente

Misma clase de causa, sin cambio de comportamiento:

- `test_canonical_six_wounds_once_without_a_wound_or_critical_die[wights, grave-guards]`: Wights lleva `mechanic.causes-fear` y `mechanic.psychology-immunity`; Grave Guards, `mechanic.psychology-immunity`. Ambos están en `NATIVE_PENDING.local_modifier_tags`, así que la puerta lanza `Local modifier variants…` antes de llegar a Killing Blow.
- `test_spirit_knife_is_local_to_the_used_hand_and_keeps_its_armour_modifier`: el modificador impreso del cuchillo es una variante local pendiente en la puerta nativa y se nombra antes que Spectral Touch.

No se debilitó la garantía: se sigue exigiendo `ValueError` antes de ejecutar (nada se descarta en silencio); solo se dejó de fijar el nombre de una capacidad que la puerta legítimamente no alcanza primero. El rechazo específico de Spectral Touch permanece en la prueba sintética; el tag de Killing Blow se sigue comprobando en la misma prueba.

### Fase 1 — retirados los tests que exigían fuentes no versionadas

Los 6 skips de la fase 1 eran cotejos end-to-end que leían copias de documentos originales en `sources/origins/`. Esa ruta no está en el repositorio y nunca ha estado versionada (`git ls-files` no tiene ningún archivo bajo `origins/`, ningún commit la toca y no hay PDFs/HTML de manuales en el proyecto), así que en un clon limpio esos tests no pueden ejecutarse nunca; solo correrían si alguien colocase a mano los documentos.

Se retiraron los 6 tests de `phase1_kb_contracts` que dependían de esas copias y, en una segunda pasada, los 3 de la categoría `evidence` que tenían la misma dependencia: el módulo tenía 9 en total. Con ellos se retiraron la constante `ADJUDICATED`, los helpers `run_cotejo`/`grade_2a`, `GRADE_2A`, `COVERAGE`, los marcadores `KB_CACHED`/`SOURCE_PDFS_CACHED` y los imports de `json` y `yaml`, que solo usaban esos tests. El utillaje ([check_hireling_sources.py](tools/knowledge/check_hireling_sources.py)) y su documentación quedan intactos, y las pruebas que sí usan fixtures (lectura de entradas, tarifas, filas y resolución por registro) siguen verdes. La fase 1 pasa de «828 passed, 6 skipped» a **828 passed, 0 skipped**; el módulo completo queda en 10 passed, 0 skipped.

## Archivos modificados

- `tests/python/knowledge/test_hireling_cotejo.py`: retirados los 9 tests de cotejo que dependían de `sources/origins/` (6 de fase 1 y 3 de `evidence`).
- `tests/python/verification/test_parity_battery_runner.py`: marca de fase (ver arriba; archivo de paridad, petición al coordinador).
- `tests/python/combat/modular/test_shifty_activation.py`: puerta NumPy/nativa y pruebas de bajo nivel.
- `tests/python/combat/modular/test_spectral_touch_activation.py`: mensaje genérico de la puerta y admisión NumPy de la puerta sintética.
- `tests/python/combat/modular/test_vomit_attack.py`: ejecución NumPy con Leadership explícita y rechazo nativo genérico.
- `tests/python/combat/modular/test_killing_blow.py`: rechazo genérico de la puerta nativa para Wights y Grave Guards.
- `tests/python/construction/test_local_weapon_items.py`: rechazo genérico de la puerta nativa para el Spirit Knife.

No se modificaron reglas, contratos, CSV de conocimiento, motor modular ni el gate de capacidades.

## Pendientes reales

- Ningún bloqueo abierto en las fases 0–4.
- La marca de fase en `test_parity_battery_runner.py` queda a cargo del coordinador de paridad (adoptarla o reclasificarla).
- Los nombres de las tres pruebas de fase 2 conservan su redacción histórica («unported»); su cuerpo ya describe la conexión aceptada. Renombrarlas cambiaría identificadores de test sin necesidad funcional.

## Comprobaciones no realizadas

- Fases 5+ y campañas de paridad: fuera de alcance por instrucción.
- Benchmarks y categorías adicionales: no ejecutados.
- Lint (`ruff`): no instalado en este entorno; no ejecutado.
- No se hicieron commits ni pushes.
