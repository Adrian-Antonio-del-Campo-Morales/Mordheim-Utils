import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Domain/application packages must run in plain Node — no DOM.
// The suite lives in the repository's tests/typescript tree (support code stays
// out of the packages); the aliases are the same vocabulary the web app uses.
// Dependencies resolve through the npm workspace root.
//
// Selection is expressed through homogeneous Vitest suites grouped under the test
// contract root, not through a parallel catalog or source-text classifier. Each
// directory becomes one group the coordinator can select by component; the primary
// category stays with each test's assertions, not with this grouping.
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
    include: [
      fileURLToPath(new URL("../../tests/typescript/**/*.test.ts", import.meta.url)).replaceAll("\\", "/"),
    ],
    reporters: ["default"],
  },
});
