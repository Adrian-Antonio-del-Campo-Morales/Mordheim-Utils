/**
 * Campaign inventory/timeline visible completeness.
 *
 * The real v5 contract fixtures are imported through the real file adapter and
 * rendered through the real shell in ES and EN. The inventory and timeline
 * surfaces must show resolved, localized content — never the generic
 * unavailable notice, never a technical id, never an English capture shown as
 * the Spanish label. A serialized-and-reopened document renders identically,
 * and an unsupported document is rejected by its specific error before the
 * component ever receives it.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import "@testing-library/jest-dom/vitest";

import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { CampaignSlice } from "@src/features/campaign/CampaignSlice";
import { createService } from "@src/features/campaign/default-deps";
import type { CampaignAppService } from "@src/features/campaign/types";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { readArtefactReader } from "../../../support/kb-artefact";

const adapter = new CampaignFileV5Adapter();
const knowledge: ArtefactKnowledgeReader = readArtefactReader(
  resolve(process.cwd(), "../../outputs/web-public/knowledge/knowledge-web.json"),
);
const FIXTURES = resolve(process.cwd(), "../../contracts/campaign-file-v5/fixtures");

const GENERIC = { es: "Información no disponible", en: "Information unavailable" } as const;
const SPECIFIC_SCENARIO = {
  es: "El escenario no está reconocido en la base de conocimiento.",
  en: "The scenario is not recognized in the knowledge base.",
} as const;

function fixtureText(name: string): string {
  return readFileSync(resolve(FIXTURES, `${name}.json`), "utf8");
}

async function loadService(name: string): Promise<CampaignAppService> {
  const parsed = adapter.parseCampaignFile(fixtureText(name));
  expect(parsed.ok, parsed.ok ? "" : parsed.message).toBe(true);
  if (!parsed.ok) throw new Error(parsed.message);
  const service = createService(knowledge);
  const imported = await service.importCampaign({ text: JSON.stringify(parsed.document), confirm_replace: true });
  expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);
  if (!imported.ok) throw new Error(imported.message);
  return service;
}

/** Everything a person or assistive technology can read on the surface. */
function capturedValues(container: HTMLElement): string[] {
  const values: string[] = [container.textContent ?? ""];
  for (const element of container.querySelectorAll<HTMLElement>("*")) {
    for (const attribute of ["title", "alt", "placeholder", "aria-label", "aria-description", "data-tooltip", "data-disabled-reason", "data-title"]) {
      const value = element.getAttribute(attribute);
      if (value) values.push(value);
    }
    const value = (element as HTMLInputElement).value;
    if (typeof value === "string" && value.trim()) values.push(value);
  }
  return values;
}

function expectNoGenericNotice(container: HTMLElement): void {
  const values = capturedValues(container);
  for (const forbidden of [GENERIC.es, GENERIC.en]) {
    expect(values.filter((value) => value.trim() === forbidden), `exact generic notice: ${forbidden}`).toEqual([]);
    expect(values.some((value) => value.includes(forbidden)), `embedded generic notice: ${forbidden}`).toBe(false);
  }
}

async function renderCampaign(service: CampaignAppService, locale: "es" | "en") {
  const user = userEvent.setup();
  const view = render(
    <CampaignAppProvider service={service} locale={locale}>
      <CampaignSlice knowledge={knowledge} locale={locale} />
    </CampaignAppProvider>,
  );
  await view.findByRole("navigation", { name: locale === "es" ? "Cronología" : "Timeline" });
  const inventoryTab = [...view.container.querySelectorAll<HTMLElement>(".segmented-tabs button")].find(
    (button) => button.textContent?.trim() === (locale === "es" ? "INVENTARIO" : "INVENTORY"),
  );
  expect(inventoryTab, "the inventory section tab is available").toBeTruthy();
  if (inventoryTab) await user.click(inventoryTab);
  return view;
}

describe("campaign inventory and timeline visible completeness", () => {
  for (const fixture of ["active-campaign", "pending-post-battle"] as const) {
    for (const locale of ["es", "en"] as const) {
      it(`${fixture} stays complete in ${locale}`, async () => {
        const service = await loadService(fixture);
        const view = await renderCampaign(service, locale);
        try {
          expectNoGenericNotice(view.container);
          const text = view.container.textContent ?? "";
          // No technical id or captured reference reaches the surface.
          expect(text).not.toMatch(/holy_relic|sigmarite_hammer|scenario\.[a-z-]+/);
          // The inventory item resolves to its localized KB name.
          expect(text).toContain(locale === "es" ? "Reliquia Santa" : "Holy Relic");
          // The timeline resolves the captured scenario label to the KB name.
          expect(text).toContain(locale === "es" ? "Escaramuza" : "Skirmish");
          // The persisted desktop date is reformatted for the locale, not shown as captured.
          expect(text).toContain(locale === "es" ? "21/8/2026" : "8/21/2026");
          expect(text).not.toContain("21 Aug 2026");
          // The one scenario the KB does not publish gets a specific notice.
          expect(text).toContain(SPECIFIC_SCENARIO[locale]);
        } finally {
          view.unmount();
        }
      });
    }
  }

  it("stays complete after a serialize/reopen round trip", async () => {
    const service = await loadService("active-campaign");
    const current = service.current();
    expect(current).not.toBeNull();
    const saved = adapter.serializeCampaign(current!.campaign as never);
    expect(saved.ok, saved.ok ? "" : saved.message).toBe(true);
    if (!saved.ok) throw new Error(saved.message);

    const reopened = createService(knowledge);
    const imported = await reopened.importCampaign({ text: saved.text, confirm_replace: true });
    expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);

    const view = await renderCampaign(reopened, "es");
    try {
      expectNoGenericNotice(view.container);
      const text = view.container.textContent ?? "";
      expect(text).toContain("Reliquia Santa");
      expect(text).toContain("Escaramuza");
      expect(text).toContain("21/8/2026");
    } finally {
      view.unmount();
    }
  });
});

describe("unsupported documents are rejected before the component", () => {
  it.each([
    [4, "retired_version"],
    [6, "unsupported_version"],
  ] as const)("rejects format version %i with its specific error", async (version, reason) => {
    const raw = JSON.parse(fixtureText("active-campaign")) as Record<string, unknown>;
    raw.format_version = version;
    const text = JSON.stringify(raw);

    const parsed = adapter.parseCampaignFile(text);
    expect(parsed.ok).toBe(false);
    if (parsed.ok) throw new Error("unsupported document must be rejected");
    expect(parsed.reason).toBe(reason);
    expect(parsed.message).toContain(`version ${version}`);

    const service = createService(knowledge);
    const imported = await service.importCampaign({ text, confirm_replace: true });
    expect(imported.ok).toBe(false);
    if (!imported.ok) expect(imported.message).toContain(`version ${version}`);
    // The component never sees a document: nothing was loaded or rendered.
    expect(service.current()).toBeNull();
  });
});
