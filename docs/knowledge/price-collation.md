# Trading Post price collation

_Regenerate with `python tools/kb/price-collation.py`._  
_Compared every `cost` of every `equipment-access.yaml` against `campaign/trading-post.yaml` (2152 rows across 81 warbands)._

## Status counts

| Status | Rows | Meaning |
|---|---|---|
| `no-market` | 229 | No Trading Post sellable row: list price stands, nothing to collate |
| `relative-tp` | 4 | Trading Post price is multiplier-based; compare via the base record |
| `consistent` | 1726 | List cost equals the Trading Post base price |
| `consistent-special` | 42 | Matches the TP base; TP also has a variable part/`per` (pairs — glance) |
| `differs` | 88 | List cost differs from a flat Trading Post price |
| `differs-special` | 31 | List cost differs from a TP price with dice/per part |
| `creation-price` | 14 | Page-verified creation price; the Trading Post prevails at the market |
| `override` | 18 | `price_override` already recorded |

## How to read a differing row

A warband equipment list is the **creation/recruitment** price list of
its printed source; the Trading Post is the **market** price used when
the item is bought outside the list (post-battle). The two may differ
by design, so a difference alone is not an exception. An override is
recorded only when the warband's own source confirms that the list
amount is what the warband pays as a market price too:

- Nuln *Impeccable Care*: reduced black-powder weapon costs apply always.
- Hochland *Powder's Expensive!*: bandit heroes always pay the higher
  black-powder weapon costs of the Duelist list.
- Lizardmen *Armour*: light armour always costs 50 gc for Lizardmen,
  including from the Equipment chart.

18 rows carry a `price_override` and 14 differing rows were page-verified as plain
creation prices (the list price is what a recruit pays; the Trading
Post prevails at the market). Remaining differing rows keep their list
`cost` as historical evidence and stay in the queue until each printed
source is verified; rows whose warband has no recorded source URL
(Trollheim/Lustria/Khemri settings) are part of that queue.

## Review queue (per warband)


### Amazons (Lustria) (`mordheim/amazons-lustria`)

- Source: Henchwomen equipment list — https://mordheimer.net/docs/warbands/grade-1b-warbands/amazons-lustria
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Sling (`sling`) | 5 gc | 2 gc | `campaign.trading-post.sling` | differs | — |
| Healing Herbs (`healing_herbs`) | 35 gc | 20 gc + dice | `campaign.trading-post.healing-herbs` | differs-special | — |
| Sling (`sling`) | 5 gc | 2 gc | `campaign.trading-post.sling` | differs | — |

### Arabian Tomb Raiders (`mordheim/arabian-tomb-raiders`)

- Source: Warrior equipment list — https://mordheimer.net/docs/warbands/grade-1b-warbands/arabian-tomb-raiders
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Light Armour (`light_armour`) | 50 gc | 20 gc | `campaign.trading-post.light-armour` | differs | — |

### Averlander Mercenaries (`mordheim/averlanders`)

- Source: Mountainguard Equipment List — https://mordheimer.net/docs/warbands/grade-1a-warbands/averlander
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Hunting Arrows (`hunting_arrows`) | 35 gc | 25 gc + dice | `campaign.trading-post.hunting-arrows` | differs-special | — |

### Battle Monks of Cathay (`mordheim/battle-monks-of-cathay`)

- Source: Soldier Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/battle-monks-of-cathay
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Cathayan Silk Cloak (`cathayan_silk_cloak`) | 40 gc | 50 gc + dice | `campaign.trading-post.cathayan-silk-clothes` | differs-special | — |
| Horse (`horse`) | 30 gc | 40 gc | `campaign.trading-post.riding-draft-horse` | differs | — |

### Black Dwarfs (`mordheim/black-dwarfs`)

- Source: Chaos Dwarf Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/black-dwarfs
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Dagger (`dagger`) | 1 gc | 2 gc | `campaign.trading-post.dagger` | differs | — |
| Engine Of Chaos (`engine_of_chaos`) | 125 gc | 195 gc | `campaign.trading-post.engine-of-chaos` | differs | — |
| Mechanical Suit (`mechanical_suit`) | 175 gc | 225 gc | `campaign.trading-post.mechanical-suit` | differs | — |

### Bretonnian Chapel Guard (`mordheim/bretonnian-chapel-guard`)

