# Remaining 2A/2B integration into Combat Lab — T13–T15

Current status (2026-10-05): **T13 modular implementation is partial**. The latest autonomous continuation completes optional Eagle Friend as separate repeatable Strike First/S3 weapon contributions, using the directing Priestess's WS/Initiative without hand-weapon or poison duplication; no third fighter is created. Snerik now compiles and runs with his complete printed kit: his inline Camouflage Cloak remains owned but inactive, justified by its uniquely resolved excluded rule. The editor preserves supplied ownership for the same profile and round-trips the number of eagles. Prior House Guard/Tranquil Fauna deliveries remain implemented. Native admission remains 23 base hired swords plus Aldred, Armen, conditional Snorri and Snerik. Other optional Marks and source-blocked modular clauses remain.

**Implementation granularity:** finish each admitted effect end to end in one
lot, including canonical grants, compilation, modular behavior and necessary
product inputs. Group effects with similar semantics. Split only for a source
blocker, dependency or concrete implementation benefit. Add a small number of
meaningful cases to the existing family suite and run only affected checks;
collective certification remains a separate task.

**Execution boundary, 2026-10-05:** continue remaining modular families,
retaining deferred problems in the follow-up register. Do not start L19/L20
without changing the current modular-first instruction. The interleaved
optimized-port recommendation below does not govern this execution; unresolved
source gates are not silently excluded.

