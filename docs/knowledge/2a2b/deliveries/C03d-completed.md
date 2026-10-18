# C03d — Destinatarios y combinaciones en objetos

**Estado: integrado y cerrado**, 5 cláusulas resueltas (tres cambios declarativos y dos consumidores existentes reconciliados). Base
inicial: rama `2A2B`, HEAD `a1f92653`, árbol compartido con cambios heredados de
otros escritores. Incremento propio: 3 hunks de datos + 1 archivo de pruebas
nuevo; no se tocaron archivos compartidos del motor ni de otros paquetes.

## Capacidades antes → después

- **Huge Jaws (cambio real).** El destinatario impreso «Saurus Heroes only» era
  el único Héroe inicial (`eligibility: [saurus-totem-warrior]`): un Saurus Brave
  promovido no podía elegir la marca. Ahora la marca declara el rol
  (`applies_to.profile_types: [hero]`) junto con los perfiles Saurus que lo
  pueden llenar: el Totem Warrior accede, un `saurus-braves` con
  `promotion.hero` suministrado accede y compila `trait.huge_jaws`, un Saurus
  Brave sin promover (secuaz) se rechaza y ningún perfil Skink accede, promovido
  o no. No se añadió compuerta de fase: la marca no queda limitada a los Héroes
  iniciales. Los Skinks conservan Venom Glands.
- **Skull Busta — proyección de destinatario (reconciliado).** La prohibición a
  Goblins vivía sólo en `notes`; ahora la línea declara sus destinatarios Orco
  (`applies_to.profile_ids`), como ya hacen las líneas hermanas `bow` y
  `kumfy_gear`. `entryReachesProfile` niega al Gobbo Boyz desde esa declaración,
  la oferta no le llega, `equipmentIssue` responde `equipment_not_permitted` y la
  selección directa la rechaza `compile_fighter`. La combinación se re-comprobó:
  escudo legal, otra arma y mano adicional rechazadas por el predicado
  compartido, el arma debe ser la principal. `F063` queda descargado por el
  ruling del 2026-10-04 (Knight's Helm), que declaró que ya no bloquea.
- **Maibd Poison (reconciliado, con corrección de encuadre).** El destinatario
  Witch Elves se publica en la línea que suministra la dosis
  (`applies_to.profile_ids: [witch-elves]`). La procedencia se conserva: la dosis
  del mercado abierto sigue legal para otros perfiles Druchii (un Noble y un
  Corsair con `poison.black-lotus` compilan); no se añadió prohibición universal.
  El precio, el descuento y el ciclo entre batallas siguen excluidos.
- **Tridente / Priest of Manann (reconciliado).** La línea «Priest of Manann
  only» la lleva el propio kit del perfil: el censo sobre todo el catálogo de
  hirelings (131 perfiles) da el tridente a ese único perfil; el tridente del
  Imperial Assassin procede de su propio Weapons Master, una ruta distinta que
  esta cláusula no debe estrechar.

## Archivos propios / base

Propios: `sources/knowledge/bands/mordheim/savage-orcs-kaz/equipment-access.yaml`,
`sources/knowledge/bands/mordheim/druchii-mic/equipment-access.yaml`,
`sources/knowledge/bands/trollheim/lustria-lizardmen/special-rules.yaml`,
`tests/python/construction/test_c03d_object_recipients.py`. Base exacta previa,
incremento final (con SHA-256) y diff base→final:
`C:\Users\Pholtergate\AppData\Local\Temp\c03d-base`,
`...\c03d-final`, `...\c03d-increment.diff`.

## Comprobación

`python -X utf8 -m pytest tests/python/construction/test_c03d_object_recipients.py -q`
→ **4 passed, exit 0** (`%TEMP%\c03d-focused-3.txt`). Archivos directamente
afectados: `test_local_weapon_items.py`, `test_t13_construction_recipients.py`,
`test_c03c_dependency_connections.py` pasan junto al nuevo
(`%TEMP%\c03d-affected.txt`: 21 fallos, los 21 de
`tests/python/web/test_knowledge_artefact.py`, que falla igual con mis tres
archivos en su base —「conflicting Spanish rule label for 'Netter'」, ajeno a este
incremento; evidencia en `%TEMP%\c03d-artefact-base.txt`). Esquemas editoriales
de los tres documentos: OK. Sonda de comportamiento:
`%TEMP%\c03d-probe-3.txt`.

## CSV e integración

Coordinador, 2026-10-16: las tres fuentes entregadas coinciden byte a byte con
`%TEMP%\c03d-final`; se reutiliza la evidencia focal existente, sin nueva batería.
Cinco cambios aplicados sobre el CSV actual, conservando sus 4.556 claves,
textos, huellas y notas mediante `prepare` → preview → `apply --write`.
Snapshot, propuesta, paquete y salidas:
`C:\Users\PHOLTE~1\AppData\Local\Temp\c03d-coordinator-integration-xk6ldh96`.

Propuesta por `(id, clause_id)`: `%TEMP%\t13-c03d-changes.json`; paquete
validado `%TEMP%\t13-c03d-prepared.json` (5 cambios, CSV
`sha256 f6eb05ee8892e852fe83e4c6829250203e288af854a2751d18f35448278bc8d2`).
El ejecutor sólo utilizó `query` + `prepare` + `apply` en preview; la escritura
corresponde a la integración del coordinador descrita arriba. Sin E2E, commits ni pushes.

## Pendientes exactos

Ninguno dentro de C03d. Fuera de este encargo: el artefacto web (etiqueta
`Netter`) y la rama redundante de `profileEquipmentItems` para
`savage-orcs-kaz/gobbo-boyz`, que el coordinador puede retirar ahora que el
destinatario es dato declarado.
