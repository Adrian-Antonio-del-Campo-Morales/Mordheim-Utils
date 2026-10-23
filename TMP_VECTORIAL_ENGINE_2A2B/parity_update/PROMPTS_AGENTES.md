# Paridad estadística: instrucciones y prompt vigente

Este documento ejecuta [PARITY_BATTERY_RENOVATION.md](PARITY_BATTERY_RENOVATION.md), revisado el 22 de octubre de 2026: conservar la comparación estadística de resultados de duelos y aprovechar la selección ampliada de escenarios. Sustituye los prompts anteriores de este archivo. No se relanzan P00, P01 y P02 desde cero.

La referencia reutilizable es [SCENARIO_DESIGN_REFERENCE.md](SCENARIO_DESIGN_REFERENCE.md), junto con el catálogo ejecutable y los datos auxiliares de P00. Las entregas y revisiones obsoletas se han retirado; no hay que buscarlas ni reconstruirlas. [P03-deliverable.md](P03-deliverable.md) registra el estado de la adaptación. No hay un encargo para completar instrumentación ni modificar planes del motor.

## Propiedad y validación

- Comprobar rama y cambios locales; preservar trabajo concurrente y un escritor por archivo.
- Delegar capacidades independientes en subagentes si acelera la entrega. El padre integra; no crear revisiones sucesivas ni entregas paralelas.
- Archivos del paquete: `apps/combat-lab/mordheim_combat_lab/verification/parity/`, conexión en `cli/commands.py` de la misma aplicación, comprobantes afectados de `tests/python/verification/`, `docs/reference/verification.md` y entrega `parity_update/P03-deliverable.md`.
- No editar motores, modelos compartidos, planes del motor, KB, CSV canónico ni corpus E2E. No hacer commits ni pushes ni crear otro registro de cobertura.
- Solo lectura y edición estática: no ejecutar tests, importaciones de validación, `py_compile`, compilaciones ni motores. Dejar comprobantes expresamente no ejecutados. P04/P05 serán campañas posteriores con autorización propia.

## Prompt vigente — Adaptación estadística

