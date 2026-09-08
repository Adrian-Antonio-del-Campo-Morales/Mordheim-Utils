# Web migration — Phase 0 preparation map

Status: preparation only. No behaviour change. This document inventories the
Campaign Manager code, records its current import boundaries, and lists the
modules that are candidates for extraction during the migration described in
`web-migration-plan.md`.

## Scope confirmation

- The web migration covers **only** the Warband Manager / Campaign Manager
  (`mordheim_campaign`).
- Combat Lab, `mordheim_combat`, the NumPy/Cython engines and any combat
  simulation stay out of the web bundle and the port plan.
- The shared KB in `sources/knowledge/` remains the single canonical source;
  the web consumes a generated artefact (Phase 4), never a copy of the YAML.

## Current package layout

```text
src/mordheim_campaign/          (~14.2k lines total)
  app.py                        entry point; wires theme, locales, AppController + AppShell
  application/                  (~6.7k lines) domain + use-case layer
    state.py                    AppState, CampaignVM, WarriorVM, ... (677)
    controller.py               AppController: use cases + undo history (1205)
    knowledge_port.py           KnowledgePort: read-only DTOs over the KB (648)
    hire_eligibility.py         hire decision rules (435)
    post_battle_engine.py       post-battle state transitions (2191)
    post_battle_resolution.py   serious injury outcomes (583)
    post_battle_catalogue.py    post-battle action catalogue (554)
    rules_catalogue.py          items/skills/rules display catalogue (285)
    scenario_rewards.py         scenario reward rules (139)
  persistence/
    campaigns.py                .mordheim save/load (format v3, 354 lines)
    warband_pdf.py              PDF roster export (fpdf2)
  ui/                           (~6.5k lines) Tkinter views, panels, dialogs
```

## Import boundaries (verified 2026-09-08)

Verified by scanning every module's imports:

- `application/` imports: stdlib, `mordheim_knowledge` (loaders, i18n,
  rules_catalog) and sibling `mordheim_campaign.application` modules.
  **No tkinter, no `mordheim_ui`, no filesystem writes** in the application
  layer.
- `persistence/campaigns.py` imports only stdlib + `application.state`.
  `persistence/warband_pdf.py` imports `fpdf2` + `mordheim_ui.i18n` (locale
  strings) + `application.state`.
- `ui/` imports `application.*` (controller, state, knowledge_port,
  post_battle_catalogue) and `persistence` — never `mordheim_knowledge`
  directly. All Tkinter usage stays in `ui/` and `app.py`.
- `app.py` composes: `mordheim_ui` theme/i18n, `mordheim_knowledge.i18n`,
  `AppController`, `AppShell`.

### Existing coupling to resolve during migration

1. **Locale switching** (`controller.set_locale`): the application layer
   calls both `mordheim_ui.i18n.set_locale` and
   `mordheim_knowledge.i18n.set_locale`. The web port must replace this with
   a locale mechanism that does not depend on `mordheim_ui`.
2. **Display strings from the KB** (`knowledge_port`, `rules_catalogue`,
   `post_battle_catalogue`): names/effects are resolved through
   `mordheim_knowledge.i18n` at read time. The web artefact must carry
   per-locale display strings or the web must resolve them itself.
3. **`AppController.persist_path` / `campaign_library_path`**: `Path`-based
   filesystem knowledge inside the application layer. Harmless for the
   desktop adapter, but the domain/application split (Phase 2) must move
   path handling to the persistence adapter.
4. **`pending_battle_draft` and view fields live in `AppState`** alongside
   campaign state; the v4 contract separates `campaign` and `view`, so the
   state model will need a matching split.

## Layer classification (plan §10 Fase 0 output)

| Module | Layer | Extraction candidate |
| --- | --- | --- |
| `application/state.py` | domain (models) | Yes — campaign domain, minus view fields |
| `application/controller.py` | application | Split: pure use cases → domain/application; undo + locale + paths → app shell |
| `application/post_battle_engine.py` | domain | Yes — largest pure-logic block |
| `application/post_battle_resolution.py` | domain | Yes |
| `application/post_battle_catalogue.py` | application | Yes (KB-dependent) |
| `application/hire_eligibility.py` | domain | Yes |
| `application/knowledge_port.py` | application/adapter | Port interface stays; Python impl stays in desktop adapter |
| `application/rules_catalogue.py` | application | Yes (KB-dependent) |
| `application/scenario_rewards.py` | domain | Yes |
| `persistence/campaigns.py` | persistence adapter | Format v4 rewrite target (Phase 1) |
| `persistence/warband_pdf.py` | persistence adapter | Desktop-only; stays |
| `ui/**`, `app.py` | UI adapter | Stays (desktop); not ported |

## Public entry points today

- Console script `mordheim-campaign-manager` → `mordheim_campaign.app:main`.
- `python -m mordheim_campaign` (`__main__.py` → `app.main`).
- `tools/mordheim-utils.py warband-manager` → `python -m mordheim_campaign`.
- Public imports consumed by tests: `mordheim_campaign.application`
  (`AppState`, VMs, `KnowledgePort`, `make_draft_state`,
  `make_example_state`), `mordheim_campaign.persistence`
  (`load_campaign`, `save_campaign`, `CampaignFileError`,
  `export_campaign_summary`, `suggest_filename`).

## Test coverage available as regression net

`tests/campaign/` — 15 modules, 196 tests, **no Tkinter required**:
battle creation, dice resolution, draft, equipment editor, hire eligibility,
knowledge port, out-of-action tracking, persistence (round-trip),
post-battle (advancements, engine, resolution), rules catalogue, undo,
variable prices/restrictions, warband PDF.

These tests run without a window and are the regression net for Phases 1-2.

## Current file format (Phase 1 starting point)

`persistence/campaigns.py`: self-contained JSON, marker
`MORDHEIM_CAMPAIGN_MANAGER`, `format_version: 3`, top-level sections
`campaign` + `view`, KB references by stable IDs (`band_id`, `profile_id`,
`item_id`), `saved_at` UTC timestamp. Loader rejects wrong marker/version
with `CampaignFileError`. `tests/campaign/test_persistence.py` holds the
existing round-trip behaviour.
