# Terminar la implementación modular desde el CSV

**Estado 2026-10-18:** integradas las últimas nueve filas de H03b; el CSV conserva
4.556 claves y devuelve cero pendientes. La cola de cláusulas está cerrada.
Permanece el bloque 4: los encargos acotados de contratos del catálogo y
admisión/kits ya están integrados; falta ejecutar las comprobaciones
integradas aplicables y resolver los fallos admitidos
que impidan la entrega. No se declara terminado ni certificado el motor por este
recuento; E2E y T14 siguen excluidos.

Asignación a agentes: consultar [los paquetes por consumidor](MODULAR_ENGINE_WORK_PACKAGES.md),
con selección de cláusulas, resultados y reservas de archivos. El CSV sigue siendo
la única cola de estado; los conteos de ese documento son una fotografía de asignación.
Cada encargo externo entrega únicamente su resumen breve
`deliveries/IDTAREA-completed.md`, conforme al contrato de los paquetes; se permite
este documento de finalización, sin planes ni informes de desarrollo adicionales.

Los agentes externos reciben bloques completos nuevos. El coordinador resuelve
los remates pequeños de las entregas; sólo devuelve un bloque previo al ejecutor
si todavía requiere implementación sustancial.

## 0. REGLAS OBLIGATORIAS: IMPLEMENTAR, NO PROLONGAR LA PREPARACIÓN

**La actividad principal es implementar capacidades pendientes. Investigación,
clasificación, pruebas y documentación son apoyo; no sustituyen la implementación.
Estas reglas gobiernan los bloques 1–3 y todos sus encargos delegados. El bloque 4
mantiene la validación integrada final. No requieren nuevas autorizaciones.**

1. **Comprobar pronto si existe trabajo real.** Lee el contrato y localiza la ruta
   relevante; reutiliza evidencia vigente y, sólo si hace falta, un discriminador.
   Si ya funciona, reconcilia brevemente la fila y pasa inmediatamente a la siguiente
   capacidad pendiente. No busques cambios artificiales ni añadas pruebas para
   justificar una entrega. Si un paquete delegado ya está resuelto, comunícalo sin
   prolongarlo; el coordinador reasigna trabajo con un defecto concreto.
2. **Investigar para decidir y editar.** Antes de ampliar una búsqueda, identifica
   el dato desconocido que impide la siguiente edición. Comprueba el dato con una
   lectura o prueba pequeña antes de desarrollar hipótesis extensas. Reutiliza los
   resultados de búsquedas y delegaciones; no repitas la exploración del delegado.
   Una compactación o reanudación no reinicia la auditoría: retoma el siguiente
   cambio concreto con el contexto conservado.
   **Prioriza la KB y las decisiones del repositorio.** No consultar web ni PDF
   para reconfirmar información suficiente. Usarlos sólo cuando falte un dato
   imprescindible para implementar o haya una contradicción concreta no resuelta;
   identificar ese dato y consultar únicamente el pasaje necesario. No inventar
   una regla para evitar una consulta imprescindible. Repetir este límite en prompts.
3. **Pruebas con alcance explícito.** Empieza por los casos del contrato cambiado,
   mediante selectores o, como límite inicial, tres archivos directamente afectados.
   Amplía sólo ante un fallo nuevo o un riesgo concreto de un consumidor compartido
   no cubierto; indica brevemente qué riesgo y qué casos adicionales lo comprueban.
   No basta llamarlos «focales» o «familia»: queda prohibido acumular directorios o
   decenas de archivos por precaución durante los bloques 1–3.
4. **No repetir ejecuciones sin causa nueva.** Tras un resultado suficiente, vuelve
   a implementar. Reejecuta sólo después de cambiar código/datos relevantes, corregir
   un fallo o detectar evidencia inválida. Guarda la salida útil de la primera
   ejecución; no repitas una batería para recuperar nombres, contar fallos, normalizar
   su salida o producir una afirmación más vistosa de ausencia de regresiones.
5. **Los fallos se atienden por causa.** Lee el primer fallo representativo y corrige
   la causa abordable dentro del encargo. Un fallo heredado no se descarta por su edad.
   Si es necesario distinguir una regresión, compara sólo el caso discriminante con
   una base coherente. No ejecutes baterías completas otra vez en HEAD, ni crees un
   worktree únicamente para demostrar que todos los fallos ya existían.
