# Guía para detectar y corregir salidas de texto inseguras

Estado revisado: 24 de septiembre de 2026. Esta guía describe el proceso de
migración y mantenimiento del gestor **web**, incluidos sus historiales, PDF y
exportaciones legibles. No modifica el escritorio ni el formato `.mordheim` v5.

## 1. Qué queremos garantizar

Todo texto del sistema o de la KB que llegue a una persona debe proceder de una
resolución válida para el idioma activo: español o inglés. No se permite usar un
ID, tag, nombre capturado, traducción de otro idioma ni texto técnico como salida
alternativa.

Esto incluye contenido visible y no visible a primera vista: menús, opciones,
tablas, etiquetas, nombres, tooltips, diálogos, errores, estados vacíos,
placeholders, atributos accesibles, contenido de CSS, impresión y documentos.

Hay dos excepciones por **procedencia**, no por el aspecto de la cadena:

- Los nombres personales y las notas introducidas por el usuario se conservan
  literalmente, aunque contengan guiones bajos o parezcan identificadores.
- Los identificadores de persistencia, selección, relaciones y acciones siguen
  siendo identificadores. Un `option.value`, una clave React o un ID de relación
  no son una etiqueta para mostrar.

Si falta una referencia o traducción, se muestra el aviso localizado previsto.
El detalle técnico se mantiene en diagnóstico. Un aviso evita una fuga, pero
**no convierte el flujo en completo ni la traducción en válida**.

## 2. Cómo se originan los errores

| Patrón inseguro | Qué puede ocurrir | Corrección |
| --- | --- | --- |
| `{row.id}`, `{row.tag}`, `{item.item_id}` | Aparece un identificador técnico. | Resolver la referencia exacta de KB. |
| `{row.name}` o `{row.description}` | El campo puede contener el idioma canónico, una captura antigua o datos sin validar. | Usar el lector de presentación, incluso si la propiedad se llama `name`. |
| `name_es &#124;&#124; name_en &#124;&#124; id` | Se oculta una traducción ausente mostrando inglés o un ID. | Resolver solo el idioma solicitado; en error, aviso localizado. |
| `id.replaceAll("_", " ")`, capitalización de un ID | El tag parece una etiqueta, pero sigue sin ser una traducción. | Enumeración cerrada o referencia de KB, según su origen. |
| Buscar por nombre visible o elegir `matches[0]` | Se puede escoger otra banda, perfil, tabla o regla homónima. | Identidad completa y contexto exacto; ambigüedad significa error. |
| Si falla una regla contextual, buscar una global | Puede mostrarse una regla distinta con el mismo ID. | Conservar el contexto; usar `scope: "global"` solo para una referencia realmente global. |
| Una frase traducida con `${rawId}` como argumento | La plantilla es correcta, pero introduce el ID dentro de la frase. | Resolver entidades antes de componer el mensaje. |
| `error.message`, `String(error)` en un diálogo | Se muestran excepciones, rutas o mensajes internos en otro idioma. | Mensaje de error conocido o aviso genérico; diagnóstico separado. |
| `event.description`, `applied_label`, `roll_history` | El historial conserva frases escritas en otro idioma. | Guardar hechos estructurados y resolverlos al presentar. |
| `String(value)`, `.join()` sobre datos importados | Un supuesto número o lista puede contener texto arbitrario. | Validar números, dados, fechas y miembros de listas antes de formatearlos. |
| Texto en `title`, `aria-label`, `data-title` o CSS | La tabla parece correcta, pero el tooltip, lector de pantalla o vista móvil filtra texto. | Aplicar la misma frontera que al contenido principal. |
| Estado o caché con una frase ya traducida | La pantalla no cambia por completo al cambiar de idioma. | Guardar hechos/claves; resolver con el idioma activo e invalidar cachés pertinentes. |
| Copiar una fila antes de `recordText` | Se pierde la identidad del registro original utilizada por el lector. | Resolver sobre la fila original; copiar después los valores ya validados. |
| `as UiText`, `as ResolvedKbText`, `any` o supresiones | Se engaña al compilador sin validar la procedencia. | Corregir el origen y los tipos; no forzar el resultado. |
| Diccionario manual de traducciones de KB | Se duplica la KB y se ocultan pendientes o cambios canónicos. | Corregir el índice/fuente; reservar el catálogo de interfaz para mensajes y enumeraciones del sistema. |

La detección por guiones bajos, prefijos o idioma aparente no es una garantía:
puede aceptar texto incorrecto y rechazar nombres personales legítimos.

## 3. Detectar las salidas inseguras

### Método de detección y revisión

Desde la raíz del repositorio se puede ejecutar el control completo mediante:

```console
python tools/mordheim-utils.py check-presentation
```

Ejecuta las pruebas del detector y, si pasan, la auditoría estricta y profunda.
Requiere npm y las dependencias web instaladas; conserva el código de salida del
control. Consultar `check-presentation --help` para ver los requisitos e informes.

1. Ejecutar `npm run audit:gui:deep` desde `apps/warband-manager-web` y consultar
   `build/generated/gui-text-audit-deep.md` y su JSON. La salida con código 1
   indica incidencias que bloquean el control; no un fallo de ejecución por sí sola.
2. Para cada incidencia, seguir **origen → transformaciones → destino**. Revisar
   archivo, línea, elemento, expresión, orígenes y recorridos incompletos del JSON.
   Buscar todos los consumidores cuando el dato pasa por un componente compartido.
3. Clasificar la procedencia del campo: KB, mensaje del sistema, enumeración,
   valor formateado o dato personal. Un nombre de variable como `label`, una frase
   aparentemente traducida o la ausencia de guiones bajos no prueban protección.
4. Comprobar todos los destinos del mismo dato: texto visible, atributos accesibles,
   controles, tooltips, historial, impresión y PDF. Examinar tanto la referencia
   original como capturas guardadas, alias, callbacks y escrituras posteriores.
