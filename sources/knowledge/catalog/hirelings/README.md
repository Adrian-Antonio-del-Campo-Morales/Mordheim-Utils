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
tracked per profile in each file's `unresolved_references`; the counts by kind:

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
| other (one each) | 15 |

TODO.md §4 tracks creating those catalogues; when one lands, remove its
resolved entries from the profiles' `unresolved_references` and update the
59-count here. The per-profile detail is in the YAML files themselves —
`unresolved_references` is the authoritative, always-current list.

> The 15 `spell_list` references were already canonicalized against
> `catalog/campaign/magic.yaml` (45 lore↔wizard assignments, 31 lores with
> 188 spells) — including registering `lore.dark-magic` (the Dark Mage's Dark
> Magic list, *Letters of the Damned* 6), transcribed from its hiring page
> because it was not indexed in the magic section of the site. 0 pending of
> type `spell_list`.

## Loader contract

`mordheim_knowledge.campaign.load_hirelings(ruleset)` is the authorised read
path: it validates the catalogue (ID uniqueness, declared rules with
cross-file rule references and item resolution) and the campaign catalogues
resolve every `profile_id` against band profiles **and** this pool. Tests:
`tests/knowledge/test_campaign_loaders.py`.
