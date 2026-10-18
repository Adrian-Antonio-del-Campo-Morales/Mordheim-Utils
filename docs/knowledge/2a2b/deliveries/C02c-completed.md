# C02c — Restricciones de equipo: perfiles y estricturas

**C02c cerrado e integrado por el coordinador, 2026-10-17.** Las 41 disposiciones
pendientes se aplicaron con snapshot íntegro, prepare/preview y control
concurrente; 4.556 claves, textos, huellas y notas conservados. Evidencia previa
conservada y enlace a esta entrega añadido a verification. Integración en
`%TEMP%/c02c-coordinator-o3evhyjg/`. Resultados del ejecutor reutilizados sin
repetir baterías. Vim-To y las otras filas ya cerradas no se reescribieron.

**Paquete preparado:** `build/c02c-package.json` (41 disposiciones, sha256
`8c00533d2ed8…`; `prepare` validó conservación). No se ejecutó `apply --write`.
Vim-To se omite porque C02a ya lo cerró; su evidencia no se toca.

## Implementación y reconciliación

- **Young'uns**: no había lista vacía que corregir. La `henchmen-list` ya
  publica el equipo legal impreso y sus `applies_to` limitan `great_weapon` a
  Boyz/Nuttaz y `crossbow` a Shootaz. La proyección ofrece 8 objetos legales
  (daga, hacha, espada, choppa, lanza, escudo, casco, armadura ligera), rechaza
  el arma a dos manos en `compile_fighter` y no ofrece ballesta; sin disparo.
  Nuevo discriminador: `test_black_orc_younguns_keep_legal_gear_and_recipient_exceptions`.
- **Khorne**: reutilizada la implementación de C02a. `madbrains--equipment-restrictions`
  prohíbe armadura; Quartermasters y Flayerkin reciben la sección de armadura;
  Flayerkin solo lleva Hooks y no puede seleccionar otras armas. Sin cambios de
  motor ni pruebas repetidas.
- **Taal**: la nota de `campaign/magic.yaml` es una consecuencia de construcción,
  no casting. El consumidor compartido ya prohíbe `heavy-armour` y admite
  `light-armour`, casco y escudo en Horned Hunters y Ostlanders; no requirió
  código nuevo.
- **Ostlanders**: la fila `profiles/5` es Ruffians sin armas de proyectil, no el
  Priest of Taal. `ruffians--no-missile-weapons` ya está referenciada por el
  perfil; `weapon.pistol` se rechaza con «missile weapons are forbidden».
- **Conexiones previas conservadas**: Kislev, Marauders, Necrarchs, Savage Orcs
  sar, Horned Hunters, Vampire Hunters (Morr), Knights of the Bitter Moors,
  corsarios oscuros y Altos Elfos; Ulric/Verena con sus excepciones (pelt 6+,
  daga ceremonial, Sea Dragon Cloak).

## Claves exactas del paquete (41)

