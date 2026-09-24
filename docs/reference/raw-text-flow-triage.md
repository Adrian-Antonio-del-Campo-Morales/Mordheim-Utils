# Clasificación de las incidencias `raw-text-flow`

Estado revisado: 24 de septiembre de 2026. Fuente:
`build/generated/gui-text-audit-deep.json` — 1.946 puntos inventariados, 718
incidencias de análisis, de las cuales **166 son `raw-text-flow`**.

Este documento cierra el conjunto de incidencias `raw-text-flow`: para cada una
indica si es una fuga demostrada, qué mecanismo la protege y qué queda fuera de
la garantía. Complementa [la guía de salidas
localizadas](guia-salidas-localizadas-web.md); no sustituye su contrato ni el
control obligatorio del detector.

## 1. Qué afirma y qué no afirma una incidencia `raw-text-flow`

`audit:gui:deep` marca un destino cuando el rastreo de procedencia encuentra, en
la misma expresión, una lectura de campo crudo —`row.name`, `row["effect"]`,
`row["id"]`, `item.item_id`, `warrior.profile_id`, `result.message`…— y no puede
demostrar que el valor haya pasado por un productor de presentación.

La incidencia significa **«no se ha demostrado la protección»**, no «hay una
fuga». Puede ser:

- un identificador usado como clave, valor, argumento de acción o búsqueda;
- una entrada personal del usuario;
- una cantidad, un dado o una condición de renderizado;
- una escritura de datos de negocio sin destino textual;
- texto que sí pasa por un resolver, pero cuya llamada el rastreador no puede
  atribuir (módulo de otro paquete, función local, índice del lector).

Cerrar una incidencia exige **leer el origen y el destino** y, cuando la
protección se apoya en código, bloquearla con una prueba que rechace una fuga
deliberada. Un recuento limpio no acredita nada por sí solo.

## 2. Reglas de clasificación empleadas

| Regla | Cuándo aplica | Qué exige | Incidencias |
| --- | --- | --- | --- |
| R1 Identidad | El valor sólo se usa como `key` de React, `value` de control, miembro de una acción, argumento de búsqueda o campo persistido. | La sección 1 de la guía mantiene los IDs como identificadores; su etiqueta visible se resuelve aparte. | 122 |
| R2 Prosa o captura resuelta | El valor entra en un resolver/adaptador revisado y la salida es un valor de presentación. | Haber leído el productor y, cuando aporta cobertura nueva, añadir una prueba marcada. | 35 |
| R3 Mixto o escritura | El valor se escribe en el documento/caché, o combina identidad y prosa en la misma expresión. | Comprobar que no existe destino textual y que la identidad no se imprime. | 9 |

El reparto R1/R2/R3 se calcula por familia de origen (identificador frente a
prosa/captura) y es orientativo: la evidencia vinculante es la clasificación por
archivo de la sección 4, que cubre las 166 incidencias una a una.

Ninguna incidencia quedó en «sin resolver»: **0 fugas demostradas, 0 incidencias
sin clasificar** en el informe del 24 de septiembre. Lo que sigue sin
certificarse son los 76 recorridos truncados (`incomplete-text-flow`) y las
pantallas que estas sondas no ejecutan (sección 6).

## 3. Productores verificados

Estas son las fronteras leídas durante la clasificación. Un valor que pasa por
cualquiera de ellas deja de ser texto crudo; quitar una de ellas invalida la
clasificación de los archivos que dependen de ella.

