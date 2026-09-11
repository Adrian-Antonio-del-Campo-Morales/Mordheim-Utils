# Cambios para aproximar la GUI web a la de escritorio

Fecha: 11 de septiembre de 2026.

## Objetivo y alcance

Tomar la GUI de `warband-manager-desktop` como referencia de navegación, organización, información disponible y comportamiento de interacción. La web debe ofrecer los mismos recorridos y decisiones, manteniendo las adaptaciones necesarias del navegador y las pantallas pequeñas. No se exige una reproducción visual idéntica.

Este documento registra la implementación y verificación de la paridad de GUI. Las capturas sirven para localizar funciones y comprobar que la información no se pierde; diferencias de color, medidas, tipografía o iconografía son aceptables cuando no cambian el uso.

Prioridades: **P1**, estructura y flujos que más afectan a la familiaridad; **P2**, presentación y coherencia; **P3**, ajuste visual final. «Confirmado» indica una diferencia identificada en el código; «por contrastar» indica un objetivo de revisión, no un fallo probado.

## Lista de cambios

### P1 — Navegación y organización

Estado del bloque P1: GUI-01 a GUI-09 implementados el 11 de septiembre de 2026. Su cierre depende de conservar funciones y recorridos, no de reproducir medidas exactas.

- [x] **GUI-01. Igualar la navegación principal.** Confirmado: escritorio ofrece Campaña, Reglas y Ajustes; web añade Inicio, Estadísticas y Biblioteca. Dejar las tres secciones de referencia y dar acceso contextual a las funciones adicionales sin perderlas. **Aceptación:** mismo orden y mismos destinos principales en ambos encabezados; estadísticas sigue siendo accesible.
- [x] **GUI-02. Sustituir la portada web por una entrada centrada en campaña.** Confirmado: la web arranca en una portada con un gran titular. Usar el espacio de campaña como entrada y resolver la ausencia de campaña con acciones compactas de crear/cargar. Contrastar el estado inicial exacto de escritorio antes de cerrarlo. **Aceptación:** al abrir una campaña se presenta directamente su espacio de trabajo, sin paso por una portada.
- [x] **GUI-03. Unificar las acciones del encabezado.** Confirmado: la web ofrece Nueva campaña y Nueva banda con el mismo formulario. Mantener una sola acción de creación y ordenar las acciones como escritorio: Nueva campaña, Campañas, Cargar, Guardar, Deshacer, Exportar PDF. **Aceptación:** ninguna acción duplicada; cada etiqueta tiene una función inequívoca.
- [x] **GUI-04. Abrir la biblioteca como diálogo de Campañas.** Confirmado: escritorio utiliza un diálogo y web una página con tarjetas. Reproducir la organización del diálogo de referencia, conservando las operaciones disponibles y el contexto de la campaña abierta. **Aceptación:** abrir/cerrar Campañas no obliga a abandonar el momento seleccionado.
- [x] **GUI-05. Igualar la composición del espacio de campaña.** Ambas versiones sitúan cronología a la izquierda y detalle a la derecha, incluido el borrador inicial. **Aceptación:** cronología y detalle conservan esa distribución y permiten el mismo recorrido, aunque sus proporciones y acabado difieran.
- [x] **GUI-06. Recuperar las secciones del estado de banda.** Confirmado: escritorio divide el estado en Resumen, Guerreros e Inventario mediante pestañas segmentadas; el resumen web reúne métricas y tarjetas de guerreros. Reproducir la separación y el orden de escritorio. **Aceptación:** cada sección muestra el contenido del momento seleccionado y conserva sus restricciones de edición.
- [x] **GUI-07. Igualar el contenido y la jerarquía del resumen.** Confirmado: escritorio presenta valoración, miniaturas/límite, tesorería y piedra bruja, seguidos de composición y posición de campaña; la web mezcla identidad con métricas y guerreros. Replicar la franja de indicadores y los bloques de contexto. **Aceptación:** mismos datos, orden y avisos de acciones pendientes para una misma campaña.
- [x] **GUI-08. Reorganizar el borrador inicial.** Confirmado: la web usa una lista con controles y un formulario lateral; escritorio incorpora tarjetas detalladas y acciones específicas para héroes, grupos y espadas de alquiler. Reproducir agrupación, acciones de alta, identidad, resumen y validaciones del borrador. **Aceptación:** crear y equipar una banda sigue la misma organización visible, sin una lista indiferenciada de perfiles.
- [x] **GUI-09. Sustituir el indicador simple de postbatalla por el navegador de escritorio.** Confirmado: web muestra paso X/8 y Continuar; escritorio dispone de cuatro capítulos, ocho pasos, iconos y estados completado/activo/futuro, además de revisión final. Reproducir esa presentación y las posibilidades de navegación que permita escritorio. **Aceptación:** el usuario identifica el paso actual, los completados y lo pendiente sin recorrer formularios; no se habilitan saltos ilegales.

