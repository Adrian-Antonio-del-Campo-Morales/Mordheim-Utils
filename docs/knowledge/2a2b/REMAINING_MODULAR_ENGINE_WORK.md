# Terminar la implementación modular desde el CSV

## 1. Estado real y objetivo

Base inspeccionada: rama `2A2B`, checkpoint `cee529cd`. Durante el análisis han aparecido cambios del bloque de mutaciones/equipo; deben incorporarse antes de continuar, conservando su propietario actual.

El CSV mantiene **4.556 cláusulas y 3.594 orígenes**:

| Trabajo registrado | Cláusulas pendientes |
|---|---:|
| Evaluación del estado real | 205 |
| Datos | 177 |
| Conexiones | 130 |
| Proyección de hechos al motor | 55 |
| Comportamiento | 7 |
| **Total** | **574** |

De esas 574, **566 están admitidas**, siete siguen sin clasificar y una figura como posterior. No representan 574 funcionalidades nuevas: hay conexiones ya implementadas y estados desactualizados. Tampoco las 3.982 filas con trabajo `none` certifican por sí solas funcionamiento completo.

Dos problemas concretos amplían el trabajo respecto al resumen anterior:

- De los 130 perfiles de mercenarios/personajes expuestos, **72 presentan intrínsecas pendientes según el criterio de admisión**. Incluyen consecuencias ejecutables y reglas externas al duelo. Resolver sólo tres personajes dejaría el problema general abierto.
- La batería E2E falla al colectar por una referencia obsoleta a `_lookup`. Hay que reparar esa conexión para utilizar la batería existente.

**Objetivo de salida:** ninguna consecuencia admitida pendiente de implementación, conexión, configuración o corrección conocida. Las exclusiones deben estar justificadas por su contenido, sin utilizarlas para ocultar funcionalidades incompletas.

## 2. Ejecución en cuatro bloques completos

### Bloque 1 — Estado, equipo y consumidores del combate

Incorporar y completar el trabajo de mutaciones/equipo actualmente en curso. Resolver en este mismo bloque los defectos conocidos de los consumidores compartidos:

- Procedencia física de equipo, manos, miembros y ataques; ejemplares distintos; venenos, materiales y runas.
- Retirada de bonos e identidades al perder equipo, incluidos bonos de W, armadura metálica y ataques adicionales.
- Persistencia entre rondas y composición con transformación, ruptura y desarme.
- Correcciones pendientes de contacto, cargas, miedo, identidades, inmunidades y Crude Belch.
- Consumo y caducidad de recursos y preparaciones; orden y excepciones de salvaciones.
- Ambigüedades pendientes de Djinn, Lunatics, Alchemist y Scryer, aplicando la autorización de criterio del implementador.

Reconciliar aquí las filas correspondientes del CSV, sin volver a implementar comportamientos existentes. Entre las siete filas `behavior`, comprobar y cerrar en su consumidor Crimson Shade, Magic Acorn, Slaanesh y Barrage. Las dos cláusulas de Aquatic Mutants pertenecen al bloque 3; Haunted Mien, al bloque 2.

Reparar al comienzo la conexión de lectura de observaciones del harness E2E, reutilizando la función existente en `corpus.py`, sin crear otro adaptador.

**Resultado tangible:** las consecuencias de combate funcionan y se componen correctamente durante sucesivas rondas. No quedan defectos conocidos de esta familia pospuestos para una futura integración.

### Bloque 2 — Admisión canónica completa de mercenarios y personajes

Revisar los perfiles con intrínsecas pendientes como un conjunto, agrupando reglas equivalentes y sus variantes:

- Separar manualmente cada consecuencia admitida de campaña, disparo, casting, monturas y otros productores excluidos.
- Corregir clasificaciones que bloquean un perfil por reglas exclusivamente externas. Mantener el rechazo cuando realmente falte una consecuencia intrínseca admitida.
- Conectar inmunidades, Fear, Hatred, Frenzy, características, habilidades y recursos mediante operadores existentes.
- Completar equipos fijos, opciones, objetos únicos, personajes con variantes y restricciones particulares.
- Terminar Marianna, Sigmund y Bone Goliath dentro de este cierre general, aprovechando sus pruebas positivas existentes.
- Cerrar las proyecciones y referencias pendientes de Aenur, enanos, Morr, patrones del Emisario y restantes perfiles afectados.

No retirar la protección de admisión ni sustituirla por una lista permisiva. Un perfil estará disponible cuando todas sus consecuencias admitidas estén resueltas; una exclusión parcial no cerrará una regla compuesta.

**Resultado tangible:** cada perfil individual admitido puede seleccionarse, compilarse y ejecutar sus reglas particulares con un equipo legal. Los perfiles realmente excluidos conservan un diagnóstico preciso.

### Bloque 3 — Construcción compartida y resto del CSV

Completar todas las filas pendientes que no hayan quedado resueltas en los bloques anteriores, agrupadas por sus consumidores reales:

