# B04 — Remates de admisión y kits

**Integrado por el coordinador, 2026-10-18.** Tres causas corregidas conservando
los contratos de prueba: admisión legal de Drenok y negativo de equivalencia
incompleta, rechazo de recubrimiento sin arma y arma canónica del Buccaneer.
Resultados focales del ejecutor reutilizados sin repetir pruebas. Sin cambios
al motor, datos o CSV; el registro sigue sin pendientes. Este remate queda
cerrado y no sustituye la comprobación integrada final del bloque 4.

Encargo acotado del bloque 4: corregir las tres causas conocidas de Drenok,
Wulfen/Zombies y Buccaneer, con casos afectados por selector. Sin cambios al CSV
(no se consultó ni escribió), sin E2E, sin suites globales, sin commits.

## Causas y corrección

1. **Drenok — expectativa obsoleta y kit incompatible.**
   `test_a_blocked_equivalence_names_its_own_blocker` seguía esperando
   `intrinsic duel clauses are pending`, pero las reglas del perfil ya están
   implementadas en `grade-1b.yaml`; además pedía `weapon.double-handed-weapon`,
   que el matcher de kit no acepta porque su arma única es el Axe of Icefang.
   Se sustituyó el rechazo artificial por su admisión canónica con
   `weapon.icefang-axe` y `defence.sabertooth-hide`, comprobando que el arma
   conserva su identidad y la clase de dos manos. El propósito negativo se
   mantiene con el Halfling Knight, cuya Cavalry Spear sigue sin mapeo de
   combate canónico y nombra su propio bloqueo. No se retiró ninguna protección
   de admisión.

2. **Wulfen/Zombies — veneno sin arma portadora.**
   La rama `weapons-armour` de
   `test_every_profile_refuses_what_its_printed_line_refuses` esperaba que un
   perfil sin arma compilara con `main_poison_id="poison.black-lotus"`. La línea
   impresa solo prohíbe armas y armadura; el rechazo real lo produce el contrato
   compartido `a poison needs a carried weapon in the hand it coats` (los siete
   perfiles de esa rama luchan con `weapon.natural-attacks`). La expectativa
   ahora afirma ese rechazo compartido, sin inventar una prohibición de venenos
   ni permitir recubrimientos sobre puños. Corregidas las siete
   parametrizaciones `weapons-armour` afectadas por la misma causa.

3. **Buccaneer — arma fuera de la lista canónica.**
   Los dos casos compilaban `shallows-beasts-mim/buccaneer` con `weapon.mace`.
   La lista impresa de héroes ofrece una única entrada `club` (nota
   «Club/Mace/Staff») cuyo `mechanic_id` canónico es `weapon.club`; el dato es
   correcto y `weapon.mace` es un arma distinta que Cold Steel necesita
   distinguir. Se corrigió el arma elegida por los casos a `weapon.club`, sin
   ampliar el acceso al catálogo ni tocar el perfil canónico. Las comprobaciones
   de Electrical Touch y Eye Stalks quedan intactas.

## Archivos propios

- `tests/python/construction/test_t13_hireling_admission.py`
- `tests/python/construction/test_c01b_intrinsic_profile_declarations.py`
- `tests/python/combat/modular/test_t13_residual_lifecycle.py`
- este documento

Base exacta previa de los tres archivos conservada fuera del repositorio en
`/tmp/b04/base/`; primeras salidas en `/tmp/b04/initial*.txt`.

## Casos ejecutados (una ejecución por selector)

| Selector | Resultado |
|---|---|
| `test_t13_hireling_admission.py::test_a_blocked_equivalence_names_its_own_blocker` | 1 passed |
| `test_c01b...::test_every_profile_refuses_what_its_printed_line_refuses -k weapons-armour` | 7 passed, 14 deselected |
| `test_t13_residual_lifecycle.py::test_electrical_canonical_shallows_mutation_uses_s3_not_hero_strength_or_armour` + `::test_canonical_aquatic_mutants_eye_stalks_reaver_sends_the_fear_consequence` | 2 passed |
| `test_c01b...::test_the_sting_applies_black_lotus_without_equipping_it` (control de veneno intrínseco) | 1 passed |
| `test_c01b...::test_a_profile_with_printed_access_keeps_its_purchased_poison` (control de veneno legal sobre arma) | 1 passed |

Salidas finales en `/tmp/b04/final-*.txt` (EXIT=0 en las cinco). El veneno legal
sobre arma y el veneno intrínseco del Tomb Scorpion se reutilizan sin cambios de
motor.

## Bloqueos

Ninguno dentro del alcance. La validación integrada conjunta del bloque 4 queda
para su gate posterior; E2E sigue completamente excluido.