6. **Sin bucles alrededor de cambios concurrentes.** Identifica una vez el archivo
   en vuelo y su propietario. No lo modifiques ni repitas sondeos esperando que se
   estabilice. Continúa con implementación independiente y deja la integración al
   coordinador. Excluir archivos de una copia de verificación no acredita el estado
   integrado; no construyas infraestructura alternativa para evitar ese bloqueo.
7. **Aislamiento preparado antes de editar.** Cuando se autorice una copia aislada,
   conserva al inicio su base exacta, incluidos los cambios locales heredados, fuera
   del árbol entregable. Genera después el diff base→final de los archivos propios.
   No reconstruyas retrospectivamente esa base desde el checkout original cambiante,
   no mezcles cambios heredados y no dediques ciclos a fabricar/verificar parches.
   Si falta la base, el coordinador integra el diff disponible con esa limitación.
8. **Criterio de avance y de parada.** Comunica capacidades concretas antes→después,
   no números de pruebas, etiquetas cerradas o perfiles sin marcadores pendientes.
   Una entrega sólo de pruebas, inventario o diagnóstico no cierra un bloque mientras
   queden correcciones abordables. No inventes modificaciones para aparentar avance:
   reconoce lo ya implementado y continúa. Detente sólo por el límite explícito del
   encargo, su finalización real o un bloqueo que impida todo trabajo independiente.

**Incumplir estas reglas es una desviación del encargo, aunque las pruebas pasen.**
El coordinador debe corregir el rumbo sin crear otro plan ni otra ronda de auditoría.
Los prompts deben incluir esta prioridad y los límites de pruebas, repetición,
concurrencia y entrega; no basta con enlazar este documento. Se preservan las
comprobaciones de conservación/concurrencia del CSV y los contratos obligatorios.
No se debilitan pruebas, reglas de admisión ni expectativas para ahorrar trabajo.

### Límites operativos y contenido obligatorio de los prompts

**E2E COMPLETAMENTE FUERA DEL ENCARGO, TAMBIÉN EN EL BLOQUE 4.** Por orden
expresa del usuario, no ejecutar, colectar, investigar, reparar ni modificar tests,
harness o corpus E2E. No usar sus fallos como bloqueos ni sus resultados como
condición de terminado. Esta orden prevalece sobre referencias históricas a E2E.
No lanzar un comando global que los incluya indirectamente.

- **Antes de cada ejecución:** identificar el cambio que se comprueba y seleccionar
  los casos mínimos. El límite de tres archivos no autoriza ejecutar archivos
  parametrizados con cientos de casos ajenos. Si el consumidor está cubierto y no
  cambió, continuar implementando; «por seguridad» no justifica otra ejecución.
- **Salida conservada una sola vez:** guardar la salida necesaria fuera del árbol
  entregable. Contar o filtrar esa salida, nunca relanzar pruebas para obtenerla.
  Una reanudación conserva resultados válidos. Si se inicia por error una batería
  prohibida, cancelar ese proceso propio; no esperar su final ni investigar sus fallos.
- **Prohibido convertir implementación en auditoría:** no regenerar inventarios
  globales ni recuentos sucesivos. Consultar las cláusulas siguientes y editar su
  consumidor real. Una conexión requiere comprobar destinatario y acceso; eliminar
  un marcador pendiente no prueba que la consecuencia funcione. No cerrar filas en
  masa a partir de `implemented`, `scope` o presencia de binding.
- **CSV: sin copia previa, no escribir.** Sólo su escritor autorizado puede integrar.
  Conservar los bytes actuales completos fuera del repositorio antes de cada
  integración; acceder por nombres de columna y clave `(id, clause_id)`, nunca por
  índices numéricos o sólo `id`. Validar el candidato antes de escribir: mismas 4.556
  claves, textos y huellas; notas válidas conservadas; celdas ajenas a las decisiones
  explícitas idénticas. Releer y verificar que el original no cambió antes de sustituirlo.
  Ante una discrepancia, no publicar el candidato. Si ya hubo daño, suspender las
  escrituras al CSV y avisar; no reconstruirlo con HEAD, exportaciones antiguas ni
  conjeturas. Continuar código independiente si es posible.
