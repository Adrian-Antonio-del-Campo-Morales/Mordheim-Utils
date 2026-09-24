/**
 * P5.2 acceptance — test-environment setup.
 *
 * The production shell upgrades to the real KB reader by fetching
 * `knowledge/knowledge-web.json`. jsdom has no serving layer, so every test
 * environment stubs `fetch` to reject cleanly: the upgrade path fails, the
 * hook falls back to the fake-composed service, and the app renders with
 * built-in sample data (this degradation is itself the tested behaviour).
 * Tests that exercise the upgrade explicitly stub a responding artefact via
 * `vi.stubGlobal("fetch", …)` / `unstubAllGlobals()`.
 */
import { afterEach, expect, vi } from "vitest";

afterEach(() => {
  expect(document.body.textContent, "La interfaz no debe mostrar identificadores técnicos").not.toMatch(/\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b/i);
  vi.unstubAllGlobals();
});

vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("Failed to parse URL from knowledge/knowledge-web.json"))));
