# Prosa retirada de las reglas `rule_ref` de 2B

Decisión (2026-09-15): la KB define una regla que repite una regla compartida como
`rule_ref: <shared-rule.id>` **en lugar de** un `effect` duplicado, y ningún
consumidor renderiza la prosa local —`shared_rule_text`, `catalogue._rule_text` y el
generador web resuelven siempre el registro compartido—. Estas reglas llevaban las
dos cosas, así que la prosa local se retiró para dejar la forma KB exacta.

La redacción de la fuente (EN y su traducción ES) se conserva aquí: la vista no
cambia, porque ese texto ya se ignoraba al renderizar; el texto que se muestra sigue
siendo el de la regla compartida de `sources/knowledge/catalog/rules/special-rules.yaml`.

Regenerable con `python tools/knowledge/strip_rule_ref_restatements.py --tree 2B --write` (idempotente).

## `bretonnian-buccaneers-sar` → `swabbies--never-gain-experience` (`shared-rule.never-gain-experience`)

**Nombre:** Never Gain Experience — ES: Nunca Ganan Experiencia

**EN (fuente):**

> Swabbies never gain experience in games.

**ES (traducción):**

> Los Fregones nunca ganan experiencia en las partidas.

## `call-of-the-night-haint-mim` → `malignant-spirits--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> Malignant Spirits are immune to poison.

**ES (traducción):**

> Los Espíritus Malignos son inmunes al veneno.

## `call-of-the-night-haint-mim` → `mourngul--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> The Mourngul is immune to poison.

**ES (traducción):**

> El Mourngul es inmune al veneno.

## `call-of-the-night-haint-mim` → `poltergeists--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> Poltergeists are immune to poison.

**ES (traducción):**

> Los Poltergeists son inmunes al veneno.

## `call-of-the-night-haint-mim` → `revenants--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> Revenants are immune to poison.

**ES (traducción):**

> Los Espectros son inmunes al veneno.

## `call-of-the-night-haint-mim` → `spirit-hosts--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> Spirit Hosts are immune to poison.

**ES (traducción):**

> Las Huestes de Espíritus son inmunes al veneno.

## `call-of-the-night-haint-mim` → `tomb-banshee--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> The Tomb Banshee is immune to poison.

**ES (traducción):**

> La Banshee de Tumba es inmune al veneno.

## `clan-angrund-kep` → `band--armour` (`shared-rule.armour-2`)

**Nombre:** Armour — ES: Armadura

**EN (fuente):**

> Dwarfs never suffer movement penalties for wearing armour.

**ES (traducción):**

> Los enanos nunca sufren penalizaciones de movimiento por llevar armadura.

## `clan-angrund-kep` → `band--dwarf-special-skills-extra-tough` (`shared-rule.extra-tough`)

**Nombre:** Extra Tough — ES: Extra Resistente

**EN (fuente):**

> This Dwarf is notorious for walking away from wounds that would kill a lesser being. When rolling on the Hero's Serious Injury chart for this Hero after a game in which he has been taken out of action, the dice may be re-rolled once. The result of this second dice roll must be accepted, even if it is a worse result.

**ES (traducción):**

> Este Enano es conocido por sobrevivir a heridas que matarían a un ser inferior. Al tirar en la tabla de Heridas Graves del Héroe tras una partida en la que haya quedado Fuera de Combate, se puede repetir el dado una vez. El resultado de esta segunda tirada debe aceptarse, incluso si es peor.

## `clan-angrund-kep` → `band--dwarf-special-skills-resource-hunter` (`shared-rule.resource-hunter`)

**Nombre:** Resource Hunter — ES: Cazador de Recursos

**EN (fuente):**

> This Dwarf is especially adept at locating valuable resources. When rolling on the Exploration chart at the end of a game, the Hero may modify one die roll by +1/-1.

**ES (traducción):**

> Este Enano es especialmente hábil localizando recursos valiosos. Al tirar en la tabla de Exploración al final de una partida, el Héroe puede modificar una tirada de dado en +1/-1.

## `clan-angrund-kep` → `band--dwarf-special-skills-thick-skull` (`shared-rule.thick-skull`)

**Nombre:** Thick Skull — ES: Cabeza dura (Thick Skull)

**EN (fuente):**

> This Dwarf's head is exceptionally well adapted to knocks. If he is stunned, treat a stunned result as knocked down instead. If the Dwarf also wears a helmet, this save is 2+ instead of 4+ (this takes the place of the normal helmet special rule).

