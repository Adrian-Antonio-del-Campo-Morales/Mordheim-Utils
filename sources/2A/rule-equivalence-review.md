# Revisión de equivalencia de reglas 2A ↔ KB activa

Fecha: 2026-09-15. Objetivo: garantizar que **ninguna regla introducida en la ingesta 2A
duplique una regla ya existente en la KB activa**. Toda regla 2A cuya semántica esté
verificada como idéntica a una regla compartida de la KB lleva un `rule_ref`; las demás
permanecen como reglas propias de banda (posiblemente `NO`/`LATER` si el motor no las
cubre). Formato y criterios heredados de `sources/2B/rule-equivalence-review.md`.

## Metodología (sin vínculos por nombre)

1. Inventario: **357 reglas** en los `special-rules.yaml` de las 19 bandas 2A; 28 ya
   llevaban `rule_ref` de las transcripciones (todas re-verificadas: los 25 ids existen en
   la KB; ver punto 3).
2. Candidatos por nombre: normalización de nombres (minúsculas, sin signos) contra las 73
   reglas de `sources/knowledge/catalog/rules/` + detección difusa (contención de nombre).
3. Comparación de texto: `effect` de ambos lados normalizado y comparado; dump lado a
   lado de todos los candidatos fuertes (`build/cache/2a-sources/dump_texts.py`).
4. Decisión manual caso por caso (tablas siguientes), con el mismo criterio que 2B:
   vínculo solo si la semántica operativa es idéntica aunque la redacción difiera; las
   variantes Undead específicas de la KB (`-2`/`-3`/`-4`) se reservan para reglas que
   confieren el efecto *vía* la regla Undead.

## Vínculos `rule_ref` existentes re-verificados (28, de la fase de transcripción)

Necrarchs (25): leader, cause-fear×4, immune-to-psychology×4, immune-to-poison×4,
no-pain×4, may-not-run×2, brainless (zombie), large-target — todos contra variantes
genéricas de la KB, correcto porque cada perfil declara el efecto en su propio texto
(vampiros/no-muertos con texto propio en el paquete, no por delegación). Protectorate
warrior-priest, Sorcerous Society magus y Vampire Hunters leader: patrón general. **Sin
correcciones.**

## Vínculos nuevos confirmados por comparación de texto (25)

