# C07a — variantes de armas y discrepancias de catálogo

## Estado

**C07a cerrado e integrado por el coordinador, 2026-10-17: 11/11.** Seis filas
finales aplicadas con snapshot íntegro, prepare/preview y control concurrente;
4.556 claves, textos, huellas y notas conservados. Verificación previa acumulada.
Evidencia de integración: `%TEMP%/c07a-coordinator-n2pa3l07/`. Resultados del
ejecutor reutilizados sin repetir pruebas. Cierre por reconciliación, sin nueva
implementación de producción.

Seis cláusulas asignadas, **ninguna requería código nuevo**: la ruta canónica ya
funcionaba en las tres armas y sólo faltaba un discriminador que separase el
contrato correcto del retirado. Se añadieron tres pruebas en un único archivo
directamente afectado; no se modificó motor, datos ni bindings. Las otras cinco
cláusulas del paquete (Belaying Pin, Sunstaff, `item/sun_gauntlet`) ya estaban
cerradas y no se tocaron.

Base propia conservada antes de editar: copia y hash de
`tests/python/combat/modular/test_t13_weapon_variant_combat.py` en
`C:\Users\Pholtergate\AppData\Local\Temp\c07a-base-test_t13_weapon_variant_combat.py`
(sha256 `45039efb…52f2`). Sin E2E, sin su suite global, sin commits.

## Capacidades (antes → después)

**Reconciliadas (ya funcionaban, evidencia ejecutada):**

- **Cathayan Longsword** — decisión de `design-rulings.md` (2026-10-14):
  `+1 Iniciativa`, `+1 Habilidad de Arma`, Parada y **sin** penetración de
  armadura. La ejecución ya no lleva `armour_penetration`; el defensor con
  armadura pesada salva en su propia cara impresa 5+.
- **Starsword** — `Fuerza +1`, Parada e `ignore_armour`; el ataque niega la
  armadura y `resolve_special_save` sigue resolviendo la salvación especial.
  La decisión identifica la salvación Dodge impresa con la ward: se conserva esa
  salvación y **no** se añadió otro sistema Dodge.
- **Sun Gauntlet** — variante cuerpo a cuerpo recuperada por R13: uso secundario
  (mano principal rechazada), Fuerza fija 4 e ignorar armadura, resuelta como el
  ataque adicional de la mano secundaria. Disparo sigue excluido. Evidencia y
  fuentes de R13 reutilizadas; no se repitió la búsqueda.

**Implementado:** nada nuevo. Los tres discriminadores añadidos son la única
modificación ejecutable.

## Ruta canónica comprobada

Sonda ejecutada fuera del repositorio contra el catálogo real y `compile_fighter`
(no es E2E):

| objeto | perfil que lo recibe | oferta | coste | compilación |
|---|---|---|---|---|
| `cathayan_longsword` | battle-monks-of-cathay / emissary | mano principal | 75 gc | Parada, +1 I, +1 HA, penetración 0 |
| `starsword` | amazons-lustria / serpent-priestess | mano principal | 30 gc | +1 F, Parada, `ignore_armour` |
| `sun_gauntlet` | amazons-mordheim / priestess (y lustria-amazons priestess, champions, totem-warriors) | **sólo** mano secundaria | 40 gc | Fuerza fija 4, `ignore_armour`, ataque adicional |

`validate_configuration` no devuelve avisos en los tres casos. No se concedió
ningún permiso de equipo nuevo a perfiles que no lo tuvieran.

## Disposiciones CSV propuestas

Paquete preparado (sin `--write`):
`C:\Users\Pholtergate\AppData\Local\Temp\c07a-t13-prepared.json` — 6 cambios,
claves exactas, instantánea íntegra y hash del CSV coincidente con el estado
actual. `apply` en modo vista validó conservación; **no se escribió el CSV**.

| id | clause_id | pending | relation | evidencia ejecutada |
|---|---|---|---|---|
| `item/cathayan_longsword` | `armour-penetration-discrepancy` | `{}` | `equivalent` | `test_the_cathayan_longsword_grants_no_extra_armour_penalty` |
| `mechanic/weapon.cathayan-longsword` | `armour-penetration-discrepancy` | `{}` | `equivalent` | el mismo caso |
| `item/starsword` | `whole` | `{}` | `equivalent` | `test_the_starsword_denies_armour_while_its_ward_exception_saves` |
| `mechanic/weapon.starsword` | `whole` | `{}` | `equivalent` | el mismo caso |
| `mechanic/weapon.starsword` | `dodge-exception` | `{}` | `equivalent` | el mismo caso; `effect_id` pasa de `proposed.defence.dodge-save` a `weapon.starsword` |
| `mechanic/weapon.sun-gauntlet` | `whole` | `{}` | `equivalent` | `test_the_sun_gauntlet_second_hand_resolves_its_own_strength_four_attack` + caso R13 de `test_t13_weapon_variant_profiles.py` |

Las propuestas actualizan `semantic_contract`, `parameters` y `conditions`
obsoletos (penetración 1, `conflict`, `missing_mechanic: dodge save`) a la
decisión vigente, conservan la evidencia anterior y sólo **añaden** notas. La
integración con copia previa completa y control concurrente corresponde al
coordinador.

## Archivos propios

- `tests/python/combat/modular/test_t13_weapon_variant_combat.py` — tres pruebas
  nuevas (antes 8 casos; después 11).
- `docs/knowledge/2a2b/deliveries/C07a-completed.md` — este documento.

Sin cambios en fuentes, bindings, consumidores ni CSV.

## Comprobación mínima

- `pytest tests/python/combat/modular/test_t13_weapon_variant_combat.py` →
  **11 passed**, exit 0 (salida en
  `C:\Users\Pholtergate\AppData\Local\Temp\c07a-combat-run1.txt`).
- Caso R13 reutilizado:
  `test_the_sun_gauntlet_melee_half_is_the_off_hand_strength_four_attack` →
  **1 passed**, exit 0 (salida en
  `C:\Users\Pholtergate\AppData\Local\Temp\c07a-sun-run1.txt`).
- `t13_csv.py prepare` y `apply` (vista) → exit 0, 6 claves, instantánea
  coincidente (salida en `…\Temp\c07a-apply-preview.txt`).

No se repitieron baterías ni se ejecutaron suites globales o E2E.

## Límites y bloqueos

- **CSV:** integración del coordinador completada; seis filas cerradas.
- **Prosa editorial no ejecutable:** los registros de catálogo
  (`catalog/items/weapons-close-combat.yaml` y `catalog/mechanics/close-combat.yaml`)
  todavía describen el Cathayan Longsword con *Cutting Edge* («-1 adicional a la
  armadura»), texto anterior a la decisión y que ningún consumidor lee; el
  registro de item además repite la frase «this sword).». No se editaron porque
  ambos YAML tienen escritores concurrentes de C07b. Si el coordinador quiere
  alinear la ficha con la decisión, son dos cadenas (EN/ES) más la línea
  duplicada, sin efecto en el duelo.
