# Los 76 recorridos truncados (`incomplete-text-flow`)

Estado revisado: 24 de septiembre de 2026. Fuente:
`build/generated/gui-text-audit-deep.json` — 1.946 puntos inventariados, 718
incidencias, de las cuales **76 son `incomplete-text-flow`**.

Este documento explica **por qué** se trunca cada recorrido y **qué destino
queda detrás de cada corte**, con la medición que lo respalda. Cierra el punto 1
de [la clasificación `raw-text-flow`](raw-text-flow-triage.md) y complementa [la
guía de salidas localizadas](guia-salidas-localizadas-web.md); no sustituye su
contrato ni el control obligatorio del detector.

Resumen en una frase: los 76 cortes son **agotamiento de un presupuesto de
trabajo** compartido por recorrido, no profundidad ni ciclos; al ampliarlo
aparecen 690 orígenes adicionales, y **todos** pertenecen a las dos familias ya
clasificadas (claves de identidad y nombre/prosa canónica que la web resuelve al
renderizar). Ningún corte oculta un texto que llegue al DOM sin resolver.


## 1. Qué es un recorrido truncado

`createPresentationFlowAudit` (`apps/warband-manager-web/tools/presentation-flow-audit.mjs`)
recorre hacia atrás la expresión de cada punto de salida. El estado se lleva en
una clausura **por punto**:

```js
let budget = maxSteps, truncated = false;
const incomplete = [];
const walk = (node, bindings, active, path = []) => {
  if (--budget < 0 || path.length > maxDepth) {
    truncated = true;
    if (incomplete.length < 5) incomplete.push({ ...location(node),
      reason: budget < 0 ? "step-limit" : "depth-limit", path });
    return;
  }
  // …sigue el recorrido
};
```

Cuatro consecuencias que definen el conjunto:

1. **El presupuesto se descuenta por nodo visitado, no por nivel.** El modo
   profundo usa `maxSteps: 2500, maxDepth: 80`
   (`presentation-audit.mjs:359`); el normal, 250/24. Cada llamada a `walk`
   resta 1.
2. **La fontanería no es gratis.** El contador se gasta también en los nodos
   "transparentes" que el rastreador atraviesa a propósito: `as`, paréntesis,
   `!`, anotaciones de tipo, literales de tipo, declaraciones de identificador y
   el abanico de `writes`/`collectionWrites`. Un punto con una lambda en línea
   que llama al kernel consume cientos de nodos antes de acercarse a un dato.
3. **Los cinco cortes registrados son muestras de frontera, no destinos.**
   Cuando el presupuesto se agota, el recorrido se desenrolla y va anotando los
   **cinco primeros nodos** que encuentra en ese momento. Por eso los cortes
   típicos son `'string'`, `'??'`, `'raw'`, `'"id"'`: no son "los cinco destinos
   importantes", son dónde estaba el DFS.
4. **El corte es una incidencia independiente, no un veredicto.** El CLI emite
   `incomplete-text-flow` **además de** `raw-text-flow` para el mismo punto
   (`presentation-audit.mjs:114-115`). 72 de los 76 puntos truncados **también
   tienen incidencia `raw-text-flow`**: el rastreador sí alcanzó un origen por
   otra rama y sólo dejó de enumerar las demás.

Registro de los 380 cortes (76 puntos × 5): **366 `step-limit`** y **14
`depth-limit`**. La profundidad es, pues, un caso marginal; el caso normal es
trabajo agotado.


## 2. Cuánto esconde cada corte

Para medir el efecto se reejecutó el rastreador sobre los mismos puntos con un
presupuesto mucho mayor (60.000 pasos; 200.000 en `ProductApp.tsx` y
`CampaignSlice.tsx`) y se comparó el conjunto de orígenes por punto.

Fidelidad de la sonda: a 2.500 pasos reproduce el informe profundo **sin
discrepancias** (95 hallazgos comparados en cinco archivos, 0 diferencias), de
modo que los orígenes "nuevos" son orígenes que el informe no recoge.

Resultados:

| Medición | Valor |
| --- | --- |
| Puntos que dejan de truncarse al ampliar el presupuesto | la mayoría: `WyrdstoneSalePanel` 1→0, `ReviewPanel` 1→0, `InjuriesPanel` 3→1, `ProductApp` 16→2 |
| Puntos que **siguen** truncados con 200.000 pasos | `CampaignSlice` 20→18 |
| Orígenes adicionales que aparecen al ampliar | **690** |
| De esos 690, claves de identidad | 503 (73 %): `profile_id` 207, `id` 115, `band_id` 85, `item_id` 72, `lore_id` 8, `group_id` 3, `category_id` 3, `entry_id` 3, `label` 2, `opponent_band_id` 2, `procedure_id` 1, `special_id` 1, `profile_name` 1 |
| De esos 690, nombre o prosa canónica | 187 (27 %): `name` 106, `names` 48, `notes` 23, `effect` 5, `result` 5 |

Dos lecturas, ambas importantes:

- **El corte oculta más orígenes de la misma clase, no una clase nueva.** Los
  `name`/`names` nuevos son nombres canónicos del KB que se copian al modelo y
  que la web resuelve al renderizar (`result.record.names` → `makeItemName` →
  `entry.name`; `profile["name"]` → `warrior.name` / `profile_name`; `entry["names"]`
  → `advanceResultText`). Los `notes` son **sólo control**: la comparación de
  `create-draft.ts:155` detecta la daga gratuita y nunca se imprime.
- **Ampliar el presupuesto no cierra el problema.** `CampaignSlice` pasa de 20
  cortes a 18 con 200.000 pasos: sus puntos reciben `doc`, `battle` y
  `stateDocument`, y el recorrido sigue el grafo de construcción del documento
  entero (`create-draft.ts` acumula 125 cortes). No hay presupuesto razonable que
  agote esa frontera. Un recorrido truncado, por tanto, **nunca** puede leerse
  como recorrido completo.


## 3. Los 16 destinos ocultos, familia por familia

Cada uno de los 76 puntos aparece exactamente una vez. La columna "corte
registrado" cita el nodo donde se agotó el presupuesto; la última columna es el
destino que habría alcanzado el recorrido.

