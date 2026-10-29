# Migration plan: modular → vectorized engine

Measured on 2026-10-24, branch `hfi/.../elm`, working tree as checked out.
All numbers below come from commands recorded in §1; re-run them to refresh.

## 0. Conclusion up front

The vectorized engine is **not** a stub. `vectorized/_driver.py::_simulate_batch_core`
is a ~870-line round loop that already mirrors the structure of
`modular/rounds.py::resolve_round` (~1560 lines), and all five tracked
non-tag *behaviours* (effect-values, vomit, spectral-touch, shifty,
killing-blow) are already marked connected.

So this is **incremental rule porting against an existing admission gate**,
not a rewrite. The repository already contains the exact machinery the
migration needs:

| Asset | Path | Role in the migration |
|---|---|---|
| Admission gate | `packages/python/combat-engine/mordheim_combat/kernel.py` — `_pending_snapshot()`, `NUMPY_CONNECTED_TAGS`, `NUMPY_CONNECTED_BEHAVIOURS`, `require_optimized_support()` | The authoritative, executable list of what vectorized still refuses. Each port step moves tags from pending → connected. |
| Worklist with pointers | `apps/combat-lab/.../verification/consumers.py` — `MODULAR_TAG_CONSUMERS`, `MODULAR_FIELD_CONSUMERS`, `MODULAR_COMPLEX_SCENARIOS` | Each unported tag already names the modular module *and function* that implements it. This is the port spec; do not re-derive it from the KB. |
| Differential oracle | `apps/combat-lab/.../verification/parity/_specifications.py` — 36 operation adapters running the same semantic case against modular and vectorized | Per-case, per-field pass/divergence. This is the acceptance test for every step. |
| Per-phase entry points | `vectorized/_operators.py`, `_attacks.py`, `_driver.py` | Ports attach to existing operators; the adapters already call them by name. |

**Do not** start by writing new tests or a new harness. Start by draining the
gate, measuring with `parity`, and only adding discriminators the existing
corpus lacks.

## 1. Baseline (reproduce before touching code)

```bash
python tools/mordheim-utils.py parity          # ~250 s
```

Recorded result:

```
vectorized_parity_complete=False
321/391 obligations verified; 70 pending; 0 divergences
specifications: 3728 PASS; 10 PENDING_ADAPTER; 55 DIVERGENCE; 0 OUT_OF_SCOPE
```

Gate contents (`mordheim_combat.kernel`):

| Category | Base snapshot | Still pending for NumPy |
|---|---|---|
| `residual_tags` | 91 | **81** |
| `local_modifier_tags` | 109 | **90** |
| `weapon_profile_tags` | 8 | **8** |
| `behaviours` | 5 | **0** |

Total: **179 tags** gated off, 0 behaviours.

## 2. What the gap actually is — four distinct classes

The 55 spec divergences are *not* 55 independent bugs. Classified by detail
string, they collapse into a small number of root causes. Treat them in this
order; the cheap classes unblock measurement of the expensive ones.

### Class A — reporting artifacts (not engine gaps). Fix first, ~0.5 day.

`_vectorized.py::verify_vectorized_parity` decides a tag is "verified" by
**substring-searching the vectorized sources for `"tag.name"`**. That produces
false negatives whenever the engine stores the tag under a different literal.

Confirmed example: `dance.whirling-death`, `dance.storm-of-blades`,
`dance.the-shadows-coil`, `dance.woven-mist` are listed as PENDING, yet they
are listed in `NUMPY_CONNECTED_TAGS` *and* implemented in
`_driver.py:543` (`SHADOW_DANCES = ("whirling-death", ...)`, unprefixed) and
`_select_shadow_dance`. Same shape for `mechanic.hypnotist`
(`_driver.py:256`).

- **Action:** audit the 70 pending obligations against `NUMPY_CONNECTED_TAGS`.
  Any tag in both lists is an evidence-mapping defect, not a port. Resolve it
  by pointing `INDIRECT_TAG_EVIDENCE` (or an equivalent explicit mapping) at
  the real consumer, **not** by inserting a decorative string literal into the
  engine.
- **Also catch here:** `mechanic.death-blow` (connected, implemented at
  `_attacks.py:178`, `_driver.py:70`) is a *different rule* from
  `mechanic.deathblow` (Slayer; pending; modular at `rounds.py:1723`). The
  near-identical names are a live trap for anyone porting by name match. Record
  the distinction before touching either.
- **Also:** the 10 `PENDING_ADAPTER` cases are harness limits, not engine
  limits — `halfling-shifty` (×5), `mechanic-black-hunger`,
  `editorial-black-hunger-variants` all fail with *"vectorized round adapter
  only supports state-only terminal cases"* (`_specifications.py:618`), and
  `_vector_priority` bails with *"lacks initiative_floor"*
  (`_specifications.py:69`). Extending those three adapters is adapter work and
  should be scheduled with Class B, because it is what will *observe* the port.

**Exit:** a pending list that contains only genuinely unported behaviour.

### Class B — DONE (2026-10-25). Diagnosis below was wrong; see §6 for what it actually was.

> **Correction.** The analysis in this section was derived from the truncated,
> *one-sided* vectorized dumps in the parity output and concluded that
> `_new_state` seeded parry capacity and the initiative floor incorrectly. That
> was wrong. Once both sides were diffed field by field, 36 of the 37
> initialization/recovery cases had **no value mismatch at all** — the failure
> was a key-set mismatch in the comparison. The engine was not at fault. The
> corrected account and the measured outcome are in §6; the original text is
> kept below because it names the affected cases.

### Class B (original, superseded) — one systemic state-initialization defect.

21 of the 55 divergences are `operation=initialize` / `operation=recovery`
through `vectorized._new_state` and `recover_round_state`. Across *every* one
of them the dumped vectorized state shows:

```
'parries_remaining': 0, 'initiative_floor': 1, 'resources_spent': [...]
```

Affected specs include `core-parry/two-swords-one-attempt`,
`weapon.sword/one-per-phase`, `defence.buckler/compiled`,
`sword-master-generic-reroll/capacity`, `advanced-dwarf-parries-*` (6 cases),
`preparation-crimson-shade/*` (3), `mechanic-disability/*` (7),
`editorial-ogre-flesh/*`, `skill.monstrous/*`, `selected-blessings-*`,
`editorial-cripples-disability/selected`, `defence.lucky-charm/compiled-resource`,
`core-critical-hits/next-round-restores-critical`,
`core-injury-states/two-recovery-rounds`.

That is a **single family**: initial parry capacity, initiative floor,
resource-ledger shape and starting-wounds/characteristic application are not
being seeded the way `modular/state.py::initialize_fighter` seeds them.

- **Action:** diff `vectorized/_driver.py::_new_state` + `_types.py::CombatState`
  construction against `modular/state.py::initialize_fighter`, field by field,
  reusing `_parry_capacity` (already shared with the native compiler). Expect
  one or two fixes to clear most of the 21.
- **Why first:** every later port is validated through initialized state. Fixing
  this removes noise from all downstream measurements.
- **Measure:** re-run `parity` and expect the divergence count to drop from 55
  to roughly the mid-20s. If it does not, the family hypothesis was wrong and
  the cases must be split.

### Class C — small, individually-scoped rule divergences. ~3–5 days.

Remaining divergences after Class B, each a named rule with a named modular
consumer:

