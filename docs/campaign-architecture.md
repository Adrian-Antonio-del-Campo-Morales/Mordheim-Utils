# Architecture direction

The prototype keeps three layers so the current GUI work can survive the real
implementation.

```text
src/
├── mordheim_core/        # future domain + KB-facing ports
├── mordheim_ui/          # reusable theme and generic Mordheim widgets
└── mordheim_campaign/
    ├── application/
    │   ├── knowledge_port.py   # KB read model (mordheim_knowledge loaders)
    │   ├── controller.py       # UI-facing actions + draft editing
    │   ├── state.py            # view models + canonical builders
    │   ├── hire_eligibility.py # the 18 roster-dependent hire rules
    │   ├── post_battle_catalogue.py  # trading post + hiring offers, provenance
    │   ├── post_battle_resolution.py # injuries / exploration / rarity dice
    │   └── post_battle_engine.py     # applies outcomes, commits next State
    ├── persistence/campaigns.py  # .mordheim JSON save/load + Markdown export
    └── ui/
        ├── dialogs/      # NewCampaignDialog, AddWarriorDialog
        ├── components/   # dice resolution + sequential workflow UI
        ├── panels/       # timeline, inventory, shared cards
        └── views/
            └── moments/
                ├── initial_warband_draft.py
                ├── state_moment.py
                ├── battle_moment.py
                └── post_battle_moment.py
```

Layer rule (executable in `tests/architecture/test_boundaries.py`):

```text
KB YAML → mordheim_knowledge.loader → application.knowledge_port → AppController → ui
                                                                    ↕ persistence
```

`ui` never imports the KB loaders or YAML. `application` and `persistence` never
import Tkinter. Campaign files reference stable KB IDs only; the rules never leave
the KB.

## Central timeline model

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

`InitialWarbandDraftMoment` is intentionally a special editable moment. Once the
campaign begins it becomes the same historical State #0 used by the rest of the
application.

## Construction UI principle

The construction screen is denser than ordinary campaign views because its single
job is to configure the roster. Density is still controlled by one rule:

> The card shows the result; Edit reveals the controls that modify it.

Therefore +/- characteristic buttons, equipment checkboxes and other editing
controls do not live permanently on the roster cards.

## Real implementation status

`KnowledgePort` (application) now provides the KB read model used to replace the old
demo warband/profile data: canonical band picker, profile DTOs with roster limits,
canonical item names, inherent rules and the flat Trading Post price exceptions
(`price_override`). Draft rosters are derived from the KB and edited through controller
actions that enforce per-profile/group/model/gold limits.
`mordheim_campaign/persistence` saves and loads `.mordheim` JSON files (marker +
format version) and exports Markdown summaries; the payload references stable KB IDs
(`band_id`, `profile_id`, `item_id`) and never serializes rules.

Beyond the read model, the application layer implements the first campaign-side
rule consumers of the catalogues (see the Campaign Manager guide's *New in this
iteration* section):

- `hire_eligibility.py` — the 18 dynamic `*.rule.campaign-eligibility` rules keyed
  by canonical rule id over a small hire context (band groups, member and employed
  Hired Sword profile ids, optional Mercenary variant), with explicit
  `allowed/rejected/conditional/needs_variant` decisions; the hireling facts the
  rules reason about come from the KB trait registry
  (`catalog/hirelings/traits.yaml` → `KnowledgePort.hireling_traits()`), not from
  curated sets in the application;
- `post_battle_resolution.py` — serious-injury, exploration and rarity dice read
  from the validated campaign catalogues;
- `post_battle_catalogue.py` — Trading Post and hiring offers with static + dynamic
  eligibility and per-action KB provenance.
- `post_battle_engine.py` — the write side: applies resolved outcomes to the
  campaign (roster, XP, treasury, shards, hires, stash) and commits the next
  immutable State. Working gold/wyrdstone deltas live on the persisted
  `PostBattleVM` so a mid-sequence save/load resumes in place.

