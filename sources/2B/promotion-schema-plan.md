# Contrato editorial para la promoción de los catálogos staging 2A/2B

**Estado:** plan de promoción — qué extensiones de esquema hará falta aceptar en
`contracts/knowledge-editorial-v1` para que los catálogos staging validen al
incorporarse a la KB activa, y qué formas se normalizan antes (paso ya
ejecutado: ver §0 y §4).

**Método:** los documentos staging (`sources/2A/catalog`, `sources/2B/catalog`)
se validan contra los esquemas JSON oficiales que los reclamarán al promoverse
(mapping `CATALOGUE_TARGETS` de `mordheim_knowledge.staging_contract_audit`, con
su mapping de documentos en `mordheim_knowledge.editorial_schemas`):

| Documento staging | Esquema de destino |
| --- | --- |
| `2B/catalog/hirelings/*.yaml` (4 ficheros, 23 perfiles) | `hireling-profile-hired-sword.yaml.schema.json` |
| `2B/catalog/hirelings/dramatis-personae/*.yaml` (5 perfiles) | `hireling-profile-dramatis-personae.yaml.schema.json` |
| `2B/catalog/hired-swords-and-dramatis-2b.yaml` (26 entradas) | `campaign-hired-swords-and-dramatis.yaml.schema.json` |
| `2A/catalog/magic-2a.yaml` (12 lores) | `campaign-magic.yaml.schema.json` |
| `2B/catalog/magic-2b.yaml` (10 lores) | `campaign-magic.yaml.schema.json` |
| `2A/catalog/items/*.yaml` (14 ficheros) | `catalog-items.yaml.schema.json` |
| `2B/catalog/items/*.yaml` (18 ficheros) | `catalog-items.yaml.schema.json` |
| `2A/catalog/trading-post-2a.yaml` (35 entradas) | `campaign-trading-post.yaml.schema.json` |
| `2B/catalog/trading-post-2b.yaml` (109 entradas) | `campaign-trading-post.yaml.schema.json` |

**Resultado (aplicado):** las dos pasadas están verdes — **0 clases abiertas en
2A y en 2B** — con los catálogos staging ya en la forma de promoción: items y
mercado (§3), hirelings con su reparto de familia y su lado de campaña (§2, §7) y
magia con su envoltura y sus reprints (§1, §7). Las *clases* siguen fijadas en
`tests/python/knowledge/test_editorial_schemas.py` (`STAGED_CATALOGUE_CLASSES`, ahora
vacío en los dos árboles), así que una clase nueva falla el test y obliga a
actualizar este plan. El único fichero que la promoción deja atrás está declarado
en `staging_contract_audit.NOT_PROMOTED`.

---

## 0. Lo que ya está hecho (paso ejecutado)

1. **Vocabulario abierto** (`status`, `categories`/`grade`, `sources[].manual`,
   `profiles[].source_path`): normalizado en los tres árboles y el vocabulario
   nuevo declarado con su decisión
   (`staging_contract_audit.ACCEPTED_OPEN_VALUES`, `registry/sources.yaml`).
2. **`status` de los catálogos (§1)**: los documentos de items y hirelings no
   llevan `status` en la KB — se elimina; los documentos que *son* un documento KB
   nuevo (el mercado, la magia) llevan `draft`, el valor que el contrato reserva
   para contenido sin confirmar.
3. **Los hechos de mercado de los items (§3.1)**: `rarity`, `availability_note`,
   `availability_note_i18n` y `unique` salen del ítem y pasan al **catálogo de
   mercado staging** (`catalog/trading-post-2a.yaml`, `-2b.yaml`), una entrada por
   ítem en la forma exacta de `catalog/campaign/trading-post.yaml`. El ítem se
   queda con identidad, texto impreso, `kind` y procedencia.
4. **La prosa de reglas del ítem (§3.2)**: `special_rules` y `rules` se pliegan en
   `effect` / `effect_i18n.es` (el único campo de prosa del contrato de ítem),
   conservando cada nombre de regla y su texto en los dos idiomas.
