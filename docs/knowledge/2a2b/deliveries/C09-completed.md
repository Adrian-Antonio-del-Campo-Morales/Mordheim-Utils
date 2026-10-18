# C09 — Preparaciones y características compartidas

**Estado:** completo, diez cláusulas cerradas,
2026-10-15. Rama `2A2B`, HEAD `a1f92653`, checkout compartido
con trabajo concurrente ajeno. Base inicial y snapshot del CSV en
`D:/DEVEL/Mordheim/_c09-out`. Sin commits ni pushes.

**Capacidades (antes → después).**

1. **Brewers, `brew-characteristic`** (era `unimplemented`, sin binding). Ahora
   `condition.troll-brew-special-brew` enlaza `profile.characteristics` con +1
   Habilidad de Armas y +1 Fuerza y su tope impreso de 10, declarado con un nuevo
   parámetro `maximum` del binding; los resultados 1-2 y 3-4 ya usaban esa ruta
   suministrada. El llamante aporta el enano y el resultado; la nominación D3, el
   grupo y el barril quedan fuera.
2. **Remas/Remasen +1 Ld** (eran `LATER`/`NO`, binding `null`). Las reglas
   `band--remasen-officer-leadership` y `band--remas-officer-leadership` son ahora
   `warband_variant` seleccionables que enlazan `profile.characteristics`
   (`captain`/`champions`/`youngbloods` y `mercenary-captain`/`champions`/`recruits`).
3. **Paladin of Horror** (era `LATER`/`NO`). Modificación seleccionable que da +1
   Liderazgo sólo a `necromantic-abomination`.
4. **Power Grab**: `condition.power-grab-majority` (+1) y `-minority` (-1) Liderazgo
   suministrado al inicio del enfrentamiento; una sola raza por partida.
5. **Human Rememberer**: `_supplied_rememberer` prepara la línea Humana impresa y la
   lista de equipo Mercenaria del reglamento en lugar de la lista Dwarf Warrior,
   sólo para ese duelista.
6. **Hueco corregido:** un id de regla seleccionada repetido aplicaba su bono dos
   veces, contra el criterio «exactamente una vez» del paquete; `compiler.py`
   resuelve ahora una vez cada selección.

**Reconciliado:** Condemned y Middenheim ya funcionaban. Comprobado en KB que
los perfiles Middenheim imprimen Fuerza 3; el +1 produce el 4 impreso.

**Alchemist completado por el coordinador:** el usuario fijó un intento al inicio
de cada turno propio. Backley reintenta el test de Resistencia hasta superarlo y
restaura sólo las penalizaciones aplicadas. El adicto reintenta hasta 6, recupera
la acción ese turno y obtiene Vigortia una sola vez. Sin tiradas en turno rival
ni tras liberarse. Ruling registrado; Movement y campaña siguen excluidos.

**Cambios:** `catalog/rules/conditions.yaml`, `conditions.py`, `compiler.py`,
`source_profiles.py`, `defs.schema.json`, cinco fuentes de banda y
`test_t13_shared_preparations.py` (nuevo).

**Comprobación:** `test_t13_shared_preparations.py` (8 casos) y
`test_characteristic_bonus_contract.py` → 48 aprobados, exit 0
(`_c09-out/c09-cases-2.txt`). El coordinador corrigió Brewers para rechazar
henchmen y una especie suministrada no enana; pasó el caso de destinatarios ampliado
(`coordinator-recipient.txt`), sin repetir la batería completa.
El log editorial permitió corregir dos omisiones del cierre C03b del coordinador:
`when_items` en el esquema y nombres traducidos en sus bindings. Pasaron los dos
contratos afectados (`coordinator-c03b-schemas.txt`); no se amplió la auditoría.
Alchemist: tres discriminadores nuevos y un caso existente aprobados
(`%TEMP%/alchemist-recovery-focused.txt`), cubriendo reintento, caducidad, mínimo
de características y no duplicación. Cambios en `modular/alchemy.py`, estado,
consumo por turnos y descripciones canónicas. E2E excluidos.

**CSV:** ocho cierres integrados mediante nueva preparación, preview y escritura,
conservando 4.556 claves, textos, huellas y notas y verificando concurrencia.
Snapshot/propuesta/salidas: `%TEMP%/c09-integrated-q04huvew`. Las dos filas
Alchemist se cerraron después con snapshot nuevo y controles de conservación:
`%TEMP%/alchemist-completed-wm_s1htw`. Sin pendientes propios, commits ni pushes.
