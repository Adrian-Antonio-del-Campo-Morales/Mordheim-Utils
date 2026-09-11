# Referencia funcional de las GUI de escritorio y web

Fichero de campaña: `tests/fixtures/gui-capture-sisters-of-morr.mordheim`.

## Preparación

- Usar español, escala del sistema al 100 % y zoom del navegador al 100 %.
- Usar un área útil de 1560 × 900 en ambas aplicaciones.
- Abrir una copia nueva del fichero en cada aplicación; no sobrescribir el original.
- Las capturas de escritorio usan el prefijo `D-`. No es obligatorio producir una pareja web ni reproducir tamaños, colores o separaciones exactos.
- En web, recorrer el mismo momento y la misma pestaña para comprobar las mismas funciones y datos, con una distribución equivalente de cabecera, cronología, pestañas y detalle.

## Capturas base

- [ ] `01-inicio`: escritorio en su borrador inicial (`D-01-borrador-inicial`) y web en su estado vacío equivalente.
- [ ] `02-nueva-campana`: diálogo Nueva campaña abierto.
- [ ] `03-biblioteca`: diálogo Campañas con la campaña de ejemplo cargada.
- [ ] `04-estado-resumen`: momento `state:7`, pestaña Resumen.
- [ ] `05-estado-guerreros`: momento `state:7`, pestaña Guerreros.
- [ ] `06-estado-inventario`: momento `state:7`, pestaña Inventario.
- [ ] `07-estado-historico`: momento `state:3`, mostrando el aviso de solo lectura.
- [ ] `08-batalla-resumen`: momento `battle:7`, pestaña Resumen.
- [ ] `09-batalla-participantes`: momento `battle:7`, pestaña Participantes.
- [ ] `10-batalla-notas`: momento `battle:7`, pestaña Notas.
- [ ] `11-postbatalla-navegador`: momento `post:8`, vista completa del navegador; debe mostrar el paso 5 de 8.
- [ ] `12-postbatalla-paso-1` a `19-postbatalla-paso-8`: comprobar que cada paso ofrece las mismas decisiones y resultados visibles. Si un paso futuro está bloqueado, comprobar su estado deshabilitado en la vista 11.
- [ ] `20-revision-final`: revisión final, después de completar el postbatalla sobre una copia temporal del fichero.
- [ ] `21-reglas`: Reglas especiales, con Siempre Hambriento seleccionado.
- [ ] `22-ajustes`: Ajustes en español.
- [ ] `23-ajustes-ingles`: Ajustes después de cambiar a inglés.
- [ ] `24-campana-ingles`: resumen actual en inglés.

## Estados de interacción

- [ ] `25-cambios-pendientes`: campaña modificada con el indicador de cambios sin exportar.
- [ ] `26-confirmacion-descarte`: confirmación al retirar una campaña con cambios.
- [ ] `27-error-validacion`: validación visible en un formulario sin rellenar un campo obligatorio.
- [ ] `28-acciones-deshabilitadas`: encabezado sin campaña, mostrando Guardar, Deshacer y Exportar PDF deshabilitados.
- [ ] `29-foco-dialogo`: Nueva campaña abierta con el foco visible en Nombre de campaña.

## Pantalla estrecha, solo web

Usar un área útil de 390 × 844 y nombres con prefijo `W-M-`.

- [ ] `30-vacio-movil`: estado vacío y encabezado completo.
- [ ] `31-borrador-movil`: borrador con las pestañas y el formulario de alta.
- [ ] `32-resumen-movil`: `state:7`, Resumen.
- [ ] `33-inventario-movil`: `state:7`, Inventario.
- [ ] `34-postbatalla-movil`: `post:8`, navegador y paso activo.
- [ ] `35-reglas-movil`: categorías, lista y detalle.
- [ ] `36-ajustes-movil`: panel de Ajustes.

## Qué debe comprobarse

- Encabezado, orden y nombres de acciones.
- Ancho de cronología, alineación de títulos y densidad de contenido.
- Pestañas, avisos y estados activo, deshabilitado y solo lectura; su estilo puede diferir.
- Mismos guerreros, atributos, equipo, inventario, batalla y paso de postbatalla.
- Ausencia de recortes que impidan usar una función o consultar información.

## Capturas de escritorio generadas

Directorio: `artifacts/gui-captures/desktop/`.

- [x] Inicio, Nueva campaña y Biblioteca: `D-01` a `D-03`.
- [x] Estado actual, Guerreros, Inventario e histórico: `D-04` a `D-07`.
- [x] Batalla, Participantes y Notas: `D-08` a `D-10`.
- [x] Navegador de postbatalla y pasos 1–8: `D-11` a `D-19`.
- [x] Revisión final: `D-20`.
- [x] Reglas, Ajustes español/inglés y campaña en inglés: `D-21` a `D-24`.
- [x] Pasos futuros 6–8 y revisión final renderizados sobre una copia exclusivamente en memoria; el fichero original no se modificó.