5. **Los `kind` fuera del enum (§3.4)**: reclasificados ítem a ítem
   (`miscellaneous`/`mount` → `combat-equipment`, `material-or-upgrade`,
   `out-of-scope`). El enum KB no se ha tocado.
6. **Tres extensiones de contrato sí aceptadas (§5)**, cada una siguiendo un
   patrón que la KB ya tiene.

Las herramientas que lo hacen: `tools/ingestion/normalize_staging_for_promotion.py`
(pases `status`, `market`, `items`; idempotente) sobre
`mordheim_knowledge.staging_promotion`, más `tools/knowledge/maintenance/format_yaml.py` para la forma
canónica.

---

## 1. Extensiones del documento raíz

### 1.1 `status: staging` (todos los catálogos staging)

- **Esquema:** `defs.schema.json#/$defs/catalog_status` solo acepta
  `published` | `draft`.
- **Decisión (aplicada):** el vocabulario `staging` desaparece. Cada documento
  lleva lo que lleva su destino KB: los ítems y los hirelings **nada** (los
  ficheros KB de esas familias no tienen `status`), y los documentos nuevos
  (mercado, magia) `draft` — el valor que `docs/guides/campaign-knowledge.md` reserva a
  lo no confirmado. Fusionar con el documento KB publicado es lo que los publica.

### 1.2 Raíz de los ficheros de items: `status` no existe

- **Esquema:** `catalog-items.yaml.schema.json` raíz = `{schema_version, ruleset,
  items}` exacto (`additionalProperties: false`).
- **Decisión (aplicada):** `status` se borra de la raíz de los 15 ficheros de
  items que lo llevaban. El esquema no cambia.

### 1.3 Documento de magia: campos raíz nuevos (magic-2a/2b)

> **Aplicado:** las propuestas de esta sección quedaron **rechazadas** donde la KB
ya tiene sitio para el dato; lo que se hizo está en §7.2.

Esquema `campaign-magic.yaml.schema.json` raíz = `{schema_version, ruleset,
catalog, status, casting_rules, lores, lore_assignments, pending_lores, effect_ids}`.

| Campo staging | Dónde | Qué aporta | Propuesta |
| --- | --- | --- | --- |
| `casting_rules_note` | 2A y 2B | Prosa de la fuente que matiza las reglas de lanzamiento (p. ej. variantes Miracle Workers). | **Aceptar** como `string` opcional. La KB ya modela notas editoriales análogas (`note` en lores). |
| `magical_failure_table` + `_note` + `_source` | 2A | La tabla de fallo mágico alternativa de Letters of the Damned/Sylvania. | **Aceptar** los tres como campos opcionales (array de filas + texto + source_refs). Es contenido real de la fuente; rehúsarlos perdería datos. |
| `lore_assignments` en forma **dict por banda** | 2B | `{band: lore}` directo, en vez del shape KB `{rows: [...], source_refs: [...]}`. | **No aceptar la forma dict**: al promover, reescribir a filas KB (`rows` con `wizard/profile_id/band/lore`) — es una transformación mecánica ya posible con los datos actuales. |

Campos `required` que faltan en staging (`casting_rules`, `lore_assignments`,
`pending_lores`, `effect_ids`, y en 2B además `rows`/`source_refs`): no son
extensiones — son datos que **deben generarse en la fusión**:
- `lore_assignments`: componer las filas KB desde el dict 2B + los assignments
  de bandas 2A (`existing_lores`).
- `casting_rules`: copiar la regla de lanzamiento canónica de la KB
  (`campaign.magic.casting`) o declarar la variante de la fuente si la hay.
- `pending_lores`: `[]` (todo lo staging está resuelto o declarado).
- `effect_ids`: enumerar los effect ids de los lores promovidos.

### 1.4 Segundo documento de transición en `magic-2b.yaml` (`existing_lores`,
`new_lores`, `unresolved`)

Es un documento YAML auxiliar del flujo de ingesta, no contenido. **No se
promociona**: retirarlo al fusionar (su información viva se convierte en
`lore_assignments.rows` y en el propio `lores`). El esquema no necesita saber de él.

---

## 2. Extensiones del perfil de hireling (2B)

Esquema `hireling-profile-hired-sword.yaml.schema.json`. Desviaciones del staging:

> **Aplicado:** las propuestas de aceptación de §2.1–§2.4 y §2.8 quedaron
rechazadas (el dato tenía sitio en la KB); lo que se hizo está en §7.1.

### 2.1 `hire_fee` (19 perfiles) — la extensión principal

- **Qué es:** `{kind: base_plus_upkeep, hire: N, upkeep: N}` — la tarifa impresa
  en la fuente ("N gold crowns to hire + N upkeep"), verificada contra fuente en
  la pasada de cotejo.
- **KB:** ningún fichero de hired swords (core/1a/1b/1c/2a) modela la tarifa hoy.
- **Decisión:** **aceptar en el esquema** como propiedad opcional del perfil.
  Es el hueco de modelado más claro que trae el staging 2B (la tarifa es dato
  esencial de un hired sword) y viene de fuente verificada. Requiere además
  extender `hireling-profile-dramatis-personae.yaml.schema.json` si algún DP la
  llevara.

### 2.2 `available_to` (28 perfiles)

- **Qué es:** lista de bandas/grupos que pueden contratar al hireling — la regla
  "May be Hired" de cada bloque fuente.
- **KB:** la elegibilidad hoy vive solo en la prosa de las bandas.
- **Decisión:** **aceptar** como propiedad opcional (`array[string]` de band ids
  o grupos del registry). Es el valor editorial que el loader necesitará para
  filtrar contrataciones; documentar que la autoridad semántica sigue siendo el
  catálogo de grupos del registry.

### 2.3 `choice_groups` (2 perfiles: grade-2b, miracle-workers)

- **Qué es:** agrupación de opciones de equipamiento/habilidades con exclusividad
  mutua que la fuente imprime como "elige una de".
- **Decisión:** **aceptar** como propiedad opcional del perfil (array de grupos
  con `pick: N` y opciones). Alternativa: normalizar a las listas de equipo KB…
  pero el shape de `equipment-access` de banda no encaja en un hireling. Aceptar.

### 2.4 `fixed_items[].notes` (38 apariciones)

- **Qué es:** nota editorial por ítem fijo — sobre todo resoluciones "counts as"
  (p. ej. «Harpoon gun counts as harpoon crossbow», «resolves to the KB item
  `beastlash`»).
- **KB:** `equipment.fixed_items[]` solo admite `{item_id, quantity}`.
- **Decisión:** **aceptar `notes: string` opcional** en el ítem fijo. Es el mismo
  patrón que la KB ya usa en los listados de equipo de banda (`equipment-access`
  admite `notes` por ítem); hacerlo simétrico es coherente.

### 2.5 `kind` distintos de `hired-sword` (15) y `normalization_status` (2)

- `dramatis-personae` (4): el staging reúne hired swords y DP en los mismos
  ficheros 2B. Al promover, **repartir en los dos catálogos KB** (`hired-swords/`
  vs `dramatis-personae/`) y usar el esquema DP para los segundos — el esquema DP
  ya acepta el `const: dramatis-personae`. Sin cambio de esquema.
- `priest` (9, miracle-workers): nuevo kind. El DP schema permite `kind` distinto
  vía `out_of_scope_reason`… pero estos sacerdotes tienen perfil completo.
  **Decisión:** o (a) añadir `priest` como kind válido con su propio sub-esquema
  (recomendado: los 9 sacerdotes son hired swords con `lore_assignments` propios,
  la fuente los imprime en un capítulo "Miracle Workers" con tarifa y stats), o
  (b) reescribirlos como `hired-sword` con las extensiones 2.1/2.2 y el nuevo
  campo `lore_assignments` por perfil (ver 2.6). **Recomendada: (b)** — menos
  superficie de contrato.

### 2.6 `lore_assignments` y `starting_experience` por perfil (9 sacerdotes)

- **Qué es:** el lore que lanza el sacerdote y su experiencia inicial (la fuente
  imprime ambas cosas en cada bloque).