**ES (traducción):**

> La cabeza de este Enano está excepcionalmente bien adaptada a los golpes. Si queda aturdido, trata un resultado de aturdido como derribado en su lugar. Si el Enano además lleva casco, esta salvación es de 2+ en lugar de 4+ (esto sustituye a la regla especial normal del casco).

## `clan-angrund-kep` → `band--dwarf-special-skills-true-grit` (`shared-rule.hard-as-steel`)

**Nombre:** True Grit — ES: Entereza (True Grit)

**EN (fuente):**

> Dwarfs are hardy individuals and this Hero is hardy even for a Dwarf! When rolling on the injury table for this Hero, a roll of 1-3 is treated as knocked down, 4-5 as stunned, and 6 as out of action.

**ES (traducción):**

> Los Enanos son individuos duros, ¡y este Héroe es duro incluso para ser un Enano! Al tirar en la tabla de heridas para este Héroe, un resultado de 1-3 se trata como derribado, 4-5 como aturdido y 6 como Fuera de Combate.

## `clan-angrund-kep` → `band--grudgebearers` (`shared-rule.grudgebearers`)

**Nombre:** Grudgebearers — ES: Portadores del Agravio

**EN (fuente):**

> Dwarfs hold an ancient grudge against Elves from the days when the two races fought for supremacy in the Old World. A Dwarf warband may never include any kind of Elven Hired Sword or Dramatis Personae.

**ES (traducción):**

> Los Enanos guardan un antiguo agravio contra los Elfos desde los días en que ambas razas lucharon por la supremacía en el Viejo Mundo. Una banda de Enanos no puede incluir nunca ningún tipo de Espada Contratada Elfa ni Dramatis Personae.

## `clan-angrund-kep` → `band--hard-head` (`shared-rule.hard-head-2`)

**Nombre:** Hard Head — ES: Cabeza Dura

**EN (fuente):**

> Dwarfs ignore the special rules for maces, clubs... They are hard to knock out!

**ES (traducción):**

> Los Enanos ignoran las reglas especiales de mazas, garrotes, etc. ¡Es difícil dejarlos inconscientes!

## `clan-angrund-kep` → `band--hard-to-kill` (`shared-rule.hard-to-kill`)

**Nombre:** Hard to Kill — ES: Difíciles de Matar

**EN (fuente):**

> Dwarfs are tough, resilient individuals who can only be taken out of action on a roll of 6 instead of 5-6 when rolling on the Injury chart. Treat a roll of 1-2 as knocked down, 3-5 as stunned, and 6 as out of action.

**ES (traducción):**

> Los enanos son individuos duros y resistentes que solo pueden ser dejados fuera de combate con un resultado de 6 en lugar de 5-6 al tirar en la tabla de Heridas. Trata un resultado de 1-2 como derribado, 3-5 como aturdido y 6 como fuera de combate.

## `clan-angrund-kep` → `band--incomparable-miners` (`shared-rule.incomparable-miners`)

**Nombre:** Incomparable Miners — ES: Mineros Incomparables

**EN (fuente):**

> Dwarfs spend much of their lives underground searching for precious minerals, and they are the best in the world at this kind of work. In the City of Mordheim they apply similar skills to the search for wyrdstone. When checking for treasure at the end of a game, add +1 to the number of pieces found for a Dwarf warband.

**ES (traducción):**

> Los Enanos pasan gran parte de sus vidas bajo tierra buscando minerales preciosos, y son los mejores del mundo en este tipo de trabajo. En la Ciudad de los Condenados aplican habilidades similares a la búsqueda de piedra bruja. Al buscar tesoros al final de una partida, suma +1 al número de piezas encontradas para una banda de Enanos.

## `clan-angrund-kep` → `dwarf-troll-slayers--deathwish` (`shared-rule.deathwish`)

**Nombre:** Deathwish — ES: Deseo de Muerte

**EN (fuente):**

> Troll slayers seek an honourable death in combat. They are completely immune to all psychology and never need to test if fighting alone.

**ES (traducción):**

> Los Matatrolles buscan una muerte honorable en combate. Son completamente inmunes a toda la psicología y nunca necesitan hacer chequeos si luchan solos.

## `clockworkers-sc` → `dwarf-engineer--armour` (`shared-rule.armour-2`)

