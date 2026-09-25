# Prosa retirada de las reglas `rule_ref` de 2A

Decisión (2026-09-15): la KB define una regla que repite una regla compartida como
`rule_ref: <shared-rule.id>` **en lugar de** un `effect` duplicado, y ningún
consumidor renderiza la prosa local —`shared_rule_text`, `catalogue._rule_text` y el
generador web resuelven siempre el registro compartido—. Estas reglas llevaban las
dos cosas, así que la prosa local se retiró para dejar la forma KB exacta.

La redacción de la fuente (EN y su traducción ES) se conserva aquí: la vista no
cambia, porque ese texto ya se ignoraba al renderizar; el texto que se muestra sigue
siendo el de la regla compartida de `sources/knowledge/catalog/rules/special-rules.yaml`.

El invariante se comprueba con `python tools/knowledge/audit_kb_conformance.py --tree 2A`.

## `dreamwalkers-cult-of-morr-fbg` → `dreamer--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Dreamer may use his Leadership instead of his own.

**ES (traducción):**

> Cualquier guerrero a 6" o menos del Soñador puede usar su Liderazgo en lugar del propio.

## `druchii-mic` → `noble--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6" of the Noble may use his Leadership instead of their own.

**ES (traducción):**

> Cualquier modelo de la banda que esté a 6" del Noble puede usar su Liderazgo en lugar del propio.

## `dwarf-slayer-cult-web` → `band--grudgebearers` (`shared-rule.grudgebearers`)

**Nombre:** Grudgebearers — ES: Portadores del Agravio

**EN (fuente):**

> Dwarfs hold an ancient grudge against Elves from the days when the two races fought for supremacy in the Old World. A Dwarf warband may never include any kind of Elven Hired Sword or Dramatis Personae.

**ES (traducción):**

> Los enanos guardan un antiguo agravio contra los Elfos desde los días en que ambas razas lucharon por la supremacía en el Viejo Mundo. Una banda Enana no puede incluir nunca ningún tipo de Espada a Sueldo Elfa ni Dramatis Personae.

## `dwarf-slayer-cult-web` → `band--hard-head` (`shared-rule.hard-head-2`)

**Nombre:** Hard Head — ES: Cabeza Dura

**EN (fuente):**

> Dwarfs ignore the special rules for maces, clubs, etc. They are not easy to knock out!

**ES (traducción):**

> Los enanos ignoran las reglas especiales de mazas, garrotes, etc. ¡No es fácil dejarlos inconscientes!

## `dwarf-slayer-cult-web` → `band--hard-to-kill` (`shared-rule.hard-to-kill`)

**Nombre:** Hard to Kill — ES: Difícil de Matar

**EN (fuente):**

> Dwarfs are tough, resilient individuals who can only be taken out of action on a roll of 6 instead of 5-6 when rolling on the Injury chart. Treat a roll of 1-2 as knocked down, 3-5 as stunned, and 6 as out of action.

**ES (traducción):**

> Los enanos son individuos duros y resistentes que solo pueden ser dejados fuera de combate con un resultado de 6 en lugar de 5-6 al tirar en la tabla de Heridas. Trata un resultado de 1-2 como derribado, 3-5 como aturdido y 6 como fuera de combate.

## `dwarf-slayer-cult-web` → `giant-slayer--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6" of the Giant Slayer may use his Leadership instead of their own.

**ES (traducción):**

> Cualquier modelo de la banda a 6" del Gran Matatrolles puede usar su Liderazgo en lugar del propio.

## `halflings-mic` → `halfling-elder--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Elder may use his Leadership when taking a Leadership test.

**ES (traducción):**

> Cualquier guerrero a 6" del Anciano puede usar su Liderazgo al hacer una prueba de Liderazgo.

## `masters-of-horror-sylv` → `mad-scientist--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6" of the Mad Scientist may use his Leadership value.

**ES (traducción):**

