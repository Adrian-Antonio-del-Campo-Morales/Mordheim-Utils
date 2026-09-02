# Generar reportes de tests y paridad

El reporte humano recomendado se genera con:

```powershell
python -m mordheim_combat_lab test-report
```

El comando ejecuta la paridad semántica y toda la suite técnica. Escribe dos
archivos en `outputs/test-report/`:

- `semantic-parity.csv`: los casos de las specs comparados entre el motor
  modular, NumPy y el backend nativo.
- `technical-tests.csv`: todos los tests recolectados por `pytest`, incluidos
  los parametrizados, su duración y cualquier error.

Los CSV usan UTF-8 con BOM y separador `;`. Están saneados para que saltos de
línea, caracteres de control o prefijos de fórmula no rompan su visualización
en Excel.

## Opciones

```powershell
python -m mordheim_combat_lab test-report --output outputs/mi-reporte
python -m mordheim_combat_lab test-report --require-complete
python -m mordheim_combat_lab test-report --statistical --statistical-simulations 100000 --seed 2026
```

| Opción | Uso |
| --- | --- |
| `--output DIRECTORIO` | Cambia el directorio de ambos CSV. |
| `--require-complete` | Devuelve error también si faltan adaptadores o el backend nativo. |
| `--statistical` | Añade los cinco escenarios estadísticos al CSV semántico. |
| `--statistical-simulations N` | Duelos por motor y escenario; por defecto 100.000. |
| `--seed N` | Semilla de las comparaciones estadísticas. |

Sin `--require-complete`, un trabajo pendiente no hace fallar el comando. Una
divergencia semántica, un fallo técnico o un error de `pytest` sí producen un
código de salida distinto de cero. Los archivos se escriben incluso si la
ejecución falla, para conservar el diagnóstico.

## Leer `semantic-parity.csv`

Cada fila representa un caso semántico. Las columnas de resultados aparecen
juntas y, a continuación, las columnas de estado:

```text
modular_result | numpy_result | native_result
modular_status | numpy_status | native_status | passes
```

`expected` contiene el observable esperado y `rules` identifica las reglas o
mecánicas que justifican el caso. `details` solo se rellena cuando existe una
limitación o un error que explicar.

Estados globales de `passes`:

| Estado | Significado |
| --- | --- |
| `PASS` | Todas las implementaciones aplicables coinciden. |
| `FAIL` | Existe una divergencia o error real. |
| `PENDING` | Falta un adaptador, una decisión semántica o un backend. |
| `OUT_OF_SCOPE` | La regla está excluida del runtime actual. |

Estados específicos como `PASS_SHARED`, `PENDING_ADAPTER`,
`PENDING_SEMANTIC` y `NOT_AVAILABLE` explican por qué se alcanzó el estado
global. `PASS_SHARED` indica que los motores consumen el mismo resultado del
compilador; no representa dos implementaciones independientes.

## Otros comandos relacionados

Para una comprobación rápida sin ejecutar `pytest` ni generar CSV:

```powershell
python -m mordheim_combat_lab parity
```

Para exigir paridad completa y guardar el certificado de máquina en JSON:

```powershell
python -m mordheim_combat_lab parity --require-complete --output outputs/parity/report.json
```

`parity --statistical` ejecuta las mismas comparaciones agregadas que
`test-report --statistical`. Una muestra inferior a dos millones de duelos por
motor se considera diagnóstico, no certificación.

Para medir rendimiento sin certificar reglas:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --scenario all --repeats 5 --save-baseline outputs/benchmarks/numpy-before.json
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --scenario all --repeats 5 --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

`benchmark` acepta `modular`, `numpy`, `native` y `all`. Cada informe JSON incluye la
configuración, las muestras individuales, la mediana, simulaciones por segundo y datos del
entorno. Una línea base solo se compara cuando semilla, tamaño de lote, calentamientos,
repeticiones y número de simulaciones coinciden.

La puerta de rendimiento aplica los criterios del desarrollo del motor optimizado:

- al menos un escenario comparable debe mejorar un 10 %;
- ningún escenario comparable puede empeorar más de un 5 %.

Los umbrales pueden ajustarse con `--min-improvement` y `--max-regression`. Sin
`--require-improvement`, una comparación fallida se muestra y se guarda en el informe, pero no
cambia el código de salida. Conviene cerrar aplicaciones intensivas y ejecutar línea base y
candidato en la misma máquina y con las mismas condiciones.
