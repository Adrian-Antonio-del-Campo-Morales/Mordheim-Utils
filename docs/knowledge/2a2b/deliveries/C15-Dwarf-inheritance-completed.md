# C15 — Herencia de reglas enanas (Karak Azgal)

**Estado: completo, 2026-10-17.** Base de los tres archivos propios conservada antes de
editar en `D:/DEVEL/Mordheim/C15-base/`. No se revisaron las bandas enteras ni el resto de
C15; sólo las dos filas `inherited-combat-rules`.

**Integrado por el coordinador:** dos filas cerradas con snapshot completo,
prepare/preview y control concurrente; 4.556 claves, textos, huellas y notas
conservados, verificación anterior acumulada. Evidencia en
`%TEMP%/c15-dwarf-coordinator-phb37s2z/`. Resultados del ejecutor reutilizados,
sin repetir pruebas. La actualización del artefacto web sigue bloqueada y no
se presenta como completada; el cierre corresponde a construcción y runtime modular.

## Consecuencias implementadas frente a reutilizadas

La cláusula hereda las reglas enanas de Town Crier 6 / Best of Town Crier excepto
Incomparable Miners. Sus tres consecuencias de combate admitidas ya tenían binding contra la
KB activa (`skill.hard-to-kill`, `trait.concussion-immune`, `mechanic.hatred-orcs-goblins`),
pero el operador publicado era `grant: selectable`: la herencia sólo llegaba a quien
"compraba" la regla como habilidad de banda, así que ningún enano la tenía por defecto y un
jugador podía adquirir Hard to Kill como elección. Esa era la capacidad ausente.

- **Implementado:** ambas reglas pasan a `grant: band` y dejan de declarar `kind` (ya no son
  una elección). En `dwarf-guildsmen-kaz` alcanza `band: true` (los seis perfiles son enanos).
  En `dwarf-slayers-kaz` declara sus cinco destinatarios impresos (`giant-slayer`,
  `troll-slayers`, `rememberer`, `slayers`, `clansmen`): el Recordador Enano hereda y el
  Recordador Humano aportado por el llamador (5-6) no, porque no es un Enano.
- **Implementado (destinatario racial):** `source_profiles._supplied_rememberer` retira
  `rememberer` de esta regla junto con la tabla de Habilidades Especiales Enanas cuando la
  especie aportada es humana; el Humano compila las cero etiquetas y conserva su línea propia.
- **Reutilizado sin cambios:** los tres operadores (`skill.hard-to-kill` en
  `_injury_context`, `concussion_immune` en el mismo contexto, `mechanic.hatred-orcs-goblins`
  en `_hit_reroll`) y sus pruebas de otras bandas. No se duplicó ningún bono de
  características ni efecto ya heredado por otro binding: la compilación de cada perfil
  contiene cada etiqueta exactamente una vez y ninguna otra regla de la banda enlaza esos
  operadores.
- **Fuera de esta fila, sin reabrir:** Hacha Enana, listas de equipo y columnas de
  habilidades ya estaban resueltas en sus propias claves. `Incomparable Miners` sigue
  excluida por la cláusula y por `band--miners`; `Armour` (sin penalización de movimiento por
  armadura) y `Grudgebearers` (sin Hojas de Alquiler élficas) son productores de movimiento y
  de composición de banda, quedan fuera de esta cláusula de combate por contenido y no se
  enlazan aquí, mientras `inherited-exclusions` mantiene fuera movimiento, contabilidad de
  campaña e Incomparable Miners. No se descartó ninguna parte de combate al separarlos.

## Disposiciones propuestas (CSV, sin escribir)

Dos cambios preparados con `t13_csv.py prepare` (paquete
`D:/DEVEL/Mordheim/C15-evidence/package.json`), claves `(id, clause_id)`:

