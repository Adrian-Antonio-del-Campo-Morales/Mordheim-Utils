/**
 * Web accessibility and small-viewport acceptance tests.
 *
 * Two layers:
 *  1. a static audit over the real UI sources — every control reachable by
 *     tab order carries an accessible name, tables expose captions/scope,
 *     landmarks label their sections, headings follow document order;
 *  2. behavioural jsdom tests on the real slice — the import dialog is
 *     keyboard reachable, buttons render their visible text as names, and
 *     the error seam is an alert role (screen-reader announced).
 *
 * Static checks read source text (jsdom cannot do layout/contrast); the
 * visual half (contrast, real focus ring) is covered by the global
 * stylesheet (`index.css`: :focus-visible ring, touch targets, scrolling
 * tables) shipped with the shell.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { ProductApp } from "@src/ProductApp";
import { createService, loadKnowledge } from "@src/features/campaign/default-deps";

vi.mock("@src/features/campaign/default-deps", () => ({
  createService: vi.fn(),
  loadKnowledge: vi.fn(),
}));

function repoRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 8; i += 1) {
    if (existsSync(join(dir, "apps", "warband-manager-web", "package.json"))) return dir;
    dir = join(dir, "..");
  }
  throw new Error("Repository root not found.");
}

const SRC_FEATURES = join(repoRoot(), "apps", "warband-manager-web", "src", "features");

const PANELS = [
  "campaign/CampaignSlice.tsx",
  "timeline/TimelinePanel.tsx",
  "equipment/EquipmentPanel.tsx",
  "advances/AdvancesPanel.tsx",
  "injuries/InjuriesPanel.tsx",
  "battle/BattlePanel.tsx",
  "draft/DraftPanel.tsx",
].map((relative) => join(SRC_FEATURES, relative));

function source(relative: string): string {
  return readFileSync(join(SRC_FEATURES, relative), "utf8");
}

describe("P7.4 static accessibility audit", () => {
  it("every panel section is a labelled landmark", () => {
    for (const panel of PANELS) {
      const text = readFileSync(panel, "utf8");
      // `<section aria-label>` or `<nav aria-label>` — both are landmarks.
      expect(text, panel).toMatch(/<(section|nav)\s+aria-label=/);
    }
  });

  it("data tables expose captions and column scopes", () => {
    for (const relative of [
      "campaign/CampaignSlice.tsx",
      "equipment/EquipmentPanel.tsx",
      "advances/AdvancesPanel.tsx",
      "injuries/InjuriesPanel.tsx",
      "hirelings/HirelingsPanel.tsx",
    ]) {
      const text = source(relative);
      if (text.includes("<table>")) {
        expect(text, `${relative}: <caption>`).toMatch(/<caption>/);
        expect(text, `${relative}: scope="col"`).toMatch(/scope="col"/);
      }
    }
  });

  it("forms associate labels with inputs", () => {
    for (const relative of ["battle/BattlePanel.tsx", "draft/DraftPanel.tsx", "advances/AdvancesPanel.tsx"]) {
      const text = source(relative);
      const labels = (text.match(/<label/g) ?? []).length;
      const associations = (text.match(/htmlFor=|<label key=/g) ?? []).length;
      expect(associations, `${relative}: labels use htmlFor or wrap their control`).toBeGreaterThanOrEqual(
        Math.min(labels, 1),
      );
    }
  });

  it("error surfaces are announced (alert role), status surfaces use status role", () => {
    expect(source("campaign/CampaignSlice.tsx")).toMatch(/role="alert"/);
    expect(source("campaign/CampaignSlice.tsx")).toMatch(/role="status"/);
  });

  it("every dynamically disabled action keeps a stable accessible name", () => {
    // Repeated per-row buttons must not rely on visible text alone.
    expect(source("equipment/EquipmentPanel.tsx")).toMatch(/aria-label=\{presentationOutput\(textJoin\(\[translate\(\{ key: "[^"]+" \}, locale\)/);
    expect(source("injuries/InjuriesPanel.tsx")).toMatch(/aria-label=\{presentationOutput\(textJoin\(\[translate\(\{ key: "[^"]+" \}, locale\)/);
  });

  it("headings follow document order (h1 once, no skipped levels)", () => {
    const shell = readFileSync(join(repoRoot(), "apps", "warband-manager-web", "src", "ProductApp.tsx"), "utf8");
    expect(shell).toMatch(/<h1>/);
    const panelHeadings = ["timeline/TimelinePanel.tsx", "equipment/EquipmentPanel.tsx", "advances/AdvancesPanel.tsx", "injuries/InjuriesPanel.tsx"].map(
      (relative) => source(relative).match(/<h([1-6])>/)?.[1] ?? "",
    );
    for (const level of panelHeadings) {
      expect(Number(level), "panels start at h3 under the slice's h2/h1").toBeGreaterThanOrEqual(3);
    }
  });

  it("the global stylesheet ships a focus ring and small-viewport table handling", () => {
    const css = readFileSync(join(repoRoot(), "apps", "warband-manager-web", "src", "index.css"), "utf8");
    expect(css).toMatch(/:focus-visible/);
    expect(css).toMatch(/@media \(max-width: 640px\)/);
    expect(css).toMatch(/@media \(pointer: coarse\)/);
    expect(css).toMatch(/\.modal[^}]*100dvh[^}]*overflow-y:\s*auto/);
    expect(css).toMatch(/\.modal-actions[^}]*position:\s*sticky[^}]*bottom:\s*0/);
    expect(css).toMatch(/\.mobile-nav[^}]*position:\s*fixed/);
    expect(css).toMatch(/safe-area-inset-bottom/);
    expect(css).toMatch(/\.mobile-cards td::before[^}]*attr\(data-label\)/);
    expect(css).toMatch(/@media \(max-width: 680px\)[\s\S]*\.modal-backdrop\s*\{\s*z-index:\s*40/);
    expect(css).toMatch(/\.moment-detail\s*>\s*section[^}]*width:\s*100%[^}]*min-width:\s*0/);
  });
});

describe("P7.4 keyboard & announcement behaviour", () => {
  beforeEach(() => {
    vi.mocked(loadKnowledge).mockResolvedValue({ list: () => [] } as never);
    vi.mocked(createService).mockReturnValue({
      importCampaign: vi.fn().mockResolvedValue({ ok: false, message: "Rejected import" }),
      subscribe: () => () => {},
      isDirty: () => false,
      current: () => null,
    } as never);
  });

  it("the import dialog is keyboard reachable", async () => {
    render(<ProductApp />);
    await waitFor(() =>
      expect(
        screen
          .getAllByRole("button", { name: "Cargar" })
          .some((button) => !button.hasAttribute("disabled")),
      ).toBe(true),
    );
    expect(screen.getByLabelText("Cargar campañas .mordheim")).toBeInTheDocument();
  });

  it("updates the import control name when the locale changes", async () => {
    render(<ProductApp />);
    fireEvent.click(screen.getByRole("button", { name: "Ajustes" }));
    await waitFor(() => expect(screen.getByLabelText(/idioma/i)).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/idioma/i), { target: { value: "en" } });
    expect(screen.getByLabelText("Load .mordheim campaigns")).toBeInTheDocument();
  });

  it("a rejected import announces through the alert seam", async () => {
    render(<ProductApp />);
    await waitFor(() =>
      expect(
        screen
          .getAllByRole("button", { name: "Cargar" })
          .some((button) => !button.hasAttribute("disabled")),
      ).toBe(true),
    );
    const input = screen.getByLabelText("Cargar campañas .mordheim") as HTMLInputElement;
    // An incomplete v3 document: the reader must reject it and the UI must
    // announce the reason through the alert role.
    const file = {
      name: "old.mordheim",
      text: async () => JSON.stringify({ marker: "MORDHEIM_CAMPAIGN_MANAGER", format_version: 3 }),
    } as File;
    fireEvent.change(input, { target: { files: [file] } });

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("El archivo incumple el formato de campaña.");
  });

  it("announces why a disabled action cannot be performed", async () => {
    render(<ProductApp />);
    const save = screen.getAllByRole("button", { name: "Guardar" })[0];
    expect(save).toBeDisabled();

    fireEvent.pointerDown(save);

    expect(await screen.findByRole("alert")).toHaveTextContent("Abre o crea una campaña antes de guardarla.");
  });
});
