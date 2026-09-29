/**
 * Node-side loader for the generated KB artefacts, for the completeness tools.
 *
 * This is NOT a second artefact reader: it reuses the maintained helper
 * `tests/support/kb-artefact.ts` (`readArtefactDocument`, which merges the
 * initial document + rules prose + display text + catalogue fragments) by
 * loading it through `node:module`'s `registerHooks`. The hooks transpile the
 * helper's TypeScript dependency graph with `ts.transpileModule`, so this tool
 * needs no build step and cannot drift from the suites that use the same
 * helper; `@adapters/knowledge-reader/index` resolves to the real package
 * files and `fs`/`path` resolve to the real node builtins, so the helper's
 * digest-addressed fragment merging behaves exactly as in the vitest tests.
 */
import { existsSync, readFileSync } from "node:fs";
import { registerHooks } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import ts from "typescript";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");

// The vite aliases (apps/warband-manager-web/vite.config.ts), mirrored so the
// transpiled TS graph resolves identically outside vitest.
const ALIASES = ["@adapters/", "@app/", "@domain/"];

const hooks = {
  resolve(specifier, context, nextResolve) {
    const alias = ALIASES.find((prefix) => specifier.startsWith(prefix));
    if (alias) {
      const rest = specifier.slice(alias.length);
      const base = { "@adapters/": "packages/typescript/adapters/", "@app/": "packages/typescript/application/", "@domain/": "packages/typescript/domain/" }[alias];
      return {
        url: pathToFileURL(resolve(REPO_ROOT, base, rest) + (rest.split("/").pop()?.includes(".") ? "" : ".ts")).href,
        format: "module-typescript",
        shortCircuit: true,
      };
    }
    // The TS sources import their own relatives without an extension.
    if ((specifier.startsWith("./") || specifier.startsWith("../")) && !/\.[cm]?js(?:\?.*)?$/.test(specifier)) {
      return nextResolve(`${specifier}.ts`, context);
    }
    return nextResolve(specifier, context);
  },
  load(url, context, nextLoad) {
    const clean = url.split("?")[0];
    if (clean.endsWith(".ts")) {
      const name = fileURLToPath(clean);
      const { outputText } = ts.transpileModule(readFileSync(name, "utf8"), {
        compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, verbatimModuleSyntax: false },
        fileName: name,
      });
      return { format: "module", source: outputText, shortCircuit: true };
    }
    return nextLoad(url, context);
  },
};

let hooksInstalled = false;
function ensureHooks() {
  if (!hooksInstalled) {
    registerHooks(hooks);
    hooksInstalled = true;
  }
}

/**
 * Merged artefact (`knowledge-web.json` + `rules-prose.json` + `display-text.json`
 * + `knowledge-catalogue.json`), or `null` when the generated output is absent.
 */
export async function readPublishedArtefact() {
  ensureHooks();
  const path = resolve(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json");
  if (!existsSync(path)) return null;
  const helper = await import(pathToFileURL(resolve(REPO_ROOT, "tests", "support", "kb-artefact.ts")).href);
  return helper.readArtefactDocument(path);
}

let cache;
/** Memoized merged artefact for one tool process. */
export async function publishedArtefact() {
  return (cache ??= await readPublishedArtefact());
}