- **KB:** los assignments viven a nivel de documento (`lore_assignments.rows`).
- **Decisión:** al promover, **mover los assignments de perfil al documento
  `campaign/magic.yaml`** (filas KB) y `starting_experience` a un campo opcional
  del perfil (**aceptar** — el staging de bandas ya usa experience inicial por
  perfil; es el mismo concepto). El campo `lore_assignments` por perfil **no se
  acepta** en el esquema de hirelings.

### 2.7 Perfiles `name-only` (2: Strigani Seer Necromancer, Snerik)

`characteristics`/`warband_rating`/`hire_fee` a `null`. El esquema exige
`characteristics` (required, type object) solo en hired-sword; el DP schema no la
exige. **Decisión:** al promover, usar el catálogo DP para estos dos registros
(la fuente solo los *menciona*; el status `name-only` es fiel) o aceptar
`characteristics: null` mediante `type: [object, 'null']`. **Recomendada:** DP +
`out_of_scope_reason` explicando la fuente, sin cambiar el esquema. El id
`hireling.dramatis.*` ya cumple el patrón del esquema DP (los 13 fallos de
`pattern` son de ids en ficheros hired-sword; al repartir, desaparecen).

### 2.8 `grade: '2b'` (32)

Los enums de grado de ambos esquemas terminan en `'2a'`. **Aceptar `'2b'`** en
`hireling-profile-hired-sword` y `hireling-profile-dramatis-personae` (y en los
esquemas de banda si aún no lo traen: los paquetes de banda ya validan, porque el
esquema `band.yaml` declara el grado como string libre — verificar al tocar).

---

## 3. Extensiones del ítem (2A y 2B) — RESUELTAS sin tocar el esquema de ítem

Esquema `catalog-items.yaml.schema.json`; `item` = `{id, kind, name, name_i18n,
effect, effect_i18n, combat_status, mechanic_id, source_refs}`. **No se ha
añadido ni un campo**: cada extensión que este plan proponía aceptar tenía ya un
sitio en la KB, y la norma es que la forma de la KB prevalece.

### 3.1 `rarity` (52 ítems) y `availability_note` (+i18n) (36)

- **Qué es:** rareza impresa por la fuente ("Rare 6") y prosa de disponibilidad
  por lista de equipo ("only available to…"), con su precio.
- **KB:** el precio, la rareza y la restricción de compra de un ítem viven en
  `catalog/campaign/trading-post.yaml` — **una entrada por ítem** (335 de 335 en
  la KB), con `price`, `availability: {kind, rarity}` y
  `restrictions[]` (`warband_only`, `heroes_only`, `condition`…).
- **Decisión (aplicada):** el ítem pierde esos campos y el árbol gana un
  **documento de mercado staging** con una entrada por ítem en esa forma exacta:
  `catalog/trading-post-2a.yaml` (35) y `-2b.yaml` (109). El documento lo genera
  `staging_promotion` desde los ficheros de items y las listas de banda, y una
  entrada ya escrita se conserva tal cual en las siguientes pasadas.
- **Detalles que importan:** un precio impreso en una moneda que la KB no modela
  (25 *warp tokens* de Clan Moulder) se registra como `price: null` con la prosa
  de la fuente verbatim en `restrictions[].note`, porque `base_gc` es coronas de
  oro por contrato; un ítem que la fuente no vende (`unique`, retenedores,
  criaturas) queda `not_sold` con la nota que lo dice, como los 78 `not_sold` de
  la KB.

### 3.2 `special_rules` y `rules` (26 + 4 ítems)

- **Qué es:** reglas de uso del ítem impresas en la fuente, en forma estructurada
  (`special_rules[]`: id, name, name_i18n, effect, effect_i18n) o como prosa
  (`rules`).
- **KB:** el ítem tiene **un** campo de prosa, `effect` (+`effect_i18n`).
- **Decisión (aplicada):** los dos se pliegan en `effect` y `effect_i18n.es`,
  conservando cada nombre de regla y su texto ("Nail in Boot: Si en la tirada…").
  Nada se pierde y el ítem no gana un campo que la KB no tenga.

### 3.3 `unique` (6 ítems, kaz-runic-artefacts)

