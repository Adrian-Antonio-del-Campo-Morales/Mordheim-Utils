# Herramientas de ingesta de 2A/2B (temporales)

Aquí viven **todas** las herramientas que solo existen para la fase de ingesta y
asimilación de los árboles de staging `sources/2A` y `sources/2B`. Están juntas a
propósito: **este directorio se borra entero cuando la fase termine** (bandas, catálogos,
hired swords, magia y traducciones ya promocionados a `sources/knowledge`).

Nada del código de la aplicación ni del pipeline de la KB importa estos ficheros, así que
borrar `tools/ingestion/` no debe dejar referencias colgando salvo las de esta tabla y las
de `sources/2A/README.md` / `sources/2B/README.md`, que se retiran con él.

Todo lo que se mantiene de forma permanente vive en `tools/knowledge/`
(`audit_kb_conformance.py`, `derive_kb_contract.py`, `audit_schema_strictness.py`,
`audit_staging_contract.py`, `strip_rule_ref_restatements.py`, `generate_knowledge_web.py`,
`normalize_open_fields.py`, y desde su promoción `printed_entries.py` y
`printed_wordings.py`).
Las tareas editoriales permanentes viven en `tools/knowledge/maintenance/`
(por ejemplo `format_yaml.py` y `normalize_names.py`).

`audit_staging_contract.py` es la puerta permanente del staging: valida los cuatro
documentos de cada paquete contra los esquemas del contrato (`--only schema`, el que
debe quedarse verde), y además contrasta los catálogos staging con el esquema KB que
los reclamará al promoverse (`--only catalogue`, las clases que decide
`sources/2B/promotion-schema-plan.md`), lista los ficheros que `normalize_names.py`
reescribiría (`--only naming`) y las colecciones flow de las claves que la KB escribe en
bloque (`--only shape`). Tanto las clases de catálogo, como el drift de nombres, como la
forma de colección están fijados en tests (`tests/python/knowledge/test_editorial_schemas.py` y
`tests/python/knowledge/test_staging_collection_shape.py`), así que un fichero nuevo que
introduzca una desviación no declarada falla el test.

## Un solo lector para todo lo que se coteja contra una fuente impresa

Los cotejos de fuente —hirelings y Dramatis Personae de 2B, Dramatis Personae de 2A, las
páginas de banda de 2A (el auditor único de su árbol) y el auditor de 2B— comparten un
mismo lector de entradas impresas (`tools/knowledge/printed_entries.py`) y difieren sólo
en qué fuente se coteja. Lo leen todo por la **geometría de la fuente**: las coordenadas
de las palabras en un PDF a dos columnas y la estructura del documento en una página web
(encabezados con su tramo, filas de tabla con sus celdas). Antes cada cotejo leía a su
manera: el de los Dramatis Personae partía del texto aplanado y atribuía al personaje la
tarifa y el rating del vecino de columna (Gwen aparecía con los 75/30 del Dark Jester y el
Foole con los 70/35 de Sigmund, que son los del personaje contiguo, y cuatro de los siete
perfiles quedaban sin localizar), el de las bandas leía con expresiones regulares sobre el
HTML, que pierden una celda con etiquetas dentro y no distinguen el tramo de una sección
de la tabla de la siguiente, y el auditor de 2B leía con `pdftotext -layout`, que conserva
las columnas a costa de comprimir sus desplazamientos e intercalar sus líneas.

La geometría da tres vistas, y cada cotejo usa la que necesita: la **línea física** —lo que
se imprime a la misma altura, de izquierda a derecha, sin partir la página en columnas— es
la que leen las tablas, porque una tabla de habilidades ocupa la página entera y sus
encabezados, a los dos lados del canal, son la misma fila; las **celdas** de esa línea, lo
que reparte sus columnas, es lo que leen las listas de precios y las filas de
características; y el **orden de lectura** —columna izquierda y luego derecha— es el de las
entradas de un personaje.

Los tres principios que comparten, y que sus tests fijan:

- **La entrada es la de la fuente**, no la del texto que la rodea: un dato del vecino no
  cuenta, ni por columna ni por prosa;
- **la divisa se compara**: guardar 75 *warp tokens* como 75 coronas es un hallazgo, y la
  tarifa que sólo declara un lado queda como nota;
