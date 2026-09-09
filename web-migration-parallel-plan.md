# Plan paralelo de migración del Warband Manager

**Documento relacionado:** [`web-migration-plan.md`](./web-migration-plan.md)  
**Ámbito:** únicamente Warband Manager / Campaign Manager.  
**Objetivo:** dividir las fases restantes de la migración en unidades de trabajo que puedan ejecutarse en paralelo con pocas colisiones y con contratos claros entre equipos o agentes.

---

## 1. Punto de partida

Este plan presupone que las fases 0, 1 y 2 están terminadas o disponen de un
checkpoint revisable:

- mapa de dependencias de `mordheim_campaign`;
- contrato `.mordheim` v4, JSON Schema, documentación y fixtures;
- escritor/lector Python v4 con rechazo explícito de v1-v3;
- dominio Python separado de Tkinter mediante fachadas temporales;
- regresión de Campaign Manager ejecutable sin inicializar Tkinter.

Antes de repartir trabajo, crear un commit o una referencia inmutable que
contenga esas fases. No iniciar ramas paralelas desde árboles de trabajo con
cambios mezclados o sin identificar.

El resultado esperado de esta estrategia no es fusionar todas las ramas a la
vez: cada bloque se integra cuando sus contratos y pruebas están listos.

---

## 2. Reglas de paralelización

### 2.1 Ownership de archivos

1. Cada tarea tiene un propietario de archivos explícito.
2. Dos tareas paralelas no pueden editar el mismo archivo.
3. Los archivos compartidos de configuración (`package.json`, workflows,
   `tsconfig`, configuración de Vite) tienen un único propietario: la tarea
   de workspace o la tarea de CI, nunca ambos.
4. El esquema v4 y sus fixtures tienen un único propietario de contrato.
   Cualquier cambio requerido por otra tarea se propone como cambio de
   contrato independiente y se integra antes de continuar.
5. No se hacen formateos globales ni renombrados masivos dentro de una tarea
   funcional.
6. Los módulos nuevos se prefieren a modificar módulos compartidos. Las
   fachadas o puntos de composición se actualizan en una tarea de integración.

### 2.2 Interfaces antes que implementaciones

Cuando dos tareas necesitan colaborar:

1. acordar primero tipos, funciones y errores públicos;
2. documentar el acuerdo en el código o en un ADR corto;
3. integrar la interfaz mínima;
4. permitir que cada lado use un fake o fixture mientras el otro avanza;
5. integrar la implementación real y añadir la prueba de integración.

Las interfaces públicas iniciales deben ser conceptualmente equivalentes a:

```text
parseCampaignFile(text) -> CampaignFileV4 | CampaignFileError
serializeCampaign(state) -> valid CampaignFileV4
loadCampaignFromFile(file) -> CampaignState
exportCampaign(state) -> text/blob
queryKnowledge(id) -> canonical KB record
useCase(state, input) -> result with next state, events or errors
```

Los nombres concretos pueden adaptarse a la implementación, pero no se debe
introducir una segunda representación del fichero ni una segunda KB.

### 2.3 Ramas y worktrees

Usar una rama por bloque, creada desde el checkpoint común. Se recomienda una
convención como:

```text
migration/p3-workspace
migration/p3-campaign-file
migration/p3-domain-kernel
migration/p4-knowledge-artifact
migration/p5-vertical-slice
migration/p6-timeline
migration/p6-draft
migration/p6-inventory
migration/p6-battles
migration/p6-progression
migration/p6-hirelings-trading
migration/ci-pages
```

Cada rama debe contener cambios pequeños y compilables. Si se usan worktrees,
cada agente trabaja en un directorio distinto y nunca modifica directamente la
rama de integración.

### 2.4 Exclusiones permanentes

Ninguna tarea web puede introducir dependencias de:

- `mordheim_combat`, NumPy o Cython;
- Tkinter o `mordheim_ui`;
- filesystem o `localStorage`/IndexedDB para persistir campañas;
- reglas o catálogos copiados manualmente desde la KB;
- nombres de objetos React dentro del dominio.

---

## 3. Mapa de dependencias