5. Tratar una salida desconocida o un recorrido incompleto como **protección no
   demostrada**. No aprobarlo porque no se haya encontrado un ID. Corregir la
   frontera o ampliar el detector con una prueba reproducible del mecanismo.
6. Verificar el detector con una fuga deliberada en un fixture de prueba y verificar
   la GUI real con datos marcados, errores y cambio es → en → es. Mantener los nombres
   personales literales aunque parezcan IDs; nunca usar su apariencia para decidir.

Las búsquedas de texto y la inspección visual complementan este proceso. La
garantía principal es la procedencia validada y el bloqueo de salidas no verificadas,
no una lista de palabras prohibidas ni la detección automática de idioma.

### 3.1 Inventario reproducible y comprobaciones

**Para buscar elementos cuya protección no puede demostrarse, usar el modo
estricto**, desde `apps/warband-manager-web`:

```powershell
npm run audit:gui
```

Desde la raíz también puede ejecutarse sin cambiar de directorio:

```powershell
npm --prefix apps/warband-manager-web run audit:gui
```

Para generar el mismo informe sin que las incidencias produzcan código de salida
1 —por ejemplo, durante una exploración manual— ejecutar desde la carpeta web:

```powershell
node tools/presentation-audit.mjs --strict
```

Esto no aprueba las incidencias: solo omite `--check`. En automatizaciones que
deban bloquear ante pendientes, usar `npm run audit:gui`.

Produce dos informes en la raíz del repositorio:

- `build/generated/gui-text-audit.md`: resumen y tabla de archivo, línea,
  elemento, motivo y expresión.
- `build/generated/gui-text-audit.json`: datos completos para filtrar o automatizar.

Devuelve código de salida **1** si encuentra una salida insegura, un error de
compilación o un punto que no sabe clasificar. No significa que el proceso se haya
roto: significa que no puede certificar el conjunto analizado. Devuelve **0** si
no encuentra incidencias dentro de su cobertura. No incorpora una lista de
excepciones para ocultar las incidencias actuales.

El modo estricto incluye la barrera existente y añade valores visibles de
controles, propiedades de componentes, propagaciones `...props`, HTML inyectado,
elementos creados dinámicamente, escritura de nodos de texto/canvas, llamadas y
asignaciones calculadas, inserciones DOM y condiciones JSX que pueden producir
texto (`count && <Panel />` puede mostrar `0`). Incluye errores del compilador
para que una llamada mal tipada al adaptador no figure como garantía válida.

Los formatos de código/GUI reconocidos pero no analizados bajo `src` —por ejemplo
JS, HTML o SVG— y el `index.html` de entrada quedan señalados para revisión del
archivo. No se certifican por omisión. Los recursos externos, bibliotecas,
archivos fuera de ese alcance y construcción dinámica arbitraria requieren
comprobaciones adicionales.

#### Interpretar los motivos del modo estricto

| Motivo | Qué revisar |
| --- | --- |
| `unvalidated-output` | Salida textual sin adaptador válido. |
| `unclassified-control-value` | `input`/`textarea` u otro valor visible: demostrar procedencia personal, búsqueda, número o texto del sistema. |
| `unclassified-component-prop` | Propiedad que puede transportar etiquetas, modelos de filas o callbacks; revisar el consumidor. También puede ser configuración legítima sin salida textual. |
| `unclassified-spread` | Expansión que puede introducir atributos, etiquetas o `children` sin que aparezcan explícitos. |
| `unclassified-html` / `unclassified-dynamic-element` | HTML o creación dinámica que necesita un adaptador explícito o análisis adicional. |
| `unclassified-computed-call` / `unclassified-computed-write` | Destino calculado; puede ser un resolver legítimo o una vía de escritura no demostrada. |
| `unclassified-dom-insertion` / `unclassified-property-write` | Inserción o propiedad susceptible de transportar texto. |
| `unclassified-render-guard` | Una condición puede renderizar una cadena/número; usar una condición booleana si ese era el propósito. |
| `unclassified-source-format` | Archivo de GUI que necesita cobertura específica o revisión. |
| `unclassified-native-attribute` | Atributo nativo de JSX no inventariado que puede transportar texto visible. |
| `unclassified-data-attribute` | Atributo `data-*` propio que no está en el inventario auditado. |
| `presentation-cast` | Cast a `any` o a `UiText`/`LocalizedText`/`PresentationText`/`ResolvedKbText` fuera del constructor autorizado. |
| `presentation-type-forgery` | Afirmación de tipo (`as`) que fabrica un valor de presentación desde otro módulo; se comprueba con los tipos resueltos, así que alias y `typeof` no la evitan. |
| `presentation-any` | Uso explícito de `any`, que anula la comprobación de tipos. |
| `presentation-suppression` | `@ts-ignore`, `@ts-nocheck`, `@ts-expect-error` o `eslint-disable`. |
| `raw-system-value` | Lectura o desestructuración de una propiedad conocida de texto del sistema sin validar. |
| `unlocalized-export` | Importación de los escritores de `review-exports` sin pasar por los adaptadores localizados. |
| `unclassified-element-attribute` | Atributo de un elemento personalizado o de animación SVG. |
| `unclassified-dynamic-code` | `eval`, `Function`, `Worker`/`SharedWorker` o import dinámico no literal. |
| `unclassified-css-syntax` | Escape con barra invertida o `@import` fuera de la gramática CSS soportada. |
| `unvalidated-css-content` | `content:` con un valor que no es un símbolo permitido ni `attr(...)` de un atributo inventariado. |
| `compiler-error` | Corregir los tipos antes de considerar fiable el informe. |
| `raw-text-flow` | Una salida o propiedad transportadora puede recibir una lectura cruda de nombre, descripción, efecto, ID, tag o texto persistido. Consultar origen y recorrido. |
| `incomplete-text-flow` | El rastreo agotó su presupuesto de trabajo o profundidad; no se certifica la procedencia. Se emite **además** de `raw-text-flow` cuando esa misma salida sí tenía origen: 72 de los 76 puntos truncados lo llevan. |
| `unclassified-aliased-writer` | Escritor de texto copiado a una variable, desestructurado, ligado con `bind` o invocado mediante `call`/`apply`. |
| `unclassified-indirect-write` | Asignación mediante `Object.assign`, `Object.defineProperty`, `Object.defineProperties` o `Reflect.set`; revisar destino y propiedades. |
| `unclassified-style` / `unclassified-style-content` | Estilo dinámico, expansión de estilos o contenido CSS capaz de mostrar texto sin pasar por JSX. |