- `source/bands/mordheim/kislevites/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/kislevites/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/kislevites/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/marauders-of-chaos/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/necrarchs-mou/profiles.yaml/@/profiles/0/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/necrarchs-mou/equipment-access.yaml/@/equipment_lists/0/items/9/notes/unclassified` / `whole`
- `source/bands/mordheim/necrarchs-mou/equipment-access.yaml/@/equipment_lists/0/items/10/notes/unclassified` / `whole`
- `source/bands/mordheim/savage-orcs-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/horned-hunters/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/nipponese-expedition-web/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/nipponese-expedition-web/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` / `label`
- `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` / `permitted-weapons`
- `source/bands/mordheim/vampire-hunters-of-sylvania-lotd5/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` / `armour-prohibition`
- `source/bands/mordheim/knights-of-the-bitter-moors-mim/profiles.yaml/@/profiles/3/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/knights-of-the-bitter-moors-mim/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/trollheim/lustria-dark-elves/profiles.yaml/@/profiles/4/equipment_restrictions/2/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/0/equipment_restrictions/1/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/1/equipment_restrictions/1/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/2/equipment_restrictions/1/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/3/equipment_restrictions/1/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/4/equipment_restrictions/1/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/0/equipment_restrictions/2/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/1/equipment_restrictions/2/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/2/equipment_restrictions/2/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/3/equipment_restrictions/2/unclassified` / `whole`
- `source/bands/trollheim/lustria-high-elves/profiles.yaml/@/profiles/4/equipment_restrictions/2/unclassified` / `whole`
- `source/bands/mordheim/ostlanders/profiles.yaml/@/profiles/5/equipment_restrictions/0/unclassified` / `whole`
- `source/catalog/hirelings/hired-swords/grade-2b.yaml/@/profiles/20/equipment/fixed_items/1/notes/unclassified` / `rule`
- `source/catalog/hirelings/hired-swords/grade-1b.yaml/@/profiles/29/unresolved_references/1/unclassified` / `rule`
- `source/catalog/rules/special-rules.yaml/shared-rule.strictures/unclassified` / `whole`
- `source/bands/mordheim/black-orcs/profiles.yaml/@/profiles/2/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/1/equipment_restrictions/0/unclassified` / `whole`
- `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/5/equipment_restrictions/1/unclassified` / `whole`
- `source/bands/mordheim/khorne-raiders-sar/profiles.yaml/@/profiles/5/equipment_restrictions/2/unclassified` / `whole`
- `source/catalog/campaign/magic.yaml/@/lores/21/note/unclassified` / `priest-armour-clarification--scope--priest-heavy-armour-stricture`
- `item/wolf_pelt_cloak` / `may-not-wear-armour`
- `item/wolf_pelt_cloak` / `may-not-carry-blackpowder-weapons`
- `mechanic/defence.wolf-pelt-cloak` / `may-not-wear-armour`
- `mechanic/defence.wolf-pelt-cloak` / `may-not-carry-blackpowder-weapons`
- `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures/defence.wolf-pelt-cloak` / `may-not-wear-armour`
- `source/catalog/hirelings/hired-swords/grade-2b.yaml/hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures/defence.wolf-pelt-cloak` / `may-not-carry-blackpowder-weapons`

Las seis filas del pelt se reconcilian sin reabrir C01b/C01c: el 6+ sigue
procediendo del kit impreso y las prohibiciones de armadura y pólvora siguen
vivas.

## Evidencia mínima

- `pytest ... -k younguns`: 1 passed (nuevo discriminador de destinatarios y
  arma a dos manos). Las ocho pruebas previas no se repitieron.
- Sonda Taal: `heavy-armour` rechazada; `light-armour`, `helmet` (donde la lista
  lo publica) y `shield` por `off_hand_id` admitidos en Horned Hunters y
  Ostlanders.
- Reutilizadas sin repetir: `test_khorne_armour_belongs_to_its_two_printed_bearers`
  y `test_flayerkin_may_carry_only_its_hooks` (C02a); Ruffians rechaza
  `weapon.pistol`.
- `prepare`: 41 claves únicas, todas con `pending` previo no vacío y `{}` como
  disposición; conservación y notas validadas por la herramienta.

## Archivos propios

- `packages/typescript/domain/eligibility/{index,bridge}.ts` y bundle
  `packages/python/roster-construction/mordheim_construction/_eligibility.js`.
-  `sources/knowledge/bands/mordheim/{kislevites,marauders-of-chaos,necrarchs-mou,savage-orcs-kaz,savage-orcs-sar,horned-hunters,knights-of-the-bitter-moors-mim}/special-rules.yaml`;
  `knights-of-the-bitter-moors-mim/profiles.yaml`;
  `savage-orcs-kaz/equipment-access.yaml`;
  `nipponese-expedition-web/special-rules.yaml`;
  `vampire-hunters-of-sylvania-lotd5/{profiles,special-rules,equipment-access}.yaml`;
  `trollheim/lustria-dark-elves/profiles.yaml`;
  `trollheim/lustria-high-elves/special-rules.yaml`;
  `catalog/hirelings/hired-swords/{grade-1b,grade-2b}.yaml`.
- `tests/python/construction/test_c02c_equipment_restrictions.py`.
- Paquete: `build/c02c-package.json`.

## Bloqueos / límites

- Monturas y disparo quedan fuera; la ballesta de Shootaz se resuelve en la
  lista canónica, no en una simulación de disparo.
- Las notas «single-use» / «bearer-allowance» pertenecen a C15. La prohibición
  de monturas de Black Orcs ya se conectó en C02a y no se reabrió aquí.
- No se ejecutó E2E, parity ni suites globales. No se escribió el CSV.
