import { defineConfig } from "vitest/config";

// P3.4: domain/application packages must run in plain Node — no DOM.
// The include globs also pick up tests added by sibling tasks (P3.2, P4.3)
// without them needing to edit this file.
export default defineConfig({
  test: {
    environment: "node",
    include: ["**/*.test.ts"],
  },
});
