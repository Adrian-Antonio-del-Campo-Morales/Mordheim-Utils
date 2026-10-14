# 2A/2B — Consolidated knowledge

Permanent scope, clarification decisions and follow-up references for the
2A/2B integration initiative (Combat Lab and Warband Manager).

The active implementation plan is
[Remaining modular engine work](REMAINING_MODULAR_ENGINE_WORK.md).
The maintained clause-level work queue is
[T13-semantic-analysis.csv](tasks/T13-semantic-analysis.csv).
Neither a plan nor a CSV disposition certifies engine behaviour.

Historical dispatches, intermediate reviews and delivery logs are available in
Git history. They are not additional work queues. Retained operational artifacts
are listed in section 7.

## 1. Purpose and scope of the initiative

- Work branch: `2A2B`. Published snapshot: `9118ca2` (`chore: snapshot 2A2B
  starting point`, 2026-09-25). Execution ends in **local** commits on `2A2B`;
  the snapshot/publication authorization does not authorize pushing later
  implementations or changing `main`.
- Scope: the 19 bands of 2A and 60 of 2B plus their catalogues, integrated
  first into the KB, then into `warband-manager-web`, and finally into
  `combat-simulator`.
- Out of scope for that execution: building deployment, hiding, shooting or
  battle-magic **resolution** systems. Their rules are preserved in full with
  explicit limitations; they are not marked as implemented.
- Applications read exclusively from the consolidated `sources/knowledge`.
  The still-versioned `sources/2A`, `sources/2B` and their exclusive ingestion
  tools are legacy material awaiting removal; their presence does not imply
  another consolidation phase. Preserve any unresolved source contradictions
  listed in [final integration problems](2A2B-final-integration-problems.md).

Phase history (all accepted before this consolidation): preparation T01–T05,
KB integration T06–T08 (phase 1), Warband Manager Web T09–T12 (phase 2).
Combat Simulator (T13–T15) is the only phase still open.

## 2. Governing product boundary (permanent)

Combat Lab and Warband Manager are **independent applications**. They share the
canonical KB and the pure
[warrior eligibility module](../../reference/eligibility.md); they do not share
documents, services or campaign state. The phase order organizes work on shared
rules, it does not establish an integration between the applications.

| Responsibility | Owner and limit |
| --- | --- |
| Legal equipment/skill choices, recipients, variants, loadout restrictions | Shared TypeScript eligibility module, used directly by Warband Manager and locally through the embedded Python adapter by Combat Lab; no duplicate validator. |
| Canonical bindings and characteristics/weapon/effect projection for simulation | Canonical KB and Combat Lab Python compiler. Legal selection does not imply implemented combat support. |
| Template ids, `member_ids`, `battle_number`, mutation acquisition, final withdrawal | Warband Manager. Combat Lab neither produces nor calls these. |
| Band rout, group psychology, multi-recipient combat | Outside Combat Lab scope (1v1 duels). |
| One mutation's combat modifiers | Combat Lab, from its own selection/compilation over the KB; it does not consume `campaign.special_rules`. |
| Individual actions and psychology admitted in T13 | Minimal two-combatant duel context. No groups, no independent third parties, no map/terrain/weather rules. |

