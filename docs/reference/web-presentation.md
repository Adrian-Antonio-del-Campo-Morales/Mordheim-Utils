# Web presentation and localization

The web UI and readable exports support Spanish and English. Internal IDs stay
in v5 persistence and action payloads, but are never display fallbacks. Personal
names and user notes preserve their original content.

## The essential rule

Every value visible to a person or exposed to assistive technology must follow
this path:

```text
identified source
  -> source-specific resolver or formatter
  -> presentation type
  -> typed composition, when needed
  -> presentationOutput(...) at the exact output boundary
```

`presentationOutput` only extracts the final `string`. It does not translate,
sanitize IDs or make arbitrary strings safe. A value that reaches it only
through a cast is not protected.

## What counts as UI output

Do not review only JSX text nodes. Inventory visible text; accessible labels;
tooltips; placeholders; visible control values; dialogs; errors; disabled-action
reasons; histories; persisted messages; PDF, CSV and other readable downloads;
DOM and canvas writes; generated HTML; CSS content; and component props that
can eventually be rendered. Cover success, error, loading, empty, damaged,
historical and pending states.

An `option`, radio, checkbox or hidden control may keep an ID in its `value`
when that value is selection identity only. Its visible label still needs
resolved presentation text.

## How to find unprotected text

### Run the mandatory gate

From the repository root:

```powershell
python tools/mordheim-utils.py check-presentation
```

The equivalent command from `apps/warband-manager-web` is:

```powershell
npm run check:presentation
```

The command runs detector regressions, the strict deep audit and the dynamic
visible-completeness audit, in that order. It writes
`outputs/web-presentation/gui-text-audit-deep.json` for machines and
`outputs/web-presentation/gui-text-audit-deep.md` for human review, and the
dynamic layer writes `outputs/web-presentation/gui-text-completeness.{json,md}`
next to them (never mixed with the static findings).

A finding does not always prove that the current UI is wrong. It proves that
the detector cannot establish that the output is protected. That uncertainty
blocks acceptance until the source and destination are classified. Never hide
it with a cast or suppression.

## Presentation security versus visible completeness

The static gate (steps 1–4) is about **security of presentation**: it proves,
from the source, that every value that reaches a GUI sink travels through the
resolvers and presentation types. Its 700+ findings are "the detector cannot
demonstrate protection", not confirmed leaks.

The dynamic layer (step 5, `tools/web/presentation-completeness-audit.mjs` plus
`tests/web/tools/presentation-completeness-sweep.test.tsx`) is about
**visible completeness**: it executes the real consumers (the `RulesCatalogue`,
the rendered shell pages, loaded v5 campaigns, the PDF text model) against the
real generated artefacts in ES and EN, captures what a person would actually
see (textContent, tooltips, aria-labels, disabled reasons, visible control
values, export text — never option `value` identity, React keys or structural
attributes), and classifies each captured text with
`tools/web/presentation-completeness-detector.mjs`.

The policy of the dynamic layer: for published data and supported formats,
every visible text must resolve to real, localized content. A generic fallback
visible to a person is a defect — also for unknown references, old data,
missing translations and rows without a presentation entry. Those cases must
be fixed with a specific error, a migration, a document rejection or an
explicit structured absence message; the fallback itself remains a failure.
No allowlists, exclusions, file suppressions or snapshot auto-accepts are
accepted in this layer.

The classification is fragment-aware, not whole-value only: a composed text
(`Autor: …`, `• 5+ …`, `Notas: …`, `Piedra bruja: …`, `lore · difficulty …`,
`11-15 — …`) is split at the catalogue's own delimiters (line breaks, `·` and
`•` chips, `: ` labels and ` — ` table rows) and every fragment is classified.
A notice glued to a label, a bullet, a die result or a chip is therefore the
same finding as a bare one, and it is reported as the fragment that carries it,
not as the surrounding page text.

### Finding classes of the dynamic layer and how to resolve them

| Class | Meaning | Required response |
|---|---|---|
| `generic-fallback` | "Información no disponible" / "Information unavailable" (or an equivalent generic notice) reached a visible surface, alone or embedded in a composed text (after `Autor:`, inside notes, after a die result or a loot bullet, inside a chip). | Give the row a real resolution (fix the generator or data) or a specific localized absence message; never the generic notice. |
| `unexpected-row-in-category` | A row appears in a category whose declared composition it does not match (e.g. a band-local copy inside the shared `special-rules` catalogue). | Fix the generator so the category publishes only its declared rows; band rules belong to "band-rules". |
| `missing-presentation-entry` | A published row cannot be resolved at all through the presentation index. | Regenerate so the row gets a presentation entry, or stop publishing the row. |
| `wrong-locale` | The other locale's published text is shown although this locale publishes a different translation. | Route the field through the resolver in the active locale; never fall back to the other language. |
| `technical-id` | A known id, a dotted/underscored identifier or the row's own id is shown as text. | Resolve the reference through `recordText`/`knowledgeName`; keep ids in `value`/identity only. |
| `raw-text` | A `TODO-TRANSLATE` or poison marker reached the surface. | Fix the source data; markers are editorial/test signals, never user-visible. |
| `unsupported-document-rendered` | A format the product does not support was rendered instead of being rejected by its specific error. | Reject before render (retired/newer version); never render unknown documents. |