- **Qué es:** marca de artefacto único (una sola unidad en campaña).
- **Decisión (aplicada):** la marca entra en la entrada de mercado —
  `availability: not_sold` + `restrictions[]: condition` con la nota de que la
  fuente imprime un solo ejemplar y se encuentra, no se compra. El enum de
  disponibilidad y el tipo de restricción son los de la KB.

### 3.4 `kind` fuera del enum (15 ítems 2A)

`miscellaneous` (13), `mount` (1), `ammunition` (1) no están en el enum KB
(`close-combat-weapon, ranged-weapon, armour, shield-or-defence,
combat-equipment, material-or-upgrade, trollheim-equipment, out-of-scope`).
- **Decisión (aplicada):** reclasificación ítem a ítem, declarada en la tabla
  `staging_promotion.ITEM_KINDS` (no una heurística en código): las criaturas y
  monturas a `out-of-scope` (como la KB guarda `warhound`, `war_boar`,
  `giant_wolf`), el equipo de warband a `combat-equipment`, la munición a
  `material-or-upgrade` (como `hunting_arrows`). El enum KB no cambia.

### 3.5 El catálogo de mercado (nuevo documento staging)

- **Destino:** `catalog/campaign/trading-post.yaml` (esquema
  `campaign-trading-post.yaml.schema.json`), que es de donde la prueba de rareza
  lee `availability.rarity` (`trading-and-rarity.yaml` lo nombra como su tabla).
- **Cobertura:** una entrada por ítem del árbol, igual que la KB (335 de 335).
  `id` con la convención KB (`campaign.trading-post.<item-id-con-guiones>`),
  `source_refs` copiados del ítem, `price` reconstruible
  (`base_gc`, `+ optional_variable_cost`, `multiplier`), `restrictions[]` con
  `warband_only` de la lista que lo vende y la prosa de compra verbatim.
- **Al promover:** las entradas se fusionan con las de la KB (una por ítem, sin
  duplicar `id`).

### 3.6 La auditoría de fuente 2A lee el mercado

`tools/ingestion/audit_2a_sources.py` comparaba el precio impreso con
`item.availability_note`; ahora lo lee de la entrada de mercado (la prosa verbatim
primero, el precio estructurado después), que es el único sitio donde vive. El
test `test_2a_source_audit` repunta el fichero de mercado al sandbox y muta la
entrada, no el ítem.

---

## 4. Forma de staging que debe normalizarse al promover (sin tocar esquema)

| Forma staging | Acción de promoción | Estado |
| --- | --- | --- |
| `status: staging` raíz | → lo que lleve su destino KB (§1) | **hecho** |
| `rarity` / `availability_note` / `unique` en el ítem | → entrada en el catálogo de mercado (§3.1, §3.3) | **hecho** |
| `special_rules` / `rules` en el ítem | → prosa de `effect` / `effect_i18n.es` (§3.2) | **hecho** |
| `kind: mount` / `kind: ammunition` / `miscellaneous` | → `out-of-scope` / `material-or-upgrade` / `combat-equipment` (§3.4) | **hecho** |
| `lore_assignments` dict por banda (2B) | → filas KB `rows[]` | **hecho** |
| `lore_assignments`/`starting_experience` por perfil (9 sacerdotes) | → `rows[]` en campaign/magic; `experience` en el perfil | **hecho** |
| `kind: dramatis-personae` / `priest` mezclados en hired-swords 2B | → repartir en `hired-swords/` y `dramatis-personae/`; sacerdotes como `hired-sword` (2.5b) | **hecho** |
| Perfiles name-only con `null` (2) | → catálogo DP con `out_of_scope_reason` | **hecho** |
| Doc auxiliar `existing_lores/new_lores/unresolved` (2B) | → no se promociona | **hecho** |
| ids `hireling.dramatis.*` en ficheros hired-sword | → desaparecen al repartir catálogos | **hecho** |
| `[]` vacío en `missing-item-stubs.yaml` | → el fichero no se promociona (los stubs ya resueltos viven en sus catálogos definitivos) | **hecho** (`NOT_PROMOTED`) |
| Colecciones flow de las 8 claves que la KB escribe en bloque | → secuencia/mapping en bloque (§7.3) | **hecho** |

---

## 5. Cambios de esquema: los tres aceptados, y los que no

