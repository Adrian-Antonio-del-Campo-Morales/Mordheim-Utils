# Revisión de equivalencia de reglas 2B ↔ KB activa

Objetivo: garantizar que **ninguna regla introducida en la ingesta 2B duplique una regla
ya existente en la KB activa**. Toda regla 2B cuya semántica esté verificada como idéntica
a una regla compartida de la KB lleva un `rule_ref`; las demás permanecen como reglas
propias de banda (posiblemente `NO`/`LATER` si el motor no las cubre).

## Metodología (sin vínculos por nombre)

1. Inventario: 900 reglas en los `special-rules.yaml` de las 60 bandas 2B; 14 ya llevaban
   `rule_ref` de las transcripciones originales.
2. Candidatos por nombre: 226 reglas 2B cuyo nombre coincide (normalizado, sin signos ni
   mayúsculas) con alguna regla de `sources/knowledge/catalog/rules/`.
3. Comparación de texto: se normalizó el `effect` de ambos lados (minúsculas, sin puntuación)
   y se calculó similitud (`difflib.SequenceMatcher`) contra **todas** las reglas de la KB con
   ese nombre (no solo la primera). El informe completo quedó en
   `build/cache/2b-pdfs/rule-equiv-report.txt`.
4. Decisión manual caso por caso (ver tabla): vínculo solo cuando la semántica es la misma,
   aunque la redacción difiera. Si la KB tiene varias variantes (p. ej. `stupidity` genérica
   vs `stupidity-2` de trol), se eligió la variante cuyo texto coincida con el caso concreto.
5. Aplicación: se insertó `rule_ref: <id>` al final de cada regla 2B vinculada, conservando
   el `effect`, `effect_i18n`, `source` y `runtime` de la banda (el `rule_ref` es una
   declaración de equivalencia, no un reemplazo).

## Vínculos `rule_ref` confirmados por comparación de texto (52)

