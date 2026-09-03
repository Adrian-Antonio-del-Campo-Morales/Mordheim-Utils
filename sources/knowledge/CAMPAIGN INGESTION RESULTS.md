# CAMPAIGN INGESTION

## Hired Swords & Dramatis Personae

This document summarizes the final state of the **Hired Swords** and **Dramatis Personae** ingestion, the modelling decisions taken during the process and the pending work to integrate this part into the shared KB.

> This file is ingestion documentation. It is not part of the executable rules model.

## Status

- **Profiles identified:** 102
- **Hired Swords:** 72
- **Dramatis Personae:** 30
- **Profiles normalized within scope:** 98
- **Profiles deliberately out of scope:** 4
- **Campaign hiring entries:** 98
- **Eligibility modelled:** 98/98
- **Dynamic/conditional rules the application must evaluate:** 18
- **Shared KB originally modified:** Yes — v2 catalogue integrated and published; profiles/groups already live in `sources/knowledge`

The functional ingestion of Hired Swords and Dramatis Personae is considered **complete**. The **integration into the shared Mordheim-Utils KB is done**: `sources/knowledge/catalog/campaign/hired-swords-and-dramatis.yaml` is schema v2 with `status: published`, its 98 entries resolve against `catalog/hirelings/**` and `registry/warband-groups.yaml`, and the invariants are covered in `tests/knowledge/test_campaign_catalogs.py` (Mercenaries section). The following TODOs 2–5 are loader/runtime work in the applications, outside the scope of the KB data.

## Where each piece of information lives in the KB

### `catalog/hirelings/**`
- canonical hireling identity
- characteristics
- intrinsic equipment
- skill access
- starting skills
- intrinsic special rules
- intrinsic warband-rating contribution

### `catalog/campaign/hired-swords-and-dramatis.yaml`
- hiring fee
- upkeep
- availability/search procedure
- static hiring eligibility
- campaign-state hiring resolution contract

### `registry/warband-groups.yaml`
- explicit reusable sets of canonical band_id values used by hiring eligibility

## ID conventions

- **hired sword profile:** `hireling.hired-sword.<slug>`
- **dramatis profile:** `hireling.dramatis.<slug>`
- **warband group:** `warband-group.<slug>`

## Modelling decisions and invariants

- Do not reuse a band profile as a hireling profile merely because names match.
- Existing canonical item_id values are referenced; item definitions are not duplicated.
- Existing canonical skill IDs are referenced only when equivalence is explicit.
- Source-only or unresolved concepts are never assigned guessed canonical IDs.
- Campaign-resolved rolls, choices and rewards remain outside the KB.
- Current-roster and selected-warband-variant eligibility checks live as hireling rules and are evaluated by the application.

## Specific decisions taken during the ingestion

- **hireling.hired-sword.goblin-lantern-bearer** — May be hired by any warband.
- Dynamic roster-dependent restrictions are modelled at hireling rule level and checked by the application.
- Chaos/followers-of-Chaos/devoted-to-Chaos hireling restrictions use warband-group.chaotic.
- Halfling Thief uses warband-group.elf rather than a Wood-Elf-only group.

## Deliberately out-of-scope work

These four Dramatis entries do not block the closing of the ingestion:

- **`hireling.dramatis.ulli-and-marquand`** — Composite entry with two independent warrior profiles.
- **`hireling.dramatis.belandysh-condemned-champion-of-chen`** — Random characteristics plus random-characteristic mount.
- **`hireling.dramatis.luthor-wolfenbaum`** — Single identity with multiple selectable personas/loadouts.
- **`hireling.dramatis.the-headless-horseman`** — Composite rider-and-steed entity with separate profiles.

# TODO

## Required before integrating into the shared KB

### 1. hirelings.integration.schema-v2 — COMPLETED

**Target:** `catalog/campaign/hired-swords-and-dramatis.yaml`

Schema_version 2 integrated into the shared KB (`status: published`), with invariants in `tests/knowledge/test_campaign_catalogs.py`.

Includes:
- hiring_fee/upkeep resource structures instead of hiring_fee_gc/upkeep_gc
- availability_procedures and special availability kinds
- eligibility simple lists
- eligibility boolean expression with all_of/any_of/not

