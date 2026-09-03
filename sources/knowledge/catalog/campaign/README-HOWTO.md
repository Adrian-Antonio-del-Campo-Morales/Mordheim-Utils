# HOWTO: usar la KB de campaña

Esta guía explica cómo consultar y ampliar las reglas post-batalla sin crear
una segunda fuente de verdad. Está dirigida a desarrolladores que implementen
pantallas, casos de uso o ingestiones de campaña.

## Límite de responsabilidad

La KB contiene exclusivamente reglas inmutables del juego: tablas, costes de
mercado, disponibilidad, procedimientos, restricciones y fórmulas. Nunca
contiene una campaña concreta ni el resultado de aplicarle una regla.

Fuera de la KB se almacenan, entre otros, la experiencia actual de cada
guerrero, coronas y wyrdstone de una banda, su alijo, lesiones recibidas,
tiradas realizadas, compras, reclutamientos y el historial de post-batalla.
Ese estado pertenece al modelo/persistencia de campaña y se identifica mediante
IDs estables de la KB (`band_id`, `profile_id`, `item_id`, `rule_id`).

## Principio básico

La GUI nunca lee YAML y nunca decide reglas. La ruta correcta es:

```text
YAML de la KB → knowledge.loader → application → ui
```

El área `knowledge` carga y valida documentos; `application` los convierte en
opciones y resultados para un caso de uso; `ui` solo presenta esos resultados
y remite las acciones del usuario a `application`.

No cargar archivos de `sources/knowledge/` desde Tkinter ni copiar tablas de
campaña a widgets, constantes de UI o persistencia.

## Dónde vive cada dato

| Necesidad | Fuente canónica | Consultar por |
|---|---|---|
| Perfil, coste de recluta, experiencia inicial, equipo y reglas propias | `bands/<collection>/<band>/profiles.yaml` | `profile_id` |
| Límites y composición de una banda | `bands/<collection>/<band>/band.yaml` | `band_id` |
| Acceso de un perfil a una lista de equipo | `bands/<collection>/<band>/equipment-access.yaml` | `equipment_list_id` + `item_id` |
| Identidad y regla de un objeto | `catalog/items/*.yaml` | `item_id` |
| Precio de mercado, rareza y disponibilidad | `campaign/trading-post.yaml` | `item_id` |
| Orden post-batalla | `campaign/post-battle-sequence.yaml` | `campaign.step.*` |
| Heridas, experiencia, exploración, comercio y rating | Los ficheros hermanos de este directorio | `campaign.*` |
| Máximos raciales de atributos (avance) | `catalog/rules/racial-maximums.yaml` | `campaign.limit.racial-maximum.*` |
| Excepción de una banda o de un perfil | `bands/<collection>/<band>/special-rules.yaml` | `rule_id` / `effect_id` |

Una entrada de campaña puede referir `item_id`, `profile_id`, `band_id` o
`rule_id`, pero no vuelve a declarar la ficha a la que apunta.

Los IDs propios de campaña siguen `campaign.<familia>.<detalle>`, con
segmentos en kebab-case. Por ejemplo,
`campaign.serious-injury.hero.22-leg-wound` y
`campaign.trading-post.sword`. El objeto de la segunda entrada sigue siendo
`item_id: sword`; no se crea un segundo ID de objeto. Para opciones de compra,
usar un ID hijo explícito, como `campaign.trading-post.pistol.brace`.

Las tiradas derivadas se estructuran, no se expresan como texto. Una subtabla
declara `resolution.type: roll_table`, los dados y ramas con `when.min`/
`when.max`; cada rama tiene su propio ID y sus efectos. Para valores como D3,
usar `games: { kind: dice, dice: { count: 1, sides: 3 } }`; para un valor fijo,
`games: { kind: fixed, value: 1 }`. Los resultados obtenidos siguen fuera de
la KB, en el estado de campaña.