**Nombre:** Armour — ES: Armadura

**EN (fuente):**

> Dwarfs never suffer movement penalties for wearing armour.

**ES (traducción):**

> Los enanos nunca sufren penalizaciones de movimiento por llevar armadura.

## `clockworkers-sc` → `dwarf-engineer--hard-head` (`shared-rule.hard-head-2`)

**Nombre:** Hard Head — ES: Cabeza Dura

**EN (fuente):**

> Dwarfs ignore the special rules for maces, clubs, etc. They are not easy to knock out!

**ES (traducción):**

> Los enanos ignoran las reglas especiales de mazas, garrotes, etc. ¡No es fácil dejarlos inconscientes!

## `clockworkers-sc` → `dwarf-engineer--hard-to-kill` (`shared-rule.hard-to-kill`)

**Nombre:** Hard to Kill — ES: Difícil de Matar

**EN (fuente):**

> Dwarfs can only be taken out of action on a roll of 6 instead of 5-6 on the Injury chart. Treat a roll of 1-2 as knocked down, 3-5 as stunned, and 6 as out of action.

**ES (traducción):**

> Los enanos solo quedan Fuera de combate con un resultado de 6 en lugar de 5-6 en la tabla de Heridas. Trata un 1-2 como derribado, un 3-5 como aturdido y un 6 como Fuera de combate.

## `crooked-moon-kep` → `cave-squigs--minderz` (`shared-rule.minderz`)

**Nombre:** Minderz — ES: Cuidadores

**EN (fuente):**

> Each Cave Squig must always remain within 6" of a Night Goblin. If a Cave Squig finds itself without a Goblin within 6" at the start of its movement phase, it will go wild. From that point on, move the Squig 2D6" in a random direction during all its movement phases. If its random movement takes it into contact with another model (friend or foe), it will engage that model in hand-to-hand combat as normal.

**ES (traducción):**

> Cada Squig de Cueva debe permanecer siempre a 6" de un Goblin Nocturno. Si un Squig de Cueva se encuentra sin un Goblin a 6" al inicio de su fase de movimiento, se volverá salvaje. A partir de ese momento, mueve al Squig 2D6" en una dirección aleatoria durante todas sus fases de movimiento. Si su movimiento aleatorio lo lleva al contacto con otro modelo (amigo o enemigo), se enfrentará a ese modelo en combate cuerpo a cuerpo con normalidad.

## `crooked-moon-kep` → `snotling-mob--weedy` (`shared-rule.weedy`)

**Nombre:** Weedy — ES: Flojitos

**EN (fuente):**

> If wounded they add +1 on the injury table.

**ES (traducción):**

> Si resultan heridos suman +1 en la tabla de heridas.

## `crooked-moon-kep` → `troll--always-hungry` (`shared-rule.always-hungry`)

**Nombre:** Always Hungry — ES: Siempre Hambriento

**EN (fuente):**

> A Troll requires an upkeep cost. This upkeep represents the copious amount of food that must be fed to the Troll in order to keep him loyal to the warband. The warband must pay 15 gc after every game in order to keep the Troll. If the warband lacks the gold to pay the upkeep, the Big Boss has the option of sacrificing three Snotlings or two Cave Squigs to the Troll in lieu of buying food (Trolls eat nearly anything). If this food isn't paid (either in gold or warband members), the Troll gets hungry and wanders off in search of food.

**ES (traducción):**

> Un Troll requiere un coste de manutención. Esta manutención representa la enorme cantidad de comida que debe darse al Troll para mantenerlo leal a la banda. La banda debe pagar 15 coronas después de cada partida para mantener al Troll. Si la banda carece de oro para pagar la manutención, el Gran Jefe tiene la opción de sacrificar tres Snotlings o dos Squigs de Cueva al Troll en lugar de comprar comida (los Trolls comen casi cualquier cosa). Si no se paga esta comida (ya sea en oro o en miembros de la banda), el Troll pasa hambre y se marcha en busca de alimento.

## `crooked-moon-kep` → `troll--dumb-monster` (`shared-rule.dumb-monster`)

**Nombre:** Dumb Monster — ES: Monstruo Tonto

**EN (fuente):**

> A Troll is far too stupid to ever learn any new skills. Trolls do not gain experience.

**ES (traducción):**

> Un Troll es demasiado estúpido para aprender alguna habilidad nueva. Los Trolls no ganan experiencia.

