# Shared warrior eligibility

`packages/typescript/domain/eligibility/index.ts` is the maintained source of equipment and skill eligibility used by Warband Manager and Combat Lab. It contains the existing Warband Manager construction contracts and the Combat Lab profile, variant, prerequisite and loadout rules. It accepts plain facts and returns decisions, without campaign state, UI, IO or a combat engine.

Warband Manager imports the module through its domain/application adapters. These adapters read the generated knowledge artefact and the current warrior's facts. Existing distinctions between manual corrections and rolled advances are preserved. Campaign purchases, injuries, advances and persistence remain application responsibilities. Existing item-specific restrictions were moved with their current semantics, including legacy name matching; extraction does not expand the supported rules.

Combat Lab projects canonical YAML and build selections in `mordheim_construction/eligibility.py`. MiniRacer runs the generated JavaScript inside the Python process. Node is needed to rebuild the bundle during development, but is not needed to run Combat Lab. A process-local runtime and catalogue cache are protected by a lock. The bundle is included in the Python package. No server or network connection is involved.

Eligibility and duel support are separate: a legal choice may still lack an implemented combat effect. Combat Lab keeps effect folding, characteristic compilation and supported-effect diagnostics in its compiler. Warband Manager keeps campaign transitions and UI presentation. Custom/free builds retain their existing access behavior.

The native 2B Sister's Blessing of Sigmar uses `compiler.sister-special-skills`
in the shared `requiredInitial` stage to require two distinct starting choices.
The participant projection borrows the existing Sisters table, preserving
Matriarch-only eligibility. Protection of Sigmar is a valid starting choice with
an explicitly excluded magic effect; it grants no spell behavior in Combat Lab.

L06 Skull Busta uses one shared active-loadout predicate in specialist and batch
queries: mounted use and other weapons are refused; shields are allowed.
`BuildFacts.mounted` and `ConstructionOperationContext.mounted` are supplied facts
defaulting to false. Owning a holstered item does not mean using it. Canonical
Savage Gobbo Boyz access is excluded in the common profile projection; adapters
transport facts without repeating these decisions.

L05 extends the existing projections, not their ownership. Published named
`profile.skill-access` tables govern both offering and final membership;
source-URL inference is only a fallback when no table exists. A published empty
table remains an explicit knowledge gap. Combat Lab displays unsupported named
members with a reason and retains their IDs when converting UI selections.

For local configured participants, `variant_ids=("promotion.hero",)` supplies a
Hero result over a Henchman profile. `configuredProfile` changes a copy's type;
`applies_to.profile_types` and profile IDs are conjunctive. No campaign promotion
eligibility, advance roll, ordinary skill-list choice or persistence is computed.
Runt active weapon limits count occupied one-handed positions, including equal
weapon IDs in two positions, separately from owned holstered weapons.

