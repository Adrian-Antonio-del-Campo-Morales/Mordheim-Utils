# Campaign Manager

The Campaign Manager (`mordheim_campaign`) explores a **campaign-timeline-first**
desktop interface for Mordheim. The campaign is the product: immutable warband
states are connected by Battles and Post-Battle transitions.

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

`InitialWarbandDraftMoment` is the only editable moment. Once the campaign
begins, each commit appends an immutable `StateVM`; `BattleVM` nodes record
real table facts; each battle opens a pending `PostBattleVM` that resolves
into the next state.

## Layer rule

```text
KB YAML → mordheim_knowledge.loader → application.knowledge_port → AppController → ui
                                                                    ↕ persistence
```

`ui` never imports the KB loaders or YAML. `application` and `persistence`
never import Tkinter. Campaign files reference stable KB IDs only
(`band_id`, `profile_id`, `item_id`); the rules never leave the KB.

- `application/knowledge_port.py` — KB read model (bands, profiles, items,
  skills, hirelings, campaign catalogues, warband groups, scenario options).
- `application/controller.py` — UI-facing actions; draft editing; battle
  recording; equipment moves.
- `application/state.py` — view models (`CampaignVM`, `StateVM`, `BattleVM`,
  `PostBattleVM`, `WarriorVM`) and the canonical builders.
- `application/hire_eligibility.py` — the 18 roster-dependent
  `*.rule.campaign-eligibility` rules keyed by canonical rule id over a small
  hire context (band groups, member and employed Hired Sword profile ids,
  optional Mercenary variant), returning explicit
  `allowed/rejected/conditional/needs_variant` decisions. The hireling facts
  the rules reason about come from the KB trait registry
  (`catalog/hirelings/traits.yaml` → `KnowledgePort.hireling_traits()`), not
  from curated sets in the application.
- `application/post_battle_resolution.py` — serious injuries (hero D66 and
  henchman D6 charts with subtables), exploration dice and the rare-item
  2D6 rarity test, read from the validated catalogues.
- `application/post_battle_catalogue.py` — Trading Post common/rare offers
  with warband-level restrictions and the confirmed `price_override`
  exceptions; hiring offers with fee/upkeep labels; per-action KB provenance.
- `application/post_battle_engine.py` — the write side: applies resolved
  outcomes (roster, XP, treasury, shards, hires, stash, advances) and commits
  the next immutable State. Working totals live on the persisted
  `PostBattleVM`, so a mid-sequence save/load resumes exactly where the
  player was.
- `persistence/campaigns.py` — `.mordheim` JSON save/load (marker + format
  version) and Markdown export.
- `ui/` — dialogs, components, panels and the timeline `views/moments/`.

Construction UI principle: **the card shows the result; Edit reveals the
controls that modify it.** Editing controls do not live permanently on roster
cards.

## Post-battle sequence

Post-Battle starts after the Battle timeline node. Eight sequential player
actions in four balanced chapters:

```text
RECOVERY                 EXPLORATION & INCOME        SEARCHES                    WARBAND
01 Injuries              03 Exploration             05 Veterans                 07 Recruitment
02 Experience            04 Sell Wyrdstone          06 Rare Items & Dramatis    08 Equipment
```

Rare Items and Dramatis Personae searches are combined into one action while
preserving their internal order. `Experience` also contains advancement rolls
triggered by the newly allocated XP. Warband rating is derived automatically,
so it appears in **Final Review** rather than as a button. Any action that
requires dice starts unresolved and asks the player to choose **Roll in app**
or **Enter manually** before a result is revealed. `DiceResolutionCard`
supports contextual result actions (e.g. **Buy**, **Hire**) that stay hidden
until the roll resolves successfully.

## Feature status

**KB-backed warbands and campaign files.** The warband picker lists every
canonical warband (collections `mordheim`/`trollheim`, ruleset `mordheim`)
with model range and starting gold; band selection derives a draft roster from
the KB (required members, legal minimum starter, canonical profiles,roster limits). Header file actions save/load `.mordheim` files and export a Markdown summary plus a **PDF warband sheet** of the moment selected in the timeline.

**PDF warband export.** `Export PDF` renders the warband at the selected timeline moment (`persistence/warband_pdf.py`, `fpdf2`): campaign/warband identity, the state's aggregates, the full roster with statlines, equipment, skills and advances, the battles recorded up to that moment and the inventory ledger. Every committed state deep-copies its roster and inventory at commit time (`WarbandStateVM.roster`/`inventory`), so any past State #N exports exactly as it was; the draft exports the live roster. The campaign file format is v3 (old files are rejected, no migration), and display labels follow `MORDHEIM_LOCALE` through the shared i18n reader.

**Hiring.** Offers merge static eligibility (fee, upkeep, availability) with
the 18 dynamic rules. Variant-capable warbands pick their Mercenary variant
(Reikland/Middenheim/Marienburg/Ostermark) in the Campaign header; it
persists in the `.mordheim` file and re-evaluates every variant-dependent
offer. Employed Hired Swords are tracked by the roster (`hireling.*` profile
ids), so mutual-exclusion rules fire (hiring a Highwayman makes the
Roadwarden offer ineligible, and vice versa). Conditional offers surface the
acceptance roll; rejected offers are not shown.