- Source: Knights Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/bretonnian-chapel-guard
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Barding (`barding`) | 30 gc | 80 gc | `campaign.trading-post.barding` | differs | — |
| Lance Not Questing Knight (`lance_not_questing_knight`) | 20 gc | 40 gc | `campaign.trading-post.lance-not-questing-knight` | differs | — |
| Holy Relic Pilgrim Only (`holy_relic_pilgrim_only`) | 25 gc | 15 gc + dice | `campaign.trading-post.holy-relic-pilgrim-only` | differs-special | — |

### Bretonnian Knights (`mordheim/bretonnian-knights`)

- Source: Knights Equipment List — https://mordheimer.net/docs/warbands/grade-1b-warbands/bretonnian
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Lance (`lance`) | 20 gc | 40 gc | `campaign.trading-post.lance` | differs | — |

### Bretonnian Knights (`trollheim/chaos-streets-bretonnian-knights`)

- Source: Bowmen Equipment List — 
- Differing rows: 6; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Sword (`sword`) | 5 gc | 10 gc | `campaign.trading-post.sword` | differs | — |
| Barding (`barding`) | 30 gc | 80 gc | `campaign.trading-post.barding` | differs | — |
| Lance (`lance`) | 20 gc | 40 gc | `campaign.trading-post.lance` | differs | — |
| Sword (`sword`) | 5 gc | 10 gc | `campaign.trading-post.sword` | differs | — |
| Sword (`sword`) | 5 gc | 10 gc | `campaign.trading-post.sword` | differs | — |
| Sword (`sword`) | 5 gc | 10 gc | `campaign.trading-post.sword` | differs | — |

### Dwarf Treasure Hunters (`trollheim/chaos-streets-dwarf-treasure-hunters`)

- Source: Dwarf Warrior Equipment List — 
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Gromril Armour (`gromril_armour`) | 75 gc | 150 gc | `campaign.trading-post.gromril-armour` | differs | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |

### Greenskins (`trollheim/chaos-streets-greenskins`)

- Source: Goblin Equipment List — 
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Ball Chain (`ball_chain`) | 25 gc | 15 gc | `campaign.trading-post.ball-and-chain` | differs | — |
| Mad Cap Mushrooms (`mad_cap_mushrooms`) | 25 gc | 30 gc + dice | `campaign.trading-post.mad-cap-mushrooms` | differs-special | — |
| Mad Cap Mushrooms (`mad_cap_mushrooms`) | 25 gc | 30 gc + dice | `campaign.trading-post.mad-cap-mushrooms` | differs-special | — |

### Sigmar's Protectorate (`trollheim/chaos-streets-sigmar-protectorate`)

- Source: Devout Equipment List — 
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Blessed Water (`blessed_water`) | 5 gc | 10 gc + dice | `campaign.trading-post.blessed-water` | differs-special | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |
| Blessed Water (`blessed_water`) | 5 gc | 10 gc + dice | `campaign.trading-post.blessed-water` | differs-special | — |

### Sons of Nagarythe (`trollheim/chaos-streets-sons-of-nagarythe`)

- Source: Shadow Warrior Equipment List — 
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Elven Cloak (`elven_cloak`) | 75 gc | 100 gc + dice | `campaign.trading-post.elven-cloak` | differs-special | — |
| Ithilmar Armour (`ithilmar_armour`) | 60 gc | 90 gc | `campaign.trading-post.ithilmar-armour` | differs | — |

### The Cursed Cavalcade (`mordheim/cursed-cavalcade`)

- Source: Heroes Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/cursed-cavalcade
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Lance (`lance`) | 20 gc | 40 gc | `campaign.trading-post.lance` | differs | — |
| Misericordia (`misericordia`) | 5 gc | 10 gc | `campaign.trading-post.misericordia` | differs | — |

### Dark Elves (`mordheim/dark-elves`)

- Source: Dark Elf Equipment List — https://mordheimer.net/docs/warbands/grade-1b-warbands/dark-elves
- Differing rows: 4; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Dark Elf Blade Weapon Upgrade (`dark_elf_blade_weapon_upgrade`) | 15 gc | 20 gc | `campaign.trading-post.dark-elf-blade` | differs | — |
| Dark Venom (`dark_venom`) | 15 gc | 30 gc + dice | `campaign.trading-post.dark-venom` | differs-special | — |
| Repeater Crossbow (`repeater_crossbow`) | 35 gc | 40 gc | `campaign.trading-post.repeater-crossbow` | differs | — |
| Repeater Crossbow (`repeater_crossbow`) | 35 gc | 40 gc | `campaign.trading-post.repeater-crossbow` | differs | — |