- **Fallos sin atribuciones inventadas:** no llamar «preexistente» a un fallo porque
  nombre otro archivo o haya muchos fallos. Sin prueba suficiente, indicar «origen
  no determinado» una vez y continuar trabajo independiente; no abrir otra auditoría.

Cada prompt de implementación debe incluir explícitamente, además de la capacidad
asignada y los archivos reservados, este contrato breve (no sólo un enlace):

> IMPLEMENTAR ES EL TRABAJO PRINCIPAL. Termina la capacidad asignada de configuración
> a consumo modular; reutiliza lo existente sin inventar cambios. Investiga sólo el
> dato que bloquea la siguiente edición y continúa con capacidades incompletas.
> E2E excluidos por completo: no ejecutar, colectar, investigar ni modificar, tampoco
> para el cierre. Usa casos mínimos afectados; inicialmente como máximo tres archivos
> directamente relacionados, sin baterías amplias ocultas en un archivo parametrizado.
> Conserva la primera salida; no repitas sin cambios relevantes ni para contar fallos.
> No rehagas inventarios ni auditorías globales. CSV sólo con propiedad autorizada,
> copia completa previa, claves `(id, clause_id)`, conservación y control concurrente;
> de lo contrario entrega las decisiones concretas sin escribirlo. Ante daño al CSV,
> suspende sus escrituras y avisa: no recuperes desde HEAD. Preserva trabajo concurrente,
> expectativas y controles de admisión; sin vectorial/nativo, commits ni pushes.
> Puedes usar subagentes y se recomienda hacerlo cuando acelere la implementación:
> asigna capacidades y archivos disjuntos, conserva un escritor por archivo y un
> responsable de integración. Transmite estos límites y reutiliza su evidencia;
> no dupliques investigaciones/tests ni generes informes separados o escrituras CSV.
> Entrega capacidades antes→después, comprobación mínima y bloqueos concretos;
> distingue implementación de reconciliación. Sigue hasta acabar el alcance asignado.

### Herramienta obligatoria del CSV: consultar → preparar → validar/aplicar

Usar `python -X utf8 tools/knowledge/t13_csv.py` desde la raíz del repositorio.
**No editar directamente el CSV ni crear scripts alternativos de reescritura.**
Cualquier agente puede consultar y preparar propuestas; sólo el propietario autorizado
puede aplicar. La herramienta no decide semántica ni acredita implementación.

1. **Consultar** cláusulas acotadas (salida JSON, diez resultados por defecto):

   ```powershell
   python -X utf8 tools/knowledge/t13_csv.py query --pending --consumer contexts.py --limit 5
   python -X utf8 tools/knowledge/t13_csv.py query --id "ID_EXACTO" --clause-id "CLAUSULA"
   ```

   Filtros combinables: `--id` y `--clause-id` exactos; `--source` y `--consumer`
   por fragmento; `--work`, `--review`, `--pending`; `--fields` selecciona columnas
   separadas por comas. No regenerar inventarios globales para empezar cada familia.

2. **Preparar cambios explícitos**, sin tocar el CSV. Guardar las propuestas y el
   paquete fuera del repositorio, por ejemplo en `$env:TEMP`. El archivo de propuestas
   es una lista JSON de claves y cambios; `set` recibe objetos/listas JSON reales en
   los campos estructurados y cadenas en los demás. Ejemplo de forma, no una decisión
   semántica aplicable automáticamente:

   ```json
   [{"id":"ID_EXACTO","clause_id":"CLAUSULA",
     "set":{"pending":{},"verification":["executed","ruta::caso_existente"]},
     "append_notes":"Consecuencia implementada y evidencia concreta."}]
   ```

   ```powershell
   python -X utf8 tools/knowledge/t13_csv.py prepare "$env:TEMP/t13-changes.json" --out "$env:TEMP/t13-prepared.json"
   ```

   El paquete conserva la huella del CSV y los valores completos anteriores y
   propuestos; la salida muestra sólo las diferencias. No modificar el paquete
   para eludir rechazos: corregir la propuesta y preparar otro archivo de salida.

