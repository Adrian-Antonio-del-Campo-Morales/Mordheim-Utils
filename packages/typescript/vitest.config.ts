import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Domain/application packages must run in plain Node — no DOM.
// The suite lives in the repository's tests tree (support code stays out of the
// packages); the aliases are the same vocabulary the web app uses.
// Dependencies resolve through the npm workspace root.
//
// Grouping uses the runner's native project mechanism: one project per suite
// family, each with an include/exclude over the maintained test tree. Test
// identities, suite names and parametrizations are unchanged, so a group is
// selected with `--project <name>` and the default run still covers everything.
const REPO_ROOT = fileURLToPath(
  new URL("../../tests/", import.meta.url),
).replaceAll("\\", "/");

const ARCHITECTURE = `${REPO_ROOT}tooling/architecture/purity.test.ts`;
const KB_PARITY = `${REPO_ROOT}knowledge/parity-kb-vectors.test.ts`;
const DOMAIN = `${REPO_ROOT}applications/warband_manager/domain/**/*.test.ts`;
const APPLICATION = `${REPO_ROOT}applications/warband_manager/application/**/*.test.ts`;
const ADAPTERS = `${REPO_ROOT}applications/warband_manager/adapters/**/*.test.ts`;
const PARITY = `${REPO_ROOT}applications/warband_manager/parity-vectors.test.ts`;

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
        test: { name: "architecture", include: [ARCHITECTURE] },
      },
      {
        extends: true as const,
        test: { name: "knowledge-parity", include: [KB_PARITY] },
      },
      {
        extends: true as const,
        test: {
          name: "typescript",
          include: [DOMAIN, APPLICATION, ADAPTERS, PARITY],
        },
      },
    ],
  },
});