## `crooked-moon-kep` → `troll--fear` (`shared-rule.fear`)

**Nombre:** Fear — ES: Miedo

**EN (fuente):**

> Trolls are frightening monsters, which cause fear.

**ES (traducción):**

> Los Trolls son monstruos aterradores, que causan miedo.

## `crooked-moon-kep` → `troll--regeneration` (`shared-rule.regeneration`)

**Nombre:** Regeneration — ES: Regeneración

**EN (fuente):**

> Trolls have a unique physiology that allows them to regenerate wounds. Whenever an enemy succeeds in fully inflicting a wound on a Troll, roll a D6; on a result of 4 or more the wound is ignored and the Troll is unhurt. Trolls may not regenerate wounds caused by fire or fire-based magic. Trolls never roll for injury after a battle.

**ES (traducción):**

> Los Trolls tienen una fisiología única que les permite regenerar heridas. Siempre que un enemigo logre infligir completamente una herida a un Troll, tira 1D6; con un resultado de 4 o más la herida se ignora y el Troll no sufre daño. Los Trolls no pueden regenerar heridas causadas por fuego o magia de fuego. Los Trolls nunca tiran por heridas tras una batalla.

## `crooked-moon-kep` → `troll--stupidity` (`shared-rule.stupidity`)

**Nombre:** Stupidity — ES: Estupidez

**EN (fuente):**

> A Troll is subject to the rules for stupidity.

**ES (traducción):**

> Un Troll está sujeto a las reglas de estupidez.

## `crooked-moon-kep` → `troll--vomit-attack` (`shared-rule.vomit-attack`)

**Nombre:** Vomit Attack — ES: Ataque de Vómito

**EN (fuente):**

> Instead of his normal attacks, a Troll can regurgitate its highly corrosive digestive juices on an unfortunate hand-to-hand combat opponent. This is a single attack that automatically hits with a Strength of 5 and ignores armour saves.

**ES (traducción):**

> En lugar de sus ataques normales, un Troll puede regurgitar sus altamente corrosivos jugos digestivos sobre un desafortunado oponente de combate cuerpo a cuerpo. Este es un único ataque que impacta automáticamente con una Fuerza de 5 e ignora las salvaciones por armadura.

## `fallen-the-rel` → `revenant--no-pain` (`shared-rule.no-pain`)

**Nombre:** No Pain — ES: Sin Dolor

**EN (fuente):**

> Revenants treat a 'stunned' result on the Injury chart as 'knocked down'.

**ES (traducción):**

> Los Espectros tratan un resultado 'aturdido' en la tabla de Heridas como 'derribado'.

## `fen-guard-mim` → `treekin--may-not-run` (`shared-rule.may-not-run`)

**Nombre:** May Not Run — ES: No Puede Correr

**EN (fuente):**

> Treekin may not run, but may charge as normal.

**ES (traducción):**

> Los Hombres Árbol no pueden correr, pero pueden cargar con normalidad.

## `guild-of-disgraced-engineers-mim` → `band--armour` (`shared-rule.armour-2`)

**Nombre:** Armour — ES: Armadura

**EN (fuente):**

> Dwarfs never suffer movement penalties for wearing armour.

**ES (traducción):**

> Los enanos nunca sufren penalizaciones de movimiento por llevar armadura.

## `high-elves-lus` → `loremaster--wizard` (`shared-rule.wizard`)

**Nombre:** Wizard — ES: Mago

**EN (fuente):**

> The Loremaster is a wizard and may use High Elf Magic. He starts with one High Magic spell; whenever he gains a new spell he may choose from either the High Elf Magic or the Lesser Magic spell lists.

**ES (traducción):**

> El Maestro del Saber es un mago y puede usar la Magia de los Altos Elfos. Comienza con un hechizo de Magia Superior; cada vez que gana un hechizo nuevo puede elegir de las listas de Magia de los Altos Elfos o de Magia Menor.

## `metal-mongers-mim` → `machine-ogre--no-brain` (`shared-rule.brainless`)

**Nombre:** No Brain — ES: Sin Cerebro

**EN (fuente):**

> Machine-Ogres never gain experience.

**ES (traducción):**

> Los Ogros Mecánicos nunca ganan experiencia.

## `night-goblins-kaz` → `cave-squigs--minderz` (`shared-rule.minderz`)

**Nombre:** Minderz — ES: Cuidadores

