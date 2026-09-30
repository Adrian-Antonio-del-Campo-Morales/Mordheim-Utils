# Implement the warband reference template

This is an implementation specification for **Rules → Warbands** in the web
Warband Manager. The Spanish tab is **Reglas → Bandas**. The intended result is
a complete, localized reference sheet for every published warband, using the
structure of the [Sisters of Sigmar example](https://mordheimer.net/docs/warbands/grade-1a-warbands/sisters-of-sigmar).

Use one reusable GUI template fed by structured knowledge. Content agents
complete and verify knowledge records; they do not write separate React pages,
HTML files, Markdown sheets or presentation layouts for each warband.

Read [Campaign knowledge](campaign-knowledge.md),
[Web presentation](../reference/web-presentation.md) and
[Verification](../reference/verification.md) before implementation.

## Product decisions

- Rename the visible `band-rules` category to `Bandas` / `Warbands`. Keep its
  internal identity and existing local-rule catalogue APIs.
- List every published band, including bands with no local special rules.
  Do not inherit exclusions from the campaign-creation picker or Settings.
- Sort localized names alphabetically and display the localized category.
- Within this tab, search only localized band names, ignoring case and accents.
  Other tabs retain their current global rule search.
- Selecting a band opens its complete sheet. Desktop uses a list and detail
  layout; mobile uses list/detail navigation with a back control.
- Keep search, list scroll position and the originating button's focus when
  returning from the mobile sheet. Changing language preserves band identity
  when it is still in the filtered result set.
- Use the current KB only. Do not import narrative background or new rules
  from the reference site. The site is a structural example, not a runtime API.
- Show variants in their own section. They do not change the rest of the sheet.
- Missing published information gets a localized absence message. A section
  that does not apply is omitted. Neither absence means zero or unlimited.
- This is a read-only reference feature, not a new campaign action or editor.

## The template and its data contract

### Ownership and flow

```text
canonical band and catalogue YAML
  → sanctioned knowledge loaders
  → generated browser artefacts
  → ArtefactKnowledgeReader
  → typed warband reference read model
  → WarbandReferenceTemplate
  → presentationOutput at visible/accessibility boundaries
```

The GUI foundation uses an application-level read model under
`packages/typescript/application/rules/warband-reference.ts`. It must have no
React or DOM dependency. Expose a localized band list and a lookup by band ID;
the lookup returns a structured sheet or an explicit missing result.

The common web component is
`apps/warband-manager-web/src/features/rules/WarbandReferenceTemplate.tsx`.
It accepts the resolved sheet and locale. `WarbandsBrowser.tsx` owns band
selection, query-dependent detail state, the back control, focus and scroll
restoration. `RulesPage` in `apps/warband-manager-web/src/ProductApp.tsx`
integrates that wrapper and owns the search input.

Profile cards share `WarriorProfileSummary.tsx` with the campaign's
`WarriorCard.tsx`: characteristic tiles, equipment and rule panels.
They use the campaign's three-column desktop layout and responsive stacking,
with skill access and the shared `ExperienceTrack` in the footer. The reference
shows published starting experience, recruitment limits below the profile name,
group size where declared, and restrictions within the equipment panel.
Already resolved reference items and profile rules use `KnowledgeTextHint`
from `KnowledgeHint.tsx`, retaining campaign hover/focus tooltips and touch
popovers. Equipment categories form compact two-column tables (item/price)
in a responsive grid; notes appear beneath the relevant item, without an
empty notes column. Armour and shields/defences share a table, as do equipment
and combat equipment. Column labels are visually hidden but remain accessible.
Main section headings use a larger gold title, a tinted
header and a gold divider.

The generator now publishes original equipment lists and scoped shared-rule
delegations in the deferred warband-reference section described below. The GUI
reads list names, recipients, prices, item notes, list notes and sources from
that section. A profile's equipment restriction has a single description: a
declared, localized bound rule that owns it (`profile.equipment-restrictions`)
is authoritative, so profiles covered by one carry no `equipment_restrictions`
aggregate and the sheet composes the restriction from those rules. The
deferred section still publishes `profile_restrictions` prose, with optional
`equipment_restrictions_i18n` source text, only for profiles with no such rule,
and the reader falls back to it. Sisters of Sigmar and Underworld
Alliance include Spanish list/notes text, and Underworld's animal/troll
restrictions are translated. Translations for other lists remain content work.
Source contracts accept list names/notes, item notes and profile restrictions
with the existing Spanish translation format. Explicit list `applies_to.profile_types`
recipients supplement profile/list relationships for reference display only.
Every item referenced by a published band's equipment lists or fixed equipment
is now included in the deferred catalogue regardless of its item kind.
Without full list metadata,
it shows a clearly labelled recruitment-equipment summary rather than naming
lists from their IDs. Missing catalogue items remain explicit absences.
The real Sisters sheet exercises composition, all five profiles, the skill
matrix, special skills, equipment and prayers, but is not yet a complete
content-coverage example.

Focused tests live in `tests/typescript/application/rules/warband-reference.test.ts`
and `tests/web/warband-reference-template.test.tsx`, alongside the updated
`tests/web/rules-page.test.tsx`. They cover the real bilingual Sisters sheet,
scoped identities, optional list metadata/shared delegation, unchanged base
roster with variants, empty bands, search and mobile focus/scroll restoration.
Underworld regressions cover list names/notes, four hero recipients of the
miscellaneous list, Cerbatana publication, restrictions and merged equipment tables.
They do not certify complete content coverage of all bands.

The dynamic presentation audit passes for the tested rendered surfaces.
The strict static audit still flags the new component-model props and callback
paths, alongside existing application findings. Review their source-to-output
contracts; do not suppress them or call the global presentation gate clean.

Use explicit typed fields for composition, warriors, skill tables, equipment
lists, rules, magic, variants and sources. Names and prose must be resolved
presentation values; IDs remain selection/link identities. Numbers and
characteristic values use existing field-specific formatters. Do not solve
typing with arbitrary string casts.

### Fixed section order

Render a localized title/category and a compact index of the sections actually
present. Use native links, headings, tables and `details`/`summary`; add no
dependencies or generic layout engine.

| Section | Template responsibilities | Data responsibilities |
| --- | --- | --- |
| Composition | Initial crowns, model bounds and recruitment overview | `band.roster`, including per-profile bounds and group sizes |
| Warriors | Group heroes, henchmen and other published types; show cost, XP, characteristics, starting equipment, restrictions and own rules | Scoped profiles plus roster membership and declared rule relationships |
| Skills | Profile/category access matrix followed by peer collapsible categories (Special, Combat, Academic, etc.), with each skill nested inside its category | `skill_access`, bounded `skill_lists`, starting skills and selectable band rules |
| Equipment | Preserve each printed list, group items by kind, show creation price, eligible profiles and notes; item descriptions/rules in hover/focus tooltips and touch popovers | Full equipment lists, profile/list relationships and item catalogue |
| Special rules | Full band-wide rules; profile rules stay with their warriors | `applies_to`, band/profile IDs and shared-rule delegation |
| Magic and prayers | Assigned users, lore names, spells, difficulties and full effects | Scoped `magic.lore_assignments` and `magic.lores` |
| Variants | Name and declared differences in crowns, roster, bonuses, equipment and rules | Published variants, resolved in the owning band |
| Sources | Links to published source URLs | Band, profile, list, rule and catalogue source records |

Keep tables readable on small screens with horizontal scrolling contained in
the table wrapper, not the entire page. Accessible labels, empty states and
expanded content must be localized too. The index must not link to omitted
sections. Scope anchors to the selected band and section.

Respect explicit bounded skill lists: category access alone must not grant
every special skill. Separate selectable special abilities from inherent
rules according to published metadata, not an English name substring.

For recruitment, explicit `maximum: null` means no per-profile maximum beyond
the band total; a missing maximum is unpublished. Keep `maximum: 0` profiles
identified as variant-only when a declared variant opens their roster slot.
Do not present every profile as available in the base roster.

Equipment list membership is not proof that every profile can use every item.
Show declared restrictions and do not label all list items as legal purchases
for all recipients. Keep creation prices distinct from later trading prices.
Fixed starting equipment does not become an optional purchase.

Keep global item and skill descriptions reusable. Resolve repeated profile
and rule IDs within their owning band; never use the adapter's unscoped
profile fallback for sheet relationships. Deduplicate a rule within its
section without erasing distinct owners or different printed applications.

## Browser data changes

The generated bands and profiles already contain most composition, stats,
experience, skill access, variant and equipment-access information. Reuse it.
Recruitment still uses flattened equipment access. The reference additionally
preserves the original lists and their metadata. `_build_rules_prose` keeps
shared-rule delegations outside `profile-special-rules`; the reference section
publishes their scoped relationships without duplicating shared prose.

`tools/knowledge/generate_knowledge_web.py` publishes an optional deferred
`campaign["warband-reference"]` section containing `rows`, one per band:

- `band_id`: the owning published band.
- `equipment_lists`: original lists with stable IDs, localized names, full
  item rows, costs, localized notes and sources.
- `rule_refs`: local rule ID, referenced shared-rule ID, declared scope and
  selectable kind when present. Resolve the shared rule's name/effect through
  the shared catalogue; do not duplicate its prose.
- Future extension: `profile_restrictions`, scoped textual equipment restrictions, retaining
  source text and explicit translations where they are not already available
  through a declared localized rule.

This additive section needs no persistence migration or schema-version bump.
Existing consumers can ignore it. Older artefacts without it must still
render available composition/profiles and explicitly indicate missing list
metadata; they must not synthesize list names from internal IDs.

Publish this section in `knowledge-catalogue.json`, using the existing
catalogue loading gate. Do not load it at application startup, create a
parallel network loader, copy the whole band/profile catalogue into it or
increase the initial-download budget.

Add nested names and notes to the existing presentation contract in
`tools/knowledge/presentation_contract.py` as necessary. Verify stable
locators survive reordering and that their identity includes band ownership.
Original rows, not caller-created copies, must reach `recordText`; that
method resolves registered presentation rows only.

Translations belong in canonical knowledge records using the existing
`name_i18n`, `notes_i18n` and applicable prose fields. Preserve English source
text and IDs. Do not add a GUI dictionary keyed by arbitrary English sentences
or infer translations from IDs. Inspect loader/schema support before adding
fields. Complete translations for every field newly exposed by this feature.

The translation workload is substantial: inspection found 366 equipment
lists with untranslated names and 449 distinct untranslated item-note
strings. Recompute coverage before assigning content batches. Also inventory
profile restriction prose. Rendering the whole sheet in Spanish is not
complete merely because profile and rule names are translated.

Editorial/runtime comments and internal identifiers embedded in source prose
must not become product explanations. Preserve editorial evidence in its
appropriate source metadata and publish the actual game clause in localized
presentation fields. Do not hide leaked IDs with a general text replacement.

Regenerate ignored browser outputs using the official generator; never edit
them by hand. Keep tests and fixed contracts under `tests/`, not beside UI
components or in generated output directories.

## Generator example for review

The GUI template and read model are implemented; the generator extension is
not. A preliminary generator-only draft was removed because it depended on a
translation file that did not exist. The following preserves its useful design
idea as an example, not a tested implementation:

```python
def build_warband_reference(packages):
    rows = []
    for package in packages:
        rows.append({
            "band_id": package.band["id"],
            # Convert using the generator's localized-row conventions.
            # Preserve item notes and source metadata; sort deterministically.
            "equipment_lists": [localized_list(row)
                                for row in package.equipment_lists],
            "rule_refs": [
                {key: rule[key]
                 for key in ("id", "rule_ref", "applies_to", "kind")
                 if key in rule}
                for rule in package.special_rules if rule.get("rule_ref")
            ],
            "profile_restrictions": localized_profile_restrictions(package),
        })
    return {"rows": sorted(rows, key=lambda row: row["band_id"])}
```

`localized_list` and `localized_profile_restrictions` are explanatory
placeholders, not existing APIs. Replace them with the smallest implementation
using canonical translations and the existing generator/resolver contract.
Filter packages by the generator's current ruleset and published collections.

## Work split and handoff

### A. Template and pipeline implementer

Build the typed read model, deferred metadata, one common GUI template and
browser integration. Use Sisters of Sigmar as the complete vertical example.
Load all other bands through that same path using their existing records;
do not hard-code the example or hand-author one display document per band.

Establish focused generation, model and rendering tests, then produce a
coverage inventory of missing translations, unresolved references and
unpublished fields, identified by canonical file and scoped entity. Generated
coverage reports belong under `outputs/` and do not replace source tests.

This stage proves the reusable template and example. It does not certify
complete multilingual coverage of every band while content work remains.

### B. Content implementers

Assign disjoint canonical band directories by collection/band ID. Supply the
shared template contract and the coverage inventory. Each content implementer
must reuse existing records, add only necessary translations/metadata, verify
all source relationships and run focused checks for their assigned bands.
Do not allow independent components, band-ID exceptions or bespoke layouts.

Shared item, skill and magic catalogues need a single designated owner per
batch to avoid conflicting edits. If an agent finds a template deficiency,
report the missing capability to the template owner rather than patching the
layout locally. Agents must not invoke the generator concurrently against the
same output directory; the integration owner regenerates the combined state.

### C. Integration verifier

Regenerate from the combined canonical sources, verify every published band
uses the common template, run cross-band/localization gates and inspect the
real GUI in both languages on desktop and mobile. Report remaining absent
source data separately from unresolved relationships and missing translations.

## Acceptance tests

For Sisters of Sigmar, verify against the canonical records:

| Profile | Recruitment bound | Cost | Starting XP |
| --- | --- | --- | --- |
| Sigmarite Matriarch | Exactly 1 | 70 | 20 |
| Sister Superior | 0–3 | 35 | 8 |
| Augur | 0–1 | 25 | 0 |
| Sigmarite Sister | No per-profile maximum | 25 | 0 |
| Novices | 0–10 | 15 | 0 |

Verify 500 starting crowns, 3–15 models, henchwoman groups of 1–5, all five
stat profiles, the published skill matrix and all five special skills.
Include the Matriarch's Prayers of Sigmar and their full spell descriptions.
Verify first dagger free, heroine-only miscellaneous equipment, the Augur's
armour prohibition and the double-Sigmarite-warhammer restriction. Spanish
Movement values must follow the existing centimetre display convention while
English and stored characteristic values remain canonical.

Additional tests must cover:

- Bands without local special rules, multiple equipment lists and scoped IDs
  reused by another band; no omitted bands or cross-band relationships.
- Shared-rule delegation, bounded skill lists, variant-only profiles and
  variant changes shown without mutating the base sheet.
- Missing source values, missing translations and older artefacts without
  reference metadata; explicit absence, no raw-ID/English display fallback.
- Alphabetical localized ordering, name-only/accent-insensitive search and
  no results. Item/rule text must not match the band-name search.
- Language and band changes, section anchors, keyboard-operable expandable
  text, mobile back navigation with restored query/focus/scroll.
- Visible and accessible text in both languages, including equipment notes
  and restrictions. Test source records and rendered output, not only labels.
- Deferred catalogue loading and stable presentation locators; regeneration
  determinism and unchanged initial delivery budget.

From the repository root, run applicable new and existing tests, including:

```powershell
python tools/knowledge/generate_knowledge_web.py
python tools/knowledge/generate_knowledge_web.py --check
python -m pytest tests/python/web/test_knowledge_artefact.py tests/python/web/test_presentation_contract.py tests/python/web/test_kb_artefact_inventory.py tests/python/web/test_kb_artefact_performance.py
npm run test --workspace campaign-web-core -- rules-catalogue
npm run test --workspace warband-manager-web -- rules-page
npm run typecheck
npm run build
python tools/mordheim-utils.py check-presentation
```

The two filtered npm commands cover existing regressions, not automatically
all newly named suites. Run the new model/template suites explicitly too.
Use the existing presentation-translation check to verify new fields; compare
pre-existing findings before claiming an unrelated global gate is clean.
Do not raise budgets or modify test contracts merely to make checks pass.

Inspect the GUI with desktop and mobile viewport sizes in Spanish and English.
Unit tests/typechecking do not certify visual behaviour. Record which checks
actually ran, any blocked check and its reason; never claim complete coverage
while an assigned content batch or visual verification remains unfinished.

## Workspace boundaries

Before editing, inspect the current branch, worktrees and status. Preserve all
concurrent work. The handoff checkout had unrelated edits in Combat Lab's
equipment/weapon tabs and their Python UI tests; verify status again rather
than assuming those are the only concurrent edits.

Do not recreate the retired desktop app, alter recruitment/campaign mechanics,
change persistence, touch `tools/ingestion/` for this feature, publish a site,
push commits or create commits unless separately requested. Keep maintained
documentation in English and the user-facing completion report in Spanish.
