# Mordheim Campaign Manager — horizontal GUI prototype

This prototype explores a **campaign-timeline-first** desktop interface for Mordheim.
The campaign is the product: immutable warband states are connected by Battles and
Post-Battle transitions.

## New in this iteration: KB read side and dynamic hiring eligibility

The application layer now consumes the published campaign catalogues through
`KnowledgePort` (`post_battle_sequence()`, `campaign_catalog()`,
`hireling_catalogue()`, `warband_groups()`):

- **Dynamic hire eligibility** (`application/hire_eligibility.py`): the 18
  roster-dependent `*.rule.campaign-eligibility` rules of `catalog/hirelings/**`
  (task 4 of the ingestion report) are evaluated against the warband context —
  band groups from the registry, member and employed-Hired-Sword profile ids,
  optional Mercenary variant. The race/alignment/nature facts the rules read
  (elf, dwarf, human, undead, ogre, evil, spellcaster, priest, fear-causing)
  are declared in `catalog/hirelings/traits.yaml` and loaded via
  `KnowledgePort.hireling_traits()`; only the warband-side heuristics (band
  groups and band-member profile keywords) stay in the application. Every rule
  id is a reviewed key in the module, and ambiguous contexts produce explicit
  `needs_variant`/`unknown` decisions rather than guesses. Hired Swords and
  Dramatis offers that are rejected by a rule are not shown; conditional ones
  surface the acceptance roll in the UI.
- **KB-backed post-battle resolution** (`application/post_battle_resolution.py`):
  serious injuries (hero D66 and henchman D6 charts, including printed row-major
  ranges and follow-up subtables), exploration dice (shards by total plus the
  matching-dice special results) and the rare-item 2D6 rarity test read the
  validated catalogue rows — nothing is canned text.
- **Post-battle catalogue** (`application/post_battle_catalogue.py`): Trading Post
  common/rare offers with warband-level restrictions and the confirmed
  `price_override` market exceptions, hiring offers with fee/upkeep resource
  labels, and the KB provenance (sequence step ids, resolved catalogues) of each
  of the eight actions.

The outcomes are now **applied to the campaign** (`application/post_battle_engine.py`):
injuries mutate the roster, XP and purchases/trades move the projected treasury and
stash, exploration and the once-per-sequence wyrdstone sale move the shard hoard,
and **COMMIT STATE** appends the next immutable state with rating derived from the
final roster. Working totals live on the persisted post-battle record, so a
mid-sequence save/load resumes exactly where the player was.

The eligibility context is now complete: **variant-capable warbands pick their
Mercenary variant** (Reikland/Middenheim/Marienburg/Ostermark) from a selector in
the Campaign header — it persists in the `.mordheim` file and re-evaluates every
variant-dependent offer (e.g. Maximilian the Mad and the Warrior Priest of Sigmar
become eligible outside Middenheim and disappear for Middenheimers). **Employed
Hired Swords are tracked by the roster** (hirelings are warriors with `hireling.*`
profile ids), so the mutual-exclusion rules fire: hiring a Highwayman immediately
makes the Roadwarden offer ineligible, and vice versa.

**Battles are recorded from the table**: the timeline's ＋ RECORD BATTLE node opens
a dialog fed by the KB scenario catalogue (1v1 first); opponent, result (Victory /
Defeat / Draw), XP granted, the warriors recorded Out of Action (a checklist) and
opponent rating become a real Battle node with its pending Post-Battle — no more
example narrative. The casualties count is derived from the checklist, and
Recovery (post-battle step 1) offers injury cards only for the recorded warriors;
battles recorded before this feature (or with none marked) offer every warrior.
Derived numbers (rating, models) snapshot the current state automatically,
recording is blocked while a post-battle is pending, and the participants tab
lists the roster with current conditions instead of hardcoded demo status.

## New in this iteration: KB-backed warbands and campaign files

The warband picker in **Create Campaign** now lists every canonical warband of the
knowledge base (collections `mordheim` and `trollheim`, ruleset `mordheim`) with its
model range and starting gold. Band selection produces a **draft roster derived from
the KB**: required members and a legal minimum starter, canonical profiles with
characteristics, costs, starting XP, skill access and inherent rules, plus the band
roster limits used by legality.