- Destinatarios y pertenencia a listas, incluidos los catálogos de comercio.
- Concesiones automáticas y seleccionables, tablas de habilidades e herencias.
- Características y estados suministrados; acceso y opciones de Aquatic Mutants.
- Restricciones de equipo, manos y capacidades de constructos; kits y equivalencias.
- Transporte de hechos desde configuración hasta compilación y consumo modular.

Las 205 evaluaciones se resuelven leyendo su contrato y comprobando la ruta existente. Si ya funciona, se reutiliza la evidencia pertinente y se corrige el registro. Si falta una conexión, se implementa en ese momento. **No habrá una fase de evaluación que entregue otra lista para implementar después.**

Consultar los helpers históricos sólo como candidatos. No ejecutarlos completos: algunos contienen estados anteriores que harían retroceder filas ya resueltas.

**Resultado tangible:** las 574 filas iniciales tienen disposición actual y justificada; ninguna consecuencia admitida queda pendiente por falta de datos, conexión, configuración o evaluación.

### Bloque 4 — Validación integrada y corrección final agrupada

Con los tres bloques anteriores integrados:

1. Ejecutar conjuntamente modular, construcción, semánticos modulares y E2E existentes.
2. Incluir comprobaciones de tipos, bundle, contratos y conservación del CSV pertinentes.
3. Agrupar los fallos por causa y consumidor. Corregir cada causa común de una vez.
4. Reejecutar sólo los grupos afectados por esas correcciones.
5. Ejecutar una confirmación integrada final sobre el estado que se entrega.

Los fallos anteriores al último parche también cuentan si impiden el objetivo. No se descartarán como «ajenos» ni se convertirán positivos en rechazos.

**Resultado tangible:** implementación integrada funcional, con resultados reproducibles y sin fallos admitidos conocidos pendientes.

## 3. Reglas para evitar otra cadena de tareas pequeñas

- **Un responsable de implementación e integración**, con un solo escritor en archivos compartidos. La entrega actual de mutaciones se incorpora antes de modificar sus consumidores.
- Se continúa de un bloque al siguiente sin esperar una nueva autorización para cada fallo, archivo o familia independiente.
- Cada bloque incluye código, datos, configuración necesaria y actualización del CSV. No se entrega un consumidor aislado cuya conexión quede para otro encargo.
- El CSV es la única cola mantenida. Se usan sus claves y campos existentes; no se crean inventarios paralelos, subplanes ni informes de desarrollo.
- No se reauditan las 4.556 cláusulas. Se recorren las 574 pendientes y las filas afectadas por defectos concretos o dependencias compartidas.
- Cada contrato se interpreta una vez por familia, comprobando manualmente las diferencias de sus orígenes. Los scripts sólo navegan, aplican decisiones explícitas y validan conservación.
- Las ambigüedades se resuelven con criterio del implementador: respetar decisiones adoptadas, preferir la cláusula específica y limitar la interpretación a las consecuencias admitidas. Registrar brevemente la decisión cuando sea necesaria. **La ausencia real de una regla no autoriza inventarla.**
- No repetir búsquedas de fuentes ya recuperadas ni comprobaciones verdes sin cambios relevantes.
- Al integrar CSV: recarga completa, conservación de claves/textos/huellas/notas, validación del candidato y rechazo de cambios concurrentes.

La documentación se limita al CSV, una actualización breve del progreso existente y decisiones normativas imprescindibles. Sin nuevos informes, certificados, volcados extensos ni documentos por entrega.

## 4. Pruebas mínimas y condición de terminado

Durante cada bloque se reutilizan los casos existentes del contrato modificado. Sólo se añaden pruebas cuando falta un discriminador de comportamiento, límites, consumo, caducidad o composición. No se duplican automáticamente casos entre Python, semánticos y E2E.

Una conexión reutiliza las pruebas del operador; sólo necesita demostrar acceso canónico y destinatario correcto. Las baterías completas se reservan para el bloque 4. No habrá campañas de cobertura, parity, estadísticas ni implementación vectorial/nativa.

El progreso se comunicará por **capacidades utilizables y familias cerradas**, distinguiendo implementación nueva de reconciliación documental. El número de pruebas verdes no será la medida del avance.

Se declarará terminado cuando:

- Todas las cláusulas admitidas tengan configuración accesible, compilación y consumo correcto.
- No queden pendientes ejecutables ni defectos conocidos de composición.
- Las siete filas sin clasificar y la fila posterior tengan disposición explícita.
- Pasen las comprobaciones integradas aplicables.
- El CSV conserve sus 4.556 claves y su trazabilidad.

No se requiere completar la autoría de todo el corpus E2E ni certificar T14. `cases/grants` conserva su propietario externo. Si aparece una fuente realmente ausente que impida implementar una consecuencia admitida, se identificará exactamente y no se afirmará que el motor está completo.

Este plan no realiza nuevas modificaciones, commits ni pushes.
