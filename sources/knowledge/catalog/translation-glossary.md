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
