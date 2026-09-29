/**
 * Dynamic visible-completeness sweeps — the rendered half of completeness
 * step 5 of `check-presentation`.
 *
 * Everything here runs against the REAL generated artefacts via the maintained
 * loader (`tests/support/kb-artefact.ts`) and the REAL consumers: the product
 * shell (ProductApp) with the real reader, the real v5 import path for the
 * contract fixtures, and the real PDF writer's drawText calls (its pre-write
 * text model). What is visible is captured per surface — textContent, title,
 * alt, placeholder, aria-label, aria-description, data-tooltip,
 * data-disabled-reason, visible input values, export text — and classified with
 * the shared detector (`tools/web/presentation-completeness-detector.mjs`).
 *
 * Never captured as visible text: `value` of option/select/hidden/checkbox/radio
 * identity controls, React keys, structural attributes (id, name, class, role,
 * href…) and ids used purely as internal identity.
 *
 * Policy: for published data and supported formats, every visible text must
 * resolve to real localized content; a generic fallback is a defect, and the
 * product's specific localized absence notices are not. Findings travel as
 * `PRESENTATION_COMPLETENESS_FINDING {json}` lines to the audit tool; the
 * sweep writes its own results file for the tool's summary. Unsupported
 * formats must be rejected by the specific error before render — asserted
 * below, never rendered.
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterAll, afterEach, describe, expect, it, vi } from "vitest";
import { PDFPage } from "pdf-lib";

import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { CampaignSlice } from "@src/features/campaign/CampaignSlice";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { ProductApp } from "@src/ProductApp";
import { createService, loadKnowledge } from "@src/features/campaign/default-deps";
import { createWarbandPdf } from "@src/features/export/warband-pdf";
import { classifyVisibleText, buildIdInventory } from "../../../tools/web/presentation-completeness-detector.mjs";
import { readArtefactDocument } from "../../support/kb-artefact";

vi.mock("@src/features/campaign/default-deps", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@src/features/campaign/default-deps")>()),
  loadKnowledge: vi.fn(),
}));

/**
 * Measured per-test budget for the two rules-page sweeps.
 *
 * Each one renders the real `ProductApp`, walks nine category tabs and
 * classifies what is visible: ~2.1 s on its own, so the 5 s default left no
 * margin and they timed out under a parallel full-suite run. 20 s is ~10x the
 * measured isolated cost and ~4x the default — enough for scheduler contention
 * without touching the global timeout or dropping any coverage.
 */
const SWEEP_TIMEOUT_MS = 20_000;

const PUBLISHED = resolve(process.cwd(), "..", "..", "outputs", "web-public", "knowledge", "knowledge-web.json");
const OUTPUT = process.env.PRESENTATION_COMPLETENESS_OUTPUT
  ?? resolve(process.cwd(), "..", "..", "outputs", "web-presentation", "gui-text-completeness-sweep.json");

const results: { title: string; status: "passed" | "failed"; message?: string }[] = [];

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

afterAll(() => {
  mkdirSync(resolve(OUTPUT, ".."), { recursive: true });
  writeFileSync(OUTPUT, JSON.stringify({ tests: results }, null, 2) + "\n");
});

/** One finding line per unique problem; the audit deduplicates itself too. */
const emitted = new Set<string>();
function emit(finding: Record<string, unknown>): void {
  const payload = JSON.stringify(finding);
  if (emitted.has(payload)) return;
  emitted.add(payload);
  console.log(`PRESENTATION_COMPLETENESS_FINDING ${payload}`);
}

const artefact = readArtefactDocument(PUBLISHED);
const knowledge = ArtefactKnowledgeReader.from(artefact);
const inventory = buildIdInventory(artefact);
const adapter = new CampaignFileV5Adapter();
vi.mocked(loadKnowledge).mockResolvedValue(knowledge as never);

/** Visible values of a rendered container (structural attributes excluded). */
function capture(container: HTMLElement): string[] {
  const values: string[] = [];
  if (container.textContent) values.push(container.textContent);
  for (const element of container.querySelectorAll<HTMLElement>("*")) {
    for (const attribute of ["title", "alt", "placeholder", "aria-label", "aria-description", "data-tooltip", "data-disabled-reason", "data-title"]) {
      const value = element.getAttribute(attribute);
      if (value) values.push(value);
    }
    const tag = element.tagName.toLowerCase();
    const type = (element as HTMLInputElement).type?.toLowerCase();
    const identityOnly = tag === "option" || tag === "select" || (tag === "input" && ["hidden", "checkbox", "radio"].includes(type ?? ""));
    const value_ = (element as HTMLInputElement).value;
    if (!identityOnly && typeof value_ === "string" && value_.trim()) values.push(value_);
  }
  return values;
}