> Cualquier modelo de la banda que esté a 6" del Científico Loco puede usar su valor de Liderazgo.

## `mazzalupo-web` → `black-sheep--animals` (`shared-rule.animal`)

**Nombre:** Animals — ES: Animales

**EN (fuente):**

> Black sheep are animals and do not gain experience.

**ES (traducción):**

> Las ovejas negras son animales y no ganan experiencia.

## `mazzalupo-web` → `black-sheep--stupidity` (`shared-rule.stupidity`)

**Nombre:** Stupidity — ES: Estupidez

**EN (fuente):**

> A Black sheep is subject to stupidity unless a Sheepherder is within 6" of it.

**ES (traducción):**

> Una Oveja Negra está sujeta a estupidez a menos que haya un Pastor a 6" de ella.

## `mazzalupo-web` → `wandering-knight--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6" of the Wandering knight may use the Wandering knight's Leadership instead of their own.

**ES (traducción):**

> Cualquier modelo de la banda a 6" del Caballero Errante puede usar el valor de Liderazgo del Caballero Errante en lugar del suyo.

## `necrarchs-the-soul-stealers-lotd1` → `abomination--cause-fear` (`shared-rule.cause-fear-2`)

**Nombre:** Cause Fear — ES: Causan Miedo

**EN (fuente):**

> Abominations are terrifying Undead creatures and thus cause Fear.

**ES (traducción):**

> Las Abominaciones son criaturas No-Muertas aterradoras y por tanto causan miedo.

## `necrarchs-the-soul-stealers-lotd1` → `abomination--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmunes al Veneno

**EN (fuente):**

> Abominations are immune to poisons.

**ES (traducción):**

> Las Abominaciones son inmunes a los venenos.

## `necrarchs-the-soul-stealers-lotd1` → `abomination--immune-to-psychology` (`shared-rule.immune-to-psychology`)

**Nombre:** Immune to Psychology — ES: Inmunes a la Psicología

**EN (fuente):**

> Abominations are not affected by psychology.

**ES (traducción):**

> Las Abominaciones no se ven afectadas por la psicología.

## `necrarchs-the-soul-stealers-lotd1` → `abomination--large-target` (`shared-rule.large-target`)

**Nombre:** Large Target — ES: Objetivo Grande

**EN (fuente):**

> Abominations are Large Targets as defined in the shooting rules.

**ES (traducción):**

> Las Abominaciones son Objetivos Grandes según se define en las reglas de disparo.

## `necrarchs-the-soul-stealers-lotd1` → `abomination--no-pain` (`shared-rule.no-pain`)

**Nombre:** No Pain — ES: Sin Dolor

**EN (fuente):**

> Abominations treat Stunned results as Knocked Down.

**ES (traducción):**

> Las Abominaciones tratan los resultados de Aturdido como Derribado.

## `necrarchs-the-soul-stealers-lotd1` → `necrarch-vampire--cause-fear` (`shared-rule.cause-fear-2`)

**Nombre:** Cause Fear — ES: Causa Miedo

**EN (fuente):**

> Vampires are terrifying Undead creatures and thus cause Fear.

**ES (traducción):**

> Los Vampiros son criaturas No-Muertas aterradoras y por tanto causan miedo.

## `necrarchs-the-soul-stealers-lotd1` → `necrarch-vampire--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> Vampires are not affected by any poison.

**ES (traducción):**

> Los Vampiros no se ven afectados por ningún veneno.

## `necrarchs-the-soul-stealers-lotd1` → `necrarch-vampire--immune-to-psychology` (`shared-rule.immune-to-psychology`)

**Nombre:** Immune to Psychology — ES: Inmune a la Psicología

**EN (fuente):**

> Vampires are not affected by psychology (such as fear) and never leave combat.

**ES (traducción):**

> Los Vampiros no se ven afectados por la psicología (como el miedo) y nunca abandonan el combate.

