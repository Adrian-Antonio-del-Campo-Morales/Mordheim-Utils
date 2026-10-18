# C03a — Destinatarios del catálogo de comercio, conectados a la construcción

**Cierre 2026-10-15: los tres pendientes quedan resueltos y sus filas del CSV preparadas**
(sólo `query`/`prepare`; el coordinador aplica). Runestones y el permiso por defecto siguen
igual.

## Capacidad implementada

- **Chosen of Chaos ejecuta.** `band--marauder-special-skills-chosen-of-chaos` pasa a
  `implemented: YES`/`scope: YES` con el operador que ya usan sus reglas hermanas de
  Merodeadores (contrato `special-rule.<rule-id>`); `contracts.SPECIAL_RULE_EFFECTS` recoge
  su efecto admitido (vacío) e `implemented-canonical-families.yaml` registra la familia. La
  selección es canónica: `compile_fighter` la acepta.
- **Ambas mitades impresas.** El máximo de campaña queda fuera y la lista de Héroes que la
  frase concede ya es la lista declarada de todos sus destinatarios («si aún no lo hace»), así
  que la selección no añade equipo ni bonos.
- **Great Axe (162).** Sin la capacidad: sin oferta, `equipment_not_permitted` y compilación
  rechazada. Con ella: oferta y compilación positivas. Los dos requisitos impresos gobiernan.
- **Chaos Steed (367).** El requisito de destinatario queda resuelto por la misma capacidad y
  ninguna lista de banda ofrece la montura, así que la construcción no da veredicto de oferta y
  la montura sigue excluida: no se simula compra ni combate montado.
- **Shortsword (187), corrección del coordinador.** La fuente de la banda no contiene
  Knights-only: era un error de extracción del catálogo, no una divergencia impresa.
  Retirada esa restricción, las listas explícitas conservan ofertas y aceptación para
  Damsel, Squires, Battle Pilgrims y Bowmen, sin concederla a los Knights.

## Evidencia mínima

`pytest tests/python/construction/test_t13_construction_recipients.py` → **33 passed**,
EXIT=0 (`%TEMP%/c03a-close/pytest-recipients.txt`): selección de Chosen, hacha positiva y
negativa, montura negativa, y las cuatro líneas de la espada corta con su cláusula.
Discriminadores de enlaces selectables → 17 passed; esquema editorial de los cuatro
documentos tocados, sin problemas.

## Propuesta CSV (sin `apply`)

Tres filas `(id, clause_id = recipient)`: 162, 367 y 187 — `semantic_contract` actualizado,
`pending` vaciado, notas anexadas (las previas se conservan), consumidores y verificación
registrados. El coordinador integró las tres filas con propuesta corregida para 187,
copia completa, conservación de las 4.556 claves/textos/huellas/notas y control concurrente
en `%TEMP%/c03a-final-integration-kbckl3m_`. Reutilizada la evidencia del ejecutor;
el discriminador de Shortsword corregido pasa (1 passed,
`%TEMP%/c03a-close/coordinator-shortsword-source.txt`).

## Bloqueos exactos

Sin pendientes C03a. El coordinador completó también el defecto de combate de Shortsword:
operador propio y mappings corregidos, Parry conservado y +1 a la salvación enemiga
(6+ sin armadura). Dos casos de ataque real frente a espada ordinaria pasan;
salida `%TEMP%/c03a-shortsword-combat-final.txt`. Fila item/shortsword integrada con
conservación y control concurrente en `%TEMP%/c03a-shortsword-fix-xd7mmip7`.