### Dwarf Rangers (`mordheim/dwarf-rangers`)

- Source: Dwarf Warrior Equipment List — https://mordheimer.net/docs/warbands/grade-1b-warbands/dwarf-rangers
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Gromril Armour (`gromril_armour`) | 75 gc | 150 gc | `campaign.trading-post.gromril-armour` | differs | — |

### Dwarf Treasure Hunters (`mordheim/dwarf-treasure-hunters`)

- Source: Dwarf Warrior Equipment List — https://mordheimer.net/docs/warbands/grade-1a-warbands/dwarf-treasure-hunters
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Gromril Armour (`gromril_armour`) | 75 gc | 150 gc | `campaign.trading-post.gromril-armour` | differs | — |

### Forest Goblins (`mordheim/forest-goblins`)

- Source: Henchmen Equipment List — https://mordheimer.net/docs/warbands/grade-1b-warbands/forest-goblins
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Spear (`spear`) | 5 gc | 10 gc | `campaign.trading-post.spear` | differs | — |
| Spear (`spear`) | 5 gc | 10 gc | `campaign.trading-post.spear` | differs | — |

### Gunnery School of Nuln (`mordheim/gunnery-school-of-nuln`)

- Source: Gunnery School equipment lists — https://mordheimer.net/docs/warbands/grade-1b-warbands/gunnery-school-of-nuln
- Differing rows: 0; overrides recorded: 16

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Double Barrelled Duelling Pistol (`double_barrelled_duelling_pistol`) | 35 gc | 45 gc + dice | `campaign.trading-post.double-barrelled-duelling-pistol` | override | 35 gc |
| Double Barrelled Handgun (`double_barrelled_handgun`) | 45 gc | 60 gc + dice | `campaign.trading-post.double-barrelled-handgun` | override | 45 gc |
| Double Barrelled Pistol (`double_barrelled_pistol`) | 20 gc | 25 gc + dice | `campaign.trading-post.double-barrelled-pistol` | override | 20 gc |
| Duelling Pistol (`duelling_pistol`) | 20 gc | 30 gc | `campaign.trading-post.duelling-pistol` | override | 20 gc |
| Handgun (`handgun`) | 25 gc | 35 gc | `campaign.trading-post.handgun` | override | 25 gc |
| Pistol (`pistol`) | 10 gc | 15 gc | `campaign.trading-post.pistol` | override | 10 gc |
| Blunderbuss (`blunderbuss`) | 20 gc | 30 gc | `campaign.trading-post.blunderbuss` | override | 20 gc |
| Double Barrelled Handgun (`double_barrelled_handgun`) | 45 gc | 60 gc + dice | `campaign.trading-post.double-barrelled-handgun` | override | 45 gc |
| Double Barrelled Pistol (`double_barrelled_pistol`) | 20 gc | 25 gc + dice | `campaign.trading-post.double-barrelled-pistol` | override | 20 gc |
| Hand Held Mortar (`hand_held_mortar`) | 70 gc | 80 gc + dice | `campaign.trading-post.hand-held-mortar` | override | 70 gc |
| Handgun (`handgun`) | 25 gc | 35 gc | `campaign.trading-post.handgun` | override | 25 gc |
| Hochland Long Rifle (`hochland_long_rifle`) | 100 gc | (not sold) | `campaign.trading-post.hochland-long-rifle` | override | 100 gc |
| Pigeon Bombs (`pigeon_bombs`) | 25 gc | 30 gc + dice | `campaign.trading-post.hersten-wenkler-pigeon-bombs` | override | 25 gc |
| Pistol (`pistol`) | 10 gc | 15 gc | `campaign.trading-post.pistol` | override | 10 gc |
| Repeater Handgun (`repeater_handgun`) | 50 gc | 60 gc + dice | `campaign.trading-post.repeater-handgun` | override | 50 gc |
| Repeater Pistol (`repeater_pistol`) | 25 gc | 30 gc + dice | `campaign.trading-post.repeater-pistol` | override | 25 gc |

### Hochland Bandits (`mordheim/hochland-bandits`)