Each finding in `gui-text-completeness.{json,md}` records surface, locale,
category, the internal id (diagnostic only), the found text, the expected
reference and the artefact origin when known. The command exits non-zero when
the dynamic layer finds at least one problem, even if every static gate is
green. Run `npm run audit:completeness` in `apps/warband-manager-web` and read
the report to inspect the layer directly.

The "Reglas compartidas" defect (band-local rows published in the shared stem as
generic fallbacks) is guarded by
`tests/web/tools/presentation-completeness-regression.test.tsx`, which stays red
whenever the generator, the catalogue or the data leak band-local rows into the
special-rules category again.

The per-family gate for the visible fallbacks closed after `4631eae` — scenario
authors, wyrdstone, notes, loot rewards, `difficulty: auto` and the
serious-injury result names — is
`tests/web/features/campaign/visible-fallback-families.test.ts`. It asserts both
directions: the generated artefact and the composed catalogue text of every
family carry no `TODO-TRANSLATE`, no generic fallback and no missing resolution,
and the pre-fix shapes still redden the shared classifier, so the gate can never
pass by being vacuous.

### Interpret the report

| Reason | Meaning | Required response |
|---|---|---|
| `unvalidated-output` | A value reaches JSX, an attribute, DOM, dialog, canvas or document directly. | Resolve or format it, then call `presentationOutput` at the boundary. |
| `raw-text-flow` | The tracer reached raw KB, persisted or system text. | Fix the responsible source path, not only the final JSX node. |
| `incomplete-text-flow` | Analysis ended without proving the complete origin. | Review the full path or extend the detector; do not assume safety. |
| `raw-system-value` | A domain or system value is being used as visible text. | Map it through a localized message or exhaustive enum adapter. |
| `unclassified-control-value` | A visible control value has no proven presentation origin. | Separate control identity from its visible label, or provide typed text. |
| `unlocalized-export` | A readable export bypasses localization or resolution. | Apply the React contract to the PDF/CSV writer. |
| `presentation-cast` or `presentation-type-forgery` | Code fabricates a safe type. | Remove the cast and use an authorized constructor. |
| `presentation-suppression` | Code suppresses presentation checking. | Remove the suppression and model the provenance. |
| `unvalidated-css-content` | CSS `content:` may expose words or an unsafe attribute. | Use an allowed decorative symbol or an audited attribute. |
| `unclassified-source-format` | A GUI source format is outside detector coverage. | Add detector support and leak tests before using it. |
| `compiler-error` | The audited program does not compile. | Fix compilation first; broken types cannot prove provenance. |

Other `unclassified-*` reasons identify dynamic props, HTML, styles, indirect
DOM operations or computed calls whose visible effect cannot be proven. Review
them explicitly. If the mechanism is legitimate, extend the detector and add a
regression that fails for a deliberate leak.

### Use supporting searches

The detector is the primary gate. These searches help find suspicious seams:

```powershell
rg -n 'name_i18n|effect_i18n|\.name\b|\.label\b|\.description\b|\.message\b' apps/warband-manager-web/src packages/typescript
rg -n 'replaceAll\("_"|toUpperCase\(|target_id|profile_id|item_id|rule_id' apps/warband-manager-web/src packages/typescript
rg -n 'aria-|title=|placeholder=|alt=|alert\(|confirm\(|prompt\(|drawText|multiCell|textContent|innerHTML' apps/warband-manager-web/src packages/typescript
```

Search results are candidates, not verdicts. For each result, ask whether the
value reaches a visible or accessible surface and whether its provenance allows
the selected adapter to display it.

## How to display each source correctly

| Source | Correct path | Forbidden shortcut |
|---|---|---|
| KB name or prose | `resolveKbText`, `recordText`, `knowledgeName` or the equivalent semantic resolver, with reference, field, context and locale. | `row.name`, parallel dictionaries, the ID, or another language as fallback. |
| Fixed application message | `translate({ key, args }, locale)`; entity arguments retain their resolved type. | Scattered literals or untyped interpolation. |
| Closed domain enum | Exhaustive adapter in `presentation-enums.ts` or an equivalent exhaustive message map. | Humanizing an ID with underscores or capitalization. |
| Number, date, dice, characteristic or resource | `textNumber`, `textDate`, `textDice`, `warriorCharacteristic`, `resourceAmount` or another field-specific formatter. | `String(value)`, locale-free concatenation, `NaN` or infinity. |
| Personal name or user note | The exact field adapter: `warriorPersonalName`, `warbandPersonalName`, `campaignPersonalName`, `battlePersonalNotes`, and similar. | A generic constructor that can launder any string. |
| Approved decorative symbol | `textSymbol`. | Treating interface words as symbols. |
| Historical system text | Resolve structured facts and current IDs; use compatibility handling only for recognized legacy formats. | Unknown persisted messages, IDs or technical exceptions. |
| Technical error | Translate a known code and retain diagnostics separately. | `String(error)`, `error.message` or stack traces in the UI. |

