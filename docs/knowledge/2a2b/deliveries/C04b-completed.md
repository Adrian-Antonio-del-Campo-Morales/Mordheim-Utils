# C04b — Acceso a listas: promoción, fase y excepciones

**Estado integrado por el coordinador, 2026-10-16: completo, 23 cláusulas.**
Las dos herencias Skaven finales ya seleccionan sus miembros admitidos y rechazan
Art of Silent Death. El coordinador corrigió el selector: tipo Héroe y perfiles
Skaven autorizados, incluidos Clanrats/Skavenslaves con promoción suministrada;
el Secuaz sin promoción sigue rechazado. Sólo se ejecutaron los dos discriminadores
afectados tras el remate: 2 passed, `%TEMP%/c04b-skaven-coordinator-final.txt`.
Últimas dos filas integradas con copia completa, conservación/concurrencia en
`%TEMP%/c04b-skaven-final-integration-b8hgtb88`. El detalle inferior conserva la
primera entrega y el incremento del ejecutor; el selector de cuatro Héroes iniciales
queda supersedido por esta corrección.
Las 23 filas se integraron conservando 4.556 claves/textos/huellas/notas y rechazando
concurrencia, con copia íntegra en `%TEMP%/c04b-coordinator-integration-k3rxxeva`.
Se reutilizó la evidencia del ejecutor sin repetir baterías. Sin commits, pushes ni E2E.

## Capacidad antes → después

| Capacidad | Antes | Después |
|---|---|---|
| Ghoul promovido (Fallen) | 0 ofertas siempre: el perfil no declaraba lista y el henchman no alcanzaba ninguna | la regla impresa se conecta: el Ghoul declara la lista de los Caídos y sus líneas nombran al héroe como destinatario, así que el Henchman no alcanza ninguna y el Héroe configurado (`promotion.hero`) todas; la selección directa se rechaza sin la promoción y compila con ella |
| Mercenarios de Maldred | creación y post-creación idénticas (23 ofertas): la primera mitad de la cláusula no existía | la lista de Mercenarios se declara con `compiler.mercenary-equipment-at-creation`: 28 ofertas antes de la primera partida y 23 fuera de ella; la fase es el mismo hecho suministrado (`equipment.post-creation`) que ya usa el resto del motor, y la prohibición de armas a distancia de la misma regla se conserva |

## Transporte

- Fuentes: `fallen-the-rel/{profiles,equipment-access}.yaml` (destinatario `profile_types: [hero]`,
  sin inventar notas ni piezas) y `disciples-of-maldred-mou/special-rules.yaml` (segundo binding de la
  regla existente).
- Consumidor: `eligibility/index.ts::contractEquipment`, leído por `profileEquipment`, de modo que la
  oferta y la aceptación deciden con la misma declaración; el contrato queda registrado en
  `contracts.py::COMPILER_CONTRACTS` y en `implemented-canonical-families.yaml`. `_eligibility.js`
  regenerado y `--check` = current.

## Comprobaciones

- `tests/python/construction/test_t13_construction_recipients.py` → **37 passed** (dos casos nuevos:
  Ghoul promovido/no promovido y la fase de Maldred, con control del Prophet y de la banda ajena).
- `test_shared_eligibility.py` + `test_construction_variants.py` → **36 passed**;
  vitest `canonical-choices` **15** + `shared-eligibility`/`band-rule-recipients` **36**; `tsc --noEmit`
  limpio. Salidas guardadas en `%TEMP%/c04b-*.txt`.
- Reconciliaciones medidas, no supuestas: Thieves Guild (Bagh Nakh sólo para el Assassin), Lustria
  Pirates (Scourge/Parrot/Flag), Corsairs y la capa de mar, Outlaws (límites de arco publicados y
  exención del Cleric), Boatswains, Liche, las dos concesiones de armadura y la variante de lanza
  (caballeros errantes sí, Caballero Errante no, peregrinos no).

## CSV (sólo `query` + `prepare` + `apply` en preview)

`%TEMP%/t13-c04b-prepared.json`: 20 claves `(id, clause_id)` con `pending {}`, verificación ejecutada
y nota conservada; el preview de `apply` valida la conservación. No se ejecutó `--write`: integra el
coordinador con snapshot íntegro.

## Incremento C04b-2 — herencia del reglamento Skaven (Mors y Skryre)

Las dos filas compuestas que quedaban abiertas están resueltas por la mitad que faltaba: el acceso
impreso a las **Skaven Special Skills** del reglamento, con destinatarios y exclusión publicados.

