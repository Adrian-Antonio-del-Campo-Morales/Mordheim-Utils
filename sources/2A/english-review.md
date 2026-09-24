# English-review 2A — verificación cruzada numérica y marcado de filas

Fecha: 2026-09-15. Revisión en inglés sobre las **19 bandas modeladas** del staging 2A,
con la misma metodología usada en 2B: re-derivación automatizada de cada número del
paquete desde el borrador fuente cacheado, adjudicación manual de los casos no-OK y
registro de veredictos aquí.

## Herramienta

Nueva herramienta de solo lectura `tools/ingestion/review_2a.py` (adaptada de
`review_2b.py`): re-deriva límites de roster, costes/XP/perfiles, precios de equipo y
cifras citadas en textos de reglas desde `build/cache/2a-sources/text/<id>.txt`
(borradores de las páginas dedicadas de mordheimer.net). Adaptaciones 2A: los marcadores
de contratación aceptan `warp tokens to hire` además de `gold crowns to hire`, y no hay
fuentes escaneadas (todo el staging procede de páginas HTML con capa de texto nativa).

## Primera pasada automatizada

**717 comprobaciones — 696 OK / 16 NOT_FOUND / 5 MISMATCH.**

## Adjudicación individual de los 21 casos no-OK

### MISMATCH (5) — todos artefactos del matching automático; cero errores de transcripción

1. **`snotlings-web` shoota-teams/mobs/runts/wheelo :xp (4 casos).** El draft imprime la
   experiencia en una sección resumida ("All Henchmen start with no experience", línea 30)
   sin el patrón `<Nombre>STARTSWITH<N>`; el checker agrupó dígitos ajenos. Los cuatro
   secuaces (`experience: 0`) son correctos contra la frase literal de la fuente.
2. **`sorcerous-society-lotd4` roster.minimum_models.** El draft imprime el mínimo en
   palabras ("a minimum of **three** models", línea 29), no como dígito; el checker encontró
   dígitos de contexto ajeno. El paquete (`minimum_models: 3`) es correcto.

### NOT_FOUND (16) — verificados uno a uno contra el draft; todos correctos

- **`halflings-mic` 8× profile:xp.** La página no tiene sección "Starting Experience"
  separada: la XP va incrustada en la lista de contratación como "20xp start." /
  "8xp start." / "0xp start." (líneas 13–16 del draft). Elder 20, Cook 8, Thief 8, Youths 0
  — el paquete coincide; henchmen sin cifra = 0, conforme al patrón de todas las bandas 2A.