**EN (fuente):**

> Each Cave Squig must always remain within 6\" of a Night Goblin, who keeps the creature in line. If a Cave Squig finds itself without a Goblin within 6\" at the start of its Movement phase, it will go wild. From that point on, move the Squig 2D6\" in a random direction during each of its movement phases. If its random movement takes it into contact with another model (friend or foe), it will engage the model in hand-to-hand combat as normal. The Cave Squig is out of the Night Goblin player's control until the end of the game.

**ES (traducción):**

> Cada Squig de Cueva debe permanecer siempre a 6" de un Goblin Nocturno, que mantiene a la criatura a raya. Si un Squig de Cueva se encuentra sin un Goblin a 6" al inicio de su fase de Movimiento, se volverá salvaje. A partir de ese momento, mueve al Squig 2D6" en una dirección aleatoria durante cada una de sus fases de movimiento. Si su movimiento aleatorio lo lleva al contacto con otro modelo (amigo o enemigo), se enfrentará al modelo en combate cuerpo a cuerpo con normalidad. El Squig de Cueva queda fuera del control del jugador de Goblins Nocturnos hasta el final de la partida.

## `night-goblins-kaz` → `cave-squigs--movement` (`shared-rule.movement`)

**Nombre:** Movement — ES: Movimiento

**EN (fuente):**

> Cave Squigs do not have a set Movement characteristic but move with an ungainly bouncing stride. To represent this, when moving Squigs, roll 2D6 for the distance they move. Squigs never run and never declare charges. Instead they are allowed to contact enemy models within their normal 2D6\" movement. If this happens, they count as charging for the following round of close combat, just as if they had declared a charge.

**ES (traducción):**

> Los Squigs de Cueva no tienen una característica de Movimiento fija, sino que se mueven con una zancada rebotante torpe. Para representar esto, al mover Squigs tira 2D6 por la distancia que se mueven. Los Squigs nunca corren ni declaran cargas. En su lugar, se les permite contactar con modelos enemigos dentro de su movimiento normal de 2D6". Si esto ocurre, cuentan como que cargan para la siguiente ronda de combate cuerpo a cuerpo, igual que si hubieran declarado una carga.

## `night-goblins-kaz` → `snotling-mob--weedy` (`shared-rule.weedy`)

**Nombre:** Weedy — ES: Flojitos

**EN (fuente):**

> Snotlings are not the most robust of creatures. If wounded they will be knocked down on a 1, stunned on a 2-3 and go out of action on a 4-6.

**ES (traducción):**

> Los Snotlings no son las criaturas más robustas. Si resultan heridos quedarán derribados con un 1, aturdidos con un 2-3 y Fuera de Combate con un 4-6.

## `night-goblins-kaz` → `troll--always-hungry` (`shared-rule.always-hungry`)

**Nombre:** Always Hungry — ES: Siempre Hambriento

**EN (fuente):**

> A Troll requires an upkeep cost. The warband must pay 15 gc after every game in order to keep the Troll. If the warband lacks the gold to pay the upkeep, the Big Boss has the option of sacrificing three Snotlings or two Cave Squigs to the Troll in lieu of buying food (Trolls eat nearly anything). If this fee is not paid (either in gold or warband members) the Troll gets hungry and wanders off in search of food.

**ES (traducción):**

> Un Troll requiere un coste de manutención. Esta manutención representa la enorme cantidad de comida que debe darse al Troll para mantenerlo leal a la banda. La banda debe pagar 15 coronas después de cada partida para mantener al Troll. Si la banda carece de oro para pagar la manutención, el Gran Jefe tiene la opción de sacrificar tres Snotlings o dos Squigs de Cueva al Troll en lugar de comprar comida (los Trolls comen casi cualquier cosa). Si no se paga esta comida (ya sea en oro o en miembros de la banda), el Troll pasa hambre y se marcha en busca de alimento.

## `night-goblins-kaz` → `troll--regeneration` (`shared-rule.regeneration`)

**Nombre:** Regeneration — ES: Regeneración

**EN (fuente):**

> Trolls have a unique physiology that allows them to regenerate wounds. Whenever an enemy successfully inflicts a wound on a Troll roll a D6; on a result of 4 or more the wound is ignored and the Troll is unhurt. Trolls may not regenerate wounds caused by fire or fire-based magic. Trolls never roll for injury after a battle.

**ES (traducción):**