## `necrarchs-the-soul-stealers-lotd1` → `necrarch-vampire--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6 inches of the Necrarch Vampire may use his Leadership instead of their own.

**ES (traducción):**

> Cualquier miniatura de la banda a 6 pulgadas del Vampiro Necrarca puede usar su Liderazgo en lugar del propio.

## `necrarchs-the-soul-stealers-lotd1` → `necrarch-vampire--no-pain` (`shared-rule.no-pain`)

**Nombre:** No Pain — ES: Sin Dolor

**EN (fuente):**

> Vampires treat a Stunned result on the Injury chart as Knocked Down.

**ES (traducción):**

> Los Vampiros tratan un resultado de Aturdido en la tabla de Heridas como Derribado.

## `necrarchs-the-soul-stealers-lotd1` → `skeletal-warrior--cause-fear` (`shared-rule.cause-fear-2`)

**Nombre:** Cause Fear — ES: Causan Miedo

**EN (fuente):**

> Skeletal Warriors are terrifying Undead creatures and therefore cause Fear.

**ES (traducción):**

> Los Guerreros Esqueléticos son criaturas No-Muertas aterradoras y por tanto causan miedo.

## `necrarchs-the-soul-stealers-lotd1` → `skeletal-warrior--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmunes al Veneno

**EN (fuente):**

> Skeletal Warriors are immune to poisons.

**ES (traducción):**

> Los Guerreros Esqueléticos son inmunes a los venenos.

## `necrarchs-the-soul-stealers-lotd1` → `skeletal-warrior--immune-to-psychology` (`shared-rule.immune-to-psychology`)

**Nombre:** Immune to Psychology — ES: Inmunes a la Psicología

**EN (fuente):**

> Skeletal Warriors are not affected by psychology.

**ES (traducción):**

> Los Guerreros Esqueléticos no se ven afectados por la psicología.

## `necrarchs-the-soul-stealers-lotd1` → `skeletal-warrior--may-not-run` (`shared-rule.may-not-run`)

**Nombre:** May not Run — ES: No Pueden Correr

**EN (fuente):**

> Skeletal Warriors are slow Undead creatures and may not run (but may charge normally).

**ES (traducción):**

> Los Guerreros Esqueléticos son criaturas No-Muertas lentas y no pueden correr (pero pueden cargar con normalidad).

## `necrarchs-the-soul-stealers-lotd1` → `skeletal-warrior--no-pain` (`shared-rule.no-pain`)

**Nombre:** No Pain — ES: Sin Dolor

**EN (fuente):**

> Skeletal Warriors treat Stunned results as Knocked Down.

**ES (traducción):**

> Los Guerreros Esqueléticos tratan los resultados de Aturdido como Derribado.

## `necrarchs-the-soul-stealers-lotd1` → `thrall--cause-fear` (`shared-rule.cause-fear-2`)

**Nombre:** Cause Fear — ES: Causa Miedo

**EN (fuente):**

> Vampires are terrifying Undead creatures and therefore cause Fear.

**ES (traducción):**

> Los Vampiros son criaturas No-Muertas aterradoras y por tanto causan miedo.

## `necrarchs-the-soul-stealers-lotd1` → `thrall--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmune al Veneno

**EN (fuente):**

> Vampires are not affected by any poison.

**ES (traducción):**

> Los Vampiros no se ven afectados por ningún veneno.

## `necrarchs-the-soul-stealers-lotd1` → `thrall--immune-to-psychology` (`shared-rule.immune-to-psychology`)

**Nombre:** Immune to Psychology — ES: Inmune a la Psicología

**EN (fuente):**

> Vampires are not affected by psychology (such as fear) and never leave combat.

**ES (traducción):**

> Los Vampiros no se ven afectados por la psicología (como el miedo) y nunca abandonan el combate.

## `necrarchs-the-soul-stealers-lotd1` → `thrall--no-pain` (`shared-rule.no-pain`)

**Nombre:** No Pain — ES: Sin Dolor