| Spec | Symptom | Modular source to port from |
|---|---|---|
| `spirit-host-spectral-touch/*` (5) | `damage: vectorized=0, modular=1` | `modular/attacks.py` spectral-touch path — note `spectral-touch` is already in `NUMPY_CONNECTED_BEHAVIOURS`, so the gate claims coverage the engine does not deliver. Treat as a **gate-accuracy defect**, high priority. |
| `warpstone-troll-vomit-option/*` (4) | `result.count: vectorized=4, modular=1`; one `list index out of range` | `modular/rounds.py::select_attack_replacement`. `vomit` is likewise already marked connected — same gate-accuracy problem. |
| `skill.infallible/active-all-faces`, `skill.crack-shot/*` (3) | hit distribution ½ vs ¾, ⅔ vs 8⁄9 | reroll composition in `modular/contexts.py::_hit_reroll` — the granted-reroll source qualification is missing in `_attacks.py`. |
| `unpredictable-attack-one-per-phase/...` | `parried: vectorized=False, modular=True` | parry eligibility per declared attack, `modular/attacks.py` |
| `weapon.first-strike-family/pike-ordinary-after-first-round` | `first_acts: True` vs `False` | `modular/rounds.py::_strike_initiative` / pike first-turn scope |
| `editorial-tentacle-*`, `editorial-*-grant`, `condemned-inconsistency-*`, `selected-attributes-monstrosity/*` | construction/grant composition | `MODULAR_FIELD_CONSUMERS` names the consumer per field |

**Flag for the user:** `spectral-touch` and `vomit` sit in
`NUMPY_CONNECTED_BEHAVIOURS` while their specs diverge. The admission gate is
therefore currently *optimistic* — the vectorized engine will accept duels it
resolves incorrectly rather than refusing them. I would fix the gate honesty
before porting anything new, so that every subsequent step is either correct or
loudly refused.

### Class D — the 179 gated tags. The bulk of the work.

These are refused up-front by `require_optimized_support`, so they produce no
divergences — they simply cannot run. They split by *where* they attach:

1. **`local_modifier_tags` (90)** — hatreds, fear/psychology immunities,
   leadership rerolls, ward/ethereal saves, strike-order modifiers. These are
   overwhelmingly **value-and-flag composition** on `EffectSet`, consumed by
   `modular/contexts.py` and `modular/leadership.py`. Vectorized already has
   `_leadership.py` (532 lines) and `_psychology.py` (448 lines), so most of
   these port as *new columns and masks on existing operators*, in batches of
   10–20 closely-related tags, not one at a time. **Highest tag-throughput per
   unit of work — do this group second-to-last-but-largest.**
2. **`weapon_profile_tags` (8)** — `weapon.katana`, `kanabo`, `knuckledusters`,
   `long-daggers`, `pry-bar`, `shock-rod`, `skull-busta`, `wizards-staff`.
   Printed profiles; each is a compile-time effect plus at most one runtime
   branch. **Smallest, most independent, best first real port and best
   candidate for parallel delegation.**
3. **`residual_tags` (81)** — the genuinely hard ones: multi-phase, stateful
   and decision-driven rules. Sub-groups:
   - *Control powers* — `CONTROL_POWERS` in `modular/rounds.py:101-150`
     (Hypnotic Gaze, the two Seductions) with persistent `SEDUCTION_RESOURCES`
     on the victim's resource ledger and auto-hit. Needs a per-row persistent
     resource column; nothing equivalent exists in `_driver.py` yet.
   - *Supplied conditions* — `condition.petru-*`, `condition.alchemist-*`,
     `condition.command.*`, `condition.danse-macabre-controlled`,
     `condition.fungus-brew-dizzy`, `condition.rememberer-support`. Mostly
     `initialize_fighter` + a recovery-phase release test. **Port these right
     after Class B**, since they reuse exactly the initialization work.
   - *Recovery-phase self-actions* — `mechanic.herb-lore*`,
     `mechanic.inconsistency`, `mechanic.marianna-no-pain-jump-up`.
   - *Attack-pool options* — `mechanic.deathblow`, `mechanic.corruption`,
     `mechanic.main-gauche-modes`, `mechanic.prehensile-tail`,
     `mechanic.beak`, `mechanic.festooned-with-pistols`,
     `mechanic.estalian-technique`, `mechanic.darting-steel`.
   - *Leadership/range providers* — `mechanic.leader-twelve`,
     `mechanic.leader-four`, `mechanic.mob-leadership`,
     `mechanic.own-leadership`, `mechanic.relay-orders`, `mechanic.songster`,
     `mechanic.sea-shanty*`.
   - *Long tail of one-offs* — `mechanic.djinns-curse`, `mechanic.lunatics`,
     `mechanic.magic-acorn`, `mechanic.marks-of-ranald`,
     `mechanic.solkan-*`, `weapon.ienh-khain`,
     `weapon.count-of-ventimiglias-misericordia`, etc.

## 3. Sequenced plan

> **Testing policy changed 2026-10-25 — see §11.** The rule below ("each phase
> ends with parity") is superseded for phases 4–7: during development use only
> the smallest focused check for the rule being ported, or none when confident.
> All heavyweight verification moves to the final verification task (phase 8).

~~Each phase ends with `python tools/mordheim-utils.py parity` and a recorded
delta. No phase is "done" on a code read.~~ *(superseded by §11)*

| # | Phase | Scope | Exit criterion | Est. |
|---|---|---|---|---|
| 0 | Baseline & honesty | Reproduce §1. Fix Class A reporting artifacts. Make `NUMPY_CONNECTED_*` honest: remove `spectral-touch` and `vomit` until Class C clears them. | Pending list contains only real gaps; gate refuses what it cannot resolve. | 1 d |
| 1 | State initialization | Class B. `_new_state` / `CombatState` / `recover_round_state` vs `modular/state.py`. | Divergences 55 → ≲25. | 1–2 d |
| 2 | Adapter reach | Extend `_vector_round` (non-terminal cases), `_vector_priority` (`initiative_floor`). | `PENDING_ADAPTER` 10 → 0. | 1 d |
| 3 | Named divergences | Class C table, one row at a time. | Divergences → 0; re-add `spectral-touch`/`vomit` to the connected set. | 3–5 d |
| 4 | Weapon profiles | 8 `weapon_profile_tags`. | `weapon_profile_tags` pending → 0. | 2–3 d |
| 5 | Supplied conditions | `condition.*` residuals (≈20 tags). | Those tags move to connected; specs pass. | 3–4 d |
| 6 | Local modifiers | 90 `local_modifier_tags`, in themed batches (hatreds / fear / leadership rerolls / saves / strike order). | `local_modifier_tags` pending → 0. | 2–3 wk |
| 7 | Stateful residuals | Control powers, recovery self-actions, attack-pool options, leadership providers, long tail (≈60 tags). | `residual_tags` pending → 0. | 3–4 wk |
| ~~8~~ | ~~Verification task~~ | **OUT OF SCOPE for this plan (2026-10-25).** This plan ends when phase 7 lands. Deep verification is a separate, later task — its inputs are collected in `HANDOFF_VERIFICATION.md`. | — | — |

**This plan is complete when the admission gate reaches zero pending tags.**
Verification is explicitly *not* a phase of it.

Rough total: **8–11 weeks of focused work.** Phases 4–7 are the bulk and are
the parallelizable part.

## 4. Execution rules

- **The gate is the ledger.** A rule is ported when its tag leaves
  `NUMPY_PENDING` *and* its specs pass — never on one of the two alone. Never
  widen `NUMPY_CONNECTED_TAGS` ahead of the implementation; the current
  `spectral-touch` / `vomit` entries show exactly how that hides a defect.
  *(Amended by §11: during phases 4–7 a tag may leave the gate on
  implementation alone; its specs are confirmed in bulk at the phase-8
  verification task. The second half of the rule — never connect a tag whose
  implementation does not exist — stays absolute.)*
- **Port from the named consumer, not from the KB.** `MODULAR_TAG_CONSUMERS`
  already states the module and function. Re-deriving the rule from
  `sources/knowledge/` risks a second, divergent interpretation — the modular
  engine is the oracle by repository policy (`README.md`).
- **Share, don't fork.** Anything genuinely scalar (`_parry_capacity`,
  `_critical_wound_threshold`, `special_save_targets`, `_compiled_attack_effect`)
  already lives in a shared home and is consumed by the native compiler
  (`native/_combat_compile.py`). Extend those rather than adding a vectorized
  copy, or the native port inherits the divergence.
