# T13.4a — Shifty independent decision review

Independent review of the pending Shifty decisions, prepared 2026-10-02 for the
coordinator to present to the user. **F003 remains in review.** This document
does not accept it, does not activate canonical Shifty and does not close
F004/F005/F006/F026/F035. It delivers unambiguous S1–S4 recommendations with
source contrast and observed behavior so the four decisions can be accepted or
corrected without further general research.

## 1. Examined revision, entry and permissions

- Workspace `D:/DEVEL/Mordheim/Mordheim-Utils REPO-REWORK`; branch `2A2B`;
  HEAD `1b7f7cf10b75a9d716c34c64039f5c908caed19e`; dirty tree (257 entries at
  entry capture). No commit, push, fetch, agent launch or shared-state edit.
- Entry capture `2026-10-02T06:50:02Z` in
  [`entry/`](../../../../build/cache/t13-parallel/shifty-independent-review/entry/);
  writable outputs were only this report and
  [`shifty-independent-review/**`](../../../../build/cache/t13-parallel/shifty-independent-review/).
- No applicable `AGENTS.md` exists in the workspace or its parent.
- Documentation drift during the review: the coordinator's documentation
  reconciliation rewrote [T13-shifty.md](T13-shifty.md) and
  [T13-shifty-review.md](T13-shifty-review.md) at 09:26 local (entry hashes
  `0b533a59…`/`b507c56e…`; post-drift
  `20cca7f7…`/`936f00bb…`, recorded in
  [`entry/postdrift.sha256.txt`](../../../../build/cache/t13-parallel/shifty-independent-review/entry/postdrift.sha256.txt)).
  Both bodies were re-read in full: the substantive Shifty text is unchanged;
  each gained a "Current ownership — 2026-10-02" note, and
  [eligibility.md](../../../reference/eligibility.md) gained the
  [construction boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation)
  section. This review examines the post-drift text.

| Examined input | SHA256 |
| --- | --- |
| `modular/rounds.py` | `d444f5a37b3e43f5e0c99febb6636b1a9ad5021216ac7a4115084807a3a0c11f` |
| `modular/pools.py` | `567a9636f7ac652d404c3c6cc09e6fb3748249dd5b6ee855005c30a25f669a0a` |
| `modular/attacks.py` | `55e05e32046a15428d43085195563ee471b07eb90be1cebeb59f6c9c444b6ef6` |
| `phases.py` | `a9d1759d2fe4028b43ca305256c220d69b499628a7367679923f4ee0a2276916` |
| `tests/.../test_shifty.py` | `09b32382bbdf127c4493bd96f06ff3fa1b155df15b06d7767aa0377d07963f9c` |
| `tests/.../test_spectral_touch.py` | `4658ddf6fd3ae0d74472375adf75e392fd788b3b188c7ff6140a06a2d474a97f` |
| `halflings-mic/special-rules.yaml` | `d59a2ccfb85caf43c73cec46fc3d5a12c0232986c71d1398d5910b81f2ff4eaf` |

## 2. Method and limits

