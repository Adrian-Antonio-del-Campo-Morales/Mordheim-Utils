# Verification

Ejecuta `tests/specs/` contra el motor modular real y queda fuera de la UI. `audit_export.py` combina, sin modificar sus fuentes, el inventario editorial, el scope y la evidencia ejecutada para producir un CSV. Véase [Verificar reglas](../../../docs/tasks/verify-rules.md).

`equipment_choices` permite probar equipo, `main_poison_id`, `off_poison_id` y
`preparation_ids` mediante el compilador real. Los escenarios de prohibiciones por
categoría exigen el motivo específico del rechazo y un control legal sin la prohibición.
La mutación aislada `suppress-category-prohibitions` elimina ese validador durante
una ejecución; no modifica la KB ni convierte la ausencia en una lista de equipo
en evidencia de una prohibición explícita.

Para mini-secuencias de mutaciones, `spines` invoca el handler de inicio de ronda,
`extra_attack` resuelve un ataque adicional compilado (índice explícito) y
`attack_reaction` enlaza un ataque real con su reacción a la herida. No calculan
impactos, daño ni probabilidades por su cuenta. Los fixtures comprueban las
solicitudes de dados, la pérdida de heridas y la ausencia de críticos donde
corresponde. `pool` comprueba además que el ataque adicional se añade al normal.