> Los Trolls tienen una fisiología única que les permite regenerar heridas. Siempre que un enemigo logre infligir completamente una herida a un Troll, tira 1D6; con un resultado de 4 o más la herida se ignora y el Troll no sufre daño. Los Trolls no pueden regenerar heridas causadas por fuego o magia de fuego. Los Trolls nunca tiran por heridas tras una batalla.

## `night-goblins-kaz` → `troll--stupidity` (`shared-rule.stupidity-2`)

**Nombre:** Stupidity — ES: Estupidez

**EN (fuente):**

> A Troll is subject to the rules for stupidity.

**ES (traducción):**

> Un Troll está sujeto a las reglas de estupidez.

## `night-goblins-kaz` → `troll--vomit-attack` (`shared-rule.vomit-attack`)

**Nombre:** Vomit Attack — ES: Ataque de Vómito

**EN (fuente):**

> Instead of his normal attacks, a Troll can regurgitate its highly corrosive digestive juices on an unfortunate hand-to-hand combat opponent. This is a single attack that automatically hits with a Strength of 5 and ignores armour saves.

**ES (traducción):**

> En lugar de sus ataques normales, un Troll puede regurgitar sus altamente corrosivos jugos digestivos sobre un desafortunado oponente de combate cuerpo a cuerpo. Este es un único ataque que impacta automáticamente con una Fuerza de 5 e ignora las salvaciones por armadura.

## `sartosan-pirates-sar` → `swabbies--never-gain-experience` (`shared-rule.never-gain-experience`)

**Nombre:** Never Gain Experience — ES: Nunca Ganan Experiencia

**EN (fuente):**

> Swabbies never gain experience in games.

**ES (traducción):**

> Los Fregones nunca ganan experiencia en las partidas.

## `skaven-of-clan-mors-kaz` → `rat-ogre--experience` (`shared-rule.experience`)

**Nombre:** Experience — ES: Experiencia

**EN (fuente):**

> Rat Ogres do not gain experience.

**ES (traducción):**

> Los Ogros Rata no ganan experiencia.

## `skaven-of-clan-mors-kaz` → `rat-ogre--stupidity` (`shared-rule.stupidity`)

**Nombre:** Stupidity — ES: Estupidez

**EN (fuente):**

> A Rat Ogre is subject to stupidity unless a Skaven Hero is within 6\" of it.

**ES (traducción):**

> Un Ogro Rata está sujeto a estupidez a menos que un Héroe Skaven esté a 6" de él.

## `skaven-of-clan-pestilens-lus` → `plague-priest--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6 inches may use the Plague Priest's Leadership instead of their own.

**ES (traducción):**

> Cualquier modelo de la banda a 6 pulgadas puede usar el Liderazgo del Sacerdote de la Peste en lugar del suyo.

## `skaven-of-clan-pestilens-mou` → `plague-priest--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Plague Priest may use his Leadership value when taking Leadership tests.

**ES (traducción):**

> Cualquier guerrero a 6 pulgadas del Sacerdote de la Peste puede usar su valor de Liderazgo cuando haga pruebas de Liderazgo.

## `skaven-of-clan-pristekk-sc` → `chieftain--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6 inches of the Chieftain may use his Leadership instead of his own.

**ES (traducción):**

> Cualquier guerrero a 6 pulgadas del Jefe de Clan puede usar su Liderazgo en lugar del propio.

## `skaven-of-clan-pristekk-sc` → `rat-ogres--experience` (`shared-rule.experience`)

**Nombre:** Experience — ES: Experiencia

**EN (fuente):**

> Rat Ogres do not gain experience.

**ES (traducción):**

> Los Ogros Rata no ganan experiencia.

## `skaven-of-clan-pristekk-sc` → `rat-ogres--large-target` (`shared-rule.large-target`)

**Nombre:** Large Target — ES: Objetivo Grande

**EN (fuente):**

> Rat Ogres are Large Targets as defined in the shooting rules.

**ES (traducción):**

> Los Ogros Rata son Objetivos Grandes según se define en las reglas de disparo.

## `skaven-of-clan-pristekk-sc` → `rat-ogres--stupidity` (`shared-rule.stupidity`)

**Nombre:** Stupidity — ES: Estupidez

**EN (fuente):**

> A Rat Ogre is subject to stupidity unless a Skaven Hero is within 6 inches of it.

**ES (traducción):**

