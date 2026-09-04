# Architecture

## Monorepo packages and allowed dependencies

```text
mordheim_core
  ↑
mordheim_knowledge → mordheim_construction → mordheim_combat
                  ↑          ↑
                  └ mordheim_combat_lab.application ← mordheim_combat_lab.persistence
                         ↑
                         mordheim_combat_lab.ui
                         mordheim_campaign (reuses mordheim_ui)

mordheim_combat_lab.verification → mordheim_knowledge + mordheim_construction
                                   + mordheim_combat + tests/specs
```

`mordheim_core` knows no YAML, UI or verifiers. `mordheim_combat` receives
`CompiledFighter` and never loads the KB. `mordheim_combat_lab.application`
runs use cases without Tkinter. Both applications present results with the
shared `mordheim_ui` layer and coordinate their own threads. `verification`
sits outside the runtime and exercises the real engine as the system under
test.

`mordheim_campaign` is interface-first: widgets depend on view-models and the
shared UI layer; canonical warbands and profiles enter through
`mordheim_campaign.application.knowledge_port` (on top of `mordheim_knowledge`)
and campaign persistence lives in `mordheim_campaign/persistence`. Post-battle
legality and the use of `mordheim_construction` are later phases.

## Shared resources

The KB lives once in `sources/knowledge/`. Path resolution belongs to
`mordheim_knowledge.paths` (`knowledge_root()`), with an override via the
`MORDHEIM_COMBAT_LAB_KNOWLEDGE_PATH` environment variable and frozen-EXE
support for both applications. The verification corpus lives in `tests/specs/`
(`specifications_root()`); it is test material and is not distributed.

## Path of a rule

1. The editorial rule and its binding live in `sources/knowledge/`.
2. `mordheim_knowledge` validates and loads documents by stable ids.
3. `mordheim_construction` validates access and compiles the binding into a
   `CompiledFighter`.
4. The engine consumes the effect in a phase or stateful handler.
5. A scenario in `tests/specs/` checks granting, compilation and the observable
   result.

## Engines

### Modular (oracle)

`mordheim_combat/modular/` is the scalar reference engine and the **only
correctness oracle**. It splits responsibility into state, context preparation,
attacks, pools, aftermath effects, rounds and duel orchestration:

- `state.py` — fighter/duel state and immutable transitions.
- `contexts.py` — prepared per-attack contexts shared by orchestration and
  verification.
- `attacks.py` / `pools.py` — reference attack resolution and pooled attacks.
- `aftermath.py` — stateful post-wound effects (fire, nets, black hunger, …).
- `rounds.py` — per-round state machine; `duel.py` — the public
  `simulate_duel` API.

Changing the oracle requires an independent semantic review and is outside the
optimization flow. Its behaviour is exercised by `tests/specs/` (see
[Verify rules](tasks/verify-rules.md)) and is considered critical: functional
changes are treated as dangerous and must never be made casually.

### Vectorized (analysis)

`mordheim_combat/vectorized/` is the NumPy batch engine used by the UI for
analysis; it is **not** the correctness oracle. The former single
`vectorized.py` module was split into a package without changing its public
namespace:

- `_types.py` — run constants, ledger types, tag predicates and compile-time
  helpers shared by every layer.
- `_operators.py` — stateless NumPy projections of the canonical scalar phase
  operators.
- `_attacks.py` — per-weapon attack preparation, hit/parry boundaries and wound
  resolution.
- `_driver.py` — per-round state machines, the batch loop and the public
  `simulate_duel` / `available_backends` entry points.
- `__init__.py` — facade that re-exports the historical module namespace so
  existing imports keep working unchanged.

The vectorized engine is certified against the modular oracle by
`mordheim_combat_lab.verification.parity` (per-field obligations, semantic
specifications and statistical six-sigma gates). A divergence detected while
working on the vectorized engine is presumed to be a defect of the candidate:
`parity` only reads the oracle and never modifies it. The full interaction
corpus (217/217 required pairs, see
[interaction-matrix.md](interaction-matrix.md)) runs through these adapters;
the 2026-09-04 implementation of that corpus surfaced and fixed exactly such
a candidate defect — the vectorized engine drew a wound die for automatic
wounds, shifting the ward-save roll stream that follows (`_attacks.py` now
mirrors the oracle's roll order for `automatic-wound` rows).

### Native (compiled)

`mordheim_combat/native/` holds the sources of the compiled Cython backend.
The built extension keeps the historical module name
`mordheim_combat._combat_native` so importers and already-compiled binaries are
unaffected by the source layout:

- `_combat_compile.py` — pure-Python folding layer that reuses the exact
  certified helpers of the vectorized engine to flatten every per-duel tag
  decision into scalar flags once per duel.
- `_combat_native.pyx` / `.pxd` — the Cython core consuming the compiled plan
  with flat structs (`FighterC`, `SourceC`, `DuelC`, `StateC`); each round runs
  over the active rows in C with the same phase order and tables as the
  vectorized engine.
- `__init__.py` — package description; the root `mordheim_combat/_combat_compile.py`
  facade keeps the historical import path of compiled binaries working.

The Python driver (`simulate_duel` in `vectorized`) exposes the backend with
`backend="native"` or `"auto"`; `available_backends()` reports it only when the
extension is compiled, so an environment without a C compiler keeps the NumPy
behaviour unchanged. The engine uses one PCG32 per batch derived from the
request seed, so the same request is reproducible (deterministic replay per
seed). The plan is compiled once per request (~0.5 ms); compiling the `.pyx`
to a `.pyd` happens once at install time and is outside any performance
measurement.

### Verification and performance

The native backend is certified against the modular oracle with the same
six-sigma statistical gate as NumPy (`compare_statistical_parity(...,
backend="native")` shares the modular sample with NumPy), and the performance
gate requires at least one scenario to improve 10 % without regressions above
5 % versus NumPy (`benchmark --backend native`). `test-report --statistical`
and `parity --statistical` include the native backend automatically when it is
available; in the semantic CSV the per-operator cases do not apply to it
(`NOT_APPLICABLE`): the native engine is a complete duel engine without
independent operators, verified on the duel (statistical) rows, with operator
semantics covered by the NumPy adapter. While the extension is not compiled,
those rows are marked `NOT_AVAILABLE` and the report stays `PENDING` — a
signal of real pending work. Core C changes pass through AddressSanitizer
before integration (uninitialised struct overwrites, array sizing and batch
accumulation have already been detected and fixed that way).

## Responsibility map

Legality belongs to `mordheim_construction`; composition to
`mordheim_core.effects`; phases to `mordheim_combat.phases`; workbooks and
preferences to `mordheim_combat_lab.persistence`. The tests in
`tests/architecture/` make these boundaries executable.
