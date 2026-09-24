# Web presentation contract

Guía práctica en español: [detectar, corregir y verificar salidas inseguras](guia-salidas-localizadas-web.md), con ejemplos y pendientes por sección.

The web UI and readable exports use Spanish or English. Internal identifiers
remain in v5 persistence and action payloads, but are not display fallbacks.
Personal names and user notes retain their original content.

## Required policy for new GUI fields

Every new or modified GUI field must follow the
[detection methodology and mandatory field checklist](guia-salidas-localizadas-web.md).
This includes visible content, control labels and values, accessibility attributes,
tooltips, all UI states, history and readable exports. Classify the source, use
the appropriate typed resolver/formatter and active locale, preserve presentation
types through composition, and extract strings only at the output boundary.
`presentationOutput` does not translate or sanitize arbitrary strings.

Run `npm run check:presentation`; unknown outputs and incomplete provenance paths
block acceptance. A new output mechanism requires detector coverage and a deliberate
leak regression test before use. Never bypass the contract using casts, suppressions,
raw identifiers, captured KB labels, cross-language fallbacks or generic personal-text
exceptions. Existing findings do not authorize new unprotected fields.

## KB generation and resolution

`tools/knowledge/presentation_contract.py` builds the presentation index from
canonical records, including nested text fields. Entity names are required;
other prose fields may be absent, but must have both locales when present.
Missing values are recorded as `TODO-TRANSLATE`. These markers are editorial
work items, never usable translations or user-visible fallback text.

`display-text.json` contains `presentation_entries` and `translation_todos`.
The main artefact records hashes for its companion artefacts. The web reader
checks those hashes and validates the index before using it.

`resolveKbText(ref, field, locale)` resolves exact identity and supplied context.
It returns provenance on success and a structured error on failure. Unknown,
ambiguous and untranslated references show localized unavailable messages at
presentation boundaries. Technical diagnostics are retained separately and
deduplicated. No other language is substituted.

Successful resolver strings now carry the opaque `ResolvedKbText` type. The
reader's `recordText`, web `knowledgeName` and tooltip names preserve this type.
There is no public constructor accepting an arbitrary string. A compiler test
checks that raw strings and forwarded ordinary labels cannot satisfy this type.
Ordinary strings cannot enter the typed PDF writer or migrated React components.
The remaining acceptance work concerns provenance coverage, history detail and end-to-end validation; see the practical guide.

UI catalogue output carries `UiText`. Parameterized messages declare arguments
per key, with entity names requiring `ResolvedKbText` and numeric parameters
rejecting non-finite values. `presentationOutput` accepts only these validated
text types. `KnowledgeHint` and `NumberStepper` route text and accessible labels through
that adapter, including descriptions after unit conversion. The syntax gate
rejects unvalidated output in every scanned web source, including new files
without an adapter import. This is not yet a proof that every possible output
mechanism and runtime provenance path is covered.

Regenerate with `python tools/knowledge/generate_knowledge_web.py`; verify with
`--check`. The separate `--check-translations` option rejects editorial pending
items. Ordinary generation permits them under the current implementation
instruction to record missing translations rather than author them.

## Cómo localizar traducciones pendientes con las herramientas

`TODO-TRANSLATE` significa que el generador no ha obtenido un valor válido para
un campo e idioma exigidos por el contrato. Actualmente se incorpora **durante
la generación**, no se escribe automáticamente en las fuentes de
`sources/knowledge/`. Por eso buscar el marcador en la KB original puede no
devolver resultados aunque existan pendientes.

Los marcadores y la lista `translation_todos` están en `display-text.json`:

- `build/generated/knowledge-web/display-text.json`: salida del generador.
- `apps/warband-manager-web/public/knowledge/display-text.json`: copia utilizada
  por la web; puede quedar desactualizada respecto a la generación.

La interfaz no muestra el marcador como traducción: presenta el aviso localizado
«Información no disponible» / «Information unavailable». No sustituye el texto
por un ID ni por el otro idioma.

### Uso de las tools del repositorio

Ejecutar los siguientes comandos desde la raíz del repositorio, con Python y
las dependencias del proyecto disponibles:

| Herramienta / comando | Para qué sirve | Límites y efectos |
| --- | --- | --- |
| `python tools/knowledge/generate_knowledge_web.py --check --check-translations` | Construye el índice en memoria desde las fuentes actuales y comunica las ubicaciones de traducción pendientes. | No escribe los artefactos con `--check`. Si faltan traducciones, termina con error: es el resultado esperado del control. Si no faltan, comprueba también que los artefactos estén actualizados. |
| `python tools/band_translation_status.py` | Muestra un resumen de traducción al español por banda. | Solo lectura. Cubre nombres de banda/perfiles y nombres/efectos de reglas especiales; no toda la KB ni ambos idiomas. |
| `python tools/band_translation_status.py --json` | Obtiene esos mismos recuentos en JSON. | No devuelve un inventario completo de campos pendientes. |
| `python tools/band_translation_status.py --band mordheim/mercenaries` | Desglosa los recuentos de una banda por categoría. | Sustituir `mordheim/mercenaries` por la ruta `colección/banda` deseada. |
| `rg -n -F -- 'ID_DEL_PROPIETARIO' sources/knowledge` | Localiza referencias a una identidad en los archivos fuente, con números de línea. | Solo lectura; revisar los resultados para distinguir definición y referencias. |

