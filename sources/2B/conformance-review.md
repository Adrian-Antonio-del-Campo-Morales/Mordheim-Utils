# 2B ↔ KB shape conformance review (2026-09-15)

Auditoría de **forma** (no de contenido de juego) de los paquetes de `sources/2B`
(60 filas de manifiesto → 61 paquetes: el documento orco de Sartosa se dividió en dos,
ver la sección correspondiente) contra los patrones canónicos de la KB activa
(`sources/knowledge/bands/mordheim/*`) y el contrato
`sources/knowledge/registry/runtime-schema.yaml`.

Regla aplicada: **ninguna etiqueta, campo o valor que la KB no use**. Cuando la KB no
tiene un campo para un dato, el dato se conserva fuera del paquete (en este documento)
en lugar de inventar una clave.

## Método

Tres comprobaciones de solo lectura, ejecutables sobre el staging:

| Script | Qué compara |
|---|---|
| `build/cache/2b-sources/conform_audit_2b.py` | claves de `band.yaml`, gramática y runtime de reglas, tuplas de perfil, claves de `equipment-access` |
| `build/cache/2b-sources/conform_keys_2b.py` | formas anidadas KB vs 2B: tipos de perfil, juegos de claves de `characteristics`, claves de `roster`, tuplas de miembro, `applies_to` |
| `tools/ingestion/ingest_2b.py validate` | guardas permanentes (abajo) |

## Desviaciones encontradas y corregidas

### 1. `runtime.grant` con valores inventados — 213 reglas

El schema solo admite `profile` / `band` / `selectable` / `none`; `ingest_2b.py` no lo
validaba, así que se habían colado `hero` (86), `henchman-group` (117) e `item` (10).

- `hero`, `henchman-group` → **`profile`** (la KB expresa el alcance por perfil con
  `applies_to.profile_ids`, que estas reglas ya tenían).
- `item` → **`band`**.

### 2. `applies_to.profiles` en vez de `profile_ids` — corregido

La KB usa `profile_ids` (o `band: true`). Todas las reglas usan ahora esas dos formas.

### 3. Propietario del id de regla inexistente — 20 reglas

La gramática KB es `<owner>--<name>` con `owner` = `band` o un id de perfil del paquete.

| Antes | Después | Criterio |
|---|---|---|
| `item--cursed-pistol`, `item--katana`, `item--hellblade`, … (10) | `band--cursed-pistol`, … | reglas de documentación de equipo |
| `skills--special-skills`, `skills--slayer-special-skills`, … (3) | `band--special-skills`, … | listas de habilidades |
| `specialists--roster` | `band--roster` | regla de roster |
| `skeletons--fear`, … (6, blood-dragons) | `skeleton-warriors--fear`, … | el perfil se llama `skeleton-warriors` |
| `captain--leader` (pirates-of-the-cathayan-sea) | `disgraced-warlord--leader` | id real del perfil |
| `truant--spry`, `dead-eye--…`, `fugitive--…` (channel-rats) | `truants--…`, `dead-eyes--…`, `fugitives--…` | ids plurales reales |
| `strigany-special-skills-list` | `band--strigany-special-skills-list` | sin `--` → no cumplía la gramática |

Las referencias en `rule_ids` (banda y perfiles) se actualizaron en la misma operación.

### 4. `band.yaml rule_ids` con reglas de perfil y sin reglas de banda — 17 paquetes

Patrón KB: **todas** las reglas `band--` del paquete se listan en `band.yaml rule_ids`;
las reglas de perfil nunca. (Con `variants`, cada variante lista las suyas — patrón
Tileans.) Se regeneraron las 17 listas y se retiraron 4 `band--` de `rule_ids` de perfil.

### 5. `type` de perfil con valores inventados — 17 perfiles

La KB solo usa `hero` / `henchman` / `animal`. Se habían introducido `henchman-group`
(15), `warmachine` (1, Gyrocopter) y `equipment` (1, River Boat).

- Todos → **`henchman`**, siguiendo el precedente KB `carnival-of-chaos/plague-cart`
  (máquina/vehículo contratado, `experience: 0`, características nulas explícitas).

### 6. `characteristics` incompletas — 7 perfiles

La KB siempre lista las nueve claves (M WS BS S T W I A Ld), admitiendo `null` para lo
que la fuente no imprime y cadenas como `2D6` (precedente KB `orc-mob/cave-squigs`
y `orc-mob/troll`). Ahora **390/390** perfiles tiene las nueve claves.

### 7. Claves de roster y de miembro inventadas — 21