| Band | Regla 2A | `rule_ref` | Base del vínculo |
|---|---|---|---|
| dwarf-slayer-cult-web | band--hard-to-kill | `shared-rule.hard-to-kill` | misma regla (1-2 derribado, 3-5 aturdido, 6 OoA); la KB comprime la redacción |
| dwarf-slayer-cult-web | band--hard-head | `shared-rule.hard-head-2` | misma regla ("maces, clubs, etc." vs "maces, clubs and similar weapons") |
| dwarf-slayer-cult-web | band--grudgebearers | `shared-rule.grudgebearers` | segunda frase verbatim idéntica; la primera es lore |
| dwarf-slayer-cult-web | giant-slayer--leader | `shared-rule.leader` | patrón general |
| skaven-of-clan-moulder-web | rat-ogres--stupidity | `shared-rule.stupidity` | la variante KB ya es "unless a Skaven Hero is within 6\"" (aquí: Clan Moulder Hero) |
| skaven-of-clan-moulder-web | rat-ogres--experience | `shared-rule.experience` | misma regla ("The Rat Ogre never gains Experience") |
| skaven-of-clan-moulder-web | rat-ogres--large-target | `shared-rule.large-target` | misma regla |
| vampire-hunters-of-sylvania-lotd5 | wolfhound--animal | `shared-rule.animal` | animal + sin experiencia, ambas cláusulas |
| druchii-mic | slavehounds--animals | `shared-rule.animal` | animal + sin experiencia |
| halflings-mic | piggies--animals | `shared-rule.animal` | animal + sin experiencia |
| ogre-hunting-party-web | sabretusks--animals | `shared-rule.animal` | animal + sin experiencia |
| protectorate-of-sigmar-lotd3 | hound--animals | `shared-rule.animal` | animal + sin experiencia |
| survivors-of-strigos-sylv | giant-bats--animals | `shared-rule.animal` | animal + sin experiencia |
| mazzalupo-web | black-sheep--animals | `shared-rule.animal` | animal + sin experiencia |
| mazzalupo-web | black-sheep--stupidity | `shared-rule.stupidity` | regla genérica (estupidez salvo custodio a 6") |
| dreamwalkers-cult-of-morr-fbg | dreamer--leader | `shared-rule.leader` | patrón general ("Any warrior within 6\"") |
| druchii-mic | noble--leader | `shared-rule.leader` | patrón general |
| halflings-mic | halfling-elder--leader | `shared-rule.leader` | patrón general |
| masters-of-horror-sylv | mad-scientist--leader | `shared-rule.leader` | patrón general |
| mazzalupo-web | wandering-knight--leader | `shared-rule.leader` | patrón general |
| nipponese-expedition-web | hatamoto--leader | `shared-rule.leader` | patrón general |
| ogre-hunting-party-web | ogre-hunter--leader | `shared-rule.leader` | patrón general |
| order-of-the-mare-web | paragon--leader | `shared-rule.leader` | patrón general |
| outlaws-of-stirwood-forest-redux-fbg | bandit-leader--leader | `shared-rule.leader` | patrón general |
| skaven-of-clan-moulder-web | packmaster--leader | `shared-rule.leader` | patrón general |
| snotlings-web | bullied-goblin--leader | `shared-rule.leader` | patrón general |
| survivors-of-strigos-sylv | strigoi-vampire--leader | `shared-rule.leader` | patrón general |
| wood-elves-of-athel-loren-web | hunt-master--leader | `shared-rule.leader` | patrón general |

**Total con esta pasada: 53 reglas vinculadas** (28 re-verificadas + 25 nuevas).

## Candidatos descartados (no vinculados) — casos notables

- **Fear/Cause Fear (necrarchs thrall/zombies, survivors ghouls,
  village-ogre, sabretusks, rat-ogres ya en re-verificación…):** la KB distingue `fear`
  ("This warrior causes Fear") de `cause-fear-2` (no-muertos). Los textos 2A justifican
  la regla narrativamente ("are terrifying Undead creatures **and therefore** cause
  Fear") y el efecto llega por la propia regla Undead declarada en cada paquete, igual
  que el criterio 2B para Ghouls/sgulls. Sin vínculo nuevo; el runtime ya lo clasifica.
- **No Pain / Immune to Psychology / Immune to Poison / May not Run de no-muertos 2A**
  (thrall/zombies/flesh-construct/strigoi): los paquetes ya llevan `rule_ref` a las
  variantes **genéricas** porque el texto de cada perfil declara el efecto por sí mismo
  ("Vampires treat a Stunned result…"), no por delegación Undead. Re-verificado; sin
  cambios. (2B vinculó a variantes Undead solo donde la fuente no imprimía texto propio.)
- **Wizard ×6** (necrarch, sorceress druchii, magus/mage, seer, forest-mage, shaman
  snotling): la KB solo modela el patrón Necromancer con lista no modelada; las listas 2A
  son propias (Necromancy para necrarchs — mismo patrón pero la KB ya tiene el vínculo
  implícito vía `lore.necromancy` activa; elemental/Charms & Hexes/Woodland/Snotling
  Waaagh! viven en `sources/2A/catalog/magic-2a.yaml`). Sin vínculo, mismo criterio 2B.
- **`shared--mob-rule` (snotlings):** mecánica propia (+1 Ld por cada 2 Snotlings),
  sin equivalente en la KB → regla de banda.
- **`village-ogre--skills` / `shared-rule.skills`:** la KB es específica del Ogre Pit
  Fighter (Combat/Strength/Pit Fighter); el ogre de halflings usa Combat/Strength →
  alcance distinto, sin vínculo.
- **`village-ogre--large` / `giant-bats--large` vs `shared-rule.large-target`:** los
  textos 2A son variantes narrativas ("any target may shoot at him even if not closest"),
  semánticamente la misma mecánica pero redactadas como reglas de banda con texto propio;
  el patrón KB es la frase canónica. Decisión: sin vínculo (texto propio completo), igual
  que el criterio 2B para los Large Target con justificación narrativa.
- **`sabretusks--charge` vs `shared-rule.charge`:** la KB es específica del Dire Wolf; el
  efecto es el mismo (2A en el turno de carga) pero la regla KB nombra otra criatura →
  sin vínculo.
- **`band--death-of-the-leader` / `band--death-of-a-leader`** (necrarchs, protectorate):
  reglas de banda sobre sucesión, no la regla Leader → sin vínculo.
- **Undead-foes/Hate Undead (dreamwalkers, grave-robbers):** la KB solo tiene
  `shared-rule.undead` (ser no-muerto); las reglas 2A son *odio/miedo hacia* no-muertos →
  sin equivalente.
- **Never-gain-experience:** la regla KB `never-gain-experience` es específica de los
  Swabbies (2B); para animales 2A se usó `shared-rule.animal`, que imprime ambas cláusulas.

## Salvaguardas añadidas

- `ingest_2a.py validate` ya comprueba que todo `rule_ref` exista en la KB activa (al
  igual que la comprobación de `item_id`); `test_2a_staging.py` replica la aserción.
- Todos los archivos tocados pasan `format_yaml.py --check` (92 YAML de 2A, 0 would
  change, 0 failures).

## Verificación final

- `ingest_2a.py validate`: 19 filas, 0 problemas
- `pytest tests/knowledge/test_2a_staging.py`: 7/7
- Estado del manifiesto intacto: 19× `english-reviewed`
