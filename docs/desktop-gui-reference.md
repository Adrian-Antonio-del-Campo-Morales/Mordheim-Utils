# Guía visual y de uso de la GUI de escritorio

Este documento describe la apariencia, la estructura y el uso de la aplicación de escritorio. Las proporciones indicadas se basan en las capturas de `artifacts/gui-captures/desktop/`, tomadas con una ventana de aproximadamente 1560 × 900 píxeles.

## Estructura global de la ventana

La aplicación usa una ventana única con tres zonas permanentes:

1. Una **cabecera horizontal** de unos 60 píxeles de alto.
2. Un **panel de trabajo** que ocupa el resto de la ventana.
3. Barras de desplazamiento vertical cuando la cronología o el contenido superan el alto disponible.

El fondo general es azul marino casi negro (`#11151a`). Los paneles usan un tono ligeramente más claro, con bordes grises finos. El dorado identifica la acción principal, la selección activa, los valores importantes y los iconos de navegación. Los textos descriptivos son azul grisáceo o blanco; los mensajes de estado usan verde, dorado o rojo según su significado.

## Cabecera

La cabecera se divide horizontalmente en identidad, navegación y acciones.

### Identidad del producto

Está en el extremo izquierdo, dentro de una zona de unos 420 píxeles. Muestra en mayúsculas y con serifas el texto `GESTOR DE CAMPAÑAS DE MORDHEIM`; debajo aparece en dorado `UNA BANDA A TRAVÉS DEL TIEMPO`. No cambia entre vistas y sirve como referencia visual permanente de la aplicación.

### Navegación principal

Ocupa la zona central y contiene tres pestañas anchas, cada una con un icono dorado encima o junto al texto:

- **CAMPAÑA:** icono de estandarte o pergamino. Vuelve al espacio de la campaña activa.
- **REGLAS:** icono de libro o balanza. Abre el catálogo de consulta y oculta la cronología.
- **AJUSTES:** icono de engranaje. Abre las preferencias generales.

La pestaña activa se distingue mediante un fondo algo más claro, borde inferior dorado y texto destacado. Las pestañas no cierran la campaña abierta; solo cambian el área de trabajo.

### Acciones de archivo

Se alinean a la derecha en una única fila. Cada botón combina un icono grande y una etiqueta corta:

- **Nueva campaña:** abre el diálogo de creación.
- **Campañas:** abre la biblioteca de campañas.
- **Cargar:** abre el selector de archivos.
- **Guardar:** guarda la campaña actual.
- **Deshacer:** revierte la última modificación.
- **Exportar PDF:** genera una copia imprimible.

Los botones sin una campaña válida o sin una acción aplicable se muestran atenuados. La cabecera mantiene el mismo orden en español e inglés.

## Espacio de campaña

Cuando está activa la pestaña Campaña, el contenido se divide en dos columnas. La columna izquierda ocupa aproximadamente un cuarto del ancho; la derecha contiene el momento seleccionado.

### Cronología lateral

Es un panel oscuro con borde completo y título `LÍNEA TEMPORAL DE LA CAMPAÑA`. Bajo el título aparece una línea de contexto, por ejemplo `7 estados de batalla completados · Batalla #8 en resolución`.

Cada entrada de la cronología tiene:

- un icono grande que identifica el tipo de momento;
- un nombre en mayúsculas, como `ESTADO #4`, `BATALLA #7` o `POSTBATALLA #8 · EN CURSO`;
- una segunda línea con valoración, número de miniaturas, escenario o paso actual;
- un botón de acción a la derecha cuando el momento requiere continuar;
- una banda de selección cuando es el momento visible.

Las entradas se ordenan cronológicamente: borrador inicial, estados, batallas y postbatallas. La lista tiene desplazamiento independiente, por lo que se puede recorrer la historia sin perder el panel de detalle. Al hacer clic en un nodo se actualiza el contenido de la columna derecha.