- **la cobertura se declara por chequeo**: un «0 hallazgos» sin filas comparadas no es un
  «0 comprobado». Lo no comparable —una tabla que la fuente no imprime, un dato que el
  catálogo no modela, una etiqueta de regla editorial— es una nota con su razón, y baja la
  cobertura en vez de pasar por verde. La cuentan `Coverage` (por personaje) y `Ledger`
  (agregada, por banda), que imprimen lo mismo que sus cotejos: cuánto se comparó y qué no.

## Herramientas retiradas con su trabajo hecho

El directorio sólo conserva herramientas **vivas**. Se retiraron, con sus veredictos ya
registrados en `sources/2A/*.md` y `sources/2B/*.md`:

- `audit_2a.py`, el auditor de texto plano: sus chequeos numéricos (costes, experiencia
  inicial, límites de roster, statlines y tabla de habilidades) se **portaron** a
  `audit_2a_sources.py`, que los lee por la estructura de la página en vez de por una
  ventana de tokens. Es el único auditor de 2A.
- `review_2a.py` y `review_2b.py`, la re-derivación numérica por expresiones regulares:
  sus comprobaciones están cubiertas con más precisión por los auditores geométricos
  (costes/XP/oro/habilidades en `audit_2b.py`, prosa por cobertura de tokens en
  `audit_2ab_fidelity.py`).
- Los ayudantes de una sola pasada, agotados: `fill_2a_es_effects.py`,
  `fill_2b_es_effects.py` (las traducciones que faltaban de verdad ya estaban escritas),
  `fill_2b_prayer_lores.py` (la lista de *Prayers of Taal & Rhya* quedó aplicada en
  `catalog/magic-2b.yaml`), `migrate_2b_kb_schema.py` (los dos `grant` que faltaban,
  aplicados), `migrate_staging_records.py`, `repair_2b_flow_i18n.py` (0 escalares),
  `find_stub_sources.py` (los stubs de `missing-item-stubs.yaml` llevan vacíos desde la
  barrida de completitud) y las lecturas de imagen de las páginas escaneadas KEP
  (`read_scanned_costs.py`, `read_2b_kep_stats.py`), cuya lectura queda registrada como
  evidencia en `sources/2B/discrepancy-verdicts.md`.

Dos herramientas se **promocionaron** a `tools/knowledge/`, que es donde vive lo
permanente: `printed_entries.py` (el lector geométrico de entradas impresas, con sus tests
en `test_printed_entries.py`) y `printed_wordings.py` (el registro único de las palabras
que una fuente imprime, con `test_printed_wordings.py`). Los cotejos de esta carpeta los
leen de allí; la condición de borrado del directorio ya no los arrastra.

## Inventario