3. **Validar y aplicar**. Sin `--write` sólo valida y muestra las diferencias:

   ```powershell
   python -X utf8 tools/knowledge/t13_csv.py apply "$env:TEMP/t13-prepared.json"
   # Sólo el escritor autorizado, después de revisar las diferencias:
   python -X utf8 tools/knowledge/t13_csv.py apply "$env:TEMP/t13-prepared.json" --write
   ```

   Antes de sustituir el registro, valida esquema y tipos con el validador existente,
   conserva las 4.556 claves `(id, clause_id)`, bloquea cambios de fuente/texto/huella,
   admite sólo añadir notas y comprueba todas las celdas no modificadas. Conserva
   literalmente los registros ajenos y los finales de línea originales, incluidos
   CRLF de Windows. Crea una copia completa en el directorio temporal del sistema
   e imprime su ruta; conservar esa copia hasta aceptar la integración.

   Usa un bloqueo exclusivo entre escritores de esta herramienta y vuelve a
   comprobar los bytes justo antes de sustituir el archivo. **Todo escritor debe
   usarla:** el bloqueo no controla editores o scripts externos. Si cambió cualquier
   byte desde la preparación, rechaza el paquete: recargar y revisar las decisiones
   contra el estado nuevo, sin forzar ni recuperar desde HEAD. Un `.csv.lock`
   existente bloquea la escritura; no borrarlo mientras pueda pertenecer a otro
   escritor. La herramienta valida conservación respecto al estado leído; no repara
   ni certifica posibles daños anteriores.

En cada prompt, indicar: **«CSV sólo mediante `tools/knowledge/t13_csv.py`:
`query`, `prepare` y `apply`; únicamente el propietario aplica con `--write`»**.
Las pruebas de la herramienta son `python -X utf8 tools/knowledge/test_t13_csv.py`;
usan CSV sintéticos temporales y no modifican el registro real. No repetirlas al
implementar reglas si la herramienta no ha cambiado.

### Progreso de integración — 2026-10-14

All-seeing Eye of Numas integrado (2026-10-15): artefacto fisico suministrado y
seleccionable, salvacion de 6+ mediante el consumidor existente tras armadura,
sin modificacion por Fuerza ni modificadores de armas. La composicion mantiene
las prohibiciones existentes; vision, Exploracion y disparo quedan excluidos.
Clausula compartida cerrada, 4.556 claves conservadas. Se reutiliza la evidencia
entregada (dos pruebas nuevas, tres casos); sin reejecutar baterias ni ampliar
el encargo a auditorias estructurales o formato global.

Marquand integrado (2026-10-15): participante individual canonico con perfil,
equipo legal, Step Aside y Lightning Reflexes; Knife Fighter queda separado por
su contenido de disparo. La pareja y la referencia de Ulli permanecen intactas,
sin nueva contratacion individual. Propuesta integrada contra el CSV actual con
4.556 claves conservadas; evidencia recibida: cuatro casos focales y el censo
afectado. No se repiten baterias ni se abre otra familia de hirelings.

Violent Entry integrado (2026-10-15): hecho suministrado de invocacion en el turno
actual mas carga concede +1 al impacto y +1 Fuerza al Malignant Spirit; sin hecho,
sin carga o en turno posterior no hay bonos. Se reutiliza la evidencia focal de
la entrega (7 casos); propuesta rehecha contra el CSV actual e integrada con
conservacion de las 4.556 claves. No se implementa invocacion ni ports optimizados.

Penthesilea cerrada (2026-10-15): decision humana Weapon Master = Weapons Training,
implementada como acceso a armas cuerpo a cuerpo con ejemplares suministrados y
sin bonos adicionales. Admision canonica, Marca 5/5, Danza/Furia, Odio contra
varones humanos y configuracion Star Sword + Star Blade comprobados. Se rechazan
armas a distancia, copias inexistentes, ataques innatos como equipo y objetos
unicos ajenos. Quince casos focales superados; tipos y bundle de elegibilidad
validos. Ultima clausula pendiente cerrada; sin E2E ni certificacion global.

Discapacidad completada (2026-10-15): se suministra exactamente un resultado
permanente 1–6; el duelo ya no sortea creación de grupo. Estadísticas aplicadas
una vez, Parkinson conectado al validador compartido de equipo y Lesión Craneal
con exención actual por Héroe activo aliado dentro de 6 pulgadas. Límites 6/6,01,
bando y Fuera de combate comprobados. Dos pendientes cerrados y cuatro evidencias
previas corregidas; 17 casos focales, sin batería global ni parity.