**Aceptados** (cada uno sigue un patrón que la KB ya tiene; justificados en
`editorial_schema_audit.JUSTIFIED_FINDINGS` mientras la KB no los ejercite):

1. **Grado `'2b'`** en los dos esquemas de hireling (raíz y perfil): el
   vocabulario de grado ya separa las fuentes (`core`, `1a`, `1b`, `1c`, `2a`),
   y `2b` es la fuente que falta por entrar; los documentos staging ya lo usan.
2. **`notes` en `fixed_items[]`** del perfil de hireling: el campo que las
   listas de equipo de banda llevan en cada entrada (`notes`, `notes_i18n`), en
   su forma de texto.
3. **`experience`** en el perfil de hireling: el nombre y el tipo que
   `profiles.yaml` da a la experiencia inicial de un perfil.
4. **`note` en `eligibility`** del documento de campaña
   `hired-swords-and-dramatis`: el papel que `restriction.note` juega en
   `trading-post.yaml` — la regla impresa que las listas no pueden expresar.

**Rechazados** (la KB tiene sitio para el dato, así que el dato va allí y el
esquema no crece): `rarity`, `availability_note(+i18n)`, `special_rules`,
`rules`, `unique`, `miscellaneous` en el ítem; `hire_fee`, `available_to`,
`choice_groups`, `starting_experience` en el perfil de hireling (van a
`campaign/hired-swords-and-dramatis` como `hiring_fee`, `eligibility`,
`equipment.choices` y `experience`); `casting_rules_note` y
`magical_failure_table*` en la magia (la tabla es de la banda que la usa, y su
regla impresa — `band--vagaries-of-magic` — es su sitio).

## 6. Estado del trabajo y lo que queda

Hecho (todo lo que este plan abría):

1. Vocabulario abierto normalizado en los tres árboles, con su decisión
   declarada (`ACCEPTED_OPEN_VALUES`, `registry/sources.yaml`).
2. Documentos de mercado generados y validando 0 contra
   `campaign-trading-post.yaml.schema.json`.
3. Items 2A y 2B: **0 clases abiertas** (el fichero de stubs queda declarado
   fuera de la promoción).
4. Las extensiones de esquema de §5 con sus tests de contrato, y el auditor de
   fuente 2A leyendo el mercado.
5. **Hirelings 2B**: el reparto de familia, el documento de campaña y los
   perfiles en forma KB — todo aplicado por el pase `hirelings` (§7).
6. **Magia 2A y 2B**: envoltura, filas y reprints — todo aplicado por el pase
   `magic` (§7).

Lo que queda es la fusión árbol a árbol, que ya no requiere ninguna decisión de
forma: los documentos staging validan contra el esquema de su destino KB, así que
la fusión es copiar los registros en el documento que los reclama y regenerar los
índices que el documento destino ya tiene (`effect_ids`, `lore_assignments.rows`,
`availability_procedures`, `eligibility_semantics`).

## 7. Las decisiones aplicadas (hirelings y magia)

Las propuestas de aceptación de §1 y §2 quedaron **rechazadas** donde la KB ya
tiene sitio para el dato (§5). Lo que se aplicó, y dónde vive ahora:

### 7.1 Hirelings (pase `hirelings`)

| Forma staging | Destino aplicado |
| --- | --- |
| `hire_fee` | `hiring_fee`/`upkeep` de `catalog/hired-swords-and-dramatis-2b.yaml`; una tarifa que la fuente imprime en dinares conserva el importe y la divisa viaja en la expresión de `cost`, que es el campo que el contrato reserva para eso |
| `available_to` | `eligibility` de la misma entrada: los grupos del registry en `allow_groups`/`forbid_groups`, los warband ids literales en las listas de bandas, y **la regla impresa verbatim en `eligibility.note`** para lo que las listas no expresan |
| `choice_groups` | `equipment.choices` de la KB (`choose`, `options[].items`) |
| `starting_experience` | `experience`, el nombre que `profiles.yaml` ya usa |
| `lore_assignments` por perfil | filas de `campaign/magic.yaml`, con `band: null` y el perfil como `profile_id` |
| `kind: priest` + id `hireling.priest.*` | `kind: hired-sword` + `hireling.hired-sword.*` (decisión 2.5b): la fuente los imprime con stats, tarifa y plegarias propias, así que son Hired Swords del capítulo |
| Perfiles name-only | catálogo Dramatis con `normalization_status: out_of_scope` y `out_of_scope_reason`; sin entrada en el catálogo de contratación |
| `kind: dramatis-personae` en ficheros de hired-swords | `catalog/hirelings/dramatis-personae/grade-2b.yaml`, con su esquema |
| `rules: []`, `characteristics: null`, `warband_rating: null`, `equipment: {}` | se retiran: la ausencia declarada por omisión es la convención KB |

