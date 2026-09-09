# Spanish translation glossary — canonical warband-rule terminology

Single terminology authority for the Spanish translation of the knowledge
base (`name_i18n.es` / `effect_i18n.es`). Built from the reviewed pilot band
(`bands/mordheim/bretonnian-knights`) and extended band by band. Every band
translation must reuse these terms so equivalent rules across bands receive
the **same Spanish name**. Locale policy and the sanctioned i18n readers:
[the KB guide](../../docs/reference/knowledge-base.md).

Rules of engagement:

1. Translate against the KB's canonical English text (and, where the KB text
   is ambiguous, the band's registered source). Do not re-translate terms
   already fixed here — reuse them.
2. Rules that share a `binding.id` are semantically identical for the
   engines, but the *display name* is flavour and is not read by the engine.
   Enforce a shared Spanish name only when the English name also matches;
   when the English names differ (e.g. `skill.tough-as-steel` appears as
   "True Grit" and "Hard as Steel") each rule translates its own English
   name directly. When translating a band, check other bands with the same
   binding id for existing translations first. The pilot band's in-file
   Spanish text is the reference style (Caballero Andante = Questing Knight,
   Caballero Novel = Knight Errant, chequeo = test, 1D6 = D6).
3. Keep game-mechanical tokens untranslated: `D6`, `2D6`, `D66`, `XP`, `gc`,
   stat abbreviations (`M`, `WS`, `BS`, `S`, `T`, `W`, `I`, `A`, `Ld`),
   item/skill ids, and numeric bonuses (`+1 S` style stays `+1 S`).
4. `wyrdstone` stays as *wyrdstone* (proper setting noun), like *Mordheim*.

## Core terms

| English | Spanish |
| --- | --- |
| warband | banda |
| warband rating | valoración de la banda |
| hero | héroe |
| henchman / henchmen | secuaz / secuaces |
| hired sword | espada a sueldo |
| Dramatis Personae | Dramatis Personae |
| captain | capitán |
| leader | líder |
| champion | campeón |
| recruit | reclutar |
| roster | plantilla |
| treasury | tesorería |
| gold crowns (gc) | coronas de oro (gc) |
| upkeep | manutención |
| experience | experiencia |
| Troll Slayer | Matatrolles (invariable; plural also Matatrolles) |
| Dwarf Troll Slayer | Matatrolles Enano / Matatrolles Enanos |
| sight | visión |

## Rules vocabulary (seeded from the pilot band)

