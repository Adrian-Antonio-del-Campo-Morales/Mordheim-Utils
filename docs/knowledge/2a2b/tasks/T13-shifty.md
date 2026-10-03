# T13.4a — Shifty, accepted modular contract

> Current ownership — 2026-10-03. The [shared eligibility boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation) is already implemented for both products. [L04 below](#l04-canonical-activation--2026-10-03) activates explicit canonical selection for Elder, Cook, Thief and Youths and proves modular execution without injected tags. Accepted S1–S4/F060 and the shared construction decision are reused unchanged. Historical pilot results retain their dated limits; promoted local participants, pistol-only allocation and optimized ports remain separate.

Current acceptance — 2026-10-02: the user accepted independently reviewed S1–S4.
F003 is resolved for this modular contract; [permanent ruling](../../../decisions/design-rulings.md#shifty-s1s4)
and [acceptance record](T13-shifty-review.md#human-acceptance--2026-10-02) supersede
the historical pending-review statements below. F060 poison witnesses are accepted;
L04 delivers the four canonical heroes. Promoted-participant access, pistol-only
allocation and optimized ports remain separate.

This is the modular-first slice of [T13](T13.md), following the
[implementation plan](T13-implementation-plan.md) and
[local simulation contracts](T13-contracts.md). It does not complete T13.4.

Entry is `1b7f7cf` plus accepted, uncommitted T13.1. The coordinator owns this
slice. The user runs external agents: none was launched for implementation or
review. T13.2a compiler changes are concurrent work and are not this delivery.

## Consultation and source discrepancy

- [Original Halflings PDF](https://broheim.net/downloads/warbands/experimental/Halflings.pdf),
  PDF page 4, Special Skills / Shifty: one bonus attack when charged, with
  Strike First timing. The section presents these as chosen skills.
- [Halflings transcription](https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings),
  skill table and Halfling Special Skills / Shifty. Elder, Cook, Thief and
  Youths have Special access; Youths are Heroes. These sources were consulted
  on 2026-09-30.
- [Canonical Shifty entry](../../../../sources/knowledge/bands/mordheim/halflings-mic/special-rules.yaml),
  ID `halfling-elder--shifty`. At pilot entry, `grant: profile`, `LATER` /
  `implemented: NO` and a null binding contradicted the selectable source.
  L04 changes these to a selected warband skill with an executable binding;
  its four existing recipient IDs and full source/localized prose are preserved.
- [Close-combat weapons](https://mordheimer.net/docs/weapons-armour/close-combat):
  Double-handed weapon / Strike Last; Fist / one-attack maximum; Whipcrack;
  Serpent Staff / replacement of all normal attacks and parries.
- [Blackpowder weapons](https://mordheimer.net/docs/weapons-armour/blackpowder),
  Pistol / Hand-to-hand: the skill does not grant additional loaded shots.
- [Design rulings](../../../decisions/design-rulings.md): Strike Last,
  Initiative within equal tiers, one phase per player turn, equipment
  projection, immediate wound reactions, and suppression minimum per warrior.
- [Implement and verify rules](../../../guides/implement-and-verify-rules.md):
  real consumers, injected dice/decisions and behavioral negative mutations.
- [T13 origin register](T13-obligations.csv), Shifty origin: distinguish the
  additional attack from the ordinary pool. The register is not rewritten
  to imply global implementation or certification.

## Historical modular contract submitted for review — 2026-09-30

At pilot entry the provisional execution tag was `skill.shifty`. Tests attached it to otherwise
normally compiled fighters, including the actual canonical Halfling Elder.
That pilot proved an operator, not canonical selection. L04 below supersedes
the old compiler-refusal boundary and updates its two canonical assertions;
the synthetic composition fixtures continue to isolate S1–S4.

The initial local charge flags determine which warrior was charged, separately
from turn ownership. Its one additional attack is added after Frenzy and before
whole-warrior attack reductions. Only that attack receives at least Strike First
priority. Normal attacks retain their existing priority, count and allocation.
Equal tiers compare Initiative; equal Initiative uses an explicit D6. Existing
ties at that same tier are reused, including Whipcrack, to avoid contradicting
the warrior's already-established order. Both explicitly charged duel participants
can qualify independently. This is not a multiple-opponent simulation.

Existing Strike Last and standing-up penalties remain effective; Strongman is
the existing weapon exception. With fists alone, the total stays capped at one
and the surviving attack is the timed bonus. These compositions apply existing
general rules; Shifty's short source text does not state their precedence itself.
The independent semantic reviewer must confirm these proposed interpretations.

The additional attack nominates a usable melee hand. Distinct melee weapons
produce a boolean decision `round.N.SIDE.shifty.main-weapon`; true chooses main.
The projected attack preserves its original hand and clean/poisoned weapon.
A pistol plus melee weapon uses the melee hand. A pistol-only loadout raises
an explicit ValueError requiring a nominated melee weapon: Shifty does not
describe how its additional attack interacts with the pistol shot/brace limit,
and the Fist source applies to warriors who lost their weapons. Whether a player
may select another carried melee weapon, forgo a shot, or use a different attack
needs a source-backed allocation ruling before this combination can be enabled.
No extra pistol shot or fictitious fist attack is fabricated. Weapon nomination
is made before event resolution, alongside the existing priority preparation.

The bonus uses the real attack pipeline and current conditions, wounds, saves,
parries, critical capacity, Lucky Charm and wound reactions. It cannot duplicate
natural extra attacks, Whipcrack's charge attack or whole-pool Bull Charge,
Body Slam and Anvil Head replacements. Active Serpent Staff mode replaces all
normal attacks, including this bonus; declining it retains the normal skill.
Some compositions use synthetic fixtures to test orchestration invariants and
do not establish canonical Halfling equipment/skill eligibility.

Kusara suppression consumes the chosen hand once across all timed events, with
the established minimum for the whole warrior. Non-standing or burning warriors
cannot attack. A pool now exits when its defender is already out of action;
this prevents later attacks and dice after removal by a preceding timed event.
If Trap Blade breaks the bonus's weapon, subsequent ordinary hit rolls use the
surviving hand or the compiled unarmed fallback. Losing the second usable weapon
removes its additional attack; the fist maximum still applies. Already-prepared
hits within a single pool retain the existing snapshot semantics.

Only initial charge facts exist in the current duel contract. Subsequent phases
receive no Shifty bonus because no new charge occurred. The implementation does
not invent a once-per-battle limit or implement new mid-duel charging inputs.

## Files and evidence

- [Round orchestration](../../../../packages/python/combat-engine/mordheim_combat/modular/rounds.py)
  counts/splits/inserts the timed attack and nominates its weapon.
- [Attack pools](../../../../packages/python/combat-engine/mordheim_combat/modular/pools.py)
  accept `single_bonus` to resolve exactly one nominated attack through existing
  defenses and reactions, without repeating a pool replacement or extra list.
- [Deterministic cases](../../../../tests/python/combat/modular/test_shifty.py)
  check both participant positions, activation/absence, both charge flags,
  count, expiry, Initiative/ties, removal, resource sharing, weapon choices,
  conditions, fist cap, suppression, Trap Blade and representative compositions. Strict
  dice and decisions fail for missing/extra requests. A public modular replay
  verifies terminal winner, wounds and conditions after the bonus removes its foe.
  Isolated mutations remove the tag and promote the entire ordinary pool;
  the ordered behavior fixtures detect both incorrect implementations.

Local evidence lives in `build/cache/t13-parallel/shifty/`. The final commands
and counts are recorded in the delivery below. The six T13.1 seed31 samples
(200 duels, batch67, max5) retain exactly their accepted counts: plain modular
`(35,99,66)`, NumPy `(37,77,86)`, native `(30,97,73)`; Crimson Shade modular
`(49,83,68)`, NumPy `(45,75,80)`, native `(46,92,62)`.

NumPy/native code and binary are unchanged by this slice. Those historical
samples demonstrate preservation only; they do not test Shifty on optimized
backends. The coverage budget and complete semantic/parity certificates have
not been regenerated or advanced. The inherited 455 source-fingerprint errors
are not repinned here. No commit or push was made.

## Review and next barrier

Status: **in review**, not accepted. The initiative's
[coordination protocol](../README.md#estado-y-protocolo-de-trabajo) requires a
different reviewer for semantic changes. At the user's instruction the
coordinator supplies the following prompt for external execution, rather than
launching that reviewer. Complete modular semantic review before any optimized
port. Review findings may require changes to this proposed contract.

```text
Review T13.4a Shifty independently, read-only, in:
D:\DEVEL\Mordheim\Mordheim-Utils REPO-REWORK

Read docs/knowledge/2a2b/README.md, tasks/T13-shifty.md,
tasks/T13-contracts.md, tasks/T13-implementation-plan.md,
docs/guides/implement-and-verify-rules.md and docs/decisions/design-rulings.md.
Consult the linked Halflings original PDF, weapon/core combat sources and the
canonical Shifty entry; do not derive expectations from implementation alone.

Review ONLY the Shifty changes in modular/rounds.py and modular/pools.py and
the new tests/python/combat/modular/test_shifty.py. rounds.py also contains
accepted T13.1 changes; preserve them. Compiler T13.2a work is concurrent and
outside review ownership. No agents, writes, commits, pushes or KB repinning.

Check one attack when charged, selected rather than automatic skill grant,
independent charge/turn facts, ordinary priority preservation, tie coherence,
Frenzy, fist maximum, Strike Last/Strongman and standing-up precedence, real
weapon nomination, Trap Blade between timed pools, no added pistol shot, the explicit pistol-only source gate,
suppression, shared defenses/resources,
removal, expiry, and no duplicated natural attacks or pool replacements.
Separate proposed interpretations from what the Shifty source explicitly says.
Check that synthetic compositions do not certify illegal recipient/loadouts.

Run the focused suites listed in the document. Confirm strict fixture requests,
real modular consumers and the two negative mutations. Do not claim NumPy/native
support or global semantic certification. Return actionable findings with file
and line, severity, source/rationale and a reproducer, or explicit acceptance
limited to the modular operator with remaining production-binding barriers.
```

After acceptance, correct/review the selectable grant and introduce its canonical
binding through T13.2, then author source-linked semantic specifications and port
the agreed behavior to NumPy/native. Preserve the scenarios and observable dice,
decisions and intermediate state when preparing that separate work.

## Final validation — 2026-09-30

- **348 passed**, no skips: all modular suites, phases, T13.1 context/replay
  and architecture/documentation suites, including **44 Shifty cases**.
- All six accepted legacy samples match exactly. The historical NumPy/native
  samples used the unchanged accepted extension, not a Shifty implementation.
- Authored tracked-file whitespace check passes. Concurrent compiler changes
  from external T13.2a work were observed and preserved; they were not reviewed
  or accepted as part of this delivery.

```powershell
python -m pytest tests/python/combat/modular tests/python/combat/test_phases.py tests/python/combat/test_duel_context.py tests/python/verification/test_duel_replay.py tests/python/architecture -q --tb=short --junitxml=build/cache/t13-parallel/shifty/tests.xml
python build/cache/t13-1/legacy-sample.py
```

The passing cases establish the proposed modular contract. Independent semantic
acceptance, the canonical grant/binding, pistol-only allocation and optimized
ports remain explicit barriers, not completed work.

## Shared modular files rechecked by T13.3a — 2026-09-30

[T13.3a Spectral Touch](T13-spectral-touch.md) adds natural-hit provenance to
`pools.py` and a separate attack consumer. Shifty's `rounds.py` and test file
remain byte-identical to their delivery. Its 44 cases pass again in T13.3a's
397-case suite. The earlier delivery hashes describe that earlier snapshot;
use the T13.3a entry copies/diffs to distinguish the subsequent shared-file
changes. Shifty remains in independent semantic review.

## L04 canonical activation — 2026-10-03

**Delivered:** explicitly selected Elder, Cook, Thief and Youths now receive
Shifty through the maintained Combat Lab catalogue and shared construction
boundary and execute its accepted modular round behavior. This reuses the
user's S1–S4 acceptance and F060 poison witnesses, rather than repeating their
semantic review. No compiler, shared eligibility or modular-engine change was
needed to activate the four-hero route.

### Source and data contract

The original [Halflings PDF](https://broheim.net/downloads/warbands/experimental/Halflings.pdf),
page 4, skill table / Halfling Special Skills, and the
[maintained transcription](https://mordheimer.net/docs/warbands/grade-2a-warbands/halflings)
were checked again for this activation. The four printed Heroes have Special
access; Shifty grants one first-striking bonus attack when charged. The printed
section also says all Halflings may choose these skills; the promotion boundary
below records what the local participant API cannot yet represent.

- `halfling-elder--shifty` keeps its legacy ID, four recipient IDs, full source
  prose and EN/ES text. Only `kind: warband_skill` and runtime activation change:
  `scope/implemented: YES`, `grant: selectable`, `mechanic/skill.shifty` binding.
- The existing exact `sources/2A` mirror receives the same metadata delta.
  Canonical and staged files are byte-identical; no new mirror is invented.
- The active close-combat catalogue declares `skill.shifty` as a warband skill,
  with EN/ES labels and the original PDF reference. Its execution entry uses
  the existing passive fighter `effect-set`, tag `skill.shifty`, stacking `once`.
- The existing effect compiler folds the selected mechanic exactly once. There
  is no automatic grant or permanent Attack increment. The active catalogue
  already supplies mechanic vocabulary; registry data and runtime exclusions
  are unchanged. The maintained tag-consumer declaration now names the existing
  `rounds.py` attack/priority consumer, preserving the exact structural gate.
- The shared construction index/bridge/bundle, all eleven centralization closing
  inputs, accepted modular rounds/pools/attacks and F060 test bytes are protected.

### Executable evidence

[Canonical activation tests](../../../../tests/python/combat/modular/test_shifty_activation.py)
contain **35 cases**: all four real Hero selections, catalogue ID round-trip,
once-only compilation/absence, four unpromoted nonrecipients, foreign-band and
raw-mechanic bypass refusal, both participant positions, initial/later-round and
charge controls, a real public modular request, canonical Thief pistol-only
refusal before any dice/decisions, and public/low-level optimized refusals.
Canonical equipment is legal mace/dagger or the Thief's printed pistol option;
free-selection opponents are labelled controls. Piggies' negative compiled
control uses default natural attacks, not an illegal carried mace.

The accepted synthetic composition cases in `test_shifty.py` remain intact.
Its two old canonical pending/injection assertions now compile selected Shifty
directly; they no longer misrepresent the active route. F060 is unchanged.
The 35 canonical + 44 composition + 5 poison cases pass together (**84**).

[Source-linked specification](../../../../tests/specs/semantic/grants/t13-halfling-shifty.yaml)
adds **11 cases** for two actual new obligations: `mechanic/skill.shifty` and
the selected canonical rule effect. Strict round tapes distinguish the bonus
before the charging opponent from the later ordinary pool in either position;
absence, own charge and later-round controls have no extra attack. All three
isolated mutations are detected: missing owner tag in either position and an
incorrect permanent Attack bonus. No unrelated digest is refreshed.

Two concrete regression failures required narrow inventory updates: executable
mechanics 190 → 191 and selectable origins 54 → 55. The retained T13.2 register
still has 883 band-rule origins; live grants now partition as **828 automatic
(635 profile + 193 band) + 55 selectable**. Historical CSVs retain their entry
meaning, with current notes in their delivery documents. The selectable matrix
now lists Shifty explicitly instead of weakening completeness checks.

The first dependency run also exposed the absent 2A mirror update and warband
skill count 381 → 382; both are repaired. Supplemental bytes were captured before
editing each concrete dependency. The structural snapshot comparison separately
attributes new Shifty counts and detects stale Spectral counts left at entry;
the retained structural test is reconciled to those actual data deltas.

### Validation and retained limits

| Check | Result / evidence |
| --- | --- |
| Shifty canonical/composition/F060 suites | 84 passed; focused execution retained |
| All modular + construction + duel-context tests | 926 passed, `affected-final.txt` |
| Catalogue runtime / selectable matrix after reconciliation | 59 passed, `inventory-regression.txt` |
| Catalogue / exact staging promotion after reconciliation | 56 passed, `promotion-regression.txt` |
| Initial schema/binding/kernel/backend/architecture dependency run | 375 passed; only catalogue count and exact-mirror failures, repaired by the preceding checks; `dependencies.txt` |
| Shared recipient/F035 + campaign construction/current-KB TypeScript sweep | 56 passed, `typescript.txt` |
| Structural tests / documentation after snapshot reconciliation | 7 passed, `structural-doc-final.txt` |
| Generated publication / `--check`; `check:eligibility` | Exit 0; generated outputs only, shared bundle unchanged |
| Full semantic verifier | 720 obligations: 569 verified / 151 pending; structural complete, 1050 profiles; 11 new cases / 3 detected mutations |

Full verify retains **exactly the same 30 historical source-pin errors** as the
L03 baseline, with zero additions/removals. Its exit 1 is expected and is not a
global green claim. Earlier local authoring failures and their fixes remain in
the evidence; no live engine mutation was used. Entry/closing hashes, structural
comparison, logs and minimal attributable diffs are under
`build/cache/t13-parallel/shifty-activation/`; this document is sufficient to
reconstruct the contract without that ignored evidence.

Core reproducible checks (the full verifier still exits 1 for the 30 inherited pins):

```powershell
python -X utf8 -m pytest tests/python/combat/modular/test_shifty_activation.py tests/python/combat/modular/test_shifty.py tests/python/combat/modular/test_shifty_poison_transport.py -q
python -X utf8 -m pytest tests/python/combat/modular tests/python/construction tests/python/combat/test_duel_context.py -q
python -X utf8 -m pytest tests/python/verification/test_semantics.py -k t13-halfling-shifty -q
python -X utf8 -m pytest tests/python/verification/test_structural.py tests/python/architecture/test_documentation.py -q
python -X utf8 tools/mordheim-utils.py verify --json
python -X utf8 tools/knowledge/generate_knowledge_web.py --check
npm run check:eligibility
```

### Deferred clauses and next owner

- **F004 / L05 — promoted Halfling local participants:** four canonical Hero IDs
  are implemented; a promoted Scout/Warrior is not represented by `FighterBuild`.
  Coordinator must provide a source-backed supported local route or justify the
  local product disposition with positive/negative evidence. Keep this remaining
  access clause open; do not widen IDs to unpromoted henchmen or import campaign
  persistence. The printed Ogre's promoted skill restriction is separate.
- **F005/F026 / L08 — pistol-only allocation:** the canonical Thief can own the
  pistols, but Shifty execution still refuses before consuming a roll or choice
  when no carried melee weapon can be nominated. This is a provisional supported
  execution boundary, not a tabletop prohibition or permission for another shot.
- **F006 / L19–L20 — optimized ports:** kernel/NumPy/native entry paths explicitly
  refuse the unported tag. No optimized behavior is certified by these guards.
- **L18 — visible product/backend routing:** catalogue selection and public
  modular execution are proved; actual GUI/backend routing remains that lot's
  responsibility. No UI layout or selector was changed here.
- **F057 / L01 and F001:** current authored case corpus increases by 11, after
  L03's 10; parity must derive current cases, not retain the old 3743 pin. The
  externally reserved parity repair and 30 historical pins were not modified.

L04's four-hero canonical milestone is delivered and its file reservation can be
released. F004 remains open only for the stated promoted access clause; F003/F060
stay accepted. T13/T14/T15 remain in progress. No agent, commit or push was made.
