# C03c — Destinatarios y combinaciones de `equipment-access.yaml`

**Estado: completo**, 49 cláusulas cerradas. Base
inicial: rama `2A2B`, HEAD `a1f92653`, árbol compartido con cambios heredados de
otros escritores.

## Capacidades antes → después

- **Implementación nueva.** El `wolfcloak` de los Mercenarios imprimía
  «Middenheim Heroes only», pero la línea no declaraba destinatario: se ofrecía a
  los seis perfiles que declaran `mercenary-equipment-lists`, incluidos los
  secuaces `warriors` y `swordsmen`, y con cualquier variante de banda. Ahora la
  entrada declara `applies_to {profile_types: [hero], variants: [middenheim]}`:
  la variante publicada de banda es la compuerta conjuntiva y el tipo de perfil
  impreso excluye a los secuaces de la misma lista. Combat Lab transporta la selección por `variant_ids`.
- **Reconciliación integrada (36 filas).** Destinatarios de `profileFacts`:
  héroes, perfiles nombrados, variantes de Casa, listas exclusivas, identidades
  de banda, clarificación `F074-halfling-aliases`, `spirit_knife` para Etéreos,
  exclusión Gobbo Boyz y loadout `weapon.skull-busta`.
- **Cierre del coordinador:** lista especial High Elven accesible a los cinco
  perfiles nativos; Runas Élficas para héroes iniciales y sólo Shadow Weaver con
  `equipment.post-creation`; Hunting Bird exige destinatario y capacidad Falconer
  declarada; Kumfy Gear rechaza Warpaint y armadura ligera, también activa, sólo
  mientras se lleva. Prohibiciones condicionales separadas de las incondicionales
  en todos los consumidores compartidos. Siete dependencias adicionales ya
  funcionaban: Poison Daggers, Pike, Bearcloak, Vow of Poverty y equipo Ogre/Slayer.
  Son conexiones reconciliadas, no siete comportamientos nuevos.

## Archivos propios

Datos de Mercenaries, High Elves, Shadow Warriors, Watchmen y Savage Orcs;
`eligibility/index.ts`, bundle generado y esquema `equipment-access`; referencia
de elegibilidad y casos C03c de construcción. Cambios heredados conservados.

## Comprobación

Evidencia inicial reutilizada: `%TEMP%/c03c-evidence-final.txt`. Cierre: tres casos
de dependencias, acceso High Elven, destinatario por fase, requisito Falconer e
incompatibilidades de Kumfy Gear. Salidas `%TEMP%/c03c-dependency-tests.txt`,
`c03c-elven-list-test.txt`, `c03c-remaining-focused.txt` (Falconer/Runestones pasan)
y `c03c-kumfy-integrated.txt`. Corregidos los datos iniciales del kit de prueba;
el último caso comprueba ambas incompatibilidades y sus controles legales.
Tipos TypeScript, bundle actual y esquemas de las cuatro bandas modificadas
válidos (`%TEMP%/c03c-targeted-schema.txt`). Sin E2E ni baterías globales.

## CSV e integración

37 cierres iniciales en `%TEMP%/c03c-integrated-lwn8x28e`; 12 restantes integrados
con preparación nueva en `%TEMP%/c03c-final-4ndtbo9u`. Snapshot completo previo,
preview, conservación de 4.556 claves/textos/huellas/notas y control concurrente.
Sin pendientes asignados al paquete, commits ni pushes. Este cierre no certifica
las salvaciones propias de Kumfy Gear ni ataques Falconer de otras cláusulas.
