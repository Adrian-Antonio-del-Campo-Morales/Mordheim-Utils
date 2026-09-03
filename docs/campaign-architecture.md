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
    │   └── state.py            # view models + canonical builders
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
canonical item names and inherent rules. Draft rosters are derived from the KB and
edited through controller actions that enforce per-profile/group/model/gold limits.
`mordheim_campaign/persistence` saves and loads `.mordheim` JSON files (marker +
format version) and exports Markdown summaries; the payload references stable KB IDs
(`band_id`, `profile_id`, `item_id`) and never serializes rules.

Still future: rule validation and resolution of post-battle steps, and per-warrior
equipment/skill editors. They should continue to depend only on UI-facing models and
controller actions, not on `KnowledgePort` or storage directly.

## Post-Battle interaction boundary

`PostBattleMoment` owns the phase composition, while reusable interaction pieces
live under `mordheim_campaign.ui.components`:

- `PostBattleSequence` communicates the ordered eight-action transition as four balanced UI chapters.
- `DiceResolutionCard` handles the UI choice between application dice and
  physical/manual dice entry without knowing the underlying Mordheim table.

The future rules layer should provide dice expressions and resolved outcomes;
the widgets should remain responsible only for interaction and presentation.
Battle facts remain in `BattleMoment` and are linked from Post-Battle rather than
duplicated as a workflow phase.


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
