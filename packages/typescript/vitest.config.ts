import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Domain/application packages must run in plain Node — no DOM.
// The suite lives in the repository's tests/typescript tree (support code stays
// out of the packages); the aliases are the same vocabulary the web app uses.
// Dependencies resolve through the npm workspace root.
//
// Category selection uses the runner's native project mechanism: one project per
// phase category, each with an include/exclude over the maintained test tree.
// Test identities, suite names and parametrizations are unchanged, so a category
// is selected with `--project <name>` and the default run still covers everything.
// Vitest 3.2 exposes no per-test tag, so the category is resolved per file; the
// one mixed file and its limitation are documented in the web config and in
// docs/reference/test-sequence.md.
const TEST_ROOT = fileURLToPath(
  new URL("../../tests/typescript/", import.meta.url),
).replaceAll("\\", "/");

const ARCHITECTURE = `${TEST_ROOT}architecture/**/*.test.ts`;
const KB_PARITY = `${TEST_ROOT}parity-kb-vectors.test.ts`;

export default defineConfig({
  resolve: {
    alias: {
      "@domain/": fileURLToPath(new URL("./domain/", import.meta.url)).replaceAll("\\", "/"),
      "@app/": fileURLToPath(new URL("./application/", import.meta.url)).replaceAll("\\", "/"),
      "@adapters/": fileURLToPath(new URL("./adapters/", import.meta.url)).replaceAll("\\", "/"),
    },
  },
  server: {
    fs: { allow: [fileURLToPath(new URL("../..", import.meta.url)).replaceAll("\\", "/")] },
  },
  test: {
    environment: "node",
    reporters: ["default"],
    projects: [
      {
        extends: true as const,
        test: { name: "phase0_preflight", include: [ARCHITECTURE] },
      },
      {
        extends: true as const,
        test: { name: "phase1_kb_contracts", include: [KB_PARITY] },
      },
      {
        extends: true as const,
        test: {
          name: "phase7_warband",
          include: [`${TEST_ROOT}**/*.test.ts`],
          exclude: [ARCHITECTURE, KB_PARITY],
        },
      },
    ],
  },
});
