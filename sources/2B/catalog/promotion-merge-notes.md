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

## KAZ Savage Orc pets → KB `war_boar`, `giant_wolf`, `giant_spider` (`catalog/items/miscellaneous.yaml`)

The three Karak Azgal pets are listed in `savage-orcs-kaz` (`savage-orc-pet-list`) and reference
the KB ids, which today carry only an `out-of-scope` stub. The KB entries need the printed data
(found in the fidelity pass of 2026-09-21; source `Karak Azgal.pdf` page 60, section `Pet`):

```yaml
source_refs:
- manual: broheim.net
  printed_page: 60
  section: Pet / War Boar
  url: https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
effect: >-
  Profile M 7, WS 3, BS 0, S 3, T 4, W 1, I 3, A 1, Ld 3. Cost: 90 GCs, Availability: Rare 11.
  Large, ferocious and bad-tempered — a perfect mount for an Orc Warlord. Ferocious Charge: Orc war
  boars attack with +2S when charging, due to their bulk; this applies only to the boar, not the
  rider. Thick Skinned: the thick skin and matted fur of the boar makes him very hard to wound;
  boars confer an additional +1 bonus to the rider's armour save (making +2 total).
```

```yaml
source_refs:
- manual: broheim.net
  printed_page: 60
  section: Pet / Giant Wolf
  url: https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
effect: >-
  Profile M 9, WS 3, BS 0, S 3, T 3, W 1, I 4, A 1, Ld 4. Cost: 40 GCs, Availability: Rare 10.
  Orcs cannot ride a Giant Wolf — they are far too massive. Giant Wolves cannot be used in a
  warband that already contains Giant Spiders.
```

```yaml
source_refs:
- manual: broheim.net
  printed_page: 60
  section: Pet / Giant Spider
  url: https://broheim.net/downloads/campaigns/karakazgal/Karak Azgal.pdf
effect: >-
  Profile M 7, WS 3, BS 0, S 3(4), T 3, W 1, I 4, A 1, Ld 4. Cost: 50 GCs, Availability: Rare 11.
  Poisoned Attack: Giant Spider attacks are poisoned — attacks are considered as strength 4, but
  this will not modify any armour saves. Wall Walk: Giant Spiders may walk up and down walls
  without making Initiative tests; they may only jump up to 2" across or down, but this does count
  as a diving charge. Orcs cannot ride a Giant Spider, and Giant Spiders cannot be used in a
  warband that already contains Giant Wolves.
```

The `Pet` rule itself (personal property, does not count towards the warband's treasure or maximum
number of warriors, lost if the hero dies) is modelled as `savage-orcs-kaz` rule `band--pet`.

## `bolas` → KB `bolas` (`catalog/items/out-of-scope.yaml`)

The Lustria Lizardmen list prints the bolas' full entry; the KB entry carries only
`Range: 16" Strength: Special Dangerous`. Add the missing printed rule at promotion:

```yaml
source_refs:
- manual: broheim.net
  printed_page: 2
  section: Special Lizardmen Equipment / Bolas
  url: https://broheim.net/downloads/warbands/supplement/lustria/Lizardmen.pdf
effect: >-
  Range: 16" Strength: Special, 5 gc, Common, Lizardmen only. The bolas can only be used once per
  battle and are automatically recovered after each battle. Dangerous: if the to hit roll is a
  natural 1, the bolas brain the wielder with a Strength 3 hit. Entangle: a model hit by bolas
  isn't hurt, but his legs are entangled and he is unable to move. The model suffers a -2 Weapon
  Skill penalty in hand-to-hand combat, but may still shoot normally. The model may try to free
  himself in the Recovery phase; if the model rolls a 4+ on a D6 he is freed and may move and
  fight normally.
```

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

---

# T04 decisions: catalog identities and provenance (2026-09-25)

Recorded by T04 on branch `2A2B` @ `b2e437c`. Scope audited: **109 staged items**, **109
market entries**, **11 lores**, **28 hireling profiles**, **26 campaign hireling entries**,
61 packages. The full per-record origin -> destination map is
`build/cache/2ab-promotion-map.json` (generated by `build/cache/2ab-t04-map.py`); the
commands and exit codes live in the T04 delivery appended to
`docs/knowledge/2a2b/tasks/T04.md`.

