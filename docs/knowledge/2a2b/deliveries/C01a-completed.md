# C01a — Ataques naturales y restricciones de equipo (reglas nativas Mordheim)

**Estado final: integrado y cerrado, 27/27 (2026-10-17).** El remate de Banshee,
incluidos Cold Steel, inmunidades y ausencia de Iniciativa, queda registrado en
`C01a-Banshee-completed.md`; supera el pendiente histórico descrito debajo. La
entrega inicial cubrió 26 de las 27
cláusulas verificadas —tres capacidades implementadas (kit impreso, esclavo
Skaven y objetos bajo «no equipment») y el resto reconciliado sin cambio— y 1
bloqueada. Base: rama `2A2B`, HEAD `a1f92653`, árbol con cambios heredados de
otros escritores. No leí ni escribí archivos de C11/C02b.

## Capacidades antes → después

- **Kit impreso bajo su propia prohibición.** El `snotling-mob` imprime «may only
  ever use its free pointy stick, which counts as a dagger» y su
  `fixed_equipment: [dagger]` lo rechazaba su propia cláusula `equipment`:
  **no existía configuración legal**. `index.ts::boundEquipment` viajaba con
  `fixed_equipment: []`; ahora el kit impreso viaja con la prohibición en sus dos
  grafías y el Snotling compila la daga con su +1 a la salvación enemiga.
  Espada, armadura, casco, veneno y preparación siguen rechazados en selección y
  en compilación directa. El mismo hueco se cierra para
  `khemri-cursed-of-karak-zorn/cannibal-dwarfs` (club impreso), fuera de la
  selección.
- **Esclavo Skaven.** «count as armed with a single dagger» compilaba
  `weapon.natural-attacks`. Declarado su kit impreso, resuelve la daga y su
  oferta se reduce a esa pieza.
- **«No equipment» juzga objetos, no sólo armas.** El escenario compartido
  juzgaba manos, armadura y defensas: un Ghoul compilaba `poison.black-lotus`
  sobre sus huesos. Materiales, venenos y preparaciones pasan por el mismo
  predicado que la oferta. Cierra además `ogre-pit-fighter`
  (`material.gromril`) y `lustria-dark-elves/corsairs` (`poison.black-venom`).

## Reconciliaciones (sin cambio)

Las cláusulas no listadas ya cumplían: configuración legal con ataque intrínseco
en la Fuerza y el número de ataques impresos, sin daga física ficticia (la daga
por defecto se sustituye por el ataque natural), rechazo directo y oferta sin
piezas prohibidas. Excepciones conservadas: los huesos de Ghouls y Charnel Guard
(A=2, sin penalización de daga) no son alcanzados por `equipment`/`weapons`, y
la armadura no se prohíbe donde el impreso no la nombra. Ninguna cláusula recibe
inmunidad general al puño (`ignores_unarmed_penalties` falso en las 26): el «sin
penalización» impreso lo entrega el ataque natural.

## Pendiente exacto

`rule/mordheim/necrarchs-mou/banshee--equipment-restrictions/profile.equipment-restrictions`
sigue abierto: `sources/knowledge/registry/runtime-scope.yaml` (16-21) y
`packages/typescript/domain/campaign/construction-tables.json` excluyen el perfil
del duelo porque su Iniciativa impresa está en blanco, y el registro pide una
decisión de T13. No modifiqué registros compartidos.

## Archivos propios, base y parche

`packages/typescript/domain/eligibility/index.ts` (2 hunks),
`packages/python/roster-construction/mordheim_construction/_eligibility.js`
(regenerado con `npm run build:eligibility`, `check:eligibility` OK),
`sources/knowledge/bands/mordheim/skaven-of-clan-skryre-rel/profiles.yaml`
(1 hunk) y `tests/python/construction/test_c01a_intrinsic_attacks.py` (nuevo).
`%TEMP%\c01a-base` guarda base exacta (`BASE-SHA256.txt`), diff base→final
(`c01a-increment.diff`) y `FINAL-SHA256.txt` (index.ts `350bbf14…`, bundle
`e01b2f0d…`, profiles `69c101a3…`, prueba `088d2db1…`).

## Comprobación y CSV

Coordinador, 2026-10-16: 26 propuestas aplicadas sobre el CSV actual con snapshot
íntegro, validación de conservación de 4.556 claves/textos/huellas/notas y control
concurrente. Artefactos: `C:\Users\PHOLTE~1\AppData\Local\Temp\c01a-coordinator-integration-4iifez5a`.
Perfil Skaven y prueba mantienen las huellas entregadas; los dos hunks propios
de eligibility siguen presentes junto al remate posterior de C02b. Evidencia
existente reutilizada, sin nueva batería. Banshee permanece abierta.

`pytest tests/python/construction/test_c01a_intrinsic_attacks.py -q` → **82
passed, exit 0** (`%TEMP%\c01a-test-final.txt`): ataque intrínseco de las 26 en S
y A impresas, rechazos directos, ofertas y una ronda real resuelta. Afectados:
vitest `shared-eligibility` + `canonical-choices` (38 passed),
`test_profile_bindings.py` + `test_c14b_physical_kits.py` (53 passed),
`npm run typecheck` (exit 0). Sonda de los 27:
`%TEMP%\c01a-acceptance-final.txt` (sólo cambian Snotling y esclavo). `query` +
`prepare` de 26 propuestas por `(id, clause_id)` (`%TEMP%\t13-c01a-changes.json`
→ `t13-c01a-prepared.json`, exit 0), sin `--write`; la fila de la Banshee queda
intacta. Sin E2E, commits ni pushes.