```text
G0 checkpoint Phase 0-2
 ├── P3.1 workspace/toolchain ───────────────┐
 ├── P3.2 campaign-file TS adapter ──────────┼── P3.3 contract test harness
 ├── P4.1 KB catalogue inventory ────────────┐
 │                                            ├── P4.2 KB generator
 │                                            └── P4.3 KB indexes/query adapter
 └── P3.4 domain/application public interfaces
                                              │
             ┌────────────────────────────────┴─────────────────────────────┐
             │                                                              │
     P3.5 domain kernel                                            P5.1 application shell
             │                                                              │
             ├── P6.1 timeline                                             │
             ├── P6.2 draft/composition                                     │
             ├── P6.3 equipment/inventory                                   │
             ├── P6.4 battles                                               │
             ├── P6.5 injuries/recovery                                     │
             ├── P6.6 experience/advances                                   │
             └── P6.7 hirelings/exploration/trading                        │
                                                                            │
             P4.3 + P3.3 + P3.5 + P5.1 ─────── P5.2 first vertical slice ───┘
                                                                            │
                 P6 feature blocks ──> P7 interoperability/quality ──> P8 CI/Pages
                                                                            │
                                                                  P9 namespace rename
```

Las tareas de una misma columna pueden ejecutarse en paralelo cuando hayan
terminado sus dependencias. Las flechas representan contratos mínimos, no una
obligación de fusionar toda la rama anterior antes de comenzar el desarrollo.

---

## 4. Tareas paralelas de las fases 3 y 4

### P3.1 — Workspace TypeScript y aplicación vacía

**Objetivo:** dejar una base React + Vite + TypeScript reproducible.

**Propietario:** workspace web.  
**Archivos principales:** `apps/warband-manager-web/`, configuración del
workspace TypeScript y documentación de comandos.  
**No modificar:** dominio Python, contrato v4, generador de KB.

**Instrucciones:**

1. Crear la aplicación React + Vite sin lógica de campaña.
2. Activar TypeScript estricto y una estructura por capas.
3. Definir scripts de desarrollo, test, lint y build.
4. Añadir una página vacía que pueda compilarse en GitHub Pages.
5. Evitar dependencias de Combat Lab.

**Criterio de aceptación:** instalación limpia, test mínimo y build de Vite
completan correctamente; la aplicación no importa React desde paquetes de
dominio o aplicación.

**Puede ejecutarse en paralelo con:** P4.1 y el diseño de interfaces P3.4.

### P3.2 — Adaptador TypeScript del contrato v4

**Objetivo:** implementar el lector, validador y escritor neutral del fichero.

**Propietario:** contrato/persistencia web.  
**Archivos principales:** `packages/typescript/adapters/campaign-file/` y sus
tests unitarios.  
**Fuente de verdad:** `contracts/campaign-file-v4/`.

**Instrucciones:**

1. Consumir el JSON Schema existente; no duplicar sus reglas sin justificarlo.
2. Definir `CampaignFileV4` y los tipos necesarios para el dominio.
3. Implementar parseo de texto JSON y validación del marcador y versión.
4. Rechazar JSON inválido, marcador incorrecto, v1-v3, versiones no
   soportadas y violaciones del esquema con errores accionables.
5. Implementar serialización y validar el documento antes de devolverlo.
6. Mantener `saved_at` fuera de las comparaciones semánticas.
7. Preservar los mapas de payload abiertos definidos por el contrato.

**Criterio de aceptación:** todos los fixtures v4 se leen y validan; se
producen documentos válidos; existen tests para cada clase de error.

**Dependencia:** P3.1 para integrarse en el workspace, aunque el diseño de
los tipos puede comenzar desde G0.

### P3.3 — Harness de interoperabilidad del contrato

**Objetivo:** convertir los fixtures y casos de rechazo en evidencia común para
Python y TypeScript.

**Propietario:** calidad de contratos.  
**Archivos principales:** `tests/web/contract/` o equivalente y utilidades de
comparación semántica.

**Instrucciones:**

1. Cargar todos los fixtures desde `contracts/campaign-file-v4/fixtures/`.
2. Comparar documentos ignorando únicamente `saved_at` cuando corresponda.
3. Probar que el orden incidental y la vista se tratan según el README del
   contrato.