### P2 — Pantallas y componentes

Estado del bloque: GUI-10 a GUI-21 implementados el 11 de septiembre de 2026. La comprobación pendiente es funcional por pantalla.

- [x] **GUI-10. Igualar las tarjetas de guerrero.** Confirmado: el borrador de escritorio muestra identidad, coste, menú contextual, atributos, equipo, reglas y experiencia con una estructura específica; los componentes web presentan otra distribución. Reproducir orden, agrupación y acciones según el contexto. **Aceptación:** mismo guerrero y mismo momento muestran información equivalente, sin omisiones ni acciones fuera de fase.
- [x] **GUI-11. Homogeneizar los títulos de momentos.** Confirmado: escritorio distingue banda actual, inicial, estado histórico y subtítulo temporal, con una insignia de solo lectura. Llevar esos encabezados a web con la misma jerarquía. **Aceptación:** el estado actual y uno histórico se distinguen antes de inspeccionar sus datos.
- [x] **GUI-12. Afinar la cronología.** La web implementa una lista de botones con selección resaltada. Contrastar la presentación de `CampaignTimeline` y trasladar su jerarquía de nodos, estados, etiquetas, iconos y acciones. **Aceptación:** mismos momentos y selección reconocible; cambiar de momento conserva el comportamiento existente.
- [x] **GUI-13. Situar el selector de variante como en escritorio.** Confirmado: escritorio lo coloca en una franja compacta encima de la campaña cuando corresponde; web lo incorpora en el borrador. Revisar visibilidad por fase antes de moverlo. **Aceptación:** misma ubicación contextual y mismas condiciones de disponibilidad.
- [x] **GUI-14. Igualar el diálogo de nueva campaña.** Por contrastar en detalle: comparar campos, orden, valores iniciales, ayudas, validaciones y botones con `new_campaign.py`. **Aceptación:** mismos datos de entrada y resultado; la adaptación web respeta foco inicial y cierre/cancelación.
- [x] **GUI-15. Alinear reclutamiento y contratación.** Por contrastar: comparar los diálogos de escritorio con los paneles web de reclutamiento, veteranos y espadas de alquiler. Priorizar el mismo orden de selección y confirmación, y la misma presentación del coste. **Aceptación:** una operación equivalente exige decisiones equivalentes y muestra el gasto antes de confirmar.
- [x] **GUI-16. Alinear inventario y equipo.** Por contrastar: reproducir la organización de `InventoryWorkspace`, selección de destinatario, existencias y acciones aplicables. Distinguir inventario consultable de operaciones de compra/asignación. **Aceptación:** se entiende qué está equipado y qué está almacenado; se mantienen las restricciones del momento histórico.
- [x] **GUI-17. Alinear entrada e histórico de batalla.** Por contrastar: comparar distribución, campos, resumen y botones de `battle_moment.py` con `BattlePanel` y `BattleHistory`. **Aceptación:** registro y consulta conservan la misma jerarquía y hacen visible la diferencia entre introducir y consultar datos.
- [x] **GUI-18. Alinear cada formulario de postbatalla.** Por contrastar: heridas, experiencia, exploración, venta de piedra bruja, veteranos, búsquedas, reclutamiento y equipo. Replicar orden de bloques, destinatarios, ayudas, resultados y ubicación de confirmaciones. **Aceptación:** cada uno de los ocho pasos tiene una comparación propia; aprobar el navegador general no basta.
- [x] **GUI-19. Alinear tiradas y entrada manual.** Por contrastar: usar `dice_resolution.py` como referencia para `DiceResolver`. Igualar elección entre tirada y entrada manual, dados solicitados, resultados y confirmación. **Aceptación:** se ve qué se tira, para quién y qué resultado se aplica; no se modifica la lógica de resolución.
- [x] **GUI-20. Alinear catálogo de reglas.** Ambas GUI cuentan con una vista de reglas; contrastar categorías, búsqueda, selección, detalle y enlaces de perfiles antes de cambiar su organización. **Aceptación:** localizar la misma regla sigue un recorrido equivalente en ambos idiomas.
- [x] **GUI-21. Igualar la presentación de Ajustes.** Confirmado: escritorio usa un panel de filas con idioma y carpeta de campañas; web ofrece idioma y una explicación de sesión. Reproducir la estructura visual, explicando el almacenamiento real del navegador. **Aceptación:** idioma se encuentra en el mismo lugar; no se simula una carpeta local que la web no utiliza.

