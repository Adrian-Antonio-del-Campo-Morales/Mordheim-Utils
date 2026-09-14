# Campaign Manager

The Campaign Manager is implemented as two adapters over the same campaign concepts:

- **Desktop:** Tkinter UI in `packages/python/campaign/mordheim_campaign/ui/`, composed by `apps/warband-manager-desktop/mordheim_desktop`.
- **Web:** React/Vite UI in `apps/warband-manager-web/`, backed by the TypeScript packages in `packages/typescript/`.

The desktop and web UIs are not pixel-identical. They share the campaign workflow, stable IDs and v4 file contract while respecting platform differences: desktop uses filesystem dialogs; web imports and downloads files and keeps campaigns in the browser session only.

## Timeline model

```text
Initial Warband (draft)
        ↓ commit
State #0
        ↓
Battle #1
        ↓
Post-Battle #1
        ↓
State #1
        ↓
...
```

`InitialWarbandDraftMoment` is the editable construction stage. Committing it creates an immutable `WarbandStateVM`. A `BattleVM` records facts from the table and opens a pending `PostBattleVM`. Completing the post-battle sequence commits the next immutable state.

## Layer rule

```text
sources/knowledge/*.yaml
        ↓
mordheim_knowledge / generated knowledge-web.json
        ↓
application and domain services
        ↓
Tkinter or React UI
        ↕
versioned campaign persistence
```

UIs never read YAML or decide rules. Campaign files store state and stable KB IDs (`band_id`, `profile_id`, `item_id`, `rule_id`); they do not serialize rule definitions.

## Implemented capabilities

### Draft construction

- Select any canonical warband from the `mordheim` or `trollheim` collections.
- Build the initial roster with required profiles, model minimum/maximum, hero limit and treasury validation.
- Add, remove, rename and resize henchman groups.
- Buy creation equipment, buy stash items and apply supported weapon upgrades.
- Hire eligible Hired Swords and choose a Mercenary variant where the selected warband supports it.
- Assign, return and transfer equipment while maintaining owned/equipped/stash quantities.
- Apply auditable manual corrections for resources, known items and skills where the adapter exposes the action.

### Campaign timeline and battles

- Navigate draft, committed states, recorded battles and pending post-battles.
- Record scenario, opponent, result, XP, casualties, Out-of-Action members, optional opponent rating and notes.
- Resolve pre-battle availability checks such as Old Battle Wound.
- Preserve participant snapshots, rating/model counters and scenario progression rewards.
- Keep historical states read-only and export the selected timeline moment.

### Canonical post-battle sequence and UI presentation

The knowledge base defines the normative **10-step** sequence. The desktop UI groups those rules into **8 user actions**: rare-item and Dramatis Personae searches share one action, and warband-rating update is derived automatically and shown in final review. The web follows the same application workflow and contract; it must not be read as changing the canonical rule order.

The canonical order is:

1. Serious Injuries
2. Allocate Experience
3. Roll on the Exploration Chart
4. Sell Wyrdstone
5. Check Available Veterans
6. Make Rarity Rolls and Buy Rare Items
7. Look for Dramatis Personae
8. Hire Recruits and Buy Common Items
9. Reallocate Equipment
10. Update Warband Rating

The UI's eight actions are:

1. Injuries
2. Experience and advancement rolls
3. Exploration
4. Sell Wyrdstone
5. Veterans
6. Rare Items and Dramatis Personae searches
7. Recruitment
8. Equipment and final derived rating

The flow supports app dice or manual results, persisted intermediate data, pending follow-ups, contextual Buy/Hire actions, XP advancement tables, injuries, recruitment, resources, stash/equipment changes and final review before committing the next state. The desktop sequence is composed by `PostBattleSequence`; resolution and mutations belong to `PostBattleResolver`, `PostBattleCatalogue` and `PostBattleEngine`, not to widgets.

### Rules and reporting

Both adapters expose a read-only rules browser with categories, search, effects, sources and profile links. The web app also exposes campaign statistics. These views read the generated knowledge artefact or the application KnowledgePort and do not mutate campaign state.

### Files and exports

- Desktop: open/save `.mordheim`, export Markdown summary and export a PDF warband sheet for the selected draft/state moment.
- Web: import one or more `.mordheim` files, keep sessions in memory, download v4 JSON and export a PDF warband sheet. Reload/close loses unexported sessions after the browser warning.
- Both reject v1–v3 and unsupported future formats. See [the v4 contract](../../contracts/campaign-file-v4/README.md).

## Stable IDs and knowledge ownership

Warband/profile/item/rule names shown in the UI are display values. Eligibility, restrictions, prices, advancement tables and scenario rewards are resolved from the canonical KB through the application layer. The web consumes `knowledge-web.json`, generated by `tools/knowledge/generate_knowledge_web.py`; it does not bundle YAML.

The campaign catalogue is published data consumed by the campaign runtime. It is not duel-engine implementation. See [Knowledge base](knowledge-base.md) and the catalogue HOWTO for ownership rules.

## Known scope boundaries

These are deliberate non-features of the current product, not undocumented bugs:

- the duel engine models 1-vs-1 close combat, not a full tabletop battle;
- the Campaign Manager records scenario facts but does not simulate terrain, deployment or complete on-table scenario mechanics;
- web campaigns are session-only and require explicit export;
- the desktop campaign library is filesystem-oriented; the web library is session-oriented;
- per-warrior skill editing outside the supported advance/manual-correction paths remains limited;
- compatibility migration from v1–v3 campaign files is not provided.

## Run

```powershell
mordheim-campaign-manager
python -m mordheim_desktop
python tools/mordheim-utils.py warband-manager

cd apps/warband-manager-web
npm run dev
```

See [Architecture](architecture.md) for package boundaries and [Verification](verification.md) for the executable test strategy.
