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

The command runs detector regressions followed by the strict, deep audit. It
writes `outputs/web-presentation/gui-text-audit-deep.json` for machines and
`outputs/web-presentation/gui-text-audit-deep.md` for human review.

A finding does not always prove that the current UI is wrong. It proves that
the detector cannot establish that the output is protected. That uncertainty
blocks acceptance until the source and destination are classified. Never hide
it with a cast or suppression.

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