**EN (fuente):**

> Vampires treat a Stunned result on the Injury chart as Knocked Down.

**ES (traducción):**

> Los Vampiros tratan un resultado de Aturdido en la tabla de Heridas como Derribado.

## `necrarchs-the-soul-stealers-lotd1` → `zombie--cause-fear` (`shared-rule.cause-fear-2`)

**Nombre:** Cause Fear — ES: Causan Miedo

**EN (fuente):**

> Zombies are terrifying Undead creatures and therefore cause Fear.

**ES (traducción):**

> Los Zombis son criaturas No-Muertas aterradoras y por tanto causan miedo.

## `necrarchs-the-soul-stealers-lotd1` → `zombie--immune-to-poison` (`shared-rule.immune-to-poison`)

**Nombre:** Immune to Poison — ES: Inmunes al Veneno

**EN (fuente):**

> Zombies are immune to poisons.

**ES (traducción):**

> Los Zombis son inmunes a los venenos.

## `necrarchs-the-soul-stealers-lotd1` → `zombie--immune-to-psychology` (`shared-rule.immune-to-psychology`)

**Nombre:** Immune to Psychology — ES: Inmunes a la Psicología

**EN (fuente):**

> Zombies are not affected by psychology.

**ES (traducción):**

> Los Zombis no se ven afectados por la psicología.

## `necrarchs-the-soul-stealers-lotd1` → `zombie--may-not-run` (`shared-rule.may-not-run`)

**Nombre:** May not Run — ES: No Pueden Correr

**EN (fuente):**

> Zombies are slow Undead creatures and may not run (but may charge normally).

**ES (traducción):**

> Los Zombis son criaturas No-Muertas lentas y no pueden correr (pero pueden cargar con normalidad).

## `necrarchs-the-soul-stealers-lotd1` → `zombie--no-brain` (`shared-rule.brainless`)

**Nombre:** No Brain — ES: Sin Cerebro

**EN (fuente):**

> Zombies do not gain experience.

**ES (traducción):**

> Los Zombis no ganan experiencia.

## `necrarchs-the-soul-stealers-lotd1` → `zombie--no-pain` (`shared-rule.no-pain`)

**Nombre:** No Pain — ES: Sin Dolor

**EN (fuente):**

> Zombies treat Stunned results on the Injury table as Knocked Down.

**ES (traducción):**

> Los Zombis tratan los resultados de Aturdido en la tabla de Heridas como Derribado.

## `nipponese-expedition-web` → `hatamoto--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Hatamoto may use his Leadership when taking a Leadership test.

**ES (traducción):**

> Cualquier guerrero a 6" del Hatamoto puede usar su Liderazgo al hacer una prueba de Liderazgo.

## `ogre-hunting-party-web` → `ogre-hunter--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Ogre Hunter may use his Leadership when taking Ld tests.

**ES (traducción):**

> Cualquier guerrero a 6" del Ogro Cazador puede usar su Liderazgo al hacer pruebas de Liderazgo.

## `order-of-the-mare-web` → `paragon--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Questing knight may use his Leadership value when taking Leadership tests.

**ES (traducción):**

> Cualquier guerrero a 6" del caballero Buscador puede usar su valor de Liderazgo al hacer pruebas de Liderazgo.

## `outlaws-of-stirwood-forest-redux-fbg` → `bandit-leader--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6" of the Bandit Leader may use her Leadership instead of their own.

**ES (traducción):**

> Cualquier modelo de la banda a 6" del Líder Bandido puede usar su Liderazgo en lugar del propio.

## `protectorate-of-sigmar-lotd3` → `hound--animals` (`shared-rule.animal`)

**Nombre:** Animals — ES: Animales

**EN (fuente):**

> Hounds are animals, and thus gain no experience.

**ES (traducción):**

> Los Sabuesos son animales y por tanto no ganan experiencia.

