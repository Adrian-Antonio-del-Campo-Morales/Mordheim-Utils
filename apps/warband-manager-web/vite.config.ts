import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

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
  // The suite lives in the repository's tests/web tree (support code stays out
  // of the app), so the include patterns are absolute, the setup file lives
  // beside it and the repository root is served.
  server: {
    fs: { allow: [fileURLToPath(new URL("../..", import.meta.url)).replaceAll("\\", "/")] },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [fileURLToPath(new URL("../../tests/web/setup.ts", import.meta.url))],
    include: [fileURLToPath(new URL("../../tests/web/**/*.test.{ts,tsx}", import.meta.url)).replaceAll("\\", "/")],
  },
}));