An equipment entry may also name its printed recipients in `equipment-access.yaml`:
`applies_to` carries the profile kinds (`profile_types`) and profile ids the note
limits that line to, while `notes`/`notes_i18n` keep the printed prose for
presentation. Unlike a rule's `applies_to`, whose selectors are conjunctive,
these selectors are the **union** of the printed clause, because the source
enumerates a set of members ("Heroes and Marksmen only" is the `hero` kind
together with the named henchman). An entry without the member reaches every
profile that declares its list, so absence of a restriction stays distinct from
an explicit one, and the declared granularity is one entry of one list of one
band: a clause never narrows the list itself nor the same item on another band's
list. `entryReachesProfile` is the single predicate behind both projection paths
(`profileEquipmentItems` and `buildAccess().addLists`), so a direct selection
that never passes through the picker meets the same verdict as the offer. The
same predicate reads a named denial, `applies_to.excluded_profile_ids`: the
declared profile never receives the line, even when the recipient selectors and
the variant gate reach it ('Sniper only ... not available to the Silent
Master').

The contracts below are decided by the same owner, never item by item:

- `EquipmentLimits.item_copy_limit` (`EquipmentItemCopyLimit`) bounds how many
  copies of one named item or mechanic id a member may **possess** at once, with
  the profiles the source exempts and the bound they may carry instead ('only
  the Matriarch and Sister Superiors may carry two Sigmarite warhammers'). It
  bounds the owned kit, not the active slots, and `validateConstruction` counts
  an occurrence that is both selected and owned once.
- `ProfileFacts.required_equipment` (`RequiredEquipment`) is an obligation to
  **acquire** one item of a family: `kinds` are item kinds, or an item/mechanic
  id when the clause names one canonical object ('must include a Chaos Dwarf
  Blunderbuss'), and `excludes` names the printed items that never satisfy it
  ('a simple dagger is not acceptable'). The source obliges the purchase, never
  attacking with that weapon, so the contract is a whole-set requirement and not
  an active-slot one.
- `ProfileFacts.poison_application` with `poisonApplicationIssue` decides which
  weapon kinds a governed poison may coat for a bearer ('Skink Heroes on missile
  weapons; Saurus on close combat weapons'). A bearer the clause does not
  qualify is never refused there, and the poison's recipient set stays the
  canonical one. The missile reading is shared (`ranged-weapon` includes the
  catalogue's ranged tags) so a flattened weapon record is not misread as a
  close combat weapon.
- `ProfileFacts.active_weapon_permits` is the printed **permitted** active-weapon
  set ('may only use a sword, dagger or Mage Staff in battle'). `tokenPermits`
  reads it so an active main/off/extra weapon outside the set is refused with
  the admitted tokens named, while owning an item the clause does not admit
  remains legal. A permission clause never emits an empty forbids row.
- `ProfileFacts.missile_weapon_limit` (`MissileWeaponLimit`) bounds how many
  missile weapons a member may **possess**, with the printed items or mechanic
  ids it exempts ('only ONE non-pebble or non-slingshot missile weapon'). It
  counts units, so two copies of one weapon are two, and it stays separate from
  the active slots and from any shooting resolution.

`profileFactsProjection` materialises these families onto the canonical profile.
The generated knowledge artefact of the web consumer mirrors the same predicate
and publishes the same facts: `profile.required_equipment`,
`profile.poison_application`, `profile.missile_weapon_limit` and the band
`equipment_limits` (including the nested `item_copy_limit`). A rule the artefact
cannot express for a build selection stays a recorded construction gap, not a
silent allow.

An intrinsic armour clause is not a legality rule: a published
`trait.natural-armour-save` (with `natural-armour-unmodified` and
`natural-armour-negated-by-magic`) is folded onto the fighter by the Combat Lab
compiler and the modular engine keeps the better of the worn armour and the
natural save, so the printed constant is never added twice. The declared kit
item travels in the profile's `fixed_equipment`.

The campaign domain carries no `poison_application` and no build selection for
the House Guard 'House' or the Silent Brotherhood 'Modus Operandi' lines:
neither band publishes a warband variant and `identity.mercenary_variant` names
a published one, so Warband Manager cannot configure that selection and the
condition line is offered to no profile instead of to the wrong bearer. The
predicate is implemented and Combat Lab transports the real selection; the
visible product input remains to be built.

A printed `compiler.promoted-hero-skill-access` grant is projected as
`promotion_skill_access` on the profile facts: the canonical Henchman carries
the tables there and never in `skill_access`, while the configured Hero (or a
build declaring `promotion.hero`) receives them in both. The advance flow
consults the field only for a warrior whose kind is hero, so the tables are
never offered before the promotion happens.

`FighterBuild.owned_item_ids=None` leaves the complete carried kit unspecified;
an explicit tuple, including `()`, invokes shared final validation during
compilation. Legal unmapped items can be owned without becoming executable duel
effects. `configuration_context` supplies canonical profile/band projections,
ownership and active slots to the same batch operation used by
`CombatCatalogue.validate_configuration`. The shared module keeps its existing
blocking/informational policy; the catalogue exposes all reports. Unspecified
kit compilation is not proof of mandatory owned equipment. Visible editing of
these supplied facts belongs to the remaining L18 product integration.

Combat Lab's 2B hired-sword/Dramatis participant projection uses canonical
hireling ids and the same shared eligibility engine, without campaign hiring.
`resolveHirelingKit` / `hirelingKit` resolve one complete printed kit: fixed
quantities, whole alternative groups and optional items. Unspecified ownership
selects a compatible kit; explicit ownership must match its complete multiset.
`boundEquipment` exposes the same refusal to configuration callers. Printed
item qualifications are local projection facts: Crimashin's dagger is gromril;
the Holy Man's staff uses the double-handed weapon mechanic. They do not
change the generic dagger/staff catalogue. Native profiles with pending
intrinsic duel clauses are refused before compilation; name-only entries stay
in the source catalogue but are not offered as editable stat profiles.

See [L05 delivery](../knowledge/2a2b/tasks/T13-canonical-choices.md) for the
source-backed recipients, marker contract and still-gated behaviors.

`EquipmentLimits.exempt_profile_ids` exempts a profile only from `required_tag`;
`max_missile_weapons` still applies. For Outlaws, the Cleric may omit the bow
but may not carry two missile weapons.

Consumer centralization is complete for the previously supported equipment and
skill workflows. The contracts, consumer behavior and retained responsibilities
below describe the implemented baseline; new T13 combat effects and product
inputs keep their own delivery boundaries.

## Batch construction contract

The module owns two batch operations over a neutral `ConstructionContext`:

- `selectionDecisions(context, proposals)` evaluates proposed additions,
  replacements and removals together and returns one decision per proposal
  (`allowed`, blocking `issues`, informational `reports`). A `remove` proposal
  never blocks: an invalid existing selection stays visible and removable.
- `validateConstruction(context, { draft })` judges the complete configuration,
  including mandatory choices and whole-set limits. `draft: true` permits an
  unfinished mandatory choice so an editor can still offer the option that
  completes it; final confirmation uses the default. The catalogue-backed
  Python operation also defaults to confirmation; pass `draft=True` explicitly
  when evaluating an unfinished draft.

Both compose the same primitives as the existing wrappers (`equipmentIssue`,
`equipmentSetIssues`, `skillIssue`, `loadoutRestriction`). A caller must not
implement a second interpretation of either operation.

Informational codes (`equipment_unknown_item`, `skill_pending_special_list`,
`construction_clause_unstructured`) are owned here through
`INFORMATIONAL_ISSUE_CODES`/`issueIsInformational`; they stay visible without
refusing the choice. Neutral defaults (`weapon.fist`, `armour.no-armour`,
`material.normal`) are the absence of an equipment choice and are never
refused by access.

The single fact projection lives here too: `profileBindings`,
`profileFactsProjection`, `bandEquipmentForbids`, `bandEquipmentLimits`,
`profileSkillLists` and `selectedRuleBindings`, exposed to desktop consumers
as `profileFacts`, `bandFacts`, `profileSkillLists`, `profileBindings` and
`selectedRuleBindings` in `bridge.ts`.
`profileFactsProjection` materialises the profile's equipment access —
declared lists and their loadouts, the fixed kit and the equipment concessions
of its applicable rules — through the catalogue mappings, the same resolution
the offering layer uses, so offered options and decisions cannot drift apart.
A canonical projection always carries a filterable list, empty included: a
profile that declares no list buys no listed equipment, not anything. `null`
stays reserved for a caller that cannot supply the canonical catalogue
(custom and free-build contexts). Only equipment families are concessions:
skill and mechanic bindings never reach the access. A family-prefixed
concession without an item record (`weapon.vomit-attack`) stays offered —
canonical builds select it as their main weapon — and the missing record is
reported informationally (`equipment_unknown_item`), never refused.
`constructionCall` resolves
canonical item facts for the candidates (indexed by item id and by mechanic id
through `catalogueItemFacts`) in a single batch, and a transport or projection
failure raises instead of falling back to a permissive local rule.

`context.items` is a lookup, not a declaration of owned or selected equipment.
Complete validation checks equipment selections, active slots and `possession`;
unselected catalogue entries cannot cause access refusals, satisfy a mandatory
choice or contribute to a whole-set limit. Unknown selected or owned ids still
receive the access check. The maintained transport regressions exercise the
installed catalogue, in addition to the direct fixture exports.

The shared fixture `tests/fixtures/eligibility/construction-context.json` runs
through the direct TypeScript exports and through the embedded Python runtime
(`tests/python/construction/test_construction_context_parity.py`), so both
entry points must return equivalent decisions for equivalent facts.

## Consumer workflows

Both products obtain option states and final legality from the shared module.
Confirmation revalidates the resulting configuration so direct calls or stale
GUI state cannot bypass blocking issues. Campaign consumers supply warrior facts
without constructing synthetic duel fighters. Manual skill changes, rolled
advances, free builds and existing quantity conventions retain their contracts.

Combat Lab's supported editor and comparison workflows follow these decisions:

- Incompatible options stay visible, disabled with their reason. Availability
  is recalculated when relevant selections change.
- A selection that becomes invalid stays visible and removable; execution is
  blocked until blocking issues are corrected. Loading and rebuilding preserve
  applicable selections, including fields not exposed by the editor.
- Comparisons omit incompatible configurations and explain the omission. They
  never change the selected off hand to make a candidate legal; valid hand
  exceptions remain usable and result labels describe the actual simulated kit.
- Runtime support is reported separately from legality. Final compiler
  validation remains a confirmation gate.

Use existing selection widgets and batch candidate queries against the installed
catalogue. Preserve canonical stored values, keyboard operation and locale
refresh; adapters and UI code do not reinterpret bindings.

## Construction boundary for phased implementation

The shared module is already implemented and used by both products. A task
labelled "construction", "selection" or "validation" is not an instruction to
build a second implementation. Reuse the current decisions and adapters first.
Centralization preserves the previously supported rules; it does not claim that
every newly inventoried combat effect or canonical binding already executes.

| Question being answered | Owner | Proof required |
| --- | --- | --- |
| May this profile select the equipment, skill or combination? | Shared TypeScript eligibility; canonical KB supplies the facts | Source-derived allowed/refused cases through direct exports and the embedded Python runtime |
| Did the adapter supply the same relevant facts and return the decision correctly? | Browser projection or Python `eligibility.py`/`bridge.ts` | Actual consumer/transport cases and current bundle identity |
| Does a legal selection grant the intended characteristics, weapon or effect exactly once? | Canonical runtime binding and Combat Lab Python compiler | Canonical compilation, recipient/absence and accumulation cases |
| Does that compiled effect behave correctly in a battle? | Modular engine first, then applicable optimized engines | Source-derived dice/decision/state cases and backend parity |
| Can the product offer and execute the supported choice? | Product catalogue/application/UI | Visible workflow, preserving the shared legal-choice decision |

A legal but unsupported effect may be refused by Combat Lab's runtime gate.
That refusal does not redefine the tabletop selection as illegal. Conversely,
an injected effect tag proving a combat sequence does not prove canonical access.

For [2A/2B integration](../knowledge/2a2b/README.md), T09's accepted Web flows
remain accepted. T13.2 is consumer reconciliation, binding/effect compilation
and activation work using this existing module. F035 revalidates earlier evidence
after extraction; it is not a task to implement the module again. Before
repairing an older finding, classify it as already resolved, missing canonical
fact/binding, adapter defect, reproduced shared-decision defect, unsupported
combat projection or missing product access. Retain exact evidence and existing
finding IDs; extraction alone neither closes every finding nor proves a defect.

## Ownership and retained adapters

| Responsibility | Maintained location |
| --- | --- |
| Rule decisions and eligibility contracts | `packages/typescript/domain/eligibility/index.ts` |
| Desktop catalogue transport | `packages/typescript/domain/eligibility/bridge.ts` and `mordheim_construction/eligibility.py` |
| Generated Python resource | `mordheim_construction/_eligibility.js` |
| Browser KB projection and campaign construction entry points | `packages/typescript/domain/campaign/construction.ts` |
| Python profile resolution and effect compilation | `mordheim_construction/selection.py` and `compiler.py` |
| Isolated construction mutation seams | `mordheim_construction/restrictions.py` |
| UI labels, slot presentation and runtime availability | Combat Lab catalogue and the web shell |

The old Python eligibility tables and browser-local validators have been
replaced by shared-module calls. Retain the construction entry points and
mutation wrappers while their consumers use them; their existence is not a
second rule implementation. Catalogue item mappings used for prices and duel
effect bindings are also live data adapters.

Legitimately retained by each product:

- Warband Manager keeps money, inventory movement, purchase availability,
  hiring, advance lifecycle and persistence transitions.
  `KnowledgePort.can_gain_experience` retains Brainless/Dead/Animal rule
  references as roster/XP lifecycle logic outside equipment and skill selection.
- Combat Lab keeps compiler/runtime effect support, characteristic compilation,
  disabled-option presentation and analysis reporting.
- Legacy item-specific restrictions live once in
  `warriorEquipmentRestriction`, used directly by the web service and through
  `KnowledgePort.warrior_equipment_restriction` by Python campaign confirmation.
  The Python engine keeps thin `profile` and `loadout` stage wrappers; its local
  bearer/weapon-limit table has been removed. Stage facts preserve the existing
  confirmation order, canonical Weapons Training/Expert ids, restriction-note
  messages and the `starting_grant` quantity convention. The web's default
  combined operation retains its existing `fixed` convention. The 77-case
  `tests/fixtures/eligibility/warrior-equipment.json` records the entry decisions
  and is exercised by direct TypeScript, embedded JavaScript and Python gates.

## Changing rules

1. Edit the pure TypeScript module and its tests. Keep canonical KB IDs and existing decision ordering.
2. Run `npm run build:eligibility` to generate `packages/python/roster-construction/mordheim_construction/_eligibility.js`. Do not edit that file directly.
3. Run `npm run check:eligibility` and the affected maintained cases through direct TypeScript and embedded Python execution. Add cases only for uncovered behavior or a concrete regression risk. Projection or transport changes also check the affected UI/campaign consumer paths; broader suites run at stable integration checkpoints. Reuse existing fixtures rather than duplicate the same expectations across layers.

CI checks bundle freshness and both consumers. The Python freshness test compares the bundle's source digest with the maintained TypeScript files. Regeneration is required when either `index.ts` or `bridge.ts` changes. Python installation declares `mini-racer==0.14.1`; this is a runtime dependency, not an optional fallback to duplicated Python decisions.

The local `python tools/mordheim-utils.py run-ci` gate includes the same bundle
check and Python transport tests. Windows packaging collects the JavaScript
resource and MiniRacer's native runtime. Rebuild changed eligibility sources
before creating an executable; the target machine needs neither Node nor a server.

The extraction changes no campaign file format and moves no campaign state into Combat Lab. To roll back it must be reverted together with its consumer adapters; there is deliberately no second rule implementation to maintain.

The neutral item vocabulary also carries source-declared `thrown` and
`constant-save-cloak` tags. Slayer `non-thrown-ranged` restrictions exempt only
items carrying the former tag; constant-save cloaks use the latter. A supplied
`open_flame` fact covers lit carried items independently of the active weapon.
Loadout combination decisions receive both selected and innate mechanics;
restrictions such as Ethereal/Dodge exclusivity apply to either origin.

Construction item facts may use canonical mechanic aliases via shared
`carriedItemFacts`. The web reader supplies its existing item enumeration only
when an exact record is absent; Combat Lab uses the same merge. Direct records
retain priority, tags are merged, and unknown mechanics remain unknown. This
fact resolution creates no item record, purchase or inventory ownership and
preserves the reader's deferred-catalogue error contract.

`profile.active-weapon-restrictions` bindings carry `forbids` tokens for active
main/off/extra weapon positions only, and may carry instead (or additionally) a
permitted set in `parameters.allowed_kinds`, projected as
`active_weapon_permits` and read by `tokenPermits`. The shared projection
publishes `active_weapon_forbids` only when the clause really forbids tokens;
both selection and complete validation apply the refusal and name the admitted
set. These restrictions do not forbid possessing an inactive item (for example,
Verena's printed ceremonial dagger, or a weapon a permitted set does not
admit), because the clause bounds use and not ownership. Ordinary equipment
restrictions retain their whole-kit semantics, and a profile-scoped missile
bound (`missile_weapon_limit`) decides possession separately from the active
slots.