> Un Ogro Rata está sujeto a estupidez salvo que haya un héroe skaven a 6 pulgadas de él.

## `skaven-of-clan-skryre-kaz` → `master-engineer--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any model in the warband within 6\" of the Master Engineer may use his Leadership instead of their own.

**ES (traducción):**

> Cualquier modelo de la banda a 6" del Ingeniero Maestro puede usar su Liderazgo en lugar del propio.

## `skaven-of-clan-skryre-kaz` → `skavenslaves--experience` (`shared-rule.experience`)

**Nombre:** Experience — ES: Experiencia

**EN (fuente):**

> Skavenslaves are little better than animals and do not gain experience.

**ES (traducción):**

> Los Esclavos Skaven son poco mejor que animales y no ganan experiencia.

## `skaven-of-clan-skryre-kaz` → `warlock-engineer--wizard` (`shared-rule.wizard`)

**Nombre:** Wizard — ES: Hechicero

**EN (fuente):**

> A Warlock Engineer is a wizard and uses the Magic of the Horned Rat. See the Magic section of the rulebook for details.

**ES (traducción):**

> Un Ingeniero Hechicero es un Hechicero y usa la Magia de la Rata Cuernuda. Consulta la sección de Magia del libro de reglas para más detalles.

## `skaven-of-clan-skryre-rel` → `warlock-engineer--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Warlock Engineer may use his Leadership instead of his own.

**ES (traducción):**

> Cualquier guerrero a 6" del Ingeniero Hechicero puede usar su Liderazgo en lugar del propio.

## `strigoi-kaz` → `bats--living` (`shared-rule.living`)

**Nombre:** Living — ES: Vivientes

**EN (fuente):**

> The Bats are living beings and none of the Undead rules apply.

**ES (traducción):**

> Los Murciélagos son seres vivientes y ninguna de las reglas de No-Muertos les afecta.

## `strigoi-kaz` → `fell-bats--cause-fear` (`shared-rule.cause-fear-2`)

**Nombre:** Cause Fear — ES: Causan Miedo

**EN (fuente):**

> Fell Bats are terrifying Undead creatures and therefore cause fear.

**ES (traducción):**

> Los Murciélagos Funestos son criaturas No-Muertas aterradoras y por tanto causan miedo.

## `strigoi-kaz` → `fell-bats--immune-to-poison` (`shared-rule.immune-to-poison-3`)

**Nombre:** Immune to Poison — ES: Inmunes al Veneno

**EN (fuente):**

> Fell Bats are not affected by any drug or poison.

**ES (traducción):**

> Los Murciélagos Funestos no se ven afectados por ninguna droga o veneno.

## `strigoi-kaz` → `fell-bats--immune-to-psychology` (`shared-rule.immune-to-psychology-4`)

**Nombre:** Immune to Psychology — ES: Inmunes a la Psicología

**EN (fuente):**

> Fell Bats are not affected by psychology and never leave combat.

**ES (traducción):**

> Los Murciélagos Funestos no se ven afectados por la psicología y nunca abandonan el combate.

## `strigoi-kaz` → `fell-bats--may-not-run` (`shared-rule.may-not-run`)

**Nombre:** May Not Run — ES: No Pueden Correr

**EN (fuente):**

> Fell Bats are Undead creatures and may not run (but may charge normally).

**ES (traducción):**

> Los Murciélagos Funestos son criaturas No-Muertas y no pueden correr (pero pueden cargar con normalidad).

## `strigoi-kaz` → `fell-bats--no-pain` (`shared-rule.no-pain`)

**Nombre:** No Pain — ES: Sin Dolor

**EN (fuente):**

> Fell Bats treat a stunned result on the Injury chart as knocked down.

**ES (traducción):**

> Los Murciélagos Funestos tratan un resultado de aturdido en la tabla de Heridas como derribado.

## `strigoi-kaz` → `skeletons--no-brain` (`shared-rule.brainless`)

**Nombre:** No Brain — ES: Sin Cerebro

**EN (fuente):**

> Skeletons never gain experience. They do not learn from their mistakes. What did you expect?

**ES (traducción):**

> Los Esqueletos nunca ganan experiencia. No aprenden de sus errores. ¿Qué esperabas?

## `strigoi-kaz` → `skeletons--no-pain` (`shared-rule.no-pain`)

**Nombre:** No Pain — ES: Sin Dolor