| Clave | Dónde | Acción |
|---|---|---|
| `currency` (7), `currency_note` (1) | `roster` | eliminadas; texto conservado abajo |
| `notes` (13) | miembros de `roster` | eliminadas; texto conservado abajo |

### 8. Cualidades de objeto con claves sueltas — 42 entradas

Filas como `{"item_id": "sword", "cost": 10, "Rare 12": null}` pasaron a
`notes: "Rare 12"` (concatenadas con las existentes), que es el patrón KB/2A.

### 9. `references` (campo inventado) — 4 perfiles

La KB no tiene herencia entre paquetes: cada perfil es autocontenido. Sustituido en los
dos casos (abajo) por los valores reales de la fuente.

## Paquetes completados

### `dark-elf-corsairs-mou` — el perfil `specialist` era un marcador

El paquete tenía un perfil `specialist` con características nulas y
`references: {variants: [assassin, sorceress, beastmaster, witch-elf]}`. La fuente
imprime los cuatro especialistas (PDF pp. 4–6; su texto ya estaba transcrito verbatim en
la regla `band--roster`):

| Perfil | M | WS | BS | S | T | W | I | A | Ld | Fuente |
|---|---|---|---|---|---|---|---|---|---|---|
| `assassin` | 5 | 5 | 5 | 4 | 4 | 1 | 7 | 1 | 8 | p. 5, igual que la Espada a Sueldo de TC 12 |
| `sorceress` | 5 | 4 | 4 | 3 | 3 | 1 | 5 | 1 | 8 | p. 5, maga de Magia Oscura (2 hechizos) |
| `beastmaster` | 5 | 4 | 3 | 3 | 4 | 1 | 6 | 1 | 8 | p. 5, con dos Sabuesos de Sangre Fría |
| `witch-elf` | 5 | 4 | 4 | 3 | 3 | 1 | 6 | 1 | 8 | p. 6, frenesí, dos hojas con veneno oscuro |

- Cuatro perfiles `hero`, `cost: 0`, `experience: 0` (la fuente: gratis al contratar,
  con tasa/fianza posteriores) y su equipo descrito en `equipment_restrictions`.
- Roster: un hueco 0-1 para cada uno; la restricción "un solo Especialista por batalla"
  y "no cuenta para el tamaño máximo de la banda" queda en la regla `band--roster`.
- Las tres reglas del especialista pasan a ser compartidas por los cuatro perfiles con
  el patrón KB (precedente `battle-monks-of-cathay/band--distaste-for-poison`):
  id `band--specialist-hiring-fee` / `-provisory-ally` / `-in-demand`,
  `runtime.grant: profile`, `applies_to.profile_ids: [los cuatro]`, y se listan en
  `band.yaml rule_ids` (la KB nunca lista reglas `band--` en perfiles).
- Los dos Sabuesos de Sangre Fría siguen documentados en `band--roster` (texto de la
  fuente); separarlos a un perfil propio queda pendiente de decidir.

### `orc-pirates-sar` + `savage-orcs-sar` — dos listas hermanas de Da Mob (decisión aplicada)

La fuente ("Variants for Orc Pirates and Savage Orcs Warbands in the Sartosa Setting")
declara que **ambas listas usan las mismas reglas que la banda Da Mob** de la KB
(`sources/knowledge/bands/mordheim/orc-mob`). El paquete original estaba a medias: tres
perfiles con `cost: null` y características nulas, más `references: {inherits: da-mob-…}`
y un roster con `starting_gold: null` / `maximum_models: null`.

**Decisión de modelado (cerrada):** el documento imprime **dos listas de banda**, cada una
con su propia composición, listas de equipo y reglas:

| Lista | Miembros propios | Listas de equipo |
|---|---|---|
| Orc Pirates | Goblin Enjuneer (reemplaza al Chamán), Goblin Swabbies (reemplazan a los Guerreros Goblin), 0-5 Sea Squigs, 0-1 Sea Troll | Orc (pirata) + Goblin Swabbie |
| Savage Orcs | Forest Goblins (perfil de Guerrero Goblin de Da Mob) | Orc (salvaje) + Forest Goblin |

El motor **no puede variar el roster por variante**: `WarbandVariant`
(`packages/typescript/domain/campaign/band-variants.ts`) sólo admite `id`, `names`,
`rule_ids`, `starting_gold` y `profile_bonuses`, y `createDraft` rechaza contratar un
perfil ausente de `roster.members` ("Profile X is not available to this warband"). Por
tanto cada lista es **su propia banda** con `canonical_family: orc-mob`, nunca una entrada
`variants` dentro del paquete KB `orc-mob`. Es el patrón KB de las familias hermanas:
`chaos-streets-greenskins` junto a `orc-mob` es el caso idéntico (misma banda base, otra
ambientación, roster y listas propias).