- Source: Duelist equipment list — https://mordheimer.net/docs/warbands/grade-1b-warbands/hochland-bandits
- Differing rows: 0; overrides recorded: 1

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Pistol (`pistol`) | 20 gc | 15 gc | `campaign.trading-post.pistol` | override | 20 gc |

### Horned Hunters (`mordheim/horned-hunters`)

- Source: Henchmen equipment list — https://mordheimer.net/docs/warbands/grade-1b-warbands/horned-hunters
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Spear (`spear`) | 5 gc | 10 gc | `campaign.trading-post.spear` | differs | — |
| Hunting Arrows (`hunting_arrows`) | 20 gc | 25 gc + dice | `campaign.trading-post.hunting-arrows` | differs-special | — |
| Spear (`spear`) | 5 gc | 10 gc | `campaign.trading-post.spear` | differs | — |

### The Cursed of Karak-Zorn (`trollheim/khemri-cursed-of-karak-zorn`)

- Source: Cursed of Karak-Zorn Equipment List — 
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Gromril Armour (`gromril_armour`) | 80 gc | 150 gc | `campaign.trading-post.gromril-armour` | differs | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |

### Hobgoblin Raiders (`trollheim/khemri-hobgoblin-raiders`)

- Source: Raider Equipment List — 
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Poison Daggers (`poison_daggers`) | 8 gc | 25 gc | `campaign.trading-post.poison-daggers` | differs | — |

### Lahmian Brotherhood (`trollheim/khemri-lahmian-brotherhood`)

- Source: Foreign Warbands / Beloved Equipment List — 
- Differing rows: 4; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Duelling Pistol (`duelling_pistol`) | 50 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |
| Nomad Robes (`nomad_robes`) | 15 gc | 25 gc | `campaign.trading-post.nomad-robes` | differs | — |

### Mages (`trollheim/khemri-mages`)

- Source: Mage Equipment List — 
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Flying Carpet (`flying_carpet`) | 60 gc | 50 gc + dice | `campaign.trading-post.magic-carpet` | differs-special | — |

### Nomads of Araby (`trollheim/khemri-nomads-of-araby`)

- Source: Warrior Equipment List — 
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Nomad Robes (`nomad_robes`) | 15 gc | 25 gc | `campaign.trading-post.nomad-robes` | differs | — |

### Kislevites (`mordheim/kislevites`)

- Source: Kislev Warrior equipment List — https://mordheimer.net/docs/warbands/grade-1a-warbands/kislevites
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |

### Lizardmen (`mordheim/lizardmen`)

- Source: Saurus equipment list — https://mordheimer.net/docs/warbands/grade-1b-warbands/lizardmen
- Differing rows: 0; overrides recorded: 1

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Light Armour (`light_armour`) | 50 gc | 20 gc | `campaign.trading-post.light-armour` | override | 50 gc |

### Amazons (`trollheim/lustria-amazons`)

- Source: Amazon Heroine Equipment List — 
- Differing rows: 5; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Healing Herbs (`healing_herbs`) | 35 gc | 20 gc + dice | `campaign.trading-post.healing-herbs` | differs-special | — |
| Javelin (`javelin`) | 10 gc | 5 gc | `campaign.trading-post.javelin` | differs | — |
| Javelin (`javelin`) | 10 gc | 5 gc | `campaign.trading-post.javelin` | differs | — |
| Sling (`sling`) | 5 gc | 2 gc | `campaign.trading-post.sling` | differs | — |
| Sling (`sling`) | 5 gc | 2 gc | `campaign.trading-post.sling` | differs | — |

### Clan Pestilens (`trollheim/lustria-clan-pestilens`)

- Source: Clan Pestilens Hero Equipment List — 
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Pestilens Banner (`pestilens_banner`) | 5 gc | 10 gc | `campaign.trading-post.clan-pestilens-banner` | differs | — |

### Dark Elves (`trollheim/lustria-dark-elves`)

- Source: Dark Elf Equipment List — 
- Differing rows: 4; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Dark Venom (`dark_venom`) | 15 gc | 30 gc + dice | `campaign.trading-post.dark-venom` | differs-special | — |
| Light Armour (`light_armour`) | 50 gc | 20 gc | `campaign.trading-post.light-armour` | differs | — |
| Repeater Crossbow (`repeater_crossbow`) | 35 gc | 40 gc | `campaign.trading-post.repeater-crossbow` | differs | — |
| Repeater Crossbow (`repeater_crossbow`) | 35 gc | 40 gc | `campaign.trading-post.repeater-crossbow` | differs | — |