### P2 — Lenguaje e interacción

Estado del bloque: GUI-22 a GUI-25 implementados el 11 de septiembre de 2026. Se unificaron identidad, acciones, avisos, atajos y retorno de foco; queda incluida su revisión en la comprobación visual final.

- [x] **GUI-22. Unificar textos e identidad.** Confirmado: el encabezado web usa WARBAND MANAGER y escritorio MORDHEIM CAMPAIGN MANAGER, con subtítulo propio. Adoptar textos de referencia, capitalización y vocabulario en español e inglés; revisar rótulos fijos en inglés del producto web. **Aceptación:** la misma acción recibe el mismo nombre, salvo diferencias reales del navegador.
- [x] **GUI-23. Igualar iconos y estilos de acciones.** Confirmado: escritorio usa iconos y variantes de botones de navegación, secundarios, acento y miniatura; la barra web utiliza botones de texto. Reutilizar los recursos de referencia cuando sea viable y conservar sus significados. **Aceptación:** acción principal, secundaria y contextual se reconocen de forma consistente.
- [x] **GUI-24. Homogeneizar confirmaciones, errores y cambios pendientes.** Por contrastar: revisar guardar, cerrar, retirar campaña, cancelar formularios y deshacer. Mostrar avisos cerca de la operación y conservar la protección de datos. **Aceptación:** mismas decisiones del usuario producen mensajes y transiciones equivalentes, con diferencias de almacenamiento explicadas.
- [x] **GUI-25. Alinear teclado y foco.** Escritorio registra Ctrl+Z; verificar y completar el equivalente web evitando interceptarlo mientras se edita texto. Revisar Escape, Enter, tabulación y devolución del foco en diálogos. **Aceptación:** los flujos principales se completan con teclado y cerrar un diálogo devuelve el foco a su activador.

### P3 — Fidelidad visual y adaptación

Estado del bloque: GUI-26 a GUI-29 implementados el 11 de septiembre de 2026 a partir de los valores de `theme.py`. Estos ajustes visuales son orientativos y no condicionan la paridad funcional.

