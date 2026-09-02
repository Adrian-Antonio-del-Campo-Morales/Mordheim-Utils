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
disponibilidad post-batalla. El catálogo de campaña solo define procedimientos,
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

Cada YAML incluye un bloque `examples` con datos deliberadamente ficticios.
No debe copiarse ese bloque a la ingestión: es una referencia de forma. La
ingestión real añade entradas al bloque principal (`tables`, `awards`,
`exploration`, etc.), elimina el ejemplo equivalente y adjunta `source_refs`
verificables.