4. Añadir casos de marcador, versión, JSON corrupto, propiedades desconocidas
   y referencias KB inexistentes.
5. No copiar fixtures dentro de `apps/`.

**Criterio de aceptación:** los tests fallan si se modifica el schema, un
fixture o la política de comparación de forma incompatible.

**Dependencia:** P3.2.

### P3.4 — Interfaces públicas de dominio y aplicación

**Objetivo:** congelar los límites que permiten trabajar en paralelo.

**Propietario:** arquitectura TypeScript.  
**Archivos principales:** tipos públicos de
`packages/typescript/domain/campaign/` y
`packages/typescript/application/campaign/`.

**Instrucciones:**

1. Definir el estado de campaña, inputs, resultados, errores y eventos.
2. Separar el estado persistible de la selección de vista.
3. Definir el puerto de conocimiento y el puerto de fichero.
4. Definir cómo se representa una operación rechazada sin lanzar errores de
   UI arbitrarios.
5. Mantener las funciones de dominio puras y libres de React y navegador.
6. Si todavía no se conocen todos los campos de una operación, usar interfaces
   pequeñas y extensibles, no un objeto global mutable.

**Criterio de aceptación:** las tareas de dominio, aplicación y UI pueden
compilar contra estas interfaces usando fakes.

**Dependencia:** G0; debe revisarse junto con P3.2 antes de congelarse.

### P4.1 — Inventario de catálogos requeridos por campaña

**Objetivo:** determinar qué parte de `sources/knowledge/` necesita la web.

**Propietario:** Knowledge Base.  
**Archivos principales:** decisión/documentación en `docs/` y tests de
cobertura de catálogos.  
**No modificar:** componentes React ni el dominio de campaña.

**Instrucciones:**

1. Enumerar warbands, perfiles, objetos, reglas, escenarios, hirelings y
   textos necesarios para el alcance inicial.
2. Relacionar cada registro con sus IDs estables.
3. Identificar referencias obligatorias, opcionales y variantes por locale.
4. Excluir explícitamente datos de Combat Lab no consumidos por campaña.
5. Acordar el shape mínimo del artefacto JSON web.

**Criterio de aceptación:** existe una lista versionada de catálogos y un test
que detecta una referencia inexistente o un catálogo omitido.

**Puede ejecutarse en paralelo con:** P3.1, P3.2 y P3.4.

### P4.2 — Generador YAML → JSON web

**Objetivo:** generar reproduciblemente el artefacto de KB para Vite.

**Propietario:** pipeline de conocimiento.  
**Archivos principales:** `tools/knowledge/`, tests del generador y artefactos
transitorios bajo `build/generated/knowledge-web/`.

**Instrucciones:**

1. Leer únicamente `sources/knowledge/` mediante el lector canónico o una
   interfaz equivalente.
2. Validar estructura, IDs únicos y referencias antes de escribir la salida.
3. Generar JSON determinista, con orden estable y sin timestamps.
4. No editar manualmente el JSON generado.
5. Hacer que el fallo de validación detenga el build.
6. Generar solo los catálogos aprobados en P4.1.

**Criterio de aceptación:** dos ejecuciones con la misma KB producen la misma
salida; una referencia inválida falla antes del build web.

**Dependencia:** P4.1.

### P4.3 — Índices y KnowledgeReader TypeScript

**Objetivo:** exponer consultas por ID al dominio y a la UI sin filtrar YAML.

**Propietario:** adaptador `knowledge-reader`.  
**Archivos principales:** `packages/typescript/adapters/knowledge-reader/` y
sus tests.

**Instrucciones:**

1. Cargar el artefacto generado, no los YAML directamente.
2. Construir índices por `band_id`, `profile_id`, `item_id` y demás IDs que
   apruebe P4.1.
3. Devolver registros inmutables o copias seguras.
4. Distinguir entre ID inexistente y texto no disponible para un locale.
5. No resolver equivalencias usando nombres visibles.
6. Probar consultas con los datos reales generados y con datos corruptos.

**Criterio de aceptación:** el dominio puede resolver referencias de fixtures
sin conocer el formato interno de la KB.