```text
Adapta la renovación de paridad a la decisión vigente del usuario. Implementa
el cambio; no entregues solo un diagnóstico o un nuevo plan.

Lee AGENTS.md y estos documentos:
TMP_VECTORIAL_ENGINE_2A2B/parity_update/PARITY_BATTERY_RENOVATION.md
TMP_VECTORIAL_ENGINE_2A2B/parity_update/PROMPTS_AGENTES.md
Lee SCENARIO_DESIGN_REFERENCE.md y P03-deliverable.md de la misma carpeta y
reutiliza el catálogo y las conexiones existentes. Los documentos obsoletos se
han retirado: no los busques ni restaures el contrato de instrumentación interna.

OBJETIVO
Mantener la filosofía anterior: muestras de duelos reales modular/candidato y
comparación estadística de resultados. Aprovechar el catálogo y su relación con
cláusulas/variantes y quick/complete/deep. No exigir sondas de eventos internos
para ejecutar o aprobar la comparación estadística.

TRABAJO
1. Comprueba rama, cambios locales y responsables. Reutiliza el camino histórico
   de comparación y sus helpers antes de añadir código. No reinicies inventario
   ni catálogo ni deshagas cambios ajenos.
2. Adapta runner y definición/validación de casos para ejecutar cada escenario
   válido con preparación semántica equivalente en ambos motores y comparar sus
   resultados. Las proporciones de victoria/derrota/sin resolver y tolerancias
   históricas son la base. Aprovecha duración, heridas y condiciones finales solo
   donde ya haya APIs y comparación compatibles; informa magnitudes efectivas.
3. Retira del camino estadístico los gates witness/positive_control y blocked_by
   que únicamente exigen publicación de contadores, flags, hashes o checkpoints
   de observación. Mantén los pares como escenarios normales y sus referencias.
   No interpretes expect=absent como exigir cero victorias ni conviertas
   witness_value en un resultado terminal esperado.
4. Examina aparte dependencias reales de entrada, contexto y decisiones. Un caso
   con estado inicial no expresable se conserva pendiente/incompatible, con causa
   y dentro del denominador. No borres bloqueos en masa, omitas reglas, inventes
   condiciones, fabriques estado ni emules reglas. Reutiliza preparaciones
   alternativas justificadas solo si representan fielmente el comportamiento.
5. Conserva quick ⊆ complete ⊆ deep y trazabilidad de variantes y cláusulas.
   Distingue diseño, ejecución, comparación y sensibilidad. PASS compara las
   distribuciones medidas; no certifica cada evento ni todas las reglas internas.
   Conserva los pares con/sin regla para comprobar sensibilidad en una campaña
   posterior, sin crear ahora un framework o gate universal de contrastes.
6. Conecta esta semántica en CLI e informes existentes, sin otro modo ni batería
   paralela. Mantén ruta histórica sin --profile, perfiles y backends. Native no
   cae a numpy. Divergencias y errores propios fallan; dependencias producen
   parcialidad explícita y --require-complete falla si faltan casos requeridos.
   No declares completitud por un conjunto vacío ni apruebes casos omitidos.
7. Reutiliza compilaciones y muestra modular cuando coincidan entradas y
   configuración. No exijas igualdad fila a fila de muestras independientes ni
   ajustes tolerancias para lograr PASS. Muestras pequeñas de autoría no acreditan
   aceptación. No permitas que la nueva ruta imponga scripts de tiradas exactas
   a escenarios estadísticos que no los necesitan.
8. Ajusta comprobantes existentes y docs/reference/verification.md. No añadas una
   suite por regla. Retira la exigencia de completar G06 para poder comparar
   estadísticamente duelos. Conserva la trazabilidad de límites de sensibilidad.

SUBAGENTES
Usa subagentes si aceleran capacidades independientes. Reparto sugerido:
- uno adapta catálogo/validación y su comprobante;
- otro adapta runner y su comprobante;
- tú integras contrato compartido, CLI, informes y documentación.
Fija primero el contrato mínimo catálogo/runner. Un escritor por archivo; los
subagentes no editan motores, CSV ni documentos compartidos de entrega. No los
lances solo para producir más auditorías. Integra sus cambios en una única pasada
y corrige defectos concretos hasta completar el paquete.

LÍMITES Y VERIFICACIÓN
No modificar motores modular/vectorial/nativo, modelos compartidos, planes del
motor, KB, CSV canónico ni corpus E2E. No implementar instrumentación pendiente,
inyección nueva de estado, cargador E2E, DSL ni planificador. Las sondas actuales
pueden permanecer. No hacer commits ni pushes.
Mantén la restricción vigente: no ejecutar tests, importaciones de validación,
py_compile, compilaciones ni motores. Comprueba por lectura el flujo, selección,
limitaciones y coherencia de comprobantes. Declara lo no ejecutado. No iniciar
P04/P05 ni afirmar paridad.

ENTREGA Y FIN
Actualiza solo TMP_VECTORIAL_ENGINE_2A2B/parity_update/P03-deliverable.md como
entrega del paquete. Resume archivos cambiados/reutilizados, disposición de casos
conservados/pendientes y causas reales, comprobantes escritos no ejecutados y
comandos exactos propuestos para una comprobación pequeña posterior y P04/P05.
Registra defectos concretos pendientes en TODO.md si existen. No conviertas la
instrumentación descartada en backlog obligatorio.
Termina con catálogo → motores reales → comparación estadística → CLI/informe
conectado, con limitaciones reales visibles. No reabras P00 ni encargues sondas.
Conexión escrita no significa ejecución validada ni cobertura exhaustiva.
```

## Campañas posteriores

P04 medirá costes, parámetros y sensibilidad con las APIs actuales y el catálogo adaptado. P05 ejecutará aceptación estadística sobre una versión identificada y con muestras y criterios fijados. Sus prompts se prepararán después de esta entrega y de autorizar ejecución; los prompts instrumentados anteriores quedan sustituidos, no pendientes.