#### Cobertura adicional de escrituras indirectas

El modo estricto también señala estas vías:

- `iframe.srcDoc`, `setHTML`, `setHTMLUnsafe`, `createContextualFragment` y
  `DOMParser.parseFromString`: introducir HTML puede introducir texto visible.
- `setAttributeNS` para atributos textuales, incluidos nombres calculados.
- `aria-placeholder`, `aria-roledescription`, `aria-braillelabel` y
  `aria-brailleroledescription`, además de los atributos accesibles anteriores.
- Escritores con alias: `const emit = document.write; emit(raw)`, cadenas de
  alias locales, desestructuración y `bind`/`call`/`apply`.
- Asignaciones indirectas mediante `Object` y `Reflect`, aunque también puedan
  modificar objetos de negocio sin presentación. Son candidatos a revisión.
- `style.content`, `style.cssText`, estilos JSX dinámicos o propagados y llamadas
  `insertRule`, `addRule`, `replaceSync` y `setProperty`. Un estilo desconocido
  no se aprueba porque la propiedad visible no aparezca literalmente en el JSX.

Estos mecanismos no se consideran seguros por haber escapado HTML: escapar
caracteres evita otros problemas, pero no traduce una etiqueta ni resuelve un ID.
Para repararlos, preferir componentes y adaptadores tipados; si la escritura
dinámica es necesaria, crear una frontera estrecha y verificable, con pruebas
de rechazo para datos crudos. No añadir excepciones generales por nombre de API.

#### Consultar y priorizar el informe

Desde la raíz, en PowerShell:

```powershell
$audit = Get-Content 'build/generated/gui-text-audit.json' -Raw | ConvertFrom-Json
$audit.findings | Group-Object reason | Select-Object Name, Count
$audit.findings |
  Where-Object reason -eq 'raw-text-flow' |
  Select-Object file, line, element, expression, origins
$audit.findings |
  Where-Object reason -eq 'incomplete-text-flow' |
  Select-Object file, line, expression
```

Para abrir un recorrido completo sin truncar sus objetos:

```powershell
$audit.findings |
  Where-Object reason -eq 'raw-text-flow' |
  Select-Object -First 1 |
  ConvertTo-Json -Depth 30
```

Primero corregir errores de compilación y salidas directamente sin validar.
Después seguir cada `raw-text-flow` desde el consumidor hasta su origen. Revisar
los recorridos incompletos y propiedades indirectas antes de cerrar la garantía.
Tras cada corrección, regenerar el informe: los números de línea y los recuentos
anteriores no son una lista estable de incidencias.

**No existe todavía garantía de detectar cualquier texto sin blindar.** El
analizador combina sintaxis, tipos y un rastreo acotado; no ejecuta todas las
pantallas ni comprende cualquier construcción dinámica. Tampoco comprueba la
calidad lingüística de traducciones presentes. Un resultado limpio se refiere
exclusivamente a su cobertura implementada.

La ampliación de escrituras indirectas deja una fotografía de **1.946 puntos y
728 incidencias**, con **110 pruebas del detector superadas**. El modo estricto
termina con código 1 por esos pendientes, y `npm run lint` —que ejecuta
`check:presentation`— y la publicación heredan ese bloqueo; `eslint` por sí solo
no ve estas incidencias: son comprobaciones con alcances diferentes, no
resultados contradictorios.

**Una incidencia sin clasificar es una solicitud de revisión, no una fuga
confirmada.** Se prefiere señalar un caso dudoso a aprobarlo silenciosamente.
El primer informe del modo estricto, antes del rastreo de procedencia y de los
mecanismos indirectos, encontró 447 incidencias sobre los 1.924 puntos de su
inventario: 346 propiedades de componentes, 62 llamadas calculadas, 19 valores de
controles, 12 condiciones de renderizado y 8 casos de otras categorías. Ampliar el
detector elevó después el inventario; son recuentos históricos y cambiarán al
modificar código.

#### Rastreo de textos crudos desde el origen

`audit:gui` también ejecuta `tools/presentation-flow-audit.mjs`. Usa los símbolos
y funciones resueltos por TypeScript para seguir hacia atrás el valor de una
salida. Cubre alias, inicializadores de objetos, desestructuración, asignaciones,
plantillas, concatenaciones, alternativas de idioma/ID, transformaciones de
cadenas, argumentos y retornos de funciones locales o importadas. También recoge
inicializadores y actualizaciones directas de estados creados con `useState`.

Una lectura como `row.name`, `row.effect`, `row.profile_name` o `row.id` se trata
como **origen potencialmente inseguro**, incluso después de copiarla o formatearla.
La comprobación no afirma que todo campo llamado `name` proceda de la KB: puede
ser personal o formar parte de un modelo que no se renderiza. Estos casos se
revisan por procedencia y destino. Se rastrean conservadoramente los argumentos
de transformaciones desconocidas; puede señalar valores que la función descarte.

Los resultados opacos de resolución/formateo detienen la propagación. Un cast
directo no la detiene. Esta regla se complementa con el control de tipos y de
casts; los constructores autorizados requieren revisión propia. No convierte
una traducción lingüísticamente incorrecta en detectable automáticamente.