Para una recompensa de exploración que sea un objeto, usar `rewards.item_ids`.
Ejemplos ya presentes: `lucky_charm` en `catalog/items/combat-equipment.yaml`,
`axe`, `dagger` y `sword` en `catalog/items/weapons-close-combat.yaml`, y
`light_armour` en `catalog/items/armour.yaml`. Si el objeto no existe en el
catálogo —como ocurrió con Mordheim Map antes de añadir su ficha canónica en
`catalog/items/out-of-scope.yaml`— detener la ingestión de ese resultado y
añadir primero la ficha canónica del objeto con su fuente.

## Cómo consultar la KB existente desde código

Para información de bandas y perfiles, usar los cargadores existentes. Nunca
reconstruir rutas a mano desde la GUI:

```python
from mordheim_knowledge.loader import load_bands

packages = load_bands("mordheim")
package = next(row for row in packages if row.band["id"] == "pit-fighters")
profile = next(row for row in package.profiles if row["id"] == "pit-king")
```

Para un selector o pantalla que ya pertenece al simulador de combate, usar
`application.catalogue.CombatCatalogue`. Por ejemplo, `bands`, `profiles`,
`profile`, `weapons` y `cost` ya ofrecen datos preparados para la UI. Esta
clase es de solo combate: no debe ampliarse con estado post-batalla.

## Patrón para una función de campaña

Cuando se implemente campaña, crear un caso de uso en `application` —por
ejemplo `CampaignCatalogue` o `PostBattleService`— que reciba IDs y estado de
campaña, cargue las reglas mediante `knowledge.loader` y devuelva DTOs simples
para la UI.

```text
UI: «resolver exploración»
  → application: resolve_exploration(campaign_state, band_id)
    → knowledge: tablas de exploración + reglas especiales aplicables
    → application: ExplorationResult
  → UI: muestra dados, resultado y cambios propuestos
```

El estado mutable —oro, wyrdstone, lesiones, experiencia acumulada, alijo y
equipo asignado— pertenece por completo a `persistence`/modelo de campaña,
nunca a los YAML. La KB solo define cómo transformarlo. La UI solicita una
previsualización y el caso de uso aplica una transacción validada; no actualiza
valores directamente.

## Contrato mínimo de lectura que habrá que implementar

Antes de conectar una pantalla de campaña, añadir a
`knowledge.loader` cargadores con esta responsabilidad:

```text
load_campaign_catalog("serious-injuries", ruleset)
load_campaign_catalog("trading-post", ruleset)
load_post_battle_sequence(ruleset)
```

Cada cargador debe comprobar `schema_version`, `ruleset`, IDs únicos y que las
referencias (`item_id`, `profile_id`, `rule_id`) existen. El caso de uso nunca
debe interpretar YAML crudo ni tolerar referencias faltantes silenciosamente.

## Reglas de precio y equipo

1. Consultar primero el precio y la disponibilidad en `trading-post.yaml`.
2. Usar `equipment-access.yaml` solo para saber si ese perfil puede seleccionar
   el objeto.
3. Aplicar `price_override` únicamente si existe, está referenciado y su fuente
   confirma una excepción.
4. Representar pares, descuentos y costes variables con `purchase_options` y
   el precio estructurado del Trading Post; no con nuevos `item_id` ni precios
   alternativos implícitos.

Los `cost` históricos de las listas de equipo todavía deben ser cotejados:
véase el TODO en [README.md](README.md).

## Cómo añadir conocimiento

1. Localizar primero el dueño del dato en la tabla anterior.
2. Añadir la regla o tabla al fichero canónico y mantener un ID estable.
3. Añadir `source_refs` verificables; no convertir ejemplos en datos reales.
4. Para una excepción, crear o ampliar la regla especial de la banda y enlazar
   el `effect_id` de campaña pertinente.
5. Añadir validación de referencias y un caso semántico antes de hacer el dato
   ejecutable. La validación de la ingesta actual de campaña (cabeceras,
   ausencia de ejemplos ficticios, conteos canónicos y resolución de
   referencias contra items, bandas, grupos, condiciones, habilidades y
   perfiles) vive en `tests/knowledge/test_campaign_catalogs.py`.
6. Ejecutar `python -m mordheim_combat_lab validate`.

## Añadir o revisar recompensas de un escenario