`canonical_family` no es decorativo: `packages/python/roster-construction/…/restrictions.py`
resuelve las habilidades especiales con `{band_id, canonical_family}`, así que el enlace
con `orc-mob` es lo que mantiene las habilidades orcas (Waaagh, 'Ere We Go…, `test_catalogue_uses_a_trollheim_band_canonical_family_for_special_skills`).

- El contenido ya transcrito se **movió** entre los dos paquetes; `band--da-mob-rules`
existe en ambos, con el texto de su propia lista.
- `orc-pirates-sar`: perfiles completados con los valores de `orc-mob` que la fuente cita
  (`orc-boss` 80 gc, `orc-big-uns` 40 gc, `orc-boyz` 25 gc, `sea-squigs` 15 gc con M
  `2D6-1` vía `sea-squigs--stats-like-da-mob`, `sea-troll` 200 gc vía
  `sea-troll--loses-vomit`).
- `savage-orcs-sar`: perfiles y composición heredados de la lista Da Mob (la fuente no
  imprime statlines propias), documentado en `band--roster`; las reglas propias son
  `band--savage-orc-rules`, `band--wild-animosity`, `band--savage-orc-special-skills` y
  `band--throwing-axe`.
- Una fila de manifiesto (`Orc Pirates & Savage Orcs`, SAR) declara los dos paquetes en
  `packages:`; `ingest_2b.py validate` los comprueba uno a uno y falla si aparece un
  paquete del árbol que ninguna fila declare.

## Texto conservado fuera del paquete (la KB no tiene campo para ello)

### Divisas de roster (8 bandas)

| Banda | Texto |
|---|---|
| `fallen-the-rel` | `currency: dinars` |
| `ghutani-rel` | `currency: dinars` |
| `muzil-rel` | `currency: dinars` |
| `skaven-of-clan-skryre-rel` | `currency: dinars` |
| `slavers-rel` | `currency: dinars` |
| `turjuk-rel` | `currency: dinars` |
| `metal-mongers-mim` | `currency: warp tokens` |
| `skaven-of-clan-pestilens-mou` | `currency_note: "Skaven deal in warp tokens (wt); treat these the same as gold crowns."` |

### Restricciones de composición del roster (13 miembros)

Hoy solo estaban como nota de miembro. El hogar KB para una restricción de composición
es una **regla de banda** (precedente KB `outlaws-of-stirwood-forest/band--cleric-hero-slot`:
`applies_to: {band: true}`, `runtime: {scope: NO, implemented: NO, grant: band}`, con
`reason` explícito). **Pendiente de aplicar** (ver "Trabajo en curso" abajo).

| Banda | Miembro | Restricción |
|---|---|---|
| `blood-dragons-mou` | `grave-guards` (0-5) | Never more Grave Guards than Skeletons |
| `disciples-of-maldred-mou` | `squires` (0-2) | Never more Squires than Knights |
| `disciples-of-maldred-mou` | `men-at-arms` (0-8) | 0-4 per Questing Knight |
| `orc-pirates-sar` | `goblin-enjuneer` (0-1) | Replaces Orc Shaman |
| `orc-pirates-sar` | `goblin-swabbies` | Replace Goblin Warriors in the henchmen list |
| `pirates-of-the-cathayan-sea-sar` | `dragon-monk` (0-1) | Replaces one Shanghai'er |
| `pirates-of-the-cathayan-sea-sar` | `floordogs` (0-5) | Never more Floordogs than Deck Hands |
| `slayer-pirates-sar` | `thaggi` (0-5) | May not have more Thaggi than other Henchmen |
| `woodsmen-de-artois-mou` | `hunting-hound` (0-5) | No more Hunting Hounds than Trappers |

(Las notas "Same as Da Mob" de `boss`, `big-uns` y `orc-boyz` quedaron resueltas al
completar los perfiles, y no son reglas.)

## Guardas permanentes añadidas a `ingest_2b.py validate`

A partir de ahora el validador falla si un paquete 2B presenta cualquiera de estas
desviaciones (todas introducidas por esta auditoría):

- `band.yaml` con claves fuera del patrón KB; `rule_ids` obligatorio; solo ids `band--`.
- Toda regla `band--` del paquete debe estar listada (banda + variantes).
- Gramática `<owner>--<name>` y owner = `band` o id de perfil.
- `runtime.grant` ∈ {profile, band, selectable, none}; `runtime.scope` ∈ {YES, NO, LATER};
  `implemented` ∈ {YES, NO}; `effects` dentro de `runtime`; `reason` en todo efecto
  NO/LATER; `binding` en todo efecto YES; `kind` en reglas selectable.
- `applies_to` solo `profile_ids` / `band`.
- Perfiles: `type` ∈ {hero, henchman, animal}; sin campo `references`;
  `characteristics` con las nueve claves.
- `roster` con claves KB; miembros solo `profile_id` / `minimum` / `maximum` / `group_size`.
- `equipment-access`: entradas de lista solo `item_id` / `cost` / `notes`.

## Auditoría final (autoritativa)

El repo tiene el auditor del contrato KB, que es la herramienta de referencia:

```
python tools/knowledge/audit_kb_conformance.py --tree 2B
```

Resultado: **1 desviación, 1 clase** — `call-of-the-night-haint-mim/spirit-hosts--spectral-touch`
usa el binding `trait.spectral-touch`, que no existe en la KB.

**Veredicto: legítima, no es un duplicado.** Comprobado contra los bindings de la KB:
Spectral Touch = «con un 6 al impactar, +1 herida»; el candidato más cercano,
`trait.perfect-killer` (Clan Eshin), es «-1 adicional a la salvación por armadura», y
`skill.crushing-blow` es «los ataques no pueden pararse». Son mecánicas distintas, así
que el id nuevo debe registrarse en la KB al promover la banda. El auditor lo reporta
como informativo, no como defecto.

Auditoría de forma complementaria (`build/cache/2b-sources/final_audit_2b.py`, que
compara conjuntos de claves y dominios de valor de los cuatro documentos contra la KB):
**0 problemas** sobre 61 bandas, 397 perfiles, 902 reglas, 137 listas y 1626 entradas de
equipo. Las reglas que llevan `rule_ref` heredan la prosa de efecto de la regla compartida
de la KB, así que sólo necesitan su propio nombre en español.

### Corrección de una guarda propia

El contrato del inventario de equipo permite `item_id`, `cost`, `notes` **y
`price_override`** (la KB lo usa 18 veces, con el comentario de la regla que lo justifica).
La guarda inicial de esta auditoría lo prohibía por error; ya acepta los cuatro campos.

## Verificación

| Comprobación | Resultado |
|---|---|
| `tools/knowledge/audit_kb_conformance.py --tree 2B` | 1 informe informativo (`trait.spectral-touch`) |
| `ingest_2b.py validate` | 60 filas / 61 paquetes, **0 problemas** (incluye huérfanos) |
| `final_audit_2b.py` (formas y dominios) | **0 problemas** sobre 61 paquetes |
| `tests/knowledge/test_2b_staging.py` | **12 pasan** (contrato, referencias, paquetes declarados) |
| `tests/knowledge/test_binding_registry.py` | **3 pasan**; con el registro incompleto, falla |
| `format_yaml.py --check sources/2B` | 261/264 limpios (2 avisos de longitud previos, en otros paquetes) |
| `pytest tests/knowledge` | **toda la suite en verde** |

## Reparto del trabajo

Un primer pase ejecutó `migrate_2b_kb_schema.py` (runtime completo en las 60 bandas,
bindings alineados al canon KB) y `migrate_2b_records.py` (notas de lista, divisas,
tipos de `fixed_equipment`, `references`); la auditoría de conformidad aportó después las
guardas de forma, la gramática de ids, los tipos de perfil, las características completas
y el completado de los dos paquetes a medias.

## Pendiente (decisiones, no defectos)

1. **`orc-pirates-sar` + `savage-orcs-sar` (resuelta):** cada lista es banda propia con
   `canonical_family: orc-mob`; **no** se convierten en entradas `variants` de `orc-mob`
   (el motor no puede variar roster ni listas de equipo por variante; detalle en la
   sección anterior).
2. **Sabuesos de Sangre Fría** (`dark-elf-corsairs-mou`): siguen descritos en el texto de
   `band--roster`; separarlos a perfil propio es una decisión de modelado.
3. **`trait.spectral-touch`:** registrar el binding nuevo en la KB al promover
   `call-of-the-night-haint-mim`.
4. **Estados del manifiesto:** las 60 filas siguen en `english-reviewed`. Esta pasada es
   de forma; no cambia la revisión de contenido ni traduce nada nuevo.
