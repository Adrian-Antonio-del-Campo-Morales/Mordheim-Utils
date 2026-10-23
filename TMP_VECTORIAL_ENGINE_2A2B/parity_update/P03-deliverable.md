# P03 — Batería estadística conectada (quick, complete y deep)

## Alcance entregado

La batería compara **muestras de duelos reales** del oráculo modular y de cada
candidato por sus resultados terminales. El catálogo, los perfiles, el
comparador y el informe de P03 se conservan y se completan: no se reinicia
inventario, catálogo, corpus ni validación del modular.

Retirado del camino estadístico: testigos tipados, `expect`/`positive_control`,
`witness_value`, contadores, banderas, hashes y checkpoints. Se conservan como
datos de declaración, sin bloquear ni aprobar un caso. Los pares con/sin regla
siguen siendo escenarios normales de duelo.

Los tres perfiles quedan revisados y conectados. `quick` ⊆ `complete` ⊆ `deep`
se mantiene por id de caso y la cobertura de variantes de duelo es completa
(60/60 en `complete`). Ninguna tolerancia se cambió: la puerta sigue siendo
`_statistical.six_sigma_tolerance` (6σ, suelo 0,25 %).

## Correcciones realizadas

| Archivo | Caso / área | Corrección |
| --- | --- | --- |
| `_battery_cases.py` | catálogo completo | Retiradas 103 declaraciones `blocked_by="witness:…"`. Un testigo no es una entrada: no limita, no bloquea y no se contaba como límite. `input_limit` solo conserva `state:`/`decision:` y el guion per-row. |
| `_battery_cases.py` | `c05-bear-hug` | La preparación genérica con `weapon.fist` + reglas sueltas se sustituye por el **perfil Domnu** con `weapon.fist`. El perfil compila `mechanic.bear-hug` y `rule.bear-hug-unarmed`, y la puerta del pool exige dos impactos desarmados; las claves `round.0/1.first.bear-hug` son las que consume `pools.resolve_attacks`. |
| `_battery_cases.py` | `v14-handler`, `v14-handler-absent` | Primero se pasó al receptor canónico del Oso adiestrado, pero esa rama queda inalcanzable (`bear-handler-recipient` exime la estupidez a 6" —la única prueba del Oso— y su miedo no se prueba porque el Oso lo causa). La revisión posterior de `modular/leadership.py:170-203` mostró una **segunda rama canónica del mismo consumidor**: `squig_recipient` se identifica por `fighter_id == "night-goblins-web:cave-squigs"`, acepta al `squig-herder` con `mechanic.handler-leadership` de la misma banda a 6" (12" con pinchador) y presta su Ld a *cualquier* prueba de Liderazgo. La variante se prepara ahora con **Squigs de Cueva + Squig Herder** (Ld 6) y estupidez suministrada para que la prueba exista; el control deja al pastor a 8". `vectorized/_leadership.py:346-366` implementa la misma rama. La incompatibilidad desaparece y no se sustituye por otra regla. |
| `_battery_cases.py` | `c00-amazon-isolationists` | El defensor era otra amazona, pero `contexts.py` activa la repetición solo contra `band.lizardmen*`/norse (`amazon_enemy`). Se sustituye por `saurus-braves` de la banda `lizardmen`, que es el enemigo que nombra el origen E2E. |
| `_battery_cases.py` | `c09-beastlash-fear` | El látigo de bestias solo causa miedo a un animal (`species.animal`), y el defensor genérico no lo era. Se usa la jauría canónica `warhounds` (regla `--animals`), que además no causa miedo, de modo que la prueba de miedo cargada sí se toma. |
| `_battery_cases.py` | `v15-torturer` | Retirada la decisión `round.0.first.torturer-grapple`: su consumidor real es `aftermath._react_to_wound` (pérdida de Fuerza reactiva a una herida no salvada en close combat) y no pide decisión. El agarre pertenece a `mechanic.gaoler-grapple`, otra regla. |
| `_battery_cases.py` | `d05-spines-injury` | Renombrado desde `d05-spines-regeneration`: la composición es espinas + varias heridas en la misma fase (B15.4 + lesión); no incluye regeneración. |
| `_battery_cases.py` | `v01-restriction` | El duelo declaraba al portador de `mechanic.shallya-strictures` sin carga, así que la restricción nunca se ejercía. La única expresión real es una carga rechazada: `build_duel_state` lanza `ValueError` antes de muestrear. Se conserva `INCOMPATIBLE` (`state:mechanic.shallya-strictures`) y no se sustituye por un duelo normal. |
| `_battery_cases.py` | `c03-petru-potion` | La preparación con raíz de mandrágora se retira: declaraba como build otra poción. La causa real es que `petru--potions` está `implemented: NO` en la KB (reparto pre-batalla con persistencia de campaña). El caso permanece `INCOMPATIBLE` con `state:preparation.strength-draught` y no materializa un sustituto. |
| `_battery_cases.py` | `q00-honorable` | Reordenado y preparado con las APIs actuales: el portador de la maza es el **segundo** participante y el objetivo el primero. La maza derriba/aturde en la ronda 0 (`concussion: 2-4`) y la ronda 1 es el turno del portador, mientras el objetivo aún no ha tenido su recuperación; `pools.resolve_attacks` evalúa `mechanic.honorable` al construir el pool y no ataca. El derribo se produce dentro del duelo: no se inyecta estado inicial y el caso deja de ser incompatible. Sin la regla ese mismo estado se resolvía como fuera de combate automático, así que la diferencia es material. |
| `_battery_cases.py` | notas `q11-black-hunger`, `v08-base-pool`, `v09-netted` | Retiradas tres frases que aún describían prerrequisitos del camino por testigo (`falta observación por evento`, `attack-count pendiente`, `init de estado pendiente`). El retroceso de Hambre Negra lo resuelve `aftermath._black_hunger` sin decisión, el reparto por mano lo hace el motor antes del pool y `condition.netted` inicializa al portador como derribado en ambos motores (`state.py`, `_state.py`). Las notas describen ahora el escenario estadístico real. |
| `_battery_runner.py` | resultado malformado | Cada motor valida su propia convención antes de normalizar (oráculo `0/1/2`, candidato `1/-1/0`). Un código desconocido, un dtype no entero o un `bool` lanzan `OutcomeCodeError` y el caso queda `NOT_RUN:outcome-codes` (error propio). Nunca se convierte en «sin resolver» ni se descarta de la muestra. |
| `_statistical.py` | resultado malformado | `outcome_counts` rechaza códigos fuera de `0/1/2` y valores no enteros; la tolerancia compartida no cambia. |
| `_statistical.py` | booleanos NumPy | `isinstance(value, bool)` no cubre `numpy.bool_` y `int(True) == 1`, así que recorrer `np.array([True, False])` contaba 1/0 como ganadores. El guardián rechaza ahora también el dtype booleano (`getattr(getattr(value, "dtype", None), "kind", None) == "b"`) antes de convertir, sin importar NumPy en este módulo ni tocar los códigos válidos (`np.int64` sigue aceptado) ni las tolerancias. |
| `tests/python/verification/test_parity_battery_cases.py` | comprobantes | Ajustados a que el catálogo ya no declara bloqueos de testigo y a que los únicos `blocked_by` reales son `c03-petru-potion` y `v01-restriction`. |
| `tests/python/verification/test_parity.py` | marcadores de secuencia | Ocho pruebas de la batería (payload, excepción previa a la observación, códigos de ganador malformados y CLI) no declaraban categoría. `tools/verification/test_sequence.py` exige exactamente una por ítem y aborta la colección completa con `UsageError`, así que ni el archivo ni el resto de la sesión se podían ejecutar. Se les asigna `evidence`, la misma categoría que sus vecinas del bloque de certificado. |
| `docs/reference/verification.md`, `TODO.md` | documentación | Actualizados al estado real: 122 casos revisados, tres límites declarados (cuatro casos), composiciones de `deep` y recuentos exclusivos/acumulados. |

No se tocaron motores modular/vectorial/nativo, modelos compartidos, planes del
motor, KB, CSV canónico ni corpus E2E. No hay sondas, estado inicial ni
interfaces nuevas.

## Disposición de los 122 casos

Todos los casos se revisaron por lectura estática de catálogo → preparación →
compilador → consumidores de motores → comparación → informe. `P` = preparado
según lectura estática; `I` = incompatible por una limitación real.

| Variante | Casos | Disp. |
| --- | --- | --- |
| B01.1 | `v01-profile` | P |
| B01.2 | `v01-force-of-will`, `v01-force-of-will-absent`, `d08-force-of-will` | P |
| B01.3 | `c03-petru-potion` | **I**: `petru--potions` es campaña pre-batalla (`implemented: NO`); falta el brebaje de Fuerza, no hay preparación equivalente |
| B01.5 | `v01-restriction` | **I**: la cláusula solo se ejerce con una carga que `build_duel_state` rechaza antes de muestrear; sin carga no hay restricción que medir |
| B01.6 | `v01-random` | P |
| B02.2 | `v02-hatred`, `v02-hatred-absent` | P |
| B02.3 | `c00-amazon-isolationists`, `v02-hit-reroll`, `v02-hit-reroll-absent` | P |
| B02.4 | `v02-general-hit`, `v02-general-absent` | P |
| B03.2 | `v03-poison`, `v03-poison-immune` | P |
| B03.3 | `v03-strength`, `v03-strength-absent` | P |
| B03.4 | `v03-wound-reroll`, `v03-wound-reroll-absent` | P |
| B03.5 | `q05-flammable-fire`, `c03-flammable-absent` | P |
| B04.1 | `q06-intrinsic-save` | P |
| B04.2 | `q04-natural-armour-six`, `c04-hide-combines` | P |
| B04.3 | `v04-buckler-armour`, `d04-armour-parry` | P |
| B05.1 | `c05-ethereal-save`, `c05-ethereal-improved`, `c05-ethereal-bypass` | P |
| B05.2 | `v05-regeneration`, `v05-regeneration-blocked` | P |
| B06.1 | `q04-parry-attempt`, `q04-parry-absent` | P |
| B06.2 | `c04-parry-reroll`, `c06-two-swords-one-attempt`, `c06-two-parries`, `c06-two-swords-capacity`, `c06-reroll-capacity`, `d04-long-horizon` | P |
| B06.3 | `v06-parry-denial` | P |
| B07.1 | `q04-injury-chart`, `c04-hard-head`, `c04-hard-to-kill`, `c04-thick-skull`, `c05-poltergeist-immediate-out` | P |
| B07.2 | `c04-highest-injury` | P |
| B07.3 | `v07-weapon-injury` | P |
| B08.1 | `v08-base-pool` | P |
| B08.2 | `v08-extra-attack`, `d08-frenzy-parry` | P |
| B08.4 | `v08-unarmed`, `v08-ordinary-fist` | P |
| B08.5 | `c05-bear-hug` | P |
| B09.2 | `v09-transform` | P |
| B09.3 | `v09-netted`, `v09-netted-absent` | P |
| B10.1 | `v10-priority`, `d10-order-attacks` | P |
| B10.2 | `c04-stand-up-last` | P |
| B10.3 | `q08-death-blow-optional`, `c08-death-blow-decline` | P |
| B10.4 | `q00-honorable`, `v10-round-state` | P |
| B11.1 | `q09-fear-charged`, `c09-troll-fear`, `c09-beastlash-fear`, `d09-fear-charge-parry` | P |
| B11.2 | `v11-immunity`, `v11-immunity-absent` | P |
| B11.3 | `v11-psych-immunity`, `v11-psych-absent` | P |
| B11.4 | `v11-conditional-immunity`, `v11-conditional-absent` | P |
| B11.5 | `v11-cold-blood`, `v11-cold-blood-absent` | P |
| B11.6 | `c00-questing-vow`, `c00-questing-vow-absent` | P |
| B11.7 | `c11-great-thirster` | P |
| B12.1 | `v12-stupidity`, `v12-stupidity-exempt` | P |
| B14.1 | `q10-leader-six`, `c10-leader-absence`, `c10-leader-swapped`, `d10-leader-retest` | P |
| B14.2 | `v14-leader-twelve`, `v14-leader-thirteen` | P |
| B14.3 | `v14-auto`, `v14-auto-absent` | P |
| B14.4 | `v14-own`, `v14-own-absent` | P |
| B14.5 | `v14-handler`, `v14-handler-absent` | P: receptor `cave-squigs` (rama de identidad del consumidor) y proveedor `squig-herder` a 6"/8"; el préstamo se mide con la estupidez suministrada del Squig, no con la regla del Bear Tamer |
| B14.6 | `v14-mob`, `v14-mob-absent` | P |
| B14.7 | `v14-brood`, `v14-brood-absent` | P |
| B14.8 | `v14-cold-blood`, `v14-cold-blood-absent` | P |
| B14.9 | `v14-reroll`, `v14-reroll-absent` | P |
| B14.10 | `v14-relay`, `v14-relay-absent` | P |
| B14.11 | `v14-relic-first`, `v14-relic-second` | P |
| B14.12 | `v14-slave`, `v14-slave-absent` | P |
| B14.13 | `v14-modifiers`, `v14-modifiers-absent` | P |
| B15.1 | `q11-black-hunger`, `c15-hunger-absent` | P |
| B15.2 | `c11-curse-of-revenant` | P |
| B15.3 | `v15-monstrous` | P |
| B15.4 | `c11-acid-blood`, `c11-acid-blood-absent`, `c11-spines`, `c11-spines-absent`, `d05-spines-injury` | P |
| B15.5 | `v15-contagious`, `v15-contagious-absent` | P |
| B15.6 | `v15-torturer`, `v15-torturer-absent` | P |

B00.1, B09.1 y B99.1 son referencias estructurales o sin consumidor decisivo y
no se acreditan con un duelo genérico; quedan fuera de la cobertura de duelo.

### Recuentos

| Perfil | Exclusivos | Acumulados | Preparados (acum.) | Incompatibles (acum.) |
| --- | --- | --- | --- | --- |
| `quick` | 11 | 11 | 11 | 0 |
| `complete` | 103 | 114 | 112 | 2 |
| `deep` | 8 | 122 | 120 | 2 |

Son recuentos de **preparación estática**, no de ejecución. Los dos casos
incompatibles son `c03-petru-potion` (mecánica de campaña) y `v01-restriction`
(entrada rechazada en construcción); siguen en el denominador de `complete` y
`deep`. La rama del handler ya no es un límite: `v14-handler` y
`v14-handler-absent` se preparan por la regla canónica de Squigs.
La preparación está revisada por lectura —catálogo → compilador → consumidores de
motor → comparador → informe— pero **no validada por ejecución**: no hay muestras,
ni `PASS`, ni aceptación de ninguno de los tres perfiles.

### Composiciones de `deep`

Las ocho composiciones reutilizan material ya justificado y cubren los huecos
del plan: miedo → carga → parada (`d09-fear-charge-parry`), liderazgo →
psicología (`d10-leader-retest`), ataques adicionales → capacidad defensiva
(`d08-frenzy-parry`), armadura → parada (`d04-armour-parry`), orden → ataques
(`d10-order-attacks`), reacciones → lesión (`d05-spines-injury`), recurso
único → recuperación (`d08-force-of-will`) y horizonte largo de desgaste
(`d04-long-horizon`). No se añadieron combinaciones exhaustivas ni variantes
nuevas.

## Validación de resultados malformados

- Oráculo: solo `0/1/2`; candidato: solo `1/-1/0`. La normalización ocurre
  después de validar, nunca antes.
- `np.unique` sobre los códigos fuera de convención produce el detalle
  `NOT_RUN:outcome-codes: <motor> winner code(s) [...] outside [...]`.
- El caso no suma a `executed`, `compared` ni `approved`; el CLI sale con 1 por
  ser error propio, sin `--require-complete`.
- `rounds`, `wounds` y `condition` se comparan como distribuciones discretas con
  la misma tolerancia; ambos motores publican enteros con el mismo significado
  (`resolution_rounds`/`rounds`, heridas y códigos de condición).

## Revisión estática de la conexión

1. **Catálogo → preparación**: todos los `band`/`profile` usados existen en la
   KB; los ids con prefijo (`weapon.*`, `skill.*`, `mechanic.*`, `defence.*`,
   `armour.*`, `condition.*`, `poison.*`, `preparation.*`) resuelven a entradas
   del catálogo; los `requires` son subconjunto de los ids declarados en el
   build y en los proveedores del contexto.
1b. **Orden de turnos**: `DuelState.first_player_turn` alterna y solo el combatiente del turno activo recupera (`_start_round_state(..., recover=...)`). `q00-honorable` depende de ese orden para que la guarda vea al oponente derribado en la entrada del pool; `c04-stand-up-last` y `v14-relic-second` usan el mismo reloj.
2. **Decisiones → consumidores**: `round.{r}.{side}.stupidity.{leader|handler|relay}.{id}`
   y `.reroll` coinciden con `leadership.resolve_local_leadership`;
   `round.{r}.{side}.fear.{charge|charged}…` con `psychology.resolve_fear`;
   `round.{r}.{side}.death-blow` con `rounds.select_attack_replacement`;
   `round.{r}.{side}.attack.{i}.lotus-critical` con `attacks`; y
   `round.{r}.{side}.bear-hug` con la puerta de `pools`. No queda ninguna clave
   sin consumidor.
3. **Preparación → motores**: `resolve_context` compila los proveedores a
   `LocalParticipant`; `compile_fighter` resuelve condiciones suministradas
   (`condition.netted`, `condition.stupidity-exempt`) y rasgos tipados
   (`mob_allies`, `stupidity_leadership_bonus`, `injury_profile`, `spines`,
   `acid_blood`, `contagious`, `causes_fear`, `frenzy`). El marcador del Domnu y
   el `mechanic.bear-handler` del Bear Tamer son grants de perfil.
4. **Motores → comparación**: ambos caminos reciben las mismas filas, semilla,
   horizonte, contexto y decisiones; se comprueba forma y determinismo antes de
   comparar y después se aplican las magnitudes declaradas.
5. **Comparación → informe**: `BatteryCaseResult` conserva etapas, magnitudes,
   tasas y tolerancias; `battery_report_payload` deriva `prepared` de
   `blocked_by`, conserva `limits` y mantiene `sensitivity: pending`; el CLI y el
   informe comparten `battery_failure_kind`.

## Comprobantes escritos (no ejecutados)

- `test_parity_battery_cases.py`: el catálogo no declara bloqueos de testigo;
  `input_limit` sigue ignorando `witness:`/`consume:` y solo retiene
  `state:`/`decision:`/per-row; los casos bloqueados son `c03-petru-potion` y
  `v01-restriction`.
- `test_parity_battery_runner.py`: convenciones de ganador y
  `NOT_RUN:outcome-codes`; tolerancia compartida; guardas de forma y
  determinismo; `combine_reports`. `test_outcome_counts_uses_the_oracle_codes`
  ya exigía rechazar `np.array([True, False])`, que ahora cubre el dtype
  booleano de NumPy; no hizo falta una prueba nueva.
- `test_parity.py`: cobertura, magnitudes, límites, agrupación de dependencias,
  claves por cláusula, backends separados y salida de la CLI; las 30 pruebas
  declaran ahora una única categoría (`phase5_vectorized` o `evidence`).

No se ejecutaron tests, motores, campañas, importaciones de validación,
`py_compile` ni compilaciones. La revisión es lectura estática: no hay PASS, ni
muestras, ni aceptación.

## Comandos propuestos (ejecución posterior)

### Workers en los perfiles

`--workers N|auto` está conectado al muestreo modular de `quick`, `complete` y
`deep`. Reutiliza `chunk_ranges` y `resolve_oracle_workers`: cada bloque recibe
`seed + inicio` y los resultados terminales se reúnen en el orden original. Un
pool de procesos se reutiliza entre casos de un backend; la muestra modular
conserva su reutilización entre candidatos. Los lotes NumPy/nativo no cambian.
`1` es secuencial, los números explícitos se limitan a las CPUs disponibles y
`auto` aplica el umbral histórico de coste. El JSON incluye la política solicitada
en `oracle_workers_requested`, sin presentarla como número efectivo por caso.

Se añadieron dos comprobantes sintéticos de rangos/filas y reutilización del
pool, escritos y **no ejecutados**. No se ejecutaron tests, motores,
importaciones de validación ni compilaciones para este cambio. No se modificó
ningún motor. Ejemplo para ejecución posterior:

```powershell
python -X utf8 tools/mordheim-utils.py parity --profile quick --backend numpy --rows 1000 --workers 10 --output outputs/parity/battery-quick-1000.json
```

```bash
# quick: 11 casos preparados, 0 incompatibles esperados
python -X utf8 tools/mordheim-utils.py parity --profile quick \
  --output outputs/parity/battery-quick.json

# complete: 114 declarados, 112 preparados, 2 incompatibilidades esperadas
python -X utf8 tools/mordheim-utils.py parity --profile complete --backend all \
  --output outputs/parity/battery-complete.json

# deep: 122 declarados, 120 preparados; certificado markdown y puerta estricta
python -X utf8 tools/mordheim-utils.py parity --profile deep --backend all \
  --output outputs/parity/battery-deep.md --require-complete

# calibración de muestreo, nunca aceptación
python -X utf8 tools/mordheim-utils.py parity --profile quick --rows 256 \
  --output outputs/parity/battery-quick-256.json
```

`complete` y `deep` seguirán siendo parciales mientras `c03-petru-potion` y
`v01-restriction` conserven sus limitaciones;
`--require-complete` debe fallar por esas dependencias, no por un defecto de
preparación. Cualquier `NOT_RUN:decision-script`,
`NOT_RUN:compile` o `NOT_RUN:outcome-codes` sería un defecto propio a corregir.

## Límites conservados

- `c03-petru-potion` requiere una capacidad de campaña que la KB declara fuera
  de alcance; corregirla exige cambios de KB/motor y no amplía este encargo.
- `v01-restriction` no es preparable como comparación: la carga restringida es
  una entrada rechazada antes de muestrear y un duelo sin carga no ejerce la
  cláusula.
- `v14-handler`/`v14-handler-absent` sí son preparables y se preparan: la rama
  de Squigs de `leadership.py` usa el mismo consumidor con receptor canónico
  `cave-squigs` y proveedor `squig-herder`. No se usó la rama del Oso porque en
  ella la exención de estupidez y el miedo compartido dejan el préstamo sin
  prueba que medir.
- La sensibilidad con/sin regla sigue `pending`: la paridad estadística compara
  distribuciones, no demuestra que la regla las cambie. La medición corresponde
  a P04.
- No se declara que los escenarios funcionen por ejecución ni que todas las
  variantes estén estadísticamente comprobadas.

## Ejecución `battery-complete-10000` (114 casos): causas, correcciones y disposición

Evidencia de la ejecución recibida: 41 PASS, 33 diferencias estadísticas, 4
excepciones, 25 rechazos de admisión, 4 incompatibilidades declaradas y 7
errores de preparación/decisiones. Las correcciones de esta sección se aplicaron
por lectura de contratos y consumidores; **no se ejecutó** nada después de
aplicarlas. Los dos informes de la campaña (`outputs/parity/battery-quick-10000.json`
y `outputs/parity/battery-complete-10000.json`) no se han sobrescrito: siguen
siendo la evidencia de la ejecución recibida, con sus recuentos originales.

### Tabla por causa compartida

| Casos afectados | Causa (referencias) | Corrección aplicada | Defecto de motor o incertidumbre | Comprobante ajustado | Comprobación posterior |
| --- | --- | --- | --- | --- | --- |
| `q10-leader-six`, `c10-leader-absence`, `c10-leader-swapped` (+ `v14-leader-twelve`, `v14-leader-thirteen`) | La entrada suministraba `mechanic.leader-six` como *skill* de `serpent-priestess`, que su `skill_access` rechaza. El grant canónico es `serpent-priestess--leader` (`sources/knowledge/bands/mordheim/amazons-lustria/special-rules.yaml:4-20`, `grant: profile`, efecto `mechanic.leader-six`). | `_leader_context` ya no inyecta el mechanic: compila el perfil canónico y deja que el grant lo materialice. `v14-leader-twelve/thirteen` usan `senior-gunnery-officer` (grant `--leader`: `leader-six` + `leader-twelve`). | Ninguno del motor. El liderazgo del escenario se conserva y no se relaja la validación del compilador. | `test_parity_battery_cases` (ids y `requires` materializados). | Reejecutar `quick`/`complete`: los cinco deben compilar y comparar, no `NOT_RUN:compile`. |
| `c09-beastlash-fear`, `v14-relay`, `v14-relay-absent` | La ejecución exigía declarar la casa: `modular/contexts.py:205-209` y `vectorized/_operators.py:625-631` solo aceptan `mechanic.dueling-pride` con una etiqueta `house-guard.*`. El compilador la produce desde `house_guard_house` (`compiler.py:1167-1173`, valores `fierezza|halcon|baluardo`). | Se declara `traits={"house_guard_house": "fierezza"}` en los tres casos (y en sus proveedores de contexto). No se cambia el perfil ni el propósito. | Ninguno: era preparación incompleta. | `requires` incluye `house_guard_house` (clave de trait admitida por `_build_ids`). | Reejecutar: deben pasar de excepción a comparación. |
| `v14-handler`, `v14-handler-absent` | La incompatibilidad declarada suponía que el Oso era el único receptor del consumidor. `modular/leadership.py:170-203` tiene una rama propia de Squigs: receptor por identidad (`night-goblins-web:cave-squigs`), proveedor `squig-herder` con `mechanic.handler-leadership` de la misma banda a 6" (12" con pinchador), y el valor prestado se usa en cualquier prueba de Liderazgo. `vectorized/_leadership.py:346-366` replica la rama. | Se preparan con `cave-squigs` (Ld 5) + `squig-herder` (Ld 6) a 6" y a 8", con estupidez suministrada en el receptor para que la prueba exista y `round.0.first.stupidity.handler.leader`. No se usa la regla del Bear Tamer ni se sustituye por otro escenario. | Ninguno del motor: misma rama en ambos. Incertidumbre: el Squig canónico no trae estupidez impresa (`combat_traits: {}`), así que el caso declara el estado suministrado, igual que el resto de la familia B14. | `requires` = `cave-squigs`, `squig-herder`, `stupidity`; sin `blocked_by`. | Reejecutar: el positivo debe prestar 6 y el control probar 5; si divergen, la causa está en `leadership.py` frente a `_leadership.py`. |
| `c11-curse-of-revenant` | La entrada de la ejecución no declaraba el prerrequisito canónico. La guarda `compiler.py:1097-1099` exige `mechanic.great-thirster` en `global_effects.tags`, y ese tag sí llega desde `build.skill_ids`: el id entra en `selected` (`compiler.py:653`), pasa a `global_ids` (`:782-789`) y `apply_execution_effects(..., "passive", "fighter")` lo publica porque su efecto es `trigger: passive` (`catalog/mechanics/execution.yaml:2357-2363`). El par canónico E2E declara exactamente ambas habilidades (`tests/E2E/.../mechanic.curse-of-the-revenant.yaml:110-112`). | El caso declara ahora `skills=("mechanic.great-thirster", "mechanic.curse-of-the-revenant")` (`_battery_cases.py:1023-1027`) y conserva la regla y su prerrequisito. | **Ninguno del motor ni del compilador.** La atribución anterior a un «defecto del compilador» queda retirada: no hay evidencia de que la puerta lea una etapa equivocada. | `test_parity_battery_cases` (ids y `requires` del caso). | Reejecutar: debe compilar y comparar; si volviera a lanzar esa guarda, entonces sí habría que revisar la proyección del tag. |
| `v03-poison` | El camino vectorial pregunta el crítico del Loto Negro con la clave que recibe `_resolve_weapon` (`vectorized/_attacks.py:605`, `f"{key}.lotus-critical"`), que en este escenario es la clave por defecto `test` y no la de ronda/ataque que declara el catálogo. El modular compone la misma clave desde su `key` (`modular/attacks.py:556`). | Se declara `test.lotus-critical: False` además de las claves por ronda: mismo rechazo, distinta clave. No se cambia la regla ni se elimina la decisión. | Límite de motor (la clave no viaja hasta esa llamada), no causa del caso; no se corrige aquí. | — | Reejecutar `complete`: debe comparar en lugar de `NOT_RUN:decision-script`. |
| 21 casos `Local modifier variants…` + 4 `Residual modular effects…` (`q00-honorable`, `q05-flammable-fire`, `q06-intrinsic-save`, `c00-amazon-isolationists`, `c00-questing-vow`, `c05-ethereal-save/improved/bypass`, `v01-profile`, `v02-hatred*`, `v11-psych-immunity`, `v11-conditional-immunity`, `v11-cold-blood`, `v14-auto`, `v14-brood`, `v14-cold-blood`, `v14-reroll`, `v14-relic-first/second`, `v15-torturer`; los cuatro residuales son `v01-random`, `v14-own`, `v14-mob`, `v14-mob-absent`) | La batería llama al punto de entrada correcto: `_battery_runner._candidate_sample` → `simulate_batch_observed` con `backend="numpy"` implícito (`_battery_runner.py:145-155`; firma en `vectorized/_driver.py:1640-1646`). Ese camino llama `require_optimized_support(..., backend="numpy")` en `_driver.py:761-767`, y la puerta NumPy resta solo `NUMPY_CONNECTED_TAGS` de la instantánea (`kernel.py:122-182`, `:216-220`), lanzando en `kernel.py:257-266`. | El runner clasifica ahora el rechazo como `INCOMPATIBLE:admission` y nombra las etiquetas concretas (`_battery_runner.py:586-604` + `_admission_tags`), en lugar de llamarlo `construction`. No se elimina ninguna guarda ni se fuerza soporte. | **Defecto de motor/portado**: capacidad no portada a NumPy, no un error de la batería. El rechazo es correcto y permanece dentro del denominador. | — | Reejecutar `complete`: el detalle debe citar las etiquetas; el número de rechazos solo baja cuando el portado las conecte. |
| `v09-netted` (winner/wounds/condition) | **Defecto del motor demostrado.** El modular libera a la víctima de la red y **la levanta en esa misma recuperación**: `rounds.py:552-565` fija `condition=KNOCKED_DOWN` y añade `freed_from_net`, y `aftermath._start_round_state(..., recover=<turno propio>)` levanta cualquier `KNOCKED_DOWN` (`aftermath.py:125-134`). El vectorial excluye explícitamente esas filas: `_driver.py:863-876` calcula `stood2` con `~netted2`. | Ninguna: la comparación es correcta (mismo contexto `_charging()`, horizonte 2, mismo participante). | Resultado observado coherente: `condition[second]` modular 45,6 % de pie frente a 0 % del candidato; `winner[first]` 52,1 % → 75,1 %. Registrado en `TODO.md`. | — | Comprobar con una fila de red que el candidato quede derribado al liberarse: `_state.netted` + `_driver` 863-876 frente a `rounds.py` 552-565. |
| Cola de heridas: `q04-parry-attempt`, `q04-parry-absent`, `c04-parry-reroll`, `c04-stand-up-last`, `c04-highest-injury`, `c04-hard-head`, `c04-hard-to-kill`, `c06-two-swords-one-attempt`, `c08-death-blow-decline`, `c11-great-thirster`, `v02-hit-reroll`, `v02-general-hit/absent`, `v03-strength*`, `v03-wound-reroll`, `v06-parry-denial`, `v08-base-pool`, `v08-extra-attack`, `v09-transform`, `v09-netted-absent`, `v10-round-state`, `v12-stupidity*`, `v14-brood-absent` | Las heridas se comparan con el mismo campo y el mismo significado: ambos productores publican las heridas restantes (`modular/duel.py:97-101`; `vectorized/_driver.py:1620`) y ninguno usa `-1` como centinela de fuera de combate —ese estado solo vive en `condition`—, así que los negativos son sobre-daño real y las categorías se ordenan igual (`_battery_runner._distribution` 266-293). La asimetría de código está en el tramo indefenso: el modular devuelve `OUT` con `damage=1` **sin tocar las heridas** (`modular/attacks.py:741-747`), mientras el vectorial marca `OUT` y además resta el daño completo sobre esas mismas filas (`vectorized/_attacks.py:757-764` + `:776-786`). El corrimiento de masa lo confirma sin ejecutar: en `c06-two-swords-one-attempt` (3 heridas) el modular deja 14,2 % de filas en heridas negativas y 37,5 % en `1`, el candidato 19,8 % y 31,6 %; en `v10-round-state`, 11,0 % → 16,8 % negativas con `1` 34,5 % → 28,2 %. `q04`/`c04`/`v02`/`v12` muestran la misma forma (más masa en `-1`, menos en los cubos altos). | **No se normaliza.** Recortar los negativos o quitar `wounds` ocultaría la diferencia; el contrato y los productores no demuestran equivalencia entre «1 de sobre-daño» y «3 de sobre-daño». | Defecto del motor (vectorial) en el tramo indefenso; la atribución caso por caso exige ejecución. | — | Comprobar en ejecución que las filas añadidas en los cubos negativos son exactamente las `helpless` y que `condition`/`winner` ya coincidían. |
| `c09-troll-fear` (solo heridas del receptor) | Ganador y **ambas** condiciones son idénticas (el segundo tiene una sola categoría), y las heridas del atacante cargado coinciden dentro de tolerancia; solo cambia el cubo *intacto* del Troll: 99,58 % modular frente a 92,33 % candidato. El Troll recibe el ataque de un combatiente que acaba de ser cargado y ha de tomar la prueba de Miedo (perfil `black-orcs/troll`, regla `troll--fear`), y el Troll lleva `skill.regeneration` (`special-rules.yaml:434-461`). | Ninguna: el escenario reproduce la cara opuesta del miedo con el perfil canónico y horizonte 1. | Incertidumbre acotada, **no atribuida**: dos mecanismos del motor pueden producir esta forma sin cambiar condición ni ganador —la máscara de «impacta solo con 6» (`vectorized/_psychology.py:430,446` → `_driver.py:1038-1039` → `_operators.py:910-913`, frente a `modular/attacks.py:208`) y la etapa de salvación/regeneración (`modular/attacks.py:718-758` frente a `vectorized/_attacks.py:745-764`)— y la lectura no los separa. | — | Una fila con dados declarados (impacto, herida y salvación de regeneración) decide entre ambas: si el impacto del cargado ocurre con menos de 6, la causa es la máscara de Miedo. |
| `q11-black-hunger` (winner, heridas y condición) | Retroceso resuelto con un conjunto de filas obsoleto. El modular resuelve un impacto cada vez sobre el estado ya actualizado y **corta** en cuanto el portador deja de estar activo (`modular/aftermath.py:243-258`), y nunca rescata. El vectorial calcula `active = rows[condition != OUT]` **una sola vez** antes de los tres grupos (`_driver.py:711-722`), no vuelve a filtrar tras cada impacto, y además llama `_rescue_force_of_will` dentro del retroceso (`:722`). | Ninguna: perfiles, contexto, decisiones y horizonte ya coinciden; la preparación es la del E2E de Hambre Negra. | Defecto del motor (vectorial) **y causa suficiente** del cambio de ganador: `condition[first]` de pie 52,9 % → 23,1 % y fuera de combate 36,1 % → 52,0 %, misma dirección y orden que `winner[second]` 35,7 % → 51,1 %. El reparto exacto entre «sin re-filtrado» y «rescate dentro del retroceso» exige ejecución. | — | Reproducción de un retroceso con `round.0.first.black-hunger.hits` fijado: el candidato debe dejar de resolver impactos sobre una fila ya fuera de combate. |
| `v14-own-absent`, `v14-slave`, `v14-slave-absent`, `v14-modifiers`, `v14-modifiers-absent` (winner) | **La carga inicial cancelada no cancela el contacto en el vectorial.** El modular, al fallar la Estupidez en la ronda 0 con carga declarada, borra la carga y recalcula `engaged = state.engaged and any(charges)` (`modular/psychology.py:126-131`); `modular/rounds.py:674-677` devuelve entonces `_without_combat`. El vectorial calcula `engaged` una sola vez **antes** de Psicología (`_driver.py:799-801`), y la rama de Estupidez solo reasigna `first_charges`/`second_charges` (`:986-1021`); únicamente la rama de Miedo recalcula `engaged = fear.engaged` (`:1040-1041`). | Ninguna: los perfiles canónicos, el proveedor, la distancia, las decisiones (`round.0.first.stupidity.leader.leader`) y el horizonte coinciden. No se cambia semilla ni escenario. | Defecto del motor (vectorial), mismo operador de Estupidez en ambos (`modular/psychology.py:64-70` vs `vectorized/_psychology.py:167-180`): el candidato retira el bono de carga pero ambos combatientes siguen intercambiando golpes. Evidencia coherente: `v14-slave-absent` 98,9 % sin resolver en modular frente a 38,7 % de victorias del segundo en el candidato; `v14-modifiers` 92,5 % → 84,1 % sin resolver. | — | Reproducción con la prueba de Estupidez forzada a fallo: el candidato debe dejar la ronda sin contacto, no solo sin bono de carga. |
| `c05-bear-hug` (`IndexError`) | **Filas de abrazo sin ordenar.** `hug_rows` se acumula recorriendo los ataques preparados (`vectorized/_attacks.py:1147-1161`), así que concatena las filas del ataque 1 detrás de las del ataque 0 y `won_rows` deja de ser monótono; `_prepare_weapon_attack` lo recibe como `active` (`:1168-1172`, el filtro de `:202` conserva el orden) y `_resolve_weapon` recalcula posiciones con `np.searchsorted(active, hit_rows)` (`:465`), que exige entrada ordenada. Con entrada desordenada devuelve `len(active)`, y el índice observado (4891) es exactamente el tamaño del array. La batería solo pasa combatientes, filas, semilla, horizonte, decisiones y contexto (`_battery_runner.py:145-160`): no aporta índices. | Ninguna. | Defecto del motor (vectorial) localizado por lectura; la línea exacta del traceback queda como predicción acotada (`rolls[hit_positions]`, `_attacks.py:466`). | — | Reproducir con la muestra completa: el fallo debe desaparecer al ordenar `won_rows` antes de preparar el ataque, sin tocar la batería. |

### Correspondencia de cobertura

Los 25 rechazos de admisión y las 2 incompatibilidades declaradas siguen dentro
del denominador de `complete`: la clasificación nueva (`INCOMPATIBLE:admission`)
cambia la etiqueta y la atribución, no el recuento. `c11-curse-of-revenant`
queda preparado con su prerrequisito declarado y no se sustituye por otro
escenario ni se retira del perfil. `v14-handler` y `v14-handler-absent` pasan de
incompatibles a preparados: los 114 casos se conservan, con 112 preparados y 2
incompatibles (`c03-petru-potion`, `v01-restriction`), los mismos dos del perfil
`deep`. Los tres perfiles conservan su denominador; lo que cambia es cuántos
casos llegan a muestrear, no qué casos cubre cada perfil.

**Entrega:** `TMP_VECTORIAL_ENGINE_2A2B/parity_update/P03-deliverable.md`
