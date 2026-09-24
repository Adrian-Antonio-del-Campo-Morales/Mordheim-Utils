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
`audit_staging_contract.py`, `strip_rule_ref_restatements.py`, `generate_knowledge_web.py`)
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
listas y tablas de las páginas de banda de 2A y los dos auditores de 2B— comparten un mismo
lector de entradas impresas (`printed_entries.py`) y difieren sólo en qué fuente se coteja.
Lo leen todo por la **geometría de la fuente**: las coordenadas de las palabras en un PDF a
dos columnas y la estructura del documento en una página web (encabezados con su tramo,
filas de tabla con sus celdas). Antes cada cotejo leía a su manera: el de los Dramatis
Personae partía del texto aplanado y atribuía al personaje la tarifa y el rating del vecino
de columna (Gwen aparecía con los 75/30 del Dark Jester y el Foole con los 70/35 de
Sigmund, que son los del personaje contiguo, y cuatro de los siete perfiles quedaban sin
localizar), el de las bandas leía con expresiones regulares sobre el HTML, que pierden una
celda con etiquetas dentro y no distinguen el tramo de una sección de la tabla de la
siguiente, y los dos auditores de 2B leían con `pdftotext -layout`, que conserva las
columnas a costa de comprimir sus desplazamientos e intercalar sus líneas.

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

## Inventario