| Herramienta | Para qué sirve |
|---|---|
| `ingest_2a.py` | Pipeline de 2A: `discover`, `download`, `extract`, `validate`, `report` (páginas dedicadas de mordheimer.net). |
| `ingest_2b.py` | Pipeline de 2B: mismas órdenes, pero PDF-first contra Broheim (hash del PDF en el manifiesto). |
| `audit_2a_sources.py` | **Auditoría única de 2A** contra las páginas cacheadas, leídas por su estructura con el lector compartido (encabezados, tramos y tablas). Coteja el contenido —listas, precios, filas impresas, aclaraciones de reglas, magia— y los **números** portados del auditor de texto plano retirado: costes y experiencia inicial por perfil (la sección del caza-suero que nombra la tarifa), límites de roster (mínimo, máximo y oro inicial, impresos como cifra o como palabra), statlines celda a celda (`profile_tables`: «3(4)» es una variante, no un décimo valor) y la tabla de habilidades por columnas (un «✓» bajo su columna, con la coincidencia por contención que subsume los alias de fila). Declara la **cobertura por chequeo** —`skills`, `special-equipment`, `lists`, `special-price`, `item-profiles`, `rules`, `clarifications`, `magic`, `costs`, `experience`, `roster`, `statlines`, `skill-tables`— con las unidades y los valores comparados de cada uno: lo que la página no imprime se declara, no se silencia. |
| `audit_2b.py` | Auditoría cruzada de 2B contra el texto de los PDFs (con adjudicaciones documentadas). Lee las listas de precios, las tablas de habilidad y las cifras de coste con la línea física y las celdas del lector compartido (`printed_entries.price_rows`), en vez de con `pdftotext -layout`: la fila de una tabla cruza el canal de las columnas y la tarifa se atribuye por la celda que la imprime, no por una ventana del texto aplanado. |
| `audit_2b_negative_tests.py` | Batería negativa de `audit_2b.py`: rompe un dato y exige el hallazgo correspondiente; restaura los ficheros byte a byte. |
| `audit_2ab_fidelity.py` | Fidelidad y completitud de los 79 paquetes de staging contra los textos extraídos: cada artefacto del paquete debe rastrearse hasta la fuente y cada etiqueta impresa debe estar modelada. Los **objetos** de cada lista de equipo (`equipment-access.yaml`) se cotejan contra las **listas impresas** —la fila que imprime su nombre con su tarifa, `price_rows` en 2B y las tablas del documento en la página web de 2A— y no contra el nombre suelto de su prosa: `item-in-list` cuando la lista del propio documento lo imprime, `item-in-supplement` cuando sólo lo imprime un capítulo que el árbol comparte, `item-outside-list` cuando el nombre está en la prosa y ninguna fila lo imprime, y `item-name-missing` cuando no está ni en la lista ni en la prosa. La fila se coteja con la **palabra que la fuente imprime** para ese objeto (`printed_wordings`: «Holy Water» para `blessed_water`, «Wardog» para `warhound`, «Warplock Pistol» para `warp_pistol`…), adjudicada fila por fila con su tarifa en §9 de los verdictos de 2A y §15.4 de los de 2B, y con la nota de la lista que la fuente **delega** al reglamento en vez de imprimirla (el KAZ skaven, §7). La lectura del documento es la del lector compartido, no la de `pdftotext -layout`, y las filas de características de la tabla impresa se leen por **estructura** —la línea física y sus celdas (`printed_row`), el orden de lectura de la columna con el nombre del título que encabeza la tabla (`entry_row`, `title_above`, `column_row`) y las tablas de la página web por sus celdas (`profile_tables`)—, nunca por una ventana de tokens de prosa (que queda sólo como respaldo de la fuente sin lectura estructural): el nombre es el de la celda que lleva los valores o el del encabezado que titula la tabla, la fila se lee por sus nueve **valores** (un guion es una característica que no hay; el paréntesis de «3(4)», «Giant Spider 7 3 0 3(4) 3 1 4 1 4», es una variante y no un décimo valor) y lo que la columna vecina imprime a la misma altura no lo es (la tabla de tesoros del KAZ, «D3 Gems worth 10 gc each 4+», no es la fila de un perfil llamado «D»). Una fila cuyo nombre coincide con un perfil del KB sólo cuenta como modelada si el KB también lleva sus características. |
| `normalize_staging_for_promotion.py` | Pases `status`, `market`, `items`, `hirelings`, `magic`, `shape`: el catálogo de mercado de cada árbol, el `status` que lleva cada familia, el objeto en forma KB (prosa plegada, `kind` reclasificado, hechos de mercado retirados), el reparto de hirelings en sus dos catálogos con la tarifa y elegibilidad en el documento de campaña, la magia con su envoltura, sus `lore_assignments` y los reprints/variantes en forma KB (la tabla de fallo viaja a la regla de banda que tira en ella), y la forma de colección que la KB usa (bloque, con los guiones al indent de su clave) para `source_path`, `equipment_lists`, `rule_ids`, `skill_access`, `source`, `characteristics`, `name_i18n` y `combat_traits`. Idempotente; `--write` pasa después `tools/knowledge/maintenance/format_yaml.py`. |

`strip_rule_ref_restatements.py` empezó aquí y se **promocionó** a `tools/knowledge/`:
impone un invariante de la KB (`rule_ref` sin `effect` local) y ahora corre por defecto
sobre todos los árboles, `knowledge` incluido.

## Caches que necesitan

Los auditores de content-fidelity no descargan nada: leen los caches ignorados por git.
Si faltan, se saltan o avisan (no fallan en seco).

| Cache | Contenido | Lo producen |
|---|---|---|
| `build/cache/2a-sources/` | Páginas y PDFs de 2A + textos extraídos | `ingest_2a.py download/extract` |
| `build/cache/2b-pdfs/` | PDFs de Broheim + texto, `words/` y `text-geometry/` de la lectura por geometría (y el `layout/` histórico, ya no lo lee ningún auditor) | `ingest_2b.py download/extract` |
| `build/cache/2a-dp/` | Páginas de hirelings de 2A, en la ruta que el registro declara (`dramatis-<grado>.html`/`.txt`, `hired-swords-<grado>.html`); las lee el cotejo permanente | descargas puntuales |
| `build/cache/hireling-sources/` | Informe de cada catálogo (`<catálogo>/check.json`), entradas extraídas (`<catálogo>/blocks/`) y las cachés de página del lector (`words/`, `text/`) | `tools/knowledge/check_hireling_sources.py` |

