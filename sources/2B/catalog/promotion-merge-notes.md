# Promotion merge notes: duplicates consolidated during staging

These provisional definitions were removed from `sources/2B/catalog/items/` because they
duplicate items already defined in the active KB. The 2B band equipment lists now reference
the KB item ids. At promotion, fold the source-specific data below into the KB entries as
additional `source_refs` / notes (do **not** re-create the provisional items).

## `ball_and_chain` → KB `ball_chain` (`catalog/items/weapons-close-combat.yaml`)

Merged-from: Crooked Moon Night Goblins (MIM) + Karak Azgal Night Goblins (KAZ).
`crooked-moon-kep`, `underworld-alliance-mim` and `night-goblins-kaz` now reference
`ball_chain`.

Add at promotion:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 12
  section: Special Equipment / Ball and Chain
  url: https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Crooked Moon Night Goblins.pdf
- manual: broheim.net
  printed_page: 45
  section: Special Equipment / Ball & chain
  url: https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
```

MIM-only rules text worth merging into the KB entry (the KB entry currently has no
`effect` text): *Two-handed, Incredible Blow, Cumbersome, Unwieldy, Random; only a Goblin
who has eaten a Mad Cap mushroom has the strength to wield a Ball & Chain* (full text was
captured in the removed provisional `crooked-moon-gear.yaml`, retrievable from git history
of this file's source: MIM pp. 11–12, 15 gc, Goblins only). Note the KAZ listing is
"rules as Best of Town Crier" while MIM prints full rules — equivalence already reviewed.

## `madcap_mushrooms` → KB `mad_cap_mushrooms` (`catalog/items/combat-equipment.yaml`)

Merged-from: KAZ (p. 45, "rules as Mordheim rulebook", Common, all Night Goblins) and
underworld-alliance-mim (15 gc MIM pricing vs 25 gc KAZ — pricing stays band-side).
`night-goblins-kaz` and `underworld-alliance-mim` now reference `mad_cap_mushrooms`.


Add at promotion:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 45
  section: Special Equipment / Madcap Mushrooms
  url: https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
```

## `belaying_pin` → KB `belaying_pin` (`catalog/items/weapons-close-combat.yaml`)

Merged-from: Channel Rats (MIM p. 178). The provisional added flavour text and the
MIM-printed special rules (`Thrown weapon, +1 Enemy armour save`; the KB entry implements
it as `weapon.mace` with the Town Crier wording "Awkward Thrown Weapon"). The MIM wording
differs slightly from the KB effect — flag for the equivalence review before overwriting.

Add at promotion (as extra source_ref + review note, not as replacement effect):

```yaml
source_refs:
- manual: broheim.net
  printed_page: 178
  section: Strigany Special Equipment / Belaying Pin
  url: https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Channel Rats.pdf
```

Spanish name discrepancy to resolve at translation review: KB uses `Cabilla de Maniobra`,
the MIM source context suggests `Bichero de Amarre` (actually "boat-hook"); keep KB name.

## `poison_daggers` → KB `poison_daggers` (`catalog/items/combat-equipment.yaml`)

Merged-from: Crooked Moon Night Goblins (MIM p. 11): "A pair of daggers coated in Death Cap
mushroom juice; the coating is re-applied for free after every game. Same effect as Black
Lotus." 25 gc, Fanatics only, Common. `crooked-moon-kep` references the KB id.

Add at promotion:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 11
  section: Special Equipment / Poison Daggers
  url: https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Crooked Moon Night Goblins.pdf