- **Batch by mechanism, not by alphabet.** Tags that share an operator (all
  hatreds, all leadership rerolls) must land together; they contend for the
  same arrays and separate landings cause repeated rework.
- **Reuse the existing corpus.** 3,728 specification cases already pass and the
  E2E/battery corpora exist. Add a discriminator only where the corpus cannot
  distinguish the new behaviour — per `AGENTS.md`, not as routine coverage work.
- **One writer per file.** `_driver.py` and `_operators.py` are the contention
  points. If phases 4–7 are parallelized across agents, partition by file and
  have the coordinator integrate `_driver.py`.

## 5. Open questions for the user

1. **Native engine.** This plan covers vectorized only, as asked. `NATIVE_PENDING`
   is deliberately frozen at the full snapshot and `native/_combat_compile.py`
   reuses the vectorized helpers, so every vectorized port is a prerequisite for
   the native one — but the Cython core will need its own pass. Out of scope
   here; say if it should be folded in.
2. **Gate honesty (phase 0).** Removing `spectral-touch` and `vomit` from the
   connected set will make the vectorized engine *refuse* duels it currently
   accepts. That is a visible behaviour regression in exchange for correctness.
   Confirm that trade is wanted, or phase 3 can be pulled forward instead.
3. **Decision policies.** Several residual rules are optional player choices
   (`mechanic.deathblow`, `mechanic.corruption`, Shadow Dances). Vectorized
   routes these through `_choose`/`DecisionPolicy` per row. Confirm batch
   decision semantics must stay row-identical to modular replay — the plan
   assumes yes, because `test_duel_replay.py` depends on it.

---

## 6. Phase 1 outcome (2026-10-25)

### What the initialization/recovery gap actually was

The spec corpus holds exactly **35 `initialize` + 2 `recovery` cases, and all 37
diverged** — these two adapters had never passed a single case. Diffing both
sides field by field showed only **4 real value mismatches**, all in one case
(`condemned-inconsistency-random-characteristics/initialization-defers-unused-values`,
whose `mechanic.inconsistency` is a gated-off residual tag anyway).

Every other difference was structural: `execute_case` dumps the modular
`FighterState` through `_plain`, which emits all ~68 dataclass fields, including
the modular-only columns (`mutations`, `grappled`, `djinn_power`, `lunatic_result`,
`random_rolled`, ...). The vectorized `CombatState` deliberately carries 24. The
adapters compared the two dicts whole, so the key-set difference alone failed
every case and hid whether any modelled field actually disagreed.

**This was an adapter defect, not an engine defect.** No change to
`vectorized/_new_state`, `CombatState` or `recover_round_state` was needed or
made.

### Changes

1. `apps/combat-lab/.../parity/_specifications.py` — added `_modelled_state()`,
   which restricts the modular dump to the vectorized projection's key set
   (a strict subset, verified) before comparison. Used by `_vector_initialize`
   and `_vector_recovery`. Every field the vectorized engine models is still
   compared; only fields it has no column for are dropped.
2. Same file — added `_require_numpy_admission()`. The state adapters call
   `_new_state` directly, bypassing the gate `simulate_batch` applies, so a
   deliberately unported rule was reported as a divergence instead of as
   pending work. Refused cases now raise `NotImplementedError` → `PENDING_ADAPTER`.
3. `packages/python/combat-engine/mordheim_combat/kernel.py` — withdrew
   `vomit` and `spectral-touch` from `NUMPY_CONNECTED_BEHAVIOURS` (temporary;
   documented inline with the restore condition).
4. `tests/engines/modular/test_vomit_attack.py`,
   `tests/engines/modular/test_spectral_touch_activation.py` — three assertions
   that pinned the optimistic gate ("NumPy executes the connected option") now
   assert refusal, each marked `TEMPORARY` with its restore condition.

### Measured results

Parity (`python tools/mordheim-utils.py parity`), worktree baseline re-measured
before the change to confirm it matched §1:

| | Before | After |
|---|---|---|
| specification PASS | 3728 | **3753** (+25) |
| specification DIVERGENCE | 55 | **18** (−37) |
| specification PENDING_ADAPTER | 10 | **22** (+12) |
| obligations verified | 321/391 | 321/391 (unchanged) |

All 37 initialization/recovery cases resolved: **25 now PASS**, **12 correctly
reported as gate-refused** (6 `advanced-dwarf-parries-*`, 3
`selected-attributes-monstrosity`, 2 `editorial-ogre-flesh`, 1
`condemned-inconsistency`) rather than as false divergences.

`pytest tests/engines -q`: **1598 passed, 15 failed, 5 errors** — identical
failure set to the pre-change baseline (1595 passed, 15 failed, 5 errors),
+3 from the updated gate tests. No regressions.

### Still open after phase 1

- **18 divergences remain, all Class C** (phase 3), untouched: spectral touch
  (5), vomit replacement pool (4), crack-shot/infallible reroll composition (3),
  tentacle grapple (2), crack-shot/infallible grants (2), unpredictable-attack
  parry (1), pike strike order (1).
- **22 `PENDING_ADAPTER`**: 12 are honest gate refusals (resolve when the tags
  are ported in phases 5–7); 10 are harness reach — `_vector_round` only handles
  state-only terminal cases, `_vector_priority` lacks `initiative_floor`
  (phase 2).
- **179 gated tags** untouched (phases 4–7).
- **Class A reporting artifacts not addressed** — the 70 pending obligations
  still include false negatives such as the Shadow Dances. Phase 0 remainder.
- **The two withdrawn behaviours are a live regression by design**: NumPy now
  refuses Vomit Attack and Spectral Touch duels it previously accepted and
  resolved incorrectly. Restore both when phase 3 clears their specs.

---

## 7. Phase 2 outcome (2026-10-25)

### Changes

1. **Engine, verification-only plumbing** (`vectorized/_driver.py`): the round
   driver was a closed loop with no round-level seam, which is why the round
   adapter was stuck at "state-only terminal cases". Rather than re-deriving
   round sequencing in the harness, two default-off parameters were added so
   the adapter replays through the engine's own driver:
   - `observations=` threaded from `_simulate_batch_core` /
     `simulate_batch_observed` through `_resolve_attacks_by_equipment` (13 call
     sites) into `resolve_attacks`, collecting per-attack records in the
     engine's own event order. `None` by default; production batches unchanged.
   - `first_round_index=` so a single-round replay can run exactly round N
     (`range(first_round_index, maximum_rounds)`), mirroring modular
     `resolve_round` on a `DuelState` with nonzero `round_index`.
2. **Round adapter** (`_vector_round`): keeps the terminal-state path; live
   cases now run `simulate_batch_observed` for one round with the charge
   declared via `DuelContext(charging=..., active_participant=...)` from the
   case's `first_charged`. Classification is explicit: gate refusal →
   `PENDING` (engine-unsupported); unexpressible case shape (state overrides,
   unknown context keys, unmodelled expectation paths) → `NotImplementedError`
   (adapter-missing); fewer resolved attacks or tape mismatch → divergence.
3. **Priority adapter** (`_vector_priority`): the `initiative_floor` guard was
   replaced with support via `state.initiative_floor`, the same column the
   spider-bite path writes. No corpus case exercises a non-default floor yet;
   the limitation is simply gone.
