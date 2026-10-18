# C01c — Ataques naturales y variantes Trollheim

**Estado integrado: 34/34 cláusulas cerradas (2026-10-17).** Las dos filas
restantes del Tomb Scorpion se integraron con C01b: ambos orígenes declaran el
veneno como efecto de su ataque, sin conceder acceso al frasco. Consumidor
regenerado, evidencia focal del ejecutor reutilizada y CSV integrado con snapshot,
conservación de 4.556 claves/textos/huellas/notas y control concurrente.

## Capacidades implementadas

**`profile.natural-attacks` es ahora un contrato publicado y consumido.** El
compilador leía la ausencia de daga gratuita y la lista de equipo vacía; el
binding existía en cuatro bandas de Mordheim sin que nadie lo leyera. Ahora
`compile_fighter` viste al luchador con el ataque natural que la banda declara,
antes de la heurística, y `profile.fist` sigue prevaleciendo (Dragon Monk
conserva puño, exención de penalizaciones y crítico desarmado). Un arma explícita no se
traga: `weapon.sword` llega a la comprobación de acceso y se rechaza.

**Trece perfiles publican su propia regla `--natural-weapons`** con dos
bindings: `profile.equipment-restrictions` (`forbids: weapons, armour`; Strigoi
añade `equipment` para «or items») y `profile.natural-attacks`. Cubre Great
Cats, Cold Ones, Wulfen, Wolves, Street Dogs, Mastiffs, Strigoi Vampire,
Carrion Ghoul, Zombie, Ghoul, Black Hounds, Jackals y Rat Ogre, cada uno con su
texto, manual, página y traducción. Alcance de la prohibición del Rat Ogre
evaluado: el token de equipo no alcanza `weapon.natural-attacks`, así que sus
mandíbulas siguen legales.

## Reconciliaciones

Los seis perfiles `no-unarmed-penalty` (Strigoi, Carrion Ghoul, Zombie, Ghoul,
Black Hounds, Jackals) y los dos `natural-jaws` verifican consecuencia directa:
Fuerza y Ataques impresos, `strength_bonus`/`target_armour_bonus` en (0, 0),
oferta vacía y rechazo directo de espada y armadura. La dependencia de Beastmaster
de los Cold Ones y las líneas de disponibilidad (Strigoi-only, foreign/native
background) siguen siendo hechos de plantilla. `shared-rule.natural-weapons`
llega a un binding consumido en las dos bandas que la citan. Remates previos
intactos: la ausencia de daga no regala ataque natural, el veneno exige arma en
la mano que lo recubre y Cannibal Dwarfs mantiene `weapon.club`.

## Dependencias y límites

- Dos filas Tomb Scorpion: cerradas mediante la integración compartida de C01b.
- Defecto separado de preparaciones resuelto el 2026-10-17: preparationIssue
  comparte las restricciones y excepciones impresas entre oferta y compilación,
  sin convertir una lista corta de armas en prohibición de consumibles. Conserva
  prohibiciones de equipo/drogas y distingue inmunidad de permiso. Bundle
  regenerado por el ejecutor; el coordinador ejecutó test_preparation_access.py:
  ocho casos correctos, salida en `%TEMP%/preparation-coordinator-final.txt`.
  Retirado el problema del registro; no se modificó el CSV ni el cierre 34/34.
- La suite KB completa está roja por trabajo ajeno en curso (Banshee cold-steel,
  Veteran Tracker de trappers, mutaciones de clan-moulder, condiciones de
  Disability, recuento de mapeos de objetos); ninguna de esas fallas nombra las
  filas ni los archivos de este incremento.

## Rutas

- Integración del coordinador, 2026-10-17: quince filas aplicadas con cierre,
  snapshot íntegro, validación de conservación de 4.556 claves/textos/huellas/notas
  y control concurrente. Artefactos:
  `C:\Users\PHOLTE~1\AppData\Local\Temp\c01c2-coordinator-integration-vj1ffxg0`.
  Evidencia existente reutilizada; no se repitieron las 37 pruebas. Las dos filas
  Tomb Scorpion se cerraron después con C01b; integración final en
  `%TEMP%/c01b-final-coordinator-p51qbchj/`. La discrepancia separada de
  preparaciones se resolvió posteriormente, como se indica arriba. Sin E2E,
  commit ni push.

- Base exacta: `C:\Users\Pholtergate\AppData\Local\Temp\c01c2-base\`
  (`base/` con las nueve copias previas, `BASE-SHA256.txt`, `tree.tar`,
  sha256 `4cb9e4ed…`).
- Parche del incremento: `…\c01c2-base\c01c2-natural-weapons.patch`
  (13 bloques + 10 líneas de compilador, sha256 `a2f5929c…`; revierte limpio
  sobre el árbol actual y no incluye cambios ajenos).
- CSV: `C:\Users\Pholtergate\AppData\Local\Temp\t13-c01c2-natural-prepared-2.json`
  — 15 filas, `sha256 76ab1dbd…`, snapshot `csv 97d501da…`, preparado sin
  `apply --write`. No incluye las dos filas del Tomb Scorpion.
- Evidencia focal: `C:\Users\Pholtergate\AppData\Local\Temp\c01c2-final.txt` →
  **37 passed** (`test_c01c_natural_variants.py`); sonda de los trece perfiles en
  `…\c01c2-probe3.txt`. Sin E2E, sin commit, sin editar plan ni índice.
