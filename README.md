# Mordheim Combat Lab

Simulador de duelos cuerpo a cuerpo 1 contra 1 basado en una base de conocimiento versionada. La aplicación activa usa el motor vectorizado para los análisis y dispone de un motor modular escalar para reproducir y verificar reglas por fases.

## Empezar

Requiere Python 3.10 o posterior.

```powershell
python -m pip install -e ".[dev]"
python -m mordheim_combat_lab
```

```powershell
python -m mordheim_combat_lab ui
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
python -m mordheim_combat_lab parity --require-complete
python -m mordheim_combat_lab parity --statistical --statistical-simulations 100000 --require-complete --output outputs/parity/report.json
python -m mordheim_combat_lab test-report
python -m mordheim_combat_lab audit
python -m mordheim_combat_lab benchmark -n 100000
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --save-baseline outputs/benchmarks/numpy-baseline.json
python -m pytest -q
```

`validate` comprueba estructura y conexiones. `verify` ejecuta evidencia semántica independiente; `verify --require-complete` es la puerta estricta. `audit` genera en `outputs/audit/` un CSV con scope, implementación y evidencia por regla. El informe ejecutable, no una cifra copiada aquí, es la fuente del estado actual.

`parity` certifica separadamente el motor vectorizado contra el modular: inventaría campos,
etiquetas y secuencias, ejecuta operadores exactos y, opcionalmente, cinco comparaciones
estadísticas. `benchmark` mide por separado el motor modular, el vectorizado (NumPy) y el
backend nativo, con calentamiento, repeticiones y mediana; acepta `--json`, `--scenario` y
`--backend` para limitarlo a un motor. Si el backend nativo no está instalado o no admite un
escenario, se informa como no disponible sin ocultar los resultados de los otros motores.
Los informes pueden guardarse con `--output` o `--save-baseline`. Una ejecución posterior con
`--baseline ... --require-improvement` exige por defecto una mejora mínima del 10 % en algún
escenario y rechaza regresiones superiores al 5 % en cualquier escenario comparable.
Una muestra estadística inferior a dos millones por motor se etiqueta como diagnóstico, no como
certificación. El informe puede guardarse como JSON o Markdown mediante `--output`.

`test-report` es la salida humana recomendada. Ejecuta la paridad semántica y la suite
técnica y escribe `semantic-parity.csv` y `technical-tests.csv` en
`outputs/test-report/`. Ambos usan UTF-8 con BOM y separador `;` para Excel. Añada
`--statistical` para incorporar los cinco escenarios agregados y `--require-complete`
para tratar adaptadores o backends pendientes como error. Consulte
[la guía de reportes](docs/tasks/generate-test-reports.md) para las columnas, estados,
opciones y códigos de salida.

## Mapa del proyecto

- `sources/knowledge/`: reglas y datos consumidos por el runtime.
- `specs/`: contrato estructural, escenarios e interacciones de verificación.
- `domain/`: tipos y composición pura; `knowledge/` y `construction/`: carga y compilación.
- `combat/`: fases, motor modular y motor vectorizado.
- `verification/`: auditorías fuera del runtime de la UI.
- `application/`, `persistence/` y `ui/`: casos de uso, formatos y Tkinter.
- `archive/`: código histórico no mantenido ni empaquetado.

Consulte [la arquitectura](docs/architecture.md) y [las guías de tareas](docs/README.md).

## Distribución en Windows

```powershell
tools\windows\build_MordheimCombatLab_ONEFILE.bat
```

Incluye la aplicación activa y `sources/knowledge/`, pero no `specs/` ni `archive/`.
