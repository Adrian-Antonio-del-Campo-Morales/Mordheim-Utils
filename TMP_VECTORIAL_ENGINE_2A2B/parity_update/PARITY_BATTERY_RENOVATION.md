
Renovación de la batería de paridad

## 1. Objetivo y enfoque

Preparar una batería de paridad desde las cláusulas admitidas y el **motor
modular validado como referencia**, con cierre propio independiente del plan
de implementación del vectorial.

**Situación de coordinación:** el plan del motor está terminando G07 con su
batería actual; el rework está ejecutando P01/P02. G07 puede cerrar identificando
la versión, batería y límites de su evidencia, sin esperar a los tests nuevos.
Su cierre no acredita la cobertura ampliada del rework.

**El rework se completa en P03.** P00–P03 definen todos los tests de rápido,
completo y profundo y conectan catálogo, adaptador, comparador, CLI e informes.
No se ejecutan comparaciones contra NumPy/nativo para aceptar esa preparación,
ni se exige que pasen en el candidato. El diseño no sigue el estado del portado:
se obtiene de las cláusulas y del oráculo. La falta de una capacidad del motor
se registra para la futura ejecución; no elimina ni aplaza la definición del test.

**P04 y P05 forman una campaña posterior al cierre del rework.** Con la batería
P03 terminada y una versión fija del motor entregado por G07, P04 mide costes y
calibra parámetros; P05 ejecuta la aceptación con la batería renovada. P05 no es
G07 ni reabre su cierre anterior. Este documento no modifica el plan del motor.

**La cobertura se organizará por comportamientos, no por número de combates ni por número de cláusulas.** Un mismo comportamiento puede aparecer en muchas reglas; ejecutar miles de enfrentamientos equivalentes aporta poco.

Reutilizaremos la infraestructura de paridad, los escenarios existentes y las situaciones ya descritas en los E2E. Solo añadiremos escenarios para huecos concretos. No desarrollaremos nuevas pruebas modulares ni duplicaremos su corpus.

## 2. Construir un catálogo de comportamientos comprobables

Partir del CSV actual, sus consumidores modulares y las referencias a pruebas existentes. Para cada comportamiento, identificar:

- **Activación y ausencia:** cuándo actúa y cuándo debe permanecer inactivo.
- **Variantes relevantes:** límites, excepciones y parámetros que cambian el resultado.
- **Evolución temporal:** consumo, recuperación, duración y reinicio de recursos o estados.
- **Interacciones:** efectos que comparten fase, modifican el mismo estado o alteran el orden de resolución.

Por ejemplo, comprobar un recurso de un solo uso requiere observar su consumo y que no vuelva a utilizarse. La proporción final de victorias puede no revelar ese error.

Las agrupaciones existentes sirven para repartir la revisión, pero no acreditan cobertura por sí mismas. Compartir `consumer` o `effect_id` tampoco demuestra que dos contratos tengan idéntico comportamiento.

Cada escenario declarará qué comportamientos y claves del CSV comprueba. Estas referencias pertenecerán a la definición del escenario; el informe de cobertura se generará a partir de ellas. **Mantendremos un único CSV de progreso, sin nuevas columnas ni otro registro manual.**

## 3. Una batería con tres niveles acumulativos

| Nivel | Contenido | Uso |
|---|---|---|
| **1. Rápido** | Selección pequeña que recorra las principales fases y mecanismos: ataques, defensas, estados, psicología, recursos y avance de rondas. Incluye ejecución con varias simulaciones para detectar errores de máscaras o estado compartido. | Durante el desarrollo y tras cambios pequeños. |
| **2. Completo** | Nivel 1 más los escenarios necesarios para cubrir todos los comportamientos y variantes identificados, con comparaciones enfocadas y enfrentamientos estadísticos representativos. | Al integrar funcionalidades y antes de optimizar. |
| **3. Profundo** | Nivel 2 más interacciones relevantes, posiciones intercambiadas, contextos alternativos, combates largos y horizontes de rondas. Amplía muestras y semillas en los casos que lo justifiquen. | Cierre de versión y cambios importantes del motor. |

**El nivel completo debe aportar amplitud; el profundo, mayor sensibilidad y composición.** No reservaremos una regla entera exclusivamente al nivel profundo.

Los conjuntos actuales se revisarán y reutilizarán. No conservaremos artificialmente las cantidades de 10, 30 y 42 enfrentamientos si dejan de representar el motor actual.

Los tiempos se fijarán **después de medir**, como has elegido. Un límite de tiempo agotado producirá una ejecución incompleta, nunca una aprobación con casos omitidos.

Al cerrar P03 los tres perfiles tienen todos sus escenarios y variantes
requeridos, cláusulas y comportamientos referenciados, entradas, controles,
observables, criterios de comparación y selección desde CLI. Incluyen muestras,
semillas y horizontes iniciales explícitos que P04 podrá calibrar. No puede
quedar autoría de tests para P04/P05. «Perfil preparado» no significa «perfil
ejecutado y aprobado». Sus tamaños dependen de comportamientos y variantes
justificados, sin cuotas de escenarios.