Cada escenario con datos de progresión transcritos lleva la clave
`progression:` con estas subclaves (todas opcionales salvo `experience` cuando
la clave existe; si la fuente no declara premios de progresión —p. ej.
ciertas invasiones zombi de la Archive Pestilen— la ausencia debe quedar
documentada en `notes`):

- `experience`: lista de premios. Cada fila tiene **o bien** `ref` (un id
  canónico `campaign.experience.award.*` de `experience-and-advances.yaml`
  cuando la línea coincide con el premio estándar) **o bien** `summary` (texto
  fiel a la fuente para premios propios del escenario), nunca ambos. Cuando la
  cantidad es numérica se declara `amount`; cuando la fuente la da en dados,
  `amount_dice` (p. ej. `D6`). Nunca ambos.
- `wyrdstone`: texto con el wyrdstone que obtiene la banda al final (p. ej.
  por contador en posesión, con tope si la fuente lo declara).
- `income`: texto con ingresos en coronas o pagos fijos.
- `loot`: tesoro/objetos. `summary` describe cuándo se obtiene;
  `contents` (opcional) lista las filas con `reward`, `roll` (p. ej. `4D6`),
  `when.min`/`when.max` (opcional, si la tirada discrimina) e `item_id`
  (opcional, id canónico del catálogo de items cuando el premio es un objeto
  concreto del Trading Post).
- `exploration`: (opcional) texto con bonificaciones sobre la fase de
  exploración posterior (dados extra o repeticiones).
- `notes`: dudas o aclaraciones de la fuente para pasos posteriores
  (erratas sospechadas, discrepancias de cantidad/etiqueta, convenciones
  asumidas no declaradas en la página, conversiones de contadores no
  explícitas).

La URL de `source_refs` de un escenario transcrito apunta a la página
individual (`…/scenarios/<familia>/<slug>`), no al índice.

Los tests de forma y referencias viven en
`tests/knowledge/test_campaign_catalogs.py` (sección Escenarios).

## Estado actual

Los catálogos de este directorio están ingestados desde The New Mordheimer
(mordheimer.net) como datos declarativos con `source_refs` y `status:
published`: trading post (338 entradas con precio, rareza y restricciones),tablas de heridas, experiencia, exploración, reclutamiento, rating, escenarios
(98, los 98 con `progression:` transcrita desde su página individual: rulebook,
Town Cryer, Fanatic Magazine, Fanatic Online, Archive Pestilen y Rynn Tyrr),
magia (31 lores con 188
conjuros, con las 15 referencias `spell_list` de los perfiles de mercenarios
enlazadas por `lore_id` en `lore_assignments`) y mutaciones. Son reglas y tablas, no
 implementación: ningún YAML
codifica cómo aplicar una regla ni guarda estado de una campaña concreta.

Siguen sin cargarlos los cargadores del runtime (`load_campaign_catalog`,
`load_post_battle_sequence`), por lo que ninguna pantalla actual resuelve una
secuencia post-batalla. La primera implementación debe empezar por esos
cargadores —que comprueben `schema_version`, `ruleset`, unicidad de IDs y que
las referencias (`item_id`, `profile_id`, `band_id`, `condition_id`) existen—
y por un caso de uso que reciba el estado desde la persistencia externa;
después podrá añadirse la pantalla sin acoplarla a YAML ni al motor de duelo.
El catálogo de mercenarios
(`hired-swords-and-dramatis.yaml`, 98 entradas, ver `CAMPAIGN INGESTION
RESULTS.md`) está integrado con schema v2 y publicado; las 18 reglas de
elegibilidad dinámicas (dependientes de roster, variante mercenaria o tirada
condicional) viven declaradas en `catalog/hirelings/**` y las evaluará la
aplicación, igual que los 4 Dramatis out of scope y las 74 referencias
intrínsecas pendientes de los catálogos de perfiles (no bloquean coste ni
elegibilidad).

El Campaign Manager ya consume la KB para bandas y perfiles: su
`KnowledgePort` (`mordheim_campaign/application/knowledge_port.py`) usa
`load_bands`, `load_items` y `load_skills` para alimentar la creación de banda
sin que la GUI toque YAML, y su persistencia (`.mordheim`) referencia los IDs
canónicos (`band_id`, `profile_id`, `item_id`) sin duplicar reglas.