El informe de bandas considera traducido cualquier valor español no vacío;
no valida la calidad de la traducción ni rechaza por sí mismo el literal
`TODO-TRANSLATE`. Para los pendientes del contrato web, usar el control del
generador y `translation_todos`, no únicamente el porcentaje de bandas.

`tools/translate_band.py` es una herramienta distinta: **aplica** traducciones
revisadas y modifica YAML. No se usa para esta consulta de pendientes.
No existe actualmente una tool dedicada que entregue automáticamente todos los
pendientes del índice web con su archivo y línea canónicos. Para obtener ese
informe se combinan la consulta JSON y la búsqueda de fuentes descritas abajo.

### Consulta del archivo generado

Desde la raíz del repositorio, en PowerShell:

```powershell
$displayPath = 'build/generated/knowledge-web/display-text.json'
$display = Get-Content -LiteralPath $displayPath -Raw | ConvertFrom-Json
$display.translation_todos | Select-Object status, location
```

Una ubicación como `profiles/161/equipment_access/4:notes.es` se interpreta así:

- `profiles/161/equipment_access/4`: ruta dentro de los datos usados por el
  generador, con índices de listas que empiezan en cero.
- `notes`: campo afectado.
- `es`: idioma pendiente.

No es una ruta de archivo YAML ni un número de línea de la fuente. Los índices
pueden cambiar al regenerar; no deben usarse como identificadores permanentes.

Para consultar la identidad, el contexto y el texto disponible de ese ejemplo:

```powershell
$sourcePath = 'profiles/161/equipment_access/4'
$display.presentation_entries |
  Where-Object { $_.source -eq $sourcePath } |
  ConvertTo-Json -Depth 15
```

Cada entrada contiene `ref`, `fields` y `source`. Para rastrearla a la KB:

1. Identificar la entidad y su contexto en `ref`. Si es un subregistro cuya
   identidad es una ruta, consultar el registro propietario en los artefactos
   de la misma generación (`knowledge-web.json` o `rules-prose.json`).
2. Buscar el ID estable del propietario en las fuentes, por ejemplo con
   `rg -n -F -- 'ID_DEL_PROPIETARIO' sources/knowledge`.
3. Confirmar banda, perfil, tabla y subregistro; un mismo ID puede aparecer en
   varias referencias. Revisar el campo canónico y su estructura de traducciones
   (`name_i18n`, `notes_i18n`, etc., según la fuente).
4. Registrar archivo y línea de la fuente, identidad/contexto, campo, idioma y
   texto disponible. Si el campo se deriva o combina durante la generación,
   seguir su transformación en `tools/knowledge/generate_knowledge_web.py` antes
   de atribuir el pendiente a un archivo concreto.

Las herramientas permiten hacer este rastreo y preparar un informe sin editar
la KB. La lista actual no incluye directamente archivo y línea originales:
esa correspondencia requiere inspección. El número de incidencias tampoco
equivale al número de entidades o frases únicas; puede haber varios campos,
idiomas, contextos o alias asociados a una misma fuente. Un pendiente puede
requerir revisar el contrato o el mapeo del generador, no solo traducir una frase.

Cuando se autorice corregir traducciones, se editarán las fuentes canónicas y
se regenerarán los artefactos. No se deben corregir manualmente los JSON
generados. `--check` comprueba la concordancia con la generación;
`--check-translations` comprueba los pendientes y falla si quedan incidencias.
Esta documentación no implica que se hayan modificado traducciones ni que
todos los pendientes estén ya vinculados a una línea de la fuente.

## Saved data and exports

Advances persist structured `applied_result` and `roll_history_events` beside
legacy v5 fields. The web prefers those structured values. Exact known legacy
messages and unique KB captures can be resolved through compatibility helpers;
unknown saved system text is preserved in the document but shown as unavailable.
Numeric presentation rejects arbitrary strings and non-finite values.

The PDF exporter resolves KB names afresh and keeps user names. Multiline text
is split before font encoding so line breaks cannot become replacement glyphs.
Its cell and multiline writer signatures accept only opaque presentation values;
dates, numbers, characteristics and personal names use field-specific adapters.
The bilingual shared UI catalogue also supplies its labels. Both language outputs
have been rendered and visually inspected.