Ye Give Way completado (2026-10-15): resultados previos suministrados de rechazo
y victoria accesibles por condition_ids, con destinatario, persistencia y no
acumulación. Efectos reales -1 al impacto del Héroe que rechazó; +1 al impacto
y F del Noble victorioso. No se simula el desafío que interrumpiría el duelo.
Un pendiente cerrado; siete discriminadores focales, sin ampliar baterías.

Abdul / Eye Pendant completado (2026-10-15): el No Muerto atacante debe superar
Liderazgo cada turno de combate; fallar impide sus ataques ese turno incluso con
inmunidad a Psicología. Guarda de 4+ y restricción pertenecen al objeto equipado,
y desaparecen al retirarlo. Corregido el contrato anterior, que invertía el
destinatario e inventaba el uso exclusivo del Liderazgo propio. Seis discriminadores
focales; fila antes cerrada incorrectamente, sin contabilizarla como nuevo pendiente.

Drenok completado (2026-10-15): Icefang y la piel tienen efectos propios ligados
al equipo real; perfil canónico admitido. La fuente primaria mostró que su
Berserker se había confundido con la habilidad de carga de los Matatrolles:
ahora combate a cero Heridas con 4+, sin curarse, y renueva cada turno hasta fallar.
Parada, +1 a heridas, armadura melee antes de Step Aside y ausencia del bono de
carga erróneo comprobados. Dos conexiones cerradas y una falsa equivalencia corregida;
la salvación de disparos sigue excluida. CSV conservado e integrado con copia previa.

Marks of Morr completado (2026-10-15): Haunted Mien libera el kit y la armadura
en la elegibilidad compartida, conserva cantidades y protege equipo exclusivo;
proyección/oferta y compilación coinciden. Augur mantiene -1 S e inmunidad efectiva,
y reutiliza un único recurso de repetición personal. Se conserva la exclusión mutua
de Marcas y los preceptos de los sacerdotes sin Haunted Mien. Cuatro pendientes
cerrados (tres conexiones/datos existentes reconciliados y el consumidor de equipo
completado); pruebas focales, tipos y bundle de elegibilidad actuales.

Familia TC14 Whip completada (2026-10-15): Whip Master y Snake Fear conectados
canónicamente en Heinrich, y Whip Master en Mule Skinner (tres cláusulas cerradas).
Incluye el arma completa para melee, elección de repetición sin tercera tirada,
desarme declarado y parada de retención, arma física de repuesto y réplica ya
actualizada en la misma ronda; conserva el placeholder de Trollheim sin equipararlo.
Miedo usa identidad explícita de serpiente y los consumidores ordinarios de carga.

Mantenimiento y pociones suministrados completados (2026-10-15): condiciones
canónicas, destinatarios, una elección por tabla, bonos ligados a piezas físicas,
pérdida de equipo y composición con runas/paradas; la Bruja reutiliza los operadores
de Petru para caducidad propia y Herida no recuperable. Sus dos filas ya no están
pendientes. Djinn’s Curse resuelve salvaciones expresamente inmodificables sin
rechazar el duelo; mantiene sus caras y distingue la Guarda ordinaria de Luck.
Pruebas seleccionadas de ataques, pool, recursos y composición; sin E2E ni ports.

Corrección integrada de kits (2026-10-15): arma omitida representada por `None`,
resuelta antes del matcher en el orden impreso y sólo entre armas de mano principal;
una daga explícita incompatible se rechaza, sin sustituirla por el arma del kit.
Nueve casos seleccionados pasan (defaults, elección explícita, Crow Master y ataques
innatos). Las propuestas de cerrar Potions de la Bruja y Maintenance del Armero se
corrigieron: se excluyen sus productores externos, pero sus consecuencias suministradas
durante el duelo siguen admitidas y pendientes. CSV integrado mediante la herramienta,
con copia previa y sólo dos notas añadidas; no se vaciaron esos pendientes.


