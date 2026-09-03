# Catálogo de campaña

Estas plantillas describen reglas persistentes de una banda y no participan en
el motor de duelo. Cada fichero es una fuente editorial independiente:

- conserva IDs estables y referencias a la fuente;
- separa la regla común de Mordheim de las excepciones de cada banda;
- usa `effect_id` para que las reglas de banda puedan declarar explícitamente
  qué regla de campaña modifican;
- referencia datos canónicos existentes, sin duplicar perfiles, composición,
  precios, rarezas, equipo o reglas especiales;
- deja las reglas sin confirmar como `status: draft`, en vez de inventar datos.

Las excepciones se mantienen en `bands/<collection>/<band>/special-rules.yaml`.
Cuando se implemente el runtime de campaña, los identificadores de `effect_id`
serán los puntos de enlace para sus handlers y para la persistencia de banda.

El orden de `post-battle-sequence.yaml` es normativo; los demás documentos
describen los datos que resuelve cada paso.

## Convención de IDs

Las entradas reales de este catálogo usan IDs con namespace y segmentos en
kebab-case: `campaign.<familia>.<detalle>`. Mantener el resultado semántico y,
cuando corresponda, el contexto de tabla; el número de tirada nunca es el único
identificador. Ejemplos: `campaign.serious-injury.hero.22-leg-wound`,
`campaign.exploration.double-2.shop` y `campaign.trading-post.sword`.

Los IDs ya existentes de otras áreas no se renombran: objetos usan su `item_id`
canónico en snake_case —por ejemplo `sword`— y se referencian desde una entrada
de campaña mediante ese campo. Los bloques `examples` siguen reservados a IDs
`example.*`.

## Propiedad de los datos

`bands/*/profiles.yaml` contiene características, coste, experiencia inicial,
equipo y reglas de cada perfil. `bands/*/band.yaml` contiene la composición y
los límites de la banda. `catalog/items/` contiene la ficha de cada objeto.
`trading-post.yaml` es la fuente canónica de precio de mercado, rareza y
disponibilidad post-batalla. `catalog/rules/racial-maximums.yaml` es la única
fuente de los máximos raciales de atributos: las reglas de banda y el avance de
campaña referencian sus entradas (`campaign.limit.racial-maximum.*`) por ID y
no incrustan la statline. El catálogo de campaña solo define procedimientos,
tablas de campaña y enlaces por ID; por ejemplo, una contratación refiere
`profile_id` y nunca copia la ficha del perfil.

Los valores `cost` ya presentes en `equipment-access.yaml` se conservan como
evidencia de las listas impresas durante la migración. No son un precio de
mercado: cuando un importe sea una excepción real deberá declararse de forma
explícita como `price_override`, con su fuente; en otro caso prevalece el
Trading Post. Las compras de varias unidades —por ejemplo, pares— se modelan
en `purchase_options`, no como otro precio del mismo `item_id`.

## TODO: cotejar precios de listas de banda

Antes de usar precios de campaña en el runtime, comparar cada valor `cost` de
cada `equipment-access.yaml` con el Trading Post. Para cada diferencia:

1. confirmar si es una excepción publicada, una regla de creación de banda o
   una discrepancia de la fuente;
2. si es una excepción, sustituir el uso implícito del coste por un
   `price_override` con `source_refs` verificables;
3. si no lo es, conservar el importe solo como evidencia histórica y aplicar
   el precio de `trading-post.yaml`.

No completar esta migración por coincidencia de nombres ni asumir que dos
precios distintos describen el mismo tipo de compra: revisar por `item_id`,
lista de equipo, perfil y opción de compra.

## Estado de los catálogos

Los catálogos de este directorio contienen datos reales con `source_refs`
verificables (fuente: The New Mordheimer, mordheimer.net) y `status:
published`. No quedan bloques `examples`: fueron sustituidos por la ingesta
real en el bloque principal de cada fichero.