**Battle recording.** The timeline's ＋ RECORD BATTLE node opens a dialog fed
by the KB scenario catalogue (1v1 first): opponent, result (Victory/Defeat/
Draw), XP granted, Out of Action checklist (the casualties count is derived
from it) and optional opponent rating. `AppController.record_battle`
validates the scenario, ignores unknown warrior ids in the submitted lists
(the post-battle filter skips them too) and refuses only known warriors that
cannot receive results, snapshots `rating_before`/`models_before`, appends
the `BattleVM` plus its pending `PostBattleVM`, and is refused while a
post-battle is pending or the warband is still a draft. Recording is
unblocked once COMMIT STATE runs. The participants tab lists the real roster
with current conditions. Recovery (step 1) offers injury cards only for the
warriors recorded Out of Action; battles recorded with none marked offer
every warrior.

**Scenario progression is applied at battle recording.**
`application/scenario_rewards.py` builds the award plan from the scenario's
`progression:` block and the canonical awards of
`experience-and-advances.yaml`; the dialog computes per-warrior XP totals
(`xp_awards`) from the battle facts and records prose-only rewards as manual
entries. `controller._apply_recorded_scenario_loot` applies the structured
additional rewards to the pending post-battle: gold crowns, wyrdstone
fragments, exploration-die modifiers, items and special results. The
material reward rules themselves live in the published
`catalog/campaign/scenario-rewards.yaml` catalogue, validated by
`mordheim_knowledge` and consumed through the `KnowledgePort`.

**Undo is application-wide and undoable actions carry real labels.**
`AppController.perform_undoable` retains the previous state snapshot for the
latest twenty actions and names each entry with the caller's description or
the action's own result message; the shell Undo button (and Ctrl+Z) shows a
translated `Undo: <label>`, closes any modal editor before restoring the
snapshot, and the post-battle sequence, skill/spell commits, advance rolls,
henchman promotions, recruitment and the mercenary-variant switch all flow
through it.

**Locale switching goes through the application layer.** The Settings view
never imports `mordheim_knowledge` (the layer rule forbids it):
`AppController.set_locale` switches both the UI string reader
(`mordheim_ui.i18n`) and the KB display-name reader
(`mordheim_knowledge.i18n`) and notifies the shell to rebuild.

**Post-battle mutations.** Injuries mutate the roster, XP and
purchases/trades move the projected treasury and stash, exploration and the
once-per-sequence wyrdstone sale move the shard hoard, and **COMMIT STATE**
appends the next immutable state with rating derived from the final roster.
Every action prints its KB provenance.

**Advances are fully live.** The Experience step seeds a pending advance per
crossed XP threshold (KB ladder `advance_thresholds` in
`experience-and-advances.yaml`), resolves the 2D6 roll (with D6 sub-rolls for
the choice rows) against the KB advancement tables, and commits the pick:
characteristic increases respect the KB racial maximums
(`catalog/rules/racial-maximums.yaml`, race from the warband-group registry)
and the henchman +1-over-starting cap; skills are chosen from the warrior's
KB skill tables; spells from the wizard's lore (`SkillChoiceDialog`, with the
duplicate-spell "lower difficulty" message). Blocked advances stay
uncommitted for a reroll. All persisted mid-sequence (resumable).

**The Lad's Got Talent is applied** (henchman row 10–12): one member splits
off as a Hero keeping type, experience and characteristic increases, picks 2
skills from the warband's hero tables via the promotion-mode skill dialog;
the remaining group stays a henchman row and its advance resets for a reroll
(the promotion itself is excluded); the pending promotion bypasses the static
hero limit (`on_maximum_heroes`) for exactly one earned advance — once the
hero exists it counts against the limit normally.

**Equipment is editable per warrior.** The state moment's EQUIPMENT action
(and the inventory's BY WARRIOR MANAGE buttons) open `EquipmentEditorDialog`:
roster blocks with RETURN, a stash column with ASSIGN. Moves
(`move_stash_to_warrior` / `return_warrior_to_stash`) are legal at any
campaign moment (tabletop reallocation), keep the inventory ledger
(owned/equipped/stash) consistent, and buying/selling stays inside the
post-battle sequence.

**Searches and Equipment are actionable end to end**: successful Rare Item
searches reveal a contextual **Buy** action and successful Dramatis searches
a contextual **Hire** action only after the dice resolve; **Equipment** is
split into a purchase workspace (treasury always visible) and an inventory
notebook whose Stash view shows every owned item with holders, unassigned
quantity and Assign/Sell actions; the wyrdstone sale uses the KB pricing
table (fragments × warband size) and is one-shot per sequence.

## Still open

- Per-warrior skill editing outside advances.
- Out-of-sequence purchases and resource corrections (would reuse the same
  stored IDs).
- Campaign library ("Manage Campaigns…" header entry), inventory ADD ITEM and
  MANAGE RESOURCES toolbar actions.

## Run

```bash
python -m mordheim_campaign
# equivalent entries:
mordheim-campaign-manager
python tools/mordheim-utils.py warband-manager
```

Python 3.10+ and Tkinter are sufficient.

See [Architecture](architecture.md) for the package map and
[the KB guide](knowledge-base.md) for the catalogues it reads.
