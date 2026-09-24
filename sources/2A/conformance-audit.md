# Auditoría de corrección de 2A (2026-09-15)

Alcance: las **19 bandas** de `sources/2A` contra los patrones de la **KB activa**
(`sources/knowledge`). Objetivo: que cada documento siga el esquema KB al pie de la letra,
sin campos ni etiquetas inventados, y que ninguna corrección de forma haya borrado texto
de la fuente sin dejarlo en otro sitio.

Este informe cierra la pasada de conformidad de 2A: los pendientes que quedaban abiertos
en el árbol, la divergencia de forma que sobrevivía en 2A y 2B y que el usuario decidió
corregir, y el estado verificado al final.

## Método

1. **Contrato medido, no asumido.** `tools/knowledge/derive_kb_contract.py` re-deriva de
   `sources/knowledge` la forma de cada documento (`band.yaml`, `roster`, miembros,
   `profiles`, `equipment-access` documento/lista/ítem, regla, `applies_to`, `runtime`,
   efecto, binding) y sus dominios de valor, y luego compara el árbol de staging contra
   **esa** medición. Así la lista de comprobación no puede quedarse corta por un juego de
   claves escrito a mano.
2. **Auditoría de forma clave a clave.** `tools/knowledge/audit_kb_conformance.py` recorre
   documentos, claves, gramática de ids, tipos, características, `grant`/`scope`/
   `implemented`, `applies_to`, bindings y `rule_ref`, y separa las clases informativas
   (hallazgos adjudicados) de las que sí son defecto.
3. **Auditoría de pérdida de datos.** `build/cache/diff_2a_backup.py` compara un backup
   contra el árbol vivo a nivel de hoja y lista todo campo retirado con su valor, para que
   ningún texto de la fuente desaparezca sin destino.
4. **Auditoría cruzada de contenido.** `tools/ingestion/audit_2a.py` (costes, perfiles,
   statlines y `skill_access` contra las páginas HTML cacheadas).
5. **Puertas del repo.** `ingest_2a.py validate`, `ingest_2b.py validate`,
   `tools/format_yaml.py`, `pytest tests/knowledge tests/web`.

## Hallazgos y correcciones

### 1. Restricción de roster perdida (`order-of-the-mare-web`)

La nota del miembro «Dame of the Mare» se retiró al normalizar el roster y su texto no
estaba en ningún documento. La KB no tiene campo de roster para eso; el patrón canónico es
una **regla de banda** (`applies_to: {band: true}`, precedente
`outlaws-of-stirwood-forest/band--cleric-hero-slot`).

Creada `band--dame-of-the-mare-succession` («Dama de la Yegua: Sucesión») con el texto de
la fuente, `name_i18n.es`, `effect_i18n.es`, `source` del manual de la banda y `runtime`
`scope/implemented = NO` documentado. Listada en `band.yaml → rule_ids`.

### 2. Notas de ítem colgantes (`druchii-mic`)

Cuatro ítems apuntaban a una nota de lista ya retirada (`'* Special Naggaroth price; see
list note'` ×3, `'** Common for warbands with Witch Elves, Witch Elves only; see list
note'`). La KB no usa remisiones a notas de lista: el `notes` del ítem es autosuficiente
(p. ej. «Warband-creation price only; afterwards use the Trading rules.»).

- Creada `band--naggaroth-prices` («Precios de Naggaroth») con la leyenda `*` completa
  (texto de la fuente, EN + ES, `source` a «Dark Elf equipment lists»).
- Los cuatro `notes` de ítem se leen solos y nombran la regla que lleva el texto:
  `Special Naggaroth price; see the Naggaroth Prices rule.` y
  `Common for warbands with Witch Elves; Witch Elves only. See the Maibd Poison rule.`
  (la regla `witch-elves--maibd-poison` ya existía en el paquete).

Ambas reglas se añadieron con el script idempotente que dejaba la tarea pendiente
(`build/cache/2b-sources/conform_2a_rules.py`).

### 3. Guardas del validador (verificado)

`ingest_2a.py validate` ya aplica las mismas guardas que 2B: claves KB, gramática
`<owner>--<name>`, `rule_ref` resoluble contra la KB activa, `runtime.effects` obligatorio
(incluso con `rule_ref`), `effects` fuera de `runtime` prohibido, `binding.kind` del
vocabulario, reglas de banda listadas en `band.yaml` y prohibidas en `rule_ids` de perfil.

### 4. Regla que citaba y **además** repetía la prosa (decidido y aplicado)