1. `rule/mordheim/dwarf-guildsmen-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-guildsmen-kaz.band.town-crier-6-inheritance`
   + `inherited-combat-rules`: `pending` → `{}`; `verification` → hecho ejecutado nuevo;
   nota `[C15 2026-10-17]` con las tres consecuencias, los excluidos por contenido y la
   limitación del artefacto.
2. `rule/mordheim/dwarf-slayers-kaz/band--town-crier-6-inheritance/unimplemented.dwarf-slayers-kaz.band.town-crier-6-inheritance`
   + `inherited-combat-rules`: ídem, con el Recordador Humano y sus cinco destinatarios.

`pending.requires` vacío y `pending.review` sin cambios; no se ejecutó `apply --write` ni se
editó el CSV. El coordinador integra con snapshot completo, conservación y control
concurrente.

## Archivos propios

- `sources/knowledge/bands/mordheim/dwarf-guildsmen-kaz/special-rules.yaml`
- `sources/knowledge/bands/mordheim/dwarf-slayers-kaz/special-rules.yaml`
- `packages/python/roster-construction/mordheim_construction/source_profiles.py`
- `tests/python/construction/test_c15_dwarf_inheritance.py` (nuevo)

No se tocaron archivos de C02c, C07a ni el resto de C15.

## Evidencia mínima

- `pytest tests/python/construction/test_c15_dwarf_inheritance.py` → **7 passed**,
  EXIT=0 (`D:/DEVEL/Mordheim/C15-evidence/first-run.txt`). Cubre: herencia automática en
  todos los perfiles de ambas bandas con una sola contribución por etiqueta; ausencia de la
  regla en la oferta de habilidades y rechazo (`not selectable`) si se intenta elegir; el
  Recordador Humano sin ninguna de las tres y el Enano con ellas; y el consumo modular real
  (maza con conmoción contra un no inmune, herida 2 derribado sólo para el enano, herida 5
  aturdido, re-tirada de impactos sólo en la primera ronda contra orcos/goblins).
- `pytest tests/python/construction/test_c05a_dwarf_slayer_skills.py tests/python/construction/test_profile_bindings.py`
  → **45 passed**, EXIT=0 (`D:/DEVEL/Mordheim/C15-evidence/neighbours.txt`): las columnas de
  habilidades y el Recordador Humano siguen igual tras ampliar la retirada de reglas enanas.
- `validate_band_package` sobre los dos paquetes → `[]` errores (esquemas editoriales).
- `test_t13_canonical_choices.py::test_runtime_distinguishes_planned_and_active_bindings` →
  **1 passed**, EXIT=0 (`D:/DEVEL/Mordheim/C15-evidence/runtime-validator.txt`): valida el runtime
  de todas las reglas de ambas colecciones, incluidas las dos reglas editadas.

## Bloqueos exactos

- **Artefacto web sin regenerar:** `python tools/knowledge/generate_knowledge_web.py` falla
  con `conflicting Spanish rule label for 'No Missile Weapons'` en
  `sources/knowledge/bands/mordheim/knights-of-the-bitter-moors-mim/special-rules.yaml`
  (`Sin armas de proyectil` frente a `Sin Armas de Proyectil` del resto de bandas). Es un
  archivo modificado por otro frente y ajeno a C15: no se editó ni se generó a mano. Por eso
  `apps/warband-manager-web/dist/knowledge/{knowledge-web,rules-prose}.json` todavía muestran
  la regla como `selectable`; el coordinador debe regenerar en cuanto ese conflicto se
  resuelva. `display-text.json` no cambia (las etiquetas no se tocaron).
- La rama de `Armour`/`Grudgebearers`/`Incomparable Miners` no se convierte en efectos de esta
  fila: son productores de movimiento, composición y exploración, quedan fuera por contenido y
  `inherited-exclusions` sigue pendiente como clave separada de este encargo.
- El corpus E2E (propiedad externa, excluido de este encargo) aún declara
  `special_rule_ids: [band--town-crier-6-inheritance]`; no se ejecutó ni se editó, y su
  actualización corresponde a su propietario, no a esta entrega.
