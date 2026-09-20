# Plan de ingesta de Grade 2b (Supplemental)

Este documento define el procedimiento para incorporar las bandas que Broheim clasifica
como **Grade 2b (Supplemental)** sin modificar la KB activa hasta que la ingesta completa
haya sido revisada, traducida y validada.

La fuente de alcance es la página de Broheim:

- <https://broheim.net/warbands.html>

En la fecha de elaboración, la categoría contiene 60 entradas. El inventario debe tratarse
como una fotografía revisable: si Broheim cambia el listado, el cambio se registra como una
nueva revisión del inventario y no se mezcla silenciosamente con el trabajo en curso.

## 1. Principios obligatorios

1. `sources/knowledge/` es la KB activa y no debe tocarse durante el staging.
2. `sources/2B/` es un área de trabajo aislada, no una colección consumida por la aplicación.
3. Los PDFs no se versionan en Git. Se mantienen en una caché local ignorada y se registra
   su URL, nombre y SHA-256.
4. La transcripción se hace desde el PDF, no desde nombres, snippets de buscador ni reglas
   parecidas de otra banda.
5. No se inventan valores ilegibles o ausentes. Se registra una incidencia y la banda queda
   bloqueada hasta resolverla.
6. Las bandas con el mismo nombre y suplementos diferentes son registros distintos.
7. Inglés es el texto canónico inicial. La promoción exige después traducción española
   completa y revisada.
8. Una regla no implementada por el motor se conserva igualmente, pero debe clasificarse
   explícitamente como `NO` o `LATER` con un motivo.

## 2. Estructura de staging

La estructura debe imitar el formato de la KB existente:

```text
sources/2B/
├── README.md                         este documento
├── manifest.yaml                     inventario Broheim + estado de cada PDF/banda
├── registry/
│   └── collections.yaml              metadatos mínimos del staging
├── bands/
│   └── mordheim/
│       └── <band-id>/
│           ├── band.yaml
│           ├── profiles.yaml
│           ├── equipment-access.yaml
│           └── special-rules.yaml
└── catalog/
    ├── items/                        objetos nuevos aún no promovidos
    ├── skills/                       habilidades nuevas aún no promovidas
    └── rules/                        reglas compartidas candidatas, tras revisión
```

Cada paquete de banda debe tener los cuatro YAML. La ausencia de un documento no significa
que la información no exista: significa que la transcripción está incompleta y no se puede
marcar la banda como promocionable.

El staging usa `ruleset: mordheim`, `grade: 2b` y los mismos contratos de datos que la KB
activa, pero los loaders normales no deben descubrirlo mientras permanezca en `sources/2B`.

## 3. Fases y estados

Cada banda debe avanzar por estos estados, en orden:

```text
discovered
  → pdf-verified
  → text-extracted
  → modeled
  → english-reviewed
  → translated
  → validated
  → promotable
```

Si aparece una duda, se conserva el estado anterior y se añade un bloqueo en el manifiesto.
Nunca se salta un estado solo para hacer que el contador avance.

### 3.1 `discovered`

Registrar todas las filas de Grade 2b en `manifest.yaml` con:

- identificador provisional estable;
- nombre exacto de Broheim;
- raza o categoría publicada;
- código de suplemento (`KAZ`, `SAR`, `MOU`, etc.);
- URL de la página de Broheim;
- URL del PDF individual cuando se haya resuelto;
- estado actual;
- notas de desambiguación.

Las dos entradas de igual nombre pero diferente fuente deben tener dos IDs diferentes.
Ejemplo conceptual:

```yaml
- id: skaven-clan-pestilens-mou
  broheim_name: Skaven of Clan Pestilens
  race: Skaven
  grade: 2b
  source_code: MOU
  pdf_url: https://broheim.net/...
  sha256: null
  status: discovered
  blockers: []
```

El ID provisional puede revisarse antes de `modeled`, pero después de crear referencias en
los YAML debe considerarse estable.

#### Una fila de manifiesto, varias bandas

