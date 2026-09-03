# CAMPAIGN INGESTION

## Hired Swords & Dramatis Personae

Este documento resume el estado final de la ingestión de **Hired Swords** y **Dramatis Personae**, las decisiones de modelado tomadas durante el proceso y los trabajos pendientes para integrar esta parte en la KB compartida.

> Este archivo es documentación de ingestión. No forma parte del modelo ejecutable de reglas.

## Estado

- **Perfiles identificados:** 102
- **Hired Swords:** 72
- **Dramatis Personae:** 30
- **Perfiles normalizados dentro de scope:** 98
- **Perfiles deliberadamente out of scope:** 4
- **Entradas de contratación de campaña:** 98
- **Elegibilidad modelada:** 98/98
- **Reglas dinámicas/condicionales que debe evaluar la aplicación:** 18
- **KB compartida original modificada:** Sí — catálogo v2 integrado y publicado, perfiles/grupos ya viven en `sources/knowledge`

La ingestión funcional de Hired Swords y Dramatis Personae se considera **completa**. La **integración en la KB compartida de Mordheim-Utils está hecha**:
`sources/knowledge/catalog/campaign/hired-swords-and-dramatis.yaml` está en schema v2 con `status: published`, sus 98 entradas resuelven contra `catalog/hirelings/**` y `registry/warband-groups.yaml`, y los invariantes quedan cubiertos en `tests/knowledge/test_campaign_catalogs.py` (sección Mercenarios). Los TODOs 2-5 siguientes son trabajo de cargadores/runtime de las aplicaciones, fuera del alcance de datos de la KB.

## Qué información vive en cada parte de la KB

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

## Convenciones de IDs

- **hired sword profile:** `hireling.hired-sword.<slug>`
- **dramatis profile:** `hireling.dramatis.<slug>`
- **warband group:** `warband-group.<slug>`

## Decisiones e invariantes de modelado

- Do not reuse a band profile as a hireling profile merely because names match.
- Existing canonical item_id values are referenced; item definitions are not duplicated.
- Existing canonical skill IDs are referenced only when equivalence is explicit.
- Source-only or unresolved concepts are never assigned guessed canonical IDs.
- Campaign-resolved rolls, choices and rewards remain outside the KB.
- Current-roster and selected-warband-variant eligibility checks live as hireling rules and are evaluated by the application.

## Decisiones específicas tomadas durante la ingestión

- **hireling.hired-sword.goblin-lantern-bearer** — May be hired by any warband.
- Dynamic roster-dependent restrictions are modelled at hireling rule level and checked by the application.
- Chaos/followers-of-Chaos/devoted-to-Chaos hireling restrictions use warband-group.chaotic.
- Halfling Thief uses warband-group.elf rather than a Wood-Elf-only group.

## Trabajo deliberadamente fuera de scope

Estos cuatro Dramatis no bloquean el cierre de la ingestión:

- **`hireling.dramatis.ulli-and-marquand`** — Composite entry with two independent warrior profiles.
- **`hireling.dramatis.belandysh-condemned-champion-of-chen`** — Random characteristics plus random-characteristic mount.
- **`hireling.dramatis.luthor-wolfenbaum`** — Single identity with multiple selectable personas/loadouts.
- **`hireling.dramatis.the-headless-horseman`** — Composite rider-and-steed entity with separate profiles.

# TODO

## Necesario antes de integrar en la KB compartida

### 1. hirelings.integration.schema-v2 — COMPLETADO

**Objetivo:** `catalog/campaign/hired-swords-and-dramatis.yaml`

Schema_version 2 integrado en la KB compartida (`status: published`), con invariantes en `tests/knowledge/test_campaign_catalogs.py`.

Incluye:
- hiring_fee/upkeep resource structures instead of hiring_fee_gc/upkeep_gc
- availability_procedures and special availability kinds
- eligibility simple lists
- eligibility boolean expression with all_of/any_of/not

> Pendiente solo en las aplicaciones: actualizar los consumidores que esperan schema_version 1 (cargadores/runtime), nunca en la KB de datos.

### 2. hirelings.integration.profile-resolution

**Objetivo:** `shared loaders/validators`