## Obligatory output boundary coverage

The global check in `tools/presentation-audit.mjs` enforces validated
output without a staged closed-module list, even if a component removes its adapter import. Coverage now includes
readable downloads, post-battle and battle histories, timeline, review,
advances, follow-up acknowledgements, scenario follow-ups, inventory,
equipment, upkeep, manual corrections, recruitment controls, experience,
statistics, dice controls, injury recovery, serious injury results and dice histories, wyrdstone sale,
rare searches, the isolated draft route and warrior cards.
Accessible labels and disabled-action explanations use the same boundary.
Personal names enter through field-specific adapters; stored KB names do not.

Campaign errors use the bilingual message catalogue and typed parameters.
Exact legacy errors are interpreted separately; technical exceptions have no
raw presentation fallback. An open error is re-resolved when locale changes.
Readable histories resolve recruitment, purchases, sales, upgrades, dismissals,
upkeep and corrections from structured facts. Unsupported legacy details stay
in persistence and yield a localized unavailable notice.

## Verification and remaining work

`npm run lint` in the web application runs the syntax inventory and regression
checks for raw identifiers in JSX, accessibility attributes, aliases, DOM and
PDF text calls. The inventory is written to
`build/generated/presentation-audit.json`. Tests deliberately inject leaks,
including PDF cell arguments and local functions impersonating resolvers.
It also follows destructured identifier aliases, object-literal labels and local
function parameters. The compiler contract test runs in the same lint gate.

This check is **not yet a proof of complete presentation provenance**. A clean
report means the implemented checks found no violation; it does not mean every
inventoried expression has a validated origin. In particular, the following
acceptance work remains:

- Complete the remaining runtime and data-provenance checks for input values,
  component forwarding and newly introduced output mechanisms. The syntax gate
  now rejects unvalidated JSX, attributes and document/DOM writes in every web
  source file, including newly added modules (no staged module allowlist).
- Finish structured histories beyond advances and the runtime policy for
  unexpected resolution failures in development.
- Recheck complete interactive flows and exports after those migrations.

The original exhaustive localization implementation must not be marked complete
until those requirements pass. Editorial `TODO-TRANSLATE` items are tracked
separately from these system gaps.

Description selection skips only undeclared optional fields (`missing-field`).
A declared field without its requested translation returns `missing-translation`
and cannot be replaced by another note or description. The injury history uses
this same typed boundary, including saved dice, secondary rolls and departed
warriors' personal names. Exact legacy v5 sale/exploration messages also support
the older `action` discriminator; partial matches remain unavailable.

## Remaining implementation work, split by reviewable task

The implementation was delegated in isolated batches to Sol (low effort), with
integration and review by the coordinating agent. Helper usage limits interrupted
the next batch; completion is tracked here rather than inferred from helper status.

| Subtask | Implementation status | Review evidence |
| --- | --- | --- |
| Hiring/trading outputs and original-row restrictions | Migrated | Focused tests; typed boundary; manual prose fallback removed |
| Battle input and resolved reward outputs | Migrated | Focused rendered tests; reviewer corrected localized experience unit |
| DraftWorkspace and ExperienceTrack | Migrated | Focused tests; reviewer corrected accessible experience unit |
| CampaignSlice and historical roster/state outputs | Migrated | Global syntax gate; exact owner-scoped variant names |
| CSS generated text | Enforced | Raw CSS words and unvalidated attributes rejected by regression tests |
| Exploration outputs | Migrated | Typed dice labels, personal choices, localized limits and damaged-data tests; structured producer coverage remains below |
| ProductApp and rules catalogue | Migrated | Original-row resolution, typed composition, no manual injury-translation fallback; shell and catalogue tests |
| Remaining event producers and v5 compatibility | Pending | Complete structured injury/scenario/exploration facts; preserve unknown payloads |
| Universal syntax gate | Enforced | 1,372 inventoried sinks; 30 regression checks; new modules cannot evade enforcement by omitting adapter imports |
| End-to-end/export closure | Pending | Final bilingual flows, import, PDF and release checks |

The migrated status covers presentation-boundary enforcement, not a claim that
all canonical editorial translations are present. No new helper success or clean
partial audit alone closes the global task.

The bootstrap accessibility adapter mirrors only the same control's audited
`data-disabled-reason` into its tooltip and accessible description. There is no
fixed Spanish fallback; changes to the reason update both surfaces. This exact
DOM forwarding case is tested separately from arbitrary DOM writes.

Catalogue KB names and descriptions now retain resolver provenance. Missing
injury-result translations remain unavailable and tracked editorial work; a
hard-coded injury dictionary must not conceal them. Recruitment into a group
and scenario spell rewards now carry additional structured history facts while
retaining legacy descriptions for desktop compatibility.