| Productor | Ubicación | Por qué cierra la incidencia |
| --- | --- | --- |
| `resolveKbText` / `recordText` / `legacyText` | `packages/typescript/adapters/knowledge-reader/index.ts` | Resuelve sólo el idioma solicitado y sólo para referencias con índice de presentación; en error devuelve `unavailableText`. |
| `fieldValues` / `presentationEntries` | `packages/typescript/adapters/knowledge-reader/presentation.ts` | La captura canónica es texto inglés; el mapa `names`/`*_i18n` lo sustituye por idioma. |
| `knowledgeName` / `knowledgeDescription` / `persistedSystemText` / `advanceResultText` / `readableValue` / `warriorAbilityRef` / `variantName` / `resourceAmount` | `apps/warband-manager-web/src/features/campaign/displayText.ts`, `src/features/advances/advanceResultText.ts` | Adaptadores de la frontera web: referencia exacta, aviso localizado si falta, y compatibilidad v5 aislada por coincidencia completa. |
| `RulesCatalogue.toEntry` / `tagsFor` / `profileLinks` | `packages/typescript/application/rules/rules-catalogue.ts` | Nombre y prosa por `recordText`; etiquetas sólo desde el vocabulario cerrado `isCatalogueLabel` (desconocido → sin etiqueta) y relaciones desde `catalogueLabel`. |
| `scenarioAwards` / `scenarioResourceRewards` / `scenarioExplorationRewards` / `scenarioLootRewards` | `packages/typescript/application/campaign/features/battle/scenario-awards.ts` | `label`/`rule` son `ResolvedKbText` de `recordText`; el texto canónico sólo se usa para clasificar con expresiones regulares. |
| `localizeErrorMessage` / `messageOf` | `apps/warband-manager-web/src/features/campaign/useCampaignApp.ts` | Traduce mensajes conocidos por coincidencia exacta; lo desconocido devuelve `error.action-failed`, nunca la excepción. |
| `resourceAmount` → `enumReadableValue` | `apps/warband-manager-web/src/features/campaign/presentation-enums.ts` | Enumeración cerrada; un valor desconocido es aviso, no etiqueta. |
| `warriorPersonalName` / `campaignPersonalName` / `warbandPersonalName` / `battlePersonalNotes` | `apps/warband-manager-web/src/features/campaign/presentation-values.ts` | Excepciones de procedencia personal: conservan el texto literal del usuario. |
| `presentationOutput` | `apps/warband-manager-web/src/features/campaign/presentation-output.ts` | Extracción final: es identidad en tiempo de ejecución, **no** traduce ni sanea. Sólo puede recibir un valor de presentación. |

## 4. Clasificación por archivo

«Protección verificada» resume qué se leyó para cerrar las incidencias de ese
archivo. Las líneas corresponden al informe del 24 de septiembre.

