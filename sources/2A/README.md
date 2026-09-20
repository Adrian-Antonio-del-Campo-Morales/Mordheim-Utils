# Plan de ingesta de Grade 2a (Fan-tested)

Este documento define el procedimiento para incorporar las bandas que Mordheimer's
Information Centre clasifica como **Grade 2a** ("Reliable, created and tested by fans
and gaming groups") sin modificar la KB activa hasta que la ingesta completa haya sido
revisada, traducida y validada.

El plan es una adaptación del plan de Grade 2b (`sources/2B/README.md`), ya ejecutado
con éxito, a las particularidades de esta categoría. Los principios, los estados y el
formato de los paquetes son idénticos; lo que cambia es la **fuente de alcance**, la
**naturaleza heterogénea de los documentos fuente** y las **reglas de desambiguación**
frente a las otras categorías.

La fuente de alcance es la página de bandas de Mordheimer:

- <https://mordheimer.net/docs/warbands> (sección "Grade 2a")

**Verificado (2026-09-14): todas las bandas de la categoría tienen una página dedicada
con las reglas completas** en

- <https://mordheimer.net/docs/warbands/grade-2a-warbands/<slug>>

cada una con lore, reglas especiales, choice of warriors, perfiles, experiencia, tabla
de habilidades y listas de equipo. La página dedicada es el **documento primario de
transcripción**; los PDFs de procedencia que las propias páginas citan
(`Source: Druchii.net (PDF)`, `Mordheim Italia PDF`, `Sylvania Supplement`, ...) se
descargan como documentos de contraste cuando están localizables.

En la fecha de elaboración, la categoría contiene **19 entradas** y las 19 slugs
responden HTTP 200. El inventario debe tratarse como una fotografía revisable: si la
página cambia el listado, el cambio se registra como una nueva revisión del inventario
y no se mezcla silenciosamente con el trabajo en curso.

### Discrepancias índice ↔ página (registradas, no resueltas en silencio)

Dos páginas declaran en su cabecera un grado distinto al del índice que las lista bajo
Grade 2a:

- `snotlings` — la página dice **"Grade: 2b"**, el índice la lista en 2a.
- `order-of-the-mare` — la página dice **"Grade: Heroic"** (Setting: Bretonnia /
  Mordheim), el índice la lista en 2a.

Política: el alcance de esta ingesta es el listado del índice (las 19 bandas se ingieren
como 2a), pero la discrepancia se conserva en el manifiesto (`page_grade` vs `grade: 2a`)
y en las notas, y se resuelve explícitamente antes de `promotable`.

## 0. Inventario de las 19 bandas (fotografía 2026-09-14)

| # | Band | Slug (página dedicada) | Race | Setting | Source declarado |
|---|------|------------------------|------|---------|------------------|
| 1 | Dreamwalkers, Cult Of Morr | `dreamwalkers-cult-of-morr` | Human | Mordheim | Mordheim Facebook Group |
| 2 | Druchii | `druchii` | Dark Elf | Mordheim | Druchii.net (PDF) |
| 3 | Dwarf Slayer Cult | `dwarf-slayer-cult` | Dwarf | Mordheim | Dave 'Styrofoam King' Joria |
| 4 | Grave Robbers | `grave-robbers` | Human | Sylvania | Sylvania Supplement |
| 5 | Halflings | `halflings` | Halfling | Mordheim | Mordheimer's Information Centre |
| 6 | Masters Of Horror | `masters-of-horror` | Universal Monsters | Sylvania | Sylvania Supplement |
| 7 | Mazzalupo | `mazzalupo` | Human | Mordheim | Mordheim Italia PDF (V3.5) |
| 8 | Necrarchs, the Soul Stealers | `necrarchs-the-soul-stealers` | Undead | Sylvania | Letters of the Damned #1 |
| 9 | Nipponese Expedition | `nipponese-expedition` | Human | Mordheim | WEB |
| 10 | Ogre Hunting Party | `ogre-hunting-party` | Ogre/Gnoblar | Mordheim | Seidman-Joria & Catferret |
| 11 | Order Of The Mare | `order-of-the-mare` | Human | Bretonnia / Mordheim | Fredrik Edman (página: "Grade: Heroic") |
| 12 | Outlaws of Stirwood Forest, Redux | `outlaws-of-stirwood-forest-redux` | Human | Mordheim | Mordheim Facebook Group |
| 13 | Protectorate Of Sigmar | `protectorate-of-sigmar` | Human | Mordheim | Letters of the Damned #3 |
| 14 | Skaven of Clan Moulder | `skaven-of-clan-moulder` | Skaven | Mordheim | WEB (página cita PDF) |
| 15 | Snotlings | `snotlings` | Snotling | Mordheim | Roberts & Seidman-Joria (página: "Grade: 2b") |
| 16 | Sorcerous Society | `sorcerous-society` | Human Wizard | Mordheim | Letters of the Damned #4 |
| 17 | Survivors Of Strigos | `survivors-of-strigos` | Vampire | Sylvania | Brahm Tazoul (PDF) |
| 18 | Vampire Hunters of Sylvania | `vampire-hunters-of-sylvania` | Human | Sylvania | Letters of the Damned #5 |
| 19 | Wood Elves of Athel Loren | `wood-elves-of-athel-loren` | Wood Elf | Mordheim | WEB |

Las slugs son las URLs reales verificadas (19/19 HTTP 200); las columnas Race/Setting/
Source mezclan el índice con los metadatos declarados en cada página dedicada.

## 1. Principios obligatorios

Idénticos a los del plan 2B (sección 1 de `sources/2B/README.md`), con estas
adaptaciones específicas de 2A:

1. `sources/knowledge/` es la KB activa y no debe tocarse durante el staging.
2. `sources/2A/` es un área de trabajo aislada, no una colección consumida por la
   aplicación. **Tampoco debe leerse `sources/2B/` en tiempo de ejecución**; es
   staging hermano, no catálogo.
3. Los documentos fuente no se versionan en Git. Se mantienen en una caché local
   ignorada y se registran su URL, nombre y SHA-256. Esto aplica tanto a PDFs como
   a las **instantáneas HTML de las páginas dedicadas** (ver §3.2).
4. La transcripción se hace desde el documento fuente, no desde nombres, snippets de
   buscador ni reglas parecidas de otra banda o de otra categoría.
5. No se inventan valores ilegibles o ausentes. Se registra una incidencia y la banda
   queda bloqueada hasta resolverla.
6. **Desambiguación entre categorías.** Varias bandas de 2A conviven con bandas de
   igual o parecido nombre en otras categorías y en el staging 2B. Son registros
   distintos salvo evidencia textual contraria; ejemplos que NO deben fusionarse:
   - `Outlaws of Stirwood Forest, Redux` (2A) vs `Outlaws of Stirwood Forest` (1b);
   - `Necrarchs, the Soul Stealers` (2A, LotD #1) vs `necrarchs-mou` (2B, Mousillon);
   - `Survivors Of Strigos` (2A, Sylvania) vs `strigoi-kaz` (2B, Karak Azgal);
   - `Wood Elves of Athel Loren` (2A) vs `wood-elves-of-arden-mou` (2B);
   - `Halflings` (2A) vs `Mootlanders` (1b) y `militiant-mootlanders-mim` (2B).
   Los IDs llevarán siempre el sufijo de fuente para impedir colisiones.
7. Inglés es el texto canónico inicial. La promoción exige después traducción española
   completa y revisada.
8. Una regla no implementada por el motor se conserva igualmente, pero debe clasificarse
   explícitamente como `NO` o `LATER` con un motivo.
9. **Objetos compartidos con 2B.** Si una banda 2A necesita un objeto que ya existe en
   la KB activa, se reutiliza su `item_id`. Si solo existe como provisional en
   `sources/2B/catalog/items/`, **no se duplica**: se referencia el ID provisional y se
   anota en `sources/2A/promotion-merge-notes.md` para que la promoción (2A, 2B o ambas)
   lo materialice una sola vez en la KB.

## 2. Estructura de staging

Idéntica a la de 2B, con su propia raíz:

```text
sources/2A/
├── README.md                         este documento
├── manifest.yaml                     inventario mordheimer.net + estado de cada fuente/banda
├── registry/
│   └── collections.yaml              metadatos mínimos del staging
├── bands/
│   └── mordheim/
│       └── <band-id>/
│           ├── band.yaml
│           ├── profiles.yaml
│           ├── equipment-access.yaml
│           └── special-rules.yaml
├── catalog/
│   ├── items/                        objetos nuevos aún no promovidos
│   ├── skills/                       habilidades nuevas aún no promovidas
│   └── rules/                        reglas compartidas candidatas, tras revisión
└── promotion-merge-notes.md          notas de fusión con KB y con staging 2B
```

Cada paquete de banda debe tener los cuatro YAML. La ausencia de un documento significa
que la transcripción está incompleta y no se puede marcar la banda como promocionable.

El staging usa `ruleset: mordheim`, **`grade: 2a` y `categories: [2a]`**, y los mismos
contratos de datos que la KB activa. Los loaders normales no deben descubrirlo mientras
permanezca en `sources/2A`.

## 3. Fases y estados

Misma máquina de estados que 2B, generalizada a fuentes web:

```text
discovered
  → source-verified        (equivale a pdf-verified en 2B)
  → text-extracted
  → modeled
  → english-reviewed
  → translated
  → validated
  → promotable
```

### 3.1 `discovered`

Registrar las 19 filas de Grade 2a en `manifest.yaml` con:

- identificador provisional estable (`<nombre>-<fuente>`, p. ej. `grave-robbers-sylv`,
  `necrarchs-lotd1`, `wood-elves-athel-web`);
- nombre exacto de la página;
- **slug de la página dedicada** (verificado: `druchii`, `halflings`, `snotlings`, ...);
- raza y ambientación publicadas (índice) y las declaradas en la página (`Setting`,
  `Version`);
- código de fuente (`SYLV`, `LOTD1`, `LOTD3`, `LOTD4`, `LOTD5`, `MIC`, `FBG`, `WEB`,
  `JORIA`, `ITALIA`);
- `page_grade`: el grado que declara la propia página (`2a`, `2b`, `Heroic`) para
  registrar las discrepancias del índice;
- URL de la página dedicada y URL de la página de alcance;
- `source_kind: page | pdf` para el documento primario (siempre `page` en 2A) y URL del
  PDF de procedencia cuando se localice;
- estado actual y notas de desambiguación.

### 3.2 `source-verified` (resolución y verificación de la fuente)

Aquí está la **mayor diferencia con 2B**: en 2B el documento primario era el PDF;
en 2A el documento primario es la **página dedicada de cada banda** en mordheimer.net
(verificadas: las 19 slugs existen bajo `grade-2a-warbands/` y contienen las reglas
completas). El flujo de verificación es:

1. **Instantánea de la página dedicada** (documento primario). El descubridor descarga
   el HTML crudo de cada página a la caché, le calcula SHA-256 y lo registra en el
   manifiesto. De la página se extraen además los metadatos declarados: `Grade`,
   `Source`, `Setting`, `Version` (p. ej. Mazzalupo declara "V3.5") y los enlaces al
   PDF de procedencia cuando la página los cita.
2. **PDFs de procedencia (contraste).** Varias páginas citan su PDF original
   (`Druchii.net (PDF)`, `Mordheim Italia PDF`, `Sylvania Supplement`, `Letters of the
   Damned #N`, `Brahm Tazoul (PDF)`, el PDF de Clan Moulder, ...). Cuando el enlace es
   localizable y descargable, el PDF se guarda en caché, se hashea y se usa como
   **documento de contraste** para resolver ambigüedades del HTML (tablas rotas,
   glifos especiales, notas al pie). Si el PDF no está disponible, la página dedicada
   basta como fuente única y se anota la ausencia.
3. **Publicaciones multi-banda.** A diferencia de 2B, aquí cada banda tiene su página
   propia, por lo que no hay que partir documentos compartidos; las menciones a
   *Sylvania Supplement* y *Letters of the Damned* aparecen como `Source` declarado de
   cada página, no como documentos a reconstruir. No obstante, si durante el contraste
   se localiza el suplemento completo, puede guardarse una vez en caché (clave por URL
   normalizada) y anclar cada banda a su sección.

Regla general de procedencia: cada banda necesita **una** fuente primaria verificada
(la página dedicada). Las fuentes "WEB", "PDF" o de autor citadas en el índice no
exigen investigación adicional para poder transcribir — la página dedicada ya es el
documento —, pero sí se documentan en el manifiesto cuando se localizan, para el
contraste y para la promoción (`registry/sources.yaml`).

### 3.3 `text-extracted`

Igual que en 2B: extracción con layout conservado para PDFs; para páginas web,
extracción del texto del artículo (sin navegación ni comentarios). El resultado es un
artefacto local de trabajo, no la fuente canónica.

Revisión visual mínima por banda: encabezados y secciones, tablas de perfiles, límites,
costes y experiencia, listas de equipo, reglas con porcentajes/rangos/tiradas/excepciones,
notas al pie y texto que continúe en otra página.

Si la instantánea HTML presenta tablas rotas o caracteres problemáticos, se marca
`ocr-required`/`html-difficult` y se verifica manualmente cada valor contra el PDF de
procedencia o el render de la página (la experiencia de 2B con los PDFs de KEP —OCR a
300/600 dpi y recortes quirúrgicos— es el procedimiento de referencia).

### 3.4 `modeled`

Crear los cuatro documentos de banda exactamente con el contrato de 2B (sección 3.4 de
`sources/2B/README.md`), con dos diferencias:

- `band.yaml`: `categories: [2a]`, `grade: 2a`;
- `source.manual` debe nombrar la fuente real de la banda (`Sylvania Supplement`,
  `Letters of the Damned #4`, `mordheimer.net`, `Mordheim Facebook Group`, ...), no
  genéricamente "broheim.net".

### 3.5 `english-reviewed`

Igual que 2B (sección 3.5): segunda revisión independiente contra el documento fuente,
con verificación automatizada de todos los números mediante una herramienta de
verificación cruzada equivalente a `tools/knowledge/review_2b.py` (lecciones aprendidas:
interleave de marcadores de página, monedas no estándar, unidades gratuitas, fórmulas D6).

### 3.6 `translated`

Igual que 2B (sección 3.6): traducción española completa de nombres y efectos con el
vocabulario de `sources/knowledge/catalog/translation-glossary.md`, sin alterar IDs,
números, rangos ni condiciones. Oportunidad práctica detectada en 2B: si la i18n se
rellena desde el modelado, la revisión inglesa valida ambos idiomas a la vez.

### 3.7 `validated` y `promotable`

Mismos criterios que 2B (sección 3.7), con `format_yaml.py --check sources/2A` y
`normalize_names.py --check sources/2A`.

## 4. Modelado de reglas runtime

Idéntico a 2B (sección 4 de su README): `YES` solo con binding ejecutable validada;
`NO` para disparo, campaña, magia; `LATER` para psicología, movimiento, monturas;
razón explícita en cada efecto sin binding. Una binding `YES` inventada para hacer pasar
la validación es un error de ingesta.

El contrato `runtime-schema.yaml` de la KB es el mismo; el barrido final de 2B detectó
que la transcripción tiende a introducir scopes booleanos y `effects` descolocados: `ingest_2a.py validate` debe rechazar ambas desviaciones desde el primer
día (lección aprendida documentada en `sources/2B/completeness-sweep.md`).

## 5. Objetos, habilidades y reglas compartidas

Mismo procedimiento que 2B (sección 5 de su README) con el orden de resolución:

1. KB activa (`sources/knowledge/catalog/`) → reutilizar ID canónico.
2. Catálogo provisional de 2A (`sources/2A/catalog/`) → crearlo ahí.
3. Catálogo provisional de 2B (`sources/2B/catalog/items/`) → **no duplicar**: referenciar
   el ID provisional y anotarlo en `sources/2A/promotion-merge-notes.md`.
4. Reglas especiales: mantenerlas dentro de cada banda; enlazar con `rule_ref` solo tras
   equivalencia textual verificada (el revisor de 2B documentó el método y sus trampas en
   `sources/2B/rule-equivalence-review.md`; usarlo como manual de procedimiento).

## 6. Validaciones obligatorias

```text
python tools/format_yaml.py --check sources/2A
python tools/normalize_names.py --check sources/2A
python tools/knowledge/ingest_2a.py report
python tools/knowledge/ingest_2a.py validate
python -m pytest tests/knowledge/test_2a_staging.py
```

La herramienta `tools/knowledge/ingest_2a.py` se implementa adaptando `ingest_2b.py`:

- `discover`: parser de la tabla Grade 2a de mordheimer.net + construcción de la URL
  dedicada de cada banda a partir de su slug (patrón verificado:
  `docs/warbands/grade-2a-warbands/<slug>`) y verificación HTTP 200;
- `download`: igual que 2B pero a `build/cache/2a-sources/`, aceptando PDFs e HTML:
  descarga la página dedicada de cada banda (primaria) y los PDFs de procedencia
  citados (contraste), con deduplicación por URL;
- `extract`: extracción de texto PDF y de artículos HTML;
- `validate`: mismas comprobaciones estructurales que 2B + las endurecidas por las
  lecciones de 2B (scopes string-only, `effects` obligatorio dentro de `runtime`,
  `rule_ref` e `item_id` resolubles, aislamiento de la KB y de `sources/2B`);
- `report`: progreso por banda y por fuente.

`tests/knowledge/test_2a_staging.py` replica el aislamiento y los invariantes del
staging (misma batería que `test_2b_staging.py`, con la añadidura de que ninguna
herramienta lee `sources/2B` accidentalmente y viceversa).

## 7. Promoción final a la KB activa

Checklist equivalente al de 2B (sección 7 de su README):

1. Confirmar que las 19 entradas del manifiesto están en `promotable`.
2. Revisar el diff completo de `sources/2A`.
3. Comparar IDs nuevos con la KB activa **y con el staging 2B** (colisiones
   `necrarchs-*`, `strigos/strigoi`, `wood-elves-*`, `halflings/mootlanders`).
4. Copiar las bandas a `sources/knowledge/bands/mordheim/`.
5. Copiar solo los objetos, habilidades y reglas compartidas aprobados; ejecutar las
   notas de fusión de `promotion-merge-notes.md` (2A y las que apliquen de 2B) de forma
   que cada objeto materialice una sola entrada en la KB con todos sus `source_refs`.
6. Añadir o actualizar fuentes y aliases del registro: `mordheimer.net`,
   `Sylvania Supplement`, `Letters of the Damned #1/#3/#4/#5`, `Mordheim Facebook Group`,
   `Mordheimer's Information Centre`, fuentes WEB resueltas.
7. Auditar `warband-groups.yaml` para las nuevas razas y alineamientos
   (Universal Monsters, Vampire, Ogre/Gnoblar, Wood Elf).
8. Regenerar el artefacto web desde la KB activa.
9. Ejecutar tests de conocimiento, construcción, campaña y web.
10. Verificar que no se han añadido PDFs ni instantáneas HTML al diff.

## 8. Informe de progreso

Mismo formato que 2B, con la columna de fuente:

```text
ID                       Fuente  Doc  Inglés  Español  Validación  Bloqueos
grave-robbers-sylv       SYLV    OK   OK      OK       OK          -
druchii                  DRUC    OK   OK      --       --          falta traducción
order-of-the-mare        WEB     OK   --      --       --          page_grade="Heroic": resolver antes de promotable
```

Totales por estado y por código de fuente. Una entrada con dudas no se cuenta como
completa aunque sus cuatro YAML existan.

## 9. Criterio de finalización

- las 19 filas de mordheimer.net están inventariadas;
- cada fuente está identificada, descargada y verificada por hash
  (página dedicada siempre; PDF de procedencia cuando se haya localizado);
- cada banda tiene transcripción inglesa revisada y traducción española revisada;
- todas las validaciones pasan sobre `sources/2A`;
- no hay referencias sin resolver ni bloqueos abiertos;
- `sources/knowledge` y `sources/2B` permanecen sin cambios atribuibles a esta ingesta;
- existe un diff de promoción explícito y revisado.