Fresh focal execution, full source re-reading, and isolated probes built in
process memory inside the evidence directory. Expected observables are derived
from the original PDFs and general rules, not from the implementation. Probes
use the provisional `skill.shifty` tag on compiled fixtures; per the accepted
[construction boundary](../../../reference/eligibility.md#construction-boundary-for-phased-implementation),
an injected tag proves a combat sequence, never canonical selection or a legal
loadout.

Limits: no NumPy/native Shifty behavior was executed; no full semantic, parity
or coverage gate was rerun (the current-tree parity count blocker belongs to
F057); no maintained test, KB, specification, pin or shared document was
modified; historical pre-R4 Spectral Touch expectations were not reused.

## 3. Source / deduction / interpretation / limitation

Every statement below is classified:

- **(a) Printed source.** Halflings.pdf p. 4: *"The halfling gains a bonus
  attack when charged that strikes first."* The surrounding block is headed
  *"All Halflings may choose from the following special skills."* Same page,
  Crude Belch: the affected warrior *"must miss his first attack (regardless of
  whether he has only one attack or not)"* — a penalty on the **enemy** that
  includes a zero-attack clause. Core p. 18 priority: equal Initiative is
  decided by a die; several "strike first" models order by Initiative. p. 19:
  the extra weapon attack is added after other modifiers such as frenzy; with
  two different weapons one attack uses the chosen weapon and the rest the
  other. p. 23: frenzy doubles the Attacks characteristic. p. 24: the
  one-attack fist cap applies to *"warriors who have lost their weapons"*.
  p. 27: double-handed weapons strike last even when charging. p. 31: a pistol
  with another close-combat weapon gives +1 Attack once per combat at S4/−2;
  a brace gives 2 Attacks in the first turn. Errata p. 3: Whipcrack grants
  +1A when charging and +1A when charged that must target the charger and
  strikes first; two whips still only the first gets Whipcrack. Town Cryer 18 p. 618: the Serpent Staff
  power is chosen by forgoing *"all his normal attacks and parries in a
  round"* and makes *"a single attack with WS4 and S4"* that *"always attacks
  first"*.
- **(b) General-rule deduction.** The bonus is a separate grant added after
  frenzy and the two-weapon extra (it is not the Attacks characteristic);
  equal first-strike tiers resolve by Initiative; penalties such as Strike
  Last/stood-up apply unless a printed exception (Strongman) removes them.
- **(c) Project composition** (not printed Shifty text): survivor timing under
  the fist cap; min-1 reduction survivor treated as the bonus; tie reuse per
  warrior pair; Staff replacement covering the skill bonus.
- **(d) Provisional simulator limitation:** pistol-only refusal; no
  mid-duel charge input; no multiple-charger contract.

## 4. Canonical boundary — selectable skill vs current profile grant

Verified with the real shared module and compiler
([probe](../../../../build/cache/t13-parallel/shifty-independent-review/probes/probe_shifty.json)):