| Archivo | Nº | Líneas | Protección verificada |
| --- | --- | --- | --- |
| `src/features/battle/BattlePanel.tsx` | 22 | 70, 75–80, 82 | Etiquetas de objetivos y recompensas desde `scenarioAwards`/`scenario*Rewards` (`recordText`, `ResolvedKbText`); IDs como claves, argumentos de acción y estado numérico (`enemyOoa`, `objectives`, `loot`); `notes` es la nota personal del usuario; errores ya resueltos (`app.error: PresentationValue`). |
| `src/features/campaign/CampaignSlice.tsx` | 22 | 40, 46, 105–117 | Propiedades de modelo/documento que cada workspace resuelve con `knowledge`; `variantName` busca dentro de la banda propietaria y falla con aviso; `String(entry.item_id)` y `warriorAbilityRef` alimentan `KnowledgeHint`; `app.error` es un valor de presentación. |
| `src/ProductApp.tsx` | 20 | 93, 94, 179–198 | `RulesCatalogue` (`recordText` + vocabulario cerrado de etiquetas + `catalogueLabel`); IDs de sesión como claves; `kbError` sólo se usa como condición y muestra `t.kbFail` (la excepción nunca se imprime); `operationError` pasa por `localizeErrorMessage`; nombre de campaña y banda los escribe el usuario. |
| `src/features/draft/DraftWorkspace.tsx` | 16 | 56, 71, 72, 80–85 | `knowledgeName`/`knowledge.recordText`/`warriorPersonalName`; `resourceLabel` → `resourceAmount` → enumeración cerrada; IDs como claves y valores de control; el diálogo de renombrado muestra la entrada personal. |
| `src/features/hirelings/HirelingsPanel.tsx` | 12 | 138, 150–230 | `displayName` es `resolveKbText(...)` con `unavailableText` en error; `resourceLabel`; `restriction_notes` está tipado `ResolvedKbText[]`; los IDs son claves, valores de control y claves de estado (`buy:<id>`). |
| `src/features/searches/RareSearchPanel.tsx` | 11 | 21, 45–66 | Los nombres de las ofertas se sustituyen por `knowledgeName` antes de renderizar; los IDs son claves y valores de `select`; la captura persistida `searches[].label` no la imprime ningún consumidor (revisado); `DiceResolver` recibe `PresentationText` o un elemento `KnowledgeHint`. |
| `src/features/advances/AdvancesPanel.tsx` | 8 | 23, 36, 45–52 | `advanceResultDetails`/`advanceResultText` (coincidencia completa, si no aviso), `localizedLabel` para la tabla, `knowledgeName` para habilidades y hechizos, IDs como claves y argumentos. |
| `src/features/injuries/InjuriesPanel.tsx` | 8 | 55, 61, 79, 98–107 | `warriorPersonalName`, cantidades y dados numéricos, `translate` con argumentos tipados, `KnowledgeHint` por `result_id`; `targets` es el nombre personal que escribe el usuario. |
| `src/features/injuries/PostBattleInjuries.tsx` | 7 | 115, 143, 166, 269–329 | Igual que el panel anterior: `KnowledgeHint` por id, dados y rescates numéricos, objetivo de odio escrito por el usuario. |
| `src/features/draft/DraftPanel.tsx` | 5 | 36, 50, 72, 78, 95 | `useDraftWorkflow` declara `options[].name: PresentationValue` y `error: PresentationValue \| null`; el resto son mensajes `translate` y estados booleanos. |
| `src/features/exploration/ExplorationPanel.tsx` | 5 | 126, 232, 273, 306 | `legacyVisibleText` (mensaje exacto, `uiMessageForText` o `legacyText`; si no, aviso) y `readableValue`; el héroe se ordena por nombre personal y se muestra con `warriorPersonalName`; `count` es numérico. |
| `src/features/campaign/WarriorCard.tsx` | 4 | 21, 22 | `warriorPersonalName`, `knowledgeName` para habilidades y reglas, `KnowledgeHint` por id, símbolo de estado vacío. |
| `src/features/equipment/EquipmentPanel.tsx` | 4 | 61, 79–121 | `warriorPersonalName`, `KnowledgeHint` por `item_id`, `localError` es `app.error` (`PresentationValue`). |
| `src/features/exploration/ScenarioFollowupsPanel.tsx` | 3 | 17 | Las opciones de hechizo salen de `scenarioSpellOptions` y se vuelven a resolver con `knowledgeName`; los nombres sólo se usan para ordenar; el héroe se muestra con `warriorPersonalName`. |
| `src/features/review/ReviewPanel.tsx` | 3 | 92, 93, 94 | `pendingStep` es un número validado 0–7; las condiciones renderizan mensajes `translate`; las exportaciones usan los escritores legibles localizados. |
| `src/features/recruitment/RecruitProfilePanel.tsx` | 2 | 17 | Los perfiles se resuelven con `knowledgeName`; el nombre del recluta es una entrada personal. |
| `packages/typescript/domain/campaign/kernel/hirelings.ts` | 2 | 142, 303 | Escrituras de características y avances sobre el documento; sin destino textual. |
| `src/features/advances/ManualSkillPanel.tsx` | 1 | 16 | `warriorPersonalName`; IDs como claves y argumentos. |
| `src/features/battle/BattleHistory.tsx` | 1 | 62 | `battleParticipantName` (adaptador) y `localizedLabel` para el resultado; cantidades numéricas. |
| `src/features/dice/DiceResolver.tsx` | 1 | 19 | La propiedad `label` está tipada `PresentationText \| ReactElement` y todas las llamadas revisadas pasan un productor o un elemento `KnowledgeHint`; una cadena arbitraria no compila. |
| `src/features/hirelings/HirelingUpkeepPanel.tsx` | 1 | 18 | `warriorPersonalName` y `resourceAmount`; la ordenación usa el nombre personal. |
| `src/features/recruitment/GroupRecruitmentPanel.tsx` | 1 | 19 | `warriorPersonalName`, `resourceAmount`, cantidades y el tipo de guerrero por enumeración localizada. |
| `src/features/review/FollowUpAcknowledgements.tsx` | 1 | 11 | `persistedSystemText` (mensaje exacto o `legacyText`; si no, aviso) y `localizedLabel` para el tipo de seguimiento. |
| `packages/typescript/adapters/knowledge-reader/presentation.ts` | 1 | 89 | Asignación de procedencia (`source`) dentro del constructor del índice de presentación. |
| `packages/typescript/domain/campaign/kernel/create-draft.ts` | 1 | 524 | Combinación de filas de inventario en el documento. |
| `packages/typescript/application/campaign/features/injuries/injuries-workflow.ts` | 1 | 202 | Modificadores de características sobre el documento. |
| `packages/typescript/application/campaign/features/recruitment/recruitment-workflow.ts` | 1 | 48 | Transferencia de equipo entre inventario y guardarropa. |
| `packages/typescript/adapters/knowledge-reader/index.ts` | 1 | 329 | Normalización del mapa de idiomas dentro del lector (`names[locale] = value`). |
| `packages/typescript/application/campaign/features/searches/search-workflow.ts` | 1 | 14 | **Paridad, no fuga:** `searches[hero.id]` guarda `label: offer.name`, un nombre canónico inglés (o el propio ID si el lector no lo resuelve). La web no lo imprime: `RareSearchPanel` y las exportaciones vuelven a resolver el nombre por KB, y ningún otro consumidor lee ese campo (revisado en toda la web). El **escritorio** sí lo lee (`packages/python/campaign/mordheim_campaign/ui/views/moments/post_battle_moment.py:212`, con `target_id` como alternativa), así que retirarlo rompería la paridad v5. Corregirlo pertenece a la presentación del escritorio, fuera del ámbito de esta guía. |