The eligibility context is complete: `CampaignVM.mercenary_variant` (set via
`AppController.set_mercenary_variant`, listed in the Campaign header for
variant-capable bands and persisted) and employed Hired Swords derived from the
roster (`hireling.*` profile ids, fed into `PostBattleCatalogue` as
`hired_sword_profile_ids`) let every dynamic rule fire instead of returning
`needs_variant`.

Advances are applied by the same engine: crossed XP thresholds (KB ladder in
`experience-and-advances.yaml`) seed persisted `pending_advances` on
`PostBattleVM`; the 2D6 roll and D6 sub-rolls resolve against the KB advancement
tables; committed picks mutate the roster (stats into `WarriorVM.stat_advances`,
respecting racial maximums and the henchman +1-over-starting cap; skills from the
warrior's KB tables; spells from the wizard's lore). The Lad's Got Talent row
(henchman 10-12) splits one member off as a Hero preserving type, experience and
stat advances, spends 2 promotion picks on the warband's hero skill tables, and
resets the remaining group's advance for its reroll; the pending promotion
bypasses the static hero limit (KB ``on_maximum_heroes``).

Battles are created through `AppController.record_battle`: it validates the
scenario against the KB catalogue, snapshots `rating_before`/`models_before` from
the current state, appends a `BattleVM` plus its pending `PostBattleVM`, and is
refused while a post-battle is pending or the warband is still a draft. The
recorded `out_of_action_ids` derive the ``casualties`` count and scope Recovery
(step 1) to those warriors; ``None`` (legacy battles) keeps the every-warrior
fallback.

Equipment moves between roster and stash are always legal (tabletop
reallocation): `PostBattleEngine.move_stash_to_warrior` /
`return_warrior_to_stash` need no pending sequence, and the
`EquipmentEditorDialog` (state moment EQUIPMENT action, inventory BY WARRIOR
MANAGE) drives them through `AppController.assign_stash_item` /
`return_equipped_item`. The inventory ledger keeps owned/equipped/stash
consistent; selling stays a post-battle action.

Still future: nothing in the record-battle → commit-state loop; pending work is
per-warrior skill editing outside advances and battle-side details (scenario
progression rolls).

## Post-Battle interaction boundary

`PostBattleMoment` owns the phase composition, while reusable interaction pieces
live under `mordheim_campaign.ui.components`:

- `PostBattleSequence` communicates the ordered eight-action transition as four balanced UI chapters.
- `DiceResolutionCard` handles the UI choice between application dice and
  physical/manual dice entry without knowing the underlying Mordheim table.

The rules layer lives in `mordheim_campaign.application` (not the widgets):
`PostBattleResolver` resolves injuries, exploration and rarity tests from the
catalogues, `PostBattleCatalogue` supplies the offers and per-action KB
provenance, and `PostBattleEngine` applies the outcomes and commits the next
state. The widgets only present results and trigger engine actions; the engine
keeps depending only on UI-facing models and controller actions. Battle facts
remain in `BattleMoment` and are linked from Post-Battle rather than duplicated
as a workflow phase.


## Post-Battle UI chapters

The interactive sequence is grouped 2/2/2/2 for clarity: Recovery, Exploration & Income, Searches and Warband. Advances are resolved inside Experience; traditional source steps 6–7 share the Searches action; rating is derived and appears in Final Review.

## Post-Battle contextual actions

`DiceResolutionCard` now supports optional result actions. This keeps search actions
hidden until a roll has actually resolved successfully, so the UI can expose
contextual operations such as **Buy rare item** or **Hire Dramatis Personae** without
cluttering the unresolved dice state.

The Equipment phase remains one post-battle action but has two UI responsibilities:
1. a compact purchase control with treasury in context;
2. an inventory notebook whose Stash view is the primary equipment-management surface.

These are view concerns only. Final affordability, eligibility, assignment and sale
rules belong in application/domain services rather than Tk widgets.