- `halfling-elder--shifty` in
  [`special-rules.yaml:628`](../../../../sources/knowledge/bands/mordheim/halflings-mic/special-rules.yaml#L628)
  has `runtime: scope LATER`, `implemented: NO`, `grant: profile`, a null
  effect binding and no top-level `kind`/`bindings`/`eligibility`.
- `applies_to.profile_ids` lists **all four** Halfling Heroes — elder, cook,
  thief, youths — matching the `special` skill access in
  [`profiles.yaml`](../../../../sources/knowledge/bands/mordheim/halflings-mic/profiles.yaml).
  Scouts, Warriors, Piggies and the Village Ogre do not receive it. The
  dossier's statement that the entry has *"only Elder in
  `applies_to.profile_ids`"* is inaccurate (see FIND-1).
- `applicableProfileRules` therefore materializes Shifty as an **automatic
  profile rule** for the four Heroes, while `specialRuleOptions` offers it to
  nobody (`elder_selectable_special_rules = []`): it is not a
  `kind: warband_skill` selection.
- Compiling without selection leaves `skill.shifty` absent; compiling with
  `special_rule_ids=('halfling-elder--shifty',)` raises
  `ValueError: special rule is outside the executable duel runtime: … Deferred
  subsystem: charge-response bonus attacks are outside the current engine
  scope.`

So the discrepancy is **grant mode + implementation status + entry naming**,
not recipient coverage: the canonical facts already know the four eligible
Heroes, but represent a chosen skill as an unimplemented profile grant. A legal
selection grant, its absence controls and the compiler binding remain F004
work. Promoted Halfling henchmen still need their own advancement/recipient
evidence. Nothing here authorizes activation.

## 5. S1–S4 decision matrix

| Point | Source-explicit (a) | Deduced (b) | Project interpretation (c) | Alternative and observable effect | Recommendation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| **S1 count/reductions** | Shifty bonus on being charged; frenzy doubles A; two-weapon extra added after modifiers; fist cap; Crude Belch can remove an enemy's sole first attack. | The bonus is a separate grant, not the A characteristic; reductions act on the warrior's pool. | Add after `build_attacks` (post-frenzy, post-extra-weapon), before whip/boar-spear/opponent reductions; min-1 survivor is the timed bonus; fist cap keeps one attack, timed as the bonus; Kusara suppression once per warrior across timed events. | Add after reductions (two-weapon analogy): A1 charged + incoming −1 → **2** attacks instead of 1. Consume bonus first: same total, survivor loses strike-first. Drop the fist bonus: one ordinary-timed attack. | **Accept the composition**; keep the fist/min-1 survivor timing as declared project composition; source-specific clauses (Crude Belch) must keep their own targeted mechanism. | `rounds.py:161–190`; `phases.py:176–229`; maintained frenzy/fist/incoming/suppression tests; fresh focal 101 passed. |
| **S2 weapon/pistols** | Shifty does not name a hand or pistols; pistol H2H +1A once per combat / brace 2 in first turn, S4/−2; fist cap applies only to warriors who lost their weapons; Thief can buy pistols. | A "bonus attack" must project an actual usable weapon; combat state cannot be chosen after observing dice. | Nominate one usable melee hand before resolution; preserve weapon, clean/poisoned pair and hand slot; mixed pistol/melee uses melee and adds no shot; pistol-only raises `ValueError` before dice. | Allocate one permitted pistol attack to the bonus (needs shot/brace limit contract); nominate another carried melee weapon; waive. Observable: an extra S4/−2 shot, or a legal melee-profile bonus vs no result. | **Accept early melee nomination and no extra ammunition; keep the refusal as an interim operator guard, not a tabletop ban.** F005/F026 must decide allocation. Do not invent a fist. | `rounds.py:326–345`; mixed/brace tests; [probe `pistol_only_refusal`]: refusal before any die/decision. Missile weapons other than pistols do not compile (`KeyError`), so the nomination gap is not reachable. |
| **S3 ties/Whipcrack** | Equal Initiative → die; equal first-strike → Initiative; Whipcrack is a distinct +1A struck first; two whips still one Whipcrack. | A warrior pair's order is established once for the round. | Reuse the warrior-order tie for Shifty and Whipcrack at the same tier/Initiative; no per-event redraw; both separately earned bonuses resolve. | Redraw per event: same warrior's events can interleave with the opponent differently (two tie dice, different order). Cancel one bonus: fewer attacks. | **Accept tie coherence and retention of both bonuses.** Does not assert canonical whip access for Halflings. | `rounds.py:219–259`; maintained whip-tie/distinct-bonus tests; [probes](../../../../build/cache/t13-parallel/shifty-independent-review/probes/probe_shifty_ties.json): exactly one tie die in both scenarios, both bonuses present. |
| **S4 replacements** | Serpent Staff power forgoes all normal attacks/parries for one WS4/S4 strike-first attack. | Whole-pool replacements do not combine with extra/natural attack lists unless a source says so. | Chosen Staff mode removes the Shifty bonus too; declining retains it; `single_bonus` never repeats Bull Charge, Body Slam, Anvil Head or natural extras. | Bonus survives Staff: 2 attacks (staff + Shifty). Bonus repeats a replacement: duplicated attack(s). | **Accept the replacement composition**; keep it declared as composition (source does not define "normal" vs a skill bonus); synthetic Staff fixtures are not loadout certification. | `rounds.py:347+`, `pools.py:160–205,341`; maintained Staff/bull-charge/extra tests; [probes](../../../../build/cache/t13-parallel/shifty-independent-review/probes/probe_shifty.json): anvil/body-slam offered only to the ordinary pool; Staff accept → no Shifty keys, decline → Shifty keys. |

## 6. S1 — count and reductions (detailed)

**Observed behavior.** For a charged Shifty owner the engine computes the
ordinary count, then `first_count += 1` before weapon/opponent reductions
(`rounds.py:161–190`); the timed event is split off only afterwards, so
`first_count == 1` yields an ordinary pool of 0 and one strike-first bonus.
Frenzy (doubling) therefore never doubles the bonus; the fist cap keeps the
single survivor timed as the bonus; `apply_opponent_attack_modifiers` returns
`max(1, count + modifier)` and no generic path reaches zero attacks for an
active, standing warrior (probe `zero_attack_clamp`). Kusara's `attack_penalty`
is consumed once per warrior across timed events with a per-warrior minimum
(maintained tests).

**Adjudication.** The +1-after-Frenzy placement is required by the core
two-weapon precedent and is safe. Adding *before* reductions is the
conservative choice (a reduction can consume the bonus rather than being
shielded from it, unlike the two-weapon extra); the only visible consequence is
that the final min-1 survivor carries the bonus timing. That consequence is a
composition, not printed Shifty text, but it preserves the source grant without
granting extra attacks. I recommend accepting it as written, with one hard
condition: **the generic reduction must never be used to implement a named
"miss the first attack" clause.** Crude Belch targets the *enemy* and can
remove its only attack; the current min-1 pipeline cannot express that, so
Crude Belch needs a targeted timed suppression when it is implemented
(see proposed register entry below). This corrects the dossier's framing
("generic minimum-one count fixture cannot certify that clause") by stating
precisely why: the clause does not belong to the halfling's count at all.

## 7. S2 — weapon and pistols (detailed)

**Observed behavior.** [`select_shifty_weapon`](../../../../packages/python/combat-engine/mordheim_combat/modular/rounds.py#L326)
runs before any attack dice. It nominates a distinct melee off-hand (decision
`round.N.SIDE.shifty.main-weapon`), automatically nominates the melee hand over
a pistol, preserves that hand's `*_without_poison` pair and slot, clears the
other hand/extra lists, and raises the documented `ValueError` for a
pistol-only main weapon. The probes confirm: nominated-main and nominated-off
poisoned hands both keep their own poison in the bonus pool and in their
ordinary hand; a piggybacking S4 pistol shot is never created; the refusal
happens before any die or decision is consumed. Compilation bound: among the 72
executable weapon mechanics, the only ranged entries are `weapon.pistol` and
`weapon.duelling-pistol` — bows, crossbow pistols and throwing knives raise
`KeyError`, so the "unusable missile hand" gap is not reachable in the current
contract and the pistol guard covers the reachable case.

**Adjudication.** The source settles none of the pistol allocation; the pilot's
refusal is a **simulator limitation**, not a tabletop prohibition (the Thief
list legally includes pistols and the free dagger). I recommend accepting the
nomination/no-extra-ammunition semantics and keeping the refusal as an explicit
interim guard. A future allocation contract (F005, coordinated with F026) must
choose among: (i) resolve the bonus with another carried melee weapon; (ii)
resolve it as one of the permitted pistol attacks without exceeding
once-per-combat/brace limits — the source text does not identify the Shifty
bonus with a pistol shot, so this needs an explicit reviewed ruling; (iii)
waive the bonus. Fabricating a fist while the warrior still carries usable
weapons contradicts core p. 24 and stays forbidden. Accepting the interim guard
cannot close F005/F026.

## 8. S3 — ties and Whipcrack (detailed)

**Observed behavior.** One warrior pair's tie is resolved once per
tier/Initiative (`ties` map in `rounds.py:219–259`); Whipcrack's insertion may
resolve the tie first and Shifty reuses it. The probes show exactly one
`round.0.first.whip-priority-tie` for Shifty+Whipcrack, exactly one
`round.0.priority-tie` for both-charged Shifty, with both bonuses resolving and
no `shifty-priority-tie` redraw. Distinct bonuses are retained
(`test_shifty_and_charged_whip_have_distinct_single_bonuses`).

**Adjudication.** Reusing the established warrior order is the only reading
that keeps one coherent order between two warriors for the round; redrawing per
event would let the same two warriors interleave differently within one phase,
which no source supports. Keep both bonuses: Whipcrack and Shifty are separate
grants with no cancellation clause. The engine composition says nothing about
whether a Halfling may legally carry a whip — the tests' Steel Whip fixture is
synthetic and the Halflings lists carry no whips; keep that separation explicit
when this composition is recorded.

## 9. S4 — replacements (detailed)

**Observed behavior.** When the Staff choice is true,
`select_attack_replacement` substitutes a single `effect.serpent-staff-power`
attack (fixed S4, priority 1), zeroes parries, and `first_shifty` is forced
false because the staff-power tag is present. When the choice is false the
normal Shifty bonus remains. The probes confirm the accepted path has no
`.shifty.` dice (2 outcomes: staff attack + charger) and the declined path has
the bonus (3 outcomes). Body Slam's decision and Anvil Head's D3 repeat are
offered only to the ordinary pool (`single_bonus` gating), and natural extras
are skipped for the bonus (maintained test).

**Adjudication.** "Forgo all his normal attacks" is the staff's printed
condition, and a chosen replacement of the round's attack activity is the
defensible reading; treating the bonus as surviving would contradict the
forgoing choice. Keep the composition, but record it as composition: the
source does not define whether a skill-granted bonus is "normal". The
single-bonus exclusions (Bull Charge, Body Slam, Anvil Head, natural/extra
lists) are correct general-rule applications: a single projected attack must
not re-trigger whole-pool replacements or independent attack lists. Synthetic
fixtures still do not certify a legal Halfling staff loadout.

## 10. Implementation findings (decision-independent)

- **FIND-1 — dossier correction (canonical target).** The dossier's claim that
  only Elder appears in `applies_to.profile_ids` is wrong; the KB lists the
  four skill-eligible Heroes (also at HEAD). The real defect is `grant:
  profile` + missing selectable `kind` + `implemented: NO`, not limited
  recipients. Correct F004's framing accordingly; promoted henchmen remain
  separate recipient evidence. Evidence:
  [`probe_shifty.json`](../../../../build/cache/t13-parallel/shifty-independent-review/probes/probe_shifty.json)
  `canonical_boundary`.
- **FIND-2 — no selectable option exists.** `specialRuleOptions` returns `[]`
  for the elder today; none of the Halfling special skills is offered, because
  their rules lack `kind: warband_skill`. Activation therefore needs both a
  correct grant model and the selectable route (F004), not just a binding.
- **FIND-3 — poisoned-hand transport verified.** Both nomination directions
  preserve the nominated hand's clean/poisoned pair and keep each ordinary
  hand's own poison state; request sequences match source-derived
  expectations exactly (probes `poison_nominated_main/off`). This closes the
  dossier's poisoned-hand gap for the tested spider-spittle compositions;
  a maintained regression is still proposed below.
- **FIND-4 — shared parry resource verified.** A parry spent on the bonus is
  not restored for the ordinary pool (probe `shared_parry_resource`); Lucky
  Charm and Kusara already have maintained cases.
- **FIND-5 — removal between pools.** The bonus removing the defender stops
  later pools/dice; the charger removing the Shifty owner stops the bonus
  (maintained tests `test_bonus_removal_prevents_both_later_pools`,
  `test_charger_removes_shifty_before_bonus_can_resolve`).
- **FIND-6 — single-bonus gating verified.** Anvil Head repeats, Body Slam
  decisions and natural extras are never offered to the bonus pool
  (probes; maintained bull-charge/extra tests).
- **FIND-7 — zero-attack clause cannot use the generic pipeline.** Crude Belch
  removes the enemy's first attack even when it is the only one; active
  standing warriors always keep ≥1 attack through the generic modifiers
  (`max(1, …)`). A targeted mechanism is required; this is a design boundary,
  not a current engine defect (the clause is canonically unimplemented).
- **FIND-8 — pistol-only refusal is clean.** `ValueError` before any dice or
  decisions; error text stable; no fabricated shot or fist (probe
  `pistol_only_refusal`).
- **FIND-9 — nomination is observable and mutation-detected.** An isolated
  in-process mutation that ignores the nomination decision changes the bonus
  hit target from 3 to 4 and is detected (probe `nomination_mutation`); the
  maintained tag-removal and whole-pool-promotion mutations pass inside the 44
  Shifty cases.
- **FIND-10 — no new engine defect.** Within the checked modular contract all
  probes matched source-derived expectations. The remaining barriers are
  canonical binding/access (F004), pistol allocation (F005/F026) and optimized
  ports (F006).

## 11. Decisions ready for human acceptance

Short, precise texts; the coordinator can present each independently. None of
them accepts F003 by itself.

- **S1.** *Accept the Shifty count composition: the bonus attack is added after
  frenzy and the two-weapon extra and before whole-warrior reductions; when
  reductions leave one attack, that survivor keeps the bonus's strike-first
  timing (including under the one-attack fist cap); a consumed hand's
  suppression is spent at most once per warrior; source-specific clauses such
  as Crude Belch (enemy must miss its first attack even when it has only one)
  keep their own targeted mechanism and are never modelled as a generic
  reduction.*
- **S2.** *Accept the nomination contract: one usable carried melee hand is
  nominated before resolution, preserving its weapon, poison pair and hand
  slot; mixed pistol/melee resolves the bonus with the melee weapon and never
  fabricates an extra shot or a fist; a pistol-only loadout stays an explicit
  interim refusal and must not be read as a tabletop prohibition; the
  allocation ruling for pistol-only is deferred to F005/F026.*
- **S3.** *Accept tie coherence: equal priority/Initiative is resolved once per
  warrior pair and reused for that warrior's timed events (Shifty, Whipcrack);
  do not redraw per event; both separately earned bonuses resolve. This does
  not assert canonical whip access for Halflings.*
- **S4.** *Accept the replacement composition: choosing the Serpent Staff power
  replaces the Shifty bonus together with the normal attacks; declining retains
  normal Shifty behavior; a single bonus never repeats Bull Charge, Body Slam,
  Anvil Head or natural/extra attack lists. Synthetic Staff fixtures are not
  legal-loadout certification.*

## 12. Changes required after acceptance

1. **Coordinator register update.** Record the accepted S1–S4 scope and this
   review's evidence in the authorized coordination documents; unblock F004;
   leave F005/F026/F006 gated. Do not close F003/F004/F005/F006/F026/F035 in
   this lot.
2. **F004 — canonical representation.** Correct `halfling-elder--shifty` from
   an unimplemented `grant: profile` to a reviewed selectable special skill
   covering the four Heroes (with promoted-henchmen evidence), add absence
   controls and the compiler/selection binding, and keep supported-effect
   refusal separate from legality. The corrected recipient facts already exist;
   the entry id/`kind`/runtime need review. Route through the shared
   TypeScript eligibility module; do not build a second implementation.
3. **Maintained regressions (small, source-linked).** Add a poisoned-hand
   transport case for both nomination directions; the fist-cap, incoming-min-1
   survivor, pistol-refusal, tie single-die and Staff accept/decline witnesses
   already exist as strict cases. Do not certify poison beyond the tested
   compositions.
4. **F005/F026 allocation contract.** Decide the pistol-only allocation among
   carried melee weapon, permitted pistol attack (respecting once-per-combat /
   brace limits) or waiver, with ordered shot/decision cases; preserve the
   explicit refusal until then.
5. **F006 ports.** After F003/F004, port the accepted modular behavior to
   NumPy/native with backend-specific dice/decision order and observable state;
   carry any F005 limitation forward.

## 13. Dependencies

- **F004** (canonical grant/specifications) depends on this acceptance and on
  FIND-1's corrected framing; it must not be closed by injected tags.
- **F005** (pistol-only allocation) and **F026** (Duelling Pistol
  H2H/reload/save) depend on the S2 acceptance; accepting the interim refusal
  does not resolve them and they must be decided together.
- **F006** (optimized backends) resumes only after F003/F004 stabilize and must
  reproduce the accepted decisions; no optimized claim is made here.
- **F035** (post-extraction construction evidence revalidation) must re-check
  this entry's construction facts (`applicableProfileRules`,
  `specialRuleOptions`, bundle freshness) after any KB/eligibility change; it
  is not a second eligibility implementation. The construction-boundary
  section added during this review is the governing reference.

## 14. Proposed follow-up register entries (coordinator assigns IDs)

- **Shifty poison transport regression.** *Status/type:* open; bounded test
  addition after acceptance. *Action/target:* add strict maintained cases for
  nominated-main and nominated-off poisoned hands, including ordinary-hand
  poison preservation. *Resume:* after the S1/S2 acceptance and with the
  modular contract frozen. *Close when:* the cases pass in the maintained Shifty
  suite and do not assert canonicity.
- **Crude Belch targeted first-attack suppression.** *Status/type:* open;
  mechanism gap (FIND-7). *Action/target:* implement Crude Belch's enemy-side
  "miss the first attack, even a sole attack" as a timed suppression distinct
  from generic count modifiers, with its Leadership test. *Resume:* when the
  Crude Belch/activation lot is dispatched. *Close when:* ordered cases show
  the affected enemy's first (including only) attack being skipped and generic
  reductions unchanged.
- **F003 acceptance recording and F004 framing correction.** *Status/type:*
  coordination. *Action/target:* record the accepted S1–S4 scope; correct the
  dossier/F004 statement about `applies_to.profile_ids` (all four Heroes, not
  Elder only) and note that a selectable `kind` is required. *Resume:* on the
  user's decision. *Close when:* the register reflects the accepted decisions
  and F004's updated entry, without closing any blocked follow-up.

## 15. Commands, exit codes and evidence index

| Command (repo root, `PYTHONDONTWRITEBYTECODE=1`) | Exit | Result |
| --- | --- | --- |
| `python -X utf8 -m pytest tests/python/combat/modular/test_shifty.py tests/python/combat/modular/test_spectral_touch.py -q -p no:cacheprovider --junitxml=…/checks/focal.xml` | 0 | **101 passed** in 13.50s; tests=101, failures=0, errors=0, skipped=0 |
| `python -X utf8 build/cache/t13-parallel/shifty-independent-review/probes/probe_shifty.py` | 0 | 9/9 probes ok (`probe_shifty.json`) |
| `python -X utf8 build/cache/t13-parallel/shifty-independent-review/probes/probe_shifty_ties.py` | 0 | 3/3 probes ok (`probe_shifty_ties.json`) |

Evidence index (all hashes verified in
[`checks/manifest.json`](../../../../build/cache/t13-parallel/shifty-independent-review/checks/manifest.json)):

- [`checks/focal.xml`](../../../../build/cache/t13-parallel/shifty-independent-review/checks/focal.xml)
  / `focal.log`; [`probes/`](../../../../build/cache/t13-parallel/shifty-independent-review/probes/)
  scripts, JSON results and logs; [`entry/`](../../../../build/cache/t13-parallel/shifty-independent-review/entry/)
  head/status/inputs/postdrift; [`sources/`](../../../../build/cache/t13-parallel/shifty-independent-review/sources/)
  original Halflings and Town Cryer PDFs plus text transcriptions.
- Historical contrast evidence (read-only): `build/cache/t13-parallel/shifty-review/`
  (93-pass pre-R4 focused XML, 78-hash entry, commands, selected core/errata texts).
- The 49 pre-repair Spectral Touch expectations in that historical run were
  superseded by the accepted R4 repair; this review does not reuse them. The
  current focal run (101 = 44 Shifty + 57 Spectral) passes.

## 16. What this review does not claim

No canonical selection, legal-loadout certification, activation, KB pin
refresh, specification authoring, optimized-port support, coverage/parity
certificate or acceptance of F003/F004/F005/F006/F026/F035. The pistol-only
refusal remains an operator limitation. The overhaul gate's current parity
count failure belongs to F057 and is unrelated to Shifty.