## 5. Índice de las 166 incidencias

El informe JSON conserva las 166 incidencias individuales; aquí se agrupan las
que comparten archivo, línea y mecanismo para que el listado sea revisable. Los
números coinciden con el orden del informe (`[nº] archivo:línea`).

<details>
<summary>Listado completo</summary>

- **[1]** `src/features/advances/AdvancesPanel.tsx:23` — fieldset — `tables.map(...)` con `localizedLabel`.
- **[2]** `:36` — tbody — `rows.map(...)`, `id = String(row["warrior_id"])`.
- **[3]** `:45` — KnowledgeHint — `result.skillId`.
- **[4]** `:45` — td — `advanceResultText(message, ...)`.
- **[5]** `:46` — PromotionSetup — `id`.
- **[6]** `:50` — select — `knowledgeName` sobre `skill["id"]`.
- **[7]** `:51` — PromotionOffer — `id`.
- **[8]** `:52` — select — `knowledgeName` sobre `spell["id"]`.
- **[9]** `src/features/advances/ManualSkillPanel.tsx:16` — select — `warriorPersonalName(row, locale)`.
- **[10]** `src/features/battle/BattleHistory.tsx:62` — article — `battleParticipantName(battle, row.id, locale)`.
- **[11]**–**[14]** `src/features/battle/BattlePanel.tsx:70` — section/fieldset — `app.error`, guardas de `checks` y `warriorPersonalName`.
- **[15]**–**[17]** `:75` — form/div/NumberStepper — objetivos manuales (`row.label` de `recordText`) y `enemyOoa[warrior.id]`.
- **[18]**–**[21]** `:76` — form/fieldset/div/NumberStepper — igual, con `objectives[row.id]`.
- **[22]**–**[24]** `:77` — form/fieldset/NumberStepper — `battle.resource-obtained` y `rewardQuantities[row.id]`.
- **[25]**–**[27]** `:78` — form/fieldset/LootReward — recompensas de botín por `recordText`.
- **[28]**–**[29]** `:79` — fieldset/NumberStepper — `casualtiesFor(warrior.id)`.
- **[30]** `:80` — textarea — `notes` (nota personal).
- **[31]**–**[32]** `:82` — fieldset/NumberStepper — `displayedXpAwards[warrior.id]`.
- **[33]** `src/features/campaign/CampaignSlice.tsx:40` — WarriorCard — `campaign.identity.band_id`.
- **[34]**–**[36]** `:46` — KnowledgeHint — `String(entry.item_id)` y `warriorAbilityRef(...)`.
- **[37]**–**[40]** `:105`–`:107` — section/select — `app.error`, mensajes `translate`, `variantName(...)`.
- **[41]**–**[54]** `:109`–`:117` — TimelinePanel, DraftWorkspace, StateWorkspace, BattleHistory, PostBattleHistory, PostBattleWorkspace, BattlePanel — propiedades de documento/estado.
- **[55]**–**[58]** `src/features/campaign/WarriorCard.tsx:21,22` — KnowledgeHint/section — `entry.item_id`, `entry.id`, símbolo vacío.
- **[59]** `src/features/dice/DiceResolver.tsx:19` — strong — `typeof label === "string" ? presentationOutput(label) : label`.
- **[60]**–**[64]** `src/features/draft/DraftPanel.tsx:36`–`:95` — section/select — `workflow.options[].name` y `workflow.error`, ambos `PresentationValue`.
- **[65]**–**[80]** `src/features/draft/DraftWorkspace.tsx:56`–`:85` — article/section/select/fieldset/input — resoluciones por KB, claves por ID, diálogos con entrada personal.
- **[81]**–**[84]** `src/features/equipment/EquipmentPanel.tsx:61`–`:121` — section/KnowledgeHint/select — `localError`, `entry.item_id`, `warriorPersonalName`.
- **[85]**–**[89]** `src/features/exploration/ExplorationPanel.tsx:126`–`:306` — section/ul/DiceResolver/select/fieldset — `legacyVisibleText`, `count` numérico, héroe por `warriorPersonalName`.
- **[90]**–**[92]** `src/features/exploration/ScenarioFollowupsPanel.tsx:17` — section/select — `scenarioSpellOptions` + `knowledgeName`, orden por nombre.
- **[93]**–**[104]** `src/features/hirelings/HirelingsPanel.tsx:138`–`:230` — section/tbody/td/KnowledgeHint/NumberStepper/select — `displayName` (`resolveKbText`), `resourceLabel`, claves y cantidades.
- **[105]** `src/features/hirelings/HirelingUpkeepPanel.tsx:18` — section — `warriorPersonalName` y `resourceAmount`.
- **[106]**–**[113]** `src/features/injuries/InjuriesPanel.tsx:55`–`:107` — section/tbody/td/input/NumberStepper/DiceResolver — errores resueltos, rescates y objetivos personales, dados.
- **[114]**–**[120]** `src/features/injuries/PostBattleInjuries.tsx:115`–`:329` — tbody/KnowledgeHint/td/input/NumberStepper/DiceResolver — igual que el panel anterior.
- **[121]** `src/features/recruitment/GroupRecruitmentPanel.tsx:19` — tbody — `warriorPersonalName` y `resourceAmount`.
- **[122]**–**[123]** `src/features/recruitment/RecruitProfilePanel.tsx:17` — select/section — `knowledgeName` sobre `profile_id` y nombre personal.
- **[124]** `src/features/review/FollowUpAcknowledgements.tsx:11` — section — `persistedSystemText(row["description"], ...)`.
- **[125]**–**[127]** `src/features/review/ReviewPanel.tsx:92`–`:94` — section — `pendingStep` numérico y guardas con `translate`.
- **[128]**–**[138]** `src/features/searches/RareSearchPanel.tsx:21`–`:66` — KnowledgeHint/section/optgroup/article/RarePurchase/DramatisHire — `offer.item_id`, `hero.id`, ofertas con nombre resuelto.
- **[139]**–**[158]** `src/ProductApp.tsx:93`–`:198` — div/article/section/main/select — catálogo de reglas, sesiones, `kbError`/`operationError`, `variantName`, diálogos.
- **[159]** `packages/typescript/adapters/knowledge-reader/presentation.ts:89` — asignación de `source` en el índice.
- **[160]** `packages/typescript/domain/campaign/kernel/create-draft.ts:524` — combinación de inventario.
- **[161]**–**[162]** `packages/typescript/domain/campaign/kernel/hirelings.ts:142,303` — `stats[key]`, `statAdvances[key]`.
- **[163]** `packages/typescript/application/campaign/features/injuries/injuries-workflow.ts:202` — `statModifiers[stat]`.
- **[164]** `packages/typescript/application/campaign/features/recruitment/recruitment-workflow.ts:48` — transferencia de inventario.
- **[165]** `packages/typescript/application/campaign/features/searches/search-workflow.ts:14` — `label: offer.name` persistido para paridad con el escritorio; no lo imprime la web.
- **[166]** `packages/typescript/adapters/knowledge-reader/index.ts:329` — `names[locale] = value` en la normalización.