## `protectorate-of-sigmar-lotd3` → `warrior-priest--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6 inches of the Warrior Priest may use his Leadership instead of their own.

**ES (traducción):**

> Cualquier miniatura de la banda a 6 pulgadas del Sacerdote Guerrero puede usar su Liderazgo en lugar del propio.

## `skaven-of-clan-moulder-web` → `packmaster--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Packmaster may use his Leadership when taking Ld tests.

**ES (traducción):**

> Cualquier guerrero a 6" del Maestro de Manada puede usar su Liderazgo al hacer pruebas de Liderazgo.

## `skaven-of-clan-moulder-web` → `rat-ogres--experience` (`shared-rule.experience`)

**Nombre:** Experience — ES: Experiencia

**EN (fuente):**

> Rat Ogres do not gain experience.

**ES (traducción):**

> Los Ogros Rata no ganan experiencia.

## `skaven-of-clan-moulder-web` → `rat-ogres--large-target` (`shared-rule.large-target`)

**Nombre:** Large Target — ES: Objetivo Grande

**EN (fuente):**

> Rat Ogres are Large Targets as defined in the Shooting rules.

**ES (traducción):**

> Los Ogros Rata son Objetivos Grandes tal y como se definen en las reglas de Disparo.

## `skaven-of-clan-moulder-web` → `rat-ogres--stupidity` (`shared-rule.stupidity`)

**Nombre:** Stupidity — ES: Estupidez

**EN (fuente):**

> A Rat Ogre is subject to Stupidity unless a Clan Moulder Hero is within 6" of it.

**ES (traducción):**

> Un Ogro Rata está sujeto a Estupidez salvo que haya un Héroe del Clan Moulder a 6" de él.

## `snotlings-web` → `bullied-goblin--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Chieftain may use his Leadership value when taking Leadership tests.

**ES (traducción):**

> Cualquier guerrero a 6" del Jefe puede usar su valor de Liderazgo al hacer pruebas de Liderazgo.

## `sorcerous-society-lotd4` → `magus--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6 inches of the Magus may use his Leadership instead of their own.

**ES (traducción):**

> Cualquier miniatura de la banda a 6 pulgadas del Mago Supremo puede usar su Liderazgo en lugar del propio.

## `survivors-of-strigos-sylv` → `giant-bats--animals` (`shared-rule.animal`)

**Nombre:** Animals — ES: Animales

**EN (fuente):**

> Giant Bats are animals and thus do not gain experience.

**ES (traducción):**

> Los Murciélagos Gigantes son animales y por tanto no ganan experiencia.

## `survivors-of-strigos-sylv` → `strigoi-vampire--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6" of the Strigoi Vampire may use his Leadership instead of their own.

**ES (traducción):**

> Cualquier modelo de la banda que esté a 6" del Vampiro Strigoi puede usar su Liderazgo en lugar del propio.

## `vampire-hunters-of-sylvania-lotd5` → `vampire-hunter--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any models in the warband within 6 inches of the Vampire Hunter may use his Leadership instead of their own.

**ES (traducción):**

> Cualquier miniatura de la banda a 6 pulgadas del Cazador de Vampiros puede usar su Liderazgo en lugar del propio.

## `vampire-hunters-of-sylvania-lotd5` → `wolfhound--animal` (`shared-rule.animal`)

**Nombre:** Animal — ES: Animal

**EN (fuente):**

> Wolfhounds are animals and thus do not gain experience.

**ES (traducción):**

> Los Sabuesos son animales y por tanto no ganan experiencia.

## `wood-elves-of-athel-loren-web` → `hunt-master--leader` (`shared-rule.leader`)

**Nombre:** Leader — ES: Líder

**EN (fuente):**

> Any warrior within 6" of the Protector of the Hunt may use his Leadership value when taking Leadership tests.

**ES (traducción):**

> Cualquier guerrero a 6" del Protector de la Caza puede usar su valor de Liderazgo al hacer pruebas de Liderazgo.