**El problema.** 53 reglas de 2A y 72 de 2B llevaban `rule_ref: shared-rule.*` **y** un
`effect`/`effect_i18n` propio: una forma que la KB no usa (0 de 898 reglas de banda). Ese
texto local no lo renderizaba nadie — es texto muerto:

| Consumidor | Comportamiento |
|---|---|
| `mordheim_knowledge.loader.shared_rule_text` | con `rule_ref` devuelve el `effect` de la regla compartida e ignora el local |
| `combat_lab…catalogue._rule_text` | ídem: renderiza el registro compartido |
| `tools/knowledge/generate_knowledge_web.py` | las reglas con `rule_ref` no se publican como reglas de banda, solo como etiquetas i18n de nombre |
| `campaign…rules_catalogue` | usa `rule_ref` para enlazar reglas compartidas ↔ perfiles |

Y no era una copia redundante: en 2A difería de la compartida en **53 de 53** casos y suele
ser la redacción **larga de la fuente** (p. ej. `dwarf-slayer-cult-web/band--hard-to-kill`:
216 caracteres frente a los 103 de `shared-rule.hard-to-kill`).

**Decisión (usuario, 2026-09-15):** dejar la forma KB exacta, es decir **quitar la prosa
local**. Aplicada con `tools/knowledge/strip_rule_ref_restatements.py` (idempotente; aborta
si el cambio no se limita a esas dos claves), que además **archiva la redacción retirada**
(EN + traducción ES) en:

- `sources/2A/retired-rule-restatements.md` (53 reglas)
- `sources/2B/retired-rule-restatements.md` (72 reglas)

La vista no cambia —ese texto ya se ignoraba al renderizar— y la forma de esas reglas pasa
a ser la de la KB (`id`, `name`, `name_i18n`, `rule_ref`, `runtime`, `source`,
`applies_to`).

**Guarda permanente:** `ingest_2a.py` y `ingest_2b.py` (`validate`) ahora fallan si una
regla con `rule_ref` lleva `effect`/`effect_i18n`, con mensaje explicando el patrón KB
(probado con un caso negativo real: la guarda dispara y el fichero se restaura). El
auditor cuenta la clase `rule-ref-restated` como desviación, no como informativa.

## Verificación de contenido contra las fuentes (2026-09-15 23:30)

`audit_2a.py` cotejaba nombres, costes, experiencia, roster, statlines y la tabla de
skills. El hueco era el **contenido**: si las reglas, las skills especiales, el equipo
especial y las tablas de las listas están realmente en el paquete. Para cerrarlo se añadió
`tools/ingestion/audit_2a_sources.py` (solo lectura), que parsea la página cacheada de cada
banda y comprueba, en las dos direcciones:

- cada `<h3>` bajo **Special Skills** → una regla (por nombre, o dentro de la prosa de una
  regla-contenedor como `band--slayer-special-skills`);
- cada `<h3>` bajo **Special Equipment** → un ítem del catálogo;
- cada `<h3>` *… Equipment List* → una lista con ese nombre, cada fila *Item/Cost* en la
  lista con su precio, y cada ítem de la lista en la tabla de la página;
- cada nombre de regla del paquete es rastreable a la página (o a la sección que cita).

El emparejamiento usa la misma pool de ítems que el validador (KB + catálogos de 2A y 2B) y
entiende la taquigrafía de las páginas: paréntesis que dan el arma base (``Meat Cleaver
(Axe)``), ``Yari (Spear)``, ``Longbow`` ↔ ``Long Bow``, plurales, ``and``/``&`` y
``Double-handed weapon`` ↔ ``Great Weapon`` (misma opción de motor).

**Corregido:**

1. **`two_handed_weapon` → `great_weapon`** (21 usos en 13 listas). Los dos ids existen en
   la KB y ambos mapean a la misma opción de motor (`engine_option: Double-handed
   weapon`), pero la KB usa `great_weapon` 94 veces frente a 2 y 2B usa 70 frente a 3: 2A era
   la excepción. Sin cambio de comportamiento.
2. **Scythe retirado de `dreamwalkers-cult-of-morr-fbg` Hero Equipment List.** No está en
   ninguna de las tres listas de la fuente (18 filas cotejadas), y el paquete ya modela el
   acceso real: `priest-of-morr` lo lleva en `fixed_equipment: [dagger, scythe]` con su
   restricción («May only be armed with a Dagger and a Scythe») y la regla de banda
   `band--special-equipment-scythe` recoge el equipo especial. En la lista ofrecía un Scythe
   a 0 gc a todos los héroes.