</details>

## 6. Lo que sigue sin certificarse

1. **76 recorridos truncados** (`incomplete-text-flow`). Este documento no los
   cubre —sólo clasifica las rutas que sí alcanzaron un origen—, pero sus cortes
   y destinos están revisados en [los 76 recorridos truncados](incomplete-text-flow-triage.md):
   el corte es agotamiento del presupuesto de trabajo por punto, y lo que queda
   detrás pertenece a las mismas familias de identidad y prosa canónica. Se
   revisan con `npm run audit:gui:deep`, que aplica 2.500 pasos y 80 niveles.
2. **Pantallas y estados no ejecutados.** La clasificación es de código, no de
   ejecución: menús, formularios, estados de error y diálogos abiertos siguen
   pendientes de una revisión bilingüe real.
3. **Recursos externos y construcción dinámica.** Bibliotecas, PDF visual y
   cualquier HTML ajeno al análisis requieren comprobación propia.
4. **Captura compartida con el escritorio (punto [165]).** `searches[].label`
   no se imprime en la web, pero el escritorio la muestra con `target_id` como
   alternativa. Mientras siga siendo un campo de paridad v5, la revisión de su
   texto pertenece al escritorio; el lado web ya resuelve la etiqueta por KB.
5. **Automatización del reparto.** Las reglas R1/R2/R3 de la sección 2 se
   calcularon por familia de origen; el detector no las aplica. Si se quiere
   convertir esta clasificación en una puerta automática, hace falta ampliar el
   rastreador con reglas verificables y pruebas que rechacen la variante
   insegura, no una lista de excepciones por archivo.

## 7. Reejecución y mantenimiento

```powershell
npm --prefix apps/warband-manager-web run audit:gui:deep
```

```powershell
$audit = Get-Content 'build/generated/gui-text-audit-deep.json' -Raw | ConvertFrom-Json
$audit.findings | Where-Object reason -eq 'raw-text-flow' |
  Group-Object file | Sort-Object Count -Descending | Select-Object Count, Name
```

Pruebas que bloquean una regresión en los productores de la sección 3:

```powershell
npm --prefix apps/warband-manager-web test -- `
  src/architecture/raw-text-flow-producers.test.ts `
  src/architecture/presentation-poison.test.tsx `
  src/features/export/warband-pdf.test.ts
```

Al cambiar un productor, un consumidor o una propiedad transportadora, la
clasificación deja de ser válida: volver a generar el informe, revisar los
recorridos afectados y actualizar esta tabla. No añadir excepciones por
archivo/línea ni ampliar el clasificador sin una prueba que rechace la variante
insegura.