## 4. Comparar lo suficiente sin disparar el coste

Prepararemos dos formas de comparación para su ejecución futura dentro de la misma batería:

**Comparaciones enfocadas.** Aprovechar las situaciones E2E y las reproducciones existentes para observar estados, heridas, recursos y decisiones en puntos relevantes. El adaptador deberá conducir cada motor por su ejecución real. Los casos con preparación de estado u observaciones todavía incompatibles quedarán como huecos explícitos.

No mantendremos manualmente dos grandes colecciones de tiradas. Reutilizaremos los mecanismos existentes de reproducción donde sean compatibles y añadiremos únicamente las adaptaciones necesarias. Una misma semilla no garantiza las mismas tiradas entre motores.

**Comparaciones estadísticas.** Mantener los duelos completos para detectar diferencias de distribución e interacciones. Conservar las tolerancias actuales para los resultados ya comparados; cualquier observable nuevo necesitará un criterio explícito. Comparar estados o recursos cuando sean relevantes para el escenario, además del ganador.

Para ahorrar ejecución:

- Compilar una vez las entradas reutilizadas.
- Compartir la muestra modular entre candidatos, como ya permite la infraestructura.
- Reutilizar resultados modulares guardados únicamente cuando coincidan entradas, configuración, semillas y versión del oráculo.
- Ejecutar horizontes adicionales donde puedan descubrir errores de duración u orden.
- Evitar productos cartesianos de todas las reglas.
- Usar casos dirigidos para sucesos raros; aumentar muestras indiscriminadamente puede seguir sin detectarlos.

La igualdad estadística de victorias no bastará para acreditar un comportamiento que nunca se ha observado actuar.

Ahora se define cómo distinguir cada comportamiento: entradas que contienen la
regla, disparador, ausencia, observable y criterio de comparación. Puede usarse
el oráculo para preparar una referencia cuando sea necesario; no se reconstruye
su validación. Una capacidad del candidato todavía no disponible se declara con
su contrato mínimo y propietario, sin emularla ni sustituir la situación por un
duelo que omita la regla. La falta de esa capacidad no impide aceptar el test
preparado; una entrada o un comparador incorrectos sí son defectos de preparación.

La infraestructura se comprueba con carga, selección, referencias, conexión de
interfaces y las comprobaciones mínimas del adaptador/comparador. Datos
sintéticos pueden comprobar sus ramas de informe o error, pero no son evidencia
de combate ni sustituyen un motor. No se ejecuta el candidato para buscar fallos
ni se requieren resultados suyos para cerrar la preparación.

## 5. Dos cierres independientes y una campaña posterior

| Trabajo | Secuencia | Cierre |
| --- | --- | --- |
| Plan del motor, referencia externa | G07 termina con su batería actual | Evidencia acotada a la revisión y batería que realmente ejecutó; no espera al rework. |
| Rework de tests | P00 → (P01 + P02 en paralelo) → P03 | Todos los tests y niveles definidos, preparados y conectados, sin resultados del candidato. |
| Campaña con la batería renovada | P03 terminado + versión fija del motor entregado por G07 → P04 → P05 | Medición/calibración y aceptación frente al modular con la nueva cobertura. |

P03 se acepta por autoría completa, trazabilidad, corrección del adaptador y
comparador, selección acumulativa y conexión de las herramientas. Si faltan
tests, variantes o criterios requeridos, el rework sigue abierto. Las carencias
externas de entrada, consumo o publicación del motor se especifican con sus
casos afectados y se gestionan al ejecutar; no son autoría aplazada.

P04 solo ajusta muestras, semillas, horizontes y parámetros de ejecución por el
coste y sensibilidad medidos, conservando todas las obligaciones y escenarios
base. No se utiliza para crear reglas o familias de tests faltantes. Si descubre
un defecto de preparación, devuelve la corrección a P01/P02/P03 y registra su
impacto, sin certificar una campaña incompleta. P05 distingue igualmente defectos
del test, del adaptador y del motor, sin cambiar expectativas para conseguir PASS.

La preparación será propietaria de los escenarios y herramientas de paridad.
Cualquier necesidad del motor se comunica a su propietario, sin editarlo ni
cambiar sus planes. P01/P02 no tienen que perseguir la evolución de G07.

El informe de preparación distinguirá obligaciones con test preparado, trabajo
propio pendiente y dependencias del motor, además de referencias modulares
realmente obtenidas. El informe futuro de ejecución mostrará comportamientos
declarados, ejecutados, activados, comparados, pendientes, incompatibles y
divergentes; muestras, tiempos por motor y revisión utilizada. Un resultado de
ejecución `complete=False` no es el estado de entrega de la preparación. El
coordinador no actualizará `status.numpy` ni `status.native` por preparar tests.

El objetivo será **cubrir todos los comportamientos inventariados y sus interacciones seleccionadas**. No afirmaremos que una batería finita cubre todas las combinaciones posibles. Tampoco confundiremos una etiqueta de cobertura con una ejecución que realmente distingue el comportamiento.
