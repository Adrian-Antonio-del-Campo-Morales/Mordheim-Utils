# Product parity implementation

Reference checkpoint: `27dcf73e000a0aba42a8e5b591b914de57133c90`.
Isolated worktree: `D:/DEVEL/Mordheim/Mordheim-Utils PRODUCT-PARITY`.
Branch: `warband-product-parity`.

The original worktree and its four untracked test files remain untouched.
Existing test-migration ownership is preserved. Integration must explicitly
reconcile later commits from that workstream before merging this branch.

## Ownership

- Integrator: session provider, product shell, shared UI, knowledge listings,
  package manifests, browser acceptance tests and integration.
- Service worker: campaign application service, types and product-service tests.
- Rules/export worker: new rules and export feature directories and font assets.
- Inventory worker: product feature manifest and evidence under docs/product-parity.

No worker may edit another worker's files. Focused tests only during development.
The integrator owns the final full-suite window. Completion requires executable
product acceptance; a successful build alone does not establish parity.