Cada incidencia `raw-text-flow` incorpora `origins` en el JSON: archivo, línea,
expresión de origen y `path` con el recorrido desde el consumidor. El Markdown
incluye esa información en «Origen y recorrido».

El análisis es acotado: hasta 250 pasos y 24 niveles de recorrido por expresión,
con protección contra ciclos. Al agotarse ese límite se emite
`incomplete-text-flow`, no un resultado seguro. No es un análisis completo de
alias mutables, todos los hooks, librerías, reflexión ni JavaScript arbitrario.

Tras incorporar el rastreo y el resto de mecanismos, la revisión del 24 de
septiembre encontró **728 incidencias**, incluidas **131 rutas potenciales de
texto crudo** y **121 recorridos incompletos**, sobre **1.946 puntos**. Son
incidencias de análisis, no 728 elementos distintos ni 728 fugas demostradas; un
punto puede tener varios motivos.

Las 166 rutas del informe profundo están clasificadas una a una en
[la clasificación de `raw-text-flow`](raw-text-flow-triage.md): identidad 122,
prosa o captura resuelta 35, escritura mixta 9, **0 fugas demostradas**. Esa
clasificación cita el productor que cierra cada archivo y caduca al modificar
cualquiera de ellos. Los 76 cortes del modo profundo se revisan aparte en [los 76
recorridos truncados](incomplete-text-flow-triage.md).

#### Pruebas con KB marcada

Actualización del 24 de septiembre de 2026: las pruebas marcadas también montan
`WarriorCard` y `PostBattleHistory` reales, y verifican las exportaciones de texto
de plantilla e historial en es → en → es. Conservan nombres personales y capturas
antiguas en los datos; incluyen un evento desconocido con aviso localizado. El
caso hace ida y vuelta JSON, **no sustituye la prueba del importador v5 real**.

El test de PDF añade ambos idiomas con IDs/capturas marcados. Comprueba las
cadenas entregadas a `drawText` y carga el PDF serializado para descomprimir sus
streams y verificar los textos hexadecimales de las fuentes estándar actuales.
No es un extractor general para cualquier fuente ni una revisión visual.

Actualización del 24 de septiembre de 2026: `raw-text-flow-producers.test.ts`
añade sondas marcadas para los productores que el rastreo señala como
portadores (catálogo de reglas —nombre, prosa, etiquetas y enlaces— y tabla de
objetivos de escenario): la captura canónica y el ID están envenenados y deben
quedar fuera de la etiqueta, y una etiqueta fuera del vocabulario cerrado debe
desaparecer en vez de titularse.

```powershell
npm test -- src/architecture/presentation-poison.test.tsx src/architecture/raw-text-flow-producers.test.ts src/features/export/warband-pdf.test.ts
```

#### Revisar recorridos incompletos con más profundidad

```powershell
npm run audit:gui:deep
```

El modo profundo usa hasta 2.500 pasos y 80 niveles por expresión, frente a
250/24 del modo habitual. Escribe `build/generated/gui-text-audit-deep.json` y
`.md`, sin sobrescribir el informe normal. Sigue devolviendo código 1 ante
incidencias; disponer de más recursos no declara seguro un recorrido truncado.
Las incidencias incompletas incluyen `incomplete`: hasta cinco ubicaciones de
corte, motivo (`step-limit`/`depth-limit`) y ruta alcanzada.

En la revisión del 24 de septiembre, el modo profundo pasó de 121 a **76
recorridos incompletos** y encontró **166 rutas potenciales de texto crudo**
frente a 131: **718 incidencias totales**. Esto demuestra que ampliar el
recorrido descubre más candidatos, no que los 45 recorridos ahora completos sean
necesariamente seguros.

Se probaron cadenas de alias que exceden el límite normal y alcanzan el origen
crudo en modo profundo, conservando las pruebas de ciclos y truncamiento.

Los 76 recorridos truncados están revisados en [los 76 recorridos
truncados](incomplete-text-flow-triage.md): el corte es agotamiento del
presupuesto de trabajo por punto (366 `step-limit` frente a 14 `depth-limit` en
los 380 cortes registrados), y al ampliarlo aparecen 690 orígenes más, todos de
las familias ya clasificadas. La consecuencia operativa es que un recorrido
truncado no puede leerse nunca como recorrido completo, por mucho presupuesto
que se añada.

Quedan pendientes los menús/formularios y estados de error no ejecutados por
esas sondas, los flujos del importador v5 real y una revisión visual final del
PDF. Las comprobaciones siguientes describen la sonda original.

```powershell
npm test -- src/architecture/presentation-poison.test.tsx
```

Estas pruebas introducen marcadores `RAW_KB_POISON_` en IDs y textos canónicos de
una KB de prueba. Comprueban que el detector de contenido ejecutado descubre una
fuga deliberada en texto, atributo y campo visible; después comprueban que el
selector y `KnowledgeHint` protegidos no la reproducen al cambiar es → en → es
ni al faltar la traducción española. El ID de selección permanece intacto.

Es una prueba de recorridos concretos, no un barrido automático de todas las
pantallas ni del PDF. Para ampliar cobertura, añadir escenarios renderizados y
exportaciones al mismo enfoque, incluyendo sus estados abiertos y datos dañados.
Las 110 pruebas del detector —82 de la barrera sintáctica, 26 del rastreador de
flujos y 2 del control de tipos— se ejecutan con `check:presentation` y `lint`;
comprueban también funciones importadas, estado, falsificaciones y ciclos.

Para resolver una incidencia legítima, corregir la procedencia o ampliar el
clasificador con una regla verificable y una prueba que rechace la variante
insegura. No añadir excepciones por archivo/línea, casts ni supresiones para
obtener cero. No envolver IDs de selección como si fueran etiquetas.

