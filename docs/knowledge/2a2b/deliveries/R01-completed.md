# R01 — Tres cláusulas de bandas pendientes

**R01 cerrado e integrado por el coordinador, 2026-10-17: 3/3.** Tres filas
aplicadas con snapshot íntegro, prepare/preview y control concurrente;
4.556 claves, textos, huellas y notas conservados. Consumidores y evidencia
anteriores acumulados. Integración: `%TEMP%/r01-coordinator-coz203z_/`.
Resultados focales del ejecutor reutilizados sin repetir pruebas. Reconciliación
de comportamiento existente, sin código nuevo de producción. La expectativa de
veneno señalada abajo sigue pendiente de la integración final, fuera de estos cierres.

**Estado: implementado/reconciliado y verificado, 2026-10-17.** No se editó dato de
fuente ni código de motor: las tres capacidades ya estaban conectadas por C04b,
C14b y C01b, así que este pase aporta la reconciliación, un discriminador de fase
ausente y la evidencia de consumo real. Base intacta: CSV `c8d2ceeb…`, prueba
`127c8916…` (`%TEMP%/r01/base-sha.txt`). Sin E2E, suites globales ni commits.

## Implementación nueva frente a reutilización

| Fila | Antes | Después | Origen |
|---|---|---|---|
| Maldred `whole` | la oferta ya cambiaba con la fase, pero la fila seguía `pending {"work":"data"}` y no había prueba de selección directa | cerrada sobre `compiler.mercenary-equipment-at-creation`: 28 ofertas antes de la primera partida y 23 después, sin unión permanente; `compile_fighter` acepta `weapon.morning-star` en creación y lo rechaza con `equipment.post-creation`, mientras `weapon.spear` compila en ambas fases | **reutiliza C04b** + 1 discriminador añadido |
| Gibbets `intrinsic-save` | `pending {"work":"connection"}`, `effect_id` vacío y consumidor apuntando a una proyección que no publica salvaciones | cerrada sobre la regla de perfil existente `gibbets--iron-cage` → `mechanic.iron-cage` (`armour_save_bonus: 2`, compone 5+); el compilador la consume, sobrevive `equipment_for_state` y no es pieza comprada, ward ni regeneración; la prohibición de armadura conserva su fila separada | **reutiliza C14b** |
| Undead Zombies `no-unarmed-penalty` | `pending {"requires":["weapon.natural-attacks"]}` | cerrada: la ruta existente de perfil sin `equipment_lists` compila `weapon.natural-attacks`; conserva S3/A1 impresos y `target_armour_bonus == 0`, también con `weapon.fist` explícita; no concede equipo ni inmunidades | **reutiliza C01b** |

## Disposiciones

1. **Maldred.** El perfil declara Squire y Men-at-Arms; la regla
   `mercenaries--equipment-restrictions` aporta la lista Mercenary sólo antes de la
   primera partida. Oferta (`desktop_call("equipment")`) y aceptación
   (`compile_fighter`) leen la misma fase suministrada. No se simula progresión de
   campaña ni se declara dato nuevo.
2. **Gibbets.** La jaula es una defensa intrínseca del perfil, no una pieza del kit:
   el binding canónico de la regla ya la ejecuta y el 5+ se conserva al despojar
   equipo. No se duplica con armadura comprada (esa selección se rechaza por
   `armour-suit`).
3. **Zombies.** El ataque propio es la ruta de ataques naturales ya existente; la
   ausencia de penalización de puño se mide en el ataque compilado (sin `-1 F` ni
   `+1` a la salvación del objetivo). No se añadió lista, arma ni inmunidad global.

## Paquete CSV (sólo `query` y `prepare`; sin `--write`)

`%TEMP%/r01/proposal.json`: **3 cambios** por `(id, clause_id)`, todos con
`pending {}` y notas previas conservadas por `append_notes`; snapshot
`c8d2ceeb66f653e0b692c79606eed52e131e2de1063d3552c29521c9977cbffa`, idéntico al
CSV actual antes y después de preparar. `apply` en seco validó la conservación de
las 4.556 filas con `EXIT=0` (`%TEMP%/r01/apply-preview.txt`). La fila de Zombies
sigue pendiente en el CSV: no se ejecutó `--write`; integra el coordinador.

## Archivos propios

- `tests/python/construction/test_t13_construction_recipients.py` — sólo el
  discriminador de selección directa dentro del caso C04b de Maldred.
- `docs/knowledge/2a2b/deliveries/R01-completed.md` — este documento.

## Evidencia mínima

| Comando (caso seleccionado) | Resultado |
|---|---|
| `python -m pytest tests/python/construction/test_t13_construction_recipients.py -q -k "maldred"` | **1 passed**, 52 deselected, EXIT=0 (`%TEMP%/r01/maldred.txt`) |
| `python -m pytest tests/python/construction/test_c14b_physical_kits.py -q -k "gibbet"` | **1 passed**, 13 deselected, EXIT=0 (`%TEMP%/r01/gibbets.txt`) |
| `python -m pytest tests/python/construction/test_c01b_intrinsic_profile_declarations.py -q -k "test_every_profile_fights_with_its_printed_intrinsic_attack and zombies"` | **2 passed**, 70 deselected, EXIT=0 (`%TEMP%/r01/zombies-attack.txt`) |

Medición directa adicional (sin escribir archivos): Zombies con `weapon.fist`
compila como `weapon.natural-attacks`, S3, A1, `target_armour_bonus=0`; con
`weapon.sword` falla por la prohibición impresa. Gibbets compila `armour_save=5`.

## Bloqueos exactos

- El shim `pytest` del PATH sale con código 1 sin salida en este entorno; las
  pruebas se ejecutaron con `python -m pytest` (pytest 7.1.2).
- En `test_c01b_intrinsic_profile_declarations.py`, el caso de **rechazo**
  `weapons-armour` falla para los dos Zombies porque
  `compiled(..., main_poison_id="poison.black-lotus")` lanza en vez de compilar.
  Es una expectativa de legalidad de veneno ajena a `no-unarmed-penalty` y ya
  presente en el árbol antes de este pase; no se editó ni se debilitó. El caso de
  ataque natural de la misma fila pasa.