## Órdenes habituales

```bash
# pipelines
python tools/ingestion/ingest_2a.py report && python tools/ingestion/ingest_2a.py validate
python tools/ingestion/ingest_2b.py report && python tools/ingestion/ingest_2b.py validate

# cotejo contra fuentes
python tools/ingestion/audit_2a_sources.py                  # auditoría única de 2A
python tools/ingestion/audit_2a_sources.py --all            # incluye los adjudicados
python tools/ingestion/audit_2b.py
python tools/ingestion/audit_2b_negative_tests.py
python tools/knowledge/check_hireling_sources.py            # los dos catálogos de la KB
python tools/knowledge/check_hireling_sources.py --tree 2b  # el staging que se promociona
python tools/ingestion/audit_2ab_fidelity.py                # 2A + 2B, informe limpio
python tools/ingestion/audit_2ab_fidelity.py --all          # con las adjudicadas
python tools/ingestion/audit_2ab_fidelity.py --strict-labels # barrido de completitud
```

Los detalles de método y los veredictos de cada pasada están en `sources/2A/*.md` y
`sources/2B/*.md` (conformance, discrepancy-verdicts, review-plan y los README de cada
árbol), que también son staging y se retiran con esta carpeta.

### Huecos completados a mano

El cotejo de fidelidad sólo *señala*: los huecos reales se completan a mano en el paquete
correspondiente, siguiendo la forma que ya usa el árbol. Los datos de cada añadido (texto
impreso en inglés, traducción española, página y sección resueltas del texto cacheado, más
la razón del `runtime` provisional) se guardan en `build/cache/missing-rules/<banda>.py` y
se aplican con `python build/cache/add_missing_rules.py <banda>`;
`python build/cache/sync_rule_ids.py <banda>` mantiene `rule_ids` de `band.yaml` en su
contrato (sólo reglas `band--…`). Los dos son ayudantes de esta fase: viven en `build/cache`
y se borran con ella, mientras que el resultado —las reglas— queda en `sources/2A`/`sources/2B`
y el registro de cada pasada en `sources/2B/discrepancy-verdicts.md` §8 y
`sources/2A/discrepancy-verdicts.md` §5.

## Candidatos a quedarse

El cotejo de catálogo contra fuentes **ya es permanente y vive fuera** de esta carpeta:
`tools/knowledge/check_hireling_sources.py` recorre con una sola orden los dos catálogos
publicados de hirelings —hired swords y Dramatis Personae, todos los grados— y coteja con
la misma lectura el staging que se promociona a ellos (`--tree 2b`).

| Pieza permanente | Qué es |
|---|---|
| `tools/knowledge/check_hireling_sources.py` | El cotejo: localiza la entrada impresa de cada perfil, compara el paquete y declara cobertura, hallazgos y adjudicaciones |
| `tools/knowledge/printed_entries.py` | La lectura de una entrada como la imprime el documento (geometría, divisa, cobertura) |
| `tools/knowledge/printed_wordings.py` | El registro único de las palabras impresas y las listas delegadas |
| `tools/knowledge/source_documents.py` | El resolvedor de «entrada → documento fuente», sobre el registro versionado `sources/knowledge/registry/source-documents.yaml` (los documentos que los catálogos citan, sus formas de cita y la copia del espejo de cada uno) |

El cotejo no adivina el nombre del fichero —el alias del nombre de descarga, el prefijo
`dramatis-`—: la URL de cada `source_refs` resuelve en el registro, y una cita que falte
falla en `tests/python/knowledge/test_source_documents.py`, que recorre los catálogos de
hirelings de la KB y del árbol 2B y exige que todas resuelvan. Del árbol 2B queda aquí la
*invocación* del cotejo mientras el staging viva; cuando se promueva, sus grados entran en
la orden de la KB y esa invocación se retira con la carpeta.

Lo que le queda a esta carpeta es el staging: los dos pipelines de ingesta, las auditorías
de banda de 2A y 2B (`audit_2a_sources.py`, `audit_2b.py`, `audit_2b_negative_tests.py`,
`audit_2ab_fidelity.py`) y el normalizador de promoción. Borrarla arrastra eso; el cotejo
ya no.