`audit:gui` es la misma auditoría con los límites habituales (250/24) y ya falla
(código 1) ante sus incidencias sin clasificar; es una puerta estricta
independiente. `check:presentation` añade las pruebas del detector y el modo
profundo, y es el control obligatorio de `lint` y de la publicación.

Desde `apps/warband-manager-web`:

```powershell
npm run check:presentation
npm run typecheck
npm run lint
```

`check:presentation` ejecuta las pruebas del detector y después la auditoría
estricta y profunda, que escribe `build/generated/gui-text-audit-deep.json` y
`.md`; `lint` incluye esa comprobación. El informe del inventario sintáctico (no
estricto) es `build/generated/presentation-audit.json` y se regenera al ejecutar
`node tools/presentation-audit.mjs --check`, relativo a la raíz del repositorio.

Para generar solo el informe, sin ejecutar sus pruebas, desde la carpeta web:

```powershell
node tools/presentation-audit.mjs --check
```

Para consultar incidencias desde la raíz:

```powershell
$audit = Get-Content 'build/generated/presentation-audit.json' -Raw | ConvertFrom-Json
$audit.findings | Select-Object file, line, reason, expression
$audit.sinks | Group-Object file | Select-Object Name, Count
```

Cada salida debe revisarse por su destino y por el origen del valor. El análisis
actual cubre JSX, atributos seleccionados, llamadas de documentos/diálogos,
escrituras DOM y contenido CSS. La comprobación de tipos detecta falsificaciones
de los tipos opacos, `any` explícitos y supresiones en el código web de producción.
Ya no existe una lista de componentes que permita dejar los nuevos archivos
fuera de la frontera.

**Límite:** un informe con cero incidencias solo acredita los mecanismos
implementados. No demuestra por sí solo que se inventaríen todas las APIs futuras,
todos los valores de controles, todas las propiedades transportadoras de texto
o cualquier forma indirecta de escribir en el DOM. Al añadir un mecanismo de
salida, hay que ampliar el inventario y probar una fuga deliberada por ese camino.

### 3.2 Búsquedas de apoyo

Desde la raíz, estas búsquedas ayudan a localizar código sospechoso:

```powershell
rg -n 'resolveName|titleCaseDisplay|profile_name|applied_label|roll_history' apps/warband-manager-web/src
rg -n 'textContent|innerHTML|innerText|setAttribute|insertAdjacent|drawText|multiCell' apps/warband-manager-web/src
rg -n 'aria-label|placeholder|data-title|data-tooltip|data-disabled-reason' apps/warband-manager-web/src
rg -n 'description:|message:|event_log' packages/typescript/application/campaign
```

Un resultado no es automáticamente un fallo: conservar un ID en una acción o
una descripción heredada en persistencia es válido. Hay que seguir el dato hasta
la salida. Tampoco basta con que la búsqueda no encuentre nada: los alias y
funciones intermedias pueden ocultar el origen.

### 3.3 Distinguir un fallo de código de una traducción pendiente

Desde la raíz:

```powershell
python tools/knowledge/generate_knowledge_web.py --check
python tools/knowledge/generate_knowledge_web.py --check --check-translations
```

El primer control comprueba la concordancia con la generación. El segundo también
falla si quedan traducciones pendientes. Son controles distintos.

```powershell
$display = Get-Content 'build/generated/knowledge-web/display-text.json' -Raw | ConvertFrom-Json
$display.translation_todos | Select-Object status, location
```

`TODO-TRANSLATE` se registra durante la generación; no tiene por qué existir
literalmente en los YAML originales. Nunca debe mostrarse como texto válido.
La ubicación del informe es una ruta dentro del artefacto, no una línea de YAML.
Consultar `presentation_entries`, identificar al propietario y buscar su ID en
`sources/knowledge` permite rastrear la fuente.

