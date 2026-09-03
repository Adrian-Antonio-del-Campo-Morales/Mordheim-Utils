# Implement combat behaviour

1. Classify the effect as construction, modifier, local resolution or stateful flow.
2. Use `mordheim_construction`, `mordheim_core.effects`, `mordheim_combat.phases`
   or `mordheim_combat/modular` accordingly.
3. Share the context preparer between orchestrator and verifier.
4. Inject `DiceSource` and `DecisionPolicy`; never consult global randomness or the UI.
5. Add a phase test or the minimal mini-sequence.

Example: fire-blocked regeneration compiles as data and is consumed by the
context and the special-save phase.

Done when the binding reaches an observable result and activation, absence,
limits and architecture tests pass.