### High Elves (`trollheim/lustria-high-elves`)

- Source: High Elf Equipment List — 
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Elven Cloak (`elven_cloak`) | 60 gc | 100 gc + dice | `campaign.trading-post.elven-cloak` | differs-special | — |
| Elven Wine (`elven_wine`) | 30 gc | 50 gc + dice | `campaign.trading-post.elven-wine` | differs-special | — |
| Ithilmar Armour (`ithilmar_armour`) | 60 gc | 90 gc | `campaign.trading-post.ithilmar-armour` | differs | — |

### Lizardmen (`trollheim/lustria-lizardmen`)

- Source: Lizardmen Poison List — 
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Dark Venom (`dark_venom`) | 20 gc | 30 gc + dice | `campaign.trading-post.dark-venom` | differs-special | — |
| Light Armour (`light_armour`) | 50 gc | 20 gc | `campaign.trading-post.light-armour` | differs | — |
| Javelin (`javelin`) | 10 gc | 5 gc | `campaign.trading-post.javelin` | differs | — |

### Norse (`trollheim/lustria-norse`)

- Source: Hunter Equipment List — 
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Javelin (`javelin`) | 10 gc | 5 gc | `campaign.trading-post.javelin` | differs | — |

### Pirates (`trollheim/lustria-pirates`)

- Source: Gunner Equipment List — 
- Differing rows: 4; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 60 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |
| Duelling Pistol (`duelling_pistol`) | 60 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |

### Pygmies (`trollheim/lustria-pygmies`)

- Source: Pygmy Equipment List — 
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Dark Venom (`dark_venom`) | 20 gc | 30 gc + dice | `campaign.trading-post.dark-venom` | differs-special | — |
| Javelin (`javelin`) | 10 gc | 5 gc | `campaign.trading-post.javelin` | differs | — |
| Spider Spit (`spider_spit`) | 25 gc | 30 gc + dice | `campaign.trading-post.spider-spittle` | differs-special | — |

### Savage Goblins (`trollheim/lustria-savage-goblins`)

- Source: Savage Goblin Henchman Equipment List — 
- Differing rows: 4; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Javelin (`javelin`) | 10 gc | 5 gc | `campaign.trading-post.javelin` | differs | — |
| Dark Venom (`dark_venom`) | 20 gc | 30 gc + dice | `campaign.trading-post.dark-venom` | differs-special | — |
| Javelin (`javelin`) | 10 gc | 5 gc | `campaign.trading-post.javelin` | differs | — |
| Spider Spit (`spider_spit`) | 25 gc | 30 gc + dice | `campaign.trading-post.spider-spittle` | differs-special | — |

### Tilean Mercenaries (`trollheim/lustria-tileans`)

- Source: Marksman Equipment List — 
- Differing rows: 7; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Duelling Pistol (`duelling_pistol`) | 50 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Duelling Pistol (`duelling_pistol`) | 50 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Pike (`pike`) | 12 gc | 10 gc | `campaign.trading-post.pike.merchant-caravans` | differs | — |
| Pistol (`pistol`) | 30 gc | 15 gc | `campaign.trading-post.pistol` | differs | — |

### Lustrian Reavers (`mordheim/lustrian-reavers`)

- Source: Hero Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/lustrian-reavers
- Differing rows: 6; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Blowpipe (`blowpipe`) | 15 gc | 25 gc | `campaign.trading-post.blowpipe` | differs | — |
| Buckler (`buckler`) | 10 gc | 5 gc | `campaign.trading-post.buckler` | differs | — |
| Javelin (`javelin`) | 10 gc | 5 gc | `campaign.trading-post.javelin` | differs | — |
| Shield (`shield`) | 10 gc | 5 gc | `campaign.trading-post.shield` | differs | — |
| Warhound (`warhound`) | 20 gc | 25 gc + dice | `campaign.trading-post.wardogs` | differs-special | — |
| Shield (`shield`) | 10 gc | 5 gc | `campaign.trading-post.shield` | differs | — |

### Maneaters (`mordheim/maneaters`)

- Source: Ogre Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/maneaters
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Hand Held Mortar (`hand_held_mortar`) | 70 gc | 80 gc + dice | `campaign.trading-post.hand-held-mortar` | differs-special | — |

