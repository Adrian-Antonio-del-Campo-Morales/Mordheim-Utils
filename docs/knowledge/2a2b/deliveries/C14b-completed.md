# C14b — Kits físicos y defensas intrínsecas

**Estado: completo, 2026-10-15.** Base `a1f92653` intacta (`%TEMP%/c14b/base-*`). Este pase añade
dos archivos de fuente y uno de pruebas; los demás frentes ya estaban integrados (mano del
instrumento del Cursed Piper, coraza 4+ de House Guard, y las reconciliaciones de Att'la, Gibbets y
retirada de equipo).

**Capacidad implementada (cierra `weapons-and-save`).** El perfil `witch-elf` de
`dark-elf-corsairs-mou` declara su kit obligatorio en la clave canónica del perfil de banda
(`fixed_equipment`: dos `sword`, `dark_elf_blade_weapon_upgrade`, `dark_venom`) y `compile_fighter`
lo resuelve con dos ayudantes nuevos: las copias de arma de una mano del kit ocupan la mano
principal y la secundaria, la cualificación que el propio kit declara (`material.dark-elf-blade`)
reviste exactamente esas copias y el recubrimiento (`poison.black-venom`, +1 F) las cubre; cada
mano conserva el operador de su propio ejemplar. No se añade lista de equipo (la oferta es
exactamente sus piezas impresas y sus operadores, sin acceso genérico), no se lee
`resolveHirelingKit` (sigue en H02) y no se simula adquisición. Frenesí por drogas y la salvación
intrínseca de 5+ ya conectadas se mantienen.

**Comprobación mínima.**
- `pytest tests/python/construction/test_c14b_physical_kits.py` → `13 passed`, EXIT=0
  (`%TEMP%/c14b/pytest-c14b-kit2.txt`): las dos hojas recubiertas con su identidad física, el ataque
  extra del segundo arma en el pool existente (`build_attacks`), +1 F en el objetivo de armadura y
  la salvación 5+.
- Esquema editorial del paquete de la banda tocada → `1 passed` (`%TEMP%/c14b/pytest-dec-schema.txt`).
- A/B del compilador: instantánea de los 23 perfiles con `fixed_equipment` en la base prístina (con
  mi dato de KB, sin mi conexión) frente al árbol actual → difiere **sólo** `witch-elf` (antes: una
  espada lisa y sin mano secundaria; ahora: dos hojas recubiertas con dos piezas físicas); los otros
  22 idénticos (`%TEMP%/c14b/kits-base-withdec.json` vs `kits-mine.json`).
- `test_catalog.py` y `test_editorial_schemas.py` conservan **conjuntos de fallos idénticos** a la
  base prístina (9 y 7, heredados de trabajo concurrente: hireling core, combat-equipment,
  close-combat, normalizador); ninguno nuevo.

**Integración del coordinador.** Cerrada `weapons-and-save` con propuesta nueva,
snapshot completo, conservación de las 4.556 claves/textos/huellas/notas y control
concurrente (`%TEMP%/c14b-kit-integration-6ab01217`). El coordinador corrigió además
la selección explícita de `weapon.sword`, que omitía el kit compuesto: ahora conserva
ambas hojas y sus recubrimientos igual que la selección por defecto. Los dos casos
del discriminador existente pasan (`%TEMP%/c14b/coordinator-explicit-kit.txt`);
resto de evidencia reutilizada sin repetir baterías. C14b cerrado.