**EN (fuente):**

> Skeletons treat a stunned result on the Injury chart as knocked down.

**ES (traducción):**

> Los Esqueletos tratan un resultado de aturdido en la tabla de Heridas como derribado.

## `turjuk-rel` → `emir--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Emir may use his Leadership characteristic when taking Leadership tests.

**ES (traducción):**

> Cualquier guerrero a 6" del Emir puede usar su característica de Liderazgo al realizar chequeos de Liderazgo.

## `underworld-alliance-mim` → `goblin-bully--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any Goblin Warrior within 6 inches of the Bully may use his Leadership value when taking Leadership tests.

**ES (traducción):**

> Cualquier guerrero goblin a 6 pulgadas del Matón puede usar su valor de Liderazgo en los chequeos de Liderazgo.

## `underworld-alliance-mim` → `skaven-slum-lord--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any Skaven Warrior within 6 inches of the Slave King may use his Leadership value when taking Leadership tests.

**ES (traducción):**

> Cualquier guerrero skaven a 6 pulgadas del Rey Esclavo puede usar su valor de Liderazgo en los chequeos de Liderazgo.

## `underworld-alliance-mim` → `warpstone-troll--fear` (`shared-rule.fear`)

**Nombre:** Fear — ES: Miedo

**EN (fuente):**

> Warpstone Trolls are frightening monsters which cause fear.

**ES (traducción):**

> Los Trolls de Piedra Bruja son monstruos aterradores que causan miedo.

## `underworld-alliance-mim` → `warpstone-troll--large-target` (`shared-rule.large-target`)

**Nombre:** Large Target — ES: Objetivo Grande

**EN (fuente):**

> Warpstone Trolls are Large Targets as defined in the shooting rules.

**ES (traducción):**

> Los Trolls de Piedra Bruja son Objetivos Grandes según se define en las reglas de disparo.

## `underworld-alliance-mim` → `warpstone-troll--stupidity` (`shared-rule.stupidity-2`)

**Nombre:** Stupidity — ES: Estupidez

**EN (fuente):**

> A Warpstone Troll is subject to the rules for stupidity.

**ES (traducción):**

> Un Troll de Piedra Bruja está sujeto a las reglas de estupidez.

## `underworld-alliance-mim` → `warpstone-troll--vomit-attack` (`shared-rule.vomit-attack`)

**Nombre:** Vomit Attack — ES: Ataque de Vómito

**EN (fuente):**

> Instead of his normal attacks, a Warpstone Troll can regurgitate its highly corrosive digestive juices on an unfortunate opponent: a single attack that automatically hits with Strength 5 and ignores armour saves.

**ES (traducción):**

> En lugar de sus ataques normales, un Troll de Piedra Bruja puede regurgitar sus jugos digestivos, altamente corrosivos, sobre un desdichado oponente: un único ataque que impacta automáticamente con Fuerza 5 e ignora las salvaciones por armadura.

## `wasteland-privateers-sar` → `captain--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any pirate within 6" of the Captain may use his Leadership characteristic when taking any Leadership tests.

**ES (traducción):**

> Cualquier pirata a 6" del Capitán puede usar su característica de Liderazgo en cualquier chequeo de Liderazgo.

## `wasteland-privateers-sar` → `swabbies--never-gain-experience` (`shared-rule.never-gain-experience`)

**Nombre:** Never Gain Experience — ES: Nunca Ganarán Experiencia

**EN (fuente):**

> Swabbies generally aren't interested in proving their worth to the crew, they are interested in survival and hopefully escape! Swabbies never gain experience in games.

**ES (traducción):**

> Los Fregones no están interesados en demostrar su valor a la tripulación, ¡les interesa sobrevivir y escapar si pueden! Los Fregones nunca ganan experiencia en las partidas.

## `watchmen-mim` → `turnkeys--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> After developing a resistance during years of contraband substance abuse, Turnkeys are not affected by any poison.

**ES (traducción):**

> Tras desarrollar resistencia durante años de abuso de sustancias de contrabando, los Carceleros no se ven afectados por ningún veneno.

## `watchmen-mim` → `watch-captain--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6 inches of the Watch Captain may use his Leadership value instead of his own when taking Leadership tests.

**ES (traducción):**

> Cualquier guerrero a 6 pulgadas del Capitán de la Guardia puede usar su valor de Liderazgo en los chequeos de Liderazgo.

