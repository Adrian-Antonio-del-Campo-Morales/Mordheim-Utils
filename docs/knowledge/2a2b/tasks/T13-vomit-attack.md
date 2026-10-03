# L02 — Canonical optional Vomit Attack

Implemented on 2026-10-03 on `2A2B`, HEAD `1b7f7cf`, with the existing
uncommitted T13 and shared-construction work preserved. F010 is resolved for
canonical compilation and modular execution. Optimized ports remain in
L19/L20; this delivery does not certify T14 or complete T13.

## Source and contract

[Underworld Alliance, printed p. 5](https://www.broheim.net/downloads/warbands/supplement/mutinyinmarienburg/Underworld%20Alliance.pdf)
allows the Warpstone Troll to choose one automatic Strength 5 melee hit instead
of its normal attacks, ignoring armour saves. The canonical rule references
[shared-rule.vomit-attack](../../../../sources/knowledge/catalog/rules/special-rules.yaml).
The already verified [Vomit mechanic](../../../../tests/specs/semantic/rules/vomit-attack.yaml)
also forbids parrying the automatic hit. No new source ruling or scope change
was required.

The selected `warpstone-troll--vomit-attack` binding now compiles the maintained
`attack`/`attack` execution contribution into `CompiledFighter.vomit_attack`.
It does not turn the equipped weapon into passive/global bonuses. The Troll
keeps its normal club and four base attacks, and the recipient checks remain
owned by the shared eligibility module.

The modular policy receives `round.<index>.<side>.vomit-attack` before attack
allocation each round. Accepting replaces that round's normal attack pool;
rejecting retains it. The original immutable fighter remains unchanged, so
the choice is available again in later rounds. `AlwaysAccept` chooses vomit;
`AlwaysReject` keeps the ordinary attacks.

The chosen attack has no equipped-hand material/poison contribution, no off-hand
attack or appended natural attack. Competing charge replacements and random
Spawn allocation do not replace it again. The same pool-allocation correction
applies to the existing explicit `main_weapon_id="weapon.vomit-attack"` route.
Generic defender modifiers, independent special saves, damage, injury and
after-wound reactions retain their existing consumers. Automatic success is
not a natural hit six and cannot activate Spectral Touch's six trigger.

## Implementation and usable route

- [Compiler](../../../../packages/python/roster-construction/mordheim_construction/compiler.py)
  compiles the separate option from the existing execution catalogue.
- [Models](../../../../packages/python/core/mordheim_core/models.py) carry the
  optional contribution without changing existing constructor arguments.
- [Rounds](../../../../packages/python/combat-engine/mordheim_combat/modular/rounds.py)
  choose the option; [pools](../../../../packages/python/combat-engine/mordheim_combat/modular/pools.py)
  allocate exactly the selected attack and suppress competing normal attacks.
- [Attack resolution](../../../../packages/python/combat-engine/mordheim_combat/modular/attacks.py)
  prevents a global Bull Charge tag from bypassing vomit's wound step.
- [Kernel boundary](../../../../packages/python/combat-engine/mordheim_combat/kernel.py)
  supplies the narrow unsupported-choice guard reused by optimized entry points.

Use the canonical build with `band_id="underworld-alliance-mim"`,
`profile_id="warpstone-troll"` and
`special_rule_ids=("warpstone-troll--vomit-attack",)`. Compile normally and call
`mordheim_combat.modular.duel.simulate_duel_reference` with an explicit decision
policy, or exercise `initialize_duel` followed by `resolve_round` with strict
dice/decision tapes. No trait injection, custom-profile substitution, campaign
service or duplicated eligibility decision is needed.

Combat Lab's production analysis backend is optimized. It now refuses this
optional choice with an explicit modular-only explanation, rather than silently
running ordinary attacks. The guard covers automatic/NumPy/native dispatch,
parallel NumPy dispatch, batch/observed execution, native compilation and kernel
planning. The existing explicit vomit-weapon route without an optional profile
choice remains available. This is a modular milestone, not new GUI/backend
support for the optional choice.

## Verification

[Maintained strict cases](../../../../tests/python/combat/modular/test_vomit_attack.py)
cover canonical presence/absence, acceptance/rejection, both participant slots,
later-round rejection, armour/parry omission, special-save thresholds and
synthetic whole-pool/charge compositions. Synthetic compositions demonstrate
the operator only; they do not establish canonical access to foreign skills or
weapons. The prior selectable matrix now asserts the compiled option and retains
the Goblin Bully recipient refusal.

[Source-linked specification](../../../../tests/specs/semantic/grants/t13-warpstone-troll-vomit.yaml):
7 cases and 4 detected behavioral mutations (option removal, lost automatic hit,
Strength 4, lost armour denial). The injury case distinguishes the option from
the equipped club's concussion effect. Existing mechanic and editorial-grant
specifications are preserved.

| Check | Result |
| --- | --- |
| New strict modular cases | 16 passed |
| Final modular + documentation rerun, including parallel-dispatch refusal | 17 passed |
| Modular + construction + duel context | 868 passed |
| Focused new/existing Vomit semantic cases and mutations | 43 passed |
| Kernel/backend/runtime/native/application/architecture dependencies | 70 passed |
| Full `verify --json` | Structural complete, 1050 profiles; 566 verified / 152 pending of 718; new specification has no errors, all 4 mutations detected |

The full verifier still exits 1 because of the same 30 historical `source changed`
pairs under F001. No pin was refreshed and no required gate was weakened.
Retained entry backups, attributable diffs, commands and machine-readable
results are under `build/cache/t13-parallel/vomit-attack/`.

## Remaining work and ownership

L19/L20 own actual optimized execution of the optional choice and removal of the
guard after parity proof. L18 owns any remaining product configuration/analysis
connection. T14 retains independent source/implementation certification; the
cases and source contract accompany this delivery, not a separate test-only lot.

The new specification adds exactly 7 authored cases to the parity corpus. F057's
reserved count/completeness repair must use the current corpus, including these
cases, rather than its historical 3758-case snapshot. Its test and external
delivery files were not edited. F056 and the shared eligibility source/bundle
were also preserved. No new follow-up ID, agent, commit or push was created.