- [x] **GUI-26. Derivar la paleta del tema de escritorio.** La web usa los colores de `mordheim_ui/theme.py` como referencia. **Aceptación:** los estados y acciones se distinguen con claridad; no se exige igualdad cromática.
- [x] **GUI-27. Ajustar tipografía y densidad.** Confirmado: escritorio combina Georgia y Segoe UI con encabezados compactos; web emplea Noto Sans y titulares de gran tamaño. Acercar familia, peso, escala, altura de controles, rellenos y separación, usando alternativas cuando la fuente no esté disponible. **Aceptación:** una ventana equivalente muestra una cantidad comparable de información sin reducir legibilidad.
- [x] **GUI-28. Igualar bordes, insignias, tablas y desplazamiento.** Por contrastar visualmente: unificar grosor de bordes, cabeceras, alineación de atributos, paneles y áreas desplazables. **Aceptación:** listas largas no desplazan innecesariamente los controles de navegación y no se recorta información.
- [x] **GUI-29. Adaptar a móvil conservando la organización.** Mantener la referencia de escritorio en pantallas amplias; en estrechas, plegar cronología y agrupar acciones sin cambiar sus nombres ni el orden lógico. **Aceptación:** sin desbordamiento horizontal general ni controles inaccesibles; las funciones siguen disponibles.

## Orden de ejecución propuesto

1. Capturar las pantallas de referencia y preparar las mismas campañas de prueba en ambas aplicaciones.
2. Resolver GUI-01 a GUI-09: navegación y estructura de los espacios de trabajo.
3. Resolver GUI-10 a GUI-21 por pantalla, comparando cada resultado con escritorio.
4. Completar GUI-22 a GUI-28 y verificar interacción y aspecto conjuntamente.
5. Comprobar GUI-29 y repetir los recorridos completos con teclado y ambos idiomas.

No modificar reglas de campaña, formatos de archivo ni cálculos para conseguir parecido visual. Si aparece una carencia funcional durante la comparación, registrarla por separado con un caso reproducible.

## Diferencias de plataforma que deben conservarse explícitas

- La web descarga archivos; no debe prometer que sobrescribe un archivo local cuando realmente exporta una copia. Puede usar «Guardar» con una explicación breve de la descarga.
- La biblioteca web actual vive en la sesión. Parecerse al diálogo de escritorio no implica implementar persistencia ni selección de una carpeta local.
- El navegador tiene sus propios controles, escalado y restricciones de fuentes; la comparación debe usar el mismo tamaño de contenido útil e idioma, no el tamaño exterior de las ventanas.
- Mantener accesibilidad web: foco visible, etiquetas, semántica de diálogo y controles táctiles utilizables.

## Evidencia necesaria para dar el trabajo por terminado

Campaña reproducible: `tests/fixtures/gui-capture-sisters-of-morr.mordheim`. Procedimiento y nombres de archivo: `docs/gui-capture-checklist.md`.

### Verificación ejecutada el 11 de septiembre de 2026

- **Correcto:** verificación final después del ajuste de distribución: compilación de producción, análisis estático sin errores y suite web completa con 24 archivos y 87 pruebas superadas.
- **Correcto:** revisión renderizada a 1280 × 720 de entrada vacía, nueva campaña, biblioteca, borrador inicial, reglas y ajustes. No se observaron recortes ni desbordamiento horizontal general en ese tamaño.
- **Correcto:** Nueva campaña coloca el foco en Nombre de campaña; Escape cierra el diálogo y devuelve el foco a su botón. Campañas coloca el foco en Cerrar.
- **Correcto:** el borrador conserva la cronología a la izquierda y el contenido a la derecha, y presenta las cuatro secciones de escritorio, atributos y controles en una composición compacta; Reglas mantiene categorías, búsqueda, lista desplazable y detalle; Ajustes conserva el formato por filas.
- **Correcto:** la integración de borrador y cronología está cubierta por `CampaignSlice.test.tsx`, para evitar que una futura modificación vuelva a ocultar la cronología durante la creación de la banda.
- **Correcto:** recorrido interactivo de la web con Chrome a 1560 × 900 y 390 × 844, registrado en `artifacts/gui-captures/web-verification/verification.json`. Validó acciones deshabilitadas sin campaña, foco y Escape de Nueva campaña, biblioteca, carga de la campaña de ejemplo, cronología, estado, histórico de solo lectura, batalla, postbatalla, cambios pendientes, deshacer, reglas, ajustes e inglés.
- **Correcto:** tras instalarse las dependencias, la aplicación de escritorio inicia en su tamaño de referencia de 1560 × 900. La comprobación del código ejecutado detectó y corrigió el subtítulo localizado del producto y el orden Guardar → Deshacer → Exportar PDF.
- **Correcto:** se generaron 24 capturas limpias de escritorio en `artifacts/gui-captures/desktop/`: inicio, diálogos, estado, guerreros, inventario, histórico, batalla, los ocho pasos de postbatalla, revisión final, reglas, ajustes y vistas en inglés. La utilidad reproducible está en `tools/capture_desktop_campaign_gui.py`.
- **Criterio revisado:** no se requieren parejas visualmente idénticas. Las capturas de escritorio se conservan para verificar las mismas funciones y estados, además de una organización equivalente: cabecera superior, cronología lateral, pestañas y panel de detalle en posiciones reconocibles.
- **Avisos no bloqueantes:** Vitest sigue mostrando avisos previos de actualizaciones React fuera de `act(...)`; ESLint conserva dos avisos previos de dependencias de efectos; Vite avisa de paquetes mayores de 500 kB.