| English | Spanish |
| --- | --- |
| Virtue | Virtud (del Caballero) |
| Blessing | Bendición de la Dama del Lago (Lady of the Lake's Blessing) |
| Squire Retinue Limit | Límite de Escuderos |
| Questing Knight | Caballero Andante |
| Knight Errant | Caballero Novel |
| test | chequeo |
| Leadership test | chequeo de Liderazgo |
| close combat | combate cuerpo a cuerpo |
| armour save | salvación de armadura |
| ward save | salvación de pacto |
| injury | herida |
| out of action | fuera de combate |
| knocked down | derribado |
| stunned | aturdido |
| parry | parada |
| reroll | repetir (tirada) |
| charging | cargando |
| fear | miedo |
| terror | terror |
| hatred | odio |
| frenzy | frenesí |
| immunity | inmunidad |
| True Grit / true grit | Entereza |
| Tough as Steel / Hard as Steel | Duro como el acero |
| Battle Roar | Rugido de batalla |
| Bellowing Battle Roar | Rugido de batalla atronador |
| Expert Swordsman | Espadachín experto |
| Expert Swordsmen | Espadachines expertos |
| Hardened Skin | Piel endurecida |
| Ignore Pain | Ignorar el dolor |
| No Pain | Sin dolor |
| Iron Sinews | Tirones de hierro |
| Tremendous Strength | Fuerza tremenda |
| Shield Master | Maestro del escudo |
| Shield Mastery | Maestría con el escudo |
| Master of Blades | Maestro de las hojas |
| Combat Master | Maestro de combate |
| Art of Silent Death | Arte de la muerte silenciosa |
| Art of Unarmed Combat | Arte del combate desarmado |

Extend this table band by band; when a new band translation fixes a term,
add it here in the same commit so later bands inherit it.

## Equipment vocabulary

Canonical Spanish names for the item / equipment catalogues
(`catalog/mechanics/close-combat.yaml`, `catalog/items/*.yaml`). Names were
aligned against the printed Spanish Mordheim rulebook equipment section;
where the printed term differs from a literal translation, the printed term
wins. Exotic or setting weapons (Yambiya, Bo, Choppa, Katar, Draich, Squig,
Kusara Kama, Bagh Nakh, Misericordia, Stiletto…) keep their proper-noun
form untranslated.

### Weapons

| English | Spanish |
| --- | --- |
| Flail | Mayal |
| Morning Star | Mangual |
| Mace | Maza |
| Club | Garrote |
| Hammer | Martillo |
| Sword | Espada |
| Dagger | Daga |
| Axe | Hacha |
| Dwarf Axe | Hacha Enana |
| Double-handed Weapon | Arma a Dos Manos |
| Halberd | Alabarda |
| Pike | Pica |
| Spear | Lanza |
| Lance | Lanza de Caballería |
| Weeping Blades | Espadas Supurantes |
| Claw of the Old Ones | Garra de los Ancestrales |
| Steel Whip | Látigo de Acero |
| Beastlash | Látigo de Señor de las Bestias |
| Pirate Scourge | Azote |
| Ball and Chain | Bola y Cadena (the printed book spells it “Bola con Kadena”) |
| Fighting Claws | Garras de Combate |
| Sun Gauntlet | Guantelete Solar |
| Cutlass | Sable |
| Rapier | Estoque |
| Yambiya | Yambiya |
| Starsword | Espada Estelar |
| Starblade | Hoja Estelar |
| Main Gauche | Main Gauche |
| Barbed Whip | Látigo de Púas |
| Sunstaff | Báculo Solar |

### Ranged weapons

| English | Spanish |
| --- | --- |
| Handgun | Arcabuz |
| Duelling Pistol | Pistola Duelo |
| Double-barrelled Pistol | Pistola de Dos Cañones |
| Crossbow Pistol | Pistola Ballesta |
| Blunderbuss | Trabuco |
| Hochland Long Rifle | Rifle de Caza Hochland |
| Hunting Rifle | Rifle de Caza |
| Bow | Arco |
| Long Bow | Arco Largo |
| Short Bow | Arco Corto |
| Elf Bow | Arco Élfico |
| Crossbow | Ballesta |
| Repeater Crossbow | Ballesta de Repetición |
| Sling | Honda |
| Javelin | Jabalina |
| Pistol | Pistola |
| Carronade | Carronada |

### Armour and defences

| English | Spanish |
| --- | --- |
| Helmet | Yelmo (deliberate: the whole helmet family stays Yelmo — Yelmo de Olla, Yelmo de Hueso, Yelmo de Bronce — even though the printed book says Casco) |
| Cooking Pot Helmet | Yelmo de Olla |
| Buckler | Rodela |
| Shield | Escudo |
| Light Armour | Armadura Ligera |
| Heavy Armour | Armadura Pesada |
| Gromril Armour | Armadura de Gromril |
| Ithilmar Armour | Armadura de Ithilmar |
| Toughened Leathers | Cuero Endurecido |
| Ninja Robes | Túnica Ninja |
| Sea Dragon Cloak | Capa de Dragón Marino |
| Lucky Charm | Amuleto de la Suerte |
| Enchanted Skins | Pieles Encantadas |

### Materials, poisons and preparations

| English | Spanish |
| --- | --- |
| Gromril | Gromril |
| Ithilmar | Ithilmar |
| Dark Elf weapon | Arma Elfa Oscura |
| Black Venom | Veneno Negro |
| Dark Venom | Veneno Oscuro |
| Manbane | Matahombres |
| Wolfsbane | Acónito |
| Nightshade | Belladona |
| Bloodroot | Raíz de Sangre |
| Black Lotus | Loto Negro |
| Reptile Venom | Veneno de Reptil |
| Mad Cap Mushrooms | Hongos Sombrero Loco |
| Head-Splitter Mushrooms | Champiñones Partecabezas |
| Mandrake Root | Raíz de Mandrágora |
| Crimson Shade | Sombra Carmesí |
| Tears of Shallaya | Lágrimas de Shallaya |

### Miscellaneous equipment

| English | Spanish |
| --- | --- |
| Spy Glass | Catalejo |
| Telescope | Telescopio |
| Opulent Coach | Carroza Opulenta |
| Lamp of the Djinn | Lámpara de los Djinns |
| Tarot Cards | Cartas del Tarot |
| Vial of Pestilence | Vial de Pestilencia |
| Hardtack Biscuits | Galletas de Marinero |
| Garlic | Ajo |
| Torch | Antorcha |
| Lantern | Linterna |
| Lock Picks | Ganzúas |
| Compass | Brújula |
| Monkey's Paw | Pata de Mono |
| Flying Carpet | Alfombra Voladora |
| Mandrake Root | Raíz de Mandrágora |
| Caltrops | Abrojos |
| Fire Bomb | Bomba de Fuego |
| Sword Breaker | Rompe Espadas |
| Pavise | Pavesa |

### Scenario names

Names of the nine scenarios printed in the Spanish Mordheim rulebook (1999),
verified against the scanned Spanish edition; the remaining scenario names in
`catalog/campaign/scenarios.yaml` (supplements, Heraldo / Annual, homebrew)
keep their direct translations.

| English | Spanish (printed) |
| --- | --- |
| Defend the Find | Defender el Botín |
| Skirmish | Escaramuza |
| Wyrdstone Hunt | A la Búsqueda de Piedra Bruja |
| Breakthrough | ¡No Pasaréis! |
| Street Fight | Pelea Callejera |
| Chance Encounter | Encuentro Casual |
| Hidden Treasure | Tesoro Escondido |
| Occupy | Ocupar |
| Surprise Attack | Ataque Sorpresa |

Names of the seven multiplayer scenarios of the *Caos en las Calles* campaign
(by Mark Havener, first printed in Town Cryer and compiled in the Mordheim
Annual 2002), verified against the GW-Spain *Cargad* #23 Spanish printing and
the fan translation of the Annual 2002 hosted at La Ciudad de los Condenados
(the two agree on all seven headings).

| English | Spanish (Annual 2002 / Caos en las Calles) |
| --- | --- |
| Treasure Hunt | A la Búsqueda del Tesoro |
| Street Brawl | Bronca Callejera |
| The Lost Prince | El Príncipe Perdido |
| The Wizard's Mansion | La Mansión del Hechicero |
| The Pool | El Estanque |
| Ambush! | ¡Emboscada! |
| Monster Hunt | Cacería de Monstruos |

Remaining Town Cryer scenarios in `catalog/campaign/scenarios.yaml` are aligned
to the *El Heraldo de Mordheim* fan translation (La Ciudad de los Condenados
compilation, which mirrors the printed Town Cryer / Empire in Flames / Lustria
wording).

| English | Spanish (El Heraldo de Mordheim) |
| --- | --- |
| Finders Keepers | ¡Quien se lo encuentra se lo queda! |
| Mule Train | Recua de Mulas |
| Bounty Hunting | Cazarrecompensas |
| Lost in the Bogs | Perdidos en el pantano |
| The Thing in the Woods | ¡Algo se mueve en el bosque! |
| The Frenzied Mob | Turba Enfurecida |
| Island Hopping | Saltando de isla en isla |
| In the Dead of the Night | En mitad de la noche |
| Assault on the Rock | Asalto a La Roca |
| The Watchers | Los Observadores |
| Down at the Docks | Un paseo por los muelles |
| The Hunters Become the Hunted | El cazador cazado |
| The Night of the Headless One | La noche del Hombre sin Cabeza |
| Kidnapped | ¡Secuestrada! |
| Defend the Village! | Defiende al pueblo |
| Don't Wake the Giant | No despiertes al Gigante |