Una fila describe **un documento fuente**, no necesariamente una banda. Cuando el PDF
imprime más de una lista de banda (cada una con su roster, listas de equipo y reglas
propias), la fila declara todos los paquetes que produjo:

```yaml
- id: orc-pirates-sar            # paquete primario (el que da nombre a la fila)
  broheim_name: Orc Pirates & Savage Orcs
  packages:
  - orc-pirates-sar
  - savage-orcs-sar
```

Reglas de uso:

- sin `packages`, la fila produce exactamente un paquete, `sources/2B/bands/mordheim/<id>`;
- con `packages`, la lista debe incluir el propio `id` y cada entrada debe tener los cuatro
  documentos;
- `ingest_2b.py validate` y `tests/knowledge/test_2b_staging.py` fallan si existe un paquete
  en el árbol que ninguna fila declare;
- no se crean varias filas para la misma pareja `broheim_name` + `source_code`: el
  inventario contra Broheim es 1:1.

Justificación: el motor no puede variar el roster por variante (una entrada `variants`
sólo aporta `rule_ids`, `starting_gold` y `profile_bonuses`), así que dos listas con
composiciones distintas son dos bandas hermanas con el mismo `canonical_family`.

### 3.2 `pdf-verified`

Descargar el PDF en una caché local, por ejemplo:

```text
build/cache/2b-pdfs/<manifest-id>.pdf
```

La caché no debe entrar en Git. Para cada archivo:

1. comprobar que la respuesta es realmente un PDF;
2. guardar el nombre original y el tamaño;
3. calcular SHA-256;
4. escribir el hash en `manifest.yaml`;
5. registrar si el PDF es texto seleccionable o requiere OCR;
6. conservar cualquier redirección o URL alternativa.

Si el contenido descargado cambia, no se sobrescribe silenciosamente: se registra un cambio
de hash y se decide si abre una nueva revisión del inventario.

### 3.3 `text-extracted`

Extraer el texto conservando el layout y las tablas tanto como sea posible. El resultado de
la extracción es un artefacto local de trabajo, no la fuente canónica ni un sustituto de la
revisión visual del PDF.

Para cada banda revisar visualmente, como mínimo:

- encabezados y secciones;
- tablas de perfiles;
- límites mínimos y máximos;
- costes y experiencia;
- listas de equipo;
- reglas con porcentajes, rangos, tiradas o excepciones;
- notas al pie y texto que continúe en otra página.

Si el PDF está escaneado, marcar `ocr-required` y comprobar manualmente cada valor extraído.

### 3.4 `modeled`

Crear los cuatro documentos de banda siguiendo los ejemplos existentes en
`sources/knowledge/bands/mordheim/`.

`band.yaml` debe contener, como mínimo:

- `schema_version: 2`;
- `id`, `canonical_family`, `name`, `original_locale` y `ruleset`;
- `categories: [2b]` y `grade: 2b`;
- `setting`, `publication`, `status`;
- fuente y URL del PDF;
- `roster` con mínimos, máximos, oro inicial y miembros;
- `rule_ids` y variantes si el documento las declara.

`profiles.yaml` debe capturar cada héroe y secuaz con:

- ID estable, nombre, tipo, coste y experiencia;
- características tal como aparecen en la fuente;
- listas de equipo, equipo fijo y restricciones;
- acceso a habilidades;
- reglas propias del perfil;
- `source`, `source_path` y página/sección del PDF.

`equipment-access.yaml` debe conservar las listas y los costes publicados para la creación de
la banda. Esos costes no se deben reemplazar automáticamente por los precios del Trading
Post: son datos de origen diferentes.

`special-rules.yaml` debe incluir el texto completo y fiel de cada regla, su ámbito de
aplicación y su clasificación runtime. No mover una regla a un catálogo compartido solo por
coincidencia de nombre.

### 3.5 `english-reviewed`

Una segunda revisión independiente debe comparar cada YAML con el PDF y confirmar:

- que todos los perfiles del roster existen;
- que no hay perfiles transcritos pero ausentes del roster sin justificación;
- que los valores numéricos coinciden;
- que se conservaron excepciones y notas;
- que cada regla tiene el texto completo;
- que cada `source` apunta a una página o sección verificable;
- que los IDs no dependen de errores tipográficos del PDF.

El revisor debe anotar dudas concretas en el manifiesto, no corregir silenciosamente el PDF
según una interpretación de otra edición.

### 3.6 `translated`

Traducir y revisar todos los campos de usuario:

- nombre de la banda;
- nombres de perfiles;
- nombres de reglas;
- efectos de reglas;
- nombres y efectos de objetos o habilidades nuevos.

Usar el vocabulario existente en `sources/knowledge/catalog/translation-glossary.md`.
El inglés permanece en `name` y `effect`; el español va en `name_i18n.es` y
`effect_i18n.es`. No añadir bloques `en` duplicados.

La traducción no debe alterar IDs, números, rangos, pulgadas, modificadores, nombres de
habilidades referenciadas ni condiciones de las reglas.

### 3.7 `validated` y `promotable`

Una banda solo puede pasar a `promotable` cuando:

- el PDF y su hash están registrados;
- los cuatro YAML existen;
- la revisión inglesa está completada;
- la traducción española está completa y revisada;
- todas las referencias internas resuelven;
- el formato YAML es canónico;
- la clasificación runtime es válida;
- no quedan bloqueos abiertos.

## 4. Modelado de reglas runtime

El motor actual cubre principalmente combate cuerpo a cuerpo. La ingesta no debe eliminar
reglas fuera de ese ámbito.

Clasificación recomendada:

- `scope: YES`, `implemented: YES`: solo cuando existe una binding ejecutable y validada;
- `scope: NO`, `implemented: NO`: reglas de disparo, campaña, magia u otros ámbitos
  explícitamente fuera del runtime actual;
- `scope: LATER`, `implemented: NO`: psicología, movimiento, monturas o subsistemas
  aplazados.

Las reglas no implementadas deben incluir una razón, por ejemplo:

```yaml
runtime:
  scope: LATER
  implemented: 'NO'
  grant: profile
  effects:
  - id: unimplemented.<band-id>.<profile-id>.<slug>
    scope: LATER
    binding: null
    reason: >-
      Deferred subsystem: psychology.
```

Una binding `YES` inventada para hacer pasar la validación es un error de ingesta.

## 5. Objetos, habilidades y reglas compartidas

Antes de crear un registro nuevo, buscar el ID canónico correspondiente en la KB activa.

- Si el objeto ya existe, reutilizar su `item_id`.
- Si es nuevo, crearlo temporalmente en `sources/2B/catalog/items/`.
- Si la habilidad ya existe, reutilizar su ID.
- Si es nueva, crearla temporalmente en `sources/2B/catalog/skills/`.
- Mantener inicialmente las reglas especiales dentro de cada banda.
- Promover una regla al catálogo compartido solo después de comprobar equivalencia textual
  y semántica entre las fuentes.

Durante el staging, las referencias a catálogos existentes deben resolverse contra una copia
conocida de la KB activa o mediante un validador que combine ambas raíces sin modificar la
activa. Los registros provisionales no deben quedar ocultos por IDs coincidentes.

## 6. Validaciones obligatorias

Antes de promocionar, ejecutar estas comprobaciones disponibles actualmente:

```text
python tools/format_yaml.py --check sources/2B
python tools/normalize_names.py --check sources/2B
python tools/knowledge/audit_2b.py            # re-verificación contra los PDFs de origen
python tools/knowledge/audit_kb_conformance.py --tree 2B
python -m pytest tests/knowledge -q
```

### Verificación contra fuentes