Everything in the sections above stands: T04 did not reopen a demonstrated decision. What
follows is the decision for every record the sections above did not already cover, plus two
cases T04 found beyond them.

## A. Items

### A.1 New entries (105 of 109)

An all-`new` entry needs no further decision: the id is absent from the active KB, so the
entry is promoted as-is with its printed text and source_refs intact. Two of the 105 carry a
**parent relationship** rather than a collision and must not duplicate the parent's rules:

- `swivel_gun_ball_shot`, `swivel_gun_chain_shot`, `swivel_gun_grape_shot` are the three
  printed **loads** of the KB `swivel_gun` (Town Crier 'Pirate Warband'); the parent weapon
  keeps its own entry and its own rules, the loads keep their printed price and effect text.
- `harpoon` (printed as "Harpoon (Javelin)" in the Khorne Raiders and Slayer Pirates missile
  lists) is its own entry: the source prints it as a named row and adds "thrown weapon rules
  apply", which is the KB `javelin` mechanic. No merge: the printed rows are different items.

Identity-sensitive new entries that were checked against the KB and **kept separate**:
`mage_staff_of_hoeth` (Ithilmar, Loremaster only, as user / as user +1, one or two-handed)
vs KB `mage_staff` (balanced quarter staff, +1 Initiative, Lustria High Elf list);
`mark_of_the_old_ones` (Lizardman mark, once per battle) vs KB `claw_of_the_old_ones` (a
weapon); `greenwood_scythe` vs KB `scythe` (already declared above); `house_guard_plate_armour`
vs the KB — **re-verified: the KB still has no generic Plate Armour item** (`grep -rn
"plate_armour\|Plate Armour" sources/knowledge/catalog/items/` returns nothing), so the entry
stays with the House Guard price; `rel_riding_horse` vs the KB — the KB has no generic Riding
Horse item either, so it stays with its two currencies (30 gc Disciples of Maldred, 40 dinars
Arabian lists); `wolf_pelt_cloak` vs KB `wolfcloak` (keep both, as decided above).

### A.2 Merges already documented above — unchanged (2)

`horsemans_hammer` (2B def deleted, KB entry survives, LUS/MOU source_ref added) and
`hunting_arrows` (2B def deleted, KB entry survives, Militiant Mootlanders source_ref added).
Both carry identical names and rules to the KB entry, which is why they merge rather than
become variants.

### A.3 Re-points already documented above — unchanged (5)

`dueling_pistol` -> KB `duelling_pistol` (7 band lists), `throwing_axe_sar` -> KB
`throwing_axe`, `throwing_knife` -> KB `throwing_knives`, `wardog` -> KB `warhound`,
`dragon_cloak` -> KB `sea_dragon_cloak`. In each case the 2B definition is deleted and the
KB entry gains the listed source_ref; band-side prices stay in the band list.

### A.4 NEW merge-redirect: `elven_bow` -> KB `elf_bow` (found by T04)

