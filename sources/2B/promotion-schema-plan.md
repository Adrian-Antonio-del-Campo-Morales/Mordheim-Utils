# Contrato editorial para la promoción de los catálogos staging 2A/2B

**Estado:** plan de promoción — qué extensiones de esquema hará falta aceptar en
`contracts/knowledge-editorial-v1` para que los catálogos staging validen al
incorporarse a la KB activa.

**Método:** los cuatro grupos de documentos staging (`sources/2A/catalog`,
`sources/2B/catalog`) se han validado contra los esquemas JSON oficiales que los
reclamarán al promoverse (mediante el mapping de `mordheim_knowledge.editorial_schemas`):

| Documento staging | Esquema de destino |
| --- | --- |
| `2B/catalog/hirelings/*.yaml` (4 ficheros, 28 perfiles) | `hireling-profile-hired-sword.yaml.schema.json` |
| `2A/catalog/magic-2a.yaml` (12 lores) | `campaign-magic.yaml.schema.json` |
| `2B/catalog/magic-2b.yaml` (11 lores) | `campaign-magic.yaml.schema.json` |
| `2A/catalog/items/*.yaml` (12 ficheros) | `catalog-items.yaml.schema.json` |
| `2B/catalog/items/*.yaml` (13 ficheros) | `catalog-items.yaml.schema.json` |

**Resultado:** 284 violaciones de esquema en 17 clases de desviación, repartidas
así: hirelings 2B 137, items 2A 64, items 2B 63, magic 2A 7, magic 2B 13.
Todas son extensiones deliberadas del staging; ninguna es un error de datos.
Se agrupan en **extensiones del documento raíz**, **extensiones del perfil/ítem**,
**nuevos vocabularios** y **forma de staging que debe normalizarse al promover**.

---

## 1. Extensiones del documento raíz

### 1.1 `status: staging` (todos los catálogos staging)

- **Esquema:** `defs.schema.json#/$defs/catalog_status` solo acepta
  `published` | `draft`.
- **Staging:** los 11 ficheros de catálogo staging llevan `status: staging`.
- **Decisión de promoción:** al fusionar en la KB los documentos pasan a
  `published` (los datos están verificados contra fuente), por lo que **esta
  desviación desaparece sola** y el esquema no necesita cambios. Si se quisiera
  conservar la marca durante una transición parcial, habría que añadir
  `staging` al enum — no recomendado.

### 1.2 Raíz de los ficheros de items: `status` no existe

- **Esquema:** `catalog-items.yaml.schema.json` raíz = `{schema_version, ruleset,
  items}` exacto (`additionalProperties: false`).
- **Staging:** 15 ficheros 2A y 1 de 2B (`kaz-runic-artefacts.yaml`) añaden
  `status` a la raíz.
- **Decisión:** **borrar `status` de la raíz al promover** (ver 1.1) y extender el
  esquema solo si se decide que los ficheros de items deban llevar ciclo de vida
  propio. Alternativa coherente con el contrato actual: no aceptar la extensión.

### 1.3 Documento de magia: campos raíz nuevos (magic-2a/2b)

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

## 3. Extensiones del ítem (2A y 2B)

Esquema `catalog-items.yaml.schema.json`; `item` = `{id, kind, name, name_i18n,
effect, effect_i18n, combat_status, mechanic_id, source_refs}`.

### 3.1 `rarity` (52 ítems) y `availability_note` (+i18n) (36)

- **Qué es:** rareza impresa por la fuente (p. ej. "Rare 6") y prosa de
  disponibilidad por lista de equipo ("only available to…").
- **KB:** la rareza vive en `catalog/campaign/trading-and-rarity.yaml` (por
  categoría de ítem, no por ítem) y la disponibilidad en las listas de banda.
- **Decisión:** **aceptar ambas como opcionales** (`rarity: string` verbatim de
  la fuente, `availability_note`/`availability_note_i18n`: display_text). Son el
  valor editorial que las reglas de trading necesitarán cuando las bandas 2A/2B
  entren en campaña; rehúsarlas obligaría a reescribirlas en cada banda.
  Alternativa estricta: migrar `rarity` a `trading-and-rarity.yaml` como filas
  por ítem — más trabajo y otro cambio de esquema allá. **Recomendada: aceptar.**

### 3.2 `special_rules` y `rules` (26 + 4 ítems)

- **Qué es:** reglas de uso del ítem impresas en la fuente (p. ej. la Duda del
  Umbral del corpse-liquor, reglas de las runas de Karak Azgal).
- **KB:** los ítems con reglas hoy se modelan vía `mechanic_id` o `combat_status`
  cuando existe mecánica; el resto de prosa no tiene sitio.
- **Decisión:** **aceptar** `rules: array[rules-ref o prosa]` opcional. Es
  simétrico con el modelo de bandas (prosa + clasificación runtime) y necesario
  para los artefactos únicos (kaz-runic-artefacts) que ya llevan bindings.