4. **Black Hunger temporarily gated** (`kernel.py` `_pending_snapshot`):
   extending the adapter exposed that the NumPy runtime resolves Black Hunger
   incorrectly — the printed own-turn +1 Attack is never applied (the modular
   engine adds it at round start, `modular/rounds.py:417`) and the backlash
   runs every round for both turns instead of only the owner's. The frozen
   vectorized fixture hid this by baking a pre-activated `attacks_bonus == 1`
   into the compiled fighter. Per the standing accepted-but-incorrect policy,
   `mechanic.black-hunger` joined the pending snapshot until the activation is
   ported. (`tests/engines/vectorized/test_shared_families.py::test_black_hunger_adds_attack...`
   was already failing before this phase and remains the reminder.)

### Measured results

Round-operation cases (the 10 blocked ones): **5 PASS** (all `halfling-shifty`,
including round-1 `later-round-no-repeat` via `first_round_index`), **5
gate-refused PENDING** (3 `condemned-inconsistency` via `mechanic.inconsistency`,
2 black-hunger via the new gate entry), **0 adapter-limitation refusals** —
every remaining PENDING_ADAPTER in the corpus is now an honest engine-gate
refusal. All 17 priority-operation cases still pass with the floor extension.

| specifications | after phase 1 | after phase 2 |
|---|---|---|
| PASS | 3753 | **3758** |
| PENDING_ADAPTER | 22 | **17** (all gate refusals) |
| DIVERGENCE | 18 | **18** (unchanged, all Class C) |

Targeted suites: `tests/engines/vectorized + shared + modular gate tests`
(248+ passed) and `parity battery cases/runner + duel replay + truncation`
(79 passed) show exactly the known pre-existing failures (5 + 5), none new.
Obligations inventory unchanged (321/391, Class A pending).

### Problems found / still open

- **Black Hunger is a new confirmed Class C/D gap** (own-turn activation
  missing in the driver); duels with it are now refused rather than resolved
  wrongly. Port it with the round-start activation phase.
- The round adapter replays positionally (`_RollVectorRng` ignores roll keys),
  so a case whose engine roll *order* legitimately differs from the modular
  tape would misreport as divergence. The current corpus aligns; noted as a
  harness caveat for future round cases.
- 18 Class C divergences and the Class A reporting artifacts remain untouched
  (phases 0/3).

---

## 8. Phase 3 outcome (2026-10-25)

All 18 Class C divergences fixed in six batches, plus the Black Hunger port.
Specifications: **3778 PASS / 15 PENDING_ADAPTER / 0 DIVERGENCE** (was
3758/17/18). The 15 pendings are all admission-gate refusals of genuinely
unported tags (phases 5–7 work). All three temporarily rejected behaviours
(`spectral-touch`, `vomit`, `mechanic.black-hunger`) were restored after their
specifications passed against the oracle.

| Batch | Root cause | Fix |
|---|---|---|
| A. Spectral Touch (5) | Engine: the extra wound resolved into state but not into the attack's observation; fields were assigned, not composed. | `_attacks.py`: wound/damage/critical observation fields compose (`|=`/`+=`); the nested extra merges through a child observation. Gate restored. |
| B. Vomit (4+1) | **Adapter**, not engine: `_vector_replacement_pool` re-implemented replacement selection and omitted vomit; the driver already used `_select_attack_replacement`. The phase-1 withdrawal was based on this adapter artifact. | Adapter now calls the engine's `_select_attack_replacement`. Gate and both `test_vomit_attack` assertions restored. |
| C. Crack Shot / Infallible (5) | Engine: two one-line port mistakes in `_operators.py` hit-reroll mask — Infallible gated on `first_round & charge` (modular: any charge), Crack Shot gated on charging (modular: first round only). | Conditions now mirror `modular/contexts.py` exactly. |
| D. Tentacle grapple (2) | **Adapter**: `_vector_pool` never invoked the engine's `_tentacle_forfeit`. | Adapter calls it as the driver does. |
| E. Unpredictable (1) | Engine: hardcoded attack 0 as the unpredictable one, ignoring the declaration decision. | Mirrors `_declared_unpredictable_attack`: offered per allocation index via the decision policy, default index 0 without one; applies to the off-hand allocation too. |
| F. Pike (1) | Engine: the first-round-only Strike First scope covered spears but not pikes in `_operators.priority`. | Pike added alongside spear, as in `phases.py`. |
| G. Black Hunger (2 + gate) | Engine: no own-turn activation. | Driver round start: per-row own-turn activation (+1 `attacks_bonus`, `condition.black-hunger-active`, skipped while grappled/grappling/netted); backlash now fires only for activated rows on the owner's turn and emits observations. Gate entry removed; the stale `test_shared_families` assertion (compile-time +1) corrected to the runtime model. Pre-existing failure `test_black_hunger_adds_attack_...` cleared. |

Validation (targeted only, per instruction): each batch's specification cases
re-run to PASS; `tests/engines/vectorized + shared +` touched modular tests:
309 passed with only the 4 remaining pre-existing failures (down from 5);
full specification parity once at the end. No statistical or battery campaign
was run — the production driver changed (hunger activation, observation
threading), so the statistical layer and parity battery should be exercised
before any merge/certification claim.

Remaining after phase 3: the 15 gate-refused specs (ports, phases 5–7), the
70 pending obligations (Class A reporting artifacts, phase 0 remainder), the
179-tag gate drain, and 4 pre-existing engine-test failures outside this
phase's scope (disability runtime effects, animal friendship, frantic int8
overflow, random-profile characteristics — plus the native/replay/battery and
5 calibrate items recorded in §6).

---

## 9. Phase 0 remainder — Class A reporting defects (2026-10-25)

Scope: the obligation inventory only
(`apps/combat-lab/.../parity/_vectorized.py::verify_vectorized_parity`). No rule
was ported and no behaviour was marked verified on a string match.

### The defect was two-sided, and the larger side was the opposite of §2

§2 described Class A as false *negatives* — tags the engine implements that the
substring scan cannot see. That is real but small (4 tags). Auditing the other
direction found the dominant defect: the same scan produced **108 false
positives**. A tag's literal appears in `vectorized/*.py` whenever the port was
*written*, but the NumPy admission gate refuses every duel carrying a tag that
is still in `NUMPY_PENDING`. For those 108 the code exists, is unreachable, has
never executed, and was nevertheless counted as verified coverage.

The inventory was therefore claiming 251/321 tag obligations while the engine
could only ever run 147 of them.

### Changes

1. `_vectorized.py` — tag evidence is now resolved by `_tag_evidence()` in a
   fixed order instead of one substring test:
   - `consumer == "construction"` → `shared-construction` (no overlap with the
     gate: verified, all 20 of them).
   - tag in `_numpy_gated_tags()` → **`numpy-gate-refused`, not verified**. The
     set is read from the engine's own gate via `kernel.pending_capabilities("numpy")`,
     so it tracks the port automatically and cannot drift from `require_optimized_support`.
   - explicit `INDIRECT_TAG_EVIDENCE` entry → verified only if the named
     consumer symbol is itself present in the vectorized sources, so a rename
     drops the obligation back to pending rather than silently keeping it.
   - otherwise the previous literal scan.
2. `_vectorized.py` — `INDIRECT_TAG_EVIDENCE` gained the four Shadow Dances
   pointing at `_driver._select_shadow_dance`, plus an inline record of the four
   audited-but-withheld families (below).
3. `kernel.py` — comments recording the `mechanic.death-blow` /
   `mechanic.deathblow` trap beside *both* names, as §2 asked.

### Measured results (inventory only; no parity or broad suite run)