```

Note: "same effect as Black Lotus" — the KB entry should cross-reference `black_lotus`.

## `fish_hook_shot` → KB `fish_hook_shot` (KB file: out-of-scope item)

Merged-from: Channel Rats (MIM p. 178). The KB entry carries only the Town Crier wording
(Range 3", S3, Thrown Weapon). The MIM printing adds two special rules the KB entry
lacks: **Precise** (may attack enemies engaged in close combat, useless if the wielder is
himself engaged) and **Caused fall** (instead of damage: roll to hit, then pass a Strength
test for the enemy to count as knocked down; +1 to the Strength test against large
models), plus Rare 7.

At promotion either merge the MIM rules into the KB entry or keep a MIM variant item —
decide in the equivalence review. Full MIM text preserved here:

> Hook shot is a fine rope or chain with a weighted fishing hook or scythe tied to its
> end. River gypsies use the range of this curious barbed weapon to waylay their
> victimizers. Range 3", Strength 3. Special Rules: Thrown weapon (no penalties for range
> or moving), Precise (may attack enemies engaged in close combat, useless if the wielder
> is himself engaged), Caused fall (instead of damage: roll to hit, then pass a Strength
> test for the enemy to count as knocked down; +1 to the Strength test against large
> models). Rare 7.

---

# Promotion merge notes: KB-duplicate items flagged during stub transcription

These notes cover the seven 2B-transcribed items that are **name-form duplicates of active-KB
items** (the sections above cover the five consolidated duplicates found during the item
consolidation pass). Each transcribed entry below lives under `sources/2B/catalog/items/`
with a NOTE in its `effect`; the band equipment lists currently reference the 2B id. At promotion:

1. **Do not promote the 2B item row itself** — the KB entry is the survivor.
2. Fold the listed `source_refs` into the KB entry.
3. Re-point every 2B band `item_id` listed below to the KB id.
4. Apply any marked rules-text or i18n follow-ups in the equivalence/translation review.

At-promotion re-point summary (all inside `sources/2B/bands/mordheim/*/equipment-access.yaml`):

| 2B id (transcribed) | KB id (survivor) | Bands to re-point |
|---|---|---|
| `dueling_pistol` | `duelling_pistol` | bretonnian-buccaneers-sar (×2), estalian-corsairs-sar (×2), ghost-pirates-sar (×2), pirates-of-the-cathayan-sea-sar (×2), sartosan-pirates-sar (×2), slayer-pirates-sar, wasteland-privateers-sar (×2) |
| `horsemans_hammer` (2B def) | `horsemans_hammer` (KB) | knights-of-the-bitter-moors-mim (delete 2B def, keep KB) |
| `throwing_axe_sar` | `throwing_axe` | khorne-raiders-sar, savage-orcs-sar (×2, the Sartosa orc split), slayer-pirates-sar (×2) — these already reference `throwing_axe`; only the 2B def is deleted |
| `throwing_knife` (2B def) | `throwing_knives` | no band references the 2B def (bands already use `throwing_knives`); delete the 2B def |
| `wardog` | `warhound` | watchmen-mim |
| `dragon_cloak` | `sea_dragon_cloak` | dark-elf-corsairs-mou |
| `hunting_arrows` (2B def) | `hunting_arrows` (KB) | bretonnian-brigands-mou, militiant-mootlanders-mim, wood-elves-of-arden-mou — bands already reference the KB id; delete the 2B def |

Non-duplicate transcribed items that simply need their ids kept as-is at promotion (no KB
equivalent exists): `rel_riding_horse` (disciples-of-maldred-mou, ghutani-rel, muzil-rel,
turjuk-rel) and `house_guard_plate_armour` (house-guard-sc, ×2 — see its note about a future
generic plate-armour item below).

---

## `dueling_pistol` → KB `duelling_pistol` (`catalog/items/weapons-ranged.yaml`)

Merged-from: five Sartosa warband lists that spell the weapon "Dueling Pistol" (Bretonnian
special rule: heroes treat the initial 6"/10" as Short range; at warband creation Bretonnians
buy them at 25 gc / 50 brace vs the standard 30 gc / 60 brace). The KB entry is the core
rulebook Duelling Pistol (Range 10", S4, +1 to hit) and already has a mechanic binding and
Spanish name (`Pistola Duelo` — translation review may align it with `Pistola de Duelo`).

Add at promotion (KB entry):

```yaml
source_refs:
- manual: broheim.net
  printed_page: 3
  section: Human Pirates equipment list / Dueling Pistol
  url: https://broheim.net/downloads/warbands/supplement/sartosa/Human%20Pirates.pdf
- manual: broheim.net
  printed_page: 2
  section: Ghost Pirates equipment list / Dueling Pistol
  url: https://broheim.net/downloads/warbands/supplement/sartosa/Ghost%20Pirates.pdf
- manual: broheim.net
  printed_page: 2
  section: Pirates of the Cathayan Sea equipment list / Dueling Pistol
  url: https://broheim.net/downloads/warbands/supplement/sartosa/Pirates%20of%20the%20Cathayan%20Sea.pdf
- manual: broheim.net
  printed_page: 3
  section: Slayer Pirates equipment list / Dueling Pistol
  url: https://broheim.net/downloads/warbands/supplement/sartosa/Slayer%20Pirates.pdf
- manual: broheim.net
  printed_page: 3
  section: Wasteland Privateers equipment list / Dueling Pistol
  url: https://broheim.net/downloads/warbands/supplement/sartosa/Wasteland%20Privateers.pdf
```

Band-side notes to preserve (they carry per-warband pricing): bretonnian-buccaneers-sar
(25/50 for Bret.), slayer-pirates-sar (30/60 brace). The Bretonnian short-range special rule
itself lives in the band's special rules, not in the item.

## `horsemans_hammer` → KB `horsemans_hammer` (`catalog/items/miscellaneous.yaml`)

Merged-from: Knights of the Bitter Moors equipment list (printed as "Horsemens Hammer",
30 GC). The 2B transcription (`lus-mou-remaining.yaml`) carries identical rules text (Close
Combat, S+1, two-handed, +1 armour save vs shooting with shield). The KB entry predates it
(mordheimer.net source).

At promotion: delete the 2B definition in `lus-mou-remaining.yaml`, re-point
`knights-of-the-bitter-moors-mim` (cost 30 stays band-side), and add:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 2
  section: Knights of the Bitter Moors equipment list / Horsemens Hammer
  url: https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Knights%20Of%20The%20Bitter%20Moors.pdf
```

## `throwing_axe_sar` → KB `throwing_axe` (`catalog/items/weapons-ranged.yaml`)

Merged-from: Khorne Raiders ("Throwing Axes", 15 gc) and Slayer Pirates ("Throwing Axe",
15 gc) missile lists. Same item as the KB's core Throwing Axe. The bands already reference
`throwing_axe` — at promotion only delete the 2B definition in `sar-sartosa-gear.yaml` and
add the source refs above to the KB entry (Khorne Raiders p.2, Slayer Pirates p.2).

## `throwing_knife` → KB `throwing_knives` (`catalog/items/weapons-ranged.yaml`)

Merged-from: Woodsmen de Artois ("Throwing Knife", 15 gc). No 2B band references the
singular form (they all already use `throwing_knives`). At promotion delete the 2B
definition in `lus-mou-remaining.yaml` and add:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 3
  section: Woodsmen de Artois Missile Weapons / Throwing Knife
  url: https://broheim.net/downloads/warbands/supplement/mousillon/Woodsmen%20de%20Artois.pdf
```

## `wardog` → KB `warhound` (`catalog/items/out-of-scope.yaml`)

Merged-from: Watchmen equipment list ("Wardog", 25 gc). The KB `warhound` entry already
carries the full wardog rules text ("fights exactly like a member of your warband… counts as
equipment for upkeep"). At promotion delete the 2B definition in
`mim-special-equipment-a.yaml`, re-point `watchmen-mim`, and add:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 3
  section: Watchmen Miscellaneous Equipment / Wardog
  url: https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Watchmen.pdf
```

i18n follow-up: the KB Spanish name `Sabueso de Guerra` is already correct; the 2B
transcription's NOTE text should not be merged verbatim (it contains promotion instructions).

## `dragon_cloak` → KB `sea_dragon_cloak` (`catalog/items/shields-and-defences.yaml`)

Merged-from: Dark Elf Corsairs miscellaneous equipment ("Dragon Cloak", 50 gc). The KB entry
covers the Sea Dragon Cloak concept (the Dark Elf cloak) including the rules ambiguity about
combining with armour/shields. At promotion delete the 2B definition in
`lus-mou-remaining.yaml`, re-point `dark-elf-corsairs-mou`, and add:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 2
  section: Dark Elf Corsairs Miscellaneous Equipment / Dragon Cloak
  url: https://broheim.net/downloads/warbands/supplement/mousillon/Dark%20Elf%20Corsairs.pdf
```

Equivalence review flag: confirm the MOU Dark Elf printing is indeed the same item as the
KB's `sea_dragon_cloak` (source mordheimer.net) before folding — the 2B NOTE assumes yes.

## `hunting_arrows` → KB `hunting_arrows` (`catalog/items/out-of-scope.yaml`)

Merged-from: Militiant Mootlanders missile list ("Hunting arrows", 35 gc). The KB entry
already defines the item (+1 Injury rolls, usable with Short Bow/Bow/Long Bow/Elf Bow) from
the Bretonnian Chapel Guard source. Bands (bretonnian-brigands-mou, militiant-mootlanders-mim,
wood-elves-of-arden-mou) already reference the KB id — at promotion only delete the 2B
definition in `mim-special-equipment-b.yaml` and add:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 2
  section: Militiant Mootlanders Missile Weapons / Hunting arrows
  url: https://broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Militiant%20Mootlanders.pdf
```

## Related non-duplicate keeps (for completeness)

- `rel_riding_horse` — no KB generic Riding Horse exists; keep the 2B item (Disciples of
  Maldred 30 gc, Arabian lists 40 dinars). If a generic mount item is added to the KB later,
  revisit.
- `house_guard_plate_armour` — the KB has **no generic Plate Armour** item (only
  `bronze_breastplate` in trollheim.yaml). Keep as a source-scoped entry for now; flagged as a
  candidate for a future generic `plate_armour` KB item with the House Guard prices (55 gc /
  70 gc Rare 7) folded as source refs.

## New 2B staging catalogs (ingested 2026-09-14)

Three new files close the completeness gaps found in the audit (hired swords/DPs,
runic artefacts, and spell lists that live outside `magic.yaml`):

### `sources/2B/catalog/hirelings/grade-2b.yaml`

Seven Hired Swords / Dramatis Personae introduced by the 2B sources, following the
KB `catalog/hirelings` schema:

| Profile | Status | Available to |
|---|---|---|
| `hireling.hired-sword.black-orc-bodyguard` | full profile (KAZ p. 62) | night-goblins-kaz, savage-orcs-kaz |
| `hireling.dramatis.snorri-nosebiter` | full profile (KAZ pp. 62-63) | adventurers-kaz |
| `hireling.dramatis.aldred-fellblade` | full profile (KAZ pp. 63-64) | adventurers-kaz |
| `hireling.hired-sword.bog-hunter` | full profile (MiM Specialists p. 5) | lords-of-the-marsh-mim |
| `hireling.hired-sword.whaler` | full profile (MiM Specialists p. 3) | lords-of-the-marsh-mim |
| `hireling.hired-sword.strigani-seer-necromancer` | **name-only** + hiring condition | strigoi-kaz |
| `hireling.dramatis.snerik-night-goblin-scout` | **name-only** | night-goblins-kaz, savage-orcs-kaz |

At promotion: full-profile entries merge into `catalog/hirelings/hired-swords/`
and `catalog/hirelings/dramatis-personae/`; name-only entries need their source
stat blocks before they can become hirable profiles. Band availability moves to
`catalog/campaign/hired-swords-and-dramatis.yaml` eligibility, per KB convention.

**Update 2026-09-14 (second pass):**

- **Bog Hunter and Whaler completed** — their stat blocks were published in the
  separate [Mutiny In Marienburg Specialists PDF](https://broheim.net/downloads/hiredswords/mutinyinmarienburg/MiM%20Specialists.pdf)
  (Broheim, `downloads/hiredswords/mutinyinmarienburg/`), not in the Lords of the
  Marsh band PDF. Both profiles are now `normalized` with full characteristics,
  fees, rating, equipment, skill access and rules (Bog Hunter: Unholy Stink,
  Gopher, Fenland Strider; Whaler: Marine Hunter, Hardened, Harpooner,
  Whalebone Carver). Bog Hunter's `beastlash` resolves to the active-KB item of
  the same id (catalog/items/weapons-close-combat.yaml) — no stub needed.
- **Snerik and Strigani Seer Necromancer remain name-only.** Exhaustive search
  (KAZ anthology text incl. all 8 band PDFs, web search, community forums) found
  no published stat blocks for either: the Karak Azgal anthology only ever lists
  them by name in the hire lists. The Strigany Seer row on hexedscenery's hired
  sword compendium (15 gc / 15 gc, KAZ) carries no stats either. These stay
  `normalization_status: name-only` unless the community publishes their profiles.
- **Prayers of Manann ingested** — `sources/2B/catalog/magic-2b.yaml` now carries
  `lore.prayers-of-manann` (6 prayers + 2 Marks of Manann) transcribed from the
  'Miracle Workers' chapter (Werekin, Liber Malefic; accessible copy: scribd
  241727651). The `lore_assignments.unresolved` entry is cleared; the note
  documents the Mariner-Priest profile and the trident (Rarity 7 per Unknowable
  Cargo) for a future hirelings pass. One caveat: the accessible copy of the
  article truncates the Waterwalk prayer mid-sentence ("...as if it were solid
  ground." restored from context; verify against a full copy of the PDF at
  promotion).

### `sources/2B/catalog/items/kaz-runic-artefacts.yaml`

The six Karak Azgal runic artefacts (p. 70-71) as unique items
(`unique: true`; none can appear more than once per campaign): Builder's Boots,
Sword of Snorri Elfbane, Att'la's Plate Mail, Ulthar's Bow of Seeking, Redbeard's
Belt of Rage, The Eye of Izril. All are `combat_status: out_of_scope` until the
magic-item runtime lands; found only via the KAZ exploration chart.

### `sources/2B/catalog/magic-2b.yaml`

Transitional magic catalog for the three spell lists introduced by 2B PDFs:

- `lore.songs-of-sorrow` (6 spells, ghost-pirates-sar)
- `lore.wood-elven-spells` (6 spells, wood-elves-of-arden-mou)
- `lore.lothern-sea-spells` — VARIANT of KB `lore.spells-of-the-djedhi`:
  inherits spells 1-3 and 5-6, replaces `spell.spells-of-the-djedhi.fleeting-shadows`
  with **Mistress of the Deep** (D8, summons the Oceanid).

It also records `lore_assignments` for every 2B spellcaster (existing lores vs
new lores). The Prayers of Manann (shallows-beasts-mim Mutant-Priest) were
completed in the second pass from the external 'Miracle Workers' chapter; the
unresolved map is now empty.

### `sources/2B/catalog/hirelings/miracle-workers-priests.yaml` (third pass)

`hireling.priest.mariner-priest-of-manann` — full priest profile from the
Miracle Workers chapter: 4/3/3/3/3/1/3/1/8, 12 starting experience, 40 gc hire,
ceremonial dagger + trident choice (trident resolves to the KB item in
catalog/items/miscellaneous.yaml), Combat/Academic/Speed skill access, prayer
access via `lore.prayers-of-manann`, rules for Seafaring, Navigator, Marks of
Manann and the chapter's Hero-slot errata (author ruling: a Priest replaces a
starting Hero). At promotion, decide whether `kind: priest` needs its own
hirelings subcatalog or maps onto `kind: hired-sword` with a hero-slot flag.

Beastlash: the Bog Hunter's `beastlash` equipment reference resolves to the
active-KB item (catalog/items/weapons-close-combat.yaml) — no stub required;
the `missing-item-stubs.yaml` file remains empty.

### All nine Miracle Workers priests (fourth pass)

`miracle-workers-priests.yaml` now carries the complete chapter roster as
`kind: priest` profiles (all `normalized`, 12 starting experience, Hero-slot
errata rule inherited from the Mariner-Priest pattern):

| Profile | Hire | Characteristics | Skill access | Prayers |
|---|---|---|---|---|
| Mariner-Priest of Manann | 40 gc | 4/3/3/3/3/1/3/1/8 | Combat/Academic/Speed | lore.prayers-of-manann |
| Priest of Morr | 35 gc | 4/3/3/3/3/1/3/1/8 | Academic/Speed | lore.prayers-of-morr |
| War-Priestess of Myrmidia | 40 gc | 4/3/2/3/3/1/4/1/8 | Combat/Academic/Strength | lore.prayers-of-myrmidia |
| Trickster-Priest of Ranald | 55 gc | 4/2/3/3/3/1/3/1/7 | Academic/Speed (+Haggle/Streetwise) | lore.prayers-of-ranald-and-handrich |
| Priestess of Shallya | 50 gc | 4/2/2/2/3/1/3/1/8 | Academic | lore.prayers-of-shallya |
| Warrior-Priest of Sigmar | 40 gc | 4/3/3/3/3/1/3/1/8 | Combat/Academic/Strength | lore.prayers-of-sigmar (KB rulebook list) |
| Druid-Priest of Taal | 45 gc | 4/2/3/3/3/1/3/1/7 | Combat/Academic/Strength/Speed | lore.prayers-of-taal |
| Wolf-Priest of Ulric | 60 gc | 4/3/2/3/3/1/3/1/8 | Combat/Academic/Strength/Speed | lore.prayers-of-ulric-miracle-workers (MW variant) |
| Priest of Verena | 45 gc | 4/3/2/3/3/1/3/1/8 | Academic (+Solkan variant: Strength) | lore.prayers-of-verena-and-solkan |

Each includes its strictures, special rules and Marks (Morr Augur/Haunted Mien,
Myrmidia Oracle/Eagle Friend, Ranald's Luck/Cat Friend, Shallya Healing
Hands/Tranquil Aura, Sigmar Enlightened/Symbol of Unity, Taal Tranquil
Fauna/Enlivened Flora, Ulric Son of Ulric/Wolf Friend incl. the Wolf Friend
profile, Verena Librarian/Owl Friend + Solkan Witch-finder/Inquisitor), with
Spanish translations.

Open items at promotion:

1. **Prayer lores — RESOLVED (2026-09-14, final pass)**: the full Miracle
   Workers PDF (18 pp., recovered from the author's Google Drive mirror linked
   on Liber Malefic) is cached at `build/cache/2b-pdfs/extra/Miracle
   Workers.pdf` and all seven remaining lists are now ingested into
   `magic-2b.yaml`: `lore.prayers-of-morr`, `lore.prayers-of-myrmidia`,
   `lore.prayers-of-ranald-and-handrich`, `lore.prayers-of-shallya`,
   `lore.prayers-of-taal-and-rhya` (documented MIRROR of the KB
   `lore.prayers-of-taal` — identical six spells and difficulties; map to the
   existing lore instead of duplicating), `lore.prayers-of-ulric-miracle-workers`
   (VARIANT of the KB `lore.prayers-of-ulric`: the chapter rewrites the
   Wolf-Priest prayers completely, zero spell overlap — keep both lores at
   promotion) and `lore.prayers-of-verena-and-solkan`. Every spell carries EN+ES
   text. The Wolf-Priest's `lore_assignments` now points to the MW variant id.
   Bonus repair: the truncated Waterwalk tail recovered from the full PDF
   ("The effects of this prayer last until the Priest returns to any solid
   platform.") — EN and ES both updated in `lore.prayers-of-manann`.
2. **Chapter special weapons**: Morr's scythe (As user +1, Difficult to use,
   Two-handed — the KB `scythe` item in trollheim.yaml has different stats) and
   the trident (see the PROMOTION NOTE added to the KB `trident` item in
   catalog/items/miscellaneous.yaml: chapter wording is "Strike first, Parry"
   vs the trading post's "Parry" only; 15 gc matches, Rarity 7 already applied).
3. **Dangling item refs — RESOLVED (2026-09-14, final pass)**: `wolf_pelt_cloak`
   (Wolf-Priest's white wolf pelt, 6+ save) is now defined in the staging
   catalog (`items/miracle-workers-gear.yaml`, EN+ES, strictures wording from
   MW p. 9). Not equivalent to the KB `wolfcloak` (+1 saves vs shooting,
   Middenheim hunt item): keep both and review any merge at promotion.
   Stiletto remains rendered as `sword` per the chapter's own equivalence
   (KB has only a mechanic, no item).
4. **`kind: priest`** needs a decision at promotion: own hirelings subcatalog or
   mapped onto `hired-sword` with a hero-slot flag.

# Final completeness sweep (2026-09-14, pre-promotion audit)

Sweep of all 60 extracted band texts plus the external-source PDFs against the
staging tree. Baseline validators green: `ingest_2b.py validate` 60 rows / 0
problems; `audit_2b.py` problem_count 0 (9 informational OCR notes); band i18n
1347 names + 900 effects, 0 missing ES.

## NEW GAP FOUND — REL anthology hirelings — RESOLVED (2026-09-14, hirelings pass)

All three are now ingested in `catalog/hirelings/rel-relics-hirelings.yaml`
(full stat blocks, rules, ES translations, source refs to the REL anthology
PDF). **RESOLUTIONS (2026-09-14, dangling-refs pass)**: (a) the profiles are
priced in **dinars** (Araby campaign currency) — kept with the currency note
on each `hire_fee`; (b) the REL-specific items `angel_wings`, `stickfire`,
`vermin_pot` are now defined in `catalog/items/hireling-gear.yaml` (EN+ES,
source-faithful: angel_wings carries the glide mechanics from the profile
rule; stickfire/vermin_pot state that the source prints no mechanics) —
`rel-relics-hirelings.yaml` points at them and there are NO dangling refs left
anywhere in the hirelings catalogs; (c) Crimashin's gromril dagger is resolved
as base `dagger` + the KB `gromril_weapon` material upgrade (extra -1 armour
save, 4x price) — the source offers no separate item; (d) the Holy Man's
"Holy" skill list has no printed contents anywhere in the anthology — resolved
as Strength access + the True Believer rule (Divine Intervention == the KB
`lore.prayers-of-sigmar`, which carries the actual powers), with an in-file
comment routing the Holy list to `lore.prayers-of-sigmar` at promotion.

## NEW GAP FOUND — MiM Specialists not referenced by any band PDF — RESOLVED (2026-09-14, hirelings pass)

All 10 remaining specialists are now ingested in
`catalog/hirelings/mim-specialists.yaml` (Ogre Treasure-Hunter, Grave Warden,
Halfling Fence, Halfling Pimp, Albino Stormvermin, Norse Bearman Bodyguard,
Fire-Eater, Sister of Sigmar, Midshipman — plus Bog Hunter and Whaler already
in grade-2b.yaml, the PDF's roster is now complete). **RESOLUTIONS
(2026-09-14, dangling-refs pass)**: (a) MiM-specific items `diving_bell_helmet`,
`shovel`, `fire_stick`, `arcane_candelabrum` are now defined in
`catalog/items/hireling-gear.yaml` (EN+ES, source-faithful: fire_stick carries
the breath-attack mechanics from the Fire-Eater rule; arcane_candelabrum the
holy-relic/lantern equivalence from Candle Tree; shovel "counts as an axe";
diving_bell_helmet explicitly flavour-only) — the MiM file points at them;
(b) the Bearman's wolf cloak is NOT the KB `wolfcloak`: the source grants it
no effect, so a new effect-free `wolf_cloak` item was defined in
`hireling-gear.yaml` (reusing wolfcloak would have injected rules the source
does not have; it is also distinct from the MW White Wolf Pelt Cloak 6+ save);
(c) the Albino Stormvermin is priced in **warp tokens** (Skaven currency) —
kept with the currency note on its `hire_fee`. Additionally, the two
pre-existing dangling refs in `grade-2b.yaml` were fixed: the Black Orc
Bodyguard's `double_handed_weapon` and Aldred Fellblade's
`double_handed_sword` now resolve to the KB `two_handed_weapon` item.

## Verified as covered (no action)

- **MW priest equipment-list items**: holy tome (120 gc) and holy relic (25 gc)
  exist in the KB (Sisters of Sigmar / Bretonnian catalogs); blessed water
  (20 gc) exists in `catalog/items/out-of-scope.yaml`.
- **KAZ runic artefacts**: all 6 ingested (`items/kaz-runic-artefacts.yaml`).
- **New spell/prayer lores**: all 4 in-source lists + all 9 MW lists ingested
  (11 lores / 61 spells in `magic-2b.yaml`, 0 unresolved assignments).
- **Band-scoped items**: 96 staged items; 0 dangling item_id references.
- **KAZ exploration chart, scenarios, anthology narrative**: out of scope for
  the band catalog (campaign content) — previously agreed exclusion.
- **Marienburg Annual** (107 pp.): contains the MiM band rules (already
  ingested from the individual band PDFs) plus project meta, vehicles,
  Chaos-theme optional rules and campaign narrative — out of scope for the
  Grade-2b band catalog; flagged here for a future 'MiM extras' pass if ever
  wanted.