**Dependencia:** P4.2 y P3.4.

---

## 5. Tareas paralelas de dominio y aplicación

### P3.5 — Kernel de dominio de campaña

**Objetivo:** portar la representación pura de estado y las primitivas comunes.

**Propietario:** dominio de campaña.  
**Archivos principales:** `packages/typescript/domain/campaign/kernel/`.

**Instrucciones:**

1. Modelar campaña, roster, inventario, timeline, batalla y post-battle sin
   dependencias de UI.
2. Mantener los IDs de KB y la separación `campaign`/`view`.
3. Implementar copias inmutables o actualizaciones estructuralmente seguras.
4. Definir invariantes comunes: estado actual, IDs únicos, referencias y
   draft frente a campaña confirmada.
5. Portar primero el comportamiento cubierto por los tests de `tests/campaign/`.
6. Añadir fixtures y casos de dominio antes de conectar componentes React.

**Criterio de aceptación:** puede probarse en Node sin DOM; no importa React,
Vite, navegador, Python o filesystem.

**Dependencias:** P3.4 y, para resolver registros, P4.3. Puede comenzar con
un fake de `KnowledgeReader`.

### P5.1 — Application service e historial en memoria

**Objetivo:** orquestar dominio, conocimiento e importación/exportación.

**Propietario:** aplicación TypeScript.  
**Archivos principales:** `packages/typescript/application/campaign/`.

**Instrucciones:**

1. Implementar acciones de cargar, seleccionar momento, ejecutar una operación
   y marcar cambios no exportados.
2. Mantener el estado en memoria; no añadir localStorage ni IndexedDB.
3. Traducir errores de dominio y de persistencia a resultados consumibles por
   la UI.
4. Mantener separado el historial/undo de la lógica de reglas.
5. Aceptar puertos inyectados para fichero y KnowledgeReader.
6. Añadir una interfaz mínima de importación y exportación para que la UI no
   manipule JSON directamente.

**Criterio de aceptación:** un test de aplicación ejecuta importar → editar →
exportar usando fakes, sin React ni APIs globales del navegador.

**Dependencias:** P3.2, P3.4 y P3.5. Puede desarrollar inicialmente con un
fake de los casos de uso aún no portados.

---

## 6. Primer vertical slice de la fase 5

### P5.2 — Importar, mostrar, editar y exportar

**Objetivo:** validar de extremo a extremo el contrato común antes de portar
toda la funcionalidad.

**Propietario:** equipo de integración web.  
**Archivos principales:** `apps/warband-manager-web/` y una carpeta de
componentes propia; no modificar internals del dominio.

**Instrucciones:**

1. Añadir selector de fichero y lectura en memoria.
2. Mostrar errores comprensibles para JSON inválido, versión incompatible y
   referencias inexistentes.
3. Mostrar identidad y roster usando IDs resueltos mediante KnowledgeReader.
4. Realizar una edición sencilla que produzca un nuevo estado.
5. Exportar un fichero `.mordheim` v4 mediante `Blob` y descarga explícita.
6. Mostrar un indicador de cambios no exportados.
7. Pedir confirmación antes de reemplazar una campaña cargada.
8. No añadir aún toda la navegación de Campaign Manager.

**Criterio de aceptación:** un fixture de escritorio se abre en la web, puede
editarse y exportarse; el fichero exportado vuelve a ser aceptado por Python.

**Dependencias:** P3.1, P3.2, P4.3, P3.5 y P5.1.

**Nota de paralelización:** la UI puede construirse en paralelo con P5.1 usando
un fake, pero la prueba completa solo se integra cuando ambos estén listos.

---

## 7. Bloques funcionales paralelos de la fase 6

Los bloques siguientes deben comenzar después de que P5.2 demuestre el flujo
básico o, si se dispone de interfaces estables, pueden desarrollarse en
paralelo con P5.2 sobre fakes. Cada bloque debe incluir dominio, aplicación,
UI y tests de su propia funcionalidad. No se debe portar primero toda la UI y
después toda la lógica.

Cada bloque debe vivir, siempre que sea posible, en una carpeta de feature
independiente bajo `packages/typescript/domain/campaign/features/`,
`packages/typescript/application/campaign/features/` y
`apps/warband-manager-web/src/features/`.