| Herramienta | Para qué sirve |
|---|---|
| `ingest_2a.py` | Pipeline de 2A: `discover`, `download`, `extract`, `validate`, `report` (páginas dedicadas de mordheimer.net). |
| `ingest_2b.py` | Pipeline de 2B: mismas órdenes, pero PDF-first contra Broheim (hash del PDF en el manifiesto). |
| `review_2a.py` | Cross-check de revisión inglesa: re-deriva del texto cacheado cada número del paquete 2A. |
| `review_2b.py` | Igual para 2B (límites de roster, costes, XP, precios, dígitos citados en reglas). |
| `audit_2a.py` | Auditoría cruzada de contenido de 2A: costes, statlines y skill access contra los textos extraídos. |
| `audit_2a_sources.py` | Fidelidad de 2A contra las páginas cacheadas: listas, precios, filas impresas, aclaraciones de reglas. Las lee por la estructura de la página con el lector compartido (encabezados, tramos y tablas) y declara la **cobertura por chequeo** —`skills`, `special-equipment`, `lists`, `special-price`, `item-profiles`, `rules`, `clarifications`, `magic`— con las unidades y los valores comparados de cada uno. |
| `audit_2b.py` | Auditoría cruzada de 2B contra el texto de los PDFs (con adjudicaciones documentadas). Lee las listas de precios, las tablas de habilidad y las cifras de coste con la línea física y las celdas del lector compartido (`printed_entries.price_rows`), en vez de con `pdftotext -layout`: la fila de una tabla cruza el canal de las columnas y la tarifa se atribuye por la celda que la imprime, no por una ventana del texto aplanado. |
| `audit_2b_negative_tests.py` | Batería negativa de `audit_2b.py`: rompe un dato y exige el hallazgo correspondiente; restaura los ficheros byte a byte. |
| `audit_2ab_fidelity.py` | Fidelidad y completitud de los 79 paquetes de staging contra los textos extraídos: cada artefacto del paquete debe rastrearse hasta la fuente y cada etiqueta impresa debe estar modelada. Los **objetos** de cada lista de equipo (`equipment-access.yaml`) se cotejan contra las **listas impresas** —la fila que imprime su nombre con su tarifa, `price_rows` en 2B y las tablas del documento en la página web de 2A— y no contra el nombre suelto de su prosa: `item-in-list` cuando la lista del propio documento lo imprime, `item-in-supplement` cuando sólo lo imprime un capítulo que el árbol comparte, `item-outside-list` cuando el nombre está en la prosa y ninguna fila lo imprime, y `item-name-missing` cuando no está ni en la lista ni en la prosa. La fila se coteja con la **palabra que la fuente imprime** para ese objeto (`printed_wordings`: «Holy Water» para `blessed_water`, «Wardog» para `warhound`, «Warplock Pistol» para `warp_pistol`…), adjudicada fila por fila con su tarifa en §9 de los verdictos de 2A y §15.4 de los de 2B, y con la nota de la lista que la fuente **delega** al reglamento en vez de imprimirla (el KAZ skaven, §7). La lectura del documento es la del lector compartido, no la de `pdftotext -layout`, y las filas de características de la tabla impresa se leen por **estructura** —la línea física y sus celdas (`printed_row`), el orden de lectura de la columna con el nombre del título que encabeza la tabla (`entry_row`, `title_above`, `column_row`) y las tablas de la página web por sus celdas (`profile_tables`)—, nunca por una ventana de tokens de prosa (que queda sólo como respaldo de la fuente sin lectura estructural): el nombre es el de la celda que lleva los valores o el del encabezado que titula la tabla, la fila se lee por sus nueve **valores** (un guion es una característica que no hay; el paréntesis de «3(4)», «Giant Spider 7 3 0 3(4) 3 1 4 1 4», es una variante y no un décimo valor) y lo que la columna vecina imprime a la misma altura no lo es (la tabla de tesoros del KAZ, «D3 Gems worth 10 gc each 4+», no es la fila de un perfil llamado «D»). Una fila cuyo nombre coincide con un perfil del KB sólo cuenta como modelada si el KB también lleva sus características. |
| `printed_wordings.py` | **Registro único de las palabras impresas**: la palabra con que una fuente nombra un objeto que el catálogo registra con otro (`great_weapon` → «Double-handed weapon», `blessed_water` → «Holy Water», `warhound` → «Wardog»…) y las listas que un documento **delega** al reglamento en vez de imprimirlas. Estaban en una tabla por auditor —`SOURCE_WORDING` en `audit_2a_sources.py` y en `audit_2b.py`, `ITEM_ALIASES` en `audit_2ab_fidelity.py`—, con el resultado de que una pareja adjudicada en una se quedaba sin ver en las otras: el cotejo de fidelidad declaraba huecos que los otros dos ya tenían adjudicados. Cada pareja lleva su **sitio** (árbol, banda y lista; en blanco vale para cualquiera) y la adjudicación con la fila verbatim y su tarifa vive en §9 de los verdictos de 2A y §7/§15.4 de los de 2B. La lee cada cotejo como sabe: la fila de una lista (2A), la banda entera (2B, cuya tabla siempre fue por banda) y todas las palabras del objeto en su árbol (fidelidad). |
| `printed_entries.py` | **Lector único de entradas impresas**, compartido por los tres cotejos de fuente. Lee una fuente por su geometría —`PdfCorpus` por coordenadas de palabra (`pdftohtml -xml`), `HtmlDocument`/`HtmlCorpus` por la estructura del documento (encabezados con su tramo, una entrada por `div.fighter`, una celda por columna de tabla), `TextCorpus` por el ancla `Source:` del texto plano— y devuelve la misma entrada en los tres casos. `PdfCorpus` da tres vistas del documento —la línea **física** (lo que la página imprime a la misma altura), el **orden de lectura** de la columna y las **entradas** de la página— y del documento se leen además las tablas de características (`characteristic_columns`, `profile_row`, `profile_tables`, `stat_header`): la fila sale de las columnas que su cabecera titula y el nombre, de la celda que lo imprime o del encabezado que titula la tabla, sin el cupo del perfil (`profile_name`). Las **listas de precios** (`price_rows`) se leen a razón de **una fila por celda que tasa** —la tabla de un suplemento pone tres filas a la misma altura, una por columna— y una tarifa puede ser un importe, una fórmula de dados o un **multiplicador del precio de otro objeto** («Gromril Weapon 3x the cost», «Price x 2», «2 x price»): la cifra que multiplica no es un importe en coronas, así que la fila se declara fórmula y no se le suma un precio. Compara tarifa (**importe y divisa**), fila de stats, rating y reglas una por una, y declara la **cobertura por chequeo** con `Coverage` (por personaje) o `Ledger` (agregada, por banda): lo que no se pudo comparar es una nota que baja la cobertura, nunca un verde. No conoce rutas de ningún árbol. |
| `check_2a_dramatis.py` | Coteja los Dramatis Personae de 2A (catálogo de la KB) contra su página de mordheimer.net, con el lector compartido. La página trae las entradas y las columnas de sus tablas escritas, así que se leen tal cual: el cotejo anterior partía del texto aplanado y daba a Gwen la tarifa del Dark Jester y al Foole la de Sigmund, además de dejar cuatro de los siete perfiles sin localizar. La tarifa sale del documento de contratación de la KB y las etiquetas de regla que el catálogo escribe y la fuente imprime con otro nombre se declaran en `EDITORIAL` y quedan como nota. |
| `check_2b_hirelings.py` | Coteja los hirelings y Dramatis Personae de 2B contra sus PDFs, con el lector compartido: resuelve qué PDF imprime a cada personaje y qué declara el paquete (la tarifa vive en `catalog/hired-swords-and-dramatis-2b.yaml`), lee cada entrada por geometría de página —columna izquierda y luego derecha— y adjudica los `out_of_scope` y las etiquetas editoriales como nota. Deja los bloques impresos en orden de lectura. |
| `read_scanned_costs.py` | Lee por imagen los costes de contratación de las páginas escaneadas (KEP). |
| `read_2b_kep_stats.py` | Clasifica glifo a glifo (por plantillas) las filas de stats de las páginas escaneadas KEP. |
| `migrate_2b_kb_schema.py` | Lleva los bloques `runtime` de `special-rules.yaml` al canon de la KB (idempotente). |
| `migrate_staging_records.py` | Lleva los registros de banda (notas de lista, divisas, tipos de `fixed_equipment`, `references`) al canon de la KB. |
| `normalize_open_fields.py` | Lleva los campos que el contrato deja abiertos (`status`, `categories`/`grade`, `sources[].manual`, `profiles[].source_path`) al vocabulario de la KB; `--check`/`--write`, con registro de fuentes sincronizado. |
| `normalize_staging_for_promotion.py` | Pases `status`, `market`, `items`, `hirelings`, `magic`, `shape`: el catálogo de mercado de cada árbol, el `status` que lleva cada familia, el objeto en forma KB (prosa plegada, `kind` reclasificado, hechos de mercado retirados), el reparto de hirelings en sus dos catálogos con la tarifa y elegibilidad en el documento de campaña, la magia con su envoltura, sus `lore_assignments` y los reprints/variantes en forma KB (la tabla de fallo viaja a la regla de banda que tira en ella), y la forma de colección que la KB usa (bloque, con los guiones al indent de su clave) para `source_path`, `equipment_lists`, `rule_ids`, `skill_access`, `source`, `characteristics`, `name_i18n` y `combat_traits`. Idempotente; `--write` pasa después `tools/knowledge/maintenance/format_yaml.py`. |
| `repair_2b_flow_i18n.py` | Repara escalares i18n truncados por comas en YAML flow-style. |
| `fill_2a_es_effects.py` / `fill_2b_es_effects.py` | Rellenan los `effect_i18n.es` que falten; dry run por defecto, `--write` para aplicar. |
| `fill_2b_prayer_lores.py` | Ingesta de las listas de plegarias de *Miracle Workers* en `catalog/magic-2b.yaml`. |
| `find_stub_sources.py` | Localiza el texto cacheado de cada stub de objeto pendiente. |