| Familia (módulo del corte) | Puntos | Corte registrado | Destino que queda detrás |
| --- | --- | --- | --- |
| `domain/campaign/kernel/create-draft.ts` | 25 (#4, #5, #12-#29, #42, #49, #50, #72, #73) | `roster as OpenPayload`, `raw`, `raw["starting_gold"]`, `startingGold`, `bandRecord`, `bandRecord.data["roster"]`, `"profile_id"`, `"band_id"`, `value: bandId` | `bandRecord.data["roster"]` — `minimum_models`, `maximum_models`, `starting_gold`, `members[].profile_id` — y los `queryKnowledge({ id: { kind, value } })` del kernel. Son las restricciones numéricas y las claves del roster. Los `rejected(...)` en inglés canónico que también atraviesa esta rama son prosa ya resuelta por `localizeErrorMessage`. |
| `adapters/knowledge-reader/index.ts` | 11 (#1, #2, #30, #31, #37, #38, #39, #53, #54, #74, #75) | `Map`, `string`, `ArtefactRow`, `index`, `empty`, `"id"`, `injuries: empty`, `this.campaignMaps.lores` | El índice `Map<string, ArtefactRow>` que el lector construye con `indexById` (clave = `id`/`item_id`) y las secciones vacías de `indexCampaignSections`. Identidad pura del artefacto KB. |
| `application/rules/rules-catalogue.ts` | 11 (#60-#70) | `"item"`, `lore`, `lore.spells`, `spells`, `(spells as Readonly<Record<string, unknown>>[])`, `[]` | `campaignSection("magic").lores[].spells[]` y las filas de `categoryRows(kind)`; los `[]` son los fallbacks vacíos. Los `name`/prosa de esas filas pasan por `recordText`/`localizedEffect`, la familia de prosa ya capturada. |
| `application/campaign/features/draft/draft-workflow.ts` | 5 (#32-#36) | `result.state.campaign`, `result.state.campaign.identity`, `campaign_name: campaignName`, `result`, `view: result.state.view` | El objeto `identity` del documento al renombrar la campaña (`campaign_name`) y la vista copiada. Identidad y control de estado. |
| `application/campaign/features/searches/search-workflow.ts` | 5 (#56-#59, #76) | `bandId`, `groups`, `true`/`false`, `item`, `(row["price"] ?? {})` | La evaluación de elegibilidad (`band_id`, `group_id`, `any_of`, `all_of`, `not`) y la tabla de precios (`optional_variable_cost`, `multiplier`, `base_gc`). Booleanos y números; ninguna cadena impresa. |
| `application/campaign/features/battle/scenario-awards.ts` | 4 (#6-#9) | `String(value ?? "").trim()`, `String`, `row["effect"]`, `entry["amount_dice"]` | El `effect` canónico del escenario, usado **sólo** para clasificar el reparto y extraer dados/XP por expresión regular. La etiqueta visible es `recordText(source ?? entry, "effect", locale)`. |
| `application/campaign/features/hirelings/hirelings-workflow.ts` | 3 (#46-#48) | `(profiles as ArtefactRow[]).find(...)`, `profile`, `listings.campaignSection("hirelings")` | El bloque `warband_rating` del perfil (`kind`, `value`, `base`) y el índice de perfiles de hireling. Números. |
| `adapters/knowledge-reader/presentation.ts` | 2 (#10, #11) | `??`, `row.id ?? row.item_id`, `row.item_id` | La clave de `presentationEntries` (el `id` del registro) y el `fields` que se construye con `fieldValues`. Índice de presentación. |
| `domain/campaign/band-variants.ts` | 2 (#43, #44) | `value as Readonly<Record<string, unknown>>`, `row["id"]` | `variants[].id` y el fallback `names: { en: row["id"] }`; los `names` los resuelve `variantName` en el render. Identidad. |
| `domain/campaign/kernel/document.ts` + `features/injuries/injuries-workflow.ts` | 2 (#51, #52) | `document.campaign.post_battles.find((post) => !post.complete)`, `null` | El predicado `!post.complete` y el `?? null` de `pendingPostBattle`: control de flujo. La rama continúa en `pending.pending_follow_ups`, cuyos `row["id"]`/`warrior.id`/`warrior.name` sí quedan registrados por otras ramas del mismo punto. |
| `domain/campaign/kernel/ports.ts` | 1 (#3) | `"skill_id"`, `scenario: "scenario_id"`, `ID_KIND_BY_FAMILY` | El mapa familia → campo de identidad (`band_id`, `profile_id`, `item_id`, `skill_id`, `scenario_id`…). Identidad. |
| `application/campaign/features/exploration/exploration-workflow.ts` | 1 (#45) | `row.kind`, `=== "hero"` | El filtro de héroes que alimenta `new Set(...map((row) => row.id))` y las bajas de `battle.absentees`. El punto impreso (`count`) es un número. |
| `application/campaign/features/review/follow-up-acknowledgement-workflow.ts` | 1 (#55) | `row["id"] ?? ""`, `String(row["id"] ?? "")` | `String(row["id"])` de la fila de seguimiento y `acknowledgements[step]`. Al sondear sin presupuesto, sus orígenes son `row["id"]` y `row["encounter_id"]`. Identidad. |
| `src/features/draft/DraftWorkspace.tsx` | 1 (#40) | `itemId`, `prices.has(itemId)` (profundidad 5-14) | El `Map<string, number &#124; null>` de precios de la mochila, agotado por el tamaño de `stashOffers`, no por profundidad. Números. |
| `src/features/economy/WyrdstoneSalePanel.tsx` + `wyrdstone-sale-workflow.ts` | 1 (#41) | `available`, `profit: Number(cell?.["profit_gc"] ?? 0)` | `available` = fragmentos disponibles y `profit_gc`. Números: es el único punto que, sin presupuesto, **no produce ningún origen crudo**. |
| `src/features/campaign/i18n-core.ts` | 1 (#71) | `"en":"Recovery"`, `{"es":"se pierde",…}` | La tabla estática de traducción (`ui.9de7c707a1b0`…): el propio catálogo de textos de interfaz, mantenido a propósito en `i18n-core.ts`. |

Superficie afectada, para situar el conjunto:

| Archivo del punto | Truncados | Con incidencia `raw` hermana | Incidencias `raw` en el archivo |
| --- | ---: | ---: | ---: |
| `src/features/campaign/CampaignSlice.tsx` | 20 | 20 | 22 |
| `src/ProductApp.tsx` | 16 | 13 | 20 |
| `src/features/battle/BattlePanel.tsx` | 6 | 6 | 22 |
| `src/features/draft/DraftPanel.tsx` | 5 | 5 | 5 |
| `src/features/draft/DraftWorkspace.tsx` | 4 | 4 | 16 |
| `src/features/hirelings/HirelingsPanel.tsx` | 4 | 4 | 12 |
| `src/features/searches/RareSearchPanel.tsx` | 4 | 4 | 11 |
| `src/features/advances/AdvancesPanel.tsx` | 3 | 3 | 8 |
| `src/features/exploration/ExplorationPanel.tsx` | 3 | 3 | 5 |
| `src/features/injuries/InjuriesPanel.tsx` | 3 | 3 | 8 |
| `src/features/campaign/WarriorCard.tsx` | 2 | 2 | 4 |
| `src/features/recruitment/RecruitProfilePanel.tsx` | 2 | 2 | 2 |
| `src/features/economy/WyrdstoneSalePanel.tsx` | 1 | 0 | 0 |
| `src/features/equipment/EquipmentPanel.tsx` | 1 | 1 | 4 |
| `src/features/review/ReviewPanel.tsx` | 1 | 1 | 3 |
| `…/searches/search-workflow.ts` (punto interno) | 1 | 1 | 1 |


## 4. Los cuatro puntos sin incidencia cruda hermana

Trece de los dieciséis archivos tienen todos sus puntos truncados cubiertos por
una incidencia `raw-text-flow` hermana. Los cuatro que no la tienen se
probaron uno a uno:

1. **`WyrdstoneSalePanel.tsx:17`** (`NumberStepper`, `quote.available`). Sin
   presupuesto produce **cero orígenes**: el destino es `available` y
   `profit_gc`, dos números del `WyrdstoneSaleQuote`.
2. **`ProductApp.tsx:93`** (`details` y `section`, `group.rows.map((row) => …)`).
   Al ampliar, el corte desaparece y quedan **siete orígenes, todos claves**:
   `lore.id`, `row.band_id`, `row.id`, `row.item_id`, `row.lore_id` en
   `rules-catalogue.ts`, más `row.category_id` y `row.entry_id` en
   `ProductApp.tsx:87`, que son la clave del botón y de `openRule`.
3. **`ProductApp.tsx:180`** (`div`, `disabledMessage`). El recorrido entra en
   `translate(disabledMessage, locale)` y llega a la tabla estática de
   `i18n-core.ts`: el catálogo de textos de interfaz, que es el almacén de copia
   sancionado.

Ninguno de los cuatro imprime texto crudo: dos son números, uno es un puñado de
claves y otro es el propio catálogo de interfaz.


## 5. Lo que sigue sin certificarse

1. **Un corte no es una prueba de seguridad, en ningún sentido.** El corte dice
   que la enumeración no terminó; la sonda de la sección 2 dice que lo que falta
   es de las familias ya clasificadas, no que no haya nada más.
2. **El presupuesto no cierra la frontera.** `CampaignSlice` sigue truncándose a
   200.000 pasos. Mientras el punto reciba el documento entero, el recorrido
   seguirá siendo incompleto; no es un problema de ajustar un número.
3. **Las cinco ubicaciones registradas son arbitrarias.** Cambiar el orden de
   recorrido o el presupuesto cambia los cinco cortes registrados (la sonda lo
   demuestra: a 60.000 pasos los cortes de `InjuriesPanel` se desplazan a otro
   módulo). No deben leerse como "los cinco puntos a revisar" del punto de
   salida.
4. **Estados y pantallas no ejecutados.** Sigue pendiente la revisión bilingüe
   real de menús, formularios, errores y diálogos.
5. **Reparto automático.** Las familias de la sección 3 se asignaron a mano. Para
   convertirlas en puerta automática haría falta que el rastreador **no gastase
   presupuesto en nodos de fontanería** (anotaciones de tipo, constructores de
   `Map`, llaves de índice) y una prueba que rechace la variante insegura; no una
   lista de excepciones por archivo/línea.


## 6. Reejecución

```powershell
npm --prefix apps/warband-manager-web run audit:gui:deep
```

Recuento de las tres preguntas de este documento (cortes, motivos y puntos por
archivo):

```powershell
$audit = Get-Content 'build/generated/gui-text-audit-deep.json' -Raw | ConvertFrom-Json
$inc = $audit.findings | Where-Object reason -eq 'incomplete-text-flow'
$inc.incomplete | Group-Object reason | Select-Object Count, Name
$inc | Group-Object file | Sort-Object Count -Descending | Select-Object Count, Name
```

Sonda de presupuesto (artefacto local, no versionado): reejecuta el rastreador
sobre los mismos puntos con otro presupuesto y lista los orígenes que el informe
no recoge.

```powershell
node build/generated/probe-diff.mjs "src/features/injuries/InjuriesPanel.tsx" 60000
```

Al cambiar el rastreador, el presupuesto del modo profundo o los productores,
esta clasificación deja de ser válida: volver a generar el informe, repetir la
sonda y actualizar las tablas.