Resolve profile_id references against catalog/hirelings/** as well as existing band profile locations.

### 3. hirelings.integration.warband-groups

**Objetivo:** `shared loaders/validators and campaign evaluator`

Load registry/warband-groups.yaml and resolve warband-group.* references used by eligibility.

### 4. hirelings.integration.application-rules

**Objetivo:** `campaign/warband-building application`

Implement the 18 campaign-eligibility rule IDs that depend on current roster composition, current hirelings, selected Mercenary variant, or a conditional acceptance roll. Do not infer these from static warband groups.

Reglas a implementar en la aplicación (18):
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

**Objetivo:** `campaign resource handling`

Confirm/port canonical handling for every resource used by hireling costs, especially treasures and campaign_points.

Recursos afectados:
- `gold_crowns`
- `wyrdstone_fragments`
- `treasures`
- `campaign_points`

### 6. campaign.runtime-loaders — PENDIENTE (no iniciado)

**Objetivo:** `mordheim_knowledge` (runtime de aplicaciones; fuera del alcance de datos)

Implementar los loaders de campaña pedidos en el siguiente milestone, **sin tocar la KB**
ni el motor vectorizado:
- `load_campaign_catalog(...)` — cargar los catálogos de `catalog/campaign/**`
  (scenarios, post-battle-sequence, experience-and-advances, serious-injuries,
  trading-post, magic, mutations, hired-swords-and-dramatis, …) validando
  `schema_version`, unicidad de IDs por documento y resolución de referencias
  (item_ids, profile_ids, lore_ids, band_ids, warband-group.*).
- `load_post_battle_sequence(...)` — cargador específico del catálogo
  `post-battle-sequence.yaml` con la misma validación.
- Empezar por un caso de uso que reciba estado de campaña (roster + resultados de
  partida) y consuma los catálogos cargados; el contrato de carga debe ser reutilizable
  por `mordheim_campaign.application.knowledge_port`.

## Seguimiento de KB no bloqueante para la contratación

### 1. hirelings.groups.good-aligned — COMPLETADO

**Objetivo:** `registry/warband-groups.yaml`

Auditoría de pertenencia de `warband-group.good-aligned` completada y `status: partial`
eliminado (**40 bandas**). No contradice a `warband-group.evil` ni a `warband-group.chaotic`.

**Método (banda a banda contra mordheimer.net):** las páginas de warband del sitio no
publican una etiqueta de alineamiento; la clasificación se apoya en (a) los textos
oficiales de disponibilidad de Hired Swords (paridad expresa de acceso con las bandas
Human Mercenary, acceso sin restricción a espadas de contrato de alineamiento bueno,
o listas de exclusión cortas que las dejan disponibles) y (b) la pertenencia a
razas/órdenes canónicamente buenas (Enanos, Altos Elfos, Medios, órdenes de Sigmar,
caballeros bretonianos, instituciones imperiales), cuando la banda no pertenece a los
grupos evil/chaotic del propio registro.

**Añadidas en la auditoría (14):**
- `hochland-bandits`, `kislevites`, `merchant-caravans`, `pirates`, `lustria-pirates` —
  la página declara acceso a Hired Swords idéntico al de una banda Human Mercenary
  (pirates: «same access to Hired Swords & any other items as for a regular human
  Mercenary Warband»).
- `imperial-outriders` — solo espadas montadas, incluida la Roadwarden (de contrato bueno).
- `outlaws-of-stirwood-forest` — únicamente 4 exclusiones (Bounty Hunter, Wolf-Priest of
  Ulric, Norse Shaman, Dark Elf Assassin); el resto de espadas, incluidas las de contrato
  bueno, queda disponible.
- `bretonnian-knights`, `bretonnian-chapel-guard`, `chaos-streets-bretonnian-knights` —
  orden caballeresca bretoniana (Chivalry, Holy Water, sin venenos/drogas).
- `chaos-streets-sigmar-protectorate` — espejo de `warband-group.sigmar-devoted`
  (Sisters of Sigmar y Witch Hunters ya estaban incluidas).
- `lustria-high-elves` — espejo de `warband-group.high-elf` (Shadow Warriors y Sons of
  Nagarythe ya estaban incluidos).
- `mootlanders` — raza media, sin declaración contraria en la página (convención de raza).
- `gunnery-school-of-nuln` — institución estatal imperial; la página no publica sección de
  Hired Swords (inferencia documentada).

**Dudas residuales (bandas sin declaración en la fuente, tratadas como no-buenas/
neutrales y, por tanto, NO incluidas):** `horned-hunters`, `lustrian-reavers`,
`khemri-mages`, `khemri-thieves-guild`, `chaos-streets-arcane-society`,
`chaos-streets-deathbringers`, `chaos-streets-mordheim-inhabitants`, `lustria-pygmies`,
y las bandas orcas/goblins (`black-orcs`, `orc-mob`, `forest-goblins`, `night-goblins-*`,
`lustria-savage-goblins`, `khemri-hobgoblin-raiders`, `chaos-streets-greenskins`), que el
canon de contratación excluye expresamente («Orcs & Goblins»). Si una fuente futura las
clasifica, la auditoría debe repetirse solo para esas bandas.

### 2. hirelings.profile-dependencies

**Objetivo:** `catalog items/skills/magic/companions and related rule catalogs`

Canonicalize the remaining intrinsic profile references below when the corresponding shared KB schemas/catalogs exist. These do not prevent hiring/cost/eligibility from being represented.

Hay **59 referencias intrínsecas pendientes**:
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

> **Actualización (enlace con magic.yaml):** las 15 referencias `spell_list`
> de los perfiles de hired swords y dramatis personae quedaron enlazadas con
> los `lore_id` canónicos de `catalog/campaign/magic.yaml` (45 asignaciones
> lore↔mago y 31 lores con 188 conjuros; `pending_lores` vacío). Se eliminaron
> de `unresolved_references` de los perfiles (0 pendientes de tipo
> `spell_list`). Incluye el alta del lore canónico `lore.dark-magic` (lista
> Dark Magic del Dark Mage, Letters of the Damned 6), transcrito desde su
> página de contratación al no estar indexado en la sección de magia del sitio.

<details>
<summary>Ver referencias pendientes una por una</summary>

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

# Validación del paquete

**Alcance:** structural/internal consistency of the final generated package

## Comprobaciones

- ✅ all yaml parses
- ✅ yaml only package
- ✅ campaign profile ids resolve
- ✅ static group references resolve
- ✅ static band references resolve against supplied kb
- ✅ boolean eligibility grammar valid
- ✅ goblin lantern bearer unrestricted
- ✅ good aligned group still marked partial

## Conteos

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

## Baseline final

Los archivos funcionales que forman esta entrega son:

- `catalog/hirelings/hired-swords/*.yaml`
- `catalog/hirelings/dramatis-personae/*.yaml`
- `catalog/campaign/hired-swords-and-dramatis.yaml`
- `registry/warband-groups.yaml`

Este documento (`CAMPAIGN INGESTION.md`) es únicamente la documentación de ingestión e integración.