> Pending only in the applications: updating the consumers that expect schema_version 1 (loaders/runtime), never in the KB data.

### 2. hirelings.integration.profile-resolution

**Target:** `shared loaders/validators`

Resolve profile_id references against catalog/hirelings/** as well as existing band profile locations.

### 3. hirelings.integration.warband-groups

**Target:** `shared loaders/validators and campaign evaluator`

Load registry/warband-groups.yaml and resolve warband-group.* references used by eligibility.

### 4. hirelings.integration.application-rules

**Target:** `campaign/warband-building application`

Implement the 18 campaign-eligibility rule IDs that depend on current roster composition, current hirelings, selected Mercenary variant, or a conditional acceptance roll. Do not infer these from static warband groups.

Rules to implement in the application (18):
- `hireling.dramatis.dijin-katal-the-renegade-assassin.rule.campaign-eligibility`
- `hireling.dramatis.grand-master-ippan-shu.rule.campaign-eligibility`
- `hireling.dramatis.maximilian-the-mad.rule.campaign-eligibility`
- `hireling.dramatis.william-schakestange-master-bard.rule.campaign-eligibility`
- `hireling.hired-sword.cathayan-merchant.rule.campaign-eligibility`
- `hireling.hired-sword.dwarf-treasure-hunter.rule.campaign-eligibility`
- `hireling.hired-sword.dwarf-troll-slayer.rule.campaign-eligibility`
- `hireling.hired-sword.elf-ranger.rule.campaign-eligibility`
- `hireling.hired-sword.grave-robber.rule.campaign-eligibility`
- `hireling.hired-sword.highwayman.rule.campaign-eligibility`
- `hireling.hired-sword.knight-of-the-white-wolf.rule.campaign-eligibility`
- `hireling.hired-sword.ninja-gnoblar.rule.campaign-eligibility`
- `hireling.hired-sword.roadwarden.rule.campaign-eligibility`
- `hireling.hired-sword.runesmith-journeyman.rule.campaign-eligibility`
- `hireling.hired-sword.shadow-warrior.rule.campaign-eligibility`
- `hireling.hired-sword.warrior-priest-of-sigmar.rule.campaign-eligibility`
- `hireling.hired-sword.witch-hunter.rule.campaign-eligibility`
- `hireling.hired-sword.wolf-priest-of-ulric.rule.campaign-eligibility`

### 5. hirelings.integration.resource-ids

**Target:** `campaign resource handling`

Confirm/port canonical handling for every resource used by hireling costs, especially treasures and campaign_points.

Resources affected:
- `gold_crowns`
- `wyrdstone_fragments`
- `treasures`
- `campaign_points`

### 6. campaign.runtime-loaders — PENDING (not started)

**Target:** `mordheim_knowledge` (application runtime; outside the data scope)

Implement the campaign loaders requested for the next milestone, **without touching the KB**
or the vectorized engine:
- `load_campaign_catalog(...)` — load the catalogues from `catalog/campaign/**`
  (scenarios, post-battle-sequence, experience-and-advances, serious-injuries,
  trading-post, magic, mutations, hired-swords-and-dramatis, …), validating
  `schema_version`, per-document ID uniqueness and reference resolution
  (item_ids, profile_ids, lore_ids, band_ids, warband-group.*).
- `load_post_battle_sequence(...)` — specific loader for the
  `post-battle-sequence.yaml` catalogue with the same validation.
- Start from a use case that receives campaign state (roster + match results)
  and consumes the loaded catalogues; the loading contract must be reusable
  by `mordheim_campaign.application.knowledge_port`.

## Non-blocking KB tracking for hiring

### 1. hirelings.groups.good-aligned — COMPLETED

**Target:** `registry/warband-groups.yaml`

Membership audit of `warband-group.good-aligned` completed and `status: partial`
removed (**40 warbands**). It does not contradict `warband-group.evil` nor `warband-group.chaotic`.

**Method (warband by warband against mordheimer.net):** the warband pages on the site
do not publish an alignment tag; the classification relies on (a) the official
Hired Swords availability texts (express parity of access with the Human Mercenary
warbands, unrestricted access to good-aligned contract swords, or short exclusion
lists that leave them available) and (b) membership of canonically good races/orders
(Dwarfs, High Elves, Halflings, Sigmar's orders, Bretonnian knights, imperial
institutions), when the warband does not belong to the registry's own evil/chaotic groups.

**Added during the audit (14):**
- `hochland-bandits`, `kislevites`, `merchant-caravans`, `pirates`, `lustria-pirates` —
  the page declares Hired Swords access identical to a Human Mercenary warband
  (pirates: «same access to Hired Swords & any other items as for a regular human
  Mercenary Warband»).
- `imperial-outriders` — mounted swords only, including the Roadwarden (good-aligned contract).
- `outlaws-of-stirwood-forest` — only 4 exclusions (Bounty Hunter, Wolf-Priest of
  Ulric, Norse Shaman, Dark Elf Assassin); the remaining swords, including the
  good-aligned contract ones, stay available.
- `bretonnian-knights`, `bretonnian-chapel-guard`, `chaos-streets-bretonnian-knights` —
  Bretonnian knightly order (Chivalry, Holy Water, no poisons/drugs).
- `chaos-streets-sigmar-protectorate` — mirror of `warband-group.sigmar-devoted`
  (Sisters of Sigmar and Witch Hunters were already included).
- `lustria-high-elves` — mirror of `warband-group.high-elf` (Shadow Warriors and Sons of
  Nagarythe were already included).
- `mootlanders` — halfling race, no contrary declaration on the page (race convention).
- `gunnery-school-of-nuln` — imperial state institution; the page does not publish a
  Hired Swords section (documented inference).

**Residual doubts (warbands with no source declaration, treated as non-good/
neutral and therefore NOT included):** `horned-hunters`, `lustrian-reavers`,
`khemri-mages`, `khemri-thieves-guild`, `chaos-streets-arcane-society`,
`chaos-streets-deathbringers`, `chaos-streets-mordheim-inhabitants`, `lustria-pygmies`,
and the orc/goblin warbands (`black-orcs`, `orc-mob`, `forest-goblins`, `night-goblins-*`,
`lustria-savage-goblins`, `khemri-hobgoblin-raiders`, `chaos-streets-greenskins`), which
the hiring canon expressly excludes («Orcs & Goblins»). If a future source classifies
them, the audit must be repeated only for those warbands.

### 2. hirelings.profile-dependencies

**Target:** `catalog items/skills/magic/companions and related rule catalogs`

Canonicalize the remaining intrinsic profile references below when the corresponding shared KB schemas/catalogs exist. These do not prevent hiring/cost/eligibility from being represented.

There are **59 pending intrinsic references**:
- `advancement_choice`: 1
- `alternate_hire_payment`: 1
- `alternate_profile`: 1
- `availability_procedure`: 1
- `companion_profile`: 2
- `companion_profiles`: 1
- `dependent_hirelings`: 1
- `entity_semantics`: 2
- `equipment_choice`: 5
- `equipment_loadout`: 1
- `equipment_mapping`: 12
- `equipment_modifier`: 2
- `equipment_restriction`: 1
- `item_instance_modifier`: 1
- `mount_profile`: 3
- `patron_branch`: 1
- `prayer_list`: 1
- `rating_formula`: 1
- `rune_system`: 1
- `skill`: 16
- `skill_set`: 1
- `special_skill_options`: 1
- `summoning_procedure`: 2

> **Update (link with magic.yaml):** the 15 `spell_list` references
> of the hired sword and dramatis personae profiles were linked with
> the canonical `lore_id` values of `catalog/campaign/magic.yaml` (45 lore↔wizard
> assignments and 31 lores with 188 spells; `pending_lores` empty). They were removed
> from the profiles' `unresolved_references` (0 pending of type
> `spell_list`). This includes registering the canonical lore `lore.dark-magic` (the
> Dark Mage's Dark Magic list, Letters of the Damned 6), transcribed from its
> hiring page because it was not indexed in the magic section of the site.

<details>
<summary>See the pending references one by one</summary>

- **`hireling.dramatis.aksho-akhash-the-vile-dreadwing-lord-of-the-carrion-throne`** · `summoning_procedure` — Chaos spell-caster + Macabre Tome + Leadership test
- **`hireling.dramatis.bertha-bestraufrung`** · `skill` — Righteous Fury — Only a band-scoped rule exists in the supplied KB; no global canonical skill ID.
- **`hireling.dramatis.bertha-bestraufrung`** · `prayer_list` — Prayers of Sigmar — No canonical prayer/spell catalogue exists in the supplied KB.
- **`hireling.dramatis.countess-marianna-chevaux-vampire-assassin`** · `equipment_modifier` — garlic coating acting as Black Lotus against Vampires
- **`hireling.dramatis.dijin-katal-the-renegade-assassin`** · `equipment_mapping` — Repeater Crossbow
- **`hireling.dramatis.grand-master-ippan-shu`** · `skill` — Art of Silent Death
- **`hireling.dramatis.grand-master-ippan-shu`** · `skill_set` — all Speed skills and Battle Monk special skills except Warmonger
- **`hireling.dramatis.heinrich-altdorf-schmidt`** · `equipment_mapping` — Lantern
- **`hireling.dramatis.innominatus-the-tilean-gladiator`** · `skill` — Pit Fighter
- **`hireling.dramatis.innominatus-the-tilean-gladiator`** · `skill` — Grizzled Veteran
- **`hireling.dramatis.innominatus-the-tilean-gladiator`** · `skill` — Death without a face
- **`hireling.dramatis.khar-mel-the-djinn`** · `summoning_procedure` — requires wizard/priest Leadership summoning procedure
- **`hireling.dramatis.maglah-khan-s-horde`** · `mount_profile` — Giant Wolf M9 WS3 BS0 S3 T3 W1 I4 A1 Ld4
- **`hireling.dramatis.maglah-khan-s-horde`** · `dependent_hirelings` — 2-5 Hobgoblin Scouts
- **`hireling.dramatis.penthesilea-mark-of-the-serpent`** · `skill` — Mesmerising Dance
- **`hireling.dramatis.penthesilea-mark-of-the-serpent`** · `skill` — Savage Fury
- **`hireling.dramatis.penthesilea-mark-of-the-serpent`** · `skill` — Elixir of Life
- **`hireling.dramatis.penthesilea-mark-of-the-serpent`** · `skill` — Weapon Master
- **`hireling.dramatis.penthesilea-mark-of-the-serpent`** · `skill` — Concealment
- **`hireling.dramatis.penthesilea-mark-of-the-serpent`** · `availability_procedure` — Amazon-only rating-difference search table
- **`hireling.dramatis.sigmund-spindle-the-harvester-of-flesh`** · `alternate_hire_payment` — one Hero body part / Severe Arm Wound
- **`hireling.dramatis.the-foole`** · `item_instance_modifier` — Master Craftsman weapon modifications
- **`hireling.dramatis.william-schakestange-master-bard`** · `skill` — Ride Pantomime Horse
- **`hireling.dramatis.william-schakestange-master-bard`** · `skill` — Swashbuckler (Pirate Warband skill)
- **`hireling.dramatis.william-schakestange-master-bard`** · `mount_profile` — Pantomime Horse M8 WS3 BS0 S3 T3 W1 I3 A1 Ld5; adds +6 rating when fielded
- **`hireling.hired-sword.black-orc-overseer`** · `equipment_choice` — two Axes or Double-handed Weapon
- **`hireling.hired-sword.bounty-hunter`** · `equipment_mapping` — Lantern
- **`hireling.hired-sword.chameleon-skink`** · `equipment_modifier` — poison darts
- **`hireling.hired-sword.chaos-centaur`** · `equipment_choice` — Sword or Spear
- **`hireling.hired-sword.chaos-centaur`** · `advancement_choice` — may take a mutation instead of a skill
- **`hireling.hired-sword.cursed-hillman`** · `alternate_profile` — Wolf form M7 WS4 BS0 S4 T4 W2 I5 A2(3) Ld6
- **`hireling.hired-sword.dark-elf-assassin`** · `equipment_mapping` — Repeater Crossbow
- **`hireling.hired-sword.dwarf-slayer-pirate`** · `equipment_loadout` — multiple Pistols as defined by source
- **`hireling.hired-sword.dwarf-troll-slayer`** · `equipment_mapping` — Double-Handed Axe
- **`hireling.hired-sword.emissary-of-chaos`** · `patron_branch` — Khorne/Tzeentch/Nurgle/Slaanesh; Tzeentch changes skill access
- **`hireling.hired-sword.gaoler`** · `equipment_choice` — heavy chain (counts as flail) or two Hammers/Clubs
- **`hireling.hired-sword.goblin-lantern-bearer`** · `equipment_mapping` — Lantern
- **`hireling.hired-sword.grave-robber`** · `equipment_mapping` — Lantern
- **`hireling.hired-sword.halfling-knight`** · `companion_profile` — Hound M5* WS4 BS0 S4 T3 W1 I4 A1 Ld5
- **`hireling.hired-sword.hobgoblin-scout`** · `mount_profile` — Giant Wolf profile M9 WS3 BS0 S3 T3 W1 I4 A1 Ld4
- **`hireling.hired-sword.knight-of-the-white-wolf`** · `skill` — Ride Warhorse
- **`hireling.hired-sword.ninja`** · `skill` — Art of Silent Death
- **`hireling.hired-sword.ninja`** · `skill` — Lightning Speed
- **`hireling.hired-sword.ninja`** · `skill` — Leap of Faith
- **`hireling.hired-sword.norse-shaman`** · `equipment_choice` — Sword or Axe
- **`hireling.hired-sword.ogre-bodyguard`** · `equipment_mapping` — Double-Handed Weapon
- **`hireling.hired-sword.priest-of-morr`** · `entity_semantics` — Mercenary Hero replacement rather than normal Hired Sword
- **`hireling.hired-sword.roadwarden`** · `equipment_mapping` — three Torches
- **`hireling.hired-sword.runesmith-journeyman`** · `rune_system` — Rune use
- **`hireling.hired-sword.snake-charmer`** · `companion_profiles` — three snakes with separate profile
- **`hireling.hired-sword.snake-charmer`** · `rating_formula` — +5 per snake in addition to charmer rating
- **`hireling.hired-sword.the-fallen-sister`** · `equipment_mapping` — Sling
- **`hireling.hired-sword.ungor-trapper`** · `special_skill_options` — Mutant/Fearless/Manhater
- **`hireling.hired-sword.witch-hunter`** · `equipment_choice` — Duelling Pistol or Crossbow Pistol
- **`hireling.hired-sword.witch-hunter`** · `equipment_mapping` — Garlic
- **`hireling.hired-sword.wolf-priest-of-ulric`** · `entity_semantics` — Middenheim Hero replacement rather than normal Hired Sword
- **`hireling.hired-sword.wolf-priest-of-ulric`** · `equipment_restriction` — blunt weapons only except dagger; no armour except white wolf cloak
- **`hireling.hired-sword.wolf-priest-of-ulric`** · `companion_profile` — Wolf Companion
- **`hireling.hired-sword.wood-elf-hunter`** · `equipment_mapping` — Hunting Arrows

</details>

# Package validation

**Scope:** structural/internal consistency of the final generated package

## Checks

- ✅ all yaml parses
- ✅ yaml only package
- ✅ campaign profile ids resolve
- ✅ static group references resolve
- ✅ static band references resolve against supplied kb
- ✅ boolean eligibility grammar valid
- ✅ goblin lantern bearer unrestricted
- ✅ good aligned group still marked partial

## Counts

- **yaml files:** 17
- **profiles total:** 102
- **profiles normalized in scope:** 98
- **profiles out of scope:** 4
- **hired sword profiles:** 72
- **dramatis profiles:** 30
- **campaign hired swords:** 72
- **campaign dramatis in scope:** 26
- **campaign entries total:** 98
- **warband groups:** 24
- **dynamic application rule ids:** 18
- **in scope unresolved intrinsic references:** 59

> This validation does not replace future loader/runtime integration tests in the shared KB projects.

## Final baseline

The functional files that make up this delivery are:

- `catalog/hirelings/hired-swords/*.yaml`
- `catalog/hirelings/dramatis-personae/*.yaml`
- `catalog/campaign/hired-swords-and-dramatis.yaml`
- `registry/warband-groups.yaml`

This document (`CAMPAIGN INGESTION RESULTS.md`) is only the ingestion and integration documentation.