Integrados P01–P03 (variantes Druchii y parada de hacha enana+espada), D13 sólo
modular, y las pruebas/reconciliación de Aquatic Mutants. Scryer completado:
conexiones auxiliares de combate y composición sin repetir repeticiones; se
mantienen las exclusiones de preparaciones, precarga y eventos ajenos al combate.
El catálogo Python carga sin excluir archivos Druchii. Los focales ejecutados
pasan sobre el checkout compartido; la generación web sigue bloqueada por etiquetas
traducidas incompatibles. Ese pendiente concreto está en
`REMAINING_MODULAR_ENGINE_PROBLEMS.md`. CSV conservado en 4.556 filas.
Morr integrado: inmunidad condicionada frente a vampiros, nigromantes vivos y
no muertos; perfiles e identidad canónica conectados y fila `fear-immunity` cerrada
con comprobación focal sobre el checkout principal. Sin ampliar la inmunidad a
todos los hechiceros ni a otras pruebas de Psicología.


## 1. Estado real y objetivo

Los recuentos y bloqueos de esta sección son la instantánea inicial del plan,
no una orden de volver a verificarlos ni afirmaciones del estado actual.

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
- El bloqueo histórico del harness E2E queda fuera del encargo por orden del usuario; no se investiga ni condiciona el cierre modular.

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

El harness E2E queda excluido; no repararlo ni comprobarlo dentro de este bloque.

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

Encargo acotado previo a la ejecución conjunta: reparar los errores de contrato
editorial ya señalados en las entregas (catálogos de equipo/mecánicas y reglas
de Banshee/Wolves), sin ejecutar todavía las baterías integradas ni modificar
cláusulas reservadas a otros agentes. Entrega única:
`deliveries/B04-catalogue-contracts-completed.md`. No amplía la cola semántica.

**Encargo de contratos integrado 2026-10-18:** corregidos Eye Pendant, vocabulario
true_grit, metadatos close-combat y pertenencia de runtime Wolves/Wulfen; Banshee
ya estaba resuelto. Validaciones documentales y focales del ejecutor reutilizadas.
La expectativa de veneno de Wulfen/Zombies pertenece al remate de admisión/kits;
el formato previo y cualquier fallo de la comprobación conjunta siguen pendientes
de evaluar en su gate correspondiente. No se declara completo todo el bloque 4.

Segundo encargo acotado de este bloque: resolver los fallos conocidos de admisión
y kits de Drenok, Zombies y Buccaneer, preservando sus contratos de prueba y las
distinciones canónicas de equipo. Sólo casos afectados; sin ejecución conjunta
anticipada ni cambios al CSV. Entrega única:
`deliveries/B04-admission-kits-completed.md`.

**Remate de admisión/kits integrado 2026-10-18:** expectativas Drenok, veneno sin
arma en los siete perfiles weapons-armour y arma canónica Buccaneer corregidas
sin cambios de producción, datos o CSV. Resultados focales del ejecutor
reutilizados; controles negativo de equivalencia y venenos legales conservados.
Queda la comprobación conjunta y confirmación final, sin E2E.

Con los tres bloques anteriores integrados:

1. Ejecutar conjuntamente modular, construcción y semánticos modulares existentes, con selección que excluya completamente E2E.
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

Durante cada bloque se reutilizan los casos existentes del contrato modificado. Sólo se añaden pruebas cuando falta un discriminador de comportamiento, límites, consumo, caducidad o composición. No se duplican automáticamente casos entre Python y semánticos. E2E no se ejecuta ni se modifica.

Una conexión reutiliza las pruebas del operador; sólo necesita demostrar acceso canónico y destinatario correcto. Las baterías completas se reservan para el bloque 4. No habrá campañas de cobertura, parity, estadísticas ni implementación vectorial/nativa.

El progreso se comunicará por **capacidades utilizables y familias cerradas**, distinguiendo implementación nueva de reconciliación documental. El número de pruebas verdes no será la medida del avance.

Se declarará terminado cuando:

- Todas las cláusulas admitidas tengan configuración accesible, compilación y consumo correcto.
- No queden pendientes ejecutables ni defectos conocidos de composición.
- Las siete filas sin clasificar y la fila posterior tengan disposición explícita.
- Pasen las comprobaciones integradas aplicables.
- El CSV conserve sus 4.556 claves y su trazabilidad.

E2E queda completamente excluido y no es requisito de cierre. No se certifica T14. `cases/grants` conserva su propietario externo. Si aparece una fuente realmente ausente que impida implementar una consecuencia admitida, se identificará exactamente y no se afirmará que el motor está completo.

Este plan no realiza nuevas modificaciones, commits ni pushes.