### P6.1 — Timeline y selección de estados

- navegar entre estados confirmados y draft;
- seleccionar un momento sin mutar la campaña;
- mostrar el estado actual y el seleccionado;
- probar exportación y reimportación conservando la timeline.

**Depende de:** P3.5, P5.1 y P5.2.  
**Puede paralelizarse con:** P6.2–P6.7.

### P6.2 — Draft y composición inicial

- crear y editar un draft;
- validar límites de oro, modelos y héroes;
- seleccionar warband y resolver perfiles desde la KB;
- confirmar la composición inicial;
- producir el estado inicial de campaña.

**Depende de:** P4.3, P3.5 y P5.1.

### P6.3 — Equipo, stash y asignaciones

- listar inventario equipado y stash;
- asignar y retirar equipo;
- validar restricciones y rareza;
- conservar IDs y snapshots de display al exportar;
- cubrir campañas con inventario completo.

**Depende de:** P4.3, P3.5 y P5.1.  
**No puede modificar:** la implementación de P6.2; usa sus tipos públicos.

### P6.4 — Registro de batallas

- seleccionar participantes;
- validar disponibilidad pre-battle;
- registrar resultado y recompensas;
- crear el trabajo post-battle pendiente;
- conservar payloads abiertos sin interpretarlos de forma destructiva.

**Depende de:** P3.5, P4.3 y P5.1.

### P6.5 — Injuries y recuperación

- resolver resultados de heridas;
- actualizar fuera de acción y recuperación;
- aplicar las restricciones correspondientes;
- probar estados pendientes y reanudables.

**Depende de:** P6.4 y las interfaces de post-battle.  
**Puede empezar con fixtures de `pending-post-battle.json`.

### P6.6 — Experiencia y avances

- listar avances pendientes;
- aplicar una elección válida;
- rechazar avances incompatibles;
- actualizar el snapshot del warrior y exportar el resultado.

**Depende de:** P6.4 y P4.3.  
**Puede ejecutarse en paralelo con P6.5 si ambos consumen resultados inmutables.

### P6.7 — Hirelings, exploración, búsquedas y comercio

- resolver elegibilidad de hirelings;
- contratar o rechazar contratación;
- modelar búsquedas, recompensas y comercio que estén dentro del alcance
  actual;
- conservar reglas o payloads no interpretados cuando el contrato lo exija.

**Depende de:** P4.3, P3.5 y P5.1.  
**Puede dividirse internamente en subramas, siempre que hirelings y
exploración/comercio no editen los mismos archivos.

### P6.8 — Revisión final y exportaciones auxiliares

- revisar el estado completo antes de commit;
- exportar el fichero principal validado;
- preparar exportaciones auxiliares permitidas por el alcance;
- comprobar que ningún exportador introduce reglas en la persistencia.

**Depende de:** todos los bloques funcionales que sean necesarios para el
primer release.

---

## 8. Fase 7: calidad e interoperabilidad en paralelo

Estas tareas pueden ejecutarse mientras se completan los bloques funcionales,
pero sus pruebas de integración se cierran después de P6.

### P7.1 — Round-trip bidireccional

**Objetivo:** probar Python → TypeScript → Python y TypeScript → Python →
TypeScript.

Debe cubrir draft, campaña activa, post-battle pendiente e inventario
completo. La comparación debe ser semántica y excluir únicamente los campos
volátiles documentados.

### P7.2 — Casos corruptos y referencias

Añadir documentos con campos ausentes, tipos incorrectos, propiedades
inesperadas, IDs desconocidos, payload incompleto y versiones no soportadas.
Los errores deben ser estables, accionables y no revelar trazas internas a la
UI.

### P7.3 — Arquitectura y bundle

Comprobar automáticamente que:

- dominio no importa React ni APIs del navegador;
- UI no carga YAML directamente;
- persistencia no contiene reglas de negocio;
- el bundle no incluye Combat Lab, NumPy, Cython ni Tkinter;
- no se usa localStorage/IndexedDB para campañas.

### P7.4 — Accesibilidad y pantallas pequeñas

