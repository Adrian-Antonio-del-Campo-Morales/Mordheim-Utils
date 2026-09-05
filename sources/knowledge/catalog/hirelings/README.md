# `catalog/hirelings/` — Hired Swords and Dramatis Personae

Canonical identity of the hirelings a campaign can hire: `hired-swords/` and
`dramatis-personae/` catalogues (102 profiles; 72 Hired Swords, 30 Dramatis
Personae, 4 of them deliberately out of scope). The campaign-side contract —
hiring fee, upkeep, availability/search procedure and static hiring
eligibility — lives in `catalog/campaign/hired-swords-and-dramatis.yaml`; the
reusable band sets its eligibility references live in
`registry/warband-groups.yaml`. This directory holds only what belongs to the
warrior himself.

## What a profile holds

- canonical hireling identity
- characteristics
- intrinsic equipment
- skill access
- starting skills
- intrinsic special rules
- intrinsic warband-rating contribution

## ID conventions

- **hired sword profile:** `hireling.hired-sword.<slug>`
- **dramatis profile:** `hireling.dramatis.<slug>`
- **warband group (referenced, defined in the registry):** `warband-group.<slug>`
- **campaign hiring entry (in `catalog/campaign`):** `campaign.hireling.<slug>`
  with `profile_id` pointing back here

## Modelling decisions and invariants

- Do not reuse a band profile as a hireling profile merely because names match.
- Existing canonical `item_id` values are referenced; item definitions are not
  duplicated.
- Existing canonical skill IDs are referenced only when equivalence is explicit.
- Source-only or unresolved concepts are never assigned guessed canonical IDs;
  they stay in `unresolved_references` until their catalogue exists (see
  below).
- Campaign-resolved rolls, choices and rewards remain outside the KB.
- Current-roster and selected-warband-variant eligibility checks live as
  hireling rules (`*.rule.campaign-eligibility`) and are evaluated by the
  application (`mordheim_campaign/application/hire_eligibility.py`), never
  inferred from static warband groups.
- The race/alignment/nature facts those rules reason about are declared once,
  in `traits.yaml` (this catalogue's trait registry: elf, dwarf, human, undead,
  ogre, evil, spellcaster, priest, fear-causing), validated to resolve against
  the profiles, and loaded by the application through
  `KnowledgePort.hireling_traits()` — the application keeps no curated trait
  sets.
- Chaos / followers-of-Chaos / devoted-to-Chaos hireling restrictions use
  `warband-group.chaotic`.
- The Halfling Thief uses `warband-group.elf` rather than a Wood-Elf-only
  group (as printed).
- `hireling.hired-sword.goblin-lantern-bearer` may be hired by any warband.

## Deliberately out-of-scope profiles

These four Dramatis entries are published in `profiles.yaml` with
`status: out_of_scope` and are excluded from the 98 hiring entries of
`hired-swords-and-dramatis.yaml` (`tests/knowledge/test_campaign_catalogs.py`
pins the count). They do not block the hire model; each waits on a schema for
its entity kind:

| Profile | Reason |
| --- | --- |
| `hireling.dramatis.ulli-and-marquand` | Composite entry with two independent warrior profiles. |
| `hireling.dramatis.belandysh-condemned-champion-of-chen` | Random characteristics plus random-characteristic mount. |
| `hireling.dramatis.luthor-wolfenbaum` | Single identity with multiple selectable personas/loadouts. |
| `hireling.dramatis.the-headless-horseman` | Composite rider-and-steed entity with separate profiles. |

## Unresolved intrinsic references (59)

The profiles reference 59 concepts — equipment mappings/modifiers, skills,
mount and companion profiles, prayers, runes, summoning procedures, alternate
payments/profiles, entity semantics, patron branches, availability procedures —
whose canonical catalogues or schemas do not exist yet in the KB. They are
tracked per profile in each file's `unresolved_references`; the counts by kind
are:

| Kind | Count |
| --- | --- |
| `skill` | 16 |
| `equipment_mapping` | 12 |
| `equipment_choice` | 5 |
| `mount_profile` | 3 |
| `companion_profile` | 2 |
| `summoning_procedure` | 2 |
| `entity_semantics` | 2 |
| `equipment_modifier` | 2 |
| `alternate_hire_payment` | 1 |
| `alternate_profile` | 1 |
| `availability_procedure` | 1 |
| `advancement_choice` | 1 |
| `companion_profiles` | 1 |
| `dependent_hirelings` | 1 |
| `equipment_loadout` | 1 |
| `equipment_restriction` | 1 |
| `item_instance_modifier` | 1 |
| `patron_branch` | 1 |
| `prayer_list` | 1 |
| `rating_formula` | 1 |
| `rune_system` | 1 |
| `skill_set` | 1 |
| `special_skill_options` | 1 |

TODO.md §4 tracks creating those catalogues; when one lands, remove its
resolved entries from the profiles' `unresolved_references` and update the
59-count here.

> The 15 `spell_list` references were already canonicalized against
> `catalog/campaign/magic.yaml` (45 lore↔wizard assignments, 31 lores with
> 188 spells) — including registering `lore.dark-magic` (the Dark Mage's Dark
> Magic list, *Letters of the Damned* 6), transcribed from its hiring page
> because it was not indexed in the magic section of the site. 0 pending of
> type `spell_list`.

Per-profile detail of the 59 references (as of the hireling ingestion):

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

## Loader contract

`mordheim_knowledge.campaign.load_hirelings(ruleset)` is the authorised read
path: it validates the catalogue (ID uniqueness, declared rules with
cross-file rule references and item resolution) and the campaign catalogues
resolve every `profile_id` against band profiles **and** this pool. Tests:
`tests/knowledge/test_campaign_loaders.py`.