**Scope correction, 2026-10-04:** the user reaffirmed **1v1 duels** as the
product purpose. Group Rout/psychology, All Alone counting, multi-target combat
and independent third fighters are excluded. External bonuses/conditions may
be supplied for a duelist without simulating their producers or a surrounding
group. This supersedes historical broader admissions, including related
follow-up close criteria. See the [permanent decision](../../../decisions/design-rulings.md#combat-lab-remains-a-1v1-duel-simulator--2026-10-04).
L21 reconciles historical origin/scope records; excluded group clauses are not
new implementation or certification blockers. Lot identifiers are retained.
The user's further clarification excludes map/terrain/weather rules, including
fog/Mystic Mist and fighting in water, even as supplied condition switches.
Their environmental exceptions are excluded rather than deferred blockers.

Execution priorities revised on **2026-10-02**, at the user's request to reduce
fragmentation and prioritize usable functionality. This replaces the earlier
dispatch sequence, including its completed evidence-only waves. The
[original plan](T13-implementation-plan.md) retains implementation contracts;
T13.2–T13.7 and R2–R7 keep their layer responsibilities and identities.

The [initiative README](../README.md) owns reservations and acceptance;
[follow-ups](T13-execution-follow-ups.md) retain discovered problems;
[inventory/questions](T13-inventory.md) and [origins](T13-obligations.csv) retain
scope/source identities. Scheduling changes neither scope nor interpretations,
acceptance or implementation status. This revision launches no agent.

## Current progress and remaining work — 2026-10-05

### Progress at a glance

| Workstream | Status | Remaining work |
| --- | --- | --- |
| Shared construction baseline | Implemented | Reuse it for residual item/profile projections; no repeat centralization. |
| T13 — Modular engine / L02–L17 | In progress | Remaining individual effects, target filters, keeper/mount contributions and source-blocked clauses. |
| T13 — Canonical hirelings / L16 | Partial | 23 usable base hired swords plus Aldred/Armen; Snorri requires a supplied drinking result. Strigani missing stats and optional Marks remain. |
| T13 — Product workflows / L18 | Partial | Complete affected editor, configuration, analyses and CLI workflows. |
| T13 — NumPy port / L19 | Not started for new families | Port applicable completed modular families and verify actual execution. |
| T13 — Native port / L20 | Not started for new families | Port applicable completed families and verify the built native engine. |
| T13 — Final reconciliation / L01/L21 | Pending closure | Current origin/scope/source-pin/reference reconciliation and remaining gate repairs. |
| T14 — Independent certification / L22 | Final certification pending | Semantic, parity and coverage checks against the completed applicable engines. |
| T15 — Integral review and closure / L23 | Final closure pending | Final product/integral checks, review and phase closure after T14. |

Statuses describe workstreams, not percentages or a count of dispatches.
Previously accepted deliveries remain valid within their recorded boundaries.

This is the governing progress summary. The 23 lot ids below remain work
owners, not 23 tasks still to launch. Delivered operators are reused; open
compound clauses do not require rebuilding their completed parts. This update
uses the current bindings/compiler and retained delivery results, not a new
full semantic/parity certification or an exhaustive origin audit.

| Area | Delivered | Still required |
| --- | --- | --- |
| Shared construction / L05 | Existing shared legality, named choices, recipients, grants and supplied owned/active kit facts; canonical hireling kits now use the same module. | Remaining source-specific item/choice projections under F028/F065 and their functional owners. No second constructor or repeated centralization. |
| Modular attacks, defences and sequences / L02–L11 | Canonical Vomit Attack, Spectral Touch and Shifty; grouped weapons, saves/injury/recovery, psychology, target modifiers, charm/reactions, Ghost Pirate Ethereal and user rulings Q037/Q128/Q013/F005. | Domnu Bear Hug allocation decision (F067); remaining hired-profile/optional-skill clauses below. F026/Q151 retains final pistol-contract reconciliation, rather than repeating delivered Shifty/pistol allocation. |
| Target facts / L06/L11/L21 | Explicit nature, species, normal-animal, Vampire, sex and open-flame facts; dependent Hellblade, Hatred and other local operators. | Complete source-backed classifications where still unnamed/unknown; audit compound remainders before claiming all canonical target coverage (F064/F070). Never infer nature from immunity or band names. |
| Local context and composite combatants / L12–L17 | Supplied leader/handler facts, individual one-die Animosity, two individual Command consequences, Sea Singer, Wheelo impacts/fittings and supplied mounted Righteous Charge. | Keeper-qualified Ferret contribution (F068); source-qualified contact provenance only where relevant to the existing duel (F069); admitted mount/component clauses (Q084/Q108/Q127/Q147). `weapon.lance` is still explicitly refused by modular initialization; supplied mounted facts are not complete mounted-combat support. |
| Canonical hirelings / L16 | Native 2B ids, starting skills, complete fixed/choice/optional kits, owned excluded unique items and source-qualified equipment; **23 usable base hired-sword profiles**, Aldred/Armen/Snerik and Snorri with a supplied result. Norse Bearman, Crimashin and Holy Man round-tripped through the real Tk editor. | Strigani missing stats, and optional Marks below. F036 stays open for these effects and complete product closure; F037's identities and Aldred's combat/runtime gates are resolved; he is also usable as a native Dramatis Personae. |
| Product / L18 | Optional individual facts and native participant choices are exposed in the editor; selected native kits preserve their identity. | Finish affected editor/configuration/analysis/CLI workflows and explanations for the remaining admitted effects. The tested editor round trips do not close every workflow. |
| NumPy/native / L19–L20 | Existing support and explicit guards are retained. | Port all new applicable stable families after modular completion/authorization, with actual backend execution. **These ports have not started.** |
| Final integration / L01/L21 | Earlier accepted pin lots and structural/publication checks remain reusable at their recorded revisions. | Reconcile exact new source pins, staging, origins/scope, compound clauses, item/reference integrity and current gate debt (including F057). This is consolidated integration work, not a separate review for each effect. |
| T14 / L22; T15 / L23 | Earlier bounded reviews are retained. | Final independent semantic/parity/coverage certification of the applicable engines, then integral/product review and phase closure. **Neither phase is complete.** |

H7's shared-access repair and the four residual mechanic-concession verdict
differences are delivered. Canonical alias facts now resolve the Black Lotus
and Mace offers without purchasable alias records. Six mechanic-only Vomit
Attack offers still need truthful L21 disposition. Bounded tests passed; the
full sweep was not repeated and global item parity is not asserted.
See [H7 review](T13-shared-access-parity-audit.md#8-coordinator-current-state-review--2026-10-05).

Grouped individual-modifier continuation (2026-10-05): Guiding Dream now rolls
once at battle start and applies its hit/Strength/Frenzy result only against an
explicitly nominated opposing Hero. Movement and narrative assignments remain
excluded. Iron Sinews is a selectable +1 Strength skill, never an innate grant.
Strigoi Kindred Hatred uses canonical/supplied Vampire bloodlines, including its
express grant despite innate psychology immunity, first-round timing and Frenzy
suppression. The Slayer Cult's three named non-Slayer recipients now receive
the existing Orc/Goblin Hatred operator, lost with psychology immunity.
The editor carries nomination and bloodline facts. L21 retains source-pin and
origin reconciliation; L19/L20 retain ports. Focused family cases and schema,
editor and publication checks cover this group, not whole-engine certification.

### KB reconciliation — 2026-10-05

Twelve already-executing Frenzy/Hatred grants now declare `scope: YES`; their
compiled outputs are unchanged. Two compound records retain explicit excluded
post-battle/Animosity clauses. Another 105 pure map, movement, shooting/casting,
group, campaign or post-duel rules now declare `NO`, following the accepted 1v1
boundary. Source prose and recipients are unchanged, including existing 2B mirrors.
The band-family manifest now derives from current included bindings (258 families,
990 memberships; not distinct completed rules). Eighteen delivered tag consumers
are registered; the structural probe supplies Snorri's existing required input
instead of treating its absence as an unimplemented mechanic. Structural verification
is green (1,050 profiles); this does not refresh semantic pins or certify ports.

Use `report rules --inventory-only --t13` for the current development queue.
The external `T13-modular-residuals.csv` is a historical investigation snapshot,
not a current task list: its old pending observations do not override canonical
runtime metadata. Genuine unbound duel effects and compound remainders remain
pending in the KB. Eighteen clear individual clauses now declare `YES` /
`implemented: NO` rather than obsolete subsystem deferral; four retain historical
questions to reconcile before implementation. F001/L21 still own source pins; L19/L20 and final certification
remain separate. This reconciliation implements no new combat behavior.

### Exact native-profile blockers

No normalized base hired-sword profile remains blocked by an intrinsic rule.
Mercy and Healing Hands are excluded support: the user rejects self-healing
and healing the opponent. Source prose remains intact. Strictures and the
separate optional Tranquil Aura are implemented.

Optional Marks remain pending for Morr, Myrmidia (Oracle), Ranald and Solkan.
Eagle Friend is independently selectable and repeatable; the composite Marks
of Myrmidia entry remains pending for Oracle, never a combined grant.
Manann's water/Aquatic Marks and Taal's contact-breaking Enlivened Flora are
excluded; Taal's separately selectable Tranquil Fauna is implemented. Sigmar's Enlightened and Symbol of Unity, and Ulric's Son of Ulric are
separate delivered choices; their compound parents never grant both together.
Ulric's Wolf Friend and Verena's Librarian/Owl Friend are excluded companion,
lifecycle, casting or shooting clauses. The 23 usable base profiles do not
mean every acquired skill is implemented.
Snerik's canonical stats and full inline unique-equipment kit are now delivered.
Only uniquely resolved `scope: NO` / `implemented: NO` item rules without
executable bindings qualify for owned-only projection; active or unresolved
unique items remain refused. Strigani Seer Necromancer still lacks canonical
stats; recover source data without anonymous substitutes.

### Resume and stop criteria

Resume the remaining related individual effects in their L06–L17 owners,
starting from L16's current canonical route. Group compatible effects and
finish their bindings, compilation, behavior and necessary inputs together.
Source-blocked F067, Strigani missing stats can be deferred while
other families proceed; record the blocker in the existing register.
Then finish L18 and perform consolidated modular origin/scope reconciliation.
Stop before the NumPy/native implementation boundary. A percentage or a fixed
number of implementation dispatches is not claimed: the remaining compound
origin reconciliation is still required, and a lot may contain many effects.

Group Rout, All Alone, independent third combatants, map/terrain/weather,
shooting/casting and voluntary escape/unresolved endings are **excluded**, not
future implementation tasks. Q158's group emission/range ambiguity does not
block the two supplied individual Command effects already implemented.
`knights_helm` is a user-declared source erratum: retain F063's data/reference
cleanup, not a new helmet mechanic. User rulings Q037/Q128/Q013/F005 are
implemented and are not questions awaiting another answer.

Evidence boundary: this continuation adds four cases to the existing modular
family, one shared TypeScript kit case and one real editor round-trip. Family,
source schemas/mirror, trait contract, shared bundle/typecheck, documentation
and publication checks cover the affected delivery. Independent whole-engine
certification and ports remain separate. Oracle/Augur and Ranald's Luck require
ownership-safe arbitrary-roll handling; the existing narrower `skill.luck`
operator is not an equivalent implementation.

## 1. Accepted work and active dependency

| Baseline to reuse | Remaining boundary |
| --- | --- |
| T13.0 inventory; T13.1 contracts/replay | Extend only inputs required by a real remaining mechanism; do not repeat the inventory. |
| T13.2a/b bonuses and Bloated Foulness | Accepted; Movement compilation is not movement resolution. |
| T13.2c/d and hireling/command traces | Reuse their origin matrices; finish real mappings, behavior and participant access. |
| L02 / F010 optional Vomit Attack, delivered 2026-10-03 | Canonical compilation and modular replacement implemented; reuse [the delivery](T13-vomit-attack.md). Optimized choice remains explicitly refused until L19/L20, with product integration in L18 and independent certification in T14. |
| F035/F017/F019 reconciliation, recipients and equipment tokens | Accepted/resolved; no repeated extraction or eligibility investigation. |
| Shifty S1–S4/F003; Spectral R1–R4/F007 | Modular contracts accepted; canonical activation/product access and applicable ports remain. F060 poison witnesses are accepted/resolved. |
| F011/F012 Fimir/Boglar thresholds | Canonical compilation/modular saves accepted; applicable optimized consumption belongs in the backend batch. |
| F040, F042–F044/F050–F052 | Coverage/catalogue/schema/presentation repairs accepted at their recorded boundaries; no new review without changed inputs or a real discrepancy. |
| 300 translation pins and 125 context-data pins | Accepted. F001 retains only the 30 historical pairs for their source/mechanism owner. |

T13 remains incomplete. Follow-up counts and test totals do not provide a
completion percentage: lot memberships overlap, and origin and executable
verifier inventories are different measures.

The shared eligibility module and its
[completed consumer centralization](../../../reference/eligibility.md#consumer-workflows)
are the implemented baseline. The external handoff was delivered on 2026-10-03;
the coordinator repaired its two identified closing gaps at the user's request:
[F062](T13-execution-follow-ups.md#t13-f062--catalogue-backed-validation-treats-lookup-items-as-selected-equipment)
lookup/selection separation and the remaining Python campaign restriction-table
migration. Affected suites pass (1881 Python and 466 TypeScript cases), with the
77-case captured migration fixture exercised through direct/embedded/consumer
routes. Both repairs stayed inside the centralization assignment; L01–L23 is
unchanged. Reuse the current projection, candidate batches and confirmation
routes. Do not create another constructor; obtain a new exclusive reservation
for actual shared paths needed by canonical activation.

Reuse the delivered direct/browser/embedded and visible-flow proof at its
recorded boundary. Reconcile F016/F018/F020/F021/F028 against the actual result
and reuse anything it completes. Centralization does not itself implement
combat effects, activate pending mechanics or settle source questions.

Combat Lab uses local participants and explicit battle facts, without campaign
services/state, `member_ids`, `battle_number`, purchases or hiring lifecycle.

## 2. Delivery unit: a complete mechanism family

A family carries source-backed canonical facts, compiled projection, modular
behavior, supported Combat Lab access, focused regressions and necessary
documentation together. It may cross T13.2–T13.6; layer boundaries do not require
separate agent dispatches for data, tests, implementation and documentation.

1. Select affected origin/clauses from the existing register. Reuse accepted
   rulings and cases; investigate only the family's actual remaining questions.
2. Reproduce the gap, implement in its responsible layer and add cases that
   detect the changed behavior. Reuse maintained operators and verification.
3. Connect the canonical route to the real modular consumer without injected
   tags, then verify the supported catalogue/editor/analysis flow. A listing or
   successful compilation alone does not prove usable combat behavior.
4. Review with proportional independent coordinator checks; an external review
   may assess several completed family deliveries together.
   Ask the user only for missing source/composition decisions, not accepted
   Shifty/Spectral interpretations.
5. Port stable families in coherent applicable-backend batches. Modular progress
   does not certify optimized engines; never advertise silent unsupported
   execution or use a hidden fallback.

All admitted clauses remain required, including those without a follow-up ID.
Source-blocked clauses keep their existing questions and dependent work; they
are not excluded for scheduling convenience. Preserve the agreed deployment,
hiding, shooting and battle-magic exclusions, with minimum explicit battle
context rather than an autonomous board.

## 3. Priority and observable result

| Order / existing routes | Functional delivery | Findings to absorb and dependencies |
| --- | --- | --- |
| First: canonical pilots — R2/R3/R4/R6 | Shifty and Spirit Hosts' Spectral Touch reach actual supported Combat Lab selection, compilation and execution. | F004/F008, with F056 inside Spectral activation; F060 is complete. Modular contracts already accepted. Coordinate data/compiler writes with centralization. Final pilot completion includes applicable F006/F009 ports and retains F005/F026 pistol limits. |
| Attacks, saves and weapon properties — R2/R3/R4 | Reuse the delivered Vomit Attack milestone; continue with Talismanic Tattoos and remaining local families. | F022/F023; reconcile F002/F014 with their family and decide F015 alongside F014. F024/Q128 and F025/Q146 retain source gates. Reserve actual compiler/engine paths; shared construction is already delivered. |
| Next: ordered sequences — R4/R2/R3/R6 | Correct allocation, reactions, suppression, resources and expiry across ordinary/bonus pools. | F005/F026/Q151 pistol contract together; F013/Q013 recovery and remaining sequence origins. Resolve the actual source question before dependent implementation; reuse accepted sequencing operators. |
| Next: psychology, proximity and commands — R5/R4/R6 | Leadership, neighbors, immunity and conditions produce the admitted consequences. | Existing T13.5 origin families; F061 Halfling Crude Belch; F039/Q158 command activation/range. Add only necessary context. Preserve Crude Belch's first/only-attack loss and generic minimum-one semantics separately. No general battle-magic engine. |
| Then: charges/individual actions and canonical duelists — R6/R2 | Source-qualified charge/contact/action consequences within 1v1; hirelings become canonical duelists. Map, terrain and weather rules are excluded. | Remaining admitted T13.6 clauses; F036/F037/F038 hireling integration; F028 relevant item routes. Reuse loaders/shared legality without campaign lifecycle. |
| Interleaved after each stable family: optimized execution — R3–R7 | Equivalent real modular/NumPy/native behavior for every applicable flow. | F006/F009 plus local/threshold/sequence/contextual ports. Batch by shared execution seam, after modular acceptance; serialize kernel/model/layout/generation writes. Record actual native binary execution. |
| Finish: R7, T14, T15 | Coherent origin coverage, exact-revision certification, integral gate and local phase commit. | F001's historical pins with source owners; already-reserved F057 count repair; product/generated/manifest integration below. No new exclusions, weaker gates, push or deployment. |

The coordinator has delivered **L02/F010 Vomit Attack's canonical modular
replacement** on 2026-10-03. Its source-linked specification passes 7 cases and
kills 4 mutations; normal/bonus consumers and shared construction are preserved.
Reuse the completed milestone and the explicit optimized support boundary.
L03/F008 canonical Spectral Touch is also [delivered on 2026-10-03](T13-spectral-touch.md#l03-canonical-activation--2026-10-03),
including source-linked cases, real modular requests and F056 acceptance. The
optimized support guard remains until L19/L20. L04's four canonical Halfling
heroes are now [delivered](T13-shifty.md#l04-canonical-activation--2026-10-03);
promoted Scouts/Warriors are now supported by [L05](T13-canonical-choices.md).
L05's named tables, Runt active positions and supplied owned-kit route reuse
shared construction. **L06 is in progress**: its [first canonical weapon block](T13-local-weapons.md)
connects eight items (including F023 and F025/Q146), with five new profiles and
source-specific shared access; actual modular attacks pass. The subsequent
[Killing Blow milestone](T13-local-weapons.md#subsequent-l06-milestone-blood-dragon-killing-blow)
now implements Wight/Grave Guard natural-six auto-wounds and parry exclusion,
with saves and physical hit provenance retained. The subsequent
[Shock Rod milestone](T13-local-weapons.md#subsequent-l06-milestone-shock-rod)
adds its canonical access, strike-first/two-hand profile and local 1–4 stun
replacement using the existing injury/reaction pipeline.
[Skull Busta](T13-local-weapons.md#subsequent-l06-milestone-skull-busta) now adds
its first-turn Strength, Concussion, ordinary-helmet Basha and shared active-loadout
restrictions; Knight's Helm is a user-confirmed source erratum (2026-10-04).
F063 tracks pending KB removal/reference cleanup, not L07 behavior. Continue the
remaining L06 hit/wound/critical/poison/parry families; L06 is not closed.
The [paired-weapon milestone](T13-local-weapons.md#subsequent-l06-milestone-long-daggers-and-knuckledusters)
now connects Long Daggers (Hero recipients, Pair and Parry) and Knuckledusters
(normal Strength, Pair). F064 routes Hellblade's exact target categories to
L11, then returns the weapon to L06; F065 retains Concealable's shared carry
and scenario clauses for L05 residual/L18 work before L21. These are dependencies
inside the existing lots, not additional review or test-only dispatches.
The [local modifier and special-save milestone](T13-local-modifiers-defences.md)
connects eight more canonical rules, corrects High Elf skill-table facts,
separates Bitter Moors' wound Valour from the existing hit variant, and resolves
F022's modular save-kind defect. F063 no longer blocks modular implementation
after the user's erratum decision; continue other admitted families.
The [subsequent natural/injury and conditional/recursive blocks](T13-local-modifiers-defences.md#subsequent-l06l07-block--natural-attacks-and-injury-grants)
deliver 34 more canonical rules: Wolf Rat armour exception, intrinsic Lotus,
poison/No Pain grants, Poltergeist removal, Dwarf/Snotling injury and save
clauses, Domnu's magical-only ward and recursive Mourngul attacks. Reuse the
same operators and family cases; these milestones do not close L06–L08.
The subsequent [unarmed/hide/Leadership block](T13-local-modifiers-defences.md#subsequent-l07l08l10-block--unarmed-training-natural-hide-and-leadership)
delivers Domnu Prize-Fighter, Sabretusk armour and the duel portion of
[Crude Belch](T13-crude-belch.md). F061 retains product access; multi-enemy resolution is excluded.
F067 retains the Domnu Bear Hug allocation ruling. In total this autonomous
continuation added 45 canonical rule milestones, without closing T13 or starting
the optimized ports. The local Leadership operator is a real caller's minimal
2D6 path; L10 still owns its variants and L12 its providers/group effects.
The [subsequent L08/L09 block](T13-local-modifiers-defences.md#subsequent-l08l09-block--ordered-natural-attacks-and-one-chosen-reroll)
adds the Priest's independently timed final bite, Sabretusk's exact charge
replacement and Seaguard's first-round spear/one-chosen-reroll contract: 48
canonical rules across this continuation. Neutral empty-hand projection for
unequippable creatures was corrected in the same functional lot. F005/F026/Q151
remain source-gated; continue other admitted allocation/resource families.
The [subsequent L10/L12 block](T13-local-modifiers-defences.md#subsequent-l10l12-block--actual-local-leadership-providers)
adds three source-qualified local leaders and Darksoul automatic Leadership,
consumed by Crude Belch: 52 cumulative canonical milestones. Proximity uses
explicit side/band/distance/standing facts, with optional provider choice.
L10/L12 remain partial for individual rerolls and supplied external conditions;
group tests/routing and mixed-alliance group modeling are excluded. Continue exact psychology/classification
and dependent functional families; L18 owns visible context configuration.
The [L11/L14 Fear block](T13-local-modifiers-defences.md#subsequent-l11l14-block--fear-tests-hits-and-cancelled-charges)
adds three canonical Fear clauses (55 cumulative milestones). Actual initial
charge direction determines cancelled contact or one-round sixes-to-hit;
personal Leadership/provider/Frenzy cases use existing consumers. Both modular
drivers preserve an unengaged pair as unresolved. Generic Fear/Hatred source
summaries were repaired. Remaining involuntary movement/interception and later
engagement facts are F069, consumed with L13/L14/L18; this is partial L11/L14.
The coordinator's remaining implementation
continues with local attack/save families after checking their source gates and
exclusive files. No new constructor or repeated centralization is required.

The next external implementation family is canonical pilot activation or a
source-backed local binding/item family using an accepted operator. Reserve its
actual KB/mirror/registry/adapter paths. If another reserved writer occupies the compiler,
that integration waits; independently owned work proceeds only after checking
its concrete source contract and files. Do not make an external task evidence-only
merely because its executor has lower implementation capacity.

## 4. Parallel lanes and existing dispatches

### Executable lot list — 2026-10-02

The sequence below contains **23 execution lots**; L02's canonical/modular
milestone is delivered on 2026-10-03. L01–L23 are
dispatch numbers inside this plan, not new task/finding IDs or another tracker.
L01 is the existing reserved F057 assignment: reuse its delivery if already
executed, rather than launch it again. The construction-centralization
assignment is implemented and remains outside these 23 lots. F056's
external report is accepted within delivered L03 as of 2026-10-03; reuse it.

Each lot includes its necessary source consultation/decisions, implementation,
canonical bindings/projection, focused cases, affected product connection and
documentation. No separate assignment for these components. Scope is selected
from `T13-obligations.csv` by the mechanisms/families below, preserving
`origin_key` and each admitted clause of compound rows. Reuse accepted behavior;
the lot fixes missing clauses rather than rewriting the whole named family.

| Lot / original tasks | Executable scope and observable output | Entry / main writable boundary | Close criterion |
| --- | --- | --- | --- |
| **L01 — Restore the current gate** / T13.7 | Finish F057's parity-inventory correction for the exact 15 new Fimir/Boglar cases and obtain a valid read-only coverage measurement. | Existing F057 reservation; parity expectation/test and its delivery. No engine or budget rewrite. | Independent corpus-completeness invariant preserved, exact case additions reconciled and current required gate passes; unrelated failures routed rather than hidden. |
| **L02 — Vomit Attack** / T13.2–T13.4 | Delivered 2026-10-03: selected canonical option reaches the source-correct modular replacement, F010 resolved locally. | Compiler/model and modular flow implemented without shared-eligibility changes; [delivery and evidence](T13-vomit-attack.md). | Canonical acceptance/rejection, armour/parry behavior, special saves, injury and whole-pool compositions pass. L19/L20 own optimized ports and L18 remaining product connection; no repeat L02 dispatch. |
| **L03 — Activate Spectral Touch** / T13.2–T13.3/T13.6 | **Canonical modular milestone delivered, 2026-10-03.** F008 active and F056 accepted in the same lot; no repeat dispatch. [Delivery](T13-spectral-touch.md#l03-canonical-activation--2026-10-03). | Accepted F007/R1–R4 reused; canonical/mirror flag, typed trait transport, catalogue status and stale pending table reconciled. Shared eligibility and accepted engine unchanged. | 23 canonical tests; public modular request, seven foreign controls and mixed 6/5 provenance; 10 spec cases/4 detected mutations; 891 affected/24 dependency/34 TS cases pass. Unported optimized execution explicitly refused; completion remains L19/L20 and GUI routing L18. |
| **L04 — Activate Shifty** / T13.2/T13.4/T13.6 | **Four-hero canonical modular milestone delivered, 2026-10-03.** [Delivery](T13-shifty.md#l04-canonical-activation--2026-10-03); no repeat pilot dispatch. F004 retains promoted local-participant access under L05. | Reused accepted S1–S4/F060 and shared construction unchanged; selectable kind/grant/binding plus active mechanic and exact 2A mirror. | Elder/Cook/Thief/Youths select, compile and execute without injection; foreign/raw-mechanic and absence controls hold; 11 source-linked cases/3 mutations. Pistol-only allocation remains L08, ports L19/L20, actual GUI routing L18. |
| **L05 — Finish canonical choices and grants** / T13.2 | **Construction milestone implemented/verified 2026-10-03:** [delivery](T13-canonical-choices.md). Named-table choices, configured promoted Halflings/Runts and supplied complete kits use shared decisions; false markers and legacy stats are reconciled. Remaining source/item effects have explicit later owners. Original scope: complete residual named skills, selectable/automatic grants, explicit mutations/characteristic bonuses, owned versus active loadout facts and supported item access. Absorb F002/F014–F016/F018/F020/F021/F028 and F004's promoted-Halfling local access disposition. | First reconcile the centralization handoff; reserve residual KB/mirrors/registry, actual adapters/compiler and only reproduced shared-decision gaps. | Supported canonical choices have correct recipients, legal/illegal controls and exactly-once projection; markers/legacy paths have truthful dispositions. Unsupported choices retain explicit gates and their L06–L17 execution owner, not a false complete-effects claim. No duplicate constructor. |
| **L06 — Weapons, hits, wounds, criticals, poisons and parries** / T13.2–T13.3 | **In progress:** [eight-item canonical weapon block](T13-local-weapons.md) delivered 2026-10-03, including F023 and separately reviewed F025/Q146. Complete the other local weapon/unarmed profiles, hit/wound modifiers/rerolls, material/target filters, natural-six auto-wounds, poison/immunity and parry variants. | Accepted operators plus actual source questions; local phases/contexts/effects, mappings and canonical weapon paths. Reuse the delivered block; Spirit Knife has its own source/recipient proof. | Canonical real attacks prove each admitted local clause, activation/absence, filter/threshold and relevant interaction. No melee rule is certified through a synthetic unmapped item or excluded shooting/spell flow. Partial weapon progress does not close L06; ports remain L19/L20. |
| **L07 — Saves, injuries, healing and regeneration** / T13.2–T13.4 | Complete natural armour, conditional/ward saves, injury transformations, stun/concussion protection, healing/recovery and remaining regeneration. Include F022 Tattoos, F024/Q128 cloak composition, F013/Q013 Revenant and admitted F047 fire-producer integration. | Resolve required save/recovery source variants first; phases, aftermath/state, compiler and defensive bindings. Preserve accepted F011/F012 thresholds. | Correct save kind/order/modifier treatment and injury/recovery timing/limits on real sequences; fire controls use actually admitted producers without a new battle-magic subsystem. |
| **L08 — Attack allocation, priority and melee pistols** / T13.3–T13.4 | Complete remaining attack counts, natural/extra/unarmed allocations, strike priority, recursive/donated attacks and replacements. Resolve F005/F026/Q151 H2H pistol shots, reload/resource and Shifty pistol-only allocation together. | Accepted Shifty/Spectral/Vomit contracts; pool/round allocation and corresponding compiled weapon contracts; source ruling before pistol activation. | Exact chosen attack/weapon/order and once-only allocation across phases; legacy ordinary/bonus consumers preserved. No fabricated fist, extra shot or shooting subsystem. |
| **L09 — Reactions, resources and special actions** / T13.4 | Complete resource rerolls/one-shots, interruption, persistent cumulative effects, contact/kill reactions, challenges/control/charm, target/attack denial and admitted special-action state. | Shared state/pools/aftermath seams; consult each clause's recipient, expiry and action timing. Extend only required state. | Minimal real sequences prove triggers, decisions, once/expiry, removed/disabled participants and continuation without duplicate consumption. |
| **L10 — Leadership test contract and modifiers** / T13.5 | Implement the shared deterministic test path, dice selection, automatic pass/reroll and individual threshold modifiers required by the origins. Recover source-correct Cold-blooded variants. | Existing characteristics/context/dice contracts; authoritative sources; phases/context and transient resources. | Actual callers use correct dice and threshold/variant, no test for exempt participants, exact reroll consumption and unchanged irrelevant contexts. This is the executable operator for L11–L15, not a contract-only project. |
| **L11 — Fear, Hatred, Frenzy, Stupidity and immunities** / T13.5 | Complete admitted individual psychology/behavior variants and their opponent/charge-direction/timing filters, including F061 Halfling Crude Belch's failed-Leadership first/only-attack loss. Correct conflicting Fear/Hatred/Cold-blooded summaries in the same source-owned implementation. | L10, relevant L08/L09 timing and the inventory psychology source gate; conditions/bindings plus modular contexts/state/rounds. | Source-derived charge/failure/first-combat-turn/mandatory-action consequences and precise immunity exceptions execute correctly. Crude Belch uses its own timed loss, preserving generic minimum-one reductions; no rule invented from a generic summary. |
| **L12 — Supplied external conditions and leaders** / T13.5 | Support source-qualified external conditions/Leadership bonuses affecting either duelist. Reuse existing provider snapshots; do not simulate group Rout, All Alone counts, group auras or provider lifecycle. | L10/L11; caller-supplied active conditions and individual test facts. No extra mutable combatants or group state. | Supplied effects alter the duelist's actual test/action with correct limits; unsupported or missing conditions are explained. Group clauses are explicitly outside scope. |
| **L13 — Animosity, goading and random preparation** / T13.4–T13.5 | Implement band-specific animosity/goading tables, construct orders, bickering/action inhibition, random pre-combat outcomes and required behavior controls. | L10/L11 where a clause uses them; original band tables and existing decision/state seams. | Exact table/recipient/action results, no inappropriate generic Leadership replacement; movement consequences are consumed by L14, preserving the same state/provenance. |
| **L14 — Charges and combat contact** / T13.4–T13.6 | Complete source-qualified charge direction/priority, individual combat action consequences within the duel. Voluntary escape/withdrawal/contact-breaking effects are excluded. Map/weather/terrain modifiers, movement through terrain and target selection outside the pair are excluded. | L09–L13 individual inputs actually needed; existing charge/contact/action seams. No terrain/weather condition switches or board movement. | Correct individual test/failure/action consequences with explicit supported-context limits. No map, deployment, hiding, shooting or autonomous movement/target system. |
| **L15 — Supplied Mazzalupo command effects** / T13.2/T13.4–T13.6 | Reconcile command clauses against 1v1 scope and implement relevant supplied effects on either duelist, with individual limits/duration. Group emission/hearing/recipient determination and missile-only effects are excluded. | L10/L14 where needed; source-backed active command facts and local configuration. Q158 blocks only a relevant individual clause, not an excluded group producer. | Actual duel consequences and expiry match supplied facts/source; no command-network, group movement or spell subsystem. |
| **L16 — Canonical hired swords and Dramatis Personae** / T13.2/T13.6 | **Partially delivered 2026-10-05:** canonical participant/printed-kit route and twenty-three usable base hired-sword profiles, Aldred/Armen and conditional Snorri. Complete remaining optional Marks and Snerik/Strigani gaps listed in the current summary; Aldred's F037 identities and combat gates are resolved. Reuse the existing route. | Centralization handoff and relevant behavior lots; canonical loaders/catalogue/adapters/compiler/product participant choices. | Real hireling profiles compile/select/run without custom-build equivalence, unresolved aliases or campaign hiring/purchases/persistence; source gates remain explicit. |
| **L17 — Composite duelist profiles** / T13.2/T13.4/T13.6 | Implement source-backed companion/mount contributions only where they form one duel combatant's profile/attacks. Reconcile Q084/Q108/Q127/Q147 per clause; independently acting third fighters and group/vehicle systems are excluded. | Source component contracts and relevant L08/L09/L14 operators; a single compiled combatant per duel side. | Correct component attack ownership and applicable transitions within the two-combatant duel. Preserve Gyrocopter/River Boat exclusions; do not invent missing profiles or extra combatants. |
| **L18 — Complete duel-context product workflows** / T13.6 | Integrate the two duelists, supplied conditions and relevant individual actions into Combat Lab catalogue/editor/configuration/analyses. No group editor, battle roster or multi-target combat workflow. | L02–L17 admitted 1v1 inputs stable; existing application/CLI/Tk workflows and centralization handoff. No repeated eligibility migration. | Actual visible duel configuration, unsupported-condition explanations, execution and correctly labeled results work; legacy context-free cases remain usable. A backend test alone does not close this lot. |
| **L19 — NumPy family batch** / T13.3–T13.7 | Port all remaining applicable stable families, including F006/F009, accepted threshold changes and new contextual/sequence inputs, through real vectorized execution. | Modular families/input layout accepted; kernel/preparation/vectorized driver seams reserved. Can begin from a stable subset but this lot closes only when its applicable set is complete. | Equivalent logical dice/decisions/observable state for applicable cases, correct transport/capacity and no modular fallback or silent omission. |
| **L20 — Native family batch** / T13.3–T13.7 | Port the same applicable families through the actual native engine and maintained deterministic replay interface; complete required model/kernel/native layout and build integration. | Accepted modular contracts, stable shared layout from L19 or a coordinated common contract; native adapter/PYX generation/build owner. | Identified rebuilt binary executes the compared cases with matching logical traces/state; no old binary, callback into modular computation, unnoticed fallback or skipped required proof. |
| **L21 — Final integration and canonical coverage** / T13.7 | Reconcile every admitted origin/clause with canonical consumer, cases, supported product path and applicable engines. Repair F001's historical source pairs with semantic review; finalize runtime/scope/pins/generators and current-data/reference integrity. Absorb F041/F045/F046/F048/F054/F055 and required residual integration. | L02–L20 delivered; one data/scope/generator owner. Reuse completed pin lots and source rulings, preserve staging mirrors. | No lost compound clause, false implementation marker or mandatory gate/data defect; reviewed exact pin/scope transitions, current generated artefacts and complete T14 handoff. F053 conditional and F058/F059 optional are not invented prerequisites. |
| **L22 — Independent semantic/parity certification** / T14 | Validate the accepted final implementation against sources/cases and every applicable engine using maintained gates and an independent reviewer. | L01/L21 accepted on the exact delivery and native build; no simultaneous repair of the certified inputs. | Required semantic/parity/coverage evidence current, applicable backends actually run, no unresolved admitted functional defect. Return defects to their existing lot and repeat only invalidated proof. |
| **L23 — Integral gate and local phase closure** / T15 | Review final diff, preserve earlier KB/Web closures and concurrent user work, run required final integral checks and make the scoped local phase commit. | Accepted L22 and matching final revision; coordinator owns Git/staging. | Required gates green, reservations released, phase-owned commit/hash/status/divergence recorded, staging preserved. No push, remote PR or deployment. |

### How to dispatch and close these lots

The table is sequentially executable; parallelism is optional. A missing
prerequisite blocks the dependent clause, not the study/development of unrelated
families. L02's canonical/modular milestone is delivered and shared construction
has handed off; any new writer still reserves the actual paths. L03/L04 close their canonical
modular milestone only, not optimized certification. Do not publish a choice
on an unsupported default backend before L19/L20 supplies that proof.

Before each dispatch, the coordinator fixes the current input revision, exact
origin/clause set, reused evidence, outstanding Q decisions and exclusive files
from the listed responsibility boundary in the README. This is ordinary lot
preparation inside the numbered assignment, not another inventory/review task.
Accepted portions of a broad family are reused; compound clauses can appear in
several lots, with a single final origin reconciliation in L21.

Interpretation/source decisions required by a lot are prepared within it and
resolved in the existing Q/specification/ruling system. Do not invent semantics
to preserve the proposed schedule. A source-blocked admitted clause prevents its
required final closure; retain its planned destination rather than silently
remove it. Revise the owning lot if new evidence changes its implementation,
instead of automatically creating more numbered microtasks.

Every handoff states the implemented behavior, canonical/visible path actually
proved, applicable backend extent, source decisions, affected origin identities,
tests/commands and material remaining blockers. Coordinator acceptance includes
one proportional independent check. Cases, documentation, mutation witnesses
and relevant bug fixes are part of their lot; no extra tasks to review a review.

| Lane | Useful work | Ownership constraint |
| --- | --- | --- |
| Shared construction baseline | Implementation and closing repairs complete; reuse projection, batch decisions, validation and consumer proof. | Reservation released; any next shared writer reserves concrete paths. |
| Coordinator | High-risk modular families; L02 delivered, then remaining attacks/saves, sequences and psychology. Prepare required decisions in the same family. | Reserve engine seams; coordinate shared models/kernel/state. |
| Next external implementer | Canonical pilot activation or bounded local binding/item implementation, with cases and supported product connection. | Disjoint concrete files and reviewed existing operator; advertised runtime support needs applicable evidence. |
| Later external implementer | Canonical hireling integration or stable configuration/editor/analysis connection. | Reserved loader/data/product paths after shared-contract handoff; no rule interpretation in the GUI. |
| Backend implementers | Port a stable family batch to NumPy/native. | Disjoint engine files after modular acceptance; shared preparation/layout has one writer. |

The user launches agents from prompts. Do not launch agents, message external
executors or interrupt their work without user authorization. If no disjoint
functional task is ready, leave a slot free rather than invent low-value work.

Preserve active user-launched assignments. F057's reserved gate repair remains
valid because it removes a concrete certification blocker without another
research phase. F056's external report was accepted within delivered F008/L03
on 2026-10-03; preserve its narrow outputs and reuse the maintained witnesses.
The earlier no-deliverable observation applied only to the preceding revision's
entry. No new standalone witness/review assignment is required.

## 5. Follow-ups are bundled work, not individual projects

The register retains IDs, exact dependencies and closure criteria. This table
changes scheduling without closing findings or replacing ordinary origin scope.

| Finding group | Execution disposition |
| --- | --- |
| F004/F008/F016/F018/F020/F021/F028 | Canonical activation/compilation families, reconciled against centralization's actual handoff; separate legality, facts, runtime support and access. Reuse F035/F017/F019. |
| F002/F014/F015 | Legacy/marker consistency inside the affected family; add a structural guard only if the reviewed maintained contract requires it. |
| F010/F022/F023 | Complete local attack/save/weapon families, including projections and meaningful cases. |
| F005/F013/F024/F025/F026/F039 and F029 | Present only decisions needed by the next functional family; preserve Q IDs and existing ruling system. Assign owner/resume barrier without another decision ledger. |
| F036/F037/F038 | One canonical hireling integration: profiles, starting-skill identities, provenance aliases and local product access. |
| F006/F009 and applicable backend gaps | Stable-family ports; retain actual execution and deterministic/native rebuild requirements. |
| F041/F045/F046/F048/F054/F055 | R7/T15 product/generated/catalogue/manifest integration, or the family changing that path. Required gate failures and current-data defects must be solved before their owning closure; inherited debt is not silently waived. F048 concerns the affected existing Warband Manager presentation path, not campaign import into Combat Lab. |
| F047 | Canonical fire-producer proof in its actually admitted family; retain battle-magic exclusions rather than manufacture a spell subsystem. |
| F049 | Apply isolation to affected negative tests; no standalone audit project to restate the requirement. |
| F053 | Conditional work when a real new citation grammar is admitted; no speculative parser extension or current blocker from hypothetical sources. |
| F056 | Accepted within delivered F008/L03, 2026-10-03; reuse maintained synthetic and canonical mixed-hit witnesses. |
| F057/F001 | Complete the reserved real count repair; disposition 30 historical source pairs with owning mechanisms, consolidate at R7. No blanket repin. |
| F058/F059 | Optional resilience/regression work with the next relevant tool change; not separate functional milestones or new prerequisites for accepted F040. |
| Resolved entries, including F003/F007/F011/F012/F017/F019/F027/F030–F035/F040/F042–F044/F050–F052/F060 | Reuse their accepted extent; reopen only when changed inputs or a concrete observation invalidate it. Historical prose is not a fresh defect. |

## 6. Proportional validation and progress

One family delivery contains code/data, cases, source/ruling references,
affected origin identities, visible-flow evidence, commands and material limits.
Append to a fitting existing family document; no extra report per assertion,
pin or minor correction. Ignored logs support a reconstructible maintained
summary, not a separate exhaustive investigation.

**Validation policy revised 2026-10-03:** minimize test development and execution
time while retaining meaningful proof. Reuse existing cases first. Add a test
only for an uncovered behavior or a concrete regression risk; choose the smallest
maintained test path that distinguishes correct behavior from the relevant fault.
A semantic case or real-consumer test can provide that proof without duplicating
the same expectation in unit, collective, integration and semantic suites. Add
edge/interaction cases or mutation probes only for a specific unresolved risk or
an applicable certification requirement, not automatically for each item/skill.

During implementation run the directly affected cases. Once the lot is stable,
run the affected dependency checks once; repeat or broaden only after a relevant
change, failure or concrete uncertainty. Full semantics, construction, parity
and Web suites belong at their planned integration/certification checkpoints,
not after every small addition. Negative mutations, when needed, remain isolated;
a setup/import exception does not count as semantic detection.

Specific external validation tasks remain useful when they assess a coherent
set of deliveries, a delicate interpretation or a concrete verification gap.
Reuse matching retained results and independently check the unresolved claims;
do not reproduce every author's battery. Another investigation needs a real unresolved semantic
question, discrepancy or T14 separation requirement. Required engine coverage,
mutation/truncation, applicable parity and integral gates still run at the
stable checkpoints specified by the original plan/verification reference.

Report progress through existing family/origin records and maintained tools:

- Canonical configurations newly usable in Combat Lab.
- Admitted behavior families with actual modular execution.
- Applicable optimized paths with equivalent deterministic evidence.
- Source decisions and reproduced defects blocking the next delivery.

Test/report counts and follow-ups closed are supporting evidence, not the main
measure. No new dashboard or duplicate tracker. R7 still reconciles every
admitted clause, including those absent from the follow-up register.

## 7. Closure and consultation

R7 integrates canonical consumers, specifications, product paths and applicable
backend evidence. Scope/pins and generators have one serial owner. Review the
meaning of affected data before refreshing fingerprints; preserve staged
mirrors through the maintained procedure.

T14 certifies the exact accepted T13 revision through existing semantic/parity
infrastructure and the identified native build. Missing applicable evidence
stays pending. T15 reviews the phase diff, required integral/presentation/
generated gates and unaffected KB/Web closures, then makes the scoped local
commit. Preserve parallel work; no push, PR or deployment.

Consult the [original contracts](T13-implementation-plan.md), [T13](T13.md),
[T14](T14.md), [T15](T15.md), [initiative README](../README.md),
[inventory/questions](T13-inventory.md), [origins](T13-obligations.csv),
[follow-ups](T13-execution-follow-ups.md) and the existing family deliveries.
Use the [implementation guide](../../../guides/implement-and-verify-rules.md),
[verification](../../../reference/verification.md),
[architecture](../../../reference/architecture.md),
[eligibility](../../../reference/eligibility.md),
[permanent rulings](../../../decisions/design-rulings.md) and the family's
canonical/original sources, execution bindings and maintained specifications.

This revision implements no rule, accepts no new interpretation, closes no
unresolved finding and starts neither an agent nor certification.

Latest continuation, 2026-10-04: [individual Cold-Blooded](T13-local-modifiers-defences.md#l10-continuation--individual-cold-blooded-tests)
connects the two canonical Lizardmen Psychology grants and Fimir's individual
Leadership variant (152 cumulative clauses). Fear and Crude Belch distinguish
the variants; group Rout is excluded. Six focused cases and affected contracts
pass. Continue individual L10/L11 clauses; neither lot is closed.

The [common Fear continuation](T13-local-modifiers-defences.md#l11-continuation--common-fear-grants-and-supplied-current-conditions) connects 97 canonical band rules, Fearsome, Hideous and weapon/current-condition inputs (149 cumulative canonical clause milestones). Seven compound records retain explicit pending non-Fear clauses; conditioned producers remain F070 within their existing implementation lots. Supplied active conditions are local snapshots, not a spell or campaign engine. L11 and T13 remain in progress; ports still start only at L19/L20.

The subsequent [individual Cold-Blooded block](T13-local-modifiers-defences.md#l10-continuation--individual-cold-blooded-tests)
adds two canonical Lizardmen Psychology grants and Fimir's individual Leadership
grant (152 cumulative clauses). Fear and Crude Belch distinguish the variants;
group Rout is excluded. Continue individual L10/L11 clauses; neither lot is closed.


### Newly resolved semantic gates — 2026-10-04

The user resolved Q128 (cloak as ordinary armour), Q013 (5+ recovery of at most
one wound at own-turn start, unaffected by fire), and F005 (pistol extra attack
and Shifty extra attack coexist). Resume existing L07/L08 implementation with
these contracts; retain Great Thirster and printed skill limits. Source prose
and historical inventory questions are provenance, not still-pending user gates.
See [permanent rulings](../../../decisions/design-rulings.md). Delivery and
modular implementation is delivered in the [accepted-contract block](T13-local-modifiers-defences.md#q128q013f005--accepted-contracts-implemented); T14 certification remains pending.


2026-10-05: [grouped modular continuation](T13-local-modifiers-defences.md#grouped-modular-continuation--2026-10-05)
delivers target facts/modifiers, charm/control, replacement/reaction attacks,
Ethereal/Drunken/fire exceptions, source-equivalent grants, individual Animosity,
leader variants and supplied individual Command consequences. Continue the
concrete remaining dependencies recorded in the existing follow-ups; do not
re-dispatch delivered shared operators or treat the external residual CSV as
current status. Neither modular closure nor optimized ports are declared.


L16 continuation (2026-10-05): the canonical 2B participant and complete
printed-kit route is delivered, reusing shared eligibility and keeping campaign
lifecycle separate. Twelve hired-sword profiles have no intrinsic runtime
blocker. Finish the eight blocked normalized profiles, optional priest Marks
and the two source-missing Dramatis profiles under their existing source gates;
do not rebuild the participant route. See the existing
[grouped continuation](T13-local-modifiers-defences.md#grouped-modular-continuation--2026-10-05).
L16/F036 and modular closure remain open. No optimized port has started.

Grouped target-qualified hireling effects (2026-10-05): Marine Hunter and
Flesh-Peddler are delivered through canonical grants, compilation and modular
attacks. Whaler doubles inflicted damage only against a supplied aquatic
opponent; Halfling Pimp gains +1 to hit an already nominated female opponent.
The editor exposes both supplied facts; invalid nomination recipients or
nonfemale targets are refused. Map movement/capture/rewards remain excluded.
Six focused cases plus the existing modifier suite passed (243 total); changed
catalogue documents validate and the trait/schema registry agrees. Optimized
execution is explicitly guarded until L19/L20; neither modular closure nor
full product certification is claimed. The remaining base-profile blockers are
the twelve rows above, plus optional Marks and source-only Dramatis.

Grouped priest continuation (2026-10-05): Ranald's no-armour restriction and
Taal's no-heavy-armour/no-blackpowder restrictions use shared profile bindings;
the existing printed-kit decision enforces the source-qualified armament.
Both base profiles compile and reject foreign equipment. Haggle/Streetwise
remain campaign-only. Morr's Servant now applies the charge/charged Leadership
exception against Undead despite their usual Psychology exemptions. Its four
isolated behavior cases do not claim canonical access: Morr's Strictures keeps
`implemented: NO` until the ceremonial scythe's S+1/Difficult-to-use variant
is reconciled against generic `weapon.scythe` (which instead adds armour
penetration). Retain that gate and the source note in `catalog/items/trollheim.yaml`;
do not change the generic weapon or use an anonymous profile as acceptance.
Seven focused regressions were added; the existing modifier suite passes all
250 cases. Changed catalogue schemas and documentation validate; publication
was regenerated. Ports remain deferred; no battle-magic, map or campaign behavior was added.

Ulric grouped continuation (2026-10-05): White Wolf Pelt Cloak is a distinct
canonical item/defence, granting the printed 6+ armour save; it does not replace
or activate the shooting-only Middenheim hunting cloak. Its once-only passive
contribution works with the printed mandatory kit and explicit selection.
Shared Strictures forbid armour/blackpowder. Crossbows and helmets being
unfavoured is not converted into a new ban; the printed-kit boundary remains.
Intense Rivals uses existing first-combat-turn Hatred. Primary canonical Witch
Hunter/Warrior-Priest profiles, Sisters of Sigmar and the named 2B Sigmarite
hirelings carry the rival identity; zealots/animals do not acquire it merely
from their warband. Other explicit named-rival identities can be supplied in
the editor via `ulric_rival`, without a broad human/cult-warband fallback.
Eight existing-suite regressions cover armour/Strength, no double contribution,
legal kit and source-qualified Hatred timing/identity; the complete existing
modifier suite passes all 258 cases. Changed schemas, trait registry and
publication checks pass. Optimized execution of
Intense Rivals is refused until L19/L20. Optional Ulric Marks remain pending.

Leadership continuation (2026-10-05): War-Honed grants Fear immunity plus one
optional reroll on the first failed Leadership test, shared across all test
causes in the duel. Declining forfeits that first-failure opportunity. Runtime
callers now retain the returned fighter state; generic boolean-only callers
remain supported for stateless rules and refuse this resource-bearing rule.
User ruling (2026-10-05): use the maintained `warband-group.chaotic`
classification for Enlightened; no separate compiler warband membership list.
Enlightened is a separate canonical special-skill choice, not the compound
Marks of Sigmar entry. It automatically passes Leadership against Orc/Goblin,
canonical chaotic-group, Daemon/Possessed or explicitly supplied Chaos-follower
identity; unrelated opponents retain ordinary tests. No Symbol of Unity effect
or campaign acquisition was activated. The editor/catalogue carries the choice
and optional follower fact. Validation: 289 modifier/Crude Belch cases passed,
including ten new regressions; changed catalogue
schemas, trait registry and documentation pass. L21 must include the new
`.skill.enlightened` origin while preserving the compound source parent's
remaining Symbol of Unity obligation. Optimized guards remain until L19/L20.

L16 priest equipment continuation (2026-10-05): Morr now uses the distinct
`ceremonial_scythe` / `weapon.ceremonial-scythe`: S+1, two hands and no extra
armour penetration. Difficult to use adds no further restriction beyond its
two-handed use. The generic trading-post scythe is unchanged. Verena's printed
ceremonial dagger remains owned, but `profile.active-weapon-restrictions`
forbids using it in any weapon position; the sword-only kit is enforced by the
shared module. Both base profiles are admitted; optional Marks remain pending.
L21 owns the new item/mechanic origin and stale source-pin reconciliation.
Validation for this equipment group: 292 existing-family/shared-adapter/docs
cases pass, with two new regressions; maintained catalogue schemas and
TypeScript typechecks pass. Publication is regenerated with the existing tool.

L16 Sigmar combat continuation (2026-10-05): shared `skill.righteous-fury`
uses the named target identities and maintained evil/chaotic classifications,
with the non-Chaos human-warband exception. It is selectable through Sisters'
canonical special skill and innate to Aldred; his separate source extension
adds Orc/Goblin Hatred. Existing Hatred timing and psychology-immunity rules
apply. Fellblade grants parry only to his printed two-handed sword, including
its poison-free projection, never an empty hand. Combat Master is explicitly
out of 1v1 scope, matching the existing runtime exclusion; it remains listed
as a starting skill without a multi-opponent attack bonus. Aldred is now usable
in addition to the 20 base hired swords. L21 retains source-pin/origin
reconciliation; target-classification completeness remains F064/F070-owned.
Validation: 296 affected-family/loader/documentation cases passed, including
11 new cases in the existing suite; changed catalogue schemas pass. No
optimized engine port or new standalone report was added.

L16 participation/drinking continuation (2026-10-05): Snorri inherits the
maintained Slayer psychology/kit contracts. Supply his pre-battle D6 result
2-6 in the editor/configuration: 2 gives WS/S -1, 3 is neutral, 4 penalizes all
combatants in contact by -1 to hit (including Snorri), 5 gives S+1, and 6 grants
Frenzy as the source's explicit Slayer exception. These persist across player
turns; ordinary Frenzy still ends on knock-down/stun. Result 1 means he never
participates and is excluded, without rolling again or claiming an unconditional
battle distribution. Missing/invalid results and use by another profile are
refused. His Lucky 5+ save remains intact.

Fire-Eater's breath and Inhaling Fire occur in the shooting phase even when
engaged, so neither enters melee; his printed kit is retained and he can fight
unarmed. Armen's Leap/Acrobat/Dodge, Rout-triggered On the Wings of Angels,
Physician serious-injury reroll and glider clauses are excluded; he can duel
with his printed sword. Source text and equipment are preserved. L21 owns
source-pin/origin/scope reconciliation; Snerik's newly available stats do not
close its unique-kit projection gap, and Strigani still has no canonical stats.
Validation: 289 affected-family/documentation cases and one real Tk editor
round-trip passed; nine added cases across the existing family/editor suites.
Maintained schemas and both 2B mirrors pass. Publication is regenerated; no
optimized engine implementation or separate report was added.

T13 reconciliation consolidation (2026-10-05): the six reconciliation lot
deliverables in `tasks/T13-reconciliation-dispatch/` were consolidated into
`consolidated-results.csv` (3394 rows = every audited ID; corrected 36,
reclassified 2, retained 1239, out_of_scope 2117). Two confirmed behaviour
defects and one confirmed construction defect were fixed.
Behaviour: `clan-angrund-kep` selectable True Grit now binds
`skill.tough-as-steel` (true_grit: 1-3 knocked down, 4-5 stunned, 6 out of
action) and Thick Skull now binds `skill.thick-skull` (3+/2+ Stun save),
replacing the Hard to Kill and Hard Head operators they wrongly reused.
Construction: the printed "May not wear armour." clause on 34 profiles across
seven Sartosan/Nippon bands now has a structured
`profile.equipment-restrictions` `forbids: armour-suit` binding, refusing armour
suits while keeping the shield/helmet those same lists sell. Validation: the two
behaviour fixes and the seven-band restriction matrix pass in the existing
construction/modular/knowledge suites; two structural snapshot counts moved by
the seven added profile rules and were re-derived, not broadly refreshed. Scope
classification is unchanged (all corrected rows were already scope=YES).
Remaining groups are recorded as F073 (51 selectable-skill `runtime` rows) and
F074 (equipment-access bearer notes); no engine was certified and T13 is not
declared finished.

F074 equipment-access bearer notes (2026-10-06): the printed per-entry recipient
clauses are canonical `applies_to` facts (172 entries across 69 bands, Mordheim
and Trollheim) plus one structured Slayer vow rule, and `entryReachesProfile` is
the single predicate behind the Combat Lab picker, the direct-selection compiler
and the Warband Manager artefact. `tasks/T13-reconciliation-dispatch/`
`F074-results.csv` carries one explicit disposition per audited candidate (378
rows): 172 applied, 6 structured rule, 4 existing binding, 117 already realised
by their list, 44 out of scope, and 35 awaiting a source decision (origin/House/
Knights/Sniper markers, special-equipment and Sacred Marking grants, and the five
halfling equivalence/cost clauses). F074 closes for its admitted cases; the 35
open rows keep their printed prose and record the exact missing decision. F073
remains open, and T13 is not declared finished.
