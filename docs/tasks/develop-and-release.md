# Desarrollar y distribuir

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m mordheim_combat_lab validate
python -m mordheim_combat_lab verify
python -m mordheim_combat_lab test-report
```

`verify` admite pendientes; `--require-complete` no. `test-report` genera los CSV
humanos de paridad y tests técnicos; use `test-report --require-complete` como
puerta estricta cuando el backend optimizado deba estar completamente certificado.
Consulte [Generar reportes de tests y paridad](generate-test-reports.md).

Antes de optimizar, guarde una línea base reproducible:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --save-baseline outputs/benchmarks/numpy-before.json
```

Después del cambio, ejecute la misma configuración y active la puerta acordada:

```powershell
python -m mordheim_combat_lab benchmark -n 100000 --backend numpy --baseline outputs/benchmarks/numpy-before.json --require-improvement --output outputs/benchmarks/numpy-after.json
```

La puerta exige una mejora del 10 % en algún escenario sin degradar otro más del 5 %.
Finalmente, construya Windows con `tools\windows\build_MordheimCombatLab_ONEFILE.bat`.

Terminado cuando pasan tests y validación, el estado semántico no retrocede y el paquete contiene la KB pero no especificaciones ni archivo histórico.