**Combat Lab remains a 1v1 duel simulator** — see the permanent ruling
[Combat Lab remains a 1v1 duel simulator — 2026-10-04](../../decisions/design-rulings.md#combat-lab-remains-a-1v1-duel-simulator--2026-10-04).
Excluded from Combat Lab (not future implementation tasks):

- group Rout tests, group casualties/psychology, All Alone enemy counting;
- multi-target resolution and independently simulated third participants;
- map/terrain/weather rules (fog/Mystic Mist, water/aquatic combat, swamps),
  including caller-supplied map-condition switches;
- voluntary escape, withdrawal and contact-breaking that ends the duel without
  resolving it (no board-movement subsystem);
- shooting/casting resolution, post-duel capture, group rally/command networks;
- healing/support of other models (Shallya Mercy/Healing Hands; post-battle
  Surgery).

Still admitted: individual tests, charges, attack sequences, escape and
conditions affecting the two duelists; an external aura/leader/temporary effect
may be supplied as an explicit current condition or bonus of a duelist. Commands
are considered only for their supplied effects on the duel. Preserve complete KB
rule text and split individual consequences from excluded group clauses.

## 3. Permanent design rulings

The authoritative text of every lasting decision lives in
[`docs/decisions/design-rulings.md`](../../decisions/design-rulings.md). Do not
duplicate it here; this is only an index of the rulings that originated from
the 2A/2B work.

| Ruling | Anchor |
| --- | --- |
| Duel engine (modular oracle): criticals, WS 0, Strike Last, phase order, Force of Will, synthetic hits, poison timing, stateful equipment, Luck, Kusara/Whipcrack, dagger armour bonus | [#duel-engine-modular-oracle](../../decisions/design-rulings.md#duel-engine-modular-oracle) |
| Spectral Touch Q019 composition/order | [#spectral-touch-q019](../../decisions/design-rulings.md#spectral-touch-q019) |
| Shifty S1–S4 modular composition contract | [#shifty-s1s4](../../decisions/design-rulings.md#shifty-s1s4) |
| Knight's Helm source erratum (F063) | [#knight's-helm-source-erratum--2026-10-04](../../decisions/design-rulings.md#knights-helm-source-erratum--2026-10-04) |
| Combat Lab is a 1v1 duel simulator | [#combat-lab-remains-a-1v1-duel-simulator--2026-10-04](../../decisions/design-rulings.md#combat-lab-remains-a-1v1-duel-simulator--2026-10-04) |
| Bloated Squishy overrides No Pain (Q037) | [#bloated-squishy-overrides-no-pain--q037--2026-10-04](../../decisions/design-rulings.md#bloated-squishy-overrides-no-pain--q037--2026-10-04) |
| Sea Dragon Cloak is armour (Q128) | [#sea-dragon-cloak-is-armour--q128--2026-10-04](../../decisions/design-rulings.md#sea-dragon-cloak-is-armour--q128--2026-10-04) |
| Curse of the Revenant recovery (Q013) | [#curse-of-the-revenant-recovery--q013--2026-10-04](../../decisions/design-rulings.md#curse-of-the-revenant-recovery--q013--2026-10-04) |
| Shifty and pistol special attacks coexist (F005) | [#shifty-and-pistol-special-attacks-coexist--f005--2026-10-04](../../decisions/design-rulings.md#shifty-and-pistol-special-attacks-coexist--f005--2026-10-04) |
| Voluntary escape does not belong to Combat Lab | [#voluntary-escape-does-not-belong-to-combat-lab--2026-10-04](../../decisions/design-rulings.md#voluntary-escape-does-not-belong-to-combat-lab--2026-10-04) |
| Shallya healing does not permit self-healing | [#shallya-healing-does-not-permit-self-healing--2026-10-05](../../decisions/design-rulings.md#shallya-healing-does-not-permit-self-healing--2026-10-05) |
| F074 equipment bearer rulings | [#f074-equipment-bearer-rulings--2026-10-06](../../decisions/design-rulings.md#f074-equipment-bearer-rulings--2026-10-06) |

Construction/KB modelling conventions and the campaign-application rules also
live in that file under
[#construction-and-kb-modelling](../../decisions/design-rulings.md#construction-and-kb-modelling)
and
[#campaign-application](../../decisions/design-rulings.md#campaign-application).

## 4. Clarification register (F074 residual origins)

Formerly `tasks/T13-clarifications.yaml`. A resolved entry clarifies
meaning/scope; it does not certify implementation. Original audit IDs are
permanent. Match origin ID + raw effect-text SHA-256 before reusing a decision.
User rulings override source-review interpretations.

| Id | Scope | Decision | Remaining work |
| --- | --- | --- | --- |
| `F074-brood-dagger` | YES | Printed dagger restricts the bearer to Henchmen; not merely a free-dagger price condition. | Encode the Henchman entry restriction in shared eligibility. |
| `F074-crooked-moon-daggers` | YES | Poison Daggers belong to the Fanatic list; their appearance on the ordinary Night Goblin list does not grant them to ordinary Goblins. | Remove/restrict the incorrect general-list offer; keep the Fanatic route and its Black Lotus effect. |
| `F074-pirate-variants` | YES | Qualifiers select warband variants: Estalian adds rapier/heavy armour and removes crossbows; Wasteland adds handguns. Keep other prohibitions conjunctive. | Reconcile affected offers against the canonical variant; no nationality selector. |
| `F074-forest-bosspole` | YES | Bosspole recipients are Chieftain and Bosses, not every Hero; its spear contribution and Animosity immunity affect the duel. | Connect the special-equipment route and its individual contributions. |
| `F074-halfling-aliases` | YES | The Cook-only footnote is about parenthesized culinary aliases; it does not prohibit generic dagger/hammer/axe/sword/helmet for other list users. | Presentation only; no mechanical bearer restriction. |
| `F074-mare-heavy-armour` | YES (user) | Web version prioritized over the conflicting PDF: heavy armour in the Footman list is restricted to Paragon, Gallant and Redeemed Knights. | Applied in KB/2A staging; retain the shared recipient regression. |
| `F074-mare-lance` | YES | Knight-only in both tables; the Paragon has a separate explicit lance prohibition. | Encode the entry restriction; preserve Vow of Poverty; the modular unsupported-lance guard is separate. |
| `F074-mare-mounts` | NO | Barding/warhorse entries belong to excluded mount-equipment support. | Keep source/campaign availability; do not add mounted combat. |
| `F074-house-equipment` | YES | A House is selected for the whole warband; Fierezza/Halcon/Baluardo qualifiers are explicit. | Transport the selected House into the shared equipment decision. |
| `F074-lizard-poisons` | YES | Skinks use these poisons only on missile weapons; Saurus may use them on melee weapons. | Publish species+weapon-qualified eligibility (Saurus melee admitted, Skink melee refused). |
| `F074-reptile-venom` | NO | Belongs to Skink Henchmen missile weapons and lasts one battle; no admitted melee contribution. | None required for the duel. |
| `F074-lizard-sacred-marks` | YES | Sacred Markings Hero-only, at most one; Oversized Jaws Saurus-only (modifies bite); Poison Glands Skink-only (replacement bite). | Connect source-qualified Hero/species eligibility and the admitted bite contributions. |
| `F074-sniper-equipment` | YES | Sniper is a chosen Modus Operandi of a Hero other than the Silent Master, not a missing profile. | Project the specialization into shared eligibility. |
| `F074-underworld-leaders` | YES | The warband has two leaders; Man Catcher is Leader-only on both faction lists, so Goblin Bully and Skaven Slum Lord qualify. | Restore source-backed access for the two canonical leaders. |
| `F074-wood-elf-ithilmar` | YES (user) | Local Ithilmar weapon/armour entries restricted to Heroes, including promoted Henchmen; discount/rarity are separate acquisition conditions. | Applied in KB/2A staging; retain the promotion.hero regression. |

The former register also carried per-origin `effect_sha256` fingerprints and
source URLs (`broheim.net` / `mordheimer.net`); recover them from Git history
if a clarification must be re-validated.

## 5. Current progress and remaining work (T13–T15)

Use [Remaining modular engine work](REMAINING_MODULAR_ENGINE_WORK.md) for the
execution sequence and [the semantic CSV](tasks/T13-semantic-analysis.csv) for
individual pending clauses. Do not reuse historical delivery counts or profile
availability claims as the current implementation state.

T13 modular implementation remains incomplete. Complete admitted consequences,
canonical access and necessary product inputs together. NumPy/native ports
(L19/L20), independent certification (T14/L22) and integral closure (T15/L23)
remain separate work; the active modular assignment does not authorize them.

The durable interpretation of former lot identifiers and findings remains in
Git history and the index below. Permanent user rulings are authoritative in
[design-rulings.md](../../decisions/design-rulings.md).

## 6. Open follow-up findings

Formerly `tasks/T13-execution-follow-ups.md` (deferred findings discovered during
T13 execution). Resolved findings are not repeated here. The identifiers remain
the stable keys; full detail is in Git history.

Open / incomplete: `F001` (inherited semantic failures and stale source pins) ·
`F004` (Shifty promoted access) · `F005`/`F026`/`Q151` (melee-pistol allocation
and reload/save contract) · `F006`/`F009` (optimized Shifty/Spectral Touch ports)
· `F013` (Curse of the Revenant implementation) · `F024` (Sea Dragon Cloak
composition) · `F028`/`F065` (residual item/choice projections) · `F036`
(canonical hireling combat route) · `F047` (Boglar fire-magic witness) · `F057`
(parity inventory count gate) · `F061` (Halfling Crude Belch first-attack loss) ·
`F063` (Knight's Helm KB/reference cleanup) · `F064`/`F070` (Hellblade target
facts; conditional Fear sources) · `F067` (Domnu Bear Hug third attack) · `F068`
(keeper/target/charge facts) · `F069` (Fear vs involuntary movement) ·
`L19`/`L20` optimized ports · `T14`/`T15` certification and closure.

## 7. Artifacts intentionally kept in this directory

- [Remaining modular engine work](REMAINING_MODULAR_ENGINE_WORK.md): active
  implementation plan and completion criteria.
- [Semantic analysis](tasks/T13-semantic-analysis.csv): maintained clause-level
  queue, contracts, provenance and evidence.
  Each row is identified by (`id`, `clause_id`), using the current rule ID;
  historical IDs remain in Git. The historical `implementation_batch` column
  is omitted. Tracking uses two JSON fields:
  `pending` contains `work`, `review` and `requires` only when they differ from
  defaults (`none`, `reviewed`, `[]`); `verification` is an array starting with
  `inspection`, `executed` or `none`, followed by the evidence references.
  Notes retain specific constraints rather than serialized historical reviews. The pre-compaction history is
  available at commit `cee529cd`.
- [Obligations](tasks/T13-obligations.csv): input to the construction matrices
  and `verification/audit_export.py`.
- [Source scope review](tasks/T13-audit-scope-review.csv): input to
  `verification/audit_export.py` and the source-review guide.
- [Final integration problems](2A2B-final-integration-problems.md): source
  contradictions and modelling gaps with exact identities and closing criteria.

The superseded modular implementation plan, scratch assignment, C/D delivery
CSVs and independent scope/equivalence review CSVs have been removed. Their
historical content remains in Git; the maintained semantic CSV is not rebuilt
from those older snapshots.
