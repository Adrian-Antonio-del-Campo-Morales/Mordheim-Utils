# Combat

Fases, motor modular y vectorizado. Consume luchadores compilados y no carga YAML. Véase [Arquitectura](../../../docs/architecture.md).

## Paridad entre motores

La evidencia semántica corresponde al motor modular. El vectorizado usado por la UI se
certifica por separado mediante `python -m mordheim_combat_lab parity`: cada campo, etiqueta
y secuencia compleja del oráculo debe tener un consumidor y evidencia vectorizada.

Las antiguas divergencias de `Poisonous` y de la Iniciativa del arma secundaria están cubiertas
por regresiones explícitas. Una regla puede seguir ejecutándose mientras su paridad está pendiente,
pero no puede entrar en un camino de ejecución nuevo u optimizado hasta quedar certificada.

La KB y el motor modular son el oráculo protegido. Una divergencia detectada durante el trabajo
del vectorizado se presume un defecto del candidato: `parity` solo los lee y nunca los modifica.
Cambiar el oráculo requiere una revisión semántica independiente y queda fuera del flujo de
optimización.

## Reportes

`python -m mordheim_combat_lab test-report` ejecuta el inventario de paridad y
la suite técnica, y genera CSV preparados para Excel en `outputs/test-report/`.
El reporte semántico coloca juntos los resultados y estados del modular, NumPy
y nativo. Un estado `PENDING` no equivale a una divergencia: puede indicar que
falta el adaptador vectorizado o que el backend nativo aún no está disponible.

La guía completa de opciones y estados está en
[Generar reportes de tests y paridad](../../../docs/tasks/generate-test-reports.md).