| Band | Regla 2B | `rule_ref` | Base del vínculo |
|---|---|---|---|
| bretonnian-buccaneers-sar | swabbies--never-gain-experience | `shared-rule.never-gain-experience` | texto idéntico |
| clockworkers-sc | dwarf-engineer--armour | `shared-rule.armour-2` | texto idéntico |
| clockworkers-sc | dwarf-engineer--hard-to-kill | `shared-rule.hard-to-kill` | misma regla, redacción más completa |
| clockworkers-sc | dwarf-engineer--hard-head | `shared-rule.hard-head-2` | misma regla ("maces, clubs and similar weapons") |
| crooked-moon-kep | cave-squigs--minderz | `shared-rule.minderz` | misma regla (redacción KEP "Night Goblin" vs KB "Goblin Warrior") |
| crooked-moon-kep | troll--vomit-attack | `shared-rule.vomit-attack` | verificado a 300 dpi: el PDF KEP imprime S5 (el "S8" era error de OCR/transcripción, corregido — ver `discrepancy-verdicts.md` caso 1) |
| crooked-moon-kep | troll--regeneration | `shared-rule.regeneration` | misma regla (KEP omite la excepción de Flaming) |
| crooked-moon-kep | snotling-mob--weedy | `shared-rule.weedy` | KEP resume "add +1 injury"; KB imprime la tabla completa — misma regla |
| fallen-the-rel | revenant--no-pain | `shared-rule.no-pain` | texto casi idéntico |
| fen-guard-mim | treekin--may-not-run | `shared-rule.may-not-run` | texto casi idéntico |
| guild-of-disgraced-engineers-mim | band--armour | `shared-rule.armour-2` | texto idéntico |
| metal-mongers-mim | machine-ogre--no-brain | `shared-rule.brainless` | misma mecánica (nunca gana experiencia); nombre fuente distinto |
| night-goblins-kaz | cave-squigs--movement | `shared-rule.movement` | texto idéntico |
| night-goblins-kaz | cave-squigs--minderz | `shared-rule.minderz` | texto idéntico (97%) |
| night-goblins-kaz | troll--stupidity | `shared-rule.stupidity-2` | texto idéntico |
| night-goblins-kaz | troll--regeneration | `shared-rule.regeneration` | misma regla (omisión menor) |
| night-goblins-kaz | troll--vomit-attack | `shared-rule.vomit-attack` | texto idéntico (S5) |
| night-goblins-kaz | troll--always-hungry | `shared-rule.always-hungry` | misma regla; **ojo: KAZ 15 gc vs KB 20 gc de manutención** |
| night-goblins-kaz | snotling-mob--weedy | `shared-rule.weedy` | texto idéntico |
| sartosan-pirates-sar | swabbies--never-gain-experience | `shared-rule.never-gain-experience` | texto idéntico |
| skaven-of-clan-mors-kaz | rat-ogre--stupidity | `shared-rule.stupidity` | texto casi idéntico (variante Skaven Hero 6") |
| skaven-of-clan-mors-kaz | rat-ogre--experience | `shared-rule.experience` | misma regla ("Rat Ogre never gains Experience") |
| skaven-of-clan-pestilens-lus | plague-priest--leader | `shared-rule.leader` | misma regla |
| skaven-of-clan-pestilens-mou | plague-priest--leader | `shared-rule.leader` | misma regla |
| skaven-of-clan-pristekk-sc | chieftain--leader | `shared-rule.leader` | misma regla |
| skaven-of-clan-pristekk-sc | rat-ogres--stupidity | `shared-rule.stupidity` | texto casi idéntico |
| skaven-of-clan-pristekk-sc | rat-ogres--experience | `shared-rule.experience` | misma regla |
| skaven-of-clan-pristekk-sc | rat-ogres--large-target | `shared-rule.large-target` | texto casi idéntico |
| skaven-of-clan-skryre-kaz | master-engineer--leader | `shared-rule.leader` | misma regla |
| skaven-of-clan-skryre-kaz | warlock-engineer--wizard | `shared-rule.wizard` | patrón de la KB (wizared + hechizos de lista propia, no modelados) |
| skaven-of-clan-skryre-kaz | skavenslaves--experience | `shared-rule.experience` | misma mecánica (no experiencia) — vínculo por patrón |
| skaven-of-clan-skryre-rel | warlock-engineer--leader | `shared-rule.leader` | misma regla |
| strigoi-kaz | skeletons--no-pain | `shared-rule.no-pain` | misma regla |
| strigoi-kaz | skeletons--no-brain | `shared-rule.brainless` | misma mecánica (zombies/esqueletos sin experiencia) |
| strigoi-kaz | bats--living | `shared-rule.living` | misma mecánica (ser vivo, sin reglas de no-muerto) |
| strigoi-kaz | fell-bats--cause-fear | `shared-rule.cause-fear-2` | KB: "todos los no-muertos causan miedo" — los Fell Bats son no-muertos |
| strigoi-kaz | fell-bats--may-not-run | `shared-rule.may-not-run` | misma regla |
| strigoi-kaz | fell-bats--immune-to-psychology | `shared-rule.immune-to-psychology-4` | variante no-muerto de la KB |
| strigoi-kaz | fell-bats--immune-to-poison | `shared-rule.immune-to-poison-3` | variante no-muerto de la KB |
| strigoi-kaz | fell-bats--no-pain | `shared-rule.no-pain` | misma regla |
| turjuk-rel | emir--leader | `shared-rule.leader` | misma regla |
| underworld-alliance-mim | goblin-bully--leader | `shared-rule.leader` | misma regla |
| underworld-alliance-mim | skaven-slum-lord--leader | `shared-rule.leader` | misma regla |
| underworld-alliance-mim | warpstone-troll--fear | `shared-rule.fear` | misma regla |
| underworld-alliance-mim | warpstone-troll--stupidity | `shared-rule.stupidity-2` | misma regla |
| underworld-alliance-mim | warpstone-troll--vomit-attack | `shared-rule.vomit-attack` | misma regla (S5) |
| underworld-alliance-mim | warpstone-troll--large-target | `shared-rule.large-target` | misma regla |
| wasteland-privateers-sar | captain--leader | `shared-rule.leader` | misma regla |
| wasteland-privateers-sar | swabbies--never-gain-experience | `shared-rule.never-gain-experience` | misma regla |
| watchmen-mim | watch-captain--leader | `shared-rule.leader` | misma regla |
| watchmen-mim | turnkeys--immune-to-poison | `shared-rule.immune-to-poison` | verificado contra el PDF: inmunidad por constitución, no la variante no-muerto (ver `discrepancy-verdicts.md` caso 4) |

Total con esta pasada: **66 reglas vinculadas** (14 originales + 52 nuevas).

## Candidatos descartados (no vinculados) — casos notables

- **Leader ×52 originales**: muchas variantes restringen a qué modelos se aplica ("any
  warrior", "any pirate", "models in the warband") — semánticamente equivalentes a la KB
  pero con alcance distinto; se vinculó solo cuando el texto es el patrón general. El resto
  quedan como reglas de banda.
- **Wizard ×20**: la KB solo modela el patrón Necromancer; los magos 2B usan listas
  distintas (Horned Rat, High Magic, Hedgewise…). Solo se vincularon los que siguen
  exactamente el patrón de la KB.
- **Fear/Cause Fear**: la KB distingue `fear` (guerrero causa miedo) y `cause-fear-2`
  (no-muertos causan miedo). Las reglas 2B con justificación de raza (Butchers, Ghouls,
  sgulls) quedaron sin vínculo: el texto es narrativo y el runtime 2B ya lo clasifica.
- **Animosity**: la KB modela la animosidad de orcos con tabla; las versiones 2B (Forest
  Goblins, Savage Orcs con remisión a WD243/TC6) son variantes distintas → sin vínculo.
- **Always Hungry**: la variante KAZ cambia coste y opción de manutención (15 gc, sacrificio
  de snotlings/squigs) → vinculada a la regla genérica pero con discrepancia anotada.
- **Regeneration de Boglars (5+ vs 4+), Movement de Sewer Squigs (2D6−1):** mecánicas
  parecidas pero valores distintos → sin vínculo, son reglas propias.
- **Immune to Poison/Psychology no-muerto**: las variantes de la KB están acotadas a
  "warriors with the Undead special rule"; se vinculó solo donde la banda 2B declara al
  perfil como no-muerto (fell-bats). Turnkeys (vivo, por Constitución) se re-vinculó a la
  variante genérica tras verificar el PDF (ver `discrepancy-verdicts.md`, caso 4).

## Salvaguardas añadidas

- `ingest_2b.py validate` ahora comprueba que todo `rule_ref` exista en la KB activa
  (idéntico a la comprobación de `item_id`).
- `test_2b_staging.py` replica la misma aserción.