### Merchant Caravans (`mordheim/merchant-caravans`)

- Source: Hero Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/merchant-caravans
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Cathayan Silk Cloak (`cathayan_silk_cloak`) | 40 gc | 50 gc + dice | `campaign.trading-post.cathayan-silk-clothes` | differs-special | — |
| Warhorse (`warhorse`) | 40 gc | 80 gc | `campaign.trading-post.warhorse` | differs | — |

### Night Goblins (`mordheim/night-goblins-mic`)

- Source: Fanatic Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/night-goblins
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Mad Cap Mushrooms (`mad_cap_mushrooms`) | 25 gc | 30 gc + dice | `campaign.trading-post.mad-cap-mushrooms` | differs-special | — |

### Night Goblins (web) (`mordheim/night-goblins-web`)

- Source: Fanatic Equipment List — https://mordheimer.net/docs/warbands/grade-1c-warbands/night-goblins-web
- Differing rows: 4; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Mad Cap Mushrooms (`mad_cap_mushrooms`) | 15 gc | 30 gc + dice | `campaign.trading-post.mad-cap-mushrooms` | differs-special | — |
| Mad Cap Mushrooms (`mad_cap_mushrooms`) | 15 gc | 30 gc + dice | `campaign.trading-post.mad-cap-mushrooms` | differs-special | — |
| Spear (`spear`) | 5 gc | 10 gc | `campaign.trading-post.spear` | differs | — |
| Mad Cap Mushrooms (`mad_cap_mushrooms`) | 15 gc | 30 gc + dice | `campaign.trading-post.mad-cap-mushrooms` | differs-special | — |

### Orc Mob (`mordheim/orc-mob`)

- Source: Goblin Equipment List — https://mordheimer.net/docs/warbands/grade-1a-warbands/orc-mob
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Mad Cap Mushrooms (`mad_cap_mushrooms`) | 25 gc | 30 gc + dice | `campaign.trading-post.mad-cap-mushrooms` | differs-special | — |

### Outlaws of Stirwood Forest (`mordheim/outlaws-of-stirwood-forest`)

- Source: Outlaws equipment lists — https://mordheimer.net/docs/warbands/grade-1b-warbands/outlaws-of-stirwood-forest
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Hunting Arrows (`hunting_arrows`) | 30 gc | 25 gc + dice | `campaign.trading-post.hunting-arrows` | differs-special | — |

### Shadow Warriors (`mordheim/shadow-warriors`)

- Source: Shadow Warrior equipment lists — https://mordheimer.net/docs/warbands/grade-1b-warbands/shadow-warriors
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Elven Cloak (`elven_cloak`) | 75 gc | 100 gc + dice | `campaign.trading-post.elven-cloak` | differs-special | — |
| Ithilmar Armour (`ithilmar_armour`) | 60 gc | 90 gc | `campaign.trading-post.ithilmar-armour` | differs | — |

### The Sons of Hashut (`mordheim/sons-of-hashut`)

- Source: Chaos Dwarf equipment lists — https://mordheimer.net/docs/warbands/grade-1c-warbands/sons-of-hashut
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Obsidian Weapon (`obsidian_weapon`) | 30 gc | 60 gc | `campaign.trading-post.sons-of-hashut-obsidian-weapon` | differs | — |

### Tileans (Miragleans / Remasens / Trantios) (`mordheim/tileans`)

- Source: Marksman equipment list — https://mordheimer.net/docs/warbands/grade-1b-warbands/tileans
- Differing rows: 2; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |

### Cult of the Possessed (`trollheim/trollheim-cult-of-the-possessed`)

- Source: Darksoul and Beastman Equipment List — 
- Differing rows: 3; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Flail (`flail`) | 10 gc | 15 gc | `campaign.trading-post.flail` | differs | — |
| Bow (`bow`) | 15 gc | 10 gc | `campaign.trading-post.bow` | differs | — |
| Short Bow (`short_bow`) | 10 gc | 5 gc | `campaign.trading-post.short-bow` | differs | — |

### Mercenaries (`trollheim/trollheim-mercenaries`)

- Source: Mercenary Equipment List — 
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | `campaign.trading-post.duelling-pistol` | differs | — |

### Skaven Clan Eshin (`trollheim/trollheim-skaven-clan-eshin`)

