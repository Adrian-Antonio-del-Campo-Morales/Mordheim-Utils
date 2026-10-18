# C07b — equivalencias impresas de armas, armaduras y materiales

## Estado

Integrado y cerrado: 23 cláusulas; la cláusula Yari restante se completó en R13.
La entrega original aportaba 21 cierres (10 con implementación y 11
reconciliados); el coordinador terminó Pointy Stick. Base inicial fuera del entregable:
`D:\DEVEL\Mordheim\C07b-base`; checkout de entrega `D:\DEVEL\Mordheim\C07b-work`
(rama 2A2B del 2026-10-16 08:34). Diff de entrega: 9 archivos de fuente/código
modificados y 2 archivos de prueba nuevos; ningún cambio ajeno alterado.

## Capacidades (antes → después)

**Implementación nueva (10):**

- Palo puntiagudo: item no registrado → `pointy_stick` con
  `mechanic_id: weapon.dagger` y kit fijo impreso de las dos Mobs Snotling
  (Crooked Moon, Night Goblins); el ataque compila la daga con su +1 a la
  salvación enemiga y un build con otra arma se rechaza.
- Pala de Sylvania: `out_of_scope` → `weapon.halberd` (ambas líneas de banda).
- Peto de bronce (Khemri): `out_of_scope` → `armour.light-armour`.
- Bastón de Viaje: `out_of_scope` → `weapon.travel-staff` con filas nuevas de
  mecánica y ejecución (iniciativa +1; sin parada ni dos manos) y nota de banda
  corregida.
- Thinglash y Cazacosas: `out_of_scope` → `weapon.thinglash` (S+1,
  `target_armour_bonus` 1, `cannot_be_parried`) y `weapon.thing-catcher` (dos
  manos); `whipcrack_weapon` reconoce la familia nueva.

**Reconciliación (11, capacidad ya existente; sólo evidencia ejecutada):**
Ashigaru/Wall of Steel, Shock Rod (primera embestida y dos manos), Dwarf Axe
(Clan Angrund y las dos bandas Karak Azgal que la heredan), Gromril Armour y
material de Gromril de Clan Angrund, mejora del Knight Errant y material Dark
Steel. Yari queda completo mediante las empuñaduras canónicas integradas desde R13.

## Cambios

`catalog/items/combat-equipment.yaml` (palo puntiagudo, pala),
`catalog/items/weapons-close-combat.yaml` (thinglash, cazacosas),
`catalog/items/trollheim.yaml` (peto, bastón), `catalog/mechanics/close-combat.yaml`
y `catalog/mechanics/execution.yaml` (tres filas nuevas), los `profiles.yaml` de
Crooked Moon y Night Goblins (kit fijo),
`bands/trollheim/chaos-streets-arcane-society/equipment-access.yaml` (nota) y
`packages/python/combat-engine/mordheim_combat/modular/equipment.py`. Cada
equivalencia sale del texto impreso ya presente en la KB; sin búsqueda externa.

## Comprobación

- `pytest` de los dos archivos nuevos más `test_tc14_whip.py` → **37 passed**,
  exit 0.
- `test_catalog.py` → 7 failed / 40 passed, **mismo conjunto que `C07b-base`**
  (rojos previos, fuera del paquete).
- `test_editorial_schemas.py` (`-k` de los documentos tocados) → 4 failed,
  idénticos a la base salvo índices desplazados.
- Salidas en `D:\DEVEL\Mordheim\_c07b-out\`. Sin E2E.

## CSV e integración

**Coordinador, 2026-10-16:** integración por hunks de nueve archivos y dos pruebas
nuevas, preservando R13 y los cambios concurrentes. Pointy Stick se declara
YES/implemented y enlaza weapon.dagger, manteniendo grant:none: el bono permanece
en el arma, no en el portador. Dieciséis casos en los dos archivos nuevos pasan
sobre el estado integrado (`%TEMP%\c07b-coordinator-focused.txt`). Veintidós filas
aplicadas con snapshot íntegro, validación de conservación de 4.556 claves/textos/
huellas/notas y control concurrente. Base previa, parche, propuesta y salidas en
`C:\Users\PHOLTE~1\AppData\Local\Temp\c07b-coordinator-zris8tq1`.

Propuesta preparada fuera del repo, **sin `--write`**:
`D:\DEVEL\Mordheim\_c07b-out\C07b-package.json` (sha256 `2720054b…`), cambios en
`c07b-changes.json`. 22 claves `(id, clause_id)`: 21 con `pending {}`, verificación
`executed` y nota, más 1 nota de alcance. `prepare` exit 0 y `apply` preview exit 0
sobre el snapshot `sha256 33b3f3cf…` (4.556 claves conservadas).
**Cierre final:** Yari integrado desde R13 con una única identidad física y
ambas empuñaduras accesibles. Seis casos finales afectados correctos
(`%TEMP%\yari-coordinator-final.txt`), incluida la actualización del conjunto
de ausencia para el Peto de Bronce conectado por C07b. Sin pendientes dentro
del paquete, E2E, commit ni push.
