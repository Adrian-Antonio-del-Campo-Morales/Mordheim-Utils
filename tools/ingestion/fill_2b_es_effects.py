"""Fill the missing Spanish effect translations in the 2B staging tree.

Every rule keeps its canonical English ``effect``; this script inserts an
``effect_i18n:`` block (folded ``es: >-`` scalar) before each rule's
``applies_to:`` entry. Terminology follows the names already established in
the staging packages and the active KB glossary (Matatrolles, Memoralista,
chequeo de Liderazgo, Fuera de Combate, ...).

Usage::

    python tools/ingestion/fill_2b_es_effects.py           # dry run
    python tools/ingestion/fill_2b_es_effects.py --write   # apply
"""
from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

STAGING = Path(__file__).resolve().parents[2] / "sources" / "2B" / "bands" / "mordheim"

TRANSLATIONS: dict[str, str] = {
    # --- adventurers-kaz (15) ---
    "band--no-fixed-leader": "La banda de Aventureros no tiene un líder fijo. Los aventureros discuten y reñían constantemente entre ellos por todo tipo de cosas menores, como la comida y el oro, ya no digamos ponerse de acuerdo sobre su líder. Al crear la banda, marca en la hoja de banda a cada Héroe (excepto al Capitán Imperial) con un número entre 1 y 5. Como el Capitán Imperial nunca puede convertirse en el Líder, siempre existe la posibilidad de que la banda no tenga líder para la siguiente batalla. Tira 1D6 antes de cada batalla. Enano: si el Enano es el Líder de la banda, el Elfo se siente tan insultado por ello que no permanecerá a 6\" del Enano en ningún momento y por tanto no podrá beneficiarse de su Liderazgo. Elfo: si el Elfo es el Líder, el Enano se siente tan insultado que no permanecerá a 6\" del Elfo y no podrá beneficiarse de su Liderazgo. Hechicero: si el Hechicero es el Líder, el Bárbaro se confunde tanto con las difíciles órdenes del Hechicero que no permanecerá a 6\" del Hechicero y no podrá beneficiarse de su Liderazgo. Bárbaro: si el Bárbaro es el Líder, el Hechicero se irrita y molesta tanto por sus estúpidas órdenes que no permanecerá a 6\" del Bárbaro y no podrá beneficiarse de su Liderazgo (ver también la regla «Cabezacuadrado» del Bárbaro). Noble Imperial: como el Noble Imperial es un líder nato, nadie sufre efectos negativos hacia ningún otro aventurero de la banda.",
    "wizard--wizard": "Los hechiceros son magos y comienzan con dos hechizos aleatorios de la lista de hechizos de Magia Menor. Consulta la sección de magia de tu libro de reglas para más detalles.",
    "elf--hatred": "El Elfo odia a los Elfos Oscuros.",
    "elf--seeker": "Un Buscador ayuda a su banda cuando esta busca tesoros en las mazmorras. Si el Buscador no queda Fuera de Combate en la batalla, puedes modificar un dado en la secuencia de exploración en +1/-1.",
    "barbarian--frenzy": "El Bárbaro está sujeto a Frenesí.",
    "barbarian--dim-witted": "Si el Bárbaro es el líder de la banda, tiene un Liderazgo efectivo de 7 para los miembros de la banda a 6\" y para las tiradas de Huida.",
    "imperial-noble--honorable": "El Noble Imperial nunca atacará a un oponente que esté Derribado o Aturdido.",
    "imperial-noble--family-heirloom": "La Reliquia Familiar es una espada o pistola especial que ha pertenecido a la familia durante mucho tiempo. Al crear la banda, tira 1D6 para ver cuál es su poder: 1-2 el Noble puede repetir el primer chequeo de Psicología fallido durante una batalla; 3-4 el Noble causa Miedo a Orcos y Goblins y Skaven; 5-6 el Noble puede repetir un dado durante una batalla.",
    "dwarf--hard-to-kill": "Ver la página 151 del libro de reglas de Mordheim.",
    "dwarf--hard-head": "Ver la página 151 del libro de reglas de Mordheim.",
    "band--elf-special-skills": "Los Héroes Elfos pueden usar la siguiente Tabla de Habilidades en lugar de cualquiera de las tablas de habilidades estándar. Feérico: cualquier efecto de un hechizo mágico o un pergamino no afectará al modelo con una tirada de 4+ en 1D6. Elegido de la Torre Blanca: el Elfo ha sido entrenado en el arte marcial de la Torre Blanca; esto le permite parar aunque no esté armado con broquel ni espada, y puede repetir la parada si ya está armado de esta forma. Ligereza Feérica: igual que TC12.",
    "band--barbarian-special-skills": "Los Bárbaros pueden usar la siguiente lista de habilidades en lugar de las listas de habilidades estándar. Difícil de Matar: los bárbaros son guerreros duros y resistentes; al tirar en la tabla de heridas, trata un resultado de 5 como aturdido; el Bárbaro solo quedará Fuera de Combate con un resultado de 6. Carga Feroz: el Bárbaro puede doblar sus ataques en el turno en el que carga; sufrirá un -1 por impactar ese turno. Guerrero Instintivo: el Bárbaro está tan acostumbrado a su Arma a Dos Manos que es capaz de parar con ella; usa las reglas de Parada normalmente, como con una espada, tal y como se describen en tu Libro de Reglas.",
    "band--noble-special-skills": "El Noble puede usar la siguiente Tabla de Habilidades en lugar de cualquiera de las tablas de habilidades estándar. Talento para el Comercio: el Noble puede repetir un dado al buscar objetos raros; además, el Noble Imperial obtiene un descuento de -2D6 coronas en un único objeto que compre con una tirada de 5+ en 1D6 después de cada batalla. Provocar: el Noble puede provocar a un oponente a 10\"; ese oponente debe superar un chequeo de Liderazgo o deberá cargar contra el Noble, incluso si está fuera de su alcance de carga.",
    "band--dwarf-special-skills": "Los Enanos pueden usar la siguiente Tabla de Habilidades en lugar de cualquiera de las tablas de habilidades estándar. Resistente a la Magia: ¡yo no creo en la magia! Cualquier efecto de un hechizo mágico o un pergamino no afectará al Enano con una tirada de 4+ en 1D6. Carga Feroz: ver la página 151 del libro de reglas de Mordheim. Matamostro: ver la página 151 del libro de reglas de Mordheim. Berserker: ver la página 151 del libro de reglas de Mordheim.",
    "cannon-fodder--mixed-bunch": "Cuando uno de los Carne de Cañón obtiene el resultado de «el chaval tiene talento», se convertirá en un Capitán Imperial. Puede escoger dos habilidades de cualquiera de las tablas de habilidades de los Aventureros, pero no de las especiales. El Capitán Imperial usa la lista de equipo de Carne de Cañón.",
    # --- channel-rats-mim (19) ---
    "band--water-caravan": "Cada banda de Strigany debe incluir un Barco Fluvial o una Barcaza Fluvial. Si no hay ríos en tu campaña, deberás sustituir el Barco Fluvial por un Carro y dos caballos. Si haces esto, sustituye la habilidad «Trincador» por «Trapacero» para permitir a tu Calderero reparar el carro.",
    "band--lucky-white-heather": "En lugar de buscar un objeto raro durante la secuencia posterior a la batalla, uno de los Héroes se prepara para engañar o robar a un Héroe elegido de otra banda. Siempre que un Héroe de una banda de Strigany participe en un trabajo visitando otra banda, tira 1D6: con un resultado de 1, el Héroe Strigany involucrado ha tentado demasiado a la suerte y ha sido linchado; tira en la Tabla de Heridas Graves y aplica el resultado. Con un 2-5, la otra banda se ve obligada a comprar un amuleto de la suerte falso por 1D6 coronas de oro. Con un resultado de 6, ¡el Strigany roba un objeto mientras están distraídos! Elige un objeto que pertenezca a un Héroe para que lo robe el molesto Strigany.",
    "band--shadowy-traditions": "El Petru es un encantador capaz de invocar a uno de los Viejos Padres. En lugar de buscar un objeto raro durante la secuencia posterior a la batalla, el Petru puede solicitar que se conceda una audiencia con el Viejo Padre a uno de sus familiares. Con un chequeo de Liderazgo superado, uno de los otros Héroes de la banda debe visitar a su antiguo maestro en la secuencia posterior a la batalla. Si el chequeo falla, este laborioso proceso obliga al Petru a perderse la siguiente batalla. Uno de los Héroes de la banda puede visitar al Viejo Padre para buscar su bendición. Elige a un guerrero humano de la banda para que el vampiro lo seduzca y tira en la tabla de Padre en la Oscuridad. El líder o un lanzador de hechizos no pueden buscar una bendición. Un Héroe con mutaciones recibe un modificador de -1. Tabla de Padre en la Oscuridad: 1-3 Hijo Indigno (el Héroe es drenado y se retira de la lista de la banda); 4 Hijo Afortunado (no ocurre nada); 5 Hijo Favorito (el Héroe se convierte en Consentido de la Sangre: +1 Iniciativa y +1 Ataque; si el Consentido de la Sangre visita de nuevo, aplica un modificador de +1 al resultado); 6 Hijo en la Oscuridad (el Héroe se convierte en Vampiro Sustituto: +1 Movimiento, +1 Resistencia, +1 Herida, +1 Iniciativa y +1 Ataque; los Sustitutos causan miedo, son inmunes al veneno y están sujetos a la Sed de Sangre). Sed de Sangre: los vampiros recién convertidos tiran 1D6 al inicio de cada turno; con un resultado de 1 el Sustituto debe hacer un chequeo de estupidez ese turno, con un 2-5 no ocurre nada y con un 6 están sujetos a frenesí ese turno.",
    "petru--wizard": "Los Petru son místicos Strigany y tienen dos hechizos generados de la lista de Encantos y Maleficios.",
    "band--charms-and-hexes": "Los Encantos y Maleficios son la magia de la brujería. Requieren grandes cantidades de ingredientes de hechizos e incantaciones minuciosas, pero pueden ser devastadores, reduciendo a los enemigos a pobres despojos e infundiendo a los camaradas una suerte casi incomprensible. 1 Escudriñar (Dificultad 6): durante el turno, un Héroe o Secuaz puede repetir 1D3 tiradas de dado con +1 o -1 al resultado. 2 Maldición (Dificultad 6): un modelo enemigo a 12\" del Petru debe repetir todas sus tiradas de dado exitosas durante este turno y el siguiente. 3 Polvo del Ciego (Dificultad 9): un modelo enemigo a 16\" del Petru queda instantáneamente ciego; no puede disparar, cargar ni correr, tiene la mitad de su Habilidad de Combate y se moverá en una dirección aleatoria al inicio de su turno; la ceguera dura hasta que el Petru lance otro hechizo o se mueva. 4 Era de Piedra (Dificultad 8): un modelo enemigo a 12\" del Petru ve todas sus características reducidas en -1 durante este turno y el siguiente. 5 Azote del Guerrero (Dificultad 7): un modelo enemigo a 18\" del Petru no podrá usar ninguna de sus armas; no podrá disparar y se considerará que pelea a puño limpio en combate cuerpo a cuerpo; el encantamiento dura este turno y el siguiente. 6 Curar (Dificultad 6): todos los modelos amistosos a 6\" del Petru curan una Herida; además, cualquier modelo aturdido o derribado puede ponerse en pie inmediatamente.",
    "petru--necromancy": "Conociendo un poco de las artes negras, los Petru pueden determinar aleatoriamente un nuevo hechizo de la lista de Necromancia en lugar de aprender una nueva habilidad.",
    "petru--potions": "Ofreciendo remedios mediante la provisión de pociones sospechosas, el Petru lleva surtido de filtros para la talasurgia terapéutica. Un único Héroe de la banda puede acercarse al Petru antes de la batalla para arriesgarse a probar uno de estos productos vitalogistas. Tira 1D6 para descubrir el efecto del brebaje: 1 Debilitante (-1 Resistencia durante toda la siguiente batalla, hasta que supere los efectos con un 6 en 1D6 en la fase de recuperación); 2-3 Fuerza (+1 al modificador de Fuerza hasta que saque un 1 en 1D6 en la fase de recuperación); 4-5 Resiliencia (+1 Resistencia hasta que saque un 1 en 1D6 en la fase de recuperación); 6 Fortaleza (gana una herida adicional para toda la batalla; una vez perdida, la herida no puede restaurarse).",
    "domnu--leader": "Cualquier guerrero a 6\" del Domnu puede usar su valor de Liderazgo en lugar del propio cuando realice chequeos de Liderazgo.",
    "domnu--prize-fighter": "El Maestro de Caravana no sufre ninguna penalización por pelear desarmado y recibe +1 Ataque al hacerlo.",
    "domnu--bear-hug": "La lucha y el pugilato son deportes tradicionales de los Strigany. Si el Domnu impacta al mismo guerrero enemigo con ambos de sus ataques desarmados en la misma ronda de combate, el jugador puede elegir hacer un único ataque de Abrazo del Oso en lugar de resolver los ataques con normalidad. Cada jugador tira 1D6 y suma la Fuerza de su guerrero a la tirada. Si el total del Domnu es mayor o los totales son iguales, el guerrero oponente sufre una herida automática sin tirada de salvación por armadura. Si el total del guerrero enemigo es mayor, el guerrero ha roto la presa del Domnu y no sufre daño del ataque.",
    "tinker--grifter": "¡Los Caldereros son tramposos! Como un mercader, un Calderero permite organizar acuerdos comerciales con otras bandas.",
    "tinker--rigger": "El Calderero es hábil reparando daños menores en embarcaciones. Si el barco o la barcaza está estacionaria y no se ha movido durante el último turno, y el Calderero está en contacto con ella, puede reparar una localización previamente dañada, es decir, una pala o un mástil. El Héroe no puede hacer nada más ese turno y el vehículo no puede moverse. Un barco no puede repararse si un modelo enemigo está en contacto con el Calderero o la embarcación.",
    "truant--spry": "Un Vagabundo está acostumbrado a trepar por ojos de buey, así como a correr por los tejados con sigilo felino. Para reflejar esto, un Vagabundo puede correr o cargar mientras trepa.",
    "truant--taunt": "Durante la fase de Disparo, el Vagabundo puede elegir provocar a un enemigo en lugar de disparar con un arma de misil. El Vagabundo debe poder ver al enemigo y provocar requiere línea de visión, igual que para disparar. El enemigo realiza entonces un chequeo de Liderazgo. Si lo supera, no ocurre nada, pero si lo falla debe gastar su siguiente fase de movimiento intentando entrar en combate cuerpo a cuerpo con el Vagabundo que lo provocó.",
    "dead-eye--dead-eye-shot": "El Ojos Muertos tiene ojos de águila y puede alcanzar el objetivo más pequeño. Ignora los modificadores por impactar por cobertura cuando dispara o lanza su arma.",
    "dead-eye--target-practice": "El guerrero puede efectuar un único ataque de misil cuando está siendo cargado. Los modelos que disparan ante una carga sufren un modificador de -1 por impactar.",
    "dead-eye--weapons-expert": "Ver la página 122 del Libro de Reglas de Mordheim.",
    "fugitive--charismatic": "Seductores desalmados que destilan machismo. Un pícaro romántico de principio a fin, cualquier modelo del sexo opuesto (Hermanas de Sigmar, Amazonas, Explorador de Kislev, etc.) debe hacer un chequeo de Liderazgo si desea cargar contra un Fugitivo.",
    "strigany-special-skills-list": "Los Strigany del Río pueden elegir usar la siguiente lista de habilidades en lugar de las listas de habilidades estándar. Conocimiento de Mitos y Leyendas: durante la fase de Exploración, si el Héroe no quedó Fuera de Combate, puedes repetir un dado, quedándote con el segundo resultado aunque sea peor. Embestida: cuando carga, el Héroe puede intentar derribar a su oponente en lugar de hacer sus ataques normales; tira por impactar una vez con un modificador de +1 por impactar, aunque no es necesaria tirada para herir; si el guerrero impacta con este ataque, el modelo oponente queda derribado. Cantor: cualquier modelo amistoso a 6\" del Héroe puede repetir cualquier chequeo de Liderazgo fallido con un +1 al Liderazgo; esto incluye las tiradas de Huida. Luchador: el Héroe no sufre ninguna penalización por pelear desarmado y recibe +1 Ataque al hacerlo. Encantador de Animales: el Héroe puede controlar hasta cinco animales usando encantos Strigany, siempre que permanezcan a 6\" de él; si un animal no está a 6\" del Encantador de Animales en la fase de Movimiento, se moverá 1D6\" en una dirección aleatoria. Infiltración: un Strigany con esta habilidad siempre se coloca en el campo de batalla después de la banda oponente y puede colocarse en cualquier parte de la mesa, siempre que esté fuera de la línea de visión de la banda oponente y a más de 12\" de cualquier modelo enemigo; si ambos jugadores tienen modelos que infiltran, tira 1D6 por cada uno, y el que saque el resultado más bajo despliega primero.",
    # --- clan-angrund-kep (19) ---
    "band--hard-to-kill": "Los enanos son individuos duros y resistentes que solo pueden ser dejados fuera de combate con un resultado de 6 en lugar de 5-6 al tirar en la tabla de Heridas. Trata un resultado de 1-2 como derribado, 3-5 como aturdido y 6 como fuera de combate.",
    "band--armour": "Los enanos nunca sufren penalizaciones de movimiento por llevar armadura.",
    "band--hard-head": "Los enanos ignoran las reglas especiales de mazas, garrotes, etc. ¡Es difícil dejarlos inconscientes!",
    "band--hate-skavens-orcs-and-goblins": "Todos los Enanos odian a los Skaven, Orcos y Goblins. Consulta la sección de Psicología de las reglas de Mordheim para más detalles sobre los efectos del odio.",
    "band--grudgebearers": "Los Enanos guardan un antiguo agravio contra los Elfos desde los días en que ambas razas lucharon por la supremacía en el Viejo Mundo. Una banda de Enanos no puede incluir nunca ningún tipo de Espada Contratada Elfa ni Dramatis Personae.",
    "band--incomparable-miners": "Los Enanos pasan gran parte de sus vidas bajo tierra buscando minerales preciosos, y son los mejores del mundo en este tipo de trabajo. En la Ciudad de los Condenados aplican habilidades similares a la búsqueda de piedra bruja. Al buscar tesoros al final de una partida, suma +1 al número de piezas encontradas para una banda de Enanos.",
    "dwarf-noble--leader": "Cualquier modelo de la banda a 6\" del Noble Enano puede usar su Liderazgo en lugar del propio.",
    "dwarf-engineer--expert-weaponsmith": "Un Ingeniero Enano es un maestro de los dispositivos mecánicos. Usando materiales de construcción más resistentes y secretos testificados por el tiempo de la ingeniería Enana, un Ingeniero Enano puede aumentar la distancia a la que disparan las armas de misil de la banda. Todas las armas de misil Enanas de la banda aumentan su alcance en 3\" para pistolas y 6\" para ballestas y armas de fuego. Los aumentos de alcance solo se mantienen mientras el Ingeniero Enano permanezca con la banda.",
    "dwarf-troll-slayers--deathwish": "Los Matatrolles buscan una muerte honorable en combate. Son completamente inmunes a toda la psicología y nunca necesitan hacer chequeos si luchan solos.",
    "dwarf-troll-slayers--slayer-skills": "Los Matatrolles pueden escoger una habilidad de la Tabla de Habilidades de Matatrolles en lugar de la tabla de habilidades normal cuando ganan una habilidad nueva.",
    "ironbreaker--watch-out": "Un Rompehierros conoce todas las profundidades y sus peligros, de modo que él o cualquier Enano a 6\" puede decidir repetir el resultado en la tabla de Encuentros que les afecta.",
    "band--dwarf-special-skills-master-of-blades": "Las habilidades marciales de este Enano superan a las de un guerrero normal; ha luchado sin un rasguño contra hordas de Orcos y Goblins. Al usar un arma que tenga la regla especial Parada, este héroe para con éxito si iguala o supera la tirada más alta «por impactar» de su oponente, no solo si la supera. Además, si este guerrero usa dos armas que tienen la regla especial Parada, puede parar dos ataques (si sus dos dados igualan o superan los dos dados de Ataque más altos contra él) en lugar del máximo normal de uno. Ten en cuenta que si este Enano lleva dos hachas Enanas (como se detalla arriba) puede repetir cualquier parada fallida.",
    "band--dwarf-special-skills-extra-tough": "Este Enano es conocido por sobrevivir a heridas que matarían a un ser inferior. Al tirar en la tabla de Heridas Graves del Héroe tras una partida en la que haya quedado Fuera de Combate, se puede repetir el dado una vez. El resultado de esta segunda tirada debe aceptarse, incluso si es peor.",
    "band--dwarf-special-skills-resource-hunter": "Este Enano es especialmente hábil localizando recursos valiosos. Al tirar en la tabla de Exploración al final de una partida, el Héroe puede modificar una tirada de dado en +1/-1.",
    "band--dwarf-special-skills-true-grit": "Los Enanos son individuos duros, ¡y este Héroe es duro incluso para ser un Enano! Al tirar en la tabla de heridas para este Héroe, un resultado de 1-3 se trata como derribado, 4-5 como aturdido y 6 como Fuera de Combate.",
    "band--dwarf-special-skills-thick-skull": "La cabeza de este Enano está excepcionalmente bien adaptada a los golpes. Si queda aturdido, trata un resultado de aturdido como derribado en su lugar. Si el Enano además lleva casco, esta salvación es de 2+ en lugar de 4+ (esto sustituye a la regla especial normal del casco).",
    "band--slayer-special-skills-ferocious-charge": "El Matatrolles puede doblar sus ataques en el turno en el que carga. Sufre entonces una penalización de -1 por impactar ese turno.",
    "band--slayer-special-skills-monster-slayer": "El Matatrolles siempre hiere a cualquier oponente con una tirada de 4+, independientemente de la Resistencia, a menos que su propia Fuerza (tras todos los modificadores por armas usadas, etc.) signifique que se necesita una tirada menor.",
    "band--slayer-special-skills-berserker": "El Matatrolles puede sumar +1 a sus tiradas «por impactar en combate cerrado» durante el turno en el que carga.",
    # --- crooked-moon-kep (22) / night-goblins-kaz (21) / savage-orcs-kaz (13) ---
    "crooked-moon-kep/band--animosity": "Los Goblins pasan gran parte de sus vidas reñían y peleando entre ellos. A veces esto ocurre en el peor de los momentos. Al inicio de cada turno de Goblins Nocturnos tira 1D6. Con un resultado de 1, empiezan a reñir y no harán nada más durante el resto del turno. Solo se ven afectados los Goblins Nocturnos. Trolls, Squigs, Snotlings y otros no goblins no se ven afectados y actuarán con normalidad.",
    "night-goblins-kaz/band--animosity": "Los Goblins pasan gran parte de sus vidas reñían y peleando entre ellos. A veces esto ocurre en el peor de los momentos. Al inicio de cada turno de Goblins Nocturnos tira 1D6. Con un resultado de 1, empiezan a reñir y no harán nada más durante el resto del turno. Solo se ven afectados los Goblins Nocturnos. Trolls, squigs, snotlings y otros no goblins no se ven afectados y actuarán con normalidad.",
    "band--hate-stunties-and-skaven": "Los Goblins Nocturnos están sujetos a odio hacia los Enanos y los Skaven. Esto solo afecta a los Goblins Nocturnos, no a otros pieles verdes. Los Fanáticos están tan fuera de sí que no se ven afectados.",
    "band--hate-stunties": "Los Goblins Nocturnos están sujetos a odio hacia los Enanos. Esto solo afecta a los Goblins Nocturnos, no a otros pieles verdes. Los Fanáticos están tan fuera de sí que no se ven afectados.",
    "band--night-goblin-special-skills": "Muy Puntero: el astuto mierdas suma +6\" al alcance de cualquier arma de misil que use (sin incluir redes). Git Listo: el piel verde es tan sigiloso que puede mover 1D3 miembros de su banda después de que todo el resto del despliegue esté completo; solo el Gran Jefe Goblin Nocturno. Infiltrarse: como la habilidad Skaven. Redador: el goblin es experto en usar una red para inutilizar a sus enemigos; la técnica que ha dominado es «lanzar y cargar» (ver mechanic.netter para el texto completo).",
    "crooked-moon-kep/band--night-goblin-special-skills": "Muy Puntero: el astuto mierdas suma +6\" al alcance de cualquier arma de misil que use (sin incluir redes). Git Listo: el piel verde es tan sigiloso que puede mover 1D6\" desde un miembro Goblin Nocturno de la banda después de que todo el resto del despliegue esté completo; solo el Gran Jefe Goblin Nocturno. Infiltrarse: como la habilidad Skaven. Redador: un Goblin Nocturno caza Squigs en las profundidades de las montañas y ha dominado la técnica de la red y la carga; el Goblin puede declarar que efectúa una carga con red, lanzando la red contra un objetivo de la misma forma que se describe en el libro de reglas de Mordheim; si impacta y el objetivo no logra escapar de la red, el objetivo cuenta como derribado y el Goblin completa su carga; si falla o el objetivo escapa, el Goblin efectúa una carga fallida (si la carga fallida lo llevara a contacto, detenlo a 1\" de distancia); un guerrero atrapado en una red será impactado automáticamente en combate, pero el Goblin aún debe tirar para herir como contra un enemigo derribado; en la siguiente fase de recuperación del guerrero, salvo que esté aturdido o fuera de combate, se cortará la red por sí mismo pero no podrá hacer nada más y contará como habiendo durado en combate como si se hubiera levantado de estar derribado.",
    "night-goblins-kaz/shaman--wizard": "Un Chamán Goblin Nocturno es un Hechicero y usa la magia Waaagh! tal y como se recoge en Best of Town Cryer.",
    "band--waagh-magic": "Los hechizos WAAAGH! son un ritual de arte, plegaria a Gork y Mork. Los hechizos del Chamán: 1 Maldición Chiflada de Gork (Dificultad 5): sea cual sea la circunstancia, el hechizo solo dura hasta que el lanzador quede derribado, aturdido o Fuera de Combate. 2 ¡Geronimoff! (Dificultad 7): una enorme y verde blob de ectoplasma impacta y empuja a un enemigo; alcance 6\"; mueve cualquier modelo enemigo dentro del alcance directamente alejándolo del Chamán; si el objetivo colisiona con otro modelo o edificio, ambos sufren 1 impacto; no puede lanzarse sobre un modelo en combate cuerpo a cuerpo. 3 ¡Zzap! (Dificultad 8): un chispeante rayo verde de energía WAAAGH! irrumpe de la frente del Chamán para golpear al oponente más cercano; alcance 12\"; causa 4 impactos sobre el objetivo enemigo más cercano sin salvaciones por armadura. 4 ¡Engañado! (Dificultad 6): el Chamán desaparece en una niebla verde, confundiendo a sus enemigos; ningún enemigo puede cargar contra el Chamán durante su siguiente turno; si el Chamán está en combate cuerpo a cuerpo puede moverse inmediatamente 4\" alejándose. 5 Garra de Gork (Dificultad 7): una enorme garra ectoplásmica verde aparece en la mano del Chamán; la garra ectoplásmica cuenta como una maza normal con un bonificador de Fuerza de +2 y otorga al portador +1 a la salvación por armadura contra ataques de combate cuerpo a cuerpo. 6 Puño de Gork (Dificultad 8): dos rayos de llama verde salen disparados de los ojos del Chamán y golpean al enemigo más cercano; alcance 12\"; cada uno de los dos rayos causa un impacto de 1D6; los rayos pueden dispararse ambos contra el objetivo enemigo más cercano o repartirse entre los dos objetivos enemigos más cercanos.",
    "big-boss--leader": "Cualquier modelo de la banda a 6\" del Gran Jefe puede usar su Liderazgo en lugar del propio.",
    "shaman--wizard": "Un Chamán Goblin Nocturno es un Hechicero y usa magia WAAAGH!.",
    "squig-hopper--squig-jump": "Los Squig Hoppers se mueven usando la característica de Movimiento aleatoria 2D6 de su montura Squig en lugar de un movimiento normal; nunca corren ni declaran una carga. En su lugar, se les permite contactar con un modelo enemigo dentro de su movimiento normal de 2D6; si esto ocurre, cuentan como que han cargado para la siguiente ronda de combate cuerpo a cuerpo.",
    "fanatics--addict": "El Fanático depende de un suministro regular de setas Capachas. Si no consigue ninguna antes de una batalla, se quedará en su cueva echando espuma por la boca y no participará. Si hay disponibles, se comerá sus setas antes de la batalla.",
    "fanatics--looney": "Debido al efecto de las setas está sujeto a Frenesí. También debe hacer un chequeo de daño permanente tras la batalla, tal y como se describe en el libro de reglas.",
    "fanatics--frantic": "El Fanático es hiperactivo y golpeará primero en combate, ignorando las penalizaciones por armas u orden de iniciativa.",
    "cave-squigs--movement": "Los Squigs de Cueva no tienen una característica de Movimiento fija, sino que se mueven una distancia increíblemente aleatoria. Los Squigs nunca corren ni declaran cargas. En su lugar, se les permite contactar con un modelo enemigo dentro de su movimiento normal de 2D6. Si esto ocurre, cuentan como que cargan para la siguiente ronda de combate cuerpo a cuerpo, igual que si hubieran declarado una carga.",
    "cave-squigs--minderz": "Cada Squig de Cueva debe permanecer siempre a 6\" de un Goblin Nocturno. Si un Squig de Cueva se encuentra sin un Goblin a 6\" al inicio de su fase de movimiento, se volverá salvaje. A partir de ese momento, mueve al Squig 2D6\" en una dirección aleatoria durante todas sus fases de movimiento. Si su movimiento aleatorio lo lleva al contacto con otro modelo (amigo o enemigo), se enfrentará a ese modelo en combate cuerpo a cuerpo con normalidad.",
    "cave-squigs--animals": "Los Squigs de Cueva son una especie de animales y no ganan experiencia.",
    "troll--fear": "Los Trolls son monstruos aterradores, que causan miedo.",
    "troll--stupidity": "Un Troll está sujeto a las reglas de estupidez.",
    "troll--regeneration": "Los Trolls tienen una fisiología única que les permite regenerar heridas. Siempre que un enemigo logre infligir completamente una herida a un Troll, tira 1D6; con un resultado de 4 o más la herida se ignora y el Troll no sufre daño. Los Trolls no pueden regenerar heridas causadas por fuego o magia de fuego. Los Trolls nunca tiran por heridas tras una batalla.",
    "troll--dumb-monster": "Un Troll es demasiado estúpido para aprender alguna habilidad nueva. Los Trolls no ganan experiencia.",
    "troll--always-hungry": "Un Troll requiere un coste de manutención. Esta manutención representa la enorme cantidad de comida que debe darse al Troll para mantenerlo leal a la banda. La banda debe pagar 15 coronas después de cada partida para mantener al Troll. Si la banda carece de oro para pagar la manutención, el Gran Jefe tiene la opción de sacrificar tres Snotlings o dos Squigs de Cueva al Troll en lugar de comprar comida (los Trolls comen casi cualquier cosa). Si no se paga esta comida (ya sea en oro o en miembros de la banda), el Troll pasa hambre y se marcha en busca de alimento.",
    "troll--vomit-attack": "En lugar de sus ataques normales, un Troll puede regurgitar sus altamente corrosivos jugos digestivos sobre un desafortunado oponente de combate cuerpo a cuerpo. Este es un único ataque que impacta automáticamente con una Fuerza de 8 e ignora las salvaciones por armadura.",
    "snotling-mob--mob": "Los Snotlings son criaturas naturalmente gregarias. Todos los miembros deben permanecer a 6\" y todos se unirán al mismo combate si es posible.",
    "snotling-mob--weedy": "Si resultan heridos suman +1 en la tabla de heridas.",
    "snotling-mob--dodgy": "Las pequeñas criaturas se agachan y esquivan constantemente de la manera más exasperante. Obtienen una salvación de esquiva de +1D6 contra disparos.",
    "crooked-moon-kep/cave-squigs--movement": "Los Squigs de Cueva no tienen una característica de Movimiento fija, sino que se mueven una distancia increíblemente aleatoria. Los Squigs nunca corren ni declaran cargas. En su lugar, se les permite contactar con un modelo enemigo dentro de su movimiento normal de 2D6. Si esto ocurre, cuentan como que cargan para la siguiente ronda de combate cuerpo a cuerpo, igual que si hubieran declarado una carga.",
    "crooked-moon-kep/cave-squigs--minderz": "Cada Squig de Cueva debe permanecer siempre a 6\" de un Goblin Nocturno. Si un Squig de Cueva se encuentra sin un Goblin a 6\" al inicio de su fase de movimiento, se volverá salvaje. A partir de ese momento, mueve al Squig 2D6\" en una dirección aleatoria durante todas sus fases de movimiento. Si su movimiento aleatorio lo lleva al contacto con otro modelo (amigo o enemigo), se enfrentará a ese modelo en combate cuerpo a cuerpo con normalidad.",
    "crooked-moon-kep/cave-squigs--animals": "Los Squigs de Cueva son una especie de animales y no ganan experiencia.",
    "crooked-moon-kep/troll--dumb-monster": "Un Troll es demasiado estúpido para aprender alguna habilidad nueva. Los Trolls no ganan experiencia.",
    "crooked-moon-kep/troll--vomit-attack": "En lugar de sus ataques normales, un Troll puede regurgitar sus altamente corrosivos jugos digestivos sobre un desafortunado oponente de combate cuerpo a cuerpo. Este es un único ataque que impacta automáticamente con una Fuerza de 8 e ignora las salvaciones por armadura.",
    "crooked-moon-kep/snotling-mob--mob": "Los Snotlings son criaturas naturalmente gregarias. Todos los miembros deben permanecer a 6\" y todos se unirán al mismo combate si es posible.",
    "crooked-moon-kep/snotling-mob--weedy": "Si resultan heridos suman +1 en la tabla de heridas.",
    "crooked-moon-kep/snotling-mob--dodgy": "Las pequeñas criaturas se agachan y esquivan constantemente de la manera más exasperante. Obtienen una salvación de esquiva de +1D6 contra disparos.",
    "skaven-of-clan-mors-kaz/band--rulebook-inheritance": "Los Skaven del Clan Mors pueden usar las armas Skaven tal y como se detallan en el libro de reglas. Los Héroes Skaven pueden usar cualquiera de las Habilidades Especiales Skaven del libro de reglas, excepto el Arte de la Muerte Silenciosa.",
    # --- night-goblins-kaz extras (differences from crooked-moon-kep) ---
    "band--cave-squig-limit": "Tu banda puede incluir hasta 5 Squigs de Cueva. Nunca puedes tener más Squigs de Cueva en tu banda que Goblins Nocturnos.",
    "night-goblins-kaz/cave-squigs--movement": "Los Squigs de Cueva no tienen una característica de Movimiento fija, sino que se mueven con una zancada rebotante torpe. Para representar esto, al mover Squigs tira 2D6 por la distancia que se mueven. Los Squigs nunca corren ni declaran cargas. En su lugar, se les permite contactar con modelos enemigos dentro de su movimiento normal de 2D6\". Si esto ocurre, cuentan como que cargan para la siguiente ronda de combate cuerpo a cuerpo, igual que si hubieran declarado una carga.",
    "night-goblins-kaz/cave-squigs--minderz": "Cada Squig de Cueva debe permanecer siempre a 6\" de un Goblin Nocturno, que mantiene a la criatura a raya. Si un Squig de Cueva se encuentra sin un Goblin a 6\" al inicio de su fase de Movimiento, se volverá salvaje. A partir de ese momento, mueve al Squig 2D6\" en una dirección aleatoria durante cada una de sus fases de movimiento. Si su movimiento aleatorio lo lleva al contacto con otro modelo (amigo o enemigo), se enfrentará al modelo en combate cuerpo a cuerpo con normalidad. El Squig de Cueva queda fuera del control del jugador de Goblins Nocturnos hasta el final de la partida.",
    "night-goblins-kaz/cave-squigs--animals": "Los Squigs de Cueva son una especie de animales y por tanto no ganan experiencia.",
    "night-goblins-kaz/troll--dumb-monsters": "Un Troll es demasiado estúpido para aprender alguna habilidad nueva. Los Trolls no ganan experiencia.",
    "night-goblins-kaz/troll--vomit-attack": "En lugar de sus ataques normales, un Troll puede regurgitar sus altamente corrosivos jugos digestivos sobre un desafortunado oponente de combate cuerpo a cuerpo. Este es un único ataque que impacta automáticamente con una Fuerza de 5 e ignora las salvaciones por armadura.",
    "night-goblins-kaz/snotling-mob--mob": "Los Snotlings son criaturas naturalmente gregarias. Se compran inicialmente en un mob de 5. Puedes reemplazar a los miembros del mob hasta un máximo de 5. Siempre se moverán y lucharán como un mob. Todos los miembros deben permanecer a 1\" (¿o 1/2\"?) y todos se unirán al mismo combate si es posible.",
    "night-goblins-kaz/snotling-mob--weedy": "Los Snotlings no son las criaturas más robustas. Si resultan heridos quedarán derribados con un 1, aturdidos con un 2-3 y Fuera de Combate con un 4-6.",
    "night-goblins-kaz/snotling-mob--dodgy": "Las pequeñas criaturas se agachan y esquivan constantemente de la manera más exasperante. Obtienen una salvación de esquiva de 6+ contra disparos.",
    "savage-orcs-kaz/band--animosity": "Igual que sus primos más sofisticados (?), los Orcos Salvajes sufren animosidad. Ver las reglas de Animosidad en TC6 del WD243.",
    "band--orc-special-skills": "Los héroes Orcos Salvajes pueden usar las habilidades especiales Orcas de TC6 (White Dwarf 243) en lugar de cualquiera de las listas de habilidades estándar disponibles para ellos.",
    "band--gobbo-rout-counting": "Los Orcos no esperan mucho de sus primos menores y no les importa que rompan o caigan en batalla. Por tanto, al hacer el chequeo para ver si una banda Orca necesita una tirada de Huida, cada Chico Gobbo Fuera de Combate cuenta como medio modelo.",
    "boss--leader": "Cualquier miembro de la banda de Orcos Salvajes a 6\" puede usar la característica de Liderazgo de Da Jefe al realizar chequeos de Liderazgo.",
    "weirdo--wizard": "Un Rarito Orco Salvaje es un Hechicero y usa magia Waaagh!. Ver la magia Waaagh en TC6 (WD243).",
    "spottaz--get-out-dere": "A veces el jefe ordena a sus Ojeadores explorar las posiciones enemigas. Si el jugador quiere que sus Ojeadores se infiltren, tira 1D6 por cada Ojeador al inicio de la partida, pero después de que todos los modelos de ambos bandos (incluidos los Ojeadores) hayan sido desplegados. Si el Jefe está a 6\" del Ojeador, resta -1 a la tirada de dado. 1-2: Lo que digas, Jefe — el Ojeador se escabulle hacia adelante y puede redeployarse en cualquier parte de la mesa, pero al menos a 12\" de cualquier modelo enemigo. 3-4: Eh… si tú lo dices, jefe — el Ojeador está preocupado por alejarse demasiado del resto de los chicos y puede moverse hasta 1D6+6\" desde su posición actual. 5-6: ¡Ni hablar! — por mucho que Da Jefe le patee al Ojeador, se niega a dejar a sus compañeros. Si el jefe está a 6\", el Ojeador comienza la partida derribado.",
    "brutes--animosity": "Los Brutos Orcos Salvajes están sujetos a las reglas de animosidad.",
    "nuttaz--animosity": "Los Chalados Orcos Salvajes están sujetos a las reglas de animosidad.",
    "nuttaz--frenzy": "Los Chalados Orcos Salvajes están sujetos a las reglas de frenesí. Ten en cuenta que, cuando están en frenesí, ignoran las reglas de animosidad.",
    "boyz--animosity": "Los Chicos Orcos Salvajes están sujetos a las reglas de animosidad.",
    "gobbo-boyz--animosity": "Los Chicos Gobbo Orcos Salvajes están sujetos a las reglas de animosidad.",
    "gobbo-boyz--aint-orcz": "Cada Chico Gobbo Fuera de Combate cuenta como medio modelo al hacer el chequeo para ver si una banda Orca necesita una tirada de Huida.",
    "gobbo-boyz--useless-gitz": "Los Goblins nunca ganan experiencia.",
    # --- skaven-of-clan-mors-kaz (12) / skaven-of-clan-skryre-kaz (8) ---
    "band--rulebook-inheritance": "Los Skaven del Clan Mors pueden usar las armas Skaven tal y como se detallan en el libro de reglas. Los Héroes Skaven pueden usar cualquiera de las Habilidades Especiales Skaven del libro de reglas, excepto el Arte de la Muerte Silenciosa.",
    "claw-leader--leader": "Cualquier modelo de la banda a 6\" del Líder Garra puede usar su Liderazgo en lugar del propio.",
    "claw-leader--tactical-genius": "Los señores de la guerra del Clan Mors están entrenados en las artes de la guerra y son genios estratégicos (al menos a sus ojos). El jugador del Clan Mors puede sumar +1 a su tirada de dado para ver quién despliega primero.",
    "mors-sorcerer--wizard": "Un Hechicero de Mors es un Hechicero y usa la Magia de la Rata Cuernuda. Consulta la sección de Magia del libro de reglas para más detalles.",
    "skavenslaves--experience": "Los Esclavos Skaven son poco mejor que animales y no ganan experiencia.",
    "skavenslaves--all-races": "Los esclavos Skaven pueden ser de cualquier raza, incluidos sus propios compañeros Skaven. El perfil anterior representa el estado debilitado de todos ellos.",
    "skavenslaves--slavers": "Cualquier guerrero enemigo que sea capturado puede añadirse a un grupo de Esclavos Skaven. Tendrá el perfil anterior y deberá equiparse igual que el resto del grupo. Cualquier equipo que llevara cuando fue capturado puede quedarse la banda o venderse.",
    "rat-ogre--fear": "Los Ogros Rata son tan aterradores que causan miedo.",
    "rat-ogre--stupidity": "Un Ogro Rata está sujeto a estupidez a menos que un Héroe Skaven esté a 6\" de él.",
    "rat-ogre--experience": "Los Ogros Rata no ganan experiencia.",
    "rat-ogre--large": "Los Ogros Rata son criaturas enormes y por tanto constituyen objetivos tentadores para los arqueros. Cualquier modelo puede disparar a un Ogro Rata, incluso si no es el objetivo más cercano.",
    "band--wolf-rats-variant": "Nota: los Ogros Rata y las Ratas Lobo son entradas de lista alternativa por confirmar. 0-5 Ratas Lobo (60 coronas de oro por contratarlas) son el producto retorcido y mutado del Clan Moulder: M 6, HA 4, HP 0, F 4, R 4, H 1, I 4, A 2, Ld 6. Las Ratas Lobo son animales y nunca ganan experiencia. No necesitan ni usan armas ni armadura.",
    "skaven-of-clan-skryre-kaz/band--rulebook-inheritance": "Los Skaven del Clan Skryre pueden usar las armas Skaven tal y como se detallan en el libro de reglas. Los Héroes Skaven pueden usar cualquiera de las Habilidades Especiales Skaven del libro de reglas, excepto el Arte de la Muerte Silenciosa.",
    "band--jezzail": "El jezzail de cerrojo urtico es un diabólico invento del Clan Skryre Skaven. Es un arma de fuego enorme y de gran alcance, más parecida a un pequeño cañón que a un arma ordinaria. Dispara un proyectil especial hecho de piedra bruja. Alcance 36\", Fuerza 5, modificador de salvación por armadura -3. Reglas de Disparar o Preparar, Apuntar, Modificador de Salvación, Asistente y Pavés tal y como el texto del objeto. 175 coronas, Rareza 11, solo héroes, puede comprarse como parte de su equipo inicial.",
    "master-engineer--leader": "Cualquier modelo de la banda a 6\" del Ingeniero Maestro puede usar su Liderazgo en lugar del propio.",
    "master-engineer--master-engineer": "El Ingeniero Maestro puede repetir cualquier pifia con las armas de pólvora o propulsadas por piedra bruja que lleve. El resultado de la repetición debe aceptarse.",
    "warlock-engineer--wizard": "Un Ingeniero Hechicero es un Hechicero y usa la Magia de la Rata Cuernuda. Consulta la sección de Magia del libro de reglas para más detalles.",
    # --- dwarf-slayers-kaz (7) ---
    "band--town-crier-6-inheritance": "Todas las reglas especiales de Town Crier 6 (o Best of Town Crier) se aplican, excepto Mineros Incomparables. Los Enanos pueden usar el Hacha Enana tal y como se detalla en Town Crier 6 (o Best of Town Crier). Los Héroes Enanos pueden usar cualquiera de las Habilidades Especiales de Enanos y los héroes Matatrolles también pueden usar las Habilidades Especiales de Matatrolles, todo tal y como se recoge en Town Crier 6 (o Best of Town Crier).",
    "band--mighty-doom": "Todo lo que busca un Matatrolles es una muerte honorable. Una banda de Matatrolles no tiene que hacer tiradas de Huida hasta que el 50% de la banda haya quedado Fuera de Combate. Una banda de Matatrolles no puede huir voluntariamente.",
    "band--shame": "Si un héroe Enano (que aún no sea un Matatrolles) queda Fuera de Combate en cualquiera de las siguientes circunstancias, el Enano se siente tan avergonzado por su fracaso que pronuncia sus votos y se convierte en Matatrolles. El Enano pierde cualquier habilidad especial, p. ej. «Líder», pero conserva las habilidades que tenga. El Enano es Inmune a la Psicología. El Enano también tiene acceso a las habilidades especiales de Matatroll del libro de reglas de Mordheim. Un héroe Enano considerará vergonzoso lo siguiente: quedar Fuera de Combate en el primer o segundo turno del jugador Enano; quedar Fuera de Combate en combate singular contra un oponente con HA 2 o F 2 o por un animal (p. ej. perros, ratas o ardillas).",
    "band--slayer-special-skills": "La Tabla de Habilidades de Enanos de la banda incluye una columna dedicada a los Matatrolles: el Gran Matatrolles y el Matatroll tienen acceso a las habilidades de Combate, Fuerza, Especiales y de Matatroll; un Memoralista Enano a Combate, Disparo, Académicas y Especiales; un Memoralista Humano a Combate, Disparo, Académicas y Velocidad. Los héroes Matatrolles también pueden usar las Habilidades Especiales de Matatrolles tal y como se recogen en Town Crier 6 (o Best of Town Crier).",
    "giant-slayer--leader": "Cualquier modelo de la banda a 6\" del Gran Matatrolles puede usar su Liderazgo en lugar del propio.",
    "rememberer--hard-to-find": "No es fácil encontrar un Memoralista adecuado. Cuando decidas reclutar uno, tira 1D6; con un 1-4 es un Enano, con un 5-6 es un Humano. Si no deseas contratar a la raza que te salga, deberás esperar hasta después de tu siguiente partida antes de volver a intentarlo.",
    "rememberer--rememberer": "La tarea del Memoralista es registrar la perdición de cada uno de los Matatrolles. Cuando está cerca, los Matatrolles lucharán aún con más ahínco para hacer su muerte más honorable. Una vez por partida, cualquier Héroe Matatrolles que luche contra una criatura grande (como un troll o un ogro) y que esté a 6\" del Memoralista puede repetir una sola vez cualquier tirada por impactar fallida.",
    # --- slave-uprising-kep (6) ---
    "band--hate-skaven": "Tras años de maltrato, los miembros de la banda odian a todos los Skaven. Consulta la sección de Psicología de las reglas de Mordheim para más detalles sobre los efectos del odio.",
    "demagogue--leader": "Cualquier esclavo puede usar su Liderazgo si está a 6\".",
    "underlings--trustworthy": "Para organizar una revolución, el Demagogo necesitará nombrados de confianza (tan de confianza como puede serlo un Skaven), para golpear en varios puntos a la vez y organizar los movimientos de miles de trabajadores forzados.",
    "goblin-leader--hate-dwarfs": "Los pieles verdes desconfían profundamente de los Skaven, y esto es doblemente cierto en el caso de los Goblins. Se agrupan en torno a uno de ellos, con quien el Demagogo tendrá que entenderse. Reglas Especiales: Odio a los Enanos.",
    "human-leader--keep-together": "Los humanos se sienten bastante perdidos en el Bajo Imperio y se mantienen unidos; uno de ellos es manipulado entonces por el Demagogo para añadir efectivos a la lucha.",
    "goblin-slaves--hate-dwarfs": "Odio a los Enanos. Consulta la sección de Psicología de las reglas de Mordheim.",
    # --- strigoi-kaz (28) ---
    "band--dead-leader": "Si el vampiro muere, no puede ser reemplazado. Todas las criaturas no-muertas se desmoronarán y se perderán junto con su equipo. Entonces puedes seleccionar un nuevo líder entre los héroes, tal y como se describe en el libro de reglas de Mordheim. Tras una partida se puede comprar un nuevo vampiro. Este se convertirá en el nuevo líder y el «líder en funciones» volverá a su posición anterior.",
    "band--corpse-liquor": "Los Strigoi destilan el licor que mana de los cadáveres en putrefacción; ver el equipo especial Licor de Cadáver (Rareza 9, 10+1D6 coronas, solo bandas Strigoi). Un arma o garra recubierta de Licor de Cadáver herirá automáticamente a su objetivo con un 6 por impactar; un 6 para herir inflige un impacto crítico. Cada compra sirve para un guerrero durante una batalla.",
    "band--bat-restriction": "Tu banda puede incluir hasta 5 Murciélagos o hasta 2 Murciélagos Funestos. No puedes tener ambos tipos de murciélago en la banda al mismo tiempo.",
    "vampire--leader": "Cualquier modelo de la banda a 6\" del Strigoi puede usar su Liderazgo en lugar del propio.",
    "vampire--bestial": "El vampiro tiene una forma innata de evitar ser dañado. Tiene una salvación de parada de 6+ contra todos los ataques.",
    "vampire--wizard": "El Vampiro es un Hechicero y por tanto puede usar magia Necromántica. Consulta la sección de Magia del libro de reglas de Mordheim para más detalles.",
    "vampire--bloodline": "El vampiro puede tomar cualquiera de las Habilidades de Estirpe en lugar de buscar equipo raro. Los costes indicados son solo para la primera habilidad; la segunda y siguientes habilidades costarán el doble. Cada habilidad solo puede tomarse una vez, salvo que se especifique lo contrario. Maldición de los No-Muertos (50 coronas): si el vampiro queda Fuera de Combate, tras la batalla puede regenerar todas sus heridas con una tirada de 5+ en 1D6; si lo logra, no necesita tirar en la tabla de heridas graves. Odio Infinito (75 coronas): puede repetir todas las tiradas por impactar fallidas en el primer turno de cada combate; solo puede repetir cada dado una vez. Sangre Ligera (40 coronas): puede mejorar su salvación de parada a 5+. Sed de Sangre (50 coronas): está sujeto a frenesí. Golpe Maestro (40 coronas): puede causar un impacto crítico con un 5 o 6. Acólito Oscuro (35 coronas): obtiene +1 a la tirada de dificultad para lanzar hechizos. Alas de Murciélago (50 coronas): puede volar hasta 12\" en la fase de movimiento; puede ignorar el terreno y trepar. Repulsión (30 coronas): cualquiera que haga un chequeo de miedo por el vampiro tiene -1 Ld. Herida Infectada (30 coronas): efectos como Loto Negro; no puede combinarse con Licor de Cadáver. Beso de Sangre (75 coronas): puede robar una herida a un enemigo aturdido o Fuera de Combate en combate por el vampiro; las heridas pueden elevarse por encima del nivel inicial original, pero el efecto solo dura lo que dure la batalla. Tendones de Hierro (40 coronas): el vampiro gana +1 Fuerza, lo que puede llevarlo más allá del límite racial. Cazador (25 coronas): puede detectar modelos ocultos hasta a 2 veces su Iniciativa.",
    "charnel-guard--cause-fear": "La Guardia de Osario son criaturas retorcidas y repugnantes y por tanto causan miedo.",
    "charnel-guard--cunning": "A diferencia de los gulles ordinarios, un miembro de la Guardia de Osario puede tomar las habilidades Entrenamiento en Armas o Experto en Armas y aprender a usar cualquier arma.",
    "strigany--living": "Los Strigany son humanos vivientes y ninguna de las reglas de No-Muertos les afecta.",
    "ghouls--cause-fear": "Los Gulles son criaturas retorcidas y repugnantes y por tanto causan miedo.",
    "skeletons--cause-fear": "Los Esqueletos son criaturas No-Muertas aterradoras y por tanto causan miedo.",
    "skeletons--may-not-run": "Los Esqueletos son criaturas No-Muertas lentas y no pueden correr (pero pueden cargar con normalidad).",
    "skeletons--immune-to-psychology": "Los Esqueletos no se ven afectados por la psicología y nunca abandonan el combate.",
    "skeletons--immune-to-poison": "Los Esqueletos no se ven afectados por ninguna droga o veneno.",
    "skeletons--no-pain": "Los Esqueletos tratan un resultado de aturdido en la tabla de Heridas como derribado.",
    "skeletons--no-brain": "Los Esqueletos nunca ganan experiencia. No aprenden de sus errores. ¿Qué esperabas?",
    "bats--living": "Los Murciélagos son seres vivientes y ninguna de las reglas de No-Muertos les afecta.",
    "bats--animals": "Los Murciélagos son animales y nunca ganan experiencia.",
    "bats--flyers": "Los Murciélagos ignoran el terreno cuando se mueven y pueden cargar libremente contra cualquier modelo que puedan ver, sin importar la altura ni los interceptores.",
    "bats--squishy": "Los Murciélagos no son muy resistentes y usan la siguiente tabla de Heridas: 1-2 Derribado, 3 Aturdido, 4-6 Fuera de Combate.",
    "fell-bats--animals": "Los Murciélagos Funestos son animales y nunca ganan experiencia.",
    "fell-bats--flyers": "Los Murciélagos ignoran el terreno cuando se mueven y pueden cargar libremente contra cualquier modelo que puedan ver, sin importar la altura ni los interceptores.",
    "fell-bats--cause-fear": "Los Murciélagos Funestos son criaturas No-Muertas aterradoras y por tanto causan miedo.",
    "fell-bats--may-not-run": "Los Murciélagos Funestos son criaturas No-Muertas y no pueden correr (pero pueden cargar con normalidad).",
    "fell-bats--immune-to-psychology": "Los Murciélagos Funestos no se ven afectados por la psicología y nunca abandonan el combate.",
    "fell-bats--immune-to-poison": "Los Murciélagos Funestos no se ven afectados por ninguna droga o veneno.",
    "fell-bats--no-pain": "Los Murciélagos Funestos tratan un resultado de aturdido en la tabla de Heridas como derribado.",
}