| Fichero | Contenido | Estado |
|---|---|---|
| `post-battle-sequence.yaml` | Los 10 pasos post-batalla en orden normativo | publicado |
| `trading-post.yaml` | 338 entradas: precio base/coste variable, disponibilidad (77 común, 183 rare, 78 no vendidas) y restricciones | publicado |
| `serious-injuries.yaml` | Tablas D66 de héroe (20 resultados) y D6 de mercenario (2) con efectos tipados | publicado |
| `experience-and-advances.yaml` | 3 premios de XP, bono de underdog y 2 tablas de avance | publicado |
| `exploration-and-income.yaml` | Asignación de dados, tabla de resultados de exploración, venta de wyrdstone y artefactos mágicos | publicado |
| `recruitment-and-veterans.yaml` | 3 políticas de reclutamiento y disponibilidad de veteranos | publicado |
| `warband-rating.yaml` | Fórmula de rating con componentes y exclusiones | publicado |
| `trading-and-rarity.yaml` | Test de rareza, modificadores y reasignación de equipo | publicado |
| `scenarios.yaml` | 98 escenarios, 2 tablas de selección, reglas previas a la batalla y recompensas de progresión (`progression:`) transcritas en los 98 desde la página individual de cada escenario | publicado |
| `magic.yaml` | Reglas de lanzamiento, 45 asignaciones lore↔mago y 31 lores con 188 conjuros | publicado |
| `mutations.yaml` | Reglas de compra y 9 mutaciones con efectos tipados | publicado |
| `hired-swords-and-dramatis.yaml` | Schema v2: 98 entradas (72 Hired Swords + 26 Dramatis Personae) con fee/upkeep por recursos, procedimiento de búsqueda y elegibilidad estática + 18 reglas dinámicas | publicado |

Los máximos raciales de atributos viven fuera de este directorio, en el
catálogo compartido `catalog/rules/racial-maximums.yaml` (29 entradas
`campaign.limit.racial-maximum.*` con `source_refs`). Las reglas de banda de
`bands/*/special-rules.yaml` que describen avance los referencian por ID en el
texto (`effect`/`effect_i18n.en`) en vez de incrustar la statline numérica, de
modo que no existen dos copias que puedan desincronizarse.

La KB declara reglas y tablas, nunca su resultado: la experiencia acumulada,
coronas, wyrdstone, alijo, tiradas realizadas y compras de una banda concreta
pertenecen al estado/persistencia de campaña de las aplicaciones.

Cada escenario tiene página propia en mordheimer.net
(`/docs/campaigns/scenarios/<familia>/<slug>`) que publica las secciones de
`experience`, `wyrdstone`, tesoro e ingresos. La KB ingesta solo lo que afecta
a la progresión de la banda en esos escenarios: premios de experiencia
(referenciando los `campaign.experience.award.*` canónicos cuando coinciden),
wyrdstone obtenido, tesoro/objetos e ingresos en coronas, bajo la clave
`progression:` de cada entrada (véase el HOWTO). Las mecánicas de juego sobre
el tablero (terreno, despliegue, condiciones de victoria, monstruos,
reglas especiales de mesa) no se modelan por decisión de alcance. Cobertura
completa: los 98 escenarios del catálogo (rulebook, Town Cryer, Fanatic
Magazine, Fanatic Online, Archive Pestilen y Rynn Tyrr) tienen `progression:`
transcrita desde su página individual. Algunas fuentes de la Archive Pestilen
no declaran premios de progresión (invasiones zombi tipo Romero's Pride, The
Restless Dead o The Battle At Koleshire Keep): en esos casos la ausencia queda
documentada en `progression.notes`. Las dudas puntuales sobre una fuente se
documentan en `progression.notes` de la entrada.
Ningún YAML de este catálogo debe cargarse como implementación de reglas: los
cargadores (`load_campaign_catalog`, `load_post_battle_sequence`) y su
validación son trabajo de integración del runtime.
