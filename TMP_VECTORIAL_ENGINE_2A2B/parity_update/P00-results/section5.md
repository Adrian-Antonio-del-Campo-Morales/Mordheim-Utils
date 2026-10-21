## 5. Selección de niveles dirigida por variantes

> **Sustituye la composición por recuentos de la revisión 2.** Los tamaños
> 31/125/149 quedan retirados: eran estimaciones, no cuotas ni criterios de
> aceptación. Un nivel es un **conjunto de variantes** (§4.4), no un número de
> casos ni una etiqueta de familia.

### 5.1 Principio

Cada `BatteryCase` declara `variant` (por ejemplo `B14.1`) y `level`. La
pertenencia se decide por la variante, no por el número de casos:

- **quick ⊆ complete ⊆ deep**, por `id` de caso. `battery_cases(level)` devuelve
  la unión de niveles hasta `level`.
- Un caso de `quick` es una **regresión** de una variante base; no acredita todas
  sus variantes ni la ausencia.
- `complete` incluye **todas** las variantes `required=True` y las materiales con
  observable/testigo disponible, incluidas las negativas.
- `deep` incluye `complete` y añade **composición** y **sensibilidad**; no añade
  reglas nuevas que no estén en `complete`.

### 5.2 `quick` — regresión de variantes base

Criterio: la variante tiene un **testigo publicado o preparable** y un resultado
directo observable. Se elige una representativa, no todas.

| Variante | Caso quick | Por qué |
| --- | --- | --- |
| B01.2 | gasto de un recurso (`force-of-will`/`luck`) | Estado inicial y recurso; la reproducción exacta ya los compara. |
| B06.1 | parada de espada | Situación E2E y `parried`; el defensor debe llevar el arma. |
| B07.2 | resultado más alto con dos heridas | `condition` es el resultado directo; el caso debe declarar el estado. |
| B07.3 | lesión por maza/concusión | Borde de tabla y arma; usable como regresión. |
| B10.2 | levantarse y golpear después | `condition`/orden por ronda; el caso debe declarar el derribo. |
| B10.3 | muerte súbita rechazada | Decisión explícita; sin guion es `NOT_RUN`. |
| B11.1 | minotauro causa miedo y el cargado falla | `fear-hit-sixes`; depende de G05/G06. |
| B14.1 | líder a 6" sobre el duelista | `leadership-first-failed`/`leadership-test-value`; requiere `nearby`+`distances`. |
| B15.1 | black hunger | Heridas al horizonte; la regla debe estar en el build. |
| B15.2 | recuperación del revenant | Heridas al inicio de turno; `skill.regeneration` es B05.2 (save), no esta variante. |

Las **puertas exactas** (`hit-targets`, `wound-targets`, `attack-pools`,
`priority`, `armour`, `keyed-dice-replay`) no son casos de `quick`: son
comprobaciones de operador de P03. `injury` no entra hasta corregir el defecto de
§4.3. `quick` puede ejecutarse sin ellas, pero no las sustituye.

### 5.3 `complete` — obligaciones base y variantes materiales

`complete` contiene:

1. Todas las variantes `required=True` de §4.4 (63) con al menos un caso cuando
   la variante es material; una por variante, no una por obligación ni por clave.
2. Todas las variantes **case-preparable** y **operator-base** con su testigo.
3. Las variantes **negativas** de las variantes que tienen una positiva:
   `expect="absent"`, `positive_control` y el predicado `absent` del tipo de
   testigo (contador 0, bandera falsa, categoría distinta, resultado distinto o
   hash igual). La ausencia no se acredita por «no pasó nada».
4. Las variantes **pending-observable/input/rule** se declaran y se ejecutan si el
   motor puede; salen `INCOMPATIBLE:witness`/`INCOMPATIBLE:input`/`INCOMPATIBLE:state`
   o `NOT_ACTIVATED`
   con propietario. **No se omiten** para que `complete` parezca verde.

`accepted=True` exige que el perfil esté completo y que no haya `DIVERGENCE`,
`INCOMPATIBLE`, `NOT_ACTIVATED` ni `NOT_RUN` (§7.9). Una dependencia externa
explícita (G00/G02/G05/G06) puede impedir que `accepted` sea verdadero **al
ejecutar**, pero no impide que P00 entregue la preparación: el caso está escrito,
declarado y asignado. P00 no espera a que el motor implemente la capacidad para
cerrar el inventario.

### 5.4 `deep` — composición y sensibilidad

`deep` = `complete` + las interacciones de §4.5 + las escaleras de §4.5. No se
generan combinaciones exhaustivas. Cada interacción se justifica por estado
compartido y orden observable:

- miedo → parada → herida; líder → miedo/estupidez; frenesí → ataque extra →
  capacidad de parada; armadura natural + escudo + buckler; muerte súbita →
  ataque único; black hunger → herida en el horizonte; espinas/ácido → daño, no
  recuperación.
- Sensibilidad: 6+ vs 5+, S3/S4/S5, primer asalto vs posterior, cargado vs no,
  1 vs 2 heridas, 6" vs 12".

`deep` no reserva una familia ni una variante entera; si una interacción necesita
una variante que no está en `complete`, se añade primero a `complete`.

### 5.5 Reglas de selección y presupuesto

- `battery_cases(level)` filtra por `case.level`; no hay alias con
  `--level deterministic|statistical|deep` ni con `--pair-set`.
- `rows` es el mínimo del caso; P04 puede ampliarlo y el informe guarda el `rows`
  efectivo. Ampliar la muestra no crea un caso nuevo ni cambia el nivel.
- P04 calibra **coste y muestra**, no cobertura. Si el presupuesto no alcanza para
  todo `complete`, el informe declara qué obligaciones quedaron fuera; no se
  rebaja `complete` a “lo que se pudo ejecutar”.
- Un caso nuevo entra por variante, no por familia. Si no se puede asignar a una
  variante de §4.4, el inventario está incompleto: se abre una variante nueva con
  los siete campos, no se mete en un cajón «otros».

### 5.6 Lo que no es un nivel

- **F00 enrutado** no es un caso de combate: es `structural` y se comprueba en
  `verification/consumers.py`, no en la batería.
- **Compilación compartida** (1256 `shared`) no es un duelo: se acredita con el
  compilador y los tests de construcción.
- **`unlocated`** (189) no es estructural ni está cubierto: queda `UNLOCATED`
  hasta que su propietario localice el consumidor.
- **`shared-operator`** no es una clase de equivalencia (§4.6): cada grupo se
  vincula a una comprobación exacta o queda pendiente.