| tag obligations (321) | before | after |
|---|---|---|
| verified | 251 | **147** |
| false positives withdrawn | — | **−108** (all `numpy-gate-refused`) |
| false negatives corrected | — | **+4** (Shadow Dances) |

| report totals (391) | before | after |
|---|---|---|
| verified | 321 | **217** |
| pending | 70 | **174** (151 gate-refused + 23 no vectorized consumer) |

### What was corrected, and why only that

**Shadow Dances (4).** `_driver._select_shadow_dance` filters `SHADOW_DANCES`
with `f"dance.{dance}"` over unprefixed names, so no full tag is ever a literal.
Confirmed, not inferred: a duel driven through `simulate_batch_observed` asks
`round.0.first.dance.<name>` for all four, and the post-selection
`global_effects` is **field-for-field identical** to
`modular.rounds.select_shadow_dance` for each of the four. The gate admits them.

**Deliberately left pending** — the consumer exists but the obligation is not
discharged. Each is recorded inline in `INDIRECT_TAG_EVIDENCE`:

| Tag(s) | Consumer found | Why not corrected |
|---|---|---|
| `condition.disability-1..6` | `_state.py` via `f"condition.disability-{result}"` — same computed-literal shape as the dances | its only vectorized validation, `test_rule_families_a.py::test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects`, **fails today** |
| `poison.vampires-only` | shared `phases.black_lotus_wounds`, called at `_operators.py:974` | modular calls it from two sites, vectorized from one; coverage of the second unproven |
| `mechanic.ogre-unarmed` | shared `phases.unarmed_attack_cap_applies`, `_driver.py:1186,1191` | modular has a third call site (`rounds.py:1711`, post-disarm re-equip) the driver has no equivalent for — partial port |
| `weapon.barbed-whip` | — | the driver actively denies it (see below) |

### New engine defect found (not fixed — out of this phase's scope)

`vectorized/_driver.py:22 _WHIPCRACK_TAGS` is a **stale fork** of
`phases.WHIPCRACK_WEAPON_TAGS` and omits `weapon.barbed-whip` and
`weapon.thinglash`. Neither tag is gate-refused, so the NumPy engine accepts
those duels and denies the whipcrack bonus attack that modular grants. Worse,
the same engine disagrees with itself: `_operators.py:405` uses the shared
frozenset while `_driver.py` uses the fork. This is a direct violation of the
§4 "Share, don't fork" rule. One-line fix (use the shared constant), but it
changes production behaviour and needs its own validation — schedule with
phase 3/7.

### Validation performed (targeted only, as instructed)

- Differential of both `select_shadow_dance` implementations, all four dances.
- Live `simulate_batch_observed` probe confirming the driver requests the dance
  decisions and the gate admits the tags.
- Before/after inventory diff reconstructing the old rule against the same
  worktree sources, so the 108/4 split is measured, not estimated.
- `tests/tooling/verification/reports/test_parity_reports.py`: **2 failed,
  1 passed** on the affected selection — the identical failure set as the
  unmodified baseline (the full file is 2 failed / 29 passed before and after).
  Both failures are the pre-existing end-state assertions `assert
  payload["complete"]`, which demand the migration already be finished.
  `tests/engines/parity/test_parity.py::test_vectorized_parity_inventory_is_complete_and_exact_checks_pass`
  (`assert report.pending == ()`) is the same pre-existing kind and was not run.
- No parity run, no battery, no statistical layer, no broad suite.

### Still open after phase 0

- **174 pending obligations.** 151 are honest gate refusals that resolve as
  phases 4–7 drain the 179-tag gate. The other 23 are tags the gate **admits**
  with no vectorized consumer found — these are the gate-honesty risk, because
  the engine resolves those duels without the rule instead of refusing them.
  Beyond the 4 analysed above, 8 more are read at runtime by the modular engine
  and by nothing in `vectorized/`: `mechanic.whip-master`,
  `mechanic.veskit-no-pain`, `mechanic.hypnotic-gaze`,
  `mechanic.drenok-berserker`, `rule.bear-hug-unarmed`, `identity.slayer`,
  plus the two whip tags above. The remaining ~8
  (`armour.attlas-plate-mail`, `armour.chaos-armour`,
  `mechanic.centaur-trample`, `mechanic.wheelo-skill-modifications`,
  `skill.axe-mastery`, `preparation.elven-wine`, `mechanic.haunted-mien`,
  `mechanic.wall-of-steel`) have no runtime literal in *either* engine and look
  construction-discharged; confirm against the compiler and, if so, re-label
  their `MODULAR_TAG_CONSUMERS` entry `construction` rather than special-casing
  the report.
- **The field obligations were not re-examined.** All 61 pass on a `f".{field}"`
  substring test, which is looser still than the tag test. Not addressed here.
- Everything from §8 remains: the 179-tag drain and the 4 pre-existing engine
  test failures.

---

## 10. Phase 0 remainder, part 2 — the 23 non-gated pending obligations (2026-10-25)

§9 left 23 obligations the NumPy gate **admits** while the inventory found no
vectorized consumer. Those were the gate-honesty risk: for each, the engine
either consumes the tag invisibly to the scan, or resolves the duel without the
rule instead of refusing it. All 23 are now classified and resolved.

| Outcome | Count |
|---|---|
| Reporting gap — consumer real and validated → mapping corrected | **7** |
| Confirmed incorrect behaviour → temporarily rejected at the gate | **7** (+1 non-obligation) |
| Uncertain → left pending, nothing implemented | **9** |

Inventory: verified **217 → 224**, pending **174 → 167**; non-gated pending
**23 → 9**. Gate `residual_tags` 81 → 89.

### Corrected (7) — implementation real, validated against the oracle

| Tag(s) | Consumer the scan could not see | Validation run |
|---|---|---|
| `condition.disability-1..6` | `vectorized/_state.py:142` reads `f"condition.disability-{result}"`, the same computed literal as the oracle's `modular/state.py:285`; no full tag is ever a source literal | all 10 `mechanic-disability` + `editorial-cripples-disability` specification cases PASS (six are one `initialize` case per table result), and a direct differential confirms identical characteristics for results 1–6 |
| `poison.vampires-only` | the **shared** `phases.black_lotus_wounds`, called with identical arguments from `modular/contexts.py:699` and `vectorized/_operators.py:974`; the scan only globs `vectorized/` | 4/4 agreement of `failure_still_wounds` across {vampires-only, plain} × {`species.vampire`, human}; 55 `black-lotus`/`bear-hug`/`trained-bear` specification cases still PASS |

Both are recorded in `INDIRECT_TAG_EVIDENCE` naming the consumer symbol, so the
mapping drops back to pending if the consumer is renamed.

### Rejected (7 obligations + 1) — measured wrong, now refused

Added to `_pending_snapshot().residual_tags` with an inline `TEMPORARY` note and
a restore condition. The NumPy engine now refuses these duels rather than
answering them incorrectly.