**Adjudicados (12, con motivo en el propio auditor):** 7 reglas cuyo nombre se deriva de la
prosa y citan una sección que sí existe en la página (`band--bow-restrictions`, `Mount
option`, los contenedores de skills…), 3 reglas de banda nombradas a partir de su leyenda o
prosa sin encabezado propio (`band--naggaroth-prices`, `band--rememberer-skills`,
`band--witch-hunter-hired-swords`) y `blessed_water` ↔ «Holy Water» de
`vampire-hunters-of-sylvania-lotd5` (la nota del ítem documenta el nombre de la fuente).

Otras dos convenciones de la fuente que el auditor respeta y que parecían hallazgos:
las skills del culto Slayer y del Clan Moulder se ingieren como una regla que enumera la
lista, y los nombres de banda se validan contra el `mordheimer_name` del manifest (el
índice), no contra la prosa de la página.

## Hechizos, Hired Swords y Dramatis Personae (2026-09-16 00:00)

Al auditor de contenido le faltaban justo las tres dimensiones que la KB modela en
**catálogos aparte** y no en el paquete: las **listas de hechizos** (`catalog/magic-2a.yaml`),
el **acceso a Hired Swords** y el **acceso a Dramatis Personae** (los stat blocks viven en
`catalog/hirelings`, que 2A no posee). Se añadieron dos secciones al auditor, con esta
cobertura real (medida, no supuesta, con `build/cache/probe_2a_coverage.py`):

```
hechizos:            69/69 emparejados 1:1 con la página · 69/69 dificultades comparadas
dramatis personae:   4 bandas con enunciados de acceso · 6/6 mencionados en las reglas
hired swords:        15 bandas con enunciados de acceso · 0 nombres ofrecidos sin ingerir
```

El cotejo de hechizos compara **nombre y dificultad** contra la sección de la página, en las
dos direcciones (hechizo del YAML ausente en la fuente, y hechizo de la fuente no ingerido),
y exige `name_i18n.es`. El de hirelings hace lo propio con cada enunciado que concede o
prohíbe Hired Swords / Dramatis Personae: cada nombre ofrecido tiene que estar en la prosa
del paquete, y cada nombre ingerido tiene que resolver contra un catálogo de hirelings (KB +
staging 2B, la misma pool que el validador usa para ítems).

**Corregido:**

3. **`druchii-mic` no tenía regla de acceso a Hired Swords.** La fuente imprime el párrafo
   «*Due to their merciless nature a Druchii warband may only employ the following Hired
   Swords: …*» (bajo el encabezado **Henchmen**, con sus niveles *Official* / *Unofficial,
   but published by SG* / *Lustria* / *Khemri* / *Completely unofficial*). El paquete no lo
   recogía en ninguna regla: la única mención a hired swords era incidental
   (`band--kindred-hatred` dice «…including High Elf Hired Swords»), que bastaba para
   satisfacer la comprobación de presencia y **no** la de nombres. Se añadió
   `band--hired-swords` (id/nombre/ES ya establecidos en 2A: «Espadas a Sueldo»,
   `applies_to.band: true`, `runtime` con `scope: 'NO'` y motivo de elegibilidad), declarada
   en `band.yaml` y con los 16 nombres de la fuente en EN y ES.
4. **Dos hechizos con `difficulty: 0`.** «Servants Eternal» (`lore.dreaded-scrolls-of-nagash`)
   y «Death Holds No Fear» (`lore.funerary-rites-lotd5`) imprimen **Difficulty: Auto** en la
   fuente, y se habían ingerido como `0`. La KB nunca usa un número ahí (sus valores son
   5-10 y la cadena `auto`, 6 casos) y `0` no significa nada para el motor: un hechizo que
   siempre funciona quedaba a dificultad cero. Corregidos a `difficulty: auto`. El chequeo
   era ciego a esto (solo comparaba dificultades numéricas en ambos lados); ahora parsea
   `Auto` y compara la dificultad **siempre**, así que esta clase se detecta sola (probado:
   con los datos antiguos el auditor reportaba exactamente estos dos).

**Dos huecos de catálogo, con motivo escrito (no son defectos del paquete).** El enunciado de
acceso de `ogre-hunting-party-web` nombra cinco Hired Swords y dos de ellos no existen en
ningún catálogo —ni en las páginas de hired swords de mordheimer (grades 1b/1c/2a), que es de
donde la KB los ingiere—:

- **Gnoblar Botcher**: uno de los tres únicos que la banda puede contratar.
- **Ogre Slaver**: nombrado en la misma regla. No confundir con `Ogre Slave Master` del
  catálogo (90 gc, contratable por Poseídos/Carnaval del Caos/Hombres Bestia): es **otro**
  hireling, no una variante de nombre.

