# Mordheim Campaign Manager — horizontal GUI prototype

This prototype explores a **campaign-timeline-first** desktop interface for Mordheim.
The campaign is the product: immutable warband states are connected by Battles and
Post-Battle transitions.

## New in this iteration: Initial Warband construction

The first campaign moment can now be an editable **INITIAL WARBAND · DRAFT**.
It deliberately reuses the strong horizontal roster-sheet structure of the original
Band Builder while simplifying the visible controls:

- characteristics, equipment, skills/rules and experience remain visible together;
- the card shows the resulting state, while **Edit** owns the editing workflow;
- Heroes and Henchmen remain separate construction tabs;
- top metrics show Gold, Rating, Models and Heroes;
- the bottom guardrail summarizes recruitment/equipment cost, treasury and legality;
- **Start Campaign** turns the draft into immutable **State #0** in the prototype.

The campaign name in the Campaign header is a selector. Its menu contains:

- **New Campaign…** — opens a small campaign/warband dialog;
- **Open creation example** — returns to the populated construction prototype;
- **Open campaign example** — opens the longer timeline demo;
- **Manage Campaigns…** — visual placeholder for the future campaign library.


## Post-Battle sequence redesign

Post-Battle starts **after** the Battle timeline node. The interface exposes eight
sequential player actions arranged as four balanced chapters:

```text
RECOVERY                 EXPLORATION & INCOME        SEARCHES                    WARBAND
01 Injuries              03 Exploration             05 Veterans                 07 Recruitment
02 Experience            04 Sell Wyrdstone          06 Rare Items & Dramatis    08 Equipment
```

The UI intentionally combines the traditional Rare Items and Dramatis Personae
searches into one action while preserving their internal order. `Experience` also
contains any advancement rolls triggered by the newly allocated XP. Warband rating
is derived automatically, so it is shown in **Final Review** rather than becoming a
button the player has to press. Final Review is an application confirmation outside
the eight rules-facing actions.

A strong four-column progress navigator shows completed chapters, the current
chapter and locked future actions. Any action that requires dice starts unresolved
and asks the player to choose **Roll in app** or **Enter manually** before a result is
revealed.

## Run

```bash
python run_prototype.py
```

Python 3.11+ and Tkinter are sufficient.

## Prototype boundaries

This remains interface-first. The new campaign dialog, Add/Edit warrior actions,
KB queries, rule validation and persistence are deliberately not the real domain
implementation yet. The GUI consumes view-model data through `AppController` so
those pieces can be replaced without coupling Tk widgets to YAML or storage.

## Searches and Equipment usability pass

This iteration makes two post-battle phases more action-oriented:

- successful Rare Item searches reveal a contextual **Buy** action only after the dice result is known;
- successful Dramatis Personae searches reveal a contextual **Hire** action only after the character is located;
- **Equipment** is split vertically into a purchase workspace (with current treasury always visible) and a lower inventory notebook;
- the default **Stash** tab shows every owned item, current holders, unassigned quantity and contextual **Assign / Sell** actions;
- **By Warrior** remains available as a secondary way to inspect the same equipment state.

The prototype is still visual-first: these controls demonstrate placement and workflow, not final campaign rules or persistence.