| Tag | Confirmed defect |
|---|---|
| `mechanic.ogre-unarmed` | **Measured** `attack_count` = 1 vs oracle 2 on the frozen Ogre Hunter. `_operators.attack_count` (lines 338/357) forked the predicate as `not ignores_unarmed_penalties(effect)` instead of shared `phases.unarmed_attack_cap_applies`, which exists precisely to exclude this tag. |
| `rule.bear-hug-unarmed` | **Measured** through `resolve_attacks`: an axe-armed Domnu is offered a `bear-hug` decision the oracle never offers. `modular/pools.py:479` requires both hits to be unarmed; `_attacks.py:1158` checks only `global_effects.bear_hug`. |
| `weapon.barbed-whip`, `weapon.thinglash` | `_driver._WHIPCRACK_TAGS` is a stale fork of `phases.WHIPCRACK_WEAPON_TAGS` missing both, so the driver denies their whipcrack attack while `_operators.py:405` (shared set) treats them as whips — the engine disagrees with itself. `weapon.thinglash` carries no obligation but has the identical defect and was rejected with it. |
| `mechanic.whip-master` | No TC14 reroll: neither `mechanic.whip-master` nor `weapon.whip-tc14` appears in any vectorized source; `modular/attacks.py:255` offers an optional hit reroll. |
| `mechanic.drenok-berserker` | No Drenok behaviour or `drenok_fighting` column; the oracle keeps the fighter standing on a 4+ at zero wounds (`modular/attacks.py:782`), vectorized puts them Out. |
| `mechanic.veskit-no-pain` | Absent; `modular/attacks.py:854` turns any non-Out injury into Standing, vectorized models only generic `ignore_pain`/`jump_up`. |
| `mechanic.hypnotic-gaze` | No control powers at all: `CONTROL_POWERS` (`modular/rounds.py:128`, Leadership contest + auto-hit) has no vectorized counterpart. |

Two of the seven (`ogre-unarmed`, `barbed-whip`) are **forked-predicate**
defects — a shared helper copied into `vectorized/` and left to rot. Both are
one-line fixes to use the shared symbol, but each changes production behaviour
and needs its own validation, so neither was applied here. This is the third
instance of the §4 "Share, don't fork" rule being broken; a sweep for other
forked copies of `phases` helpers is worth scheduling.

### Left pending (9) — nothing implemented, nothing claimed

- `identity.slayer` — unsupported in vectorized, but its only runtime use
  (`modular/attacks.py:261`) additionally requires `condition.rememberer-support`
  **and** one of `mechanic.rememberer-large-only` / `-large-or-tough`, all three
  already gate-refused. The branch is therefore unreachable in any admitted
  duel. Rejecting the tag would refuse every Slayer for no correctness gain, so
  it stays pending and ports with the Rememberer family.
- `armour.attlas-plate-mail`, `armour.chaos-armour`, `mechanic.centaur-trample`,
  `mechanic.wheelo-skill-modifications`, `mechanic.wall-of-steel`,
  `mechanic.haunted-mien`, `preparation.elven-wine`, `skill.axe-mastery` — no
  runtime literal in *either* engine; each appears only in
  `mordheim_construction/compiler.py` (or, for the last three, nowhere in
  Python at all, so they are resolved from the catalog). They look
  construction-discharged, which would make them `shared-construction`, but
  confirming that means auditing the compiler per tag and editing
  `MODULAR_TAG_CONSUMERS` — the port spec §4 says not to re-derive. Deliberately
  uncertain.

### Validation performed (targeted only)

- Differentials: ogre attack pool (19 frozen fighters, 3 distinct configs ×
  4 contexts), armed-Domnu bear hug through `resolve_attacks`, black-lotus
  wound context (4 combinations), disability initialization (results 1–6).
- Specification subsets via a filtered runner (no full parity): 10 disability
  cases PASS; 55 bear-hug/black-lotus/trained-bear cases PASS, 0 pending,
  0 divergent.
- Gate-impact scan: **no** `unit/vectorized`, `unit/shared` or `unit/parity`
  case in the frozen corpus, and no benchmark or deep scenario, carries a
  rejected tag — the statistical layer and the vectorized suite are untouched.
- `pytest tests/engines/shared/test_kernel_plan.py`,
  `test_parity_inventory_covers_fields_tags_and_complex_sequences`,
  `tests/rules/construction/test_shifty_activation_contracts.py`: 25 passed.
- `pytest tests/engines/modular/{test_domnu_bear_hug,test_drenok_lifecycle,test_tc14_whip,test_control_family}.py`: 43 passed.
- `pytest tests/engines/vectorized/test_rule_families_a.py tests/engines/shared/test_phases.py`:
  50 passed, 2 failed — `disability_guardian_unarmed_and_onogal` and
  `animal_friendship`, both pre-existing §8 failures, confirmed identical
  against the unmodified sources.
- No parity run, no battery, no statistical layer, no broad suite.

### Still open

- **9 non-gated pending obligations** (above). The 8 construction-looking ones
  are the next cheap win: audit the compiler and re-label in `consumers.py`.
- **158 gate-refused obligations**, now including the 7 freshly withdrawn ones.
  The gate is honest but the engine is more restricted than before phase 0:
  Ogre Hunters, Domnu, barbed whips/thinglash, TC14 whips, Drenok, Veskit and
  Hypnotic Gaze duels are refused by NumPy until ported.
- The **61 field obligations** still pass on the loose `f".{field}"` test
  (§9); not addressed.
- Everything from §8: the 179-tag drain and the 4 pre-existing engine failures.

---

## 11. Development testing policy (2026-10-25) — verify at the end, not per step

User decision: development speed over per-step certainty. Errors during
porting are accepted; a single verification task after the whole modular
engine is ported (phase 8) is the net that catches them. This supersedes the
per-phase rule in §3 and amends the first rule of §4 for phases 4–7.

### During development (phases 4–7)

- **Default: the smallest focused check that exercises the rule just ported,
  if one already exists.** In order of preference:
  1. the rule's own specification cases through the filtered runner
     (`§10` pattern — seconds, no full parity);
  2. the single pytest file/node that covers the rule
     (`pytest tests/engines/... -k <rule>`);
  3. a one-off differential against the modular oracle on a frozen corpus
     fighter (the §9/§10 probe pattern).
- **Skip verification entirely when confident** — e.g. mechanical ports that
  reuse a shared `phases` helper, new mask/column plumbing that mirrors an
  existing operator, or batch members identical in shape to one already
  checked. Checking one representative of a themed batch and skipping the rest
  is the expected mode for phases 6–7.
- **Do not run during development:** full `parity`, the battery, the
  statistical layer, `pytest tests/engines` or broader, or any multi-minute
  suite. No recorded parity delta per phase.
- **Keep the ledger cheap but truthful.** When a tag's port lands, move it out
  of `NUMPY_PENDING` on implementation alone (amended §4 rule); do not wait for
  spec confirmation. What stays absolute: never connect a tag with no
  implementation behind it, and never delete/weaken a failing check to get
  past it — leave it failing for phase 8.
- **Log what was skipped.** One line per port in `TMP_VECTORIZED_MIGRATION/`
  work notes: tag(s), what (if anything) was run, and "unverified" where
  nothing was. Phase 8 starts from this list, so skipping costs nothing later
  but silence would.

### Verification — moved out of this plan (2026-10-25)

Deep verification is **no longer phase 8 of this plan**. It is a separate task
that starts after this plan completes. Everything it needs — what was deferred,
what is known-partial, what is known-broken — is accumulated in
`TMP_VECTORIZED_MIGRATION/HANDOFF_VERIFICATION.md`. Keep that file current as
you port; it is the only channel to the verification task.

### Accepted risks (eyes open)

- Defects will accumulate silently between ports; a wrong shared helper can
  contaminate later ports built on top of it. Mitigation: the forked-predicate
  sweep (§10) and "share, don't fork" matter *more* under this policy, since
  shared helpers are what keep unverified code aligned with the oracle.
- Bisecting a phase-8 failure across weeks of unverified commits is the price
  paid for the speed. Small, per-tag commits keep that bisect tractable.
- The gate may be optimistic in the window between a port landing and phase 8
  (exactly the spectral-touch failure mode §4 warned about). That is now an
  accepted, temporary state rather than a defect — but only until phase 8.

---

## 12. Phase 4 outcome (2026-10-25) — weapon profiles, under the §11 policy