### Franja de resumen

En las vistas de campaña aparece sobre el detalle principal. Es una banda horizontal dividida en celdas, con el nombre de la métrica en pequeño y su valor grande debajo. Según el momento puede mostrar tesorería, reclutamiento, equipamiento, valoración, miniaturas y héroes.

Debajo de las métricas hay mensajes compactos de validación. Un texto verde indica un requisito cumplido; un aviso dorado señala una acción pendiente o un límite relevante.

### Encabezado del momento

El detalle comienza con un título grande en blanco, una etiqueta de fase en dorado y una línea secundaria con fecha, escenario o descripción. Este encabezado permite saber inmediatamente qué representa la pantalla antes de leer las tarjetas inferiores.

## Borrador inicial — `D-01-borrador-inicial`

El borrador conserva la misma división de dos columnas que el resto de la campaña. A la izquierda solo aparece el nodo `BANDA INICIAL · BORRADOR`, con el botón dorado `CONFIRMAR` cuando la composición es legal.

En la derecha se muestran, de arriba abajo:

1. La franja de métricas y comprobaciones.
2. El título `BANDA INICIAL` y la descripción de que la banda se convertirá en el estado inicial inmutable.
3. Las pestañas `HÉROES`, `SECUACES`, `ESPADAS A SUELDO` e `INVENTARIO`.
4. Una zona de alta o edición de guerreros.
5. Las tarjetas de los miembros ya incorporados.

La pestaña activa tiene fondo dorado. En la vista de héroes, cada tarjeta muestra nombre, coste, menú contextual, atributos en una tabla compacta, equipo, habilidades y experiencia en una tira segmentada. El botón superior `AÑADIR HÉROE` inicia el alta. Las pestañas de secuaces y espadas cambian el tipo de perfil disponible; Inventario cambia a la reserva común.

La banda solo puede confirmarse cuando cumple el mínimo y máximo de miniaturas, el límite de héroes y la tesorería disponible. El estado de cada regla se ve en la franja superior, antes de pulsar `CONFIRMAR`.

## Estado de banda — `D-04` a `D-07`

El encabezado cambia a `BANDA ACTUAL`. Debajo aparecen las pestañas `RESUMEN`, `GUERREROS` e `INVENTARIO`.

- **Resumen (`D-04):** presenta las métricas de valoración, miniaturas, tesorería y piedra bruja en una fila. Después muestra dos tarjetas grandes: `BANDA EN ESTE PUNTO` con el recuento de héroes, secuaces y experiencia, y `POSICIÓN EN LA CAMPAÑA` con la batalla o postbatalla asociada.
- **Guerreros (`D-05):** sustituye las tarjetas de situación por una cuadrícula de tarjetas individuales. Cada una contiene identidad, experiencia, condición, atributos, equipo y habilidades. Los grupos muestran además su cantidad de miembros.
- **Inventario (`D-06):** presenta una tabla o lista de existencias con objetos, cantidades y propietario o destino. Las acciones de asignar y retirar se sitúan junto a cada fila.
- **Histórico (`D-07):** mantiene exactamente la misma cabecera, cronología y pestañas, pero añade `HISTÓRICO · SOLO LECTURA`. No muestra controles de edición para evitar modificar una instantánea pasada.

La pestaña activa se marca en dorado; cambiar de pestaña solo cambia el panel inferior y conserva el momento seleccionado.

## Batalla — `D-08` a `D-10`

La batalla usa el mismo panel lateral de cronología. El detalle comienza con `BATALLA #N`, el resultado y una línea con escenario, rival y fecha. Las tres pestañas son `RESUMEN`, `PARTICIPANTES` y `NOTAS`.