Not in the sections above. `sources/2B/catalog/items/lus-mou-remaining.yaml` defines
`elven_bow` ("Elven Bow", 35 gc) with an effect that hedges ("No separate special-rules
paragraph is printed beyond the list entries (treat as a long bow unless the review pass
finds otherwise)"). The evidence for identity:

- The High Elves (LUS) printed list prices the three bows as **Bow 10 gc / Long Bow 15 gc /
  Elven Bow 35 gc** — exactly the KB trading-post prices for `bow`, `long_bow` and
  `elf_bow`; and the KB `elf-bow` market entry is 35 gc, Rare 12.
- Every other 2B band that prints the item already references the KB id `elf_bow`
  (`adventurers-kaz`, `lothern-sea-patrol-sar`, `sea-ghosts-mim`, `wood-elves-of-arden-mou`
  x2). Only `high-elves-lus` uses the staging id, in two rows.

At promotion: delete the 2B definition, re-point `high-elves-lus` `hero-equipment-list` and
`cadets-equipment-list` (keeping the `Ranger only` note on the second row), and add the LUS
source_ref to the KB `elf_bow` entry. The KB entry's rules stay: the printed row carries no
rules of its own, so the KB text is the only rules text and there is nothing to reconcile.

### A.5 NEW merge-redirect: `rope_and_hook` -> KB `rope_hook` (found by T04)

`sources/2B/catalog/items/channel-rats-equipment.yaml` defines `rope_and_hook` ("Rope &
Hook", Channel Rats p. 177): "Standard climbing gear of river folk ... Standard equipment for
climbing as detailed in the Mordheim rulebook." The KB `rope_hook` ("Rope Hook",
`out-of-scope.yaml`, mordheimer Lustrian Reavers) carries the same item with the printed
benefit the source defers to the rulebook: "may re-roll failed Initiative tests when climbing
up and down." Same object, same function, same absence of a separate combat rule; the MIM
text names no other effect, so it does not contradict the KB text.

At promotion: add the Channel Rats source_ref to the KB `rope_hook`, re-point
`channel-rats-mim`, and delete the staging definition. If the equivalence review prefers the
stricter reading (the MIM row prints no benefit at all), the fallback is to keep the staging
row as a source-scoped variant — the printed wording is preserved either way in this note.

### A.6 Variant kept: `wolf_cloak`

As already decided above: the Norse Bearman Bodyguard's cloak is granted no effect by the
source, so it is not the KB `wolfcloak` (Middenheim hunt, +1 save against shooting). Keep
both; do not fold the staging effect text into the KB entry.

### A.7 KB-side items referenced by 2B bands — T03's `item-name-missing` / `item-outside-list`

These rows reference an **existing KB item**; the issue was the printed word, not a catalog
entry. Decision for each, with the printed evidence read from the cached sources:

| Finding | Band / list | What the source prints | Decision |
|---|---|---|---|
| `item-name-missing` x3 | `adventurers-kaz`: Elf, Dwarf and Cannon Fodder lists | **"Club, Mace or Hammer 3 gc"** (Karak Azgal p. 20) | **Re-point** `staff_club_mace` -> KB `mace_hammer`. The KB `mace_hammer` is the 3 gc common grouping (its market id is literally `campaign.trading-post.club-mace-or-hammer`), while `staff_club_mace` is `not_sold` ("Staff, Club or Mace", Outlaws only). Keep the band-side `notes: Club, Mace or Hammer.` |
| `item-name-missing` x1 | `lords-of-the-marsh-mim` Heroes Equipment List | "Mace/Staff .... 3 gc" | Keep KB `mace_hammer` (the same 3 gc grouping); the row already carries `notes: Mace/Staff`. The henchmen list prints "Mace 3 gc" and correctly references `mace`. |
| `item-name-missing` x1 | `watchmen-mim` Private Sleuth Equipment List | "Mace/Staff .... 3 gc" | Keep KB `mace_hammer`; the row already carries `notes: Mace/Staff`. |
| `item-name-missing` x2 | `underworld-alliance-mim`: Greenskin and Skaven lists | "Throwing stars* ... 15 gc" | **Re-point** `throwing_knives` -> KB `throwing_stars`, keeping the note verbatim. The KB keeps `throwing_stars` and `throwing_knives` as two ids with the same rule text, and the printed word is decisive; the tree's own practice agrees (`skaven-of-clan-mors-kaz` and `-skryre-kaz` already reference `throwing_stars` in their hero lists). |
| `item-name-missing` x1 | `militiant-mootlanders-mim` Heroes Equipment List | "Kitchenware (counts as throwing stars) ... 15 gc" | **Re-point** `throwing_knives` -> KB `throwing_stars`, keeping the printed wording note verbatim. |
| `item-outside-list` x2 | `dwarf-guildsmen-kaz`: Thunderers (handgun) and Dwarf Warriors (gromril_armour) lists | The document prints **"DWARF EQUIPMENT LISTS / All of the equipment lists from Town Crier 6 (or Best of Town Crier) apply"** (Karak Azgal p. 26 ff.); "Handguns" and "Gromril armour" appear only in the exploration/mausoleum tables | **Keep, declared.** Both rows are inherited-list entries; `printed_wordings.DELEGATED_LISTS` already records the Thunderers list with that reason. Prices stay band-side (handgun 35 gc, gromril armour 75 gc). |
| `item-outside-list` x1 | `dwarf-slayers-kaz`: Dwarf Warriors list (gromril_armour) | "The Dwarf Warrior equipment lists from Town Cryer 6 (or Best of Town Crier) apply" | **Keep, declared** — same inherited list. Price 75 gc stays band-side; the row already carries the "Slayers may never take armour" note. |
| `item-outside-list` x2 | `skaven-of-clan-mors-kaz` / `-skryre-kaz`: Skaven Heroes list (fighting_claws) | "KAZ prints no Skaven list: 'All of the equipment lists from the rulebook apply'" (`DELEGATED_LISTS`); the document's prose reads "Tunnel Runners are equipped with Digging Claws **(counts as Fighting Claws for all purposes)**" | **Keep, declared.** The reference is supported by the printed alias, and the 35 gc row matches the rulebook's Fighting Claws entry. |

### A.8 Defect declared (not fixed in T04)

`harpoon` (`sar-sartosa-gear.yaml`) is `kind: close-combat-weapon` but is printed in the
**Missile Weapons** section of the Khorne Raiders and Slayer Pirates lists, and its own effect
text says it is "usable as a thrown javelin". The KB enum has `ranged-weapon`, so the kind is
wrong. Changing an item's kind is a reclassification, and `staging_promotion.ITEM_KINDS` is
the declared place for it, so T04 records the defect and hands it to T05 rather than editing
the item.

### A.9 KB-side consolidation notes for T07 (not a T04 decision)

The KB itself holds duplicate ids for two printed concepts. T04 records them so the merge
step does not mistake them for staged collisions:

- `familiar` (khemri) and `arcane_familiar` (chaos-in-the-streets p. 167) carry parallel
text for the same ritual familiar.
- `throwing_axe` ("Throwing Axe", Bandit equipment list) and
  `throwing_axes_same_as_throwing_knives` ("Throwing Axes Same as Throwing Knives", Norse /
  Marauders of Chaos lists) are the same printed rule under two ids; `throwing_axe` is the
  survivor the 2B re-point targets because it matches the printed name.

## B. Magic

### B.1 `lore.prayers-of-taal-and-rhya` is **NOT** a mirror — keep it (T04 ruling)

The staging note claimed the six prayers are the KB list "identical". Read against both
documents, every one of the six effects is **different printed prose**, and one differs
materially:

- `Tanglefoot` — KB: "All models, friend as well as foe, with the exception of **Ostlander
  Jaegers and friendly Horned Hunter Zealots**, within 12\" ..."; staging: "... with the
  exception of **friendly Taalites** within 12\" ...". The exception list is a different
  rule.
- `Earthshudder` — the staging adds the printed falling example ("a model falling 5\" to the
  tabletop must pass two Initiative tests to avoid taking D3 Strength 5 hits").
- `Stag's Leap`, `Blessed Ale`, `Bears Paw` (KB "Bear's Paw") and `Summon Squirrels` add
  printed flavour prose the KB entry does not carry.

Decision: **the lore and its six spells are promoted as their own variant**, verbatim, next
to the KB `lore.prayers-of-taal` (which stays for the Ostlander and Horned Hunter priests).
Dropping it would lose six printed rule blocks with no documented equivalence, which the
closing condition forbids. **Tool defect for T05:**
`magic_promotion.MIRROR_LORES` (`packages/python/knowledge/mordheim_knowledge/magic_promotion.py:137`,
applied at line 269) still lists `lore.prayers-of-taal-and-rhya`, so
`normalize_staging_for_promotion.py --check` reports "10 lores in the KB shape" for an 11-lore
document: the entry must be removed from `MIRROR_LORES` or the lore is silently dropped. The
`lore_assignments` row for `hireling.hired-sword.druid-priest-of-taal` currently points at
`lore.prayers-of-taal`; with the variant promoted it should point at the variant, which is
the same kind of mechanical remap `magic_promotion.MAGIC_ASSIGNMENTS` already performs.

### B.2 The eight `lore-source-missing` — closed by the recovered source

All eight prayer lores (`manann`, `morr`, `myrmidia`, `ranald-and-handrich`, `shallya`,
`ulric-miracle-workers`, `verena-and-solkan`, `taal-and-rhya`) cite
"Miracle-workers-in-Mordheim" as their first source. With the recovered chapter cached at
`build/cache/2b-pdfs/extra/Miracle Workers.pdf` (see section D), `audit_2b.py` reports
`problem_count 0`, `adjudicated_count 0` and **`spells_checked 66 / spells_anchored 66`**
(was 18/18 with 8 `lore-source-missing`). No equivalence was invented: the chapter is the
same published article the catalog cites.

### B.3 No other magic change

10 of the 11 lores are plain new entries; 0 `lore_id` and 0 `spell_id` collide with the KB or
with 2A. The `lore_assignments` table, the `pending_lores: []` envelope and the
`casting_rules` copy are the mechanical remaps the schema plan already declares.

## C. Hirelings — three id collisions with the KB, decided

Three Miracle Workers priests were transcribed with the same ids the KB already uses for
different publications. Every one of them is a **variant, not a duplicate**:

| Id | KB entry | Staging entry | Same id, different record |
|---|---|---|---|
| `hireling.hired-sword.priest-of-morr` | `grade-1b.yaml`, publication **Town Cryer 12**, WS2 BS2 I4 Ld9, Loner + Funerary Rites | `miracle-workers-priests.yaml`, publication **Miracle Workers**, WS3 BS3 I3 Ld8, Prayers + Strictures + Loner + Morr's Servant + Protected by Morr + Marks of Morr, 12 experience | yes |
| `hireling.hired-sword.warrior-priest-of-sigmar` | `grade-1b.yaml`, **Town Cryer 28**, I4, Hammer of Sigmar, Middenheim eligibility | `miracle-workers-priests.yaml`, **Miracle Workers**, I3, Marks of Sigmar, experience 12 | yes |
| `hireling.hired-sword.wolf-priest-of-ulric` | `grade-1b.yaml`, **Town Cryer 8**, Prayers of Ulric (KB list), Hatred, Wolf Companion, Middenheim hero replacement | `miracle-workers-priests.yaml`, **Miracle Workers**, Prayers of Ulric (Miracle Workers variant), Strictures, Intense Rivals, Marks of Ulric, experience 12 | characteristics coincide, rules do not |

The collision is not only the profile ids: the staging **rule ids** collide too
(`...priest-of-morr.rule.loner`, `...warrior-priest-of-sigmar.rule.prayers`,
`...wolf-priest-of-ulric.rule.prayers`), so a naive merge would overwrite a KB rule with
different text.

**Decision: keep both publications and disambiguate the staging ids by redirection** (this
preserves staging ids and text, as the contract requires, and gives T05 a mechanical table):

| Staging id | Promoted as |
|---|---|
| `hireling.hired-sword.priest-of-morr` | `hireling.hired-sword.priest-of-morr-miracle-workers` |
| `hireling.hired-sword.warrior-priest-of-sigmar` | `hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers` |
| `hireling.hired-sword.wolf-priest-of-ulric` | `hireling.hired-sword.wolf-priest-of-ulric-miracle-workers` |

Every rule id prefixed by a redirected profile id redirects with it (6 + 2 + 4 = 12 rule
ids), and the three `hired-swords-and-dramatis-2b.yaml` entries are keyed by the same ids, so
they redirect too. The `-miracle-workers` suffix follows the tree's own convention
(`lore.prayers-of-ulric-miracle-workers`). **Tool defect for T05:**
`hireling_promotion.py` has no id-redirect table; it needs one mirroring
`magic_promotion.LORE_RENAMES`.

Everything else in the hirelings catalog is a plain new entry (25 profiles) plus the two
`name-only` Dramatis profiles (`strigani-seer-necromancer`, `snerik-night-goblin-scout`),
which stay `out_of_scope` with no campaign entry — as already decided above. Currencies are
preserved verbatim (`75 warp tokens` for the Albino Stormvermin, `85 dinars` for Armen Abbas).

### C.1 Editorial rule label — Mariner-Priest of Manann

`check_hireling_sources.py --tree 2b` reports one finding: the rule **"Priest Hero Slot
(Chapter Errata)"** is not printed. Its effect cites an author ruling (TBMF t8634) that the
priest replaces a starting Hero. The chapter does print the related sentence — "... as a Hero
and no warband may ever include more than six Heroes" (Miracle Workers pp. 1-2) — but it does
not print the replacement ruling, and the forum ruling is not recoverable from this
repository. Decision: the rule is kept (it is translated and carries the printed statement plus
its cited ruling), classified as an editorial label, and handed to the coordinator as an
editorial item like T03's `rule-name-editorial` class. Anchoring the printed sentence into the
effect is a wording change and was not made by T04.

## D. Recovered external sources (provenance)

Both documents the catalog cites are cached again under `build/cache/2b-pdfs/extra/` (ignored
by git, restored 2026-09-25):

| Document | Source | Recovered | Bytes | sha256 | Pages | Affected records |
|---|---|---|---|---|---|---|
| `Miracle Workers.pdf` | Wayback mirror of the author's file: `https://web.archive.org/web/20120128041736if_/http://cianty.ashtonsanders.com/mim/pdf/miracle_workers.pdf` (the original URL is 404 today; the link lives on `http://libermalefic.blogspot.com/2011/05/believe-in-miracles.html`) | 2026-09-25 | 1854347 | `73678122d02bfd13ffa8af36902a3cc46d8897267bd3ac734afb919418b79607` | 18 | the 8 prayer lores of `magic-2b.yaml`; the 9 profiles of `miracle-workers-priests.yaml` (printed pages 5, 12, 14 cited); `miracle-workers-gear.yaml` (wolf pelt cloak) |
| `MiM Specialists.pdf` | `https://broheim.net/downloads/hiredswords/mutinyinmarienburg/MiM%20Specialists.pdf` | 2026-09-25 | 589488 | `8f291c721ec09ad3a179ac260e7ff65039f6c9ebcd588e9c25a5baffe259ac3f` | 5 | the 9 profiles of `mim-specialists.yaml` and the Bog Hunter / Whaler entries of `grade-2b.yaml` |

The text layer of both was extracted and cached (`extra/words-extra/`), so the auditors read
them structurally. With them present the 2B audit closes: `problem_count 0`.

**Coverage caveat declared by T04.** `audit_2ab_fidelity.py` reads the extra documents as
**tree-wide shared chapters**, not per band, so a wording printed in one extra document can
close another 2B band's `item-name-missing` finding. Measured A/B on this revision:
`item-name-missing` is **8** without the extras and **3** with them (the five that move are
reported as `item-in-supplement`, informational). The closures are not band-specific
evidence — `Miracle Workers.p2.xml` prints "Throwing knives ... 15 gc" and "Mace/Staff ... 3
gc" in its own priest equipment list, which is what closes the `throwing_knives` and
`mace_hammer` rows of unrelated bands. Both numbers are reported so a re-run is not read as
progress that did not happen.

## E. Band-side handoff (T03 owns `sources/2B/bands/**`)

Exactly three re-points are requested; nothing else in the bands changes.

| Band | List | From | To | Keep |
|---|---|---|---|---|
| `adventurers-kaz` | `elf-equipment-list` | `staff_club_mace` | `mace_hammer` | cost 3, `notes: Club, Mace or Hammer.` |
| `adventurers-kaz` | `dwarf-equipment-list` | `staff_club_mace` | `mace_hammer` | cost 3, note as above |
| `adventurers-kaz` | `cannon-fodder-equipment-list` | `staff_club_mace` | `mace_hammer` | cost 3, note as above |
| `underworld-alliance-mim` | `greenskin-equipment-list` | `throwing_knives` | `throwing_stars` | cost 15, `notes: Throwing stars; Heroes only` |
| `underworld-alliance-mim` | `skaven-equipment-list` | `throwing_knives` | `throwing_stars` | cost 15, note as above |
| `militiant-mootlanders-mim` | `heroes-equipment-list` | `throwing_knives` | `throwing_stars` | cost 15, `notes: Kitchenware (counts as throwing stars)` |

`high-elves-lus` (`elven_bow` -> `elf_bow`, two rows) is **not** in this table because it is a
2B-catalog re-point, not a band change: the band keeps referencing `elven_bow` until T05
performs the redirect, or the coordinator moves the edit to T03 — the note in section A.4
covers both routes.

All other band rows in `sources/2B/bands/**` are unchanged, including every `notes` field
that records a printed wording, every band-side cost and every inherited-list row.