Revisar teclado, foco, labels, mensajes de error, contraste, tablas y
navegación en viewport reducido. Esta tarea debe usar la aplicación real, pero
no debe cambiar los contratos de dominio.

### P7.5 — Rendimiento del artefacto KB

Medir tamaño comprimido, tiempo de carga y coste de indexación. Si se requiere
particionar catálogos, proponerlo como cambio de arquitectura separado y no
modificar simultáneamente la semántica de las consultas.

P7.1, P7.2, P7.3, P7.4 y P7.5 son paralelizables entre sí cuando existe una
build funcional mínima.

---

## 9. Fase 8: CI y GitHub Pages

### P8.1 — Workflow de validación y publicación

**Propietario único:** CI/CD.  
**Archivos principales:** `.github/workflows/` y documentación de despliegue.

**Instrucciones:**

1. Instalar dependencias Python y web de forma reproducible.
2. Validar KB y contrato antes del build.
3. Ejecutar tests Python relevantes y tests TypeScript.
4. Generar el artefacto JSON de KB.
5. Ejecutar `vite build`.
6. Publicar únicamente `dist/`.
7. Configurar la base de Vite para el nombre del repositorio.
8. Usar hash routing inicialmente.
9. No incluir ficheros de campaña de usuarios en el artefacto publicado.

**Criterio de aceptación:** un build limpio desde checkout reproduce la
aplicación y un fallo de contrato, KB, tests o build impide publicar.

**Dependencias:** P4.2, P5.2 y una versión acordada de los tests TypeScript.

**Paralelización:** puede preparar el workflow con stubs mientras se terminan
las features, pero la activación de publicación es una decisión del
integrador después de P7.

---

## 10. Fase 9: renombrado de namespaces

### P9.1 — Inventario y propuesta de nombres finales

Identificar imports provisionales y proponer nombres por responsabilidad, no
por repetición del nombre del producto. La propuesta se revisa antes de tocar
código.

### P9.2 — Renombrado Python

Actualizar paquetes, imports, entry points, tests y documentación. Mantener
fachadas de compatibilidad si hay consumidores externos.

### P9.3 — Renombrado TypeScript

Actualizar nombres de paquetes y paths internos solo si la nomenclatura
provisional quedó obsoleta.

### P9.4 — Retirada de fachadas

Eliminar las fachadas únicamente después del periodo de compatibilidad
acordado y con todos los consumidores internos migrados.

P9.1 debe ser serial. P9.2 y P9.3 pueden ejecutarse en paralelo únicamente si
sus namespaces y archivos de configuración no se solapan. P9.4 es siempre la
última tarea.

---

## 11. Orden recomendado de integración

1. **G0:** checkpoint de las fases 0–2 y ejecución de la regresión Python.
2. **P3.1:** workspace mínimo.
3. **P3.2 + P3.4:** adaptador v4 e interfaces públicas.
4. **P4.1 → P4.2 → P4.3:** artefacto e índices de KB.
5. **P3.3 + P3.5:** harness de contrato y kernel de dominio.
6. **P5.1:** aplicación en memoria.
7. **P5.2:** vertical slice importación → edición → exportación.
8. **P6.1–P6.7:** bloques funcionales en paralelo; integrar cada uno con sus
   pruebas antes del siguiente bloque dependiente.
9. **P6.8:** revisión y exportaciones auxiliares.
10. **P7.1–P7.5:** calidad e interoperabilidad en paralelo.
11. **P8.1:** habilitar CI y publicación.
12. **P9.1–P9.4:** renombrar namespaces cuando la migración funcional esté
    estable.

Si el equipo es pequeño, P4.1, P7.2 o P7.5 pueden ejecutarse como tareas de
preparación mientras otro agente implementa el bloque principal; no deben
bloquear la creación de interfaces ni introducir cambios funcionales ocultos.

---

## 12. Protocolo de integración por tarea

Antes de abrir una solicitud de integración, el propietario debe:

- describir archivos modificados y contratos consumidos;
- indicar qué tarea desbloquea o qué tarea necesita;
- ejecutar tests unitarios del bloque;
- ejecutar la validación del contrato si toca persistencia;
- ejecutar la regresión Python si toca el código compartido;
- comprobar que no hay imports prohibidos;
- incluir fixture o test de comportamiento cuando corresponda;
- verificar que no se han incluido datos de usuario, secretos ni artefactos
  generados no versionables.

