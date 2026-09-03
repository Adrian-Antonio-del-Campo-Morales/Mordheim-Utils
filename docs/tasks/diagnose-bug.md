# Diagnose a failure

1. Reduce the problem to compilation, phase, mini-sequence or integration.
2. Reproduce with explicit dice and decisions.
3. Inspect the binding, the compiled value, the context, the resolver and the
   state transfer.
4. Compare against the written source, not the vectorized engine.
5. Fix the owning responsibility and add a regression.

Done when the reproduction fails before, passes after, and expresses the cause
of the defect.