/**
 * Classify captured values.
 *
 * A captured value is often a composed text (the whole page, a scenario effect,
 * a table cell): the detector inspects its fragments, so a fallback joined to a
 * label, a bullet, a die result or a chip is reported as the fragment that
 * carries it and can no longer hide inside the surrounding prose. The product's
 * specific localized absence notices are not fallbacks and are not flagged.
 */
function classifyAll(values: readonly string[], context: Record<string, unknown>): void {
  for (const value of values) {
    const finding = classifyVisibleText(value, context);
    if (finding) emit(finding);
  }
}

/**
 * The award bullet lines of one composed scenario effect.
 *
 * `RulesCatalogue` joins the scenario parts with a blank line, so the experience
 * list is the run of `• ` blocks that follows its own `Experience:` heading.
 */
const EXPERIENCE_HEADINGS = { es: "Experiencia:", en: "Experience:" } as const;
function awardLines(effect: string, locale: "es" | "en"): string[] {
  const blocks = String(effect).split("\n\n");
  const start = blocks.findIndex((block) => block.trim() === EXPERIENCE_HEADINGS[locale]);
  if (start < 0) return [];
  const lines: string[] = [];
  for (const block of blocks.slice(start + 1)) {
    const line = block.trim();
    if (!line.startsWith("•")) break;
    lines.push(line.replace(/^•\s*/, "").trim());
  }
  return lines;
}

/** The real v5 import path for a contract fixture. */
function importFixture(name: string) {
  const raw = JSON.parse(readFileSync(resolve(process.cwd(), "..", "..", "contracts", "campaign-file-v5", "fixtures", `${name}.json`), "utf8"));
  return adapter.parseCampaignFile(JSON.stringify(raw));
}

/** Import a fixture through the real v5 file adapter (the product's import path). */
async function loadService(fixture: string): Promise<ReturnType<typeof createService>> {
  const parsed = importFixture(fixture);
  expect(parsed.ok, parsed.ok ? "" : parsed.message).toBe(true);
  if (!parsed.ok) throw new Error(parsed.message);
  const service = createService(knowledge);
  const imported = await service.importCampaign({ text: JSON.stringify(parsed.document), confirm_replace: true });
  expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);
  if (!imported.ok) throw new Error(imported.message);
  return service;
}