The roster actions in the draft are real now: **+ ADD HERO / + ADD HENCHMEN GROUP**
open a KB-fed profile picker (with per-profile and group limits), the **…** menu of a
row resizes henchmen groups or removes the entry, and Start Campaign commits when the
composition is legal. Editing per-warrior equipment/skills stays a future campaign
rules use case.

File actions in the header are wired to a versioned persistence layer
(`mordheim_campaign/persistence`): **Save/Load** use `.mordheim` JSON files with the
full campaign state (including the active view so you can resume), and **Export**
writes a readable Markdown summary. **SAVE & CLOSE** in Post-Battle saves the pending
campaign and returns to the current state.

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

The prototype ships inside the monorepo — no separate script exists.

```bash
python -m mordheim_campaign
# equivalent entries:
mordheim-campaign-manager
python tools/mordheim-utils.py warband-manager
```

Python 3.11+ and Tkinter are sufficient.

## Prototype boundaries

This remains interface-first. Warband and profile data arrive as view models through
`AppController` from `KnowledgePort` (which wraps the `mordheim_knowledge` loaders), so
Tk widgets never read YAML or know where the KB lives. Campaign persistence is JSON
with a stable schema and does not serialize rules. Post-battle resolutions mutate the
campaign state (roster, treasury, equipment, advances), battles are recorded from real
table facts and the per-warrior equipment editor works at any moment; out-of-sequence
purchases and resource corrections remain future use cases that will reuse the same
IDs (`band_id`, `profile_id`, `item_id`) already stored in the campaign state.

Deleted pre-timeline code: `roster_view.py`, `post_battle_view.py` and the
`battle_history` / `campaign_overview` / `warband_status` panels were unreachable
prototype shells; removal left no dangling references.

## Searches and Equipment usability pass

This iteration makes two post-battle phases more action-oriented:

- successful Rare Item searches reveal a contextual **Buy** action only after the dice result is known;
- successful Dramatis Personae searches reveal a contextual **Hire** action only after the character is located;
- **Equipment** is split vertically into a purchase workspace (with current treasury always visible) and a lower inventory notebook;
- the default **Stash** tab shows every owned item, current holders, unassigned quantity and contextual **Assign / Sell** actions;
- **By Warrior** remains available as a secondary way to inspect the same equipment state.

The Searches and Equipment steps are now **actionable end to end**: offer lists come
from the KB, the dice cards resolve live against the KB tables, and every contextual
action — **Buy** (rare and common), **Hire** (Hired Swords and Dramatis Personae,
with conditional acceptance rolls), **Assign / Sell** and the equipment purchases —
mutates the campaign through `post_battle_engine` (treasury, stash, roster). The
wyrdstone sale uses the KB pricing table (fragments × warband size) and is
one-shot per sequence. Each of the eight actions still prints its KB provenance.

What is still missing: nothing in the loop between recording a battle and committing
its state. **Advances are fully live**: the
Experience step seeds a pending advance per crossed XP threshold (KB ladder),
resolves the 2D6 roll (with D6 sub-rolls for rows 6/8/9) against the KB
advancement tables, and commits the pick — characteristic increases respect the
KB racial maximums and the henchman +1-over-starting cap, skills are chosen from
the warrior's KB skill tables, and spells from the wizard's lore
(`SkillChoiceDialog`). **The Lad's Got Talent is applied** (henchman row 10):
one member splits off as a Hero keeping type, experience and characteristic
increases, picks 2 skills from the warband's hero tables via the promotion-mode
skill dialog, the remaining group stays a henchman row and its advance resets
for a reroll (the promotion itself is excluded), and the promotion bypasses the
static hero limit while pending. All of it is persisted mid-sequence (resumable)
and applied to the roster.

**Equipment is editable per warrior**: the state moment's EQUIPMENT action (and
the inventory's BY WARRIOR MANAGE buttons) open the `EquipmentEditorDialog` —
roster blocks with RETURN and a stash column with ASSIGN — legal at any campaign
moment, keeping the inventory ledger (owned/equipped/stash) consistent.