El integrador debe fusionar en este orden:

1. interfaces y tipos;
2. adaptadores puros;
3. dominio;
4. aplicación;
5. UI;
6. CI/publicación.

Después de cada integración de una dependencia importante, ejecutar como mínimo:

```text
python -m pytest tests/campaign tests/architecture tests/contracts -q

# En el workspace TypeScript:
npm test
npm run build
```

El comando TypeScript debe sustituirse por el package manager y scripts
oficiales del workspace si no se usa npm. No cambiar de package manager dentro
de una tarea.

---

## 13. Definition of Done común

Una tarea paralela está terminada cuando:

- su alcance está limitado a la responsabilidad asignada;
- sus APIs públicas están documentadas;
- no depende de UI, navegador o filesystem si pertenece a dominio/aplicación;
- sus tests son deterministas y ejecutables sin una sesión manual;
- los fixtures compartidos se leen desde `contracts/`;
- no duplica reglas ni datos de `sources/knowledge/`;
- no rompe las fachadas Python existentes;
- pasa lint, typecheck, tests y build aplicables;
- deja explícitas sus limitaciones y dependencias restantes.

Una feature funcional no se considera terminada si solo tiene componentes
visuales: debe incluir la operación de dominio, la orquestación, la
serialización cuando aplique y las pruebas de interoperabilidad.

---

## 14. Matriz resumida de paralelización

| ID | Trabajo | Dependencias | Puede ir en paralelo con |
| --- | --- | --- | --- |
| G0 | Checkpoint Phase 0–2 | — | — |
| P3.1 | Workspace React/Vite | G0 | P4.1, diseño P3.4 |
| P3.2 | Adaptador `.mordheim` TS | P3.1/schema | P4.1, P3.4 |
| P3.3 | Tests de contrato | P3.2 | P4.2, P3.5 |
| P3.4 | Interfaces TS | G0 | P3.1, P4.1 |
| P3.5 | Kernel de dominio | P3.4 | P4.2, P5.1 con fake |
| P4.1 | Inventario KB | G0 | P3.1–P3.4 |
| P4.2 | Generador KB | P4.1 | P3.3, P3.5 |
| P4.3 | Índices/query KB | P4.2, P3.4 | P3.3, P3.5 |
| P5.1 | Application service | P3.2, P3.4, P3.5 | P5.2 con fake |
| P5.2 | Primer vertical slice | P3.1, P3.2, P4.3, P5.1 | preparación P6 |
| P6.1–P6.7 | Bloques funcionales | kernel + aplicación | Entre sí, sin solapamiento |
| P6.8 | Revisión/exportaciones | bloques necesarios | P7.1–P7.5 parcialmente |
| P7.1–P7.5 | Calidad | build funcional | Entre sí |
| P8.1 | CI/Pages | generador + build | P7 preparación |
| P9.1 | Propuesta namespaces | funcionalidad estable | — |
| P9.2–P9.3 | Renombrados | P9.1 | Entre sí solo con ownership disjunto |
| P9.4 | Retirar fachadas | P9.2, P9.3 | — |

---

## 15. Criterio global de éxito

La estrategia paralela se considera exitosa cuando:

- cada bloque funcional puede revisarse y revertirse de forma independiente;
- Python y TypeScript consumen el mismo contrato v4 y fixtures;
- la KB se genera desde una única fuente canónica;
- la web importa, edita y exporta campañas sin persistencia automática;
- el dominio web permanece independiente de React y del navegador;
- los tests de Campaign Manager siguen verdes;
- CI bloquea builds inválidos y publica solo una build reproducible;
- el renombrado de namespaces se realiza al final, sin bloquear el port
  funcional ni mezclarlo con cambios de reglas.

La prioridad de integración es preservar el contrato y el comportamiento
existente. Ante un conflicto entre velocidad de paralelización y una decisión
ambigua de dominio, se detiene la tarea dependiente, se fija la interfaz y se
reanuda el trabajo con un cambio pequeño y revisable.