`tools/knowledge/audit_2b.py` contrasta cada paquete con el PDF que lo originó: nombres y
costes de perfil, experiencia inicial, composición del roster, oro inicial, y nombre y precio
de **cada** fila de equipo. Evalúa dos formas de extracción por documento (texto cacheado y
`pdftotext -layout`), reconoce las divisas de cada suplemento y contrasta las listas que el
documento remite al reglamento con la transcripción de esa misma lista en la KB. Su salida es
un informe JSON; `problem_count` debe ser 0 antes de promocionar. Los veredictos que la
herramienta aplica (redacción impresa distinta del nombre canónico, filas adjudicadas a mano,
listas delegadas al reglamento) están declarados en el propio fichero con su motivo, y
resumidos en `discrepancy-verdicts.md` con la evidencia de cada caso.

Además, la herramienta de staging que se implemente como parte de este plan deberá exponer
al menos estas operaciones:

```text
python tools/knowledge/ingest_2b.py report
python tools/knowledge/ingest_2b.py validate
```

El informe de traducción existente (`tools/band_translation_status.py`) actualmente está
ligado a la KB activa y no debe usarse sobre 2B hasta que acepte una raíz explícita. Durante
el staging se debe consultar el estado mediante el informe específico de 2B o mediante un
script equivalente que reciba `sources/2B` como argumento.

El validador de 2B debe comprobar además:

- que el manifiesto contiene exactamente las entradas previstas;
- que cada entrada tiene un PDF y SHA-256;
- que cada entrada tiene exactamente un paquete de banda;
- que los IDs de bandas, perfiles, reglas y objetos no colisionan indebidamente;
- que los perfiles del roster existen;
- que `rule_ids` y `item_id` resuelven;
- que las listas de equipo son válidas;
- que todos los runtime blocks cumplen el contrato existente;
- que ninguna herramienta de la aplicación lee `sources/2B` accidentalmente;
- que la KB activa no ha cambiado como consecuencia de la validación.

Las herramientas de formato y traducción deben recibir explícitamente `sources/2B`; no usar
un valor por defecto que pueda modificar `sources/knowledge` durante el staging.

## 7. Promoción final a la KB activa

La promoción debe ser una operación separada, revisada y explícita. No se realiza por cada
banda individual mientras el catálogo esté incompleto.

Checklist de promoción:

1. Confirmar que las 60 entradas del manifiesto están en `promotable`.
2. Revisar el diff completo de `sources/2B`.
3. Comparar IDs nuevos con la KB activa.
4. Copiar las bandas a `sources/knowledge/bands/mordheim/`.
5. Copiar solo los objetos, habilidades y reglas compartidas aprobados.
6. Añadir o actualizar fuentes y aliases del registro.
7. Auditar `warband-groups.yaml` para las nuevas razas, facciones y alineamientos.
8. Regenerar el artefacto web desde la KB activa.
9. Ejecutar tests de conocimiento, construcción, campaña y web.
10. Verificar que no se han añadido PDFs ni artefactos temporales al diff.

La aplicación no debe incorporar una ruta especial para `sources/2B`. Tras la promoción, las
bandas deben aparecer por el mismo flujo que las existentes y el artefacto web debe generarse
solo desde `sources/knowledge`.

## 8. Informe de progreso

El informe debe mostrar, por banda:

```text
ID                         PDF  Inglés  Español  Validación  Bloqueos
adventurers-kaz            OK   OK      OK       OK          -
araby-smugglers-sar        OK   OK      --       --          falta traducción
blood-dragons-mou          OK   --      --       --          revisar tabla de perfiles
```

También debe mostrar totales por estado y por suplemento. Una entrada con dudas no se cuenta
como completa aunque sus cuatro YAML existan.

## 9. Criterio de finalización

La fase de staging termina cuando:

- las 60 filas de Broheim están inventariadas;
- cada PDF está identificado y verificado por hash;
- cada banda tiene una transcripción inglesa revisada;
- cada banda tiene traducción española revisada;
- todas las validaciones pasan sobre `sources/2B`;
- no hay referencias sin resolver ni bloqueos abiertos;
- `sources/knowledge` permanece sin cambios atribuibles al staging;
- existe un diff de promoción explícito y revisado.

Hasta entonces, `sources/2B` es una fuente de trabajo y no debe ser usada para crear
campañas reales ni para regenerar el catálogo publicado de la aplicación.