- [x] Capturas de referencia de creación, biblioteca, borrador, resumen, guerreros, inventario, batalla, los ocho pasos de postbatalla, revisión final, histórico, reglas y ajustes.
- [x] Campaña de ejemplo reproducible para recorrer los mismos momentos y datos en ambas aplicaciones.
- [x] Comparar una campaña con héroes y grupos, equipo almacenado, un histórico y una postbatalla pendiente. El recorrido interactivo cubrió las vistas y la navegación; la contratación conserva su cobertura funcional específica.
- [ ] Recorrer crear → reclutar/equipar → confirmar banda → registrar batalla → completar postbatalla → consultar histórico → guardar/cargar.
- [ ] Verificar deshacer, cancelar, cambios pendientes, estados deshabilitados y solo lectura.
- [x] Revisar cabecera y Ajustes en pantalla estrecha, español e inglés, y el foco/escape de los diálogos. En móvil puede apilarse el contenido, pero debe conservar su orden y agrupación lógica.
- [ ] Registrar las diferencias de plataforma aceptadas. Las pruebas de lógica o una compilación correcta no sustituyen esta comparación de GUI.

## Mapa de archivos para implementar y contrastar

Rutas relativas a la raíz del repositorio; el prefijo **D** representa `packages/python/campaign/mordheim_campaign/ui/` y **W** representa `apps/warband-manager-web/src/`.

| Área | Referencia escritorio | Implementación web |
| --- | --- | --- |
| Encabezado, navegación y biblioteca | D `shell.py`, `dialogs/campaign_library.py` | W `ProductApp.tsx` |
| Campaña | D `views/campaign_view.py` | W `features/campaign/CampaignSlice.tsx` |
| Estado y resumen | D `views/moments/state_moment.py` | W `features/campaign/CampaignSlice.tsx` |
| Borrador | D `views/moments/initial_warband_draft.py` | W `features/draft/DraftWorkspace.tsx` |
| Nueva campaña | D `dialogs/new_campaign.py` | W `ProductApp.tsx` |
| Cronología | D `panels/` (CampaignTimeline) | W `features/timeline/TimelinePanel.tsx` |
| Batalla | D `views/moments/battle_moment.py` | W `features/battle/` |
| Postbatalla | D `views/moments/post_battle_moment.py`, `components/post_battle_sequence.py` | W `features/campaign/CampaignSlice.tsx` y paneles de cada fase |
| Dados | D `components/dice_resolution.py` | W `features/dice/DiceResolver.tsx` |
| Reglas y ajustes | D `views/rules_view.py`, `views/settings_view.py` | W `ProductApp.tsx` |
| Tema | `packages/python/adapters/desktop-ui/mordheim_ui/theme.py` | W `index.css` |

Esta lista es una base de implementación priorizada. Los elementos marcados «por contrastar» deben concretarse con la referencia visual antes de considerarlos defectos confirmados o cambios obligatorios de detalle.
