# -*- coding: utf-8 -*-
"""Ingest the seven remaining Miracle Workers prayer lists into magic-2b.yaml.

Adds the lores Prayers of Morr, Prayers of Myrmidia, Prayers of Ranald & Handrich,
Prayers of Shallya, Prayers of Taal & Rhya (mirror of the KB list), Prayers of
Ulric (MW variant of the KB list) and Prayers of Verena & Solkan to
``sources/2B/catalog/magic-2b.yaml`` (idempotent), updates the Priest
``lore_assignments`` and repairs the truncated Waterwalk English effect with the
full sentence from the recovered source PDF. Spanish translations follow the KB
glossary: Ghouls, Fuera de combate, derribado, Inmune a la Psicologia,
secuencia posterior a la batalla, tirada de Liderazgo.

Usage::

    python tools/ingestion/fill_2b_prayer_lores.py          # apply
    python tools/ingestion/fill_2b_prayer_lores.py --check  # dry run
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAGIC = ROOT / 'sources' / '2B' / 'catalog' / 'magic-2b.yaml'
PRIESTS = ROOT / 'sources' / '2B' / 'catalog' / 'hirelings' / 'miracle-workers-priests.yaml'
SOURCE_REF = {
    'manual': 'Liber Malefic (Miracle Workers, Werekin)',
    'url': 'https://www.scribd.com/document/241727651/Miracle-workers-in-Mordheim',
}
LORE_PAGES = {
    'morr': 12,
    'myrmidia': 13,
    'ranald-and-handrich': 14,
    'shallya': 15,
    'taal-and-rhya': 16,
    'ulric': 17,
    'verena-and-solkan': 18,
}

# ---------------------------------------------------------------- prayers ----
# (roll, name, es, difficulty, effect, effect_es)
MORR = [
    (1, 'Destroy Undead', 'Destruir No Muertos', 8,
     "Through a devout supplicant, by the hand of Morr, the Undead shall become as dust and ashes. The Priest of Morr must be touching an enemy Undead or Daemon model to use this prayer. If successful the foe immediately goes out of action (this only affects Zombies, Dire Wolves, Vampires etc). Ghouls, Possessed and Daemons affected by this prayer will immediately flee their full Movement away from the Priest of Morr.",
     "Por medio de un devoto suplicante, de la mano de Morr, los No Muertos se convertirán en polvo y cenizas. El Sacerdote de Morr debe estar en contacto con una miniatura No Muerta o Demoníaca enemiga para usar esta plegaria. Si tiene éxito, el enemigo queda inmediatamente Fuera de combate (solo afecta a Zombis, Lobos Dire, Vampiros, etc.). Los Ghouls, Poseídos y Demonios afectados por esta plegaria huirán inmediatamente todo su Movimiento alejándose del Sacerdote de Morr."),
    (2, 'Glimpse Ahead', 'Vislumbre del Porvenir', 9,
     "Amongst the church of Morr there are augurs who are said to be possessed of witch sight. It is said this trait can lead only to madness and as such the augurs are given a wider berth by fellow clergymen than their Morrian counterparts. The Priest is entitled to modify the result of a roll he makes by +1 or -1. Successful casting of this rite cannot be repeated during a battle or else the Priest would succumb to insanity! If the modifier has not been applied to the result of a roll during the battle, then it can be applied to a roll the Priest makes during the post battle sequence when either searching for a Rare item or visiting another location.",
     "Entre la iglesia de Morr hay augures de los que se dice que poseen vista de brujo. Se cuenta que este rasgo solo puede conducir a la locura y, por ello, los clérigos les dan un margen mayor que a sus homólogos morrianos. El Sacerdote tiene derecho a modificar el resultado de una tirada que realice en +1 o -1. El lanzamiento con éxito de este rito no puede repetirse durante una batalla, o el Sacerdote sucumbiría a la locura. Si el modificador no se ha aplicado al resultado de una tirada durante la batalla, puede aplicarse a una tirada que el Sacerdote realice durante la secuencia posterior a la batalla, ya sea al buscar un objeto Raro o al visitar otra localización."),
    (3, 'Preserve Corpse', 'Preservar el Cadáver', 5,
     "Those who fall become sanctified through funerary rites carried out the Priest and their soul freed, in the name of Morr, God of Death. The Priest of Morr may attempt to perform the prayer of sanctity on a model (friend or foe) who has been taken out of action. The Priest of Morr must be within 6\" of the model in question. If successful, the model may not be raised by a Necromancer.",
     "Los que caen son santificados mediante los ritos funerarios llevados a cabo por el Sacerdote y su alma es liberada, en nombre de Morr, Dios de la Muerte. El Sacerdote de Morr puede intentar realizar la plegaria de santidad sobre una miniatura (amiga o enemiga) que haya quedado Fuera de combate. El Sacerdote de Morr debe estar a 6\" o menos de la miniatura en cuestión. Si tiene éxito, la miniatura no podrá ser alzada por un Nigromante."),
    (4, 'Sign of the Raven', 'Signo del Cuervo', 7,
     "Priests of Morr must be steadfast in their resolution and as such must, above all else, have no fear of death. Dire circumstances are when the actions of a Morrian Priest can inspire warriors to perform heroic deeds, despite of certain doom. During the next close combat phase all friendly models with 6\" including the Priest, receive +1 on all rolls to wound.",
     "Los Sacerdotes de Morr deben ser firmes en su resolución y, como tales, deben tener, ante todo, ningún miedo a la muerte. Las circunstancias adversas son cuando las acciones de un Sacerdote morriano pueden inspirar a los guerreros a realizar gestas heroicas, a pesar de la perdición segura. Durante la siguiente fase de combate cuerpo a cuerpo, todas las miniaturas amigas a 6\" o menos, incluido el Sacerdote, reciben +1 en todas las tiradas para herir."),
    (5, 'Sleep of Death', 'Sueño de la Muerte', 10,
     "Servants of Morr are taught to divine and invoke the will of the God of Dreams, allowing them to interfere with the conscious minds of the living. The most learned of the church are capable of manipulating individuals in a dreamstate. Draw a 12\" line from the Priest. Any enemy models falling under the line fall asleep for D6 turns, unless a successful Leadership test is passed by each model. Roll a D6 for each model affected. Sleeping models are treated as being knocked down. Undead creatures are immune to the effects of this prayer.",
     "A los siervos de Morr se les enseña a adivinar e invocar la voluntad del Dios de los Sueños, lo que les permite interferir en las mentes conscientes de los vivos. Los más doctos de la iglesia son capaces de manipular a los individuos en estado de ensueño. Traza una línea de 12\" desde el Sacerdote. Las miniaturas enemigas que caigan bajo la línea se quedan dormidas durante D6 turnos, a menos que cada miniatura supere con éxito una tirada de Liderazgo. Tira un D6 por cada miniatura afectada. Las miniaturas dormidas se consideran derribadas. Las criaturas No Muertas son inmunes a los efectos de esta plegaria."),
    (6, 'Threshold Line', 'Línea Umbral', 8,
     "Charcoal is used after reciting an arcane phrase when the Priest is confronted by an apparition of Old Night to block its path. Mark a 4\" long line. This mark can be applied to a walkway, doorway, stair or other entry point to prevent an Undead creature from passing it. Any Undead creature must pass a Leadership test with a +1 modifier to the roll before it can pass the threshold marker, which lasts for the duration of the battle.",
     "Se usa carbón, tras recitar una frase arcana, cuando el Sacerdote se enfrenta a una aparición de la Vieja Noche, para bloquear su paso. Marca una línea de 4\" de largo. Esta marca puede aplicarse a un paso, una puerta, una escalera u otro punto de entrada para impedir que la cruce una criatura No Muerta. Cualquier criatura No Muerta debe superar una tirada de Liderazgo con un modificador de +1 a la tirada antes de poder cruzar el marcador umbral, que dura el resto de la batalla."),
]
MYRMIDIA = [
    (1, 'Blazing Sun', 'Sol Abrasador', 10,
     "For some Priestesses there is a unique view where the world can be brought into order with blinding flames of retribution. Myrmidia answers prayer with fury. Any models within 4\" of the Priestess suffer a Strength 3 hit with no armour saves allowed, and must pass a Leadership test or be knocked down (to extinguish their attire and half-blind by the blinding flames). A War-Priestess of Myrmidia is unaffected by the prayer.",
     "Para algunas Sacerdotisas existe una visión única en la que el mundo puede ser puesto en orden con llamas cegadoras de retribución. Myrmidia responde a la plegaria con furia. Las miniaturas a 4\" o menos de la Sacerdotisa sufren un impacto de Fuerza 3 sin tiradas de salvación por armadura permitidas, y deben superar una tirada de Liderazgo o quedar derribadas (para apagar su vestimenta y quedarse medio cegadas por las llamas deslumbrantes). Una Sacerdotisa de Guerra de Myrmidia no resulta afectada por la plegaria."),
    (2, 'Command the Legion', 'Comandar la Legión', 6,
     "Myrmidia lends her strength to the snarling words of the War-Priestess. As the vassal dictates solid tactics through prayer, the legionnaires become righteous. Any target warrior within the Priestess's line of sight receives +1 Leadership until the start of the players next turn.",
     "Myrmidia presta su fuerza a las palabras atronadoras de la Sacerdotisa de Guerra. Mientras la vasalla dicta tácticas sólidas mediante la plegaria, los legionarios se vuelven justos. Cualquier guerrero objetivo dentro de la línea de visión de la Sacerdotisa recibe +1 de Liderazgo hasta el comienzo del siguiente turno de los jugadores."),
    (3, 'Dismay Foe', 'Consternar al Enemigo', 9,
     "In her wrathful aspect the War Goddess can be invoked by a Priestess. All those heretics who gaze upon her just form in melee become utterly terrified. Any model attacking the Priestess in close combat this turn must pass a Leadership test or is unable to make any attacks. Undead are immune to the effects of this prayer.",
     "En su aspecto iracundo, la Diosa de la Guerra puede ser invocada por una Sacerdotisa. Todos aquellos herejes que contemplan su forma justa en la melé quedan completamente aterrados. Cualquier miniatura que ataque a la Sacerdotisa en combate cuerpo a cuerpo este turno debe superar una tirada de Liderazgo o no podrá realizar ningún ataque. Los No Muertos son inmunes a los efectos de esta plegaria."),
    (4, "Eagle's Vision", 'Visión del Águila', 8,
     "Entering a trance-like state the Priestess receives lucid visions from the Goddess. Interpreting answers to her prayers enables sly enemies in hiding to be detected. The War-Priestess can use this prayer to reveal any hidden warrior. A Priestess who has moved this turn is unable to use this prayer, and the prayer cannot be used if the Priestess is in close combat.",
     "Entrando en un estado de trance, la Sacerdotisa recibe visiones lúcidas de la Diosa. La interpretación de las respuestas a sus plegarias permite detectar a los enemigos astutos que estén ocultos. La Sacerdotisa de Guerra puede usar esta plegaria para revelar a cualquier guerrero oculto. Una Sacerdotisa que se haya movido este turno no puede usar esta plegaria, y la plegaria no puede usarse si la Sacerdotisa está en combate cuerpo a cuerpo."),
    (5, "Fury's Call", 'Llamada de la Ira', 9,
     "Passion can be found in prayer. The Priestess recants fervent sermons deposing hated despots in opposition of the War Goddess. All friendly models within 12\" not including the Priestess may re-roll their first missed attack during the next close combat phase.",
     "La pasión puede hallarse en la plegaria. La Sacerdotisa recita fervientes sermones depuestos contra los déspotas odiados en oposición a la Diosa de la Guerra. Todas las miniaturas amigas a 12\" o menos, sin incluir a la Sacerdotisa, pueden repetir su primer ataque fallido durante la siguiente fase de combate cuerpo a cuerpo."),
    (6, 'Vengeful Wrath', 'Ira Vengativa', 6,
     "Lifeblood of the wronged fuels a divine command of unbridled fury. The Priestess dictates vengeance upon all hated foes in a rite of retaliation. The War-Priestess may re-roll each failed roll to hit the next time that a round of hand-to-hand combat is being fought. Until her next close combat has started the Priestess must always charge if there are enemy models within charge range. The player has no choice in the matter – the Priestess will automatically declare a charge.",
     "La sangre de los agraviados alimenta un mandato divino de ira desbocada. La Sacerdotisa decreta la venganza sobre todos los enemigos odiados en un rito de represalia. La Sacerdotisa de Guerra puede repetir cada tirada para impactar fallida la próxima vez que se luche una ronda de combate cuerpo a cuerpo. Hasta que comience su próximo combate cuerpo a cuerpo, la Sacerdotisa siempre debe cargar si hay miniaturas enemigas dentro de alcance de carga. El jugador no tiene elección en el asunto: la Sacerdotisa declarará automáticamente una carga."),
]
RANALD = [
    (1, 'Bamboozle', 'Engañifa', 9,
     "Creating confusion is a talent the Priest has mastered! By craving the blessing of his fickle patron the Priest cajoles a creature short on wit to do his bidding. An enemy warrior within 12\" of the Priest must pass a Leadership test or during the next turn the warrior is controlled by the player who controls the Priest. The bamboozled warrior may do something which results in its harm, but may not attack itself. Large models, Daemons and Undead are immune to the effects of this prayer.",
     "¡Crear confusión es un talento que el Sacerdote ha dominado! Suplicando la bendición de su caprichoso patrón, el Sacerdote engatusa a una criatura corta de ingenio para que haga su voluntad. Un guerrero enemigo a 12\" o menos del Sacerdote debe superar una tirada de Liderazgo o, durante el siguiente turno, el guerrero será controlado por el jugador que controle al Sacerdote. El guerrero embaucado puede hacer algo que le resulte dañino, pero no puede atacarse a sí mismo. Las miniaturas Grandes, los Demonios y los No Muertos son inmunes a los efectos de esta plegaria."),
    (2, 'Bargain Hunter', 'Cazador de Chollos', 8,
     "Intoning this litany, the Priest divines a geographical area pinpointing a hotbed of quality merchandise. Opulent goods being quickly shifted in a price slash. If successfully cast then Common items must be reduced in price by one third of their cost during the next post battle sequence. Any fractions should be rounded down. Additionally, one Hero from the Priest's warband is guided to a Rare item of his choice which is charged at the normal cost. The maximum price for Common items purchased during the post battle sequence is altered to match the price slash, which consequently affects all players. The prayer cannot be used again once it has been successfully cast.",
     "Entonando esta letanía, el Sacerdote adivina un área geográfica señalando un hervidero de mercancía de calidad. Artículos opulentos que se despachan rápidamente en una rebaja de precios. Si se lanza con éxito, los artículos Comunes deben rebajarse un tercio de su coste durante la siguiente secuencia posterior a la batalla. Las fracciones se redondean hacia abajo. Además, un Héroe de la banda del Sacerdote es guiado hacia un objeto Raro de su elección, que se cobra a su coste normal. El precio máximo de los artículos Comunes comprados durante la secuencia posterior a la batalla se altera para ajustarse a la rebaja, lo que consecuentemente afecta a todos los jugadores. La plegaria no puede usarse de nuevo una vez se haya lanzado con éxito."),
    (3, 'Bountiful Fortune', 'Fortuna Espléndida', 10,
     "Comrades are gifted with uncanny luck when the Priest implores his deity for an upturn in the gang's fortunes. The Priest and any warriors from his warband within 12\" may each reverse the chances of success on a single dice roll or characteristic test. For example, if a warrior with a missile weapon requires a 6 to hit, then reversing the odds will mean that the warrior will hit his target on a roll of 1-5 instead. The prayer is effective until the start of the players next turn.",
     "Los camaradas son agraciados con una suerte insólita cuando el Sacerdote implora a su deidad un cambio de fortuna para la banda. El Sacerdote y cualquier guerrero de su banda a 12\" o menos pueden invertir cada uno las probabilidades de éxito de una única tirada de dado o tirada de característica. Por ejemplo, si un guerrero con un arma de proyectil necesita un 6 para impactar, invertir las probabilidades significará que el guerrero impactará a su objetivo con un resultado de 1-5. La plegaria es efectiva hasta el comienzo del siguiente turno de los jugadores."),
    (4, 'Open', 'Abrir', 7,
     "Few doors are considered closed to clergymen. It is joked that this Priest can walk through walls! The Priest petitions for safe passage to override any barrier. A lock, bolt or latch becomes unlocked by the Priest. This includes magical locks. The Priest model must be touching the lock to use this prayer.",
     "Pocas puertas se consideran cerradas para los clérigos. Se bromea diciendo que este Sacerdote puede atravesar paredes. El Sacerdote pide paso seguro para superar cualquier barrera. Una cerradura, cerrojo o pestillo queda abierto por el Sacerdote. Esto incluye las cerraduras mágicas. La miniatura del Sacerdote debe estar en contacto con la cerradura para usar esta plegaria."),
    (5, 'Rumour of Bounty, Rumour of Dearth', 'Rumor de Abundancia, Rumor de Escasez', 9,
     "The Priest requisitions his lord to assist in manipulating priced commodities. If successfully cast then all equipment of one type may be halved in price (ie, bows cost 5 gold crowns) or a Rare item becomes Common during the next post battle phase. Alternatively, all equipment of one type may be doubled in price (ie, bows cost 20 gold crowns) or a Common item becomes Rare 10. All warbands are affected by the rumour during the post battle sequence. The prayer cannot be used again once it has been successfully cast.",
     "El Sacerdote solicita a su señor que le asista en la manipulación de las mercancías con precio. Si se lanza con éxito, todo el equipo de un tipo puede ver su precio reducido a la mitad (es decir, los arcos cuestan 5 coronas de oro) o un objeto Raro se convierte en Común durante la siguiente fase posterior a la batalla. Alternativamente, todo el equipo de un tipo puede ver su precio duplicado (es decir, los arcos cuestan 20 coronas de oro) o un artículo Común se convierte en Raro 10. Todas las bandas se ven afectadas por el rumor durante la secuencia posterior a la batalla. La plegaria no puede usarse de nuevo una vez se haya lanzado con éxito."),
    (6, 'Stealth', 'Sigilo', 5,
     "Calling upon divine favour, bountiful servants quickly develop a knack of going unnoticed and evading conflict whenever it suits them. The Priest becomes hidden until the start of the players next turn. Any attempts made to detect or spot the Priest will automatically fail unless they are achievable through magical means.",
     "Invocando el favor divino, los pródigos siervos desarrollan rápidamente una habilidad para pasar desapercibidos y evitar el conflicto cuando les conviene. El Sacerdote se oculta hasta el comienzo del siguiente turno de los jugadores. Cualquier intento de detectar o avistar al Sacerdote fallará automáticamente a menos que pueda lograrse por medios mágicos."),
]
SHALLYA = [
    (1, 'Cure Disease', 'Curar Enfermedad', 8,
     "The Priestess petitions Shallya to remedy those unfortunate enough to have been struck low by the sickness of plague. The Priestess or any model in contact with the Priestess is healed from the effects of a disease. The disease is removed from the subject model and all ill-effects are ignored.",
     "La Sacerdotisa implora a Shallya que remedie a aquellos desafortunados que hayan sido abatidos por la enfermedad de la plaga. La Sacerdotisa o cualquier miniatura en contacto con la Sacerdotisa queda sanada de los efectos de una enfermedad. La enfermedad se elimina de la miniatura afectada y todos sus efectos nocivos se ignoran."),
    (2, 'Cure Wounds', 'Curar Heridas', 6,
     "Beseeching the Mercy Goddess to restore health of a fallen warrior is the widely done duty of the Priestess. The Priestess or any model in contact with the Priestess immediately recovers 1 Wound.",
     "Implorar a la Diosa de la Misericordia que restaure la salud de un guerrero caído es el deber ampliamente realizado de la Sacerdotisa. La Sacerdotisa o cualquier miniatura en contacto con la Sacerdotisa recupera inmediatamente 1 Herida."),
    (3, 'Golden Tears', 'Lágrimas Doradas', 10,
     "Tears of purity shower upon the dying as the Priestess entreats Shallya for a merciful pardon. This prayer can only be used if the Priestess is able to reach the spot where a warrior was taken out of action in the previous turn. If successfully cast, the Priestess has healed the warrior. Return the model to play with 1 Wound, in the knocked down position.",
     "Lágrimas de pureza llueven sobre los moribundos mientras la Sacerdotisa implora a Shallya un indulto misericordioso. Esta plegaria solo puede usarse si la Sacerdotisa es capaz de alcanzar el punto donde un guerrero quedó Fuera de combate en el turno anterior. Si se lanza con éxito, la Sacerdotisa ha sanado al guerrero. Devuelve la miniatura al juego con 1 Herida, en la posición derribada."),
    (4, 'Purify', 'Purificar', 9,
     "The Cleric displays her abhorrence of the Plague God with an anathema to his polluting servants. The Priestess shrivels vile followers of Onogal with the purifying power of Shallya. Any warriors from a Carnival of Chaos warband or other servants of Onogal the Fly Lord within 24\" of the Priestess lose D6 Wounds, regardless of Toughness or armour. All affected warriors reduced to 0 Wounds must also pass a Leadership test or be treated as being stunned.",
     "La Clériga muestra su aborrecimiento del Dios de la Plaga con un anatema contra sus siervos contaminantes. La Sacerdotisa marchita a los viles seguidores de Onogal con el poder purificador de Shallya. Los guerreros de una banda de la Carnival of Chaos u otros siervos de Onogal el Señor de las Moscas a 24\" o menos de la Sacerdotisa pierden D6 Heridas, sin importar Resistencia ni armadura. Todos los guerreros afectados reducidos a 0 Heridas deben superar además una tirada de Liderazgo o se los considera aturdidos."),
    (5, "Shallya's Endurance", 'Aguante de Shallya', 7,
     "In chanting a rite of resilience the Sister delivers the power of Shallya, boosting the vitality of a worthy defender. At her decree the champion endures the pain. The Priestess or any model in contact with the Priestess receives +1 Toughness during the next round of close combat.",
     "Al entonar un rito de resiliencia, la Hermana canaliza el poder de Shallya, impulsando la vitalidad de un defensor digno. Por su decreto, el campeón aguanta el dolor. La Sacerdotisa o cualquier miniatura en contacto con la Sacerdotisa recibe +1 de Resistencia durante la siguiente ronda de combate cuerpo a cuerpo."),
    (6, 'Vestment of Purity', 'Vestidura de Pureza', 10,
     "A miracle of faith as the Priestess weathers the stream of corruption. Heretic lieutenants of the Plague Lord yield before the overwhelming purity of Shallya. The Priestess becomes immune to all poisons and diseases. In addition, Daemons, warriors from a Carnival of Chaos warband or any other servants of Onogal the Fly Lord must pass a Leadership test taken at -2 Leadership to charge, shoot missiles at or use magic attacks against the Priestess. The effects of this prayer last until the Priestess attacks an enemy model in close combat.",
     "Un milagro de fe mientras la Sacerdotisa resiste la corriente de corrupción. Los tenientes herejes del Señor de la Plaga ceden ante la abrumadora pureza de Shallya. La Sacerdotisa se vuelve inmune a todos los venenos y enfermedades. Además, los Demonios, los guerreros de una banda de la Carnival of Chaos o cualquier otro siervo de Onogal el Señor de las Moscas deben superar una tirada de Liderazgo con -2 de Liderazgo para cargar, disparar proyectiles o usar ataques mágicos contra la Sacerdotisa. Los efectos de esta plegaria duran hasta que la Sacerdotisa ataque a una miniatura enemiga en combate cuerpo a cuerpo."),
]
TAAL = [
    (1, "Stag's Leap", 'Salto del Ciervo', 7,
     "Many of Taal's priests wear a stag skull as a symbol of their devotion and the Forest Lord's power can be used to emulate the speed and beauty of this magnificent beast. The Priest of Taal may immediately move anywhere within 9\", including into base-contact with the enemy, in which case he counts as charging and gains a +1 Strength to his first round of attacks. If he engages a fleeing enemy, in the close combat phase he will score one automatic hit at +1 Strength and then his opponent will flee again.",
     "Muchos de los sacerdotes de Taal llevan un cráneo de ciervo como símbolo de su devoción y el poder del Señor del Bosque puede usarse para emular la velocidad y belleza de esta magnífica bestia. El Sacerdote de Taal puede moverse inmediatamente a cualquier punto a 9\" o menos, incluido el contacto base con el enemigo, en cuyo caso cuenta como carga y gana +1 de Fuerza en su primera ronda de ataques. Si alcanza a un enemigo en huida, en la fase de combate cuerpo a cuerpo conseguirá un impacto automático con +1 de Fuerza y después su oponente volverá a huir."),
    (2, 'Blessed Ale', 'Cerveza Bendecida', 5,
     "Like his brother Ulric, Taal has a great appetite for the strong ales of the Northern Empire. During the summer equinox each Priest opens one keg of ale (at least!) in Taal's honour. Drinking a flask of Taal-blessed ale (the priest is assumed to carry as many flasks as are needed) may heal any one model within 2\" of the Priest (including himself). The warrior is restored to his full quota of Wounds. In addition, any living enemy models (not Undead or Possessed) within 2\" of the Priest will lose 1 Attack during the next round of combat due to the potent fumes of the ale.",
     "Como su hermano Ulric, Taal tiene un gran apetito por las cervezas fuertes del Imperio del Norte. Durante el solsticio de verano cada Sacerdote abre un barril de cerveza (¡al menos!) en honor de Taal. Beber un frasco de cerveza bendecida por Taal (se asume que el sacerdote lleva tantos frascos como hagan falta) puede sanar a una miniatura cualquiera a 2\" o menos del Sacerdote (incluido él mismo). El guerrero recupera toda su cuota de Heridas. Además, cualquier miniatura enemiga viva (no No Muerta ni Poseída) a 2\" o menos del Sacerdote perderá 1 Ataque durante la siguiente ronda de combate debido a los potentes vapores de la cerveza."),
    (3, 'Bears Paw', 'Pata de Oso', 7,
     "Many an armoured knight has been knocked to the ground by the surprising Strength of the followers of Taal. Although traditionally called 'Bears Paw' this spell is sometimes referred to as 'Moose Breath' by those who have felt its power. The Priest invokes the blessing of Taal on himself or a single friendly model within 6\". The target receives a bonus of +2 to his Strength until the Priest's next turn.",
     "A más de un caballero armado lo han derribado al suelo la sorprendente Fuerza de los seguidores de Taal. Aunque tradicionalmente se llama 'Pata de Oso', este hechizo a veces es llamado 'Aliento de Alce' por quienes han sentido su poder. El Sacerdote invoca la bendición de Taal sobre sí mismo o sobre una única miniatura amiga a 6\" o menos. El objetivo recibe un bonus de +2 a su Fuerza hasta el siguiente turno del Sacerdote."),
    (4, 'Earthshudder', 'Sacudida de la Tierra', 9,
     "Taal's domain includes both the earth and the skies and his power can reach out even into the dark streets of Mordheim. When his name is invoked three times and the blood of an eagle is poured on the ground, the Lord of the Wild will cause thunder to rumble and the earth to shake. The spell is cast on a single building within 4\". Any enemy models touching the building will suffer a single Strength 3 hit. In addition the building will collapse and any models on it will count as having fallen to the ground (for example a model falling 5\" to the tabletop must pass two Initiative tests to avoid taking D3 Strength 5 hits.) Remove the terrain feature from the board for the rest of the game.",
     "El dominio de Taal incluye tanto la tierra como los cielos y su poder puede alcanzar incluso las calles oscuras de Mordheim. Cuando su nombre se invoca tres veces y la sangre de un águila se derrama en el suelo, el Señor de lo Salvaje hará retumbar el trueno y temblar la tierra. El hechizo se lanza sobre un único edificio a 4\" o menos. Las miniaturas enemigas que toquen el edificio sufrirán un único impacto de Fuerza 3. Además, el edificio se derrumbará y cualquier miniatura sobre él contará como caída al suelo (por ejemplo, una miniatura que caiga 5\" hasta la superficie de juego debe superar dos tiradas de Iniciativa para evitar sufrir D3 impactos de Fuerza 5). Retira la escenografía del tablero por el resto de la partida."),
    (5, 'Tanglefoot', 'Pies Enredados', 8,
     "It is said that when Taal walked the earth, living things would spring up behind him as he passed. A portion of his power can be summoned by his followers to help regrow forests and aid in the return of the land to its natural state. Plants, vines and even small trees burst forth from the earth, hindering all those who attempt to move through them. All models (friend as well as foe) with the exception of friendly Taalites within 12\" of the Priest can only move at half their Movement until the next shooting phase.",
     "Se dice que cuando Taal caminaba por la tierra, los seres vivos brotaban a su paso. Una parte de su poder puede ser invocada por sus seguidores para ayudar a reforestar y contribuir a que la tierra vuelva a su estado natural. Plantas, enredaderas e incluso pequeños árboles brotan de la tierra, dificultando el avance de todos los que intenten atravesarlos. Todas las miniaturas (amigas y enemigas), con la excepción de los taalitas amigas, a 12\" o menos del Sacerdote solo pueden moverse a la mitad de su Movimiento hasta la siguiente fase de disparo."),
    (6, 'Summon Squirrels', 'Invocar Ardillas', 7,
     "Taal is the master of all beasts both great and small. Those who anger him may be mauled by a mountain lion or drowned in a flood caused by an angry beaver. With this spell the Priest invokes the wrath of the Lord of Beasts, summoning forth dozens upon dozens of enraged squirrels. The furious rodents will assault one enemy within 12\" of the Priest, crawling inside the warrior's clothing and armour, pelting him with nuts and causing numerous tiny bites and welts. The target suffers 2D6 Strength 1 hits. No armour saves allowed.",
     "Taal es el señor de todas las bestias, grandes y pequeñas. Quienes le enfurecen pueden ser despedazados por un puma o ahogados en una inundación causada por un castor furioso. Con este hechizo el Sacerdote invoca la ira del Señor de las Bestias, convocado decenas y decenas de ardillas enfurecidas. Los furiosos roedores asaltan a un enemigo a 12\" o menos del Sacerdote, arrastrándose dentro de la ropa y la armadura del guerrero, apedreándolo con nueces y causando numerosos mordiscos diminutos y ronchas. El objetivo sufre 2D6 impactos de Fuerza 1. Sin tiradas de salvación por armadura permitidas."),
]
ULRIC = [
    (1, "Frost's Bite", 'Mordisco de Escarcha', 7,
     "The snarling Wolf-Priest prays to Ulric to freeze the blood in the body of his enemy. An enemy model within 9\" must pass a Toughness test or loses 1 Wound ignoring armour saves. Furthermore, the target is unable to take any actions during the opponents next turn. If the test is failed, the target may still make defensive actions such as Dodge, and defend itself in combat.",
     "El rugiente Sacerdote Lobo reza a Ulric para congelar la sangre en el cuerpo de su enemigo. Una miniatura enemiga a 9\" o menos debe superar una tirada de Resistencia o pierde 1 Herida, ignorando las tiradas de salvación por armadura. Además, el objetivo no puede realizar ninguna acción durante el siguiente turno del oponente. Si falla la tirada, el objetivo puede seguir realizando acciones defensivas como Esquiva y defenderse en combate."),
    (2, 'Heart of the Wolf', 'Corazón del Lobo', 8,
     "The Wolf-Priest's prayer is answered as an ear-shattering inhuman howl roars from his throat. For the duration of the battle, all members of the Priest's warband are immune to fear and All Alone tests as they feel the presence of their god. Additionally, the leader of the warband receives +1 Leadership on all Rout Tests.",
     "La plegaria del Sacerdote Lobo es respondida mientras un aullido inhumano que ensordece resuena desde su garganta. Durante el resto de la batalla, todos los miembros de la banda del Sacerdote son inmunes a las tiradas de Miedo y de Todo Solo, ya que sienten la presencia de su dios. Además, el líder de la banda recibe +1 de Liderazgo en todas las tiradas de Desbandada."),
    (3, 'Hoarfrost Thews', 'Músculos de Escarcha', 8,
     "An unnatural chill ripples through the musculature of the Priest as a frost forms upon the flesh across his entire body. A chilling cold aura surrounds him. The Priest is immune to exposure caused by freezing conditions for the remainder of the battle. This includes the ill effects of all types of cold weather and the Priest is immune to the effects of any magical attacks or spells which refer to the cold such as snow, frost, ice and hail. All models within 2\" of the Priest without a cloak or winter furs suffers -1 Leadership and -1 Initiative. However, Initiative cannot fall below 1. Undead models are immune to the chilling aura's effects.",
     "Un escalofrío antinatural recorre la musculatura del Sacerdote mientras una escarcha se forma sobre la carne de todo su cuerpo. Un aura gélida lo rodea. El Sacerdote es inmune a la exposición causada por condiciones heladoras durante el resto de la batalla. Esto incluye los efectos nocivos de todo tipo de clima frío, y el Sacerdote es inmune a los efectos de cualquier ataque mágico o hechizo que se refiera al frío, como nieve, escarcha, hielo y granizo. Todas las miniaturas a 2\" o menos del Sacerdote sin capa ni pieles de invierno sufren -1 de Liderazgo y -1 de Iniciativa. No obstante, la Iniciativa no puede quedar por debajo de 1. Las miniaturas No Muertas son inmunes a los efectos del aura gélida."),
    (4, 'Ice Storm', 'Tormenta de Hielo', 10,
     "The Priest snarls an invocation that releases a fierce storm of lashing ice to cripple Ulric's enemies. An enemy model within 24\" of the Priest is lashed by ice, receiving a Strength 5 hit. The target, along with any models (friend or foe) within 2\" of the target, must take a Toughness test. Any model which fails the test is treated as being stunned.",
     "El Sacerdote profiere una invocación que desata una feroz tormenta de hielo azotador para lisiar a los enemigos de Ulric. Una miniatura enemiga a 24\" o menos del Sacerdote es azotada por el hielo, sufriendo un impacto de Fuerza 5. El objetivo, junto con cualquier miniatura (amiga o enemiga) a 2\" o menos del objetivo, debe superar una tirada de Resistencia. Cualquier miniatura que falle la tirada se considera aturdida."),
    (5, "The Snow King's Decree", 'El Decreto del Rey de las Nieves', 10,
     "Scornful words are bellowed by the Wolf-Priest in tribute to Ulric's hatred for cowardice, weakness and dishonour. The decree of Ulric punishes the craven. Silvery, freezing fire erupts from one target within 6\", and causes one Strength 8 hit. Any devout Ulrican warriors including brave Middenheimers are assumed to be immune to the spell. If the chosen target is a warrior then he may avoid the effects of the prayer by successfully passing a Leadership test. Armour offers no protection against the Snow King's decree.",
     "Palabras desdeniosas son proclamadas por el Sacerdote Lobo en tributo al odio de Ulric por la cobardía, la debilidad y la deshonra. El decreto de Ulric castiga a los cobardes. Un fuego plateado y congelante irrumpe desde un objetivo a 6\" o menos, y causa un impacto de Fuerza 8. Se asume que cualquier guerrero ulricano devoto, incluidos los valientes Middenheimers, es inmune al hechizo. Si el objetivo elegido es un guerrero, puede evitar los efectos de la plegaria superando con éxito una tirada de Liderazgo. La armadura no ofrece protección contra el decreto del Rey de las Nieves."),
    (6, 'Wild Pack', 'Manada Salvaje', 8,
     "The Wolf-Priest howls angry prayers to Ulric, leading allies to bristle with menace. All of this unrestrained violence unsettles all except the steeliest of foes. All enemy models within 12\" suffer a -1 penalty to their Weapon Skill in the next close combat phase if they are attacking warriors from the Priest's warband. This prayer does not affect Undead.",
     "El Sacerdote Lobo aúlla plegarias furiosas a Ulric, llevando a los aliados a erizarse de amenaza. Toda esta violencia desatada inquieta a todos salvo a los enemigos más templados. Todas las miniaturas enemigas a 12\" o menos sufren una penalización de -1 a su Habilidad de Armas en la siguiente fase de combate cuerpo a cuerpo si atacan a guerreros de la banda del Sacerdote. Esta plegaria no afecta a los No Muertos."),
]
VERENA = [
    (1, 'Preserve the Balance', 'Preservar el Equilibrio', 8,
     "The Priest's prayers beg to mete out justice to all those who dare to defy a sanctified servant of justice. Until the following turn, any vicious act committed against the Priest is also inflicted upon the perpetrator of the offence. For example, if the Priest suffered a Strength 4 hit from an assailant then the same Strength hit would apply to the attacker, or if the Priest lost 1 Wound then the warrior who inflicted the wound would lose 1 Wound also. The same conditions apply in reverse when another model is being attacked by the Priest, aside from through the use of this prayer.",
     "Las plegarias del Sacerdote imploran impartir justicia a todos aquellos que se atrevan a desafiar a un siervo santificado de la justicia. Hasta el siguiente turno, cualquier acto cruel cometido contra el Sacerdote se inflige también al perpetrador de la ofensa. Por ejemplo, si el Sacerdote sufrió un impacto de Fuerza 4 de un agresor, el mismo impacto de Fuerza se aplicaría al atacante, o si el Sacerdote perdió 1 Herida, el guerrero que la infligió también perdería 1 Herida. Las mismas condiciones se aplican a la inversa cuando otra miniatura es atacada por el Sacerdote, salvo mediante el uso de esta plegaria."),
    (2, 'Retribution', 'Retribución', 9,
     "The Priest delivers a recital to punish guilty scum using the total power of Law. An enemy warrior within 12\" of the Priest must take a Leadership test with a +2 modifier. If the test is failed then during the next close combat phase the warrior loses half of his Attacks. In addition, the warrior's Movement is halved. Any fractions are rounded up.",
     "El Sacerdote pronuncia un recital para castigar a la chusma culpable usando el poder total de la Ley. Un guerrero enemigo a 12\" o menos del Sacerdote debe superar una tirada de Liderazgo con un modificador de +2. Si falla la tirada, durante la siguiente fase de combate cuerpo a cuerpo el guerrero pierde la mitad de sus Ataques. Además, el Movimiento del guerrero se reduce a la mitad. Las fracciones se redondean hacia arriba."),
    (3, 'Shackles of Law', 'Grilletes de la Ley', 6,
     "Invisible shackles immobilise a character with flagrant disregard for regulations as the Priest works magical power into the binding invocation. An enemy warrior within 6\" of the Priest becomes immobile this turn unless he successfully passes a Leadership test. If the test is failed the warrior cannot move, attack or cast spells during the players next turn.",
     "Grilletes invisibles inmovilizan a un personaje con un desprecio flagrante por las normas mientras el Sacerdote infunde poder mágico en la invocación de sujeción. Un guerrero enemigo a 6\" o menos del Sacerdote queda inmóvil este turno a menos que supere con éxito una tirada de Liderazgo. Si falla la tirada, el guerrero no puede moverse, atacar ni lanzar hechizos durante el siguiente turno de los jugadores."),
    (4, 'Sword of Justice', 'Espada de la Justicia', 8,
     "The weapon of every Priest of Law is the sword. When all other options fail a prayer can empower the weapon turning it into a divine instrument of justice. The Priest receives +1 Weapon Skill on attacks he makes in the next close combat phase. In addition, the Priest will cause a critical hit on a roll to wound of 5-6 instead of just 6.",
     "El arma de todo Sacerdote de la Ley es la espada. Cuando todas las demás opciones fallan, una plegaria puede potenciar el arma convirtiéndola en un instrumento divino de la justicia. El Sacerdote recibe +1 de Habilidad de Armas en los ataques que realice en la siguiente fase de combate cuerpo a cuerpo. Además, el Sacerdote causará un golpe crítico con una tirada para herir de 5-6 en lugar de solo 6."),
    (5, 'The Blind Maiden', 'La Doncella Ciega', 9,
     "Truth can be divined in a prayer that allows the Priest to find it when blinded. The Priest spots any hidden warriors within line of sight and ignores any penalty for effects like weather, darkness including any tunnel fighting in underground scenarios, or any blinding magical effects. In addition, the Priest ignores psychology tests for being All Alone. The effects of the prayer last until the players next shooting phase.",
     "La verdad puede adivinarse en una plegaria que permite al Sacerdote hallarla incluso ciego. El Sacerdote avista a cualquier guerrero oculto dentro de su línea de visión e ignora cualquier penalización por efectos como el clima, la oscuridad —incluida cualquier lucha en túneles en escenarios subterráneos— o cualquier efecto mágico deslumbrante. Además, el Sacerdote ignora las tiradas de psicología por estar Todo Solo. Los efectos de la plegaria duran hasta la siguiente fase de disparo de los jugadores."),
    (6, 'Trial by Fire', 'Juicio por el Fuego', 10,
     "In an ultimate test of innocence a party found guilty by the Priest of grave injustice will be engulfed in divine flames. An enemy warrior within 6\" of the Priest suffers a Strength 6 hit. The warrior is treated as being set on fire from the flaming attack.",
     "En una prueba suprema de inocencia, el accused hallado culpable por el Sacerdote de una grave injusticia será envuelto en llamas divinas. Un guerrero enemigo a 6\" o menos del Sacerdote sufre un impacto de Fuerza 6. El guerrero se considera incendiado por el ataque de fuego."),
]
LISTS = {
    'morr': MORR,
    'myrmidia': MYRMIDIA,
    'ranald-and-handrich': RANALD,
    'shallya': SHALLYA,
    'taal-and-rhya': TAAL,
    'ulric': ULRIC,
    'verena-and-solkan': VERENA,
}
LORE_META = {
    'morr': ('Prayers of Morr', 'Plegarias de Morr', 'El Sacerdote de Morr elige al azar una plegaria de esta lista.', 'hireling.priest.priest-of-morr'),
    'myrmidia': ('Prayers of Myrmidia', 'Plegarias de Myrmidia', 'La Sacerdotisa de Guerra de Myrmidia elige al azar una plegaria de esta lista.', 'hireling.priest.war-priestess-of-myrmidia'),
    'ranald-and-handrich': ('Prayers of Ranald & Handrich', 'Plegarias de Ranald y Handrich', 'El Sacerdote Tramposo de Ranald elige al azar una plegaria de esta lista; en Marienburg, los sacerdotes de Handrich (Dios del Comercio) pueden usar la misma lista.', 'hireling.priest.trickster-priest-of-ranald'),
    'shallya': ('Prayers of Shallya', 'Plegarias de Shallya', 'La Sacerdotisa de Shallya elige al azar una plegaria de esta lista.', 'hireling.priest.priestess-of-shallya'),
    'taal-and-rhya': ('Prayers of Taal & Rhya', 'Plegarias de Taal y Rhya', 'El Sacerdote Druida de Taal elige al azar una plegaria de esta lista.', 'hireling.priest.druid-priest-of-taal'),
    'ulric': ('Prayers of Ulric (Miracle Workers)', 'Plegarias de Ulric (Miracle Workers)', 'El Sacerdote Lobo de Ulric elige al azar una plegaria de esta lista.', 'hireling.priest.wolf-priest-of-ulric'),
    'verena-and-solkan': ('Prayers of Verena & Solkan', 'Plegarias de Verena y Solkan', 'El Sacerdote de Verena elige al azar una plegaria de esta lista; los guías de promoción describen a los bélicos sacerdotes de Solkan, que usan la misma lista.', 'hireling.priest.priest-of-verena'),
}
WATERWALK_OLD = ("Floating on a raft of true belief, the Priest solicits the power of faith in a majestic "
                 "display that defies all logic. In the next movement phase the Priest is able to walk on water, "
                 "marsh and swampland as if it were solid ground.")
WATERWALK_NEW = ("Floating on a raft of true belief, the Priest solicits the power of faith in a majestic "
                 "display that defies all logic. In the next movement phase the Priest is able to walk on water, "
                 "marsh and swampland as if it were firm ground. The effects of this prayer last until the "
                 "Priest returns to any solid platform.")


def build_lore(key: str) -> dict:
    en_name, es_name, note_es, _priest = LORE_META[key]
    spells = []
    for roll, name, es, diff, eff, eff_es in LISTS[key]:
        spells.append({
            'id': f'spell.prayers-of-{key}.{slug(name)}',
            'roll': str(roll),
            'name': name,
            'name_i18n': {'es': es},
            'difficulty': diff,
            'effect': eff,
            'effect_i18n': {'es': eff_es},
        })
    lore = {
        'id': f'lore.prayers-of-{key}',
        'name': en_name,
        'name_i18n': {'es': es_name},
        'note': note_es,
        'source_refs': [dict(SOURCE_REF, printed_page=LORE_PAGES[key],
                             section=f'Prayers of {en_name}')],
        'spells': spells,
    }
    return lore


def slug(name: str) -> str:
    out = []
    for ch in name.lower():
        if ch.isalnum():
            out.append(ch)
        else:
            out.append('-')
    s = ''.join(out)
    while '--' in s:
        s = s.replace('--', '-')
    return s.strip('-')


def main() -> int:
    apply = '--check' not in sys.argv
    data = yaml.safe_load(MAGIC.read_text(encoding='utf-8'))
    # Repair state from earlier runs: the MW Ulric variant must not reuse the KB id
    for lore in data['lores']:
        if lore['id'] == 'lore.prayers-of-ulric' and any(s['name'] == "Frost's Bite" for s in lore.get('spells', [])):
            lore['id'] = 'lore.prayers-of-ulric-miracle-workers'
            lore['variant_of_lore'] = 'lore.prayers-of-ulric'
            print('  repaired: MW Ulric variant renamed to lore.prayers-of-ulric-miracle-workers')
    seen = set()
    uniq = []
    for lore in data['lores']:
        if lore['id'] in seen:
            print('  dedup: removed duplicate', lore['id'])
            continue
        seen.add(lore['id'])
        uniq.append(lore)
    data['lores'] = uniq
    existing = {l['id'] for l in data['lores']}
    added = []
    for key in LISTS:
        target_id = 'lore.prayers-of-ulric-miracle-workers' if key == 'ulric' else f'lore.prayers-of-{key}'
        if target_id in existing:
            print(f'  skip (exists): {target_id}')
            continue
        lore = build_lore(key)
        if key == 'taal-and-rhya':
            lore['mirror_of_lore'] = 'lore.prayers-of-taal'
            lore['note'] += ' MIRROR of the KB lore.prayers-of-taal: the six spells and their difficulties are identical (Stag\'s Leap D7, Blessed Ale D5, Bears Paw D7, Earthshudder D9, Tanglefoot D8, Summon Squirrels D7); at promotion, verify and map to the existing lore instead of duplicating it.'
        elif key == 'ulric':
            lore['id'] = 'lore.prayers-of-ulric-miracle-workers'
            lore['variant_of_lore'] = 'lore.prayers-of-ulric'
            lore['note'] += ' VARIANT of the KB lore.prayers-of-ulric (Snow Squall D6, Hammerschlag D10, Bloodlust D7, Wolf\'s Hunger D7, Ulric\'s Howl D10, Call of Ulric D10): the Miracle Workers chapter rewrites the Wolf-Priest prayers completely (Frost\'s Bite D7, Heart of the Wolf D8, Hoarfrost Thews D8, Ice Storm D10, The Snow King\'s Decree D10, Wild Pack D8). No spell overlaps; the MW list replaces the Town Cryer list for this profile only. At promotion: keep both lores and route lore_assignments of the MW Wolf-Priest to this variant.'
        elif key == 'verena-and-solkan':
            lore['note'] += ' The chapter notes the Warrior-Priests of Solkan chant from the same list; a Solkan-only variant is not printed.'
        added.append(lore)

    # Waterwalk full-text repair
    ww_fixed = False
    for lore in data['lores']:
        if lore['id'] != 'lore.prayers-of-manann':
            continue
        for sp in lore['spells']:
            if sp['id'] == 'spell.prayers-of-manann.waterwalk' and sp['effect'] == WATERWALK_OLD:
                sp['effect'] = WATERWALK_NEW
                sp['effect_i18n']['es'] = ('Flotando sobre una balsa de fe verdadera, el Sacerdote solicita el poder de la fe '
                                           'en una exhibición majestuosa que desafía toda lógica. En la siguiente fase de '
                                           'movimiento el Sacerdote puede caminar sobre el agua, la marisma y el terreno '
                                           'pantanoso como si fuera tierra firme. Los efectos de esta plegaria duran hasta '
                                           'que el Sacerdote regresa a cualquier plataforma sólida.')
                ww_fixed = True

    # Priest lore_assignments inside the profiles file (list field, one lore id)
    DESIRED = {
        'hireling.priest.priest-of-morr': 'lore.prayers-of-morr',
        'hireling.priest.war-priestess-of-myrmidia': 'lore.prayers-of-myrmidia',
        'hireling.priest.trickster-priest-of-ranald': 'lore.prayers-of-ranald-and-handrich',
        'hireling.priest.priestess-of-shallya': 'lore.prayers-of-shallya',
        'hireling.priest.warrior-priest-of-sigmar': 'lore.prayers-of-sigmar',
        'hireling.priest.druid-priest-of-taal': 'lore.prayers-of-taal',  # KB list; MW mirror documented on the lore
        'hireling.priest.wolf-priest-of-ulric': 'lore.prayers-of-ulric-miracle-workers',
        'hireling.priest.priest-of-verena': 'lore.prayers-of-verena-and-solkan',
    }
    pdata = yaml.safe_load(PRIESTS.read_text(encoding='utf-8'))
    assigned = []
    for prof in pdata.get('profiles', []):
        prof.pop('lore', None)  # repair stray key written by earlier versions
        target = DESIRED.get(prof.get('id'))
        if target and prof.get('lore_assignments') != [target]:
            prof['lore_assignments'] = [target]
            assigned.append(f'{prof["id"]} -> {target}')

    print('lores added:', [l['id'] for l in added])
    print('waterwalk repaired:', ww_fixed)
    print('assignments:', assigned or 'none')
    if not apply:
        return 0
    if added:
        data['lores'].extend(added)
    # newline="\n": the maintained YAML is LF-only (see .gitattributes).
    MAGIC.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100),
                     encoding='utf-8', newline='\n')
    PRIESTS.write_text(yaml.safe_dump(pdata, sort_keys=False, allow_unicode=True, width=100),
                       encoding='utf-8', newline='\n')
    print('written:', MAGIC, PRIESTS)
    return 0


if __name__ == '__main__':
    sys.exit(main())