| Capacidad | Antes | Después |
|---|---|---|
| Habilidades especiales Skaven del reglamento (Clan Mors) | la regla compuesta era un `LATER/NO` sin lista ni destinatarios: los Héroes no alcanzaban ninguna entrada y el catálogo de especiales quedaba en «lista sin transcribir» | `band--rulebook-inheritance` publica su lista admitida (`profile.skill-access`, categoría `special`) y nombra a sus cuatro Héroes; las cuatro entradas impresas se publican como reglas `warband_skill` seleccionables que reutilizan los operadores del reglamento (`mechanic.black-hunger`, `special-rule.band--skaven-special-skills-tail-fighting`) y la quinta, el Arte de la Muerte Silenciosa, se rechaza por su nombre |
| Habilidades especiales Skaven del reglamento (Clan Skryre) | ídem, sobre la página 41 | ídem, con sus cuatro Héroes propios (`master-engineer`, `engineers`, `warlock-engineer`, `engineer-apprentices`); el `jezzail` propio de la banda sigue ofrecido |

**Miembros determinados por la KB** (no por parecido de nombres): la tabla del reglamento es la que
la banda reglamentaria Skaven ya publica y ejecuta, así que los miembros admitidos son Hambre Negra
(ataque propio, `mechanic.black-hunger`), Combate con la Cola (contrato de compilador ya usado por
la cola y su mano extra), Corredor de Muros e Infiltración (miembros impresos cuyo contenido completo
es movimiento/despliegue: se publican con su disposición fuera del duelo). El quinto miembro,
Art of Silent Death, es el que la cláusula excluye: no se publica como miembro y `compile_fighter`
lo rechaza como no disponible para estas bandas, en vez de concederlo en silencio.

**Transporte**: `sources/knowledge/bands/mordheim/skaven-of-clan-{mors,skryre}-kaz/{band,special-rules}.yaml`
y `catalog/rules/implemented-canonical-families.yaml` (los dos miembros compartidos se registran en
sus familias `mechanic.black-hunger` y `special-rule.band--skaven-special-skills-tail-fighting`, sin
crear operadores nuevos). Sin cambios en TS: la tabla se resuelve con el mecanismo compartido de
listas y con los contratos que ya existían, así que no hubo que regenerar `_eligibility.js`.

**Comprobaciones** (salida real conservada en `%TEMP%/c04b-skaven-out.txt`):
`tests/python/construction/test_t13_construction_recipients.py` → **39 passed** (dos casos nuevos:
ofertas/destinatarios/exclusión, y conexión hasta `compile_fighter` con los contratos existentes);
`test_t13_canonical_choices.py` → **65 passed**; vitest `band-rule-recipients` + `canonical-choices` →
**28 passed** y `shared-eligibility` → **23 passed**. Validador de KB
(`tools/knowledge/audit_schema_strictness.py`): **0 findings duros** y ninguno sobre estas bandas (sus
5 «unjustified» son anteriores y ajenos). `test_band_translation_parity.py` falla en
`ogre-hunting-party-web/band--ogre-hunting-skills-crude-belch.effect` (archivo de otro agente: su
`effect_i18n.es` repite el inglés); mis dos bandas cumplen las tres reglas de paridad.

El bloque `counts:` del mismo registro se refrescó para describir el archivo completo (260 familias /
998 miembros / compiler 65, mechanic 157, trait 38), tal y como exige su contrato («it must agree
with `families`»); incluía el incremento propio y el de otro agente en vuelo, y ahora declarado y
contenido coinciden. Comprobaciones repetidas sobre el estado final: sonda de comportamiento
(exit 0) y `audit_schema_strictness.py` con hallazgos idénticos a la ejecución previa (44: 0 duros,
39 justificados, 5 ajenos), y `test_t13_canonical_choices.py` + `test_t13_construction_recipients.py`
→ **104 passed**.

**CSV**: `prepare` + `apply` en preview sobre las dos claves compuestas
(`%TEMP%/t13-c04b-skaven-prepared.json`, snapshot `sha256 2c733d8b…`, preview con `pending {}`,
verificación ejecutada y nota añadida). No se ejecutó `--write`.

## Pendientes exactos

- La herencia de equipo Dwarf Guildsmen queda reconciliada por el coordinador:
  listas ya declaradas y destinatarios actuales, sin editar el archivo compartido con C05a.
- Ninguno de C04b. La observación sobre No Armour de Estalian corresponde a C04a,
  no es un pendiente de este paquete ni modifica su disposición por este cierre.