La instrucción actual es registrar las traducciones que faltan, no inventarlas.
No modificar a mano `public/knowledge/*.json` ni los artefactos generados.
Véase el procedimiento detallado de herramientas en
[el contrato de presentación](web-presentation-contract.md#cómo-localizar-traducciones-pendientes-con-las-herramientas).

## 4. La forma correcta de programar una salida

La secuencia obligatoria es:

```text
dato o referencia → resolución/validación según su procedencia
                 → valor de presentación opaco
                 → composición tipada, si procede
                 → adaptador de salida
```

`PresentationValue` reúne los tipos permitidos: `ResolvedKbText`, `UiText`,
`FormattedText`, `EnumText` y `CatalogueText`. No son autorizaciones para convertir
cualquier cadena mediante un cast. Solo sus productores revisados pueden crearlos.

### 4.1 Nombres y textos de KB

Ejemplo dentro de un componente con `knowledge`, `itemId` y `locale`:

```tsx
// Incorrecto:
<span>{item.name || item.item_id}</span>

// Correcto: el identificador entra en el resolver, no en la etiqueta.
<span>{presentationOutput(knowledgeName(knowledge, "item", itemId, locale))}</span>
```

Para reglas con contexto, usar la referencia completa:

```tsx
const result = knowledge.resolveKbText(
  { kind: "rule", id: ruleId, bandId, profileId },
  "name",
  locale,
);
const label = result.ok
  ? result.text
  : translate({ key: "knowledge.unavailable" }, locale);

return <span>{presentationOutput(label)}</span>;
```

No eliminar contexto para que la búsqueda «funcione». En tablas de heridas hay
que conservar también el contexto de tabla cuando corresponda.

Para subregistros, usar `knowledge.recordText(originalRow, "name", locale)` con
la fila original del lector. Para descripciones, reutilizar
`knowledgeDescription(knowledge, ref, locale)`: solo salta un campo opcional no
declarado (`missing-field`). Una traducción ausente de un campo declarado no se
suplanta por otra descripción ni por otro idioma.

### 4.2 Mensajes del sistema y composición

Añadir el mensaje bilingüe y los tipos de sus argumentos a `i18n-core.ts`.
Reutilizar claves existentes cuando expresen el mismo significado. Para nuevas
pantallas bajo `I18nProvider`, obtener el idioma y `t` mediante `useI18n()`.

```tsx
const { locale, t } = useI18n();
const name = knowledgeName(knowledge, "item", itemId, locale);
const label = t({ key: "knowledge.quantity", args: { name, quantity } });

return <button aria-label={presentationOutput(label)}>
  {presentationOutput(label)}
</button>;
```

El argumento `name` ya está resuelto. Pasar `itemId` o una cadena arbitraria como
nombre no es una solución, aunque el mensaje exterior esté traducido.

Para composiciones simples, utilizar `textJoin` con valores validados:

```tsx
const label = textJoin([
  textNumber(quantity, locale),
  knowledgeName(knowledge, "item", itemId, locale),
]);
return <span>{presentationOutput(label)}</span>;
```

No extraer cadenas con `presentationOutput` y concatenarlas para volver a
introducirlas en el contrato. La extracción corresponde al último paso.

### 4.3 Enumeraciones, cantidades y nombres personales

| Procedencia | Productor adecuado |
| --- | --- |
| Referencia de KB | `resolveKbText`, `knowledgeName`, `recordText`, `knowledgeDescription` |
| Mensaje de interfaz | `translate` o `t` con clave y argumentos tipados |
| Estado/categoría del sistema | Enumeración cerrada de `presentation-enums.ts`; desconocidos → aviso |
| Número, fecha, dados | `textNumber`, `textDate`, `textDice`, `textDieIndex` |
| Símbolo autorizado | `textSymbol`; no introducir palabras ni IDs como símbolos |
| Nombre personal | `warriorPersonalName`, `warbandPersonalName`, `campaignPersonalName` |
| Notas personales y motivo de corrección | `battlePersonalNotes`, `manualCorrectionReason` |
| Nombre personal histórico | Adaptador específico como `historicalWarriorName` |

No crear un helper general `safeText(string)` o `userText(string)`. Permitiría
declarar seguro cualquier dato de KB. Las excepciones personales deben recibir
la entidad/campo concreto y comprobar su procedencia.

### 4.4 Componentes compartidos y atributos

Las propiedades que transportan etiquetas deben conservar el tipo de
presentación hasta el componente que las muestra:

```tsx
function Caption({ label }: { label: PresentationText }) {
  return <span title={presentationOutput(label)}>
    {presentationOutput(label)}
  </span>;
}
```

Este patrón requiere mantener inventariadas las nuevas propiedades/componentes
que transportan texto. No basta con cambiar `string` por `ReactNode`: este último
también admite cadenas arbitrarias. Si solo se admiten elementos, usar un tipo de
elemento React. `NumberStepper` ya recibe una etiqueta tipada.

En selectores, separar acción y presentación:

```tsx
<option value={itemId}>
  {presentationOutput(knowledgeName(knowledge, "item", itemId, locale))}
</option>
```

`value={itemId}` es identidad de selección. En cambio, un `input` de texto sí
muestra su `value`: hay que distinguir entrada personal, búsqueda, número y texto
del sistema. No clasificar todos los `value` como inocuos.

Aplicar el mismo criterio a `title`, `alt`, `placeholder`, `aria-label`,
`aria-description`, etiquetas móviles y atributos consumidos por CSS. Para
información de KB, preferir `KnowledgeHint`, que resuelve nombre y descripción.

El adaptador de accesibilidad de `main.tsx` tiene una excepción estrecha:
reproduce el `data-disabled-reason` ya auditado **del mismo control** en el tooltip
y la descripción accesible. No autoriza a copiar cualquier atributo ni a añadir
una frase por defecto. Observa también cambios de la explicación para seguir el
idioma activo.

### 4.5 Historiales y archivos importados

Los productores deben guardar hechos: tipo de evento, referencias, contexto,
cantidades, decisiones y resultados de dados. La frase se construye al mostrar
el historial, con el idioma actual.

Por ejemplo, `scenario_spell_reward` guarda `spell_ids`, `warrior_id` y la captura
del campo personal `warrior_personal_name`. El adaptador de historial vuelve a
resolver los hechizos; no muestra los nombres capturados en `description`.

Al incorporar un evento:

1. Añadir los hechos al productor, conservando los campos heredados necesarios.
2. Documentarlos en [el contrato v5](../../contracts/campaign-file-v5/README.md).
3. Validar los datos al consumirlos: importar un archivo no los convierte en fiables.
4. Añadir su presentación a `history-presentation.ts` y un mensaje tipado.
5. Probar idioma es → en → es, entidad desaparecida, datos dañados e ida y vuelta.

La compatibilidad con frases antiguas se mantiene aislada y exige coincidencias
completas conocidas. Lo desconocido se conserva al guardar y se representa con
un aviso. No buscar fragmentos ni traducir cadenas libres mediante reemplazos.
No cambiar la versión ni aceptar v1–v4 para resolver un problema de presentación.

### 4.6 Errores, idioma y exportaciones

- Guardar códigos/hechos del error y resolver su mensaje en el idioma activo.
  Reutilizar `localizeErrorMessage` para la compatibilidad existente; nunca mostrar
  directamente una excepción como alternativa.
- Evitar valores locales predeterminados como `locale = "en"`. El contexto activo
  debe gobernar toda la pantalla, incluidos diálogos que ya estaban abiertos.
- Recalcular resultados dependientes de `locale`; no guardar la frase final como
  dato de negocio ni usar una caché sin idioma.
- PDF y exportaciones legibles deben usar los escritores y adaptadores tipados
  existentes. Resolver de nuevo entidades de KB; conservar campos personales.
- `.mordheim` es persistencia: mantener IDs allí es correcto. No confundirlo con
  un informe para lectura.

## 5. Proceso de corrección de una incidencia

### Regla obligatoria para campos nuevos o modificados de la GUI

**Toda incorporación o modificación de un campo debe seguir este contrato desde
su creación.** Se aplica a páginas, componentes compartidos, menús, listas,
columnas, selectores, etiquetas, ayudas, diálogos, estados vacíos/de carga/error,
atributos accesibles, contenido móvil, historiales y exportaciones legibles.
No existe una excepción por tratarse de un campo pequeño, temporal u oculto
inicialmente.

Antes de implementar el campo:

- Identificar su origen y elegir el productor tipado de la sección 4. KB: resolver
  por tipo, ID y contexto exactos; interfaz: mensaje bilingüe tipado; enumeración:
  adaptador explícito; cantidades/fechas/símbolos: formateador autorizado; dato
  personal: adaptador del campo concreto. No copiar texto de KB a un diccionario
  local ni tratar una captura del sistema como texto personal.
- Obtener el idioma del contexto activo. Resolver de nuevo al cambiarlo e incluirlo
  en las dependencias de memorias y cachés. Evitar valores locales por defecto que
  puedan devolver el campo a otro idioma.
- Mantener `PresentationValue` durante el transporte y la composición. Resolver
  las entidades antes de introducirlas como argumentos de mensajes. Extraer la
  cadena mediante `presentationOutput` únicamente al entregarla al destino.
  Este adaptador **no traduce ni sanea** una cadena arbitraria.
- Mantener IDs en selección, acciones y persistencia; resolver aparte su etiqueta
  visible. Para historiales nuevos, guardar hechos/referencias estructurados y
  representar esos hechos en el idioma activo.
- Ante referencia inválida o traducción ausente, usar el aviso localizado y el
  diagnóstico técnico separado. Nunca recurrir al ID, tag, nombre capturado, texto
  inglés o conversión del identificador a palabras. `TODO-TRANSLATE` registra una
  tarea editorial; no es un texto que deba mostrarse en la GUI.

Para aceptar el campo:

- Ejecutar `npm run check:presentation` y revisar su aparición en el inventario.
  Ninguna salida nueva puede quedar sin clasificar. Si usa un mecanismo nuevo,
  ampliar primero el detector y añadir una prueba que demuestre que rechaza una
  fuga por ese mecanismo; no añadir una excepción por archivo o nombre de campo.
- Verificar los destinos y estados afectados en ambos idiomas, incluida la
  accesibilidad. Cuando proceda, cubrir cambio de idioma, referencia dañada,
  historial/importación y exportación. Reutilizar pruebas representativas cuando
  ya cubran el mismo contrato.
- No usar `any`, casts de marcas, supresiones, fallbacks ni adaptadores personales
  genéricos para superar el control. Las incidencias existentes no autorizan nuevas
  salidas sin proteger ni convierten una comprobación fallida en una aprobación.

### Pasos para corregir una salida existente

1. **Reproducir:** anotar pantalla, estado, idioma, campo, origen y si procede de
   una partida importada. Revisar también tooltip, accesibilidad y exportación.
2. **Seguir el dato:** localizar productor, modelo intermedio y salida. Clasificar
   KB, mensaje, enumeración, número/símbolo o campo personal.
3. **Resolver la causa:** corregir referencia/contexto, indexación, mensaje o hechos
   persistidos. Si falta traducción, registrar `TODO-TRANSLATE`; no añadir fallback.
4. **Cerrar la salida:** mantener tipos opacos durante la composición y extraerlos
   solo en el adaptador. Revisar todos los consumidores del helper compartido.
5. **Demostrar la protección:** introducir una fuga en una prueba del mecanismo
   afectado y comprobar que la barrera la rechaza. No dejar la fuga en producción.
6. **Verificar el comportamiento:** comprobar contenido localizado, ausencia de
   IDs/capturas, nombres personales literales y cambio de idioma en pantalla abierta.
7. **Registrar el alcance:** documentar qué está probado y qué sigue pendiente.

## 6. Comprobaciones antes de darlo por arreglado

Desde la carpeta web: `npm run typecheck`, `npm run lint`, las pruebas afectadas
con `npm test -- ruta/al/test` y `npm run build`. Ante cambios transversales,
ejecutar también la suite web completa.

Si cambia el núcleo, ejecutar `npm run typecheck` y las pruebas correspondientes
desde `packages/typescript`. Si cambia el índice o una fuente, ejecutar los
controles del generador indicados arriba. Si cambia v5, comprobar los fixtures y
las pruebas de interoperabilidad; si cambia PDF, comprobar cadenas, extracción
del documento y resultado visual.

La prueba debe afirmar lo que aparece y lo que **no** aparece. No basta probar
un helper o buscar guiones bajos. Cubrir una traducción ausente, una referencia
ambigua, un dato corrupto y un nombre personal que parezca un ID ayuda a evitar
falsas garantías. Las pruebas del navegador simulado no sustituyen una revisión
visual de PDF ni todos los recorridos interactivos.

## 7. Secciones que siguen sin cerrar

Esta lista distingue trabajo funcional pendiente de traducciones editoriales.
No significa que todas estas secciones estén filtrando IDs actualmente: varias
ya tienen una salida protegida, pero no representan aún todo el detalle.

| Sección pendiente | Dónde revisar | Qué falta |
| --- | --- | --- |
| Seguimientos y resultados especiales de exploración | `packages/typescript/application/campaign/features/exploration/exploration-workflow.ts`; `history-presentation.ts` | Completar los hechos y su representación para `exploration_special` y `exploration_followup`, sin depender de mensajes agregados. El panel visible ya está migrado. |
| Seguimientos y decisiones de heridas | `features/injuries/injury-followup-workflow.ts`, `injury-decisions-workflow.ts` del núcleo | Representar fases, decisiones, tabla, dados y resultados en los eventos `injury_followup` e `injury_decision`. No basta una etiqueta genérica. |
| Capturados y pozos | `features/injuries/injury-decisions-workflow.ts`, `sold-to-pits-workflow.ts` del núcleo | Completar hechos/presentación de rescate, intercambio, destino, combate, pérdidas y recompensas; conservar nombres personales históricos. |
| Otros efectos y seguimientos de escenarios | `features/exploration/scenario-followups-workflow.ts`, productores de batalla y reconocimiento de seguimientos | Completar presentación estructurada de `scenario_encampment`, efectos persistidos y eventos todavía no cubiertos por el adaptador de historial. La recompensa de hechizos ya tiene referencias estructuradas. |
| Detalle de eventos solo resumidos | `apps/warband-manager-web/src/features/review/history-presentation.ts` | Revisar casos como `experience` y el `default`: una etiqueta localizada del tipo no demuestra representación completa del evento. |
| Contrato de idioma y fallos en desarrollo | `i18n-context.ts`, lector de KB y adaptadores | `useLocale` conserva un último recurso `en`; revisar consumidores sin contexto/idioma explícito. Completar la política de fallo para resoluciones inesperadas en desarrollo/pruebas. |
| Cobertura semántica de la barrera | `tools/presentation-audit.mjs`, `presentation-type-audit.mjs` de la web | Completar clasificación de valores visibles de controles, propiedades intermedias, escrituras indirectas y productores fuera del ámbito web auditado. Mantener pruebas contra nuevas vías de escape. |
| Consolidación de vocabulario | `i18n-core.ts`, `presentation-enums.ts`, `packages/typescript/application/rules/catalogue-text.ts` | Revisar duplicaciones entre mensajes/enumeraciones del catálogo y la interfaz. No volver a introducir diccionarios alternativos de traducciones de KB. |
| Traducciones canónicas | `translation_todos` del índice generado y fuentes canónicas | Resolver editorialmente los `TODO-TRANSLATE` cuando corresponda. Los avisos no satisfacen el requisito de KB publicada completa. |
| Cierre transversal y publicación | Flujos web, importación v5, exportaciones, CI/publicación | Repetir los recorridos bilingües finales con KB generada; comprobar payloads abiertos, PDF visual y bloqueo de publicación ante KB incompleta. No inferirlo de un lint limpio. |
| Captura de búsquedas compartida con el escritorio | `searches[].label` en `search-workflow.ts`; `RareSearchPanel.tsx`; `post_battle_moment.py` | La web no lo imprime (resuelve la etiqueta por KB), pero el escritorio la muestra con `target_id` como alternativa, así que es un campo de paridad v5. Su revisión pertenece al escritorio; registrado en [la clasificación de `raw-text-flow`](raw-text-flow-triage.md). |

Ya migrados a la frontera de salida: pantalla principal, catálogo, campaña,
borrador, batalla, exploración visible, contratación, comercio, equipo, heridas
visibles, avances, estadísticas, cronología y escritores legibles. Los historiales
de compras/ventas, mejoras, reclutamiento —incluido miembro de grupo—, bajas,
mantenimiento, correcciones y recompensas de hechizos tienen tratamiento
estructurado en los casos implementados.

Las 1.372 salidas del inventario sintáctico (sin incidencias de barrera) y las 110
pruebas del detector son una fotografía, no un objetivo fijo ni una certificación
de exhaustividad.
Regenerar el informe al modificar código y mantener esta lista al cerrar cada caso.

## 8. Archivos de referencia

### Control obligatorio del detector

`npm run check:presentation` ejecuta las pruebas del detector y después la
auditoría **estricta y profunda**. `npm run lint` y la publicación, que ejecuta
lint, heredan ese bloqueo. Para obtener el informe aunque fallen las pruebas,
ejecutar `npm run audit:gui:deep` desde `apps/warband-manager-web`.

Se inventarían las fuentes web, los módulos del workspace importados por el
programa TypeScript, `index.html` y los recursos de código/HTML/SVG/CSS de
`public`. Los formatos que no se pueden analizar generan una incidencia,
en vez de quedar aprobados. Los atributos nativos desconocidos, los elementos
personalizados, las escrituras indirectas, el código dinámico y los recorridos
de procedencia inconclusos también bloquean el control.

El informe queda en `build/generated/gui-text-audit-deep.json` y `.md`.
Una incidencia puede ser una salida insegura o una protección no demostrada;
no significa necesariamente que el usuario ya esté viendo una fuga.
Las pruebas del detector deben pasar incluso si la auditoría del producto
falla: comprueban que lo desconocido se denuncia, no que la GUI esté reparada.

Esta política no certifica la traducción lingüística ni el comportamiento de
dependencias externas o adaptadores autorizados. Estos requieren revisión y
pruebas propias. No eliminar incidencias, ampliar excepciones ni usar casts
para obtener un resultado verde sin demostrar la procedencia del texto.

- [Contrato general e instrucciones de las tools de traducción](web-presentation-contract.md).
- [Adaptadores y valores de presentación](../../apps/warband-manager-web/src/features/campaign/presentation-values.ts).
- [Frontera final de salida](../../apps/warband-manager-web/src/features/campaign/presentation-output.ts).
- [Mensajes bilingües y parámetros](../../apps/warband-manager-web/src/features/campaign/i18n-core.ts).
- [Resolver de presentación de KB](../../packages/typescript/adapters/knowledge-reader/presentation.ts).
- [Adaptador de historiales](../../apps/warband-manager-web/src/features/review/history-presentation.ts).
- [Inventario y barrera sintáctica](../../apps/warband-manager-web/tools/presentation-audit.mjs).
- [Clasificación de las incidencias `raw-text-flow`](raw-text-flow-triage.md).
- [Los 76 recorridos truncados (`incomplete-text-flow`)](incomplete-text-flow-triage.md).
- [Contrato de persistencia v5](../../contracts/campaign-file-v5/README.md).