# Ambiguous ids: resolved per band via the "<band>/<rule-id>" keys above.
AMBIGUOUS = {"band--animosity", "band--rulebook-inheritance", "cave-squigs--movement",
             "cave-squigs--minderz", "cave-squigs--animals", "troll--dumb-monster",
             "troll--dumb-monsters", "troll--vomit-attack", "snotling-mob--mob",
             "snotling-mob--weedy", "snotling-mob--dodgy"}

RULE_ID = re.compile(r"^- id: (.+?)\s*$")
ES_INLINE = re.compile(r"^    es: .+")


def wrap(text: str) -> list[str]:
    return textwrap.fill(" ".join(text.split()), width=100,
                         initial_indent="      ", subsequent_indent="      ").splitlines()


def fill_file(path: Path, band: str, write: bool) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    filled, out, i = [], [], 0
    current_rule = None
    while i < len(lines):
        line = lines[i]
        rule = RULE_ID.match(line)
        if rule:
            current_rule = rule.group(1)
        if current_rule:
            key = f"{band}/{current_rule}"
            text = TRANSLATIONS.get(key) if current_rule in AMBIGUOUS else TRANSLATIONS.get(current_rule)
        else:
            text = None
        if text and re.match(r"^  applies_to:", line):
            # Only fill when the rule has no Spanish effect yet.
            rule_start = max((k for k, l in enumerate(out) if RULE_ID.match(l)), default=0)
            block = out[rule_start:]
            has_es = any(
                l.startswith("  effect_i18n:")
                or re.match(r"^    es: ", l)
                for l in block
            ) and any(l.startswith("  effect_i18n:") for l in block)
            already = any(
                l.startswith("  effect_i18n:") for l in block
            )
            if not already:
                out.append("  effect_i18n:")
                out.append("    es: >-")
                out.extend(wrap(text))
                filled.append(f"{band}/{current_rule}")
            out.append(line)
            i += 1
            continue
        out.append(line)
        i += 1
    if filled and write:
        # newline="\n": the maintained YAML is LF-only (see .gitattributes).
        path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    return filled


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply (default: dry run)")
    args = parser.parse_args()
    total = 0
    for band_dir in sorted(STAGING.iterdir()):
        if not band_dir.is_dir():
            continue
        path = band_dir / "special-rules.yaml"
        if not path.exists():
            continue
        filled = fill_file(path, band_dir.name, args.write)
        total += len(filled)
    print(f"{'filled' if args.write else 'would fill'} {total} effect translation(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
