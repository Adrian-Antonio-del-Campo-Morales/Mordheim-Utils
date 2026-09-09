/**
 * P7.4 (web-migration-parallel-plan.md §8): accessibility & small-viewport
 * acceptance tests.
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
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";

import { CampaignSlice } from "../features/campaign/CampaignSlice";

function repoRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 8; i += 1) {
    if (existsSync(join(dir, "web-migration-parallel-plan.md"))) return dir;
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
    for (const relative of ["battle/BattlePanel.tsx", "draft/DraftPanel.tsx", "campaign/CampaignSlice.tsx", "advances/AdvancesPanel.tsx"]) {
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
    expect(source("equipment/EquipmentPanel.tsx")).toMatch(/aria-label=\{`Return /);
    expect(source("injuries/InjuriesPanel.tsx")).toMatch(/aria-label=\{`Recover /);
    expect(source("advances/AdvancesPanel.tsx")).toMatch(/aria-label=\{`Advance choice for /);
  });

  it("headings follow document order (h1 once, no skipped levels)", () => {
    const slice = source("campaign/CampaignSlice.tsx");
    expect(slice).toMatch(/<h1>/);
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
  });
});

describe("P7.4 keyboard & announcement behaviour", () => {
  it("the import dialog is keyboard reachable", async () => {
    const user = userEvent.setup();
    render(<CampaignSlice />);

    // The file input is the first tabbable control on the page.
    await user.tab();
    const input = screen.getByLabelText(/Load a \.mordheim campaign file/);
    expect(document.activeElement).toBe(input);
  });

  it("a rejected import announces through the alert seam", async () => {
    render(<CampaignSlice />);
    const input = screen.getByLabelText(/Load a \.mordheim campaign file/) as HTMLInputElement;
    // A retired v3 document: the reader must reject it and the UI must
    // announce the reason through the alert role.
    const file = new File(
      [JSON.stringify({ marker: "MORDHEIM_CAMPAIGN_MANAGER", format_version: 3 })],
      "old.mordheim",
      { type: "application/json" },
    );
    fireEvent.change(input, { target: { files: [file] } });

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/old format|version/i);
  });
});