- Source: Skaven Hero Equipment List — 
- Differing rows: 1; overrides recorded: 0

| Item | List cost | Trading Post | TP entry | Status | `price_override` |
|---|---|---|---|---|---|
| Blowpipe (`blowpipe`) | 30 gc | 25 gc | `campaign.trading-post.blowpipe` | differs | — |

## Verified creation prices (page-checked; Trading Post prevails)


### Amazons (Mordheim) (`amazons-mordheim`)

| Item | List cost | Trading Post | Verdict note |
|---|---|---|---|
| Healing Herbs (`healing_herbs`) | 35 gc | 20 gc + dice | Verified on the Amazons (Mordheim) page: healing herbs 35 gc is the printed Heroines-list price (Town Cryer #23). |
| Sling (`sling`) | 5 gc | 2 gc | Verified on the Amazons (Mordheim) page: sling 5 gc is the printed Henchwomen/Scout creation price (Town Cryer #23). |
| Sling (`sling`) | 5 gc | 2 gc | Verified on the Amazons (Mordheim) page: sling 5 gc is the printed Henchwomen/Scout creation price (Town Cryer #23). |

### Carnival of Chaos (`carnival-of-chaos`)

| Item | List cost | Trading Post | Verdict note |
|---|---|---|---|
| Bow (`bow`) | 15 gc | 10 gc | Verified on the Carnival of Chaos page: bow 15 gc is the printed creation-list price; no market-exception rule. |
| Flail (`flail`) | 10 gc | 15 gc | Verified on the Carnival of Chaos page: Brute list flail 10 gc is the printed creation-list price; no market-exception rule. |
| Short Bow (`short_bow`) | 10 gc | 5 gc | Verified on the Carnival of Chaos page: short bow 10 gc is the printed creation-list price; no market-exception rule. |

### Cult of the Possessed (`cult-of-the-possessed`)

| Item | List cost | Trading Post | Verdict note |
|---|---|---|---|
| Bow (`bow`) | 15 gc | 10 gc | Verified on the Cult of the Possessed page: bow 15 gc is the printed creation-list price; no market-exception rule. |
| Short Bow (`short_bow`) | 10 gc | 5 gc | Verified on the Cult of the Possessed page: short bow 10 gc is the printed creation-list price; no market-exception rule. |

### Gunnery School of Nuln (`gunnery-school-of-nuln`)

| Item | List cost | Trading Post | Verdict note |
|---|---|---|---|
| Superior Blackpowder (`superior_blackpowder`) | 25 gc | 30 gc | Verified on the Gunnery School page: superior black powder 25 gc is a Miscellaneous creation-list price; Impeccable Care covers black-powder weapons only. |
| Superior Blackpowder (`superior_blackpowder`) | 25 gc | 30 gc | Verified on the Gunnery School page: superior black powder 25 gc is a Miscellaneous creation-list price; Impeccable Care covers black-powder weapons only. |

### Hochland Bandits (`hochland-bandits`)

| Item | List cost | Trading Post | Verdict note |
|---|---|---|---|
| Buckler (`buckler`) | 10 gc | 5 gc | Verified on the Hochland Bandits page: Duelist-list buckler 10 gc is the printed creation price; Powder's Expensive! covers black-powder weapons only. |

### Lizardmen (`lizardmen`)

| Item | List cost | Trading Post | Verdict note |
|---|---|---|---|
| Javelins (`javelins`) | 10 gc | 5 gc | Verified on the Lizardmen page: Skink javelins 10 gc is the printed creation-list price; the Armour rule covers light armour only. |

### Mercenaries (`mercenaries`)

| Item | List cost | Trading Post | Verdict note |
|---|---|---|---|
| Duelling Pistol (`duelling_pistol`) | 25 gc | 30 gc | Verified on the Mercenaries page: 25 gc (50 for a brace) is the printed creation-list price; no market-exception rule. |

### Sisters of Sigmar (`sisters-of-sigmar`)

| Item | List cost | Trading Post | Verdict note |
|---|---|---|---|
| Holy Tome (`holy_tome`) | 120 gc | 100 gc + dice | Verified on the Sisters of Sigmar page: 120 gc is the creation-list price; the page's own Trading Post section prices the Holy Tome 100 + D6x10 (Rare 8). |

_Generated from the KB loaders; 2152 equipment-access cost rows checked._