- **Resumen (`D-08):** cuatro métricas superiores muestran valoración de la banda, valoración rival, miniaturas desplegadas y resultado. Debajo hay bloques separados de batalla, bajas y consecuencias registradas.
- **Participantes (`D-09):** cada fila identifica un guerrero o grupo, su cantidad y si participó, quedó fuera de combate o estuvo ausente.
- **Notas (`D-10):** un panel ancho muestra el texto libre asociado a la batalla.

La vista de batalla se usa principalmente para consultar un registro ya creado. La introducción de una batalla utiliza un formulario equivalente, con campos agrupados para escenario, rival, resultado, recompensas, bajas, objetivos y notas.

## Postbatalla — `D-11` a `D-19`

El encabezado muestra `POSTBATALLA #8`, la etiqueta `EN CURSO` y una explicación del flujo. La parte superior del panel derecho contiene:

- `PASO N DE 8` y el nombre de la acción activa;
- el contador de acciones pendientes;
- cuatro grupos de capítulos: recuperación/exploración, comercio, búsquedas y banda;
- dos acciones por capítulo, dispuestas de izquierda a derecha;
- botones inferiores para volver al paso anterior o continuar.

Los pasos completados se ven en verde con la marca `HECHO`; el paso actual tiene borde y etiqueta dorados; los pasos futuros aparecen atenuados y deshabilitados. El panel central cambia según el paso y puede mostrar tarjetas de heridas, tiradas de dados, exploración, venta de piedra bruja, veteranos, objetos raros, reclutamiento o equipo.

El usuario resuelve cada acción en orden. El botón de continuación avanza al siguiente paso solo cuando la acción actual está resuelta. El botón `GUARDAR Y CERRAR` queda separado en la esquina superior derecha para abandonar la secuencia sin confundirlo con el avance del paso.

## Revisión final — `D-20`

Es una pantalla de confirmación previa al guardado. Conserva el encabezado de campaña y la cronología, pero el contenido se organiza en bloques de resumen: identidad, recursos, composición de la banda, inventario, batallas y pendientes. Los botones de decisión se sitúan al final para guardar, exportar o volver a editar.

## Reglas — `D-21`

Reglas ocupa todo el ancho disponible y no muestra cronología. El título `Reglas` aparece arriba a la izquierda, seguido de una frase de ayuda. Debajo hay una fila de categorías: `Reglas Especiales`, `Estados`, `Reglas Básicas`, `Habilidades`, `Equipamiento`, `Hechizos`, `Escenarios` y `Heridas Graves`.

La zona inferior se divide verticalmente:

- una lista desplazable de entradas a la izquierda, con la entrada activa sobre fondo más claro;
- un separador vertical;
- un panel de detalle a la derecha con título, texto explicativo, etiquetas, fuentes y perfiles relacionados.

El campo `BUSCAR`, situado en la esquina superior derecha, filtra la categoría activa. Al seleccionar una entrada, el detalle se actualiza sin abandonar la categoría.

## Ajustes — `D-22` y `D-23`

Ajustes ocupa el ancho completo bajo la cabecera. El título y la descripción se sitúan arriba y un panel rectangular ocupa la primera zona de contenido.

Cada preferencia aparece en una fila horizontal: etiqueta descriptiva a la izquierda y selector o valor actual alineado a la derecha. En las capturas se ven `IDIOMA` y `CARPETA DE CAMPAÑA`. El cambio a inglés (`D-23`) conserva exactamente la misma geometría, espaciado y alineación, sustituyendo únicamente los textos.

## Ventanas modales

Los diálogos aparecen centrados sobre una capa negra semitransparente. Tienen fondo azul oscuro, borde fino dorado o gris, título grande, campos agrupados y una fila inferior de botones.

- **Nueva campaña (`D-02`):** contiene nombre de campaña, selección de banda y botones para cancelar o crear. El cursor se coloca en el primer campo.
- **Campañas (`D-03`):** es más ancha que Nueva campaña y muestra tarjetas o filas de campañas con nombre, estado y acciones de abrir, renombrar y retirar.
- **Añadir guerrero:** lista perfiles disponibles y permite elegir tipo, cantidad, nombre y coste antes de incorporarlo.
- **Equipo del borrador:** muestra opciones de compra y asignación para el guerrero seleccionado.
- **Reserva del borrador:** permite comprar objetos para la reserva común y definir cantidad.
- **Editor de equipo:** modifica cantidades equipadas o almacenadas y muestra el destinatario.
- **Contratar espada de alquiler:** presenta los perfiles elegibles, tarifa inicial y mantenimiento antes de confirmar.
- **Registrar batalla:** formulario largo dividido en datos del escenario, rival, resultado, participantes, bajas, recompensas y notas.
- **Elección de habilidad:** lista las habilidades válidas y marca la elección antes de aplicarla.
- **Gestión manual:** ofrece diálogos separados para corregir recursos, añadir objetos o registrar habilidades.
- **Precio variable:** solicita el coste final cuando una mejora, contratación u objeto no tiene precio fijo.
- **Dados:** tarjeta o diálogo compacto con el número de dados, resultado y opción de introducir una tirada manual.

Todos los diálogos bloquean la ventana principal mientras están abiertos. `Cancelar`, el botón de cierre o `Escape` los cierra sin aplicar cambios; las operaciones que podrían perder cambios muestran una confirmación.

## Convenciones de uso visibles

- El dorado significa selección, acción primaria o información que requiere atención.
- El verde confirma que un paso o requisito está completado.
- El gris azulado indica contenido futuro, bloqueado o deshabilitado.
- El texto `SOLO LECTURA` identifica una instantánea histórica no editable.
- La cronología se usa para cambiar de momento; las pestañas internas se usan para cambiar de aspecto dentro del mismo momento.
- Los botones de avance de postbatalla resuelven una secuencia ordenada; los botones de archivo actúan sobre la campaña completa.
- Las barras de desplazamiento pertenecen al panel que se desplaza: cronología, lista de reglas, inventario o detalle largo.

## Composición detallada por elemento

### Cabecera

La cabecera se lee de izquierda a derecha. La identidad ocupa un bloque fijo y no compite con los controles. A continuación, cada pestaña principal tiene su propio bloque vertical, con el icono en la parte superior y el nombre debajo. El grupo de acciones queda alineado en una sola línea a la derecha. Los botones de archivo son más estrechos que las pestañas y se separan mediante espacios pequeños, por lo que se perciben como acciones independientes y no como otra navegación.

### Cronología

La cronología tiene una cabecera propia, una lista central y un borde vertical que la separa del detalle. La cabecera no se desplaza. La lista sí puede desplazarse y conserva el orden temporal aunque haya muchos estados. Cada fila reserva el lado izquierdo para el icono, el centro para dos líneas de texto y el extremo derecho para `CONFIRMAR` o `CONTINUAR` cuando el momento exige una acción. La fila seleccionada ocupa todo el ancho disponible y se distingue con fondo gris azulado y una marca dorada en el borde.

### Franja de métricas

La franja se coloca justo debajo de la cronología de la campaña, antes de cualquier pestaña interna. Sus celdas tienen anchura similar y están separadas por líneas verticales. El nombre de cada dato aparece en mayúsculas pequeñas; el número se coloca debajo con mayor tamaño. Los avisos se agrupan en una línea inferior, alineados con el borde izquierdo, para que no interrumpan la lectura de los valores.

### Borrador y pestañas de composición

El borrador tiene una jerarquía vertical muy estable: título y descripción, selector de pestaña, botón de alta, tarjetas de miembros y confirmación final. El botón `AÑADIR HÉROE` se sitúa en el extremo superior derecho del área de detalle. Las tarjetas de guerrero ocupan todo el ancho disponible y separan tres niveles: identidad y coste, atributos y equipo, experiencia y habilidades. La tabla de atributos usa columnas estrechas y encabezados oscuros; la experiencia se representa como una tira de celdas consecutivas en la base.

Al cambiar entre `HÉROES`, `SECUACES`, `ESPADAS A SUELDO` e `INVENTARIO`, se conserva el mismo lugar de la pestaña y del contenido. Solo cambia el tipo de tarjeta o formulario que aparece debajo. La confirmación de la banda queda fuera de las tarjetas, al final del área de trabajo, para que funcione como cierre del borrador completo.

### Estado y pestañas internas

El estado coloca el título y la fecha sobre las pestañas `RESUMEN`, `GUERREROS` e `INVENTARIO`. En `RESUMEN`, la primera fila es siempre la banda de cuatro métricas; debajo hay dos tarjetas de igual jerarquía colocadas en paralelo. En `GUERREROS`, esas tarjetas se sustituyen por una cuadrícula adaptable, manteniendo un margen uniforme entre guerreros. En `INVENTARIO`, la cuadrícula se convierte en filas de existencias y acciones.

En un estado histórico, la etiqueta `HISTÓRICO · SOLO LECTURA` se coloca en la misma línea que el título, alineada al extremo derecho. No aparece una segunda pantalla de advertencia: la propia cabecera comunica que los controles de edición no están disponibles.

### Batalla y pestañas de consulta

La batalla repite la estructura de estado para que el usuario pueda orientarse: título y contexto, pestañas, métricas y paneles. `RESUMEN` distribuye los datos en bloques apilados de anchura completa. `PARTICIPANTES` usa una lista de filas homogéneas, con la situación del guerrero al final de cada fila. `NOTAS` deja un bloque de texto amplio con mucho espacio vertical libre. Las tres pestañas cambian solo el cuerpo, no el encabezado ni la cronología.

### Secuencia postbatalla

El postbatalla es más denso que las demás vistas. Primero aparece el encabezado con el botón `GUARDAR Y CERRAR` separado en la esquina superior derecha. Después se sitúa el navegador de capítulos en una banda de cuatro columnas. Cada columna tiene un rótulo de grupo y dos botones de paso apilados. Una flecha entre columnas indica la dirección del flujo. El panel de resolución comienza debajo de esa banda y ocupa casi todo el ancho; sus controles se agrupan dentro de una tarjeta interior. La navegación inferior queda pegada al borde inferior del área de detalle y separa claramente volver de continuar.

### Reglas

Reglas abandona la composición de dos columnas de campaña y usa tres franjas: título y ayuda, categorías y contenido. Las categorías son botones horizontales compactos. Debajo, la lista ocupa aproximadamente un cuarto del ancho y tiene desplazamiento independiente; el detalle usa el resto y comienza con el nombre de la regla, seguido de una línea separadora, el texto y las relaciones o fuentes. El buscador permanece arriba a la derecha, en la misma línea que las categorías.

### Ajustes

Ajustes utiliza un panel único de anchura casi completa. No hay tarjetas anidadas ni pestañas internas. Cada fila tiene una etiqueta corta en la columna izquierda y un campo, selector o ruta en la columna derecha. Las filas se separan por líneas horizontales y el espacio vacío inferior se conserva; la vista no intenta llenar la ventana con controles innecesarios.

### Diálogos

Los diálogos mantienen una composición vertical: título, explicación breve, campos o lista desplazable y acciones al pie. La ventana de Nueva campaña es estrecha y concentra la entrada inicial; la Biblioteca es más ancha porque necesita mostrar varias campañas en paralelo. Los diálogos de edición siguen el mismo patrón de formulario, mientras que los de dados o elección de habilidad reducen el contenido a una tarjeta central y una decisión principal.

El fondo oscurecido deja visible la ventana principal como contexto, pero impide interactuar con ella. El botón primario se coloca normalmente a la derecha del grupo de acciones y usa dorado; cancelar queda a su izquierda con el estilo oscuro estándar.
