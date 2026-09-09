import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// P3.1 (web-migration-parallel-plan.md): minimal React + Vite shell.
// The GITHUB_PAGES switch lets CI (task P8.1, sole owner of workflows) publish
// under the repository sub-path without touching this file again.
export default defineConfig(() => ({
  base: process.env.GITHUB_PAGES ? "/Mordheim-Utils/" : "/",
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^@domain$/, replacement: fileURLToPath(new URL("../../packages/typescript/domain/campaign/index.ts", import.meta.url)) },
      { find: "@domain/", replacement: fileURLToPath(new URL("../../packages/typescript/domain/", import.meta.url)).replaceAll("\\", "/") },
      { find: /^@app$/, replacement: fileURLToPath(new URL("../../packages/typescript/application/campaign/index.ts", import.meta.url)) },
      { find: "@app/", replacement: fileURLToPath(new URL("../../packages/typescript/application/", import.meta.url)).replaceAll("\\", "/") },
      { find: "@adapters/", replacement: fileURLToPath(new URL("../../packages/typescript/adapters/", import.meta.url)).replaceAll("\\", "/") },
    ],
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["src/test-setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
}));
