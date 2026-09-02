# Interfaz activa

Presentación Tkinter del simulador. Conserva la navegación Candidate, Enemy, Improvements, Weapons, Equipment y House Rules.

La UI posee ventanas, widgets, coordinación de threads y adaptación de resultados. No debe contener reglas, validación de construcciones ni bucles de simulación:

- `application.catalogue` prepara opciones de la KB.
- `application.analyses` ejecuta comparaciones sin Tkinter.
- `persistence` guarda preferencias y workbooks versionados.
- `construction` compila configuraciones y `combat.vectorized` las simula.

El workbook mantiene IDs estables en una hoja oculta y resúmenes legibles en las hojas visibles. Su contrato y ubicación de preferencias se conservan durante esta reorganización.

Véase [Modificar la aplicación](../../../docs/tasks/modify-application.md).