describe("dynamic visible-completeness sweeps (real artefacts, real consumers)", () => {
  /** Record each test in the results file the audit summarizes. */
  const tracked = async (title: string, run: () => Promise<void>) => {
    try {
      await run();
      results.push({ title, status: "passed" });
    } catch (error) {
      results.push({ title, status: "failed", message: String((error as Error).message ?? error).slice(0, 800) });
      throw error;
    }
  };

  for (const locale of ["es", "en"] as const) {
    it(`band selector and creation stay complete in ${locale}`, () => tracked(`band selector and creation ${locale}`, async () => {
      const user = userEvent.setup();
      const view = render(<ProductApp />);
      try {
        await view.findAllByRole("button", { name: "Nueva Campaña" });
        const createButtons = view.getAllByRole("button", { name: "Nueva Campaña" });
        await user.click(createButtons[0]);
        await view.findByRole("dialog");
        classifyAll(capture(view.container), { locale, surface: `create-modal/${locale}`, idInventory: inventory });
        // Library dialog too.
        await user.click(view.getByRole("button", { name: "Cerrar" }));
        await user.click(view.getByRole("button", { name: "Campañas" }));
        await view.findByRole("dialog");
        classifyAll(capture(view.container), { locale, surface: `library/${locale}`, idInventory: inventory });
      } finally {
        view.unmount();
      }
    }));

    it(`rules page and all categories stay complete in ${locale}`, () => tracked(`rules page ${locale}`, async () => {
      const user = userEvent.setup();
      const view = render(<ProductApp />);
      try {
        await user.click(await view.findByRole("button", { name: "Reglas" }));
        await view.findByRole("textbox", { name: "Buscar Reglas" });
        const tabs = [...view.container.querySelectorAll<HTMLElement>(".rules-toolbar .tabs button")];
        for (const [index, tab] of tabs.entries()) {
          await user.click(tab);
          const categoryId = ["special-rules", "band-rules", "conditions", "core-rules", "skills", "equipment", "spells", "scenarios", "injuries"][index] ?? `tab-${index}`;
          classifyAll(capture(view.container), { locale, surface: `rules-page/${categoryId}`, category: categoryId, idInventory: inventory });
        }
        const search = view.container.querySelector<HTMLInputElement>(".rules-toolbar input");
        if (search) {
          await user.type(search, "a");
          classifyAll(capture(view.container), { locale, surface: `rules-page/search/${locale}`, idInventory: inventory });
        }
      } finally {
        view.unmount();
      }
    }), SWEEP_TIMEOUT_MS);
  }

  /**
   * The scenario experience list composes the canonical awards every scenario
   * references (`campaign.experience-and-advances.awards.*`). Those awards
   * publish no prose at all — only recipient, trigger, amount and their source
   * references — so the composition must name the specific absence, never the
   * generic notice. The composed effect is one visible string, so the generic
   * notice used to hide inside it, out of reach of the classifier; this sweep
   * classifies the award lines themselves, in both locales, and pins the
   * coverage so a silently dropped award list fails here too.
   */
  it("scenario experience awards resolve to real prose or the specific absence", () => tracked("scenario experience awards", async () => {
    const scenarioRows = (((artefact.campaign as Record<string, unknown> | undefined)?.scenarios as Record<string, unknown> | undefined)?.scenarios as readonly Record<string, unknown>[] | undefined) ?? [];
    const declared = scenarioRows.reduce((total, scenario) => {
      const experience = (scenario.progression as Record<string, unknown> | undefined)?.experience;
      return total + (Array.isArray(experience) ? experience.length : 0);
    }, 0);
    const catalogue = new RulesCatalogue(knowledge);
    let inspected = 0;
    for (const locale of ["es", "en"] as const) {
      for (const entry of catalogue.entries("scenarios", locale)) {
        for (const line of awardLines(String(entry.effect), locale)) {
          inspected += 1;
          const finding = classifyVisibleText(line, { locale, surface: "rules-catalogue/scenarios", category: "scenarios", field: "effect", ref: { kind: "scenario", id: entry.entry_id }, idInventory: inventory });
          if (finding) emit(finding);
          expect(finding, `${entry.entry_id} award line (${locale}) -> "${line}"`).toBeNull();
        }
      }
    }
    expect(declared, "the published scenarios declare experience awards").toBeGreaterThan(0);
    expect(inspected, "every declared award of every scenario is inspected in both locales").toBe(declared * 2);
  }));

  // Loaded campaigns through the product's real file import: the four v5
  // contract fixtures are the current (and only supported) format. Old
  // versions are rejected by the specific retired-version error before any
  // render — asserted separately below, never rendered.
  for (const fixture of ["draft", "active-campaign", "full-inventory", "pending-post-battle"]) {
    it(`loaded campaign ${fixture} stays complete`, () => tracked(`loaded campaign ${fixture}`, async () => {
      const user = userEvent.setup();
      const service = await loadService(fixture);
      const view = render(
        <CampaignAppProvider service={service} locale="es">
          <CampaignSlice knowledge={knowledge} locale="es" />
        </CampaignAppProvider>,
      );
      try {
        // The loaded campaign surfaces: workspace sections + timeline/history.
        await view.findByRole("navigation", { name: "Cronología" });
        const sections: [string, string][] = [["BANDA ACTUAL", "overview"], ["Guerreros", "warriors"], ["INVENTARIO", "inventory"]];
        for (const [label, key] of sections) {
          const tab = [...view.container.querySelectorAll<HTMLElement>(".segmented-tabs button")].find((candidate) => candidate.textContent?.trim() === label);
          if (tab) {
            await user.click(tab);
            classifyAll(capture(view.container), { locale: "es", surface: `campaign/${fixture}/${key}`, idInventory: inventory });
          }
        }
        classifyAll(capture(view.container), { locale: "es", surface: `campaign/${fixture}/timeline`, idInventory: inventory });
      } finally {
        view.unmount();
      }
    }));
  }

  it("rejects an unsupported (retired) format before rendering", () => tracked("rejects retired format", async () => {
    const raw = JSON.parse(readFileSync(resolve(process.cwd(), "..", "..", "contracts", "campaign-file-v5", "fixtures", "draft.json"), "utf8"));
    raw.format_version = 4;
    const parsed = adapter.parseCampaignFile(JSON.stringify(raw));
    expect(parsed.ok).toBe(false);
    if (parsed.ok) throw new Error("retired format must be rejected");
    expect(parsed.reason).toBe("retired_version");
    expect(parsed.message, "the rejection is the specific error, not a fallback").toContain("version 4");
  }));

  it("PDF export text model stays complete for the loaded campaign", () => tracked("pdf text model", async () => {
    const parsed = importFixture("full-inventory");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) throw new Error(parsed.message);
    for (const locale of ["es", "en"] as const) {
      const draw = vi.spyOn(PDFPage.prototype, "drawText");
      try {
        await createWarbandPdf(parsed.document as never, locale, knowledge);
        const printed = draw.mock.calls.map(([text]) => text).join("\n");
        expect(printed.length, "the PDF wrote its roster text").toBeGreaterThan(0);
        classifyAll([printed], { locale, surface: "pdf/full-inventory", idInventory: inventory });
      } finally {
        draw.mockRestore();
      }
    }
  }));
});