El paquete ingiere la redacción de la fuente tal cual, así que el hueco es de **catálogo**:
la app no puede ofrecer esos dos hirelings hasta que existan sus stat blocks. Ambos quedan
como hallazgos **adjudicados y visibles** (`audit_2a_sources.py --all`), no ocultos.

**Convenciones de nombre que el auditor resuelve** (para no reportarlas como huecos):
`High Elf Mage` de la fuente ≡ `Elf Mage` del catálogo (mordheimer lo indexa así; sus reglas
son *Fey* + *Sorcery* + *Wanderer* + *Wizard* con hechizos Djed'hi), y los enunciados que
nombran **bandas** o **tablas** en vez de hirelings («as if they were Human Mercenaries»,
«roll on the Hero's Advancement Table») no son ofertas de contratación.

**Pruebas negativas** (`build/cache/negative_test_2a_hirelings.py`, en proceso y con
restauración): quitar `band--hired-swords` de druchii → salta `hireling-name-absent` por cada
Hired Sword del catálogo que la fuente ofrece; quitar un nombre del catálogo de la prosa →
lo mismo; inyectar un nombre desconocido solo en la fuente → `hireling-name-absent`;
inyectarlo también en el paquete → `hireling-not-in-catalog`.

## Re-verificación de precios contra las fuentes (2026-09-16)

Segunda pasada sobre el auditor de contenido, con el mismo criterio que la
re-verificación de 2B: **el auditor no basta como prueba si no se sabe cuánto
compara ni si es capaz de fallar**. Se reescribió la sección de listas de equipo y
se añadió el cotejo de los precios del bloque Special Equipment.

**Huecos cerrados**

1. **Listas publicadas bajo `h2`.** El auditor solo miraba encabezados `h3` con sufijo
   «equipment list», así que cinco listas nunca se habían cotejado: `ogre-equipment-list`
   y `gnoblar-equipment-list` (Ogre Hunting Party), `outlaws-equipment-list`,
   `sorcerous-society-equipment-list` y `protectorate-equipment-list`. 73 filas, ahora
   comparadas y coincidentes. El auditor pasó a ser **dirigido por la lista**: cada lista
   del paquete debe tener su sección en la página (`list-without-source` si no), un
   encabezado que solo abre listas hijas no aporta filas propias, y una lista que tiene
   filas propias y contiene una sublista (Protectorate + Huntsman) sigue siendo lista.
2. **Divisa.** Clan Moulder tarifa en **warp tokens**; el parser solo entendía `N gc`,
   así que sus 23 filas nunca se compararon. Ahora se leen `gc`, `crowns` y `wt`, y las
   filas gratuitas (`Free!` ↔ `cost: 0`) se comparan como importe 0.
3. **Fórmulas y precios relativos.** Una tirada impresa en la lista se escribe como
   expresión de dados (`cost: 15+D6`), una cifra fija con fórmula en el bloque Special
   Equipment manda por la lista (`cost: 20`, fórmula en `notes`) y un múltiplo
   (`3x cost`, `2 x price`) se queda en `null`. Antes, ocho filas con fórmula estaban
   guardadas como `null` y el auditor las daba por no comparables: **corregidas**
   (detalle y criterio en `discrepancy-verdicts.md` §2.1).
4. **Precios del bloque Special Equipment.** Los precios de los objetos propios de cada
   banda viven en el catálogo como prosa (`availability_note`) y ningún auditor los
   comparaba con la página: nueva sección 4b, 34 de 35 cotejados, sin errores (el único
   desacuerdo es el erratum documentado del Silver-tip Stake).
5. **Doble extracción.** Cada fila se coteja contra la tabla del HTML y, si la tabla no
   la lleva, contra la extracción plana (`build/cache/2a-sources/text/`), que imprime el
   nombre y su precio en líneas consecutivas.
6. **Listas delegadas al reglamento: ninguna en 2A.** Se buscaron las frases de reenvío
   al manual en las 19 páginas (2B sí tiene tres, en Karak Azgal): en 2A el hueco
   equivalente era el de las listas `h2`.
7. **Perfiles impresos dentro de un bloque Special Equipment.** Las monturas y los
   familiares llevan su propia fila de atributos en su sección (`M WS BS S T W I A Ld`),
   y esa fila no la veía nadie: `audit_2a.py` lee los bloques `div.fighter` (perfiles de
   guerrero) y estas secciones son prosa. Nueva sección 4c: la fila se compara con el
   texto del ítem como subsecuencia ordenada de sus números. Encontró un hueco real (el
   perfil del Pigback Mount, completado a mano en EN y ES) y hoy compara 3 filas con 0
   hallazgos.
8. **Aclaraciones entre paréntesis en la prosa de reglas.** La KB conserva `(i.e. …)`,
   `(thus, …)` o `(no save allowed)` y descarta los ejemplos resueltos. De las reglas
   sólo se cotejaba el nombre: tres aclaraciones se habían condensado fuera del paquete
   (Stampede, Back-up Records del Rememberer y el matiz de Monster Slayer). Nueva
   sección 4d: cada regla aporta la sección que nombra su `source.section` y cada
   aclaración de esa prosa debe existir en el paquete (cifras normalizadas a palabras).
   20 aclaraciones comparadas, 0 hallazgos; restauradas en EN y ES (detalle en
   `discrepancy-verdicts.md` §3.2).

**El auditor ahora puede fallar** (y se prueba que falla).
`tests/knowledge/test_2a_source_audit.py` (13 pruebas) inyecta sobre una copia
desechable bajo `build/cache`: un precio equivocado, una fila de la página que el
paquete pierde, un precio de tirada aplanado a `null`, una lista sin encabezado en la
página, un precio de Special Equipment contradicho, un perfil de ítem borrado y una
aclaración de regla condensada; cada caso debe producir su hallazgo. Añade pruebas
unitarias de la lectura de celdas (`10 wt`, `1st free/2 gc`, `35 wt (70 for a brace)`,
`Free!`, `15 + D6 gc`, `3x cost`) y del reparto
contenedor/listas hijas. La salida del auditor imprime además la cobertura (listas,
filas y precios comparados), para que «0 hallazgos» no se confunda con «0 comprobado».

```
sources/2A vs cached pages: 0 open finding(s), 13 adjudicated
equipment coverage: 47 list(s) matched (5 published under an h2); 558 printed row(s)
  compared (558 matching, 0 without a price cell); 0 list entr(y/ies) absent from the tables
rule prose: 20 parenthetical clarification(s) of the rule sections compared with the
  rule and lore texts
special-equipment coverage: 35 catalogue item(s), 34 with a price on the page compared;
  3 profile row(s) printed inside those sections compared with the item text
```

Los 13 adjudicados son los 12 anteriores más el `special-price-mismatch` del
Silver-tip Stake, adjudicado en el propio auditor con el verdicto 1 de
`discrepancy-verdicts.md`.

## Estado verificado (2026-09-16)

```
derive_kb_contract.py --tree 2A     → 0 claves, 0 formas y 0 dominios de valor fuera de la KB
derive_kb_contract.py --tree 2B     → ídem
audit_kb_conformance.py --tree 2A   → 0 desviaciones (+0 informativas)
audit_kb_conformance.py --tree 2B   → 0 desviaciones (+1 informativa: trait.spectral-touch,
                                      declarado en registry/bindings.yaml de la KB)
audit_2a.py                         → 19 bandas, 0 problemas
  audit_2a_sources.py               → 0 hallazgos abiertos, 14 adjudicados; cobertura 47
                                      listas / 558 filas / 34 precios de eq. especial /
                                      3 filas de perfil de ítem / 22 aclaraciones de regla
ingest_2a.py validate               → 19 filas, 0 problemas
ingest_2b.py validate               → 60 filas, 0 problemas
format_yaml.py --check 2A + 2B      → 356 ficheros, 0 would change, 0 failures
pytest tests/knowledge tests/web    → 503 pasan, 2 fallan en tests/web/parity
                                      (port desktop→web, ajeno a 2A/2B)
```

## Reproducir

```bash
python tools/knowledge/derive_kb_contract.py --tree 2A     # contrato medido vs staging
python tools/knowledge/audit_kb_conformance.py --tree 2A   # forma clave a clave
python tools/ingestion/audit_2a.py                         # costes, statlines, skills
python tools/ingestion/audit_2a_sources.py                 # contenido y precios vs páginas cacheadas
python tools/ingestion/audit_2a_sources.py --all           # incluye los adjudicados con su motivo
python -m pytest tests/knowledge/test_2a_source_audit.py   # el auditor falla de verdad (5 inyecciones)
python build/cache/probe_2a_coverage.py                    # cobertura: hechizos y DR/hirelings
python build/cache/negative_test_2a_hirelings.py           # pruebas negativas (restauran)
python tools/knowledge/strip_rule_ref_restatements.py      # idempotente: 0 a retirar
python tools/ingestion/ingest_2a.py validate
python -m pytest tests/knowledge tests/web -q
```

La auditoría es de solo lectura salvo `format_yaml.py --write`; el auditor marca las clases
informativas aparte para que su código de salida signifique «hay algo que corregir».