`strip_rule_ref_restatements.py` empezó aquí y se **promocionó** a `tools/knowledge/`:
impone un invariante de la KB (`rule_ref` sin `effect` local) y ahora corre por defecto
sobre todos los árboles, `knowledge` incluido.

## Caches que necesitan

Los auditores de content-fidelity y las lecturas por imagen no descargan nada: leen los
caches ignorados por git. Si faltan, se saltan o avisan (no fallan en seco).

| Cache | Contenido | Lo producen |
|---|---|---|
| `build/cache/2a-sources/` | Páginas y PDFs de 2A + textos extraídos | `ingest_2a.py download/extract` |
| `build/cache/2b-pdfs/` | PDFs de Broheim + texto, `words/` y `text-geometry/` de la lectura por geometría (y el `layout/` histórico, ya no lo lee ningún auditor) | `ingest_2b.py download/extract` |
| `build/cache/2a-hirelings/`, `build/cache/2a-dp/` | Fuentes cacheadas de hirelings y Dramatis Personae 2A (`dramatis-<slug>.html`/`.txt`), más las entradas extraídas (`dramatis-blocks/`) | descargas puntuales del cotejo y `check_2a_dramatis.py` |
| `build/cache/2b-hirelings/` | Bloques impresos de hirelings en orden de lectura, y el XML (`words/`) y el texto (`text/`) por página | `check_2b_hirelings.py` |

## Órdenes habituales

```bash
# pipelines
python tools/ingestion/ingest_2a.py report && python tools/ingestion/ingest_2a.py validate
python tools/ingestion/ingest_2b.py report && python tools/ingestion/ingest_2b.py validate

# cotejo contra fuentes
python tools/ingestion/audit_2a.py
python tools/ingestion/audit_2a_sources.py
python tools/ingestion/audit_2b.py
python tools/ingestion/audit_2b_negative_tests.py
python tools/ingestion/check_2a_dramatis.py                 # Dramatis Personae 2A (catálogo de la KB)
python tools/ingestion/check_2b_hirelings.py                # hirelings y Dramatis 2B (staging)
python tools/ingestion/audit_2ab_fidelity.py                # 2A + 2B, informe limpio
python tools/ingestion/audit_2ab_fidelity.py --all          # con las adjudicadas
python tools/ingestion/audit_2ab_fidelity.py --strict-labels # barrido de completitud

# migraciones idempotentes (dry run primero)
python tools/ingestion/migrate_2b_kb_schema.py
python tools/ingestion/migrate_staging_records.py
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

Si antes de borrar el directorio se quiere conservar alguno, el más defendible es el
cotejo de catálogo contra fuentes, que hoy es **uno solo** para los dos árboles: el lector
de entradas impresas (`printed_entries.py`) con sus dos drivers. La KB tiene catálogo de
hired swords y Dramatis Personae de todos los grados, y el mismo contraste
tarifa/stats/rating tendría sentido permanente. Lo que falta, eso sí, es un resolvedor de
«entrada → documento fuente»: hoy está cableado a los PDFs de 2B y a las páginas de 2A
(`reference_stems` y `source_slugs`). Cualquier promoción debería reescribir el resolvedor
y llevarse el lector entero —la geometría, la divisa y la cobertura— a `tools/knowledge/`
con sus tests, no moverlo tal cual.