### 3.3 `unique` (6 ítems, kaz-runic-artefacts)

- **Qué es:** marca de artefacto único (una sola unidad en campaña).
- **Decisión:** **aceptar** como `boolean` opcional. Contenido real de la fuente
  (la tabla de artefactos rúnicos dice "unique"), sin equivalente KB hoy.

### 3.4 `kind` fuera del enum (15 ítems 2A)

`miscellaneous` (13), `mount` (1), `ammunition` (1) no están en el enum KB
(`close-combat-weapon, ranged-weapon, armour, shield-or-defence,
combat-equipment, material-or-upgrade, trollheim-equipment, out-of-scope`).
- **miscellaneous:** la KB lo reparte entre `combat-equipment` y
  `material-or-upgrade` según el ítem; pero 13 ítems staging son genuinamente
  misceláneos (farol, pala, pértiga…). **Aceptar `miscellaneous`** en el enum
  (o migrar uno a uno; aceptar es más honesto con la fuente).
- **mount** y **ammunition:** la KB modela monturas como bestias (registry) y
  las municiones como `material-or-upgrade`. **Decisión:** migrar `mount` al
  bestiario/registry al promover (1 ítem) y `ammunition` a
  `material-or-upgrade` (1 ítem); **no** aceptar esos dos kinds nuevos.

---

## 4. Forma de staging que debe normalizarse al promover (sin tocar esquema)

| Forma staging | Acción de promoción |
| --- | --- |
| `status: staging` raíz | → `published` (o borrar en items, ver 1.2) |
| `lore_assignments` dict por banda (2B) | → filas KB `rows[]` |
| `lore_assignments`/`starting_experience` por perfil (9 sacerdotes) | → `rows[]` en campaign/magic; campo perfil opcional |
| `kind: dramatis-personae` / `priest` mezclados en hired-swords 2B | → repartir en `hired-swords/` y `dramatis-personae/`; sacerdotes como `hired-sword` (2.5b) |
| Perfiles name-only con `null` (2) | → catálogo DP con `out_of_scope_reason` |
| Doc auxiliar `existing_lores/new_lores/unresolved` (2B) | → no se promociona |
| `kind: mount` / `kind: ammunition` (1+1 ítems) | → registry de bestias / `material-or-upgrade` |
| ids `hireling.dramatis.*` en ficheros hired-sword | → desaparecen al repartir catálogos |
| `[]` vacío en `missing-item-stubs.yaml` | → el fichero no se promociona (los stubs ya resueltos viven en sus catálogos definitivos) |

---

## 5. Resumen de cambios de esquema propuestos

En `contracts/knowledge-editorial-v1` (cinco ficheros):

1. **`hireling-profile-hired-sword.yaml.schema.json`**: añadir `hire_fee`,
   `available_to`, `choice_groups`, `starting_experience` (opcionales); `notes`
   opcional en `fixed_items[]`; enum de grado + `'2b'`.
2. **`hireling-profile-dramatis-personae.yaml.schema.json`**: enum de grado +
   `'2b'` (por si algún DP 2B entra por aquí).
3. **`campaign-magic.yaml.schema.json`**: añadir `casting_rules_note` y
   (`magical_failure_table`, `_note`, `_source`) opcionales a la raíz.
4. **`catalog-items.yaml.schema.json`**: añadir `rarity`, `availability_note`,
   `availability_note_i18n`, `special_rules`/`rules`, `unique` (opcionales);
   enum de kind + `'miscellaneous'`.
5. **`defs.schema.json`**: sin cambios (catalog_status queda como está; los
   documentos promocionados pasan a `published`).

Y en `defs.schema.json`/grados: si los esquemas de campaña que referencian grado
(hired-swords-and-dramatis) fijan el enum, añadir `'2b'` también ahí.

## 6. Orden de trabajo recomendado

1. Extender los esquemas (§5) con sus tests de contracto
   (`test_editorial_schemas` cubre esquema↔código).
2. Normalizar las formas de staging de §4 con un script idempotente
   (`tools/knowledge/normalize_staging_for_promotion.py`) y re-validar staging
   contra los esquemas ya extendidos: debe bajar de 284 a 0 salvo las formas que
   la promoción elimina (que se validan tras la fusión, no antes).
3. Fusionar árbol a árbol (bandas primero — ya validan 0 violaciones —, luego
   hirelings, items, magic), regenerando en cada paso los índices
   (`effect_ids`, `lore_assignments.rows`).
4. Ejecutar la batería completa (validate/audit/conformance/pytest) sobre la KB
   ampliada y retirar `UNCOVERED_DOCUMENTS` de `registry/bindings.yaml`,
   cuyo gate ya está previsto para la promoción.