### KB name example

Wrong:

```tsx
<option value={item.id}>{item.id}</option>
<span>{item.name}</span>
```

Correct:

```tsx
const label = knowledgeName(knowledge, "item", item.id, locale);
<option value={item.id}>{presentationOutput(label)}</option>
```

The `value` keeps the ID because it is selection identity. The visible content
uses the semantically resolved name.

### Composed message example

Wrong:

```tsx
<p>{`${warrior.name}: ${experience} XP`}</p>
```

Correct:

```tsx
const message = textJoin([
  warriorPersonalName(warrior, locale),
  textNumber(experience, locale),
  translate({ key: "unit.experience" }, locale),
]);
<p>{presentationOutput(message)}</p>
```

`textJoin` accepts only presentation values and declared separators. It is not
a way to admit raw strings.

### Shared component example

A shared prop accepts `PresentationText` or a narrower type, never `string`:

```tsx
function Status({ label }: { label: PresentationText }) {
  return <p role="status">{presentationOutput(label)}</p>;
}
```

If a component receives an object or callback that later renders text, its type
and detector coverage must preserve provenance across that boundary.

## Mandatory checklist for new or modified fields

1. List every surface: visible text, accessible attribute, tooltip, placeholder,
   table, history and export.
2. Identify the real source: KB, application message, enum, formatted value,
   personal field, historical text or diagnostic.
3. Use the source-specific resolver with the active locale. Do not persist a
   translated sentence for later display.
4. Preserve the presentation type through helpers, arrays, objects, props and
   callbacks.
5. Call `presentationOutput` only at the final output boundary.
6. Test Spanish and English plus success, empty, error, unknown, persisted and
   damaged states when applicable.
7. Assert that the localized semantic name is present and the known technical
   ID is absent.
8. Cover accessible labels, tooltips and exports when the field reaches them.
9. Run `python tools/mordheim-utils.py check-presentation` and inspect the
   report, not only the exit code.
10. For a new output mechanism, add detector coverage and a regression proving
    that a deliberate leak fails.

A helper-only test does not prove that the interface is protected. Acceptance
requires a rendered test through the real route that consumes the value.

## KB generation and resolution

`tools/knowledge/presentation_contract.py` builds the presentation index from
canonical records, including nested fields. Entity names are required. Other
prose may be absent, but must provide both locales when declared.

Missing values become `TODO-TRANSLATE` entries in generated data. They are
editorial work items, never user-visible fallbacks. `display-text.json` contains
`presentation_entries` and `translation_todos`; the main artefact stores hashes
for its companion files and the reader validates them before use.

`resolveKbText(ref, field, locale)` resolves exact identity and context. Success
returns opaque `ResolvedKbText`; failure returns a structured error. Unknown,
ambiguous or untranslated references display a localized unavailable message,
while technical diagnostics remain separate. Another language is not a valid
fallback.

UI catalogue output carries `UiText`. Parameterized messages declare argument
types, and numeric formatters reject non-finite values. `presentationOutput`
accepts only approved presentation types.

Regenerate and verify with:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
python tools/knowledge/generate_knowledge_web.py --check --check-translations
```

`--check-translations` fails when editorial translation work remains. Never
edit generated JSON manually. To inspect pending entries:

```powershell
$displayPath = 'outputs/web-public/knowledge/display-text.json'
$display = Get-Content -LiteralPath $displayPath -Raw | ConvertFrom-Json
$display.translation_todos | Select-Object status, location
```

Generated list indexes are not stable IDs or source line numbers. Resolve the
owning `ref`, search its stable ID under `sources/knowledge`, confirm context,
and edit the canonical YAML before regenerating.

## Saved data and exports

Prefer structured facts such as `applied_result` and `roll_history_events` over
captured display strings. Recognized legacy records may use explicit
compatibility resolvers. Unknown system text remains in persistence but displays
as unavailable.

The PDF writer follows the same typed boundary as React. It resolves KB names
again, preserves user-authored names, formats values by locale and accepts only
presentation values in human-readable cells.

## Scope and proof

The audit covers TypeScript, JSX and CSS sources, accessible attributes, common
DOM and document writers, imported workspace modules and presentation types.
Its tests inject deliberate leaks, casts and incomplete provenance paths.

A clean report is not proof of linguistic quality or every runtime state. It
does not execute third-party libraries, arbitrary dynamic JavaScript or all
interactive flows. Representative rendered tests, bilingual export checks and
manual inspection still matter. Do not store volatile finding counts or
per-batch migration status here; generated reports and tests are the source of
truth.