- **7× roster.minimum/maximum_models** (dreamwalkers, druchii, dwarf-slayer-cult,
  mazzalupo, ogre-hunting-party, order-of-the-mare, protectorate, sorcerous-society):
  mínimo/máximo impresos en palabras ("a minimum of three models", "Maximum number of
  warriors is 12") o con variantes sintácticas no cubiertas por los needles. Verificados
  textualmente: todos coinciden con los paquetes (p. ej. dwarf-slayer-cult "Maximum number
  of warriors is 12" ↔ `maximum_models: 12`; protectorate "may not exceed 15" ↔ 15;
  sorcerous-society "three models… never exceed 15" ↔ 3/15).
- **`snotlings-web` wheelo:stats.** La statline del Wheelo empieza con `*` (movimiento
  aleatorio), que el normalizador alfanumérico no puede emparejar con el run `M0…` del
  paquete. La statline se verificó dígito a dígito en la transcripción (ver
  transcripción del paquete y nota del campo M); correcto.

## Pasada de conformidad con los patrones de la KB (2026-09-15)

Auditoría de forma exhaustiva de los 19 paquetes 2A contra el patrón canónico de
`sources/knowledge/bands/mordheim/*` (y el staging 2B aprobado). Cambios estructurales
aplicados — sin alterar ningún dato de juego:

- **`skill_tables` eliminado de los 15 band.yaml que lo tenían**: era un campo inventado
  no presente en la KB ni en 2B; su contenido (tabla de habilidades por perfil) ya vive
  en el campo KB `skill_access` de cada perfil. Se verificó previamente, fila a fila,
  que ambas representaciones eran idénticas en las 19 bandas.
- **`rule_ids` añadido a band.yaml** en las 15 bandas que lo carecían (campo KB
  requerido): listado de todas las reglas `band--` del paquete, misma convención que la
  KB (reglas de perfil listadas solo en el `rule_ids` del perfil).
- **62 reglas renombradas** a la gramática KB `<owner>--<name>` (owner = `band` o un id
  de perfil): se eliminaron los prefijos inventados `special--`, `special-skill--`,
  `special-equipment--`, `command--`, `skill--`, `shared--` y `rites--`. Reglas
  multi-perfil usan el perfil protagonista como owner (precedente KB:
  `band--hard-head` en sons-of-hashut aplica a 5 perfiles con un solo id). 21
  referencias en `rule_ids` de perfiles actualizadas en consecuencia; 0 referencias
  colgantes (verificado con `audit_2a.py`).
- **`runtime.grant` normalizado al runtime-schema**: `special-skill` → `selectable`
  (con `kind: warband_skill`, 9 reglas), `item` → `band` (5 reglas de documentación de
  equipo que pasan a ser reglas de banda referenciando el item), y `kind: warband_skill`
  añadido a 30 reglas `selectable` sin kind. `applies_to.profiles` → `profile_ids` y
  `applies_to.special_skills` → `band: true`.
- **equipment-access.yaml**: las 5 notas a nivel raíz (`list_note`/`notes`) trasladadas
  al campo `notes` a nivel de lista (patrón KB/2B); las 11 filas con claves sueltas
  nulas (p. ej. `Rare 9: null`) aplanadas al campo `notes` del item.
- **profiles.yaml**: `source_path` añadido a los 12 perfiles que lo carecían
  (mazzalupo ×7, wood-elves ×5); las notas de prosa de 5 perfiles reubicadas en campos
  KB (2 → `equipment_restrictions`, 1 → `group_size`) o conservadas aquí:
  - [dreamwalkers-cult-of-morr-fbg] `morr-worshwishpers`: nombre transcrito verbatim de
    la fuente ("Worshwishpers").
  - [order-of-the-mare-web] `companion-filly`: la cobertura (oculta tipo barda espectral)
    no es un objeto comprable; es parte del perfil y está documentada en las
    restricciones y la regla Horse.
  - [snotlings-web] `wheelo`: la M es un asterisco (*) en la fuente — movimiento
    enteramente aleatorio (1D6" andando, 2D6" corriendo/cargando); modelado como 0 con
    la regla portando la mecánica real.
- **Guardas permanentes en `ingest_2a.py validate`**: claves fuera del patrón KB en
  band.yaml, ausencia de `rule_ids`, gramática de ids de regla (`<owner>--<name>` con
  owner válido), valores de `grant` del runtime-schema, y `kind` obligatorio en reglas
  `selectable`.

## Veredicto global

**Ningún error de transcripción encontrado.** Las 19 bandas 2A superan la revisión en
inglés: cada número del paquete se re-derivó desde su fuente y los 21 casos no-OK se
resolvieron individualmente como artefactos del matching automático (números en palabras,
XP incrustada en las listas de contratación, marcador `*` del Wheelo).

Acción aplicada: las 19 filas del manifiesto avanzaron `modeled` → `english-reviewed`.

## Verificación

- `ingest_2a.py validate`: 19 filas, 0 problemas
- `pytest tests/python/knowledge/test_2a_staging.py`: 7/7
- Reporte automatizado: `build/cache/2a-sources/review-report.md`

Siguiente fase del pipeline: **traducción al español** (completar/bajar la calidad de
`name_i18n`/`effect_i18n` donde falte), después `validated` y `promotable`.
