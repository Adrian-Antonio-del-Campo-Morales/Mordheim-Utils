/**
 * D6 regression guard: the configured web font must actually be published.
 *
 * The shell declares a single `@font-face` ("Mordheim Sans") in `src/index.css`.
 * It used to point at the root-absolute public URL `/fonts/NotoSans.ttf`, but
 * the app overrides `publicDir` to the generated `outputs/web-public/`, so Vite
 * never published that path: the browser downloaded the SPA fallback HTML and
 * logged an OTS parsing warning while the text silently fell back to a system
 * font.
 *
 * The font now travels through Vite's asset pipeline as a relative `url()`,
 * which emits the real binary into the build and rebases the reference with the
 * configured `base`. These checks read the source CSS and, when a build exists,
 * the emitted `dist/` output, so a regression to a root-absolute URL (or a
 * dropped asset) fails here instead of in the browser console.
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

/** Walk up from cwd to the repository root. */
function repoRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 8; i += 1) {
    if (existsSync(join(dir, "apps", "warband-manager-web", "package.json"))) return dir;
    dir = join(dir, "..");
  }
  throw new Error("Repository root not found.");
}

const ROOT = repoRoot();
const APP = join(ROOT, "apps", "warband-manager-web");
const INDEX_CSS = join(APP, "src", "index.css");
const DIST = join(APP, "dist");

/** sfnt / WOFF magic numbers a real webfont may start with. */
const FONT_SIGNATURES = ["00010000", "4f54544f", "74727565", "74746366", "774f4646", "774f4632"];

/** The `url(...)` targets of every `@font-face` block (minified or not). */
function fontFaceUrls(css: string): string[] {
  const urls: string[] = [];
  for (const block of css.matchAll(/@font-face\s*\{[^}]*\}/g)) {
    for (const match of block[0].matchAll(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g)) {
      urls.push(match[2]);
    }
  }
  return urls;
}

/** Assert a path holds a real font binary, not the SPA fallback or an error page. */
function expectPublishedFont(path: string): void {
  expect(existsSync(path), `${path} exists`).toBe(true);
  const bytes = readFileSync(path);
  expect(bytes.length, `${path} has more than a stub`).toBeGreaterThan(1024);
  // HTML (the fallback the browser used to receive) starts with "<".
  expect(bytes.subarray(0, 1).toString("latin1"), `${path} is not HTML`).not.toBe("<");
  expect(FONT_SIGNATURES, `${path} has a font signature`).toContain(bytes.subarray(0, 4).toString("hex"));
}

describe("web font publication", () => {
  it("declares the app font through a relative asset URL Vite can rebase", () => {
    const css = readFileSync(INDEX_CSS, "utf8");
    expect(css).toContain('font-family: "Mordheim Sans"');
    const urls = fontFaceUrls(css);
    expect(urls.length, "the shell declares at least one @font-face source").toBeGreaterThan(0);
    for (const url of urls) {
      // Root-absolute or remote URLs bypass the bundler: exactly the D6
      // regression, where nothing publishes the referenced path.
      expect(url.startsWith("/"), `${url} is not root-absolute`).toBe(false);
      expect(/^[a-z][a-z0-9+.-]*:/i.test(url), `${url} is not a remote URL`).toBe(false);
      expectPublishedFont(resolve(dirname(INDEX_CSS), url));
    }
  });

  const assetsDir = join(DIST, "assets");
  const hasBuild = existsSync(assetsDir);

  it.skipIf(!hasBuild)("publishes the font in the build and honours the configured base", () => {
    const html = readFileSync(join(DIST, "index.html"), "utf8");
    const entry = html.match(/(?:src|href)="([^"]+\.(?:js|css))"/)?.[1] ?? "";
    const base = entry.slice(0, entry.indexOf("assets/"));
    expect(base, "the entry chunk reveals the configured base").toBeTruthy();

    const cssFiles = readdirSync(assetsDir).filter((name) => name.endsWith(".css"));
    expect(cssFiles.length, "the build emits a stylesheet").toBeGreaterThan(0);

    const sourceFonts = fontFaceUrls(readFileSync(INDEX_CSS, "utf8")).map((url) => readFileSync(resolve(dirname(INDEX_CSS), url)));

    const published: string[] = [];
    for (const name of cssFiles) {
      const text = readFileSync(join(assetsDir, name), "utf8");
      // The stale public path must not survive anywhere in the output.
      expect(text, `${name} keeps no stale /fonts/ reference`).not.toContain("/fonts/");
      published.push(...fontFaceUrls(text));
    }
    expect(published.length, "the built stylesheet keeps the @font-face").toBeGreaterThan(0);

    for (const url of published) {
      expect(url.startsWith(base), `${url} is served under the configured base ${base}`).toBe(true);
      const emittedPath = resolve(DIST, url.slice(base.length));
      expectPublishedFont(emittedPath);
      // The build ships the maintained source font, byte for byte — no
      // duplicated or regenerated binary.
      const emitted = readFileSync(emittedPath);
      expect(sourceFonts.some((source) => source.equals(emitted)), "the build ships the maintained source font").toBe(true);
    }
  });
});