### 7.2 Magia (pase `magic`)

| Forma staging | Destino aplicado |
| --- | --- |
| `casting_rules_note` | se retira: la nota dice que ningún pack introduce reglas de lanzamiento nuevas, y `casting_rules` copia la regla canónica de la KB |
| `lore_assignments` dict por banda (2B) | filas KB (`wizard`/`profile_id`/`band`/`lore`) + `source_refs`; la tabla de asignaciones es editorial y está declarada en `magic_promotion.MAGIC_ASSIGNMENTS`, no inferida del nombre del perfil |
| `lore_assignments` por perfil (sacerdotes) | filas con `band: null` |
| `variant_of` / `variant_of_lore` | se retira la clave: la relación ya está en la `note` de la lore, y la variante se publica como lore propia con sus seis conjuros (patrón `lore.necromancy-restless-dead`) |
| `mirror_of_lore` (Taal & Rhya) | la lore **no se duplica**: comprobado que los seis rezos son la lista KB (con una diferencia de grafía en un nombre), el druida se enruta a `lore.prayers-of-taal` y la copia desaparece |
| `marks` (Manann) | se retiran: la regla `...rule.marks-of-manann` del perfil ya imprime las dos marcas con su texto en los dos idiomas |
| `inherited_spell_ids` + `replaces_lore` + `spells[].replaces` (Lothern) | la lore se **materializa**: los cinco conjuros heredados se copian de `lore.spells-of-the-djedhi` con ids propios y *Mistress of the Deep* (D8) sustituye a *Fleeting Shadows*, que es como la KB guarda sus reprints (`lore.onogal-rituals`) |
| `lore.charms-and-hexes` (Seer, Sylvania) con el mismo id que la lore KB | se renombra a `lore.charms-and-hexes-strigos` con sus `spell.*` renombrados y la variante documentada en la `note`: el merge no puede colisionar |
| `magical_failure_table*` (2A) | la tabla viaja a la regla `band--vagaries-of-magic` que tira en ella, en la prosa del `effect` con el patrón de los gráficos impresos del pack (`2D6 result: 2 - ...`), y el `reason` del efecto deja de apuntar al catálogo de magia |

### 7.3 Forma de colección (pase `shape`)

La KB escribe ocho claves como colección **bloque** y nunca como colección flow con
datos: `source_path` (534), `equipment_lists` (529), `rule_ids` (475) y
`skill_access` (344) como secuencia en bloque — el guion al mismo indent que la clave
(delta 0 en las 3 219 secuencias de los tres árboles) — y `source` (2 290),
`characteristics` (666), `name_i18n` (3 742) y `combat_traits` (437 `{}` más bloques
anclados) como mapping en bloque, con los hijos dos columnas dentro.

Staging escribía esas claves 441 veces inline (16 de ellas repartidas en varias líneas)
y 454 veces como mapping flow. El pase `shape` los reescribe a la forma de la KB —
entradas verbatim y en su orden, comillas respetadas (los `url` llegan entrecomillados
y con comas dentro), `[]`/`{}` intactos — y **verifica el documento entero después de
reescribir**: si el parseo cambia en cualquier otra cosa, el pase falla en vez de
aplicarse. Medido y aplicado: 895 colecciones en 30 ficheros (247 en 2A, 648 en 2B),
idempotente. La puerta es `--only shape` de `audit_staging_contract.py` y
`tests/python/knowledge/test_staging_collection_shape.py`.
