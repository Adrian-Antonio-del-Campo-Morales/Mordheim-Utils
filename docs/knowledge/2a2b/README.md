# 2A/2B — checklist de integración y coordinación

Governing scope update — 2026-10-04: voluntary escape, withdrawal and contact breaking that ends the duel without resolving it are excluded, even if possible with two models. See [permanent ruling](../../decisions/design-rulings.md#voluntary-escape-does-not-belong-to-combat-lab--2026-10-04).

Current integration status — 2026-10-05: T13 modular implementation is partial.
The canonical 2B hireling route now supports twelve base hired-sword profiles;
fourteen normalized profiles retain intrinsic blockers and two Dramatis lack
stats. Optional Marks and other listed individual/product clauses remain open.
See the [governing progress and exact remaining work](tasks/T13-T15-remaining-plan.md#current-progress-and-remaining-work--2026-10-05).
NumPy/native ports have not started; final T14/T15 certification/closure remains
outstanding. Earlier delivery summaries are historical evidence.

## Punto de inicio y alcance

- Rama de trabajo: `2A2B`; remoto: `origin/2A2B`.
- Snapshot publicado: `9118ca2` (`chore: snapshot 2A2B starting point`), 25 de septiembre de 2026. Incluye los cambios locales existentes y la historia anterior; no certifica que sus tests pasen.
- La documentación de este directorio se publica después del snapshot, en un commit separado. No se ha ejecutado la integración al redactarla.
- Alcance: 19 bandas de 2A y 60 de 2B y sus catálogos; integrarlas primero en la KB, después en `warband-manager-web` y por último en `combat-simulator`.
- Fuera de esta ejecución: crear sistemas de despliegue, ocultación, disparo o resolución de magia de batalla. Sus reglas se conservan completas y con limitaciones explícitas; no se marcan como implementadas.
- Mantener staging y herramientas de ingesta. La aplicación seguirá leyendo exclusivamente `sources/knowledge`.
- La ejecución de las tareas termina en commits **locales** en `2A2B`. La autorización de push del snapshot y de esta documentación no autoriza publicar implementaciones posteriores ni cambiar `main`.

El documento es una checklist viva, no un certificado. Solo el coordinador cambia sus estados. Cada tarea tiene un [documento auxiliar](tasks/) con pasos y prompts de ejecución, revisión y reanudación.

## Frontera de producto vigente (2026-09-30)

Combat Lab y Warband Manager son aplicaciones independientes; comparten la KB canónica, no documentos, servicios ni estado de campaña. El orden de las fases organiza el trabajo sobre reglas compartidas y no establece una integración entre aplicaciones. Esta decisión sustituye las antiguas atribuciones de un productor de eventos de campaña a T13 en T09–T12.

Update 2026-10-01: they also share the pure
[warrior eligibility implementation](../../reference/eligibility.md). Combat Lab
executes it locally from projected facts; campaign services/state and combat
execution remain separate. T13 eligibility changes use that maintained module;
[T13-F035](tasks/T13-execution-follow-ups.md#t13-f035--revalidate-affected-t13-construction-evidence-after-eligibility-extraction)
tracks revalidation of the affected pre-extraction evidence.

Update 2026-10-02: the shared construction/validation module is an implemented
baseline, not a feature to recreate in T13.2. Its
[responsibility boundary](../../reference/eligibility.md#construction-boundary-for-phased-implementation)
distinguishes legal choices, fact adapters, compiled combat effects, battle
execution and product availability. T09–T12 accepted flows remain accepted;
only actual later changes can invalidate their affected evidence. F035
is accepted as current-consumer reconciliation: existing shared decisions,
canonical facts and specialized Combat Lab integration gaps now have separate
dispositions. Absence of an old Python consumer does not authorize another rule
implementation. See [F035's governing dispositions](tasks/T13-shared-eligibility-reconciliation.md#12-coordinator-acceptance-and-governing-dispositions--2026-10-02).

| Responsabilidad | Propietario y límite |
| --- | --- |
| Legal equipment/skill choices, recipients, variants and loadout restrictions | Existing shared TypeScript eligibility module, used directly by Warband Manager and locally through the embedded Python adapter by Combat Lab; no duplicate validator. |
| Canonical bindings and characteristics/weapon/effect projection for simulation | Canonical KB and Combat Lab Python compiler. Legal selection does not imply implemented combat support; supported-effect refusal is separate from illegality. |
| Identificadores de plantilla, `member_ids`, `battle_number`, adquisición de mutaciones y retirada definitiva | Warband Manager. Los hechos de la mesa son entradas de sus propios flujos; Combat Lab no los produce ni llama a sus servicios. |
| Rout de banda, psicología de grupo y combate con varios destinatarios | Fuera del alcance de Combat Lab, que sigue simulando duelos 1v1. Los hechos de partida de Warband Manager pertenecen a sus propios flujos. |
| Modificadores de combate de una mutación | Combat Lab, desde selección y compilación propias basadas en la KB; no consume `campaign.special_rules`. |
| Acciones y psicología individuales incluidos en T13 | Contexto mínimo del duelo entre dos combatientes. Sin grupos, terceros independientes ni reglas de mapa/terreno/clima: niebla, agua y condiciones similares quedan excluidas incluso como opciones manuales. |
| «Transferencia a T13» en los inventarios históricos | Candidatura para reconciliación, no garantía de inclusión. La [decisión 1v1 del usuario, 2026-10-04](../../decisions/design-rulings.md#combat-lab-remains-a-1v1-duel-simulator--2026-10-04) prevalece sobre admisiones históricas más amplias. |

La operación `withdrawLeftTableMembers` y su adaptador Web existen y tienen pruebas con entradas explícitas. El adaptador no tiene llamador de producción Web: sus llamadores actuales son pruebas. La detección y captura de quién abandonó la mesa no quedan acreditadas por esas pruebas y no se trasladan a T13. Cualquier trabajo para ofrecer esa captura pertenece al Warband Manager y requiere su propio alcance.

Los totales y dictámenes de T09–T12 se conservan como evidencia histórica. T13.0 debe reconciliar las cláusulas con esta frontera y las exclusiones, sin sumar transferencias como si fueran obligaciones nuevas ni declarar completa una funcionalidad ausente. Véase el [plan de implementación](tasks/T13-implementation-plan.md).

## Estado y protocolo de trabajo

The maintained [clarification register](tasks/T13-clarifications.yaml) keeps
source interpretations and user rulings linked to original audit IDs and text
fingerprints. It is an input, never a generated report; clarification resolution
does not certify implementation. Audit/consolidation consumption remains pending.

The [remaining T13–T15 integration plan](tasks/T13-T15-remaining-plan.md) records
current routing after the accepted T13 partial deliveries, shared eligibility
extraction and implemented construction-centralization work. Its 2026-10-02 revision
replaces the historical evidence-only dispatch waves with complete functional
families; this checklist retains status and reservation authority.

The [paired-weapon milestone](tasks/T13-local-weapons.md#subsequent-l06-milestone-long-daggers-and-knuckledusters)
connects Long Daggers and Knuckledusters to canonical modular combat. F064
retains Hellblade's precise target-category prerequisite (L11 then L06); F065
retains Concealable carry/scenario clauses (shared kit and L18, reconciled L21).

Current priority: **L06** local hit/wound/parry families. Canonical Vomit Attack,
Spectral Touch, Shifty and L05 construction routes are delivered; reuse them.

L06's [first weapon block](tasks/T13-local-weapons.md) now connects eight items,
including Darksteel Blade and separately reviewed Spirit Knife/Q146, through
the shared catalogue/construction route and modular combat. L06 remains in
progress for its other admitted families; applicable ports remain L19/L20.
Its subsequent [Killing Blow milestone](tasks/T13-local-weapons.md#subsequent-l06-milestone-blood-dragon-killing-blow)
is implemented for canonical Wights/Grave Guards, with 10 focal cases and 226
affected cases passing. Reuse this delivered operator instead of redispatching it.
The [Shock Rod milestone](tasks/T13-local-weapons.md#subsequent-l06-milestone-shock-rod)
also connects canonical access, First Strike, two hands and the 1–4 stun clause.
The [Skull Busta milestone](tasks/T13-local-weapons.md#subsequent-l06-milestone-skull-busta)
adds first-turn Strength, Concussion, ordinary-helmet Basha and shared restrictions;
the user has classified Knight's Helm as a source erratum (2026-10-04).
F063 now tracks pending KB cleanup, not an L07 implementation blocker.
Then complete local families, sequences, psychology and movement, with stable
backend batches. Cases, bindings, product connection and documentation accompany
their owning implementation. F056 belongs in F008, rather than a new standalone
test/review project. If the user already launched it, preserve its reservation
and integrate the result. Centralization's F062 and Python campaign closing
fixes are implemented; subsequent shared writers need a new reservation.
F057's concrete gate repair remains reserved; optional/conditional preventive
findings are not new functional milestones. Admitted scope and final gates remain.

The remaining plan now contains **23 executable lots, L01–L23**, with scope,
prerequisites, writable responsibility boundaries and closure criteria. L01
reuses the existing F057 reservation; the implemented centralization task
is outside this count. F056's report has arrived and its review/result belongs
inside L03 Spectral activation. These sequence labels create no new finding IDs,
reservations, implementation acceptance or automatic agent launch.

Estados válidos: `pendiente`, `en progreso`, `bloqueada`, `en revisión`, `completada`. La casilla `[x]` se usa exclusivamente para `completada`; el resto permanece `[ ]`. No usar `[~]`, que no es una casilla Markdown estándar.

1. El coordinador verifica las dependencias, identifica la revisión de entrada y asigna un agente y un conjunto explícito de archivos. Anota la reserva en la tabla antes de despachar el prompt.
2. El agente lee este documento y su tarea, inspecciona instrucciones locales, rama y diff. Si el estado difiere de la entrega, informa antes de tocar archivos solapados.
3. El agente trabaja solo en los archivos asignados. Una ruta nueva o compartida necesita reasignación del coordinador; no se resuelve editando y esperando que Git lo mezcle.
4. Si necesita una decisión, registra evidencia y alternativas en su entrega. Se bloquea la unidad dependiente, no los frentes independientes. Nunca inventar reglas para cerrar un gate.
5. Al terminar entrega archivos, resultados, revisión, cambios de contrato, riesgos y tareas desbloqueadas. No marca la tarea como completada ni hace commit/push por su cuenta.
6. El coordinador pasa a `en revisión`, comprueba el lote funcional y acepta o devuelve con revisión independiente del autor para cambios semánticos o de datos. Si el coordinador no es el autor, puede realizar esa revisión proporcional sin crear otra tarea o agente; si lo es, conserva la separación de revisión exigida. No encadenar nuevas revisiones de evidencia ya aceptada sin cambio de entradas o discrepancia concreta. T14 mantiene la certificación independiente de fase.
7. Solo tras aceptar registra `completada`, evidencia y commit si existe; libera los archivos. Una modificación posterior que invalide evidencia reabre las tareas afectadas.

El coordinador revisa la entrega y reutiliza sus resultados. No repite la tarea completa: solo realiza comprobaciones puntuales cuando detecta una contradicción, falta evidencia para un criterio de cierre o existe un riesgo material no cubierto. Si hace una comprobación adicional, registra qué duda concreta resolvió.

Deferred findings discovered during T13 execution must be recorded in the
[execution follow-up register](tasks/T13-execution-follow-ups.md) before accepting
the discovering lot. Read its matching resume conditions before dispatching the
next lot; include the shared file in the reservation or deliver entries for the
coordinator to insert. The register tracks execution findings, not the full plan.

Una tarea se puede fraccionar en lotes por mecanismo dentro de su documento auxiliar, sin crear un gestor nuevo. Cada lote tendrá responsable, entradas, archivos, prueba de cierre y estado. Si se necesita otro agente para un lote, se usa el mismo prompt con esos parámetros concretos, conservando las restricciones de la tarea madre.

### Tabla de reservas activas

External dispatches prepared on 2026-10-02; the user launches these agents.
Each executor captures actual dirty-tree hashes before starting and writes only
the paths reserved below. Read-only reviews and reconciliation lots preserve
all existing production inputs; implementation lots retain their explicit scope.

Latest modular continuation (2026-10-04): [individual Cold-Blooded](tasks/T13-local-modifiers-defences.md#l10-continuation--individual-cold-blooded-tests)
adds three canonical clauses (152 cumulative). Six focused cases and affected
contracts pass; group Rout is excluded under the user's 1v1 boundary.

| Review lot | Reserved executor | Exclusive writable outputs | Status and acceptance boundary |
|---|---|---|---|
| Semantic study A — analysis and modular implementation of offensive families | External agent A; user launches; implementation explicitly requested 2026-10-07 | Isolated checkout reproducing the current dirty inputs only: tasks/T13-semantic-analysis-dispatch/A-results.csv; A-family canonical KB and exact staging mirrors, execution/mapping contracts, necessary construction/transport/modular consumers, directly affected cases and maintained generator outputs. No writes to the shared checkout; patch and optional scratch in ignored build/audit/semantic-analysis/A/** of the isolated checkout | Reserved, pending user launch. 558 closed input IDs under the [manifest](tasks/T13-semantic-analysis-dispatch/manifest.json) and [guide](tasks/T13-semantic-analysis-guide.md). This user-authorized A dispatch extends the guide's analysis-only restriction inside the isolated checkout; B/C/D retain their read-only reservations. Complete source-resolved admitted effects by semantic family, preserve scope decisions and input fingerprints, and report genuinely blocked clauses without inventing rules. Coordinator integrates the isolated delivery; no vectorized/native ports, shared-register edits, phase certification, commit/push or nested agents |
| Semantic study B — defences, injury and recovery | External agent B; user launches | Only tasks/T13-semantic-analysis-dispatch/B-results.csv; optional ignored scratch build/audit/semantic-analysis/B/** | Reserved 2026-10-07, pending user launch. 565 current input IDs under the same manifest/guide; own all assigned clauses, including references. Analysis and implementation/evidence states remain separate; the same read-only boundaries apply |
| Semantic study C — psychology, Leadership and temporary states | External agent C; user launches | Only tasks/T13-semantic-analysis-dispatch/C-results.csv; optional ignored scratch build/audit/semantic-analysis/C/** | Reserved 2026-10-07, pending user launch. 881 current input IDs under the same manifest/guide; mixed LATER clauses require individual scope review, not admission of excluded producers. The same read-only boundaries apply |
| Semantic study D — construction, recipients, characteristics and mixed clauses | External agent D; user launches | Only tasks/T13-semantic-analysis-dispatch/D-results.csv; optional ignored scratch build/audit/semantic-analysis/D/** | Reserved 2026-10-07, pending user launch. 1,587 current input IDs under the same manifest/guide; respect the shared eligibility decision and distinguish legality, acquisition and duel effects. The same read-only boundaries apply |
| Autonomous modular continuation — L06–L18 | Coordinator; user requested autonomous execution, 2026-10-04 | Source-backed local family KB/mirrors, compiler/core/modular context/state/resolvers, shared eligibility only for reproduced access gaps, affected canonical product seams, focused family cases and coordination; preserve independently reserved files | In progress. [249-clause local attack/save/injury/resource/Leadership/Fear milestones](tasks/T13-local-modifiers-defences.md) implemented, including conditional ward, recursive Onslaught, Crude Belch, the Priest's final bite, Sabretusk charge count, one chosen Seaguard reroll, local Leader providers, Darksoul auto-pass and both Fear charge outcomes; High Elf skill tables corrected and F022 resolved locally. F061/F067 retain their explicit remaining boundaries. Common Fear now has 97 canonical connections, acquired/current-condition and item routes; F070 retains conditional producers. Stupidity static grants, acquisition and prior-history UI are complete; F071 is resolved. Four additional innate Frenzy grants and selectable Unlimited Hatred reuse the existing operators. Six opposed Elven Hatred clauses now use explicit individual identities, animal exclusions and editor overrides. Source-specific Stubborn/Barbarian Courage rerolls and Fearless/Iron Will immunity are implemented. Document deferred issues and continue remaining modular work; stop before L19/L20, no vectorized/native ports or automatic agent launches |
| L06 — local weapons and attack modifiers | Coordinator, user requested continuation 2026-10-03 | Canonical item/mechanic/mapping blocks; shared eligibility recipients and generated bundle for reproduced item-access gaps; modular/kernel support seams as required; focused canonical cases and existing coordination. External L02–L05 review uses its captured read-only revision | In progress; [eight-item weapon block](tasks/T13-local-weapons.md) implemented/verified: F023 and separate F025/Q146, five profiles, real catalogue/attacks, 15 focal cases plus reused affected checks. Continue other L06 families. Preserve F057 and user UI/i18n work; no optimized certification, agent launch, commit or push |
| L05 — canonical choices and grants | Coordinator; user requested execution, 2026-10-03 | Shared eligibility/bridge and maintained generated bundle; actual construction/core/catalogue adapters; source-backed recipient/binding/marker corrections in affected canonical bands and exact staging mirrors; pertinent editorial schema/loader contract; focused direct/embedded/canonical specs and tests; T13 coordination/eligibility reference and new canonical-choices delivery; own evidence canonical-choices/** and sanctioned publication | Implemented/verified; reservation released 2026-10-03. [Delivery](tasks/T13-canonical-choices.md): named tables, configured promoted Shifty/Runts, active versus owned kit and truthful markers. Remaining F018/F028 source/effect gates have named owners; visible new facts remain L18. F057, accepted engine and concurrent WB UI/i18n preserved; no new constructor, agent launch, commit or push |
| L04 / F004 — canonical Shifty | Coordinator; user explicitly requested execution, 2026-10-03 | Halflings special-rules.yaml (Shifty metadata only) and exact 2A mirror; close-combat/execution mechanic entries; kernel optimized support guard and verification tag-consumer declaration; new modular/test_shifty_activation.py and source-linked grants/t13-halfling-shifty.yaml; existing Shifty canonical assertions; concrete catalogue/selectable/structural inventory assertions and trace notes (supplemental entry bytes captured); existing Shifty delivery and pertinent README/T13/follow-up/remaining-plan coordination; own shifty-activation/** evidence and sanctioned publication | Four-hero canonical modular milestone implemented/verified; reservation released 2026-10-03. [Delivery](tasks/T13-shifty.md#l04-canonical-activation--2026-10-03): 35 canonical/84 focal/926 affected cases; 11 source-linked cases/3 mutations; 720 obligations, 569 verified/151 pending, same 30 historical errors. Accepted S1–S4/F060/shared construction unchanged. F004 promoted local access remains L05, pistols L08, ports L19/L20 and GUI routing L18; no phase certificate, agent launch, commit/push |
| L03 / F008/F056 — canonical Spectral Touch | Coordinator; user requested next difficult/planned T13 lot on 2026-10-03 | Night Haint special-rules.yaml and exact 2B mirror (Spectral flag only); construction/contracts.py and compiler.py (trait transport); kernel.py (optimized support guard); new modular/test_spectral_touch_activation.py and source-linked grants/t13-spirit-host-spectral-touch.yaml; existing Spectral suite's canonical pending assertion and campaign construction-tables.json/one TS status test reconciled (supplemental entry captured); existing Spectral delivery and F056 acceptance appendix; pertinent README/T13/follow-up/remaining-plan coordination; own evidence spectral-touch-activation/** and sanctioned publication | Implemented/verified, reservation released 2026-10-03. [Canonical modular delivery](tasks/T13-spectral-touch.md#l03-canonical-activation--2026-10-03): F008 delivered and F056 accepted; 891 affected/24 dependency/34 TS cases pass, 10 spec cases/4 detected mutations, exactly one new verified target with same 30 historical source errors. Accepted engine/shared eligibility/F056 test unchanged. Optimized effect explicitly refused until L19/L20; no T14/GUI optimized certificate, commit/push or agent launch |
| L02 / F010 — canonical optional Vomit Attack | Coordinator; user requested continued T13 implementation on 2026-10-03 | core/models.py; construction/compiler.py; modular/rounds.py, pools.py and the narrow attacks.py Bull Charge guard; kernel.py and narrow optimized entry refusal in vectorized/_driver.py and native/_combat_compile.py; focused canonical/modular cases, existing selectable matrix and source-linked spec; pertinent README/follow-up/remaining-plan coordination; tasks/T13-vomit-attack.md and own evidence vomit-attack/** | Implemented/verified 2026-10-03; reservation released. [Canonical modular delivery](tasks/T13-vomit-attack.md): 16 strict cases, 868 affected cases, 43 focal semantic cases/mutations and 70 dependency cases pass. Full verify: 566 verified / 152 pending, exactly 30 inherited source errors; 7 new cases / 4 detected mutations. Optimized optional choice explicitly refused until L19/L20; no GUI/T14 certificate, agent launch, commit or push |
| Construction centralization closing fixes / F062 | Coordinator; user requested implementation on 2026-10-03 | Shared eligibility index.ts/bridge.ts and generated bundle; Python eligibility transport; campaign knowledge_port.py/post_battle_engine.py; focused direct/embedded/campaign cases and fixture; pertinent existing coordination/reference docs; own evidence construction-centralization-fixes/** | Implemented/verified 2026-10-03; reservation released. Original544 false issues become0; final/draft and actual selected/owned controls pass. Python table retired with77 captured entry cases;1881 affected Python and466 TS cases pass, bundle/typechecks green, F017/F019 preserved. Existing unrelated workspace failures and T13 canonical/mechanism/backend work remain separate. No agent launch, commit or push |
| Shared construction documentation reconciliation | Coordinator, user explicitly requested all documentation/plan updates | Relevant docs/reference and docs/guides; docs/README.md; initiative README; task plans reviewed and affected historical construction/pilot deliveries; own evidence shared-eligibility-documentation/**. External executors' new reports and all production/test/data files remain read-only | Completed/released 2026-10-02; 32 documents reconciled, links/whitespace checks pass, 18 historical bodies preserved and 1,963 protected inputs unchanged. No implementation or F035 closure asserted |
| F035 — current shared-eligibility reconciliation | External executor; coordinator independent review | New tasks/T13-shared-eligibility-reconciliation.md and .csv; new tests/typescript/domain/t13-shared-eligibility-reconciliation.test.ts; external evidence shared-eligibility-reconciliation/** and coordinator evidence f035-coordinator-review/**. Existing production/data/test inputs read-only; coordinator updates plan/ledger and appends acceptance | Accepted/released 2026-10-02 as 47-clause reconciliation. Fresh bundle/27 TS/21 embedded cases pass; direct and embedded witnesses reproduce F017's 20 recipient violations and F019's specialized-stage hole. F004/F016–F021/F028 remain open with corrected scope/owners; F020/F021 and configured Bloodline effects retain admitted scope. No production repair or T13.2 certification; F057 reservation preserved |
| F007 — Spectral Touch independent review | External reviewer A, different from the modular implementer; coordinator accepted | tasks/T13-spectral-touch-independent-review.md; evidence build/cache/t13-parallel/spectral-touch-independent-review/** and spectral-touch-coordinator-acceptance/** | Accepted 2026-10-02 for modular oracle; reservation released. R1–R4 implementation/repair independently reviewed; 15 input hashes and 101/432 retained passes checked, fresh strict/mutation probes pass. F056 records the mixed-provenance maintained-witness gap; F008/F009/F040 remain separate |
| F040 — coverage independent review | External reviewer B, different from the gate implementer; coordinator accepted | tasks/T13-coverage-independent-review.md; evidence coverage-independent-review/** and coverage-coordinator-acceptance/** | Accepted 2026-10-02 for reviewed reconciliation/fail-closed repair; reservation released. 52 fresh focal tests pass; historical522 gate not current; F057 owns3758-vs3743 parity blocker, optional F058/F059 recorded; concurrent audit CLI edits preserved outside acceptance |
| F003 — Shifty independent decision review | External reviewer C, different from the pilot/dossier author; coordinator checked and user accepted S1–S4 | tasks/T13-shifty-independent-review.md; evidence build/cache/t13-parallel/shifty-independent-review/** | S1–S4 explicitly accepted by the user on 2026-10-02; F003 resolved for reviewed modular behavior, reservation released. 19 manifest pairs/report hash current; retained 101 focal tests and 12 explicit probes valid. F004 activation/F035 proof, F005/F026 pistols, F006 ports and F060/F061 retain separate boundaries |
| Shifty coordinator integration | Coordinator, independent external handoff received | Pertinent README/follow-up/remaining-plan coordination and corrections/current review note in tasks/T13-shifty-review.md; own evidence shifty-coordinator-review/**. Incoming independent report/evidence and production inputs remain read-only | Completed 2026-10-02; research/evidence accepted, source facts corrected and follow-ups assigned. No semantic self-acceptance, activation, port, code/test/KB/spec change, commit/push or agent launch |
| F057 — parity inventory count and current read-only gate | External implementation executor; user launches | Only tests/python/verification/test_parity.py; new tasks/T13-parity-inventory-count.md; evidence build/cache/t13-parallel/parity-inventory-count/** | Reserved 2026-10-02, awaiting user launch; reconcile exact15 new source-linked cases and repair count/completeness expectation; retain all result checks; no engine/spec/source/budget/shared-doc changes or live update; fresh full gate required, unrelated failures returned to coordinator |
| F017 — shared band-rule recipient filtering | External implementation executor; coordinator independently reviewed | Narrow `applicableRules` repair in index.ts and generated Python bundle; new direct/embedded tests and shared fixture; tasks/T13-band-rule-recipients.md; external evidence band-rule-recipients/** and coordinator evidence band-rule-recipients-coordinator-review/**. bridge.ts and other production/data inputs preserved; coordinator appends acceptance and updates routing | Accepted/released 2026-10-02; F017 resolved. Exact source inversion, current bundle, fresh40 TS/47 Python, unchanged reproducer20→0 and30 independent witnesses with removal/OR detection. F016 recipient prerequisite satisfied; F016 route/mechanics and F019 stage remain pending. Next shared writer requires a new exclusive reservation; no visible-flow/T14/T13.2 certificate, commit/push or agent launch |
| F019 — The Silence equipment-token integration | External implementation executor; coordinator independently reviewed | Narrow specialized bound-equipment integration/fact contracts in packages/typescript/domain/eligibility/index.ts and bridge.ts if needed; Python eligibility.py catalogue/context transport; restrictions.py only root/context forwarding with no new decisions; generated _eligibility.js via maintained builder. New tests/typescript/domain/silence-equipment.test.ts, tests/python/construction/test_silence_equipment.py, optional tests/fixtures/eligibility/silence-equipment.json; new tasks/T13-silence-equipment.md; evidence build/cache/t13-parallel/silence-equipment/** | Accepted/released 2026-10-02; F019 resolved via [independent coordinator acceptance](tasks/T13-silence-equipment.md#10-independent-coordinator-acceptance--2026-10-02). Unchanged reproducer exits0 with the stage-attributed refusal (before1); fresh7 TS/8 Python/489 construction cases pass, only the four authorized files drifted and the bundle is current. Animal decision+boundary proved with no admitted construction route; crossbow path remains latent. F016/F020/F021 remain open; next shared writer requires a new exclusive reservation; no visible-flow/T14/T13.2 certificate, commit/push or agent launch |
| F060 — Shifty poisoned-hand maintained witnesses | External test executor delivered; coordinator independently reviewed | New tests/python/combat/modular/test_shifty_poison_transport.py and tasks/T13-shifty-poison-transport.md; own delivery evidence shifty-poison-transport/**; coordinator evidence shifty-poison-transport-coordinator-review/** | Accepted/resolved 2026-10-02; reservation released. Five strict real-pipeline cases, fresh 106 focal passes, seven isolated mutations detected at contract checks; independent nominated weapon/clean-pair/slot projections pass both directions. Synthetic compiled inputs, no construction dependency or production change. Canonical activation, other poisons, ports, F061 and concurrent construction centralization retain separate ownership; no commit/push or agent launch |
| F056 — Spectral Touch mixed-hit provenance witnesses | External report present; coordinator acceptance completed within F008/L03 | Only new tests/python/combat/modular/test_spectral_touch_provenance.py and tasks/T13-spectral-touch-provenance.md; own evidence build/cache/t13-parallel/spectral-touch-provenance/**. Existing tests, engine, models, KB, construction, eligibility and shared documents read-only | Accepted within delivered [F008/L03](tasks/T13-spectral-touch.md#l03-canonical-activation--2026-10-03) on 2026-10-03; reservation released, reuse maintained synthetic and canonical mixed-hit witnesses. The canonical modular delivery leaves the six external cases unchanged. F009 ports, F057's count reconciliation and T14 retain separate ownership. No duplicate test-only or review dispatch, new production authority, commit/push or agent launch |

Read-only reviewers and reconciliation executors do not edit this README, the
follow-up register, prior deliveries, maintained tests, sources, specifications,
code or budgets. Implementation rows authorize only their listed production/test
paths; F017 explicitly permits the shared predicate repair and generated bundle.
All new findings are delivered as proposed register entries for the coordinator.

Entrada histórica de los pilotos Shifty/Spectral Touch: `1b7f7cf` + entrega T13.1 aceptada, sin commit;
diff de entrada identificado en `build/cache/t13-parallel/entry-files.json`.

For new lots, record the actual working-tree inputs as well as HEAD. The user
launched external A/B before these rows were recorded; their dispatched file
permissions are now registered below. Each agent captures its own entry hashes.

| Tarea/lote | Agente | Revisión de entrada | Archivos reservados | Inicio UTC | Estado/última entrega |
|---|---|---|---|---|---|
| T13.4a — ataque adicional de Shifty | Coordinador | `1b7f7cf` + T13.1 | README; tasks/T13.md; tasks/T13-shifty.md; packages/python/combat-engine/mordheim_combat/modular/rounds.py y pools.py; tests/python/combat/modular/test_shifty.py; evidencia build/cache/t13-parallel/shifty/** | 2026-09-30 | Contrato modular aceptado tras revisión independiente y aceptación humana S1–S4, 2026-10-02; F003 resuelto en ese alcance. Activación canónica, pistolas y portes pendientes; sin promoción KB |

| T13.3a — Spectral Touch | Coordinador | `1b7f7cf` + T13.1/T13.2a + Shifty en revisión | README; tasks/T13.md; nuevo tasks/T13-spectral-touch.md; modular/attacks.py, state.py y pools.py (preservando Shifty); nuevo tests/python/combat/modular/test_spectral_touch.py; evidencia build/cache/t13-parallel/spectral-touch/** | 2026-09-30 | En revisión; contrato Q019 propuesto y mecanismo modular en tasks/T13-spectral-touch.md; sin promoción KB ni portes |

| R1 — Spectral Touch / Q019 human review dossier | Coordinator, requested by user | `1b7f7cf10b75a9d716c34c64039f5c908caed19e` + dirty inputs captured in spectral-touch-review/entry.json | New tasks/T13-spectral-touch-review.md; pertinent coordination only in README, tasks/T13.md and tasks/T13-execution-follow-ups.md; evidence build/cache/t13-parallel/spectral-touch-review/** | 2026-10-01 08:13 UTC | Human accepted R1–R4 on 2026-10-01; historical 93 pre-repair passes; subsequent modular repair delivered in the next row, F007 implementation review pending; no canonical activation or port |
| T13.3a — accepted R4 Barrage repair | Coordinator implemented; external reviewer A independently reviewed | `1b7f7cf` + captured dirty inputs in spectral-touch-barrage-repair/entry.json | modular/attacks.py; test_spectral_touch.py; existing Spectral delivery/review, Q019 inventory and permanent design ruling; pertinent README/T13/follow-ups coordination; evidence build/cache/t13-parallel/spectral-touch-barrage-repair/** | 2026-10-01 | Modular implementation accepted 2026-10-02; reservation released. Historical 215 focused/405 broad preserved by independent 101 focused/432 broad evidence and coordinator spot checks. F056 test witness remains open; F008/F009 separate, external specs protected |
| R0 — translation-only source pins | External executor; user launches | `1b7f7cf` + working-tree spec hashes in tasks/T13-translation-pin-manifest.json | Only the 300 sources[].digest pairs in the read-only manifest (104 spec files); new tasks/T13-translation-pins.md; evidence build/cache/t13-parallel/translation-pins/** | 2026-10-01 | Accepted 2026-10-01 after independent coordinator spot checks: 300/300 registered pins equal the live fingerprint, 0 blocked, diff limited to the authorized digest lines in 104 files; fresh verify 455 -> 155 (300 removed, 0 added), structural green; reservation released. No other spec fields, tool edits, KB, engine or shared-document writes |
| F040 — modular coverage reconciliation | Coordinator implemented; external reviewer B independently reviewed | `1b7f7cf` + coverage-reconciliation/entry.json hashes | Existing verification/coverage_gate.py, narrow CLI coverage handler in cli/commands.py and tools/mordheim-utils.py deterministic scope, test_coverage_gate.py and tests/fixtures/coverage/budget.json; modular/test_t13_coverage_boundaries.py; tasks/T13-coverage-reconciliation.md and pertinent coordination; evidence coverage-reconciliation/** | 2026-10-01 | Repair accepted 2026-10-02 at reviewed revision; reservation released.647 original requirements preserved, trustworthy measurement/writers independently proved,52 focal tests pass again.Historical522 full result is stale; current gate refuses3758-vs3743 parity failure under F057.Budget unchanged; no current gate/semantic/canonical/optimized/T14 certificate |
| R0 — context-data evidence review | External executor; user launches | `1b7f7cf` + read-only tasks/T13-context-data-manifest.json, SHA256 `86aa8194f1d96ca5d616ab2b26ac8fe930322902a49a82748f5d930f101357cd` | Read-only 125 manifest pairs and canonical/consumer inputs; write only new tasks/T13-context-data-review.md and tasks/T13-context-data-review.csv; evidence build/cache/t13-parallel/context-data-review/** | 2026-10-01 | Accepted as bounded research after coordinator spot checks on 2026-10-01; 125 pairs revalidated, 29 restriction deletions in19 profiles, five independent compile probes agree, bundle freshness green; current deduplication retained, exact 125-pair pin-only lot eligible for separate dispatch; F041 tracks unexecuted presentation audit, F001/F035 open; reservation released, no pins/product changes |
| R0 — context-data coordinator review | Coordinator, external handoff received | `1b7f7cf` + context-data-coordinator-review/entry.json | Pertinent README/F001/F035 and new follow-up routing; append review to tasks/T13-context-data-review.md; evidence build/cache/t13-parallel/context-data-coordinator-review/**; CSV/manifest/specs/KB/code read-only | 2026-10-01 | Completed research acceptance/routing; checks in context-data-coordinator-review/coordinator-review.json, decision in tasks/T13-context-data-review.md section11; F001 retains 155 residual pins, F035/F040 unchanged and F041 assigned to T15; no pin refresh, product fixes, phase closure, commit/push or agent launch; review reservation released |
| R0 — context-data source pins | External executor; user launches | `1b7f7cf` + read-only tasks/T13-context-data-manifest.json SHA256 `86aa8194f1d96ca5d616ab2b26ac8fe930322902a49a82748f5d930f101357cd`; all 48 entry_spec_sha256 values rechecked at dispatch | Only the 125 sources[].digest scalar values located by manifest (spec_file, specification, target); new tasks/T13-context-data-pins.md; evidence build/cache/t13-parallel/context-data-pins/**; manifest/review/CSV/KB/code/shared-docs read-only | 2026-10-01 | Accepted 2026-10-01 after independent coordinator reconstruction from pre-dispatch-hashed backups:48 files,125 exact digest changes, exact byte inversion;125 fresh fingerprints match;300 translation and 30 historical pins preserved;fresh verify155->30 with exact identities and 0 added;structural green1050;F001 remains open for 30 historical pairs,F035/F040/F041 unchanged;reservation released;no product edits,commit/push or agent launch |
| R0 — context-data pins acceptance | Coordinator, external delivery received | `1b7f7cf` + context-data-pins-coordinator-review/entry.json | Only pertinent README/F001 and acceptance appendix in tasks/T13-context-data-pins.md; evidence build/cache/t13-parallel/context-data-pins-coordinator-review/**; all specs/KB/code/manifests/CSV and prior agent evidence read-only | 2026-10-01 | Completed acceptance; independent-review.json and fresh-verify-check.json retain proof;exact 125 digest-only changes in 48 files accepted,425 reviewed pins now current;F001 retains30 historical pairs;only coordinator docs changed,no pin/product edits,phase closure,agent launch,commit or push;reservation released |
| R2/R3 — Fimir and Boglar save thresholds | External implementation executor; coordinator reviewed | `1b7f7cf` + dispatch/independent-review.json hashes | Narrow compiler.py override; canonical and sources/2B mirrors for band--scaly-skin and boglars--regeneration; new construction/test_t13_profile_save_thresholds.py, modular/test_profile_save_thresholds.py, two source-linked specs and tasks/T13-profile-save-thresholds.md | 2026-10-01 | Accepted for canonical construction and modular saves after independent review; F011/F012 resolved locally; 65 construction/modular/promotion and 15 semantic cases passed; six canonical controls and 16 parameter probes passed; fresh verify retains exactly30 historical errors, structural green1050; two staged mirrors explicitly accepted as necessary scope expansion; F042–F047 retain inherited gates and fire-spell proof; reservation released, no optimized-port or phase certification |
| R0 / F042–F043 — catalogue contract repair | External implementation executor; coordinator reviewed | `1b7f7cf` + dispatch and independent-review.json hashes | Narrow catalogue-test/helper repair; only EN/ES Human-reference text in canonical sisters-of-sigmar/special-rules.yaml; new knowledge/test_catalogue_contract_regressions.py and tasks/T13-catalogue-contracts.md | 2026-10-01 | Accepted at catalogue-contract boundary; F042/F043 resolved and reservation released; independent reconstruction matches dispatch backups, source/AST scope exact, four protected inputs restored/unchanged;63 tests and seven invalid-shape probes passed;fresh verify retains30 historical errors/565 verified/153 pending,structural green1050;generator check and published EN/ES note probe pass;F048 product proof and F049 isolated mutation replay remain open;no engine/eligibility/spec/pin changes or phase closure |
| R0 / F044 — equipment-access schema contract | External implementation executor; independent coordinator review completed | `1b7f7cf` + equipment-access-schema-dispatch/entry.json and immutable backup hashes | equipment-access schema and its contract README; narrow exact-declaration justifications/guards in editorial_schema_audit.py; relevant test_editorial_schemas.py cases; new knowledge/test_equipment_access_schema_contract.py, TypeScript application/rules/equipment-access-contract.test.ts and tasks/T13-equipment-access-schema.md; evidence build/cache/t13-parallel/equipment-access-schema/** | 2026-10-02 | Accepted at local equipment-access contract boundary; reservation released. Supported declarations retained with exact member mappings; fresh 316 Python / 2 new TypeScript tests pass, strict audit 40 findings / 0 hard-unjustified-stale, 705 protected/KB hashes intact. F050 tracks EN/ES raw reference regression; F051 tracks inherited shared-definition pooling. No product/phase closure, commit/push or agent launch |


Parallel external dispatches prepared on 2026-10-02 (user launches both agents):

| Lot | Reserved executor | Owned implementation and delivery paths | Protected boundary | Status |
|---|---|---|---|---|
| F050 — localized reference citations | External agent A; coordinator independently reviewed | Narrow read-model composition in rules-catalogue.ts, catalogue-text.ts and new reference-citations.ts; strengthened/new TS and rendered reference tests; tasks/T13-reference-citations.md; evidence reference-citations/** and reference-citations-coordinator-review/** | Canonical citations/701 source hashes, accepted F051 auditor, warband-reference.ts, reader seams, generator and reference components preserved; two executor closing checksums superseded by independent actual-byte hashes | Accepted 2026-10-02 for current published parenthesised racial-maximum citations; F050 resolved, reservation released. Fresh 36 TS/10 rendered/21 distance/4 independent probes and both typechecks/generator pass; F053 future grammar, F054 reader duplicate identities and F055 six inherited static findings remain open; T15/static gate not closed, no commit/push or agent launch |
| F051 — shared schema evidence pooling | External agent B; coordinator independently reviewed | Narrow editorial_schema_audit.py pooling repair; new knowledge/test_shared_schema_evidence.py; new tasks/T13-shared-schema-evidence.md; evidence build/cache/t13-parallel/shared-schema-evidence/** and shared-schema-evidence-coordinator-review/** | Accepted F044 local mappings, other justifications and protected inputs preserved; concurrent F050 TypeScript test edit observed and excluded from this acceptance; contract README example corrected separately by coordinator after boundary check | Accepted 2026-10-02; F051 resolved, reservation released. Global evidence removes exactly the false rule_runtime.grant finding and its obsolete justification; remaining 39 full records unchanged, 27 fresh focal tests pass. F052 CLI output remains open; no phase closure, commit/push or agent launch |

F052 external delivery independently accepted on 2026-10-02; reservation
released. Reviewed paths are
`tools/knowledge/audit_schema_strictness.py`, new
`tests/python/knowledge/test_schema_strictness_cli.py`, new
`tasks/T13-schema-strictness-json.md` and evidence under
`build/cache/t13-parallel/schema-strictness-json/**`. Structured JSON members
are accepted with preserved text, fields, filters, counts and exit behavior.
Independent exact one-line inversion, 29 fresh tests and real CLI JSON/text
checks pass; the auditor retains 39 findings. Accepted F044/F051 auditor/tests,
contracts, canonical/staged sources and specifications/pins are preserved.
TypeScript/Web/F050 is outside the CLI lot; coordinator records are updated
separately by the reviewer.
Status: F052 resolved; no phase closure, commit/push or agent launch.

Current strictness state after [F051 acceptance](tasks/T13-shared-schema-evidence.md#12-independent-coordinator-acceptance--2026-10-02):
39 findings, zero hard/unjustified/stale. The F044 row's 40 is its historical
acceptance result; F051 removes one independently proved false finding. The two
local F044 member mappings and the other findings are unchanged.

Current review reservation, 2026-10-01: the user requested the coordinator's
Shifty semantic dossier. Owned outputs are new `tasks/T13-shifty-review.md`,
evidence under `build/cache/t13-parallel/shifty-review/**`, and pertinent
coordination in this README, `tasks/T13.md` and the execution follow-up register.
Entry: `1b7f7cf` plus dirty inputs captured in `shifty-review/entry.json`.
External A/B ownership is preserved. No engine, canonical data, existing test,
specification, port, commit or push is authorized by this review reservation.
Delivery: [Shifty review dossier](tasks/T13-shifty-review.md) prepared with
source/general/project distinctions and human decisions S1–S4. Focused run:
93 passed (44 Shifty + 49 Spectral Touch), real XML retained. F003 stays in
review; F004–F006 remain blocked. The pistol-only limitation is not a tabletop
ban; accepting its interim boundary would not close F005/F026.

Current Shifty review disposition, 2026-10-02: the
[independent decision package](tasks/T13-shifty-independent-review.md) is integrated
after coordinator checks and fresh 101 focal passes/12 probe reproductions.
The user explicitly accepted S1–S4; F003 is resolved for the reviewed modular
contract, recorded in the [permanent ruling](../../decisions/design-rulings.md#shifty-s1s4)
and [acceptance record](tasks/T13-shifty-review.md#human-acceptance--2026-10-02).
The canonical rule already targets four
Heroes; F004 now distinguishes that fact from the missing selectable grant/kind,
binding and executable status. F060's maintained Spider Spittle witnesses are
independently accepted/resolved ([acceptance](tasks/T13-shifty-poison-transport.md#9-independent-coordinator-acceptance--2026-10-02)); F061 retains
the Halfling Crude Belch first-attack-loss contract. The external review reservation
is released. The accepted interim pistol-only refusal does not close F005/F026;
F004 activation, F006 ports, F035 proof and F061 remain separate. Human
acceptance records the contract and starts no implementation lot automatically.

Current Spectral Touch disposition, 2026-10-02: R1–R4 source interpretations
accepted by the user; the [modular R4 repair](tasks/T13-spectral-touch.md#accepted-r4-modular-repair--2026-10-01)
is implemented and verified. Seven strict pre-repair failures; 215 focused and
405 broad passes. F007 is resolved for the modular oracle after
[independent review and acceptance](tasks/T13-spectral-touch-independent-review.md#13-coordinator-acceptance--2026-10-02).
L03 update, 2026-10-03: [canonical grant/specifications](tasks/T13-spectral-touch.md#l03-canonical-activation--2026-10-03)
are delivered (F008), with F056's maintained mixed-provenance witness independently
accepted in the same lot. F009 ports remain scheduled for L19/L20; the unported
effect is explicitly refused on optimized entries. The modular source contract
and engine retain their accepted semantics.
The permanent Q019 answer is recorded without editing source/specification pins.
The external translation-only pins were delivered and accepted separately; the
Shifty review retains separate ownership.

L03 supplemental scope, captured before editing on 2026-10-03: the closed
`profiles.yaml.schema.json` admits the same `spectral_touch: boolean` as the
compiler registry. The maintained strict parity gate passes (305 schema cases);
strictness remains 39 justified / zero hard-unjustified-stale. Schema/source
status reconciliation introduces no new eligibility rule or audit waiver.

R0 translation-only source pins accepted on 2026-10-01 after independent
coordinator spot checks; [delivery, proofs and limits](tasks/T13-translation-pins.md)
and retained `build/cache/t13-parallel/translation-pins/coordinator-review.json`.
All 300 registered pairs equal the live maintained fingerprint; the diff is
exactly the authorized digest lines in the 104 manifest files (300 changed
lines, nothing else, with the accepted Bloated Foulness diff preserved). A fresh
semantic run removes exactly those 300 error identities (455 -> 155, 0 added);
the residual 155 are the 125 context-data and 30 pre-snapshot classes, and the
structural layer stays green. The focused suite moved 4 failed -> 1 failed; the
remaining identity is the inherited `test_structural_success_is_not_semantic_success`
on those residual pins. T13-F001 stays open; reservation released. No rule, KB,
engine, tool or shared-register change.

R0 context-data source pins accepted on 2026-10-01;
[independent acceptance and limits](tasks/T13-context-data-pins.md#9-independent-coordinator-acceptance--2026-10-01).
Independent reconstruction from manifest-hashed originals proves exactly 125
hexadecimal pin changes in 48 files and byte-exact inversion. All 125 fresh
fingerprints match;300 accepted translation pins and 30 historical pins remain
intact. Fresh verify reproduces exactly 30 historical errors (155 ->30,125
removed,0 added), with structural success on 1050 profiles. F001 stays open for
those 30;F035,F040 andF041 retain their own gates. No pin/product edits,commit,
push or agent launch by the coordinator;reservation released.

R0 context-data research accepted on 2026-10-01 after independent checks;
[delivery and class disposition](tasks/T13-context-data-review.md#11-coordinator-acceptance-and-class-disposition--2026-10-01).
All 125 fingerprints/pins revalidated; independent context diff confirms only
29 non-i18n restriction deletions in19 profiles. Five canonical compile probes
agree across historical/live data; bundle freshness passes. Retain reviewed
structured-rule deduplication. G1/G2 are eligible for a separately dispatched
exact 125-pair pin-only refresh after revalidation; no pin changed here. F001's
155 residual pins and F035 remain open; F041 routes unexecuted EN/ES restriction
presentation checks to T15. F040 remains separately in review. Reservation released.

T13.2a aceptada el 2026-09-30 tras revisión del coordinador de la entrega externa;
[contrato, decisiones y evidencia](tasks/T13-characteristic-bonuses.md). Reserva liberada.
T13.2b aceptada el 2026-10-01 como corrección de Movimiento compilado de Bloated
Foulness; [revisión, decisiones y límites](tasks/T13-bloated-foulness.md). Reserva liberada.
T13.2d accepted on 2026-10-01 as traceability and construction-test coverage;
[coordinator review and limits](tasks/T13-selectable-equipment.md). Reservation
released. The 149 assigned origins are retained; two adjacent provenance rows
are explicit. Vomit Attack's missing projection remains open; no fix was started.
T13.2c accepted on 2026-10-01 as automatic-grant traceability and construction-test
coverage; [coordinator review and limits](tasks/T13-automatic-grants.md).
Reservation released. All 829 origins retained; combined T13.2c/T13.2d and
documentation run: 145 passed. Value mismatches and marker inconsistencies remain
open; no mechanic fix or structural-contract extension was started.
T13.2 sigue en progreso; queda la reconciliación de Iron Sinews y las restantes
obligaciones de concesión/destinatarios, sin certificar la fase completa.

R2 hireling/command traceability accepted on 2026-10-01 as bounded integrity and
representation evidence; [coordinator review](tasks/T13-hirelings-commands.md).
All 67 origins retained (62 hireling + 5 commands); input/evidence hashes and
external XML results 143/14/15/1 inspected and reused. Coordinator independently
checked the partition and Aldred's three missing starting skills. T13-F036–F039
record access, reference, alias and Q158 handoffs. Route absence does not exclude
included combat clauses. Reservation released; T13.2 remains in progress, with
no construction, command or backend certification and no production edit/commit/push.

R0 source/fingerprint investigation accepted on 2026-10-01;
[coordinator dispositions and proof](tasks/T13-source-fingerprint-review.md).
All 455 pairs independently checked: 300 translation-only, 125 context-data,
30 pre-snapshot; working/committed KB agree. The 580-row matrix is retained.
F001 remains open with three separately gated review/repair classes; no pins
were refreshed. F027 resolved because canonical shared references supply the
text, without certifying variants or combat. Four fresh semantic failures match
T13.1's four semantic failures; its fifth audit test was outside this run and
remains unvalidated here. Name-only cross-references are not consolidated.
External A reservation released; R0 eligibility revalidation/F035 and T13 remain
in progress. No production edit, agent launch, commit or push.

T13.0 aceptada el 2026-09-30; archivos de documentación y evidencia liberados.
T13.1 aceptada sobre `1b7f7cf`, el commit que recoge los cambios paralelos del usuario.
[Contratos, revisión independiente y evidencia](tasks/T13-contracts.md); archivos liberados.
Estos cambios no pertenecían a la reserva de T13.0.

Ampliación de reserva T13.1: `packages/python/core/mordheim_core/context.py`;
`packages/python/roster-construction/mordheim_construction/selection.py`;
`packages/python/combat-engine/mordheim_combat/native/_combat_compile.py`;
`apps/combat-lab/mordheim_combat_lab/application/analyses.py` (conservación de
características al incrementar atributos); módulo de replay en
`apps/combat-lab/mordheim_combat_lab/verification/parity/`. Los archivos C
generados y la extensión se regeneran con el procedimiento existente, sin
edición manual. La interfaz no forma parte de esta ampliación.

### Plantilla de entrega del agente

```text
Tarea/lote:
Revisión de entrada y revisión probada (o HEAD + lista del diff):
Archivos modificados:
Decisiones y fuentes:
Pasos completados / pendientes:
Comandos ejecutados y códigos de salida:
Casos realmente cubiertos y omisiones:
Ubicación de evidencia reproducible:
Bloqueos y dependencias afectadas:
Archivos que pueden liberarse:
Siguiente acción recomendada al coordinador:
```

Los informes generados no se editan a mano. En la entrega registrar comando, revisión y ubicación; si viven en `build/cache` u otra ruta ignorada, conservar en el documento de tarea un resumen suficiente para reconstruir el resultado. Las interpretaciones permanentes de reglas viven en las especificaciones o decisiones existentes, no únicamente en un mensaje de agente.

## Checklist principal

La columna «depende de» determina autorización de escritura, salvo la exploración anticipada de solo lectura indicada más abajo. Una dependencia no se satisface por estar `en revisión`.

| Hecho | ID y documento de ejecución | Estado | Depende de | Responsable | Evidencia / revisión |
|---|---|---|---|---|---|
| [x] | Preparación: snapshot de todos los cambios | completada | — | Coordinador | `9118ca2`, publicado en `origin/2A2B` |
| [x] | [T01 — Inventario y validación inicial](tasks/T01.md) | completada | Snapshot | Agente ejecutor | Entrega en T01 sobre `a31bd8d`; aceptada 2026-09-25 |
| [x] | [T02 — Revisión y cierre de bandas 2A](tasks/T02.md) | completada | T01 | Agente ejecutor | Entrega y gate mantenido sobre `101ca5d`; aceptada 2026-09-25 |
| [x] | [T03 — Revisión y cierre de bandas 2B](tasks/T03.md) | completada | T01; T04 completada | Agente ejecutor | Seis re-puntos y gates afectados sobre `5105860`; aceptada 2026-09-25 |
| [x] | [T04 — Catálogos, identidades y procedencia](tasks/T04.md) | completada | T01 | Agente ejecutor | Mapa y decisiones sobre `b2e437c`; aceptada 2026-09-25 |
| [x] | [T05 — Normalización y promoción reproducible](tasks/T05.md) | completada | T04 | Agente ejecutor | Promoción explícita e idempotente sobre `cd04931`; aceptada 2026-09-25 |
| [x] | [T06 — Inventario y reparto de obligaciones](tasks/T06.md) | completada | T01–T05 | Agente ejecutor | 1692 efectos y 2295 obligaciones reconciliados; aceptada 2026-09-25 |
| [x] | [T07 — Fusión en la KB canónica](tasks/T07.md) | completada | T02–T06 | Agente ejecutor | KB promovida, estructural e idempotente; aceptada 2026-09-25 |
| [x] | [T08 — Validación y cierre de la KB](tasks/T08.md) | completada | T07 | Coordinador/integrador | 2399 IDs reconciliados, carga canónica única y gates de KB aceptados 2026-09-26 |
| [x] | [T09 — Construcción y selección para Web](tasks/T09.md) | completada | T08 | Agente ejecutor | Contratos de construcción aceptados; 161/161 bandas construibles y T10/T11 liberadas 2026-09-27 |
| [x] | [T10 — Automatización de campaña Web](tasks/T10.md) | completada | T09 | Agente ejecutor | 567 obligaciones reconciliadas; automatización de campaña aceptada 2026-09-28 |
| [x] | [T11 — Interfaz Warband Manager Web](tasks/T11.md) | completada | T09; cierre tras T10 | Agente ejecutor | Contratos finales de T10 conectados; interfaz y flujos Web aceptados 2026-09-28 |
| [x] | [T12 — Artefactos, validación Web y cierre](tasks/T12.md) | completada | T10/T11 | Coordinador/integrador | Artefactos diferidos, Web y PDF validados; fase 2 cerrada 2026-09-28 |
| [ ] | [T13 — Reglas del Combat Simulator](tasks/T13.md) | en progreso | T12 | Coordinador | T13.0/1, lotes parciales T13.2, reconciliación F035 y reparación F017 aceptados; pilotos y pendientes mantienen sus límites. [Plan restante](tasks/T13-T15-remaining-plan.md): F016 puede retomar su ruta nombrada, F019 integración pendiente; completar compilación/activación y mecanismos T13.2–T13.7 |
| [ ] | [T14 — Validación y paridad de combate](tasks/T14.md) | pendiente | T13 | Sin asignar | — |
| [ ] | [T15 — Revisión y cierre del Combat Simulator](tasks/T15.md) | pendiente | T14 | Coordinador | — |

## Fases, entradas y salidas

T01–T05 constituyen la preparación ya aceptada. Las tres fases siguientes se ejecutan en orden y cada una termina en validación vigente y commit local antes de abrir la siguiente.

### Fase 1 — Integración con la KB (T06–T08)

Inicio: T01–T05 aceptadas. T06 clasifica cada obligación como `KB`, `Warband Manager Web`, `Combat Simulator` o `sistema excluido`. T07 normaliza y promueve de forma serial; T08 valida fuente y destino y cierra la fase.

Fin: todos los registros aprobados se cargan una vez desde `sources/knowledge`, sin referencias rotas, pérdida de variantes ni lectura productiva de staging. Fidelidad, traducciones, esquemas e idempotencia acreditadas; commit local de fase 1 creado.

### Fase 2 — Warband Manager Web (T09–T12)

Inicio: fase 1 cerrada. T09 fija construcción, selección y contratos; después T10 implementa campaña y T11 conecta exclusivamente `warband-manager-web`. T12 genera artefactos, valida el flujo completo y cierra la fase.

Fin: las bandas 2A/2B pueden crearse, operar, persistirse, reabrirse y exportarse en Web con ES/EN, accesibilidad y errores correctos. Automatización de campaña cubierta por casos de producto; commit local de fase 2 creado. El **producto** de escritorio se retiró y queda fuera de alcance: no se crean ni modifican diálogos Tk ni se exige paridad con él. Los **adaptadores y módulos compartidos** que ese producto consumía siguen en el árbol y no se retiran, porque los usan las pruebas y el Combat Lab (`packages/python/adapters/desktop-ui/` y `packages/python/campaign/mordheim_campaign/ui/`).

### Fase 3 — Combat Simulator (T13–T15)

Inicio: fase 2 cerrada. T13 implementa las obligaciones admitidas por la reconciliación de T13.0 contra T06, transferencias, fuentes canónicas y exclusiones; el reparto heurístico inicial no decide por sí solo el alcance. T14 demuestra semántica y paridad; T15 revisa el conjunto y cierra la fase.

T13.2 reuses shared construction/validation already implemented for both
products. F035 has reconciled old findings; remaining work is demonstrated
canonical data/adapters/shared-decision gaps and Combat Lab effect compilation,
not another implementation of T09. Engine behavior stays in T13.3–T13.6.

Fin: cada efecto de combate incluido tiene prueba determinista y paridad en todos los backends aplicables, con RNG, decisiones y estado observable correctos. Gate integral vigente y commit local de fase 3 creados; sin push ni despliegue.

## Paralelismo y barreras de sincronización

Máximo cuatro agentes simultáneos: coordinador más tres trabajadores. La tabla prioriza seguridad de escritura; las dependencias no obligan a mantener agentes ociosos.

| Oleada | Paralelismo permitido | Punto de sincronización |
|---|---|---|
| A | T01–T05 completadas; T06 activo | P0: preparación aceptada e inventario de obligaciones reconciliado |
| B | T07 serial | P1a: KB promovida; detener escritores de datos |
| C | T08 serial | P1: KB validada y commit local de fase 1 |
| D | T09 serial; T10/T11 solo leen | P2a: contratos Web estables |
| E | T10 + T11 con archivos disjuntos | P2b: campaña e interfaz Web aceptadas |
| F | T12 serial | P2: Web validada y commit local de fase 2 |
| G | T13 por lotes/backends disjuntos tras fijar el mecanismo común | P3a: comportamiento de combate implementado |
| H | T14 serial respecto de reparaciones | P3b: paridad de combate aceptada |
| I | T15 serial | P3: revisión integral y commit local de fase 3 |

La lectura preparatoria puede adelantarse, pero ninguna fase escribe antes del commit de cierre de la anterior. T10 y T11 solo escriben en paralelo después de que T09 estabilice sus contratos. T13 puede dividirse por backend únicamente después de fijar el mecanismo modular y con archivos disjuntos.

### Conflictos que requieren serialización

- Catálogos y registros compartidos: T04 durante preparación, T07 durante promoción; después asignación por archivo y lote por el coordinador.
- `runtime`, bindings, constructores y esquemas comunes: un dueño por archivo; T09 fija los contratos Web antes de T10/T11 y T13 fija el mecanismo común de combate antes de repartir backends.
- Shared eligibility source, bridge and generated bundle have one coordinated writer across both products. Only reproduced decision gaps change that module; affected direct/browser and embedded consumers must be tested. Separate compiler-only lots may proceed on disjoint files with stable shared inputs.
- T10 y T11 acuerdan las entradas y errores antes de que T11 implemente formularios; T11 no inventa una lógica de campaña alternativa.
- Generados web y manifiestos: solo T12 o el coordinador tras una corrección. Nunca varios agentes regenerando a la vez.
- Pruebas que mutan temporalmente datos, como auditorías negativas, no corren mientras otro agente los lee o edita. Ejecutarlas en una copia aislada cuando el runner no garantice aislamiento; comprobar restauración byte a byte.
- T08, T12 y T14 validan sus respectivas fases. Si encuentran fallos, los devuelven al propietario y repiten solo la evidencia invalidada antes del commit de cierre.
- Git: solo coordinador crea commits, cambia ramas, integra o publica. Sin `reset`, `clean`, amend o rebase para ocultar trabajo concurrente.

En un checkout compartido basta esta reserva por archivos; no crear infraestructura nueva de bloqueo. Un worktree solo si es necesario para aislar una prueba o lote incompatible, creado desde la revisión acordada y con integración a cargo del coordinador.

## Herramientas y documentación común

Leer primero las guías existentes, y usar `--help` o el código para confirmar argumentos antes de ejecutar. Las rutas de los siguientes enlaces son relativas a este documento.

- [Modificar la KB](../../guides/modify-knowledge-base.md), [modelo de campaña](../../guides/campaign-knowledge.md), [implementar y verificar reglas](../../guides/implement-and-verify-rules.md).
- [Arquitectura](../../reference/architecture.md), [verificación](../../reference/verification.md), [presentación web](../../reference/web-presentation.md), [glosario](../translation-glossary.md).
- [Contrato editorial](../../../contracts/knowledge-editorial-v1/README.md), [especificaciones semánticas](../../../tests/specs/README.md).
- [Herramientas de ingesta](../../../tools/ingestion/README.md), [plan 2A](../../../sources/2A/README.md), [plan 2B](../../../sources/2B/README.md).
- [Forma de promoción](../../../sources/2B/promotion-schema-plan.md), [notas de fusión](../../../sources/2B/catalog/promotion-merge-notes.md).

Reutilizar `ingest_2a.py`, `ingest_2b.py`, `audit_2a_sources.py`, `audit_2b.py`, `audit_2ab_fidelity.py`, `normalize_staging_for_promotion.py`, `audit_staging_contract.py`, `check_hireling_sources.py` y el generador web. No restaurar herramientas retiradas porque un README antiguo aún las mencione.

Las extensiones de herramientas deben ser pequeñas y demostrar una necesidad de la tarea. Mantener el orden de normalización que exige la implementación, especialmente mercado antes de retirar hechos del ítem y campaña de mercenarios antes de retirarlos de sus perfiles. La previsualización de promoción no debe escribir la KB.

Comandos de cierre existentes, desde la raíz y con el entorno del proyecto:

```powershell
python tools/mordheim-utils.py tests --scope knowledge
python tools/mordheim-utils.py verify --structural
python tools/mordheim-utils.py verify --json
python tools/mordheim-utils.py parity --require-complete
python tools/knowledge/generate_knowledge_web.py --check --check-translations
python tools/mordheim-utils.py check-presentation
npm test
npm run typecheck
npm run build
python tools/mordheim-utils.py run-ci
```

No es una orden de ejecutar todas las suites en cada tarea. Cada documento concreta el mínimo proporcional y cada fase tiene su propio cierre. T15 consolida únicamente Combat Simulator y comprueba que los cierres anteriores siguen vigentes. No actualizar digests ni cantidades para apagar un fallo sin revisar qué cambió.

## Riesgos conocidos que hay que verificar

- Los manifiestos se observaron en `english-reviewed`, no `promotable`.
- El normalizador proponía eliminar `lore.prayers-of-taal-and-rhya`; verificar equivalencia y todas las asignaciones antes de aceptar o corregir esa conducta.
- El selector Web excluía grados 2A/2B; cargar el YAML no basta.
- Existen pruebas con cantidades fijas y prohibiciones de colisión entre staging y KB que requieren adaptar el contrato de promoción retenida.
- Las notas históricas pueden describir transformaciones ya hechas. La evidencia actual manda.
- La ausencia de caché puede hacer que un auditor omita comprobaciones. Registrar cobertura real, no solo código de salida.
- `NO` en una regla de campaña puede referirse al motor de duelo; no implica que deba seguir manual en el gestor de campaña.
- Límites aceptados del cierre de la fase 2 (`D1`–`D5`): registrados en la [entrega de T12](tasks/T12.md) §13.3; no son defectos corregidos.

## Criterios globales de aceptación

- [ ] Inventario completo de bandas y catálogos reconciliado con destino; no faltan familias.
- [ ] Sin IDs duplicados, referencias rotas, pérdida de variantes o cambio accidental del contenido anterior.
- [ ] Promoción repetible sin cambios adicionales y staging fuera de los cargadores de producción.
- [ ] Fuentes y traducción ES/EN completas; precios, restricciones y magia mantienen sus contextos.
- [ ] Cada efecto tiene implementación verificada o exclusión concreta de los sistemas acordados.
- [ ] Python/TypeScript del Warband Manager Web y los motores del Combat Simulator mantienen comportamiento, decisiones y orden RNG donde corresponda.
- [ ] Creación, reclutamiento, equipo, contratación, progreso, guardado/reapertura y PDF probados donde sean aplicables; todos los mecanismos nuevos tienen casos de producto.
- [ ] Categorías 2A/2B seleccionables y excluibles; presentación visible y accesible sin IDs técnicos filtrados.
- [ ] Artefactos y evidencia pertenecen a la revisión final; fallos previos y limitaciones reales de validación declarados.
- [ ] Staging retenido; commits locales revisados, sin publicar implementación ni tocar `main`.

## Registro de decisiones y sincronizaciones

| Fecha | Barrera/tarea | Decisión | Evidencia | Aprobación del coordinador |
|---|---|---|---|---|
| 2026-10-02 | F040 independent review | Accept reviewed requirement reconciliation/fail-closed repair; release reservation; dispatch F057 stale parity-inventory fix; retain optional F058/F059 and current full-gate blocker | tasks/T13-coverage-independent-review.md section11;coverage-coordinator-acceptance/coordinator-review.json;61 retained hashes,fresh52 tests,exactfour-array budget scope;current3758 cases versus3743 pin;concurrent unrelated CLI audit edits preserved,coverage handler unchanged | Yes |
| 2026-10-02 | F007 independent implementation review | Accept accepted-Q019 modular implementation/Barrage repair after external review; release reservation; record F056 witness and make F008 activation handoff eligible, without canonical/backend/coverage certification | tasks/T13-spectral-touch-independent-review.md section13; spectral-touch-coordinator-acceptance/coordinator-review.json;15 unchanged reviewed hashes, retained101/432 passes, fresh strict and isolated mutation probes; broad additions corrected to24 profile saves +3 F040 boundary cases | Yes |
| 2026-09-25 | Preparación | Publicar snapshot y documentos en `2A2B`; implementación posterior local | Solicitud del usuario; snapshot `9118ca2` | Sí |
| 2026-09-25 | B0 / T01 | Aceptar inventario y baseline; abrir T02, T03, T04 y la exploración de T06 | Entrega de T01 sobre `a31bd8d`; validación puntual de manifiestos y contrato | Sí |
| 2026-09-25 | T02 | Mantener bloqueada hasta reparar y ejecutar el auditor 2A; conservar el cotejo ya realizado y pasar sus notas de fusión a T04 | Entrega de T02 sobre `101ca5d`; `audit_2a_sources.py` usa dos nombres no enlazados y deja chequeos vacuos | Sí |
| 2026-09-25 | T02 | Aceptar las 19 bandas 2A tras reparar el gate; transferir `sources/2A/promotion-merge-notes.md` a T04 | Auditor 2A: 0 abiertos, 14 adjudicados; 23 pruebas enfocadas; cobertura no vacua declarada | Sí |
| 2026-09-25 | T03 | Conservar la revisión de las 61 bandas y bloquear el cierre hasta que T04 resuelva fuentes e identidades; después repetir solo gates afectados | Entrega de T03 sobre `b2e437c`; 60/60 hashes PDF, 0 problemas de banda, 8 problemas de magia y barrera de catálogo declarada | Sí |
| 2026-09-25 | T04 | Aceptar mapa de promoción y decisiones; conservar Taal & Rhya y Shield of Sigmar como variantes y usar sufijo `-miracle-workers`; devolver seis re-puntos a T03 | Fuentes externas recuperadas con URL/hash; auditor 2B con 0 problemas y 66/66 conjuros; mapa `2ab-promotion-map.json` | Sí |
| 2026-09-25 | T03 | Aceptar el cierre tras aplicar seis re-puntos de objetos decididos por T04 | `ingest_2b validate` sin problemas, auditor 2B `problem_count 0`, matriz con 0 referencias sin resolver | Sí |
| 2026-09-25 | T05 | Aceptar la promoción explícita; conservar `warplock_pistol` como variante con entrada `-mim`, mantener los 26 ids históricos y normalizar staging al inicio de T07 antes de promover | Preview de 409 acciones/13 documentos, segunda pasada sin escrituras, colisión ambigua rechazada y 9 pruebas enfocadas; revisión estructural del coordinador | Sí |
| 2026-09-25 | Replanificación | Organizar el trabajo restante en KB (T06–T08), Warband Manager Web (T09–T12) y Combat Simulator (T13–T15); eliminar escritorio, incluir campaña en Web y cerrar cada fase con validación y commit local | Decisión del usuario antes de iniciar T07; T01–T05 permanecen aceptadas | Sí |
| 2026-09-25 | T06 | Aceptar el inventario y reparto por fases; tratar las 366 filas compuestas como 970 obligaciones explícitas y resolver `trait.spectral-touch` primero en T07 | Matriz: 1692 efectos, 2295 obligaciones, particiones reconciliadas, JSON/CSV UTF-8 y sin filas idénticas duplicadas; comprobación puntual del coordinador | Sí |
| 2026-09-25 | T07 | Aceptar la promoción canónica tras cerrar estructura, traducciones, catálogos, referencias y auditorías; conservar tres exclusiones de runtime justificadas y Spectral Touch pendiente de ejecución | 128 bandas, 2399 IDs creados, suite knowledge 602 pasadas/10 omitidas, estructura completa y segunda promoción sin escrituras | Sí |
| 2026-09-26 | T08 / cierre de fase 1 | Aceptar la KB integrada tras reparar los 80 efectos de objeto sin traducción y normalizar la regla pendiente; liberar T09 | 2399 IDs reproducidos, 0 referencias rotas, 396/396 objetos y 4305/4305 nodos con efectos ES, promoción idempotente y suite knowledge 602 pasadas/10 omitidas | Sí |
| 2026-09-27 | T09 | Aceptar los contratos de construcción y selección; adjudicar 12 obligaciones de magia como sistema excluido/X4 y liberar T10/T11 en paralelo | Artefacto fresco con 161/161 bandas construibles, 0 bloqueos abiertos, 25 gates focales verificados y promoción sin escrituras | Sí |
| 2026-09-28 | T10 | Aceptar la automatización de campaña y liberar su integración final en T11; conservar cinco obligaciones como bloqueo de fuente documentado | 567 obligaciones reconciliadas, retirada/sucesión/mutaciones/Born Marksmen cubiertos, 10 gates focales verificados y 30 errores semánticos heredados sin incremento | Sí |
| 2026-09-28 | T11 | Aceptar la interfaz Web tras reconciliar los contratos finales de T10 y liberar T12 | Categorías 2A/2B, variantes y obligaciones de campaña verificadas; 25 pruebas focales y typechecks Web/dominio verdes; artefactos, presentación y PDF transferidos a T12 | Sí |
| 2026-09-28 | T12 / cierre de fase 2 | Aceptar Warband Manager Web y liberar T13 | Carga inicial particionada a 282,3 kB gzip bajo el presupuesto de 350 kB; catálogo diferido verificado, 1270 obligaciones Web reconciliadas, Web/PDF ES-EN y navegador real validados | Sí |
| 2026-09-30 | T12 / cierre técnico de fase 2 | Cerrar la fase 2 tras la auditoría independiente final: corregir el recurso de fuente web (D6) y registrar los límites D1–D5 | Worktree limpio de `913d93a`; artefactos reproducidos (sha256 en T12 §13.1); 136/136 detectores, 739 estáticos heredados, 0 dinámicos; Web 428 y TS 738 verdes; sin push | Sí |
| 2026-09-30 | Preparación T13 / frontera de producto | Corregir la atribución de productores y servicios de campaña a Combat Lab: ambas aplicaciones comparten exclusivamente la KB como entrada de producto | Decisión del usuario; T10/T11 y comentarios corregidos. El adaptador de retiradas solo tiene llamadores en pruebas; no se acredita captura desde Web ni se completa T13 | Sí |
| 2026-09-30 | T13.0 / inventario y entrada | Aceptar la reconciliación documental completa y liberar el lote; T13 continúa en progreso | 1.692 orígenes únicos; 712 incluidos, 266 mixtos, 35 construcción, 354 campaña, 269 excluidos, 22 datos, 34 bloqueados por fuente; 185 preguntas asignadas. Verificación estructural válida, 455 diferencias de fuente en KB local y 30 en copia de HEAD; sin certificación semántica ni cambios de motor/KB | Sí |
| 2026-10-01 | R0 / translation-only source pins | Accept the manifest-limited pin refresh after independent coordinator spot checks; the 125 context-data and 30 pre-snapshot classes remain with F001 | 300/300 pairs equal the live fingerprint; diff limited to the authorized digest lines (104 files, 300 lines); fresh verify 455 -> 155 with 300 removed / 0 added; structural green; focused suite 4 -> 1 inherited; Bloated Foulness preserved; [delivery](tasks/T13-translation-pins.md) | Sí |
| 2026-10-01 | R0 / context-data evidence review | Accept bounded research, retain current structured-rule deduplication and permit separate exact 125-pair pin-only dispatch after revalidation; route presentation to F041/T15 | 125 live/historical/pin triples valid; 34 context documents, 29 non-i18n deletions in19 profiles; five independent compile probes agree; bundle freshness green; code/spec/source hashes current; [disposition](tasks/T13-context-data-review.md#11-coordinator-acceptance-and-class-disposition--2026-10-01); no pin edit, F001/F035 remain open | Sí |
| 2026-10-01 | R0 / context-data source pins | Accept exact 125 manifest-limited digest updates after independent reconstruction from pre-dispatch originals;retain30 historical pairs under F001 | 48 original hashes match,125 hex-only lines and exact byte inversion;fresh fingerprints match;300/30 protected pins intact;fresh verify155->30,0 added,structural green1050;[acceptance](tasks/T13-context-data-pins.md#9-independent-coordinator-acceptance--2026-10-01);no product changes | Sí |

| 2026-10-01 | R2/R3 / Fimir and Boglar thresholds | Accept canonical construction/modular corrections and the two necessary staged mirrors; release reservation and resolve F011/F012 locally | Independent exact diff/backup checks;65 construction/modular/promotion and15 semantic cases pass;6 canonical controls and16 parameter probes;fresh verify30 historical errors,565 verified/153 pending,structural green1050;[acceptance](tasks/T13-profile-save-thresholds.md#10-independent-coordinator-acceptance--2026-10-01);F042–F047 routed,ports/phase remain open | Sí |

| 2026-10-01 | R0 / F042–F043 catalogue contracts | Accept the source-reference and schema-derived validation repair; release reservation and resolve F042/F043 at contract boundary | Independent byte reconstruction/source/AST/protected-input checks;63 tests and7 negative probes pass;fresh verify30 inherited errors/565 verified/153 pending,structural1050;generator and published EN/ES note checked;[acceptance](tasks/T13-catalogue-contracts.md#11-independent-coordinator-acceptance--2026-10-01);F048/F049 retain product/mutation-method limits | Sí |

| 2026-10-02 | R0 / F044 equipment-access schema contract | Accept supported local declarations with exact member justifications; resolve F044 and release reservation | Independent original/schema/allowlist/705 protected-hash checks; 316 Python and 2 new TS tests pass; audit 40 findings / 0 hard-unjustified-stale; [acceptance](tasks/T13-equipment-access-schema.md#11-independent-coordinator-acceptance--2026-10-02). F050 presentation and F051 inherited shared pooling remain open; T13 unchanged | Sí |

| 2026-10-02 | F051 shared schema evidence | Accept global declared/observed pooling; resolve F051 and release reservation | Independent F044-backup/production hash and AST checks; canonical grant counts exhaust enum; 40 to39 exact records, one false finding/obsolete justification removed, other39 unchanged;27 fresh tests pass,705 protected inputs checked with sole concurrent F050 test drift; [acceptance](tasks/T13-shared-schema-evidence.md#12-independent-coordinator-acceptance--2026-10-02). P1/P2 docs reconciled, P3 becomes F052, P4 dismissed as current repair; phase open | Sí |

| 2026-10-02 | F050 localized reference citations | Accept current source-backed EN/ES read-model resolution; resolve F050 and release reservation | Independent five-backup/701-source/hash checks; two erroneous closing checksums superseded by tested current bytes; fresh 36 TS/10 rendered/21 distance/4 probes plus typechecks/generator pass;19 cited IDs resolve,30 complete unique maxima; [acceptance](tasks/T13-reference-citations.md#16-independent-coordinator-acceptance--2026-10-02). F053–F055 retain explicit scope/integrity/static-gate barriers; T15 open | Sí |

| 2026-10-02 | F052 strictness JSON members | Accept exact additive member serialization; resolve F052 and release reservation | Independent one-line byte inversion;29 fresh CLI/F051 tests pass; real subprocess JSON matches39 maintained findings and original after dropping members, text identical; accepted auditor/entry boundary preserved; [acceptance](tasks/T13-schema-strictness-json.md#12-independent-coordinator-acceptance--2026-10-02). No speculative schema artefact or phase closure | Sí |

| 2026-10-02 | Shared construction documentation and remaining T13–T15 plan | Reconcile current ownership throughout the relevant plans, guides and historical deliveries at the user's request. Eligibility is an implemented shared baseline; F035 classifies old findings before repairs, while canonical bindings, Python combat projection and engine behavior retain separate proofs. Preserve accepted T09–T12 scopes and existing finding/source IDs | 32 documents updated; links and scoped whitespace checks pass; 18 historical bodies preserved apart from explicit current-ownership notes; 1,963 code/data inputs and HEAD unchanged. Evidence: `build/cache/t13-parallel/shared-eligibility-documentation/`. No code/data change, runtime certification, finding closure, commit or push | Sí |

| 2026-10-02 | F003 independent Shifty decision package | Accept the independent review as source/evidence for human S1–S4 decisions; release review reservation and retain F003 in review. Correct the Elder-only dossier claim using current four-Hero facts; route maintained poison witnesses to F060 and Halfling first-attack loss to F061 | 19 manifest pairs and report hash current; canonical grant/kind/binding checked; fresh 101 focal tests pass and all 12 observations reproduce with explicit assertions. [Integration](tasks/T13-shifty-review.md#independent-review-integrated-by-coordinator--2026-10-02); no semantic acceptance, canonical activation, ports or unrelated gate closure | Sí |

| 2026-10-02 | Shifty S1–S4 human acceptance / F003 | Record the user's explicit acceptance of all four recommendations and stated limits; resolve F003 for the reviewed modular contract and preserve separate activation, pistol allocation and optimized-port barriers | [Permanent ruling](../../decisions/design-rulings.md#shifty-s1s4), [scope and reply](tasks/T13-shifty-review.md#human-acceptance--2026-10-02); 19 incoming manifest pairs/report hash rechecked unchanged, retained 101 focal passes/12 asserted probes valid. No code/KB/spec/test change, agent launch, commit or push | Sí |

| 2026-10-02 | F035 shared-eligibility reconciliation | Accept the current-consumer investigation and release its reservation; resolve F035, not F004/F016–F021/F028. Prioritize F017 before F016; preserve admitted Bow Restrictions/Teeny Hands and configured Bloodline combat effects rather than adopting metadata/ranged/campaign deferrals | [Governing dispositions and independent proof](tasks/T13-shared-eligibility-reconciliation.md#12-coordinator-acceptance-and-governing-dispositions--2026-10-02): 18 manifest pairs/24 protected inputs current, 47 unique clauses, fresh probes equal retained, bundle/27 TS/21 embedded cases pass, direct/embedded F01720 and F019 stage reproduced. Specialized stage changes may share TypeScript ownership; no Python validator copy, product certification, production repair, commit or push | Sí |

| 2026-10-02 | F017 shared band-recipient repair | Accept the single shared predicate correction and generated bundle; resolve F017 and release shared-file reservation. F016's recipient prerequisite is satisfied, while named-skill route/mechanics and F019 stage integration remained pending | [Independent acceptance](tasks/T13-band-rule-recipients.md#10-independent-coordinator-acceptance--2026-10-02): seven delivery hashes/23 entry inputs checked, exact inversion to prior source bytes, bridge unchanged, current bundle; fresh40 TS/47 embedded cases, unchanged reproducer20→0, independent30 witnesses pass and detect removed filter/wrong OR. Construction481/typecheck reused; no production edits by coordinator, phase certificate, commit/push or agent launch | Sí |

| 2026-10-02 | F019 Silence stage/fact integration | Accept the specialized bound-equipment repair and the Python transport projection; resolve F019 and release its shared eligibility/index, bundle and Python transport reservation. F016 and F020/F021 remain open | [Independent acceptance](tasks/T13-silence-equipment.md#10-independent-coordinator-acceptance--2026-10-02): 25 delivered files verified, four authorized drifts only, bridge unchanged and bundle current; unchanged reproducer exits0 stage-attributed (before1); fresh7 TS/8 Python/489 construction pass; isolated mutation proof identical; animal decision+boundary proved with no admitted construction route and crossbow latent. Combat496/full `test_semantics` retained, not rerun; no phase certificate, commit/push or agent launch | Sí |

| 2026-10-02 | F060 Shifty poisoned-hand maintained witnesses | Accept the bounded Spider Spittle witness lot, resolve F060 and release its reservation; preserve F004/F005/F026/F006/F061 and concurrent construction-centralization ownership | [Independent acceptance](tasks/T13-shifty-poison-transport.md#9-independent-coordinator-acceptance--2026-10-02): delivery/input hashes current, fresh106 focal passes, five baselines/seven isolated faults verified at contract checks; direct nominated weapon/clean-pair/slot checks pass both directions. External evidence, tests and production preserved; no broader poison, legality, port, phase certificate, commit/push or agent launch | Sí |

| 2026-10-02 | Remaining T13–T15 execution efficiency | Replace historical evidence-only dispatch waves with functional-family delivery: canonical input, modular behavior, product access, necessary cases/docs and coherent stable ports. Fold F056 into F008 while preserving any already-launched executor; retain active centralization and F057 reservations | [Revised plan](tasks/T13-T15-remaining-plan.md); original contracts, T13/T14/T15 and follow-up scheduling aligned. No scope reduction, new source ruling, finding closure, implementation, agent launch, commit/push or waived required gate | Sí |

| 2026-10-02 | Executable remaining-lot sequence | Fix L01–L23 as dispatch units with outputs/dependencies/closure; L01 reuses F057, centralization is already running, and F056's now-present external report integrates into L03. Include tests/data/docs within their functional owner | [Lot list](tasks/T13-T15-remaining-plan.md#executable-lot-list--2026-10-02). Preserve all admitted origin clauses, source gates, applicable backend evidence and required T14/T15 closure; no implementation, finding acceptance, agent launch, commit/push or changed external ownership | Sí |

| 2026-10-03 | L04 canonical Shifty milestone | Activate explicit Elder/Cook/Thief/Youths selection using accepted S1–S4/F060 and shared construction; release owned paths. Preserve F004's promoted local-participant clause under L05 and F005/F026/F006 barriers | [Delivery](tasks/T13-shifty.md#l04-canonical-activation--2026-10-03): canonical/2A metadata, once-only execution tag, actual rounds/public API, 926 affected cases, source-linked 11 cases/3 faults; exact semantic additions and unchanged 30 historical errors; preserved centralization/engine inputs. No optimized/GUI/T14 certificate, commit/push or agent launch | Sí |
| 2026-10-03 | L05 canonical construction milestone | Reuse shared eligibility for named tables, configured Hero recipients, active Runt positions and supplied complete-kit checks; remove Iron Sinews legacy stats and reject unbound implemented markers. Retain explicit source/item behavior gates and continue with L06 | [Delivery](tasks/T13-canonical-choices.md); 958 affected Python cases, 82 TS cases, unchanged 30 historical semantic errors; no full T13.2/T14/GUI certificate, agent launch, commit or push | Yes |

Añadir aquí solo decisiones de coordinación. Para una regla, enlazar su interpretación y evidencia en el sistema semántico existente. No mantener dos versiones divergentes de una misma decisión.

Historical coverage verification of the R4 repair: 519 deterministic tests
passed, but the old line-budget gate failed at 217 indexes. The dedicated
[F040 reconciliation](tasks/T13-coverage-reconciliation.md) subsequently accounts
for all 647 original instructions in the four changed modules, restores one
real missing inactive-participant witness and repairs invalid measurement/update
acceptance. Focused checks: 52 passed; fresh full gate: 522 passed, exit 0,
zero drift errors, original area floors met. F040 independent
review remains required; pilot activation, optimized ports and T14 certification
retain their own barriers.