`weapon_profile_tags` pending **8 → 0** (gate now 89/90/0). Two subagents with
non-overlapping file ownership (`_operators.py`, `_attacks.py`); coordinator
owned `kernel.py`. Scoping against the oracle showed 6 of 8 profiles compile
entirely to generic EffectSet fields (connect-only, zero engine code);
`skull-busta`'s runtime branch already existed in `_attacks.py:881`; the only
real port was Shock Rod — a `shock` branch in `injury_conditions` plus
threading `shock=` into the production `InjuryContext` (the `injury_results`
path already had it). Testing: one sub-second shock differential against
`phases.injury_condition` + gate-admission check; everything else deferred —
per-tag log in `WORK_NOTES_PHASE4.md`, including one out-of-scope observation
(tough-as-steel merged into hard_to_kill in the production injury context).
Next: phase 5, supplied conditions.

---

## 13. Phases 5–7 outcome (2026-10-25) — supplied conditions, local modifiers, stateful residuals

Gate drained **179 → 14**. `NUMPY_CONNECTED_TAGS` 40 → 205;
`weapon_profile_tags` 0, `residual_tags` 10, `local_modifier_tags` 4.

### Method: scope before delegating

Scoping first (as in phase 4) changed the shape of the work. Of the 179 gated
tags, **135 needed no new engine code**: 119 already had a working vectorized
consumer in executable code (the "written ahead of the gate" set §9 found —
checked that none was comment-only), and 16 more are construction-discharged
(no runtime reader in *either* engine; the compiler emits generic fields both
consume). Only **44** were real ports.

Seven subagents, strict one-writer-per-file, six in parallel then one
integrator:

| Agent | File | Outcome |
|---|---|---|
| supplied conditions | `_state.py` | 2 tags needed no code (one already shares the oracle's `maximum_wounds`), 1 blocked |
| psychology | `_psychology.py` | 4 ported (+4 ledger columns, no `_types.py` change), 1 needed no code |
| leadership | `_leadership.py` | 5 ported, no blockages |
| local modifiers | `_operators.py` | §10 ogre fix + 2 ported, 5 needed no code, 2 inert |
| attack residuals | `_attacks.py` | §10 bear-hug fix + 7 ported, 3 blocked |
| round loop | `_driver.py` | §10 whipcrack fix + 9 ported, 2 needed no code, 4 blocked |
| integration | `_driver.py` | wired all 9 psychology/leadership handoffs |

### The three §10 defects are fixed and re-verified in this worktree

| Defect | Before | After |
|---|---|---|
| `mechanic.ogre-unarmed` forked cap predicate | vec 1 vs oracle 2 | **2 vs 2** |
| `rule.bear-hug-unarmed` missing qualification | armed Domnu offered the hug | **no offer** (oracle agrees) |
| `_driver._WHIPCRACK_TAGS` stale fork | barbed-whip + thinglash missing | **fork deleted**, shared frozenset used |

All three were "share, don't fork" violations; all three are now single-source.

### Deferred verification (PLAN §11) — what is unproven

**Everything below is connected on implementation, not on proof.** Phase 8 owns
all of it:

- **165 tags connected without running their specifications.** The 135
  pre-existing consumers have never executed through the gate; the 30 new ports
  were written against the oracle by reading, not by differential.
- **Testing actually run:** three targeted differentials for the §10 fixes, one
  import check per file, one integration smoke (`_simulate_batch_core`, 6 seeds
  × 8 rows × 12 rounds with all eight new psychology/leadership tags forced
  live), and a final batch smoke across barbed-whip/katana/shock-rod. No parity,
  no battery, no statistical layer, no pytest suite.
- **A stale `/tmp/wtpath` pointed agents' *runtime* checks at a sibling
  worktree** for part of the run. Edits were by absolute path and are correct;
  the two measured claims were re-verified here afterwards. Any other agent
  runtime observation from that window is unconfirmed.

### Known-inert and half-ported code that is connected anyway

Flagged now so phase 8 does not mistake these for regressions:
- `mechanic.whip-master` — reroll live on the main/off-hand path; inert where
  `_prepare_weapon_attack` is called without `decisions`/`key` (the specs
  adapter, one driver site) and for `extra_attacks`.
- `condition.righteous-charge` — raises `ValueError` on a batch whose rows
  disagree about charging (refuse-don't-guess, mirroring Tranquil Fauna). A
  sampled-charge statistical run **will** hit this.
- Mark of Shornaal — test, dice, resource spend and attack bar are correct; the
  auto-hit half is inert for the same missing column that blocks Hypnotic Gaze.

### Still refused (14) — 11 blocked by one architectural decision

The **G02 frozen `CombatState` schema** is the single blocker for 11 of the 14.
Each needs a per-row column the oracle has in `FighterState` and the vectorized
state deliberately does not:

| Tag(s) | Missing column |
|---|---|
| `mechanic.drenok-berserker` | `drenok_fighting` |
| `mechanic.magic-acorn` | `magic_acorn_used` |
| `condition.rememberer-support`, `mechanic.rememberer-large-only`, `mechanic.rememberer-large-or-tough` | once-per-battle flag + per-pool marker |
| `mechanic.babbling-banter`, `mechanic.dodge-sidestepper`, `mechanic.confound-and-confuse` | `banter_trick_active`, `dodge_trick_active`, `trip_trick_active` |
| `mechanic.hypnotic-gaze` | `charm_auto_hit` |
| `condition.danse-macabre-controlled` | per-side controlled flag |
| `mechanic.needle-and-thread` | `mouth_sewn` |

**Decision needed before phase 8:** unfreezing the state schema would clear 11
tags at once. The projections are already written and inert, waiting for the
columns. This is the single highest-value remaining decision in the migration.

The other three are independent:
- `mechanic.giggle-juice-spray` — needs a positional-substitution hook in
  `_attacks.resolve_attacks` (mirroring `unpredictable_index`); the oracle
  substitutes one allocated position, not the whole pool.
- `mechanic.djinns-curse` — every *consumption* site is ported; only the
  activation (`modular/rounds.py:565`) is missing.
- `mechanic.herb-lore-outside-combat` — predicate correct but unreachable: the
  vectorized loop drops disengaged rows before recovery, while the oracle heals
  before its disengaged return.

### Engine defects found while porting (reported, NOT fixed)

1. **`_row_equipment` short-circuit is always true.** It tests
   `replacement is not fighter`, but callers pass the pristine compiled fighter
   as `fighter` and a `dataclasses.replace` descendant as `replacement`, so
   `equipment_for_rows` is **never reached** — per-row equipment (broken hands,
   transforms, Hillman wolf, mutations, brands) is silently bypassed
   engine-wide. Same defect class as the three forks. High priority.
2. **`mechanic.death-blow` out-of-action replay looks mis-keyed** — its comment
   and semantics are the Slayer's `mechanic.deathblow`, but the oracle gives
   `death-blow` no such replay. Left byte-identical; one-word fix if confirmed.
3. **`_crude_belch_losses` spends the singer's Leadership ledger for the
   listener's test** (`leadership[0]` with `first=True` while testing `second`).
4. **Missing per-round `maximum_wounds` clamp** after the equipment projection
   (`modular/rounds.py:511`).
5. `priority` lacks the oracle's `absent_initiative` and `woven-mist-active`
   clauses; `build_attacks` differs from `attack_count` in four further places
   (unarmed-fighting accepting `weapon.natural-attacks`, `elif` chaining,
   `min(attacks,1)` vs `attacks = 1`, `wraith-touch` clamp, pistol gating).
6. Sea Shanty's placement is oracle-faithful, but `_crude_belch_ogre` still
   resolves earlier in the driver than the oracle does, so its decision/RNG
   position stays divergent.

### Process note

`mechanic.needle-and-thread` was missed by the coordinator's partition — it was
assigned to no agent. It turned out to be blocked by the frozen schema anyway
(`mouth_sewn`), so nothing was lost, but the partition was derived by hand and
should be generated from the gate next time.

---

## 14. Phases 5–7 COMPLETE (2026-10-25) — gate at zero

```
NUMPY_PENDING: residual 0 | local_modifier 0 | weapon_profile 0 | behaviours 0
NUMPY_CONNECTED_TAGS: 219
```

**This plan's exit criterion is met.** Verification is a separate task; its
input is `HANDOFF_VERIFICATION.md`.

### What unblocked the last 14

The **G02 freeze on the `CombatState` schema** was lifted by explicit user
decision. That one change cleared 11 of the 14 remaining tags at once —
projections for several were already written and inert, waiting for columns.

Twelve per-row `bool` columns added (`_types.py` 53 → 65 fields):
`drenok_fighting`, `magic_acorn_used`, `rememberer_used`, `rememberer_active`,
`banter_trick_active`, `dodge_trick_active`, `trip_trick_active`,
`charm_auto_hit`, `danse_macabre_controlled`, `mouth_sewn`,
`giggle_juice_used`, `trip_trick_used`.

Plus three consumer-side fixes that were the real blockers behind the columns:
per-pool `rememberer_active` clearing, switching the save path to the
state-aware `special_save_context`, and the Jester trick declaration.

### Engine defects fixed in this pass (all previously recorded as open)

| Defect | Fix |
|---|---|
| `_row_equipment` short-circuit always true — `equipment_for_rows` was **dead code**, so per-row equipment (broken hands, transforms, Hillman wolf, mutations, brands) was bypassed engine-wide | predicate now compares against the round's phase fighter; new `_diverging_rows` gate keeps the fast path |
| `_crude_belch_losses` spent the singer's Leadership ledger for the listener's test | ledgers swapped to match the adjacent Sea Shanty calls |
| Missing per-round `maximum_wounds` clamp | `_clamp_maximum_wounds`, importing the shared `modular.state.maximum_wounds` |
| `mechanic.death-blow` out-of-action replay mis-keyed | confirmed against the oracle and removed; only `mechanic.deathblow` drives the replay |

### Notable corrections agents made to my briefs

Three times a subagent refuted the task premise rather than inventing a rule —
each saved a wrong implementation:
- **`mechanic.needle-and-thread`** has no Leadership *state* read half.
  `FighterState.mouth_sewn` is write-only in the oracle; the consumer is the
  supplied tag `condition.mouth-sewn`, already mirrored. My brief came from a
  compressed `consumers.py` gloss. Only the write half was needed.
- **`trip_trick_used` is not once-per-battle** — the oracle clears it in the
  same `replace` that declares each turn's trick (`modular/rounds.py:741`), so
  it is one replacement *per declaration*. My column docstring said otherwise;
  corrected, and relayed mid-flight to the driver agent.
- **`mechanic.giggle-juice-spray`** could not go in `_select_attack_replacement`
  as I directed; the oracle substitutes one allocated position, not the pool.
  Implemented as a positional hook mirroring `unpredictable_index`.

Also widened beyond brief, correctly: `single_bonus=True` belongs on eagle,
stomp and last-bite pools too, not just Whipcrack/Shifty — the oracle computes
it from a label-suffix set (`modular/rounds.py:1736`).

### Testing (deliberately minimal, per §11)

Per-rule sub-second smokes and instrumented tiny batches only, plus a final
end-to-end check: all modules import, four duel configurations resolve, and the
observed-batch resource ledger now reports `magic-acorn`, `rememberer` and
`giggle-juice`. **No parity, battery, statistical layer or pytest suite was
run at any point in phases 4–7.**

### New open items — added to HANDOFF_VERIFICATION.md

- `effect.no-saves` is unimplemented in the vectorized engine (oracle
  `modular/attacks.py:735-737`); a real divergence, found during the save-path
  switch but outside its scope.
- `native/_combat_compile.py:218` still calls the stateless
  `special_save_targets`, so the native backend keeps the Dodge-blind
  behaviour.
- `_specifications.py` binds the `special_save` parity spec to
  `special_save_targets`, which the engine no longer uses.
- `condition.righteous-charge` is per-row for Fear/Stupidity but still reads
  the ungranted fighter inside `_charm_gates`, `resolve_feral_instinct` and
  `_apply_opponent_leadership` on split batches.
- Decision-key drift for extra attacks when a Whipcrack or Tentacle forfeit
  shifts the oracle's tuple index (affects key strings, not dice).

---

## 15. PLAN CLOSED (2026-10-25) — completion claim reconciled

§14's "complete" meant the gate's exit criterion; the handoff file still listed
implementation debt. This final pass reconciled the two. The plan now ends with
**no known implementation gap that is not an explicit, recorded scope decision**
in `HANDOFF_VERIFICATION.md` §3.

### Closed in this pass (three parallel agents, one per file)

| Gap (recorded as open drift) | Outcome |
|---|---|
| `priority` missing `absent_initiative` tier demotion + woven-mist floor | ported; the `ABSENT_INITIATIVE` ordering constant did NOT cover the tier demotion |
| `attack_count` vs `build_attacks`, four differences | all closed; clause-level differential vs the shared oracle across the changed cases: all match |
| production `InjuryContext`: tough-as-steel in the wrong field, missing fen fire exclusion | mirrored to `modular/contexts.py` exactly |
| `effect.no-saves` unimplemented | producer (infection effect) and consumer (ward+regen forced blocked) ported |
| Bear Hug consuming wrong attack indices | oracle confirmed 0-1-only on close reading; vectorized selection now mirrors it |
| `_crude_belch_ogre` ordering | moved into the oracle's shanty/belch per-owner loop; hit-penalty fold moved with it |
| diverging rows losing round declarations | `_carry_declarations` applies the oracle's `_mutated_phase_fighter` merge to per-row projections; deliberately merges the projection *output* so declarations are not baked into the battle-lived `effective_fighter` cache |

Stale handoff entries removed after re-checking the tree: whip-master
extra-attacks coverage, the righteous-charge `ValueError`, and Mark of
Shornaal's auto-hit were all already closed by earlier passes.

### Explicit scope decisions (full detail in HANDOFF_VERIFICATION.md §3)

Engine: `_crude_belch_ogre` internals (needs a per-row hit-penalty mechanism),
round-level D6s bypassing owned-roll resources (design decision; a leadership
batch helper already exists at `_leadership.py:154`), righteous-charge
split-batch psychology readers, extra-attack decision-key drift, Bear Hug
pool-index caveat. Out of scope by charter: the native backend (frozen
`NATIVE_PENDING`, plan §5 Q1) and the parity harness
(`special_save` spec binding, adapter `decisions`/`key` plumbing).

### Checks in this pass (minimal, per §11)

One clause-level differential (`attack_count`/`priority` vs the shared oracle),
per-edit structural smokes, and a final end-to-end batch over four weapon
configurations with the gate asserted at zero — all with an inline PYTHONPATH
after `/tmp` path files were clobbered a second time by a sibling session
(handoff §7 now warns: never read a PYTHONPATH from /tmp).

### Final state

```
NUMPY_PENDING: 0/0/0/0     NUMPY_CONNECTED_TAGS: 219
CombatState: 65 fields (12 added after lifting the G02 freeze)
Implementation remaining in this plan: none
Known deferred items: all enumerated in HANDOFF_VERIFICATION.md §3 (scope
decisions), §4b (newly-live code), §5 (pre-existing failures), §6 (reporting)
```

The next task is verification, starting from `HANDOFF_VERIFICATION.md`.
