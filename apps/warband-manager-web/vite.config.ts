import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Category selection uses Vitest's native projects: one project per phase
// category over the maintained test tree. Test identities, names and
// parametrizations are unchanged; `--project <name>` selects a category and
// the default run still executes every project. Vitest 3.2 has no per-test
// tag, so the category is resolved per file: general architecture keeps the
// preflight category, and the built-bundle/font guards (which skip without a
// build) form the packaging category.
const REPO_TESTS = fileURLToPath(new URL("../../tests/", import.meta.url)).replaceAll("\\", "/");
const APPLICATIONS = `${REPO_TESTS}applications/warband_manager/`;
const WEB_APPLICATIONS = [
  `${APPLICATIONS}features/**/*.test.{ts,tsx}`,
  `${APPLICATIONS}presentation/**/*.test.{ts,tsx}`,
];
const TOOLING = `${REPO_TESTS}tooling/web/`;
const BOUNDARIES = `${REPO_TESTS}tooling/architecture/web-boundaries.test.ts`;
const FONT = `${APPLICATIONS}packaging/font-publication.test.ts`;
const BUNDLE = `${APPLICATIONS}packaging/bundle-boundaries.test.ts`;

// React + Vite shell.
// The GITHUB_PAGES switch makes CI publish under the repository sub-path.
export default defineConfig(() => ({
  base: process.env.GITHUB_PAGES ? "/Mordheim-Utils/" : "/",
  // Generated browser assets are kept outside source and test fixtures.
  publicDir: fileURLToPath(new URL("../../outputs/web-public", import.meta.url)),
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^@src$/, replacement: fileURLToPath(new URL("./src/index.ts", import.meta.url)) },
      { find: "@src/", replacement: fileURLToPath(new URL("./src/", import.meta.url)).replaceAll("\\", "/") },
      { find: /^@domain$/, replacement: fileURLToPath(new URL("../../packages/typescript/domain/campaign/index.ts", import.meta.url)) },
      { find: "@domain/", replacement: fileURLToPath(new URL("../../packages/typescript/domain/", import.meta.url)).replaceAll("\\", "/") },
      { find: /^@app$/, replacement: fileURLToPath(new URL("../../packages/typescript/application/campaign/index.ts", import.meta.url)) },
      { find: "@app/", replacement: fileURLToPath(new URL("../../packages/typescript/application/", import.meta.url)).replaceAll("\\", "/") },
      { find: "@adapters/", replacement: fileURLToPath(new URL("../../packages/typescript/adapters/", import.meta.url)).replaceAll("\\", "/") },
    ],
  },
  // The suites live in the repository's tests tree (support code stays out of
  // the app), so the include patterns are absolute, the setup file lives under
  // the application tests and the repository root is served.
  server: {
    fs: { allow: [fileURLToPath(new URL("../..", import.meta.url)).replaceAll("\\", "/")] },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [fileURLToPath(new URL("../../tests/applications/warband_manager/support/setup.ts", import.meta.url))],
    reporters: ["default"],
    projects: [
      {
        extends: true as const,
        test: { name: "phase0_preflight", include: [BOUNDARIES] },
      },
      {
        extends: true as const,
        test: { name: "packaging", include: [FONT, BUNDLE] },
      },
      {
        extends: true as const,
        test: {
          name: "phase7_warband",
          include: [...WEB_APPLICATIONS, `${TOOLING}**/*.test.{ts,tsx}`],
          exclude: [BOUNDARIES, FONT, BUNDLE],
        },
      },
    ],
  },
}));
