/**
 * Exploration follow-up caption contract.
 *
 * A current document persists a canonical `label_key` per follow-up roll and
 * localizes the caption when the panel renders it. A document that carries only
 * captured text or a locale object (`{en}`, `{es}`, `{en, es}`) without a key
 * belongs to an earlier format: it is rejected at load by the specific
 * `incompatible_format` error, localized through the application catalogue, and
 * never reaches a React component. Because no such document is ever rendered,
 * neither "Información no disponible" nor "Information unavailable" can appear
 * in place of a caption.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import "@testing-library/jest-dom/vitest";

import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import { createService } from "@src/features/campaign/default-deps";
import { translate } from "@src/features/campaign/i18n-core";
import { presentationOutput } from "@src/features/campaign/presentation-output";
import { textNumber } from "@src/features/campaign/presentation-values";
import { CampaignAppProvider, useCampaignApp } from "@src/features/campaign/useCampaignApp";
import { ExplorationPanel } from "@src/features/exploration/ExplorationPanel";
import { readArtefactReader } from "../../../support/kb-artefact";

type Locale = "es" | "en";

const adapter = new CampaignFileV5Adapter();
const knowledge = readArtefactReader(
  resolve(process.cwd(), "../../outputs/web-public/knowledge/knowledge-web.json"),
);
const FIXTURES = resolve(process.cwd(), "../../contracts/campaign-file-v5/fixtures");
const GENERIC = { es: "Información no disponible", en: "Information unavailable" } as const;
const INCOMPATIBLE = {
  es: String(translate({ key: "error.incompatible-format" }, "es")),
  en: String(translate({ key: "error.incompatible-format" }, "en")),
} as const;
const CAPTION = {
  es: { reward: "Recompensa de Coronas de Oro", test: "Chequeo de característica" },
  en: { reward: "Gold Crowns Reward", test: "Characteristic test" },
} as const;
const ROLLS_REGION = { es: "Tiradas posteriores", en: "Subsequent rolls" } as const;

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

/** The real exploration fixture, freshly parsed so every case mutates a copy. */
function fixture(): Record<string, unknown> {
  return JSON.parse(
    readFileSync(resolve(FIXTURES, "exploration-results.json"), "utf8"),
  ) as Record<string, unknown>;
}

/** The incomplete post-battle's exploration roll history and its post index. */
function exploration(raw: Record<string, unknown>): {
  readonly index: number;
  readonly rolls: Record<string, unknown>[];
} {
  const posts = asRecord(raw["campaign"])?.["post_battles"];
  if (!Array.isArray(posts)) throw new Error("the fixture must carry post-battles");
  for (const [index, post] of posts.entries()) {
    const rolls = asRecord(asRecord(asRecord(post)?.["step_state"])?.["exploration"])?.["follow_up_rolls"];
    if (Array.isArray(rolls) && rolls.length > 0) return { index, rolls: rolls as Record<string, unknown>[] };
  }
  throw new Error("the fixture must carry an exploration follow-up history");
}

/** The adapter rejects the mutated document with the specific caption error. */
function expectCaptionRejection(raw: Record<string, unknown>): void {
  const parsed = adapter.parseCampaignFile(JSON.stringify(raw));
  expect(parsed.ok).toBe(false);
  if (parsed.ok) throw new Error("an earlier-format caption document must be rejected");
  expect(parsed.reason).toBe("incompatible_format");
  expect(parsed.message).toContain("label_key");
  expect(parsed.location).toBe(
    `campaign.post_battles[${exploration(raw).index}].step_state.exploration.follow_up_rolls[0].label_key`,
  );
}

/**
 * The product's import seam: the button hands the real file to the real hook,
 * so the notice below is the localized error a user would see.
 */
function ImportHarness({ text }: { readonly text: string }) {
  const app = useCampaignApp();
  return (
    <>
      <button
        type="button"
        onClick={() => {
          const file = new File([text], "campaign.mordheim", { type: "application/json" });
          Object.defineProperty(file, "text", { value: async () => text });
          void app.importFile(file);
        }}
      >
        Importar
      </button>
      {app.error && <output role="alert">{presentationOutput(app.error)}</output>}
      {app.document && <p data-testid="loaded">{app.document.campaign.identity.campaign_name}</p>}
    </>
  );
}

/** Import `text` through the app; returns the service, the notice and the view. */
async function importThroughApp(text: string, locale: Locale) {
  const service = createService(knowledge);
  const view = render(
    <CampaignAppProvider service={service} locale={locale}>
      <ImportHarness text={text} />
    </CampaignAppProvider>,
  );
  await userEvent.click(screen.getByRole("button", { name: "Importar" }));
  const alert = await screen.findByRole("alert");
  return { service, alert, view };
}

describe("a current campaign persists canonical follow-up captions", () => {
  it("loads and reopens a document whose rolls carry label_key", async () => {
    const raw = fixture();
    for (const roll of exploration(raw).rolls) {
      expect(typeof roll["label_key"]).toBe("string");
      expect(roll).not.toHaveProperty("label");
    }
    const parsed = adapter.parseCampaignFile(JSON.stringify(raw));
    expect(parsed.ok, parsed.ok ? "" : parsed.message).toBe(true);
    if (!parsed.ok) throw new Error(parsed.message);

    const service = createService(knowledge);
    const imported = await service.importCampaign({ text: JSON.stringify(raw) });
    expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);

    const exported = await service.prepareExport();
    expect(exported.ok, exported.ok ? "" : exported.message).toBe(true);
    if (!exported.ok || !exported.payload) throw new Error("the campaign must export");

    const reopened = createService(knowledge);
    const reopenedImport = await reopened.importCampaign({ text: exported.payload.text });
    expect(reopenedImport.ok, reopenedImport.ok ? "" : reopenedImport.message).toBe(true);
    // The writer persists the canonical key only: reopening keeps the history
    // captioned by key, never by a stored sentence.
    for (const roll of exploration(JSON.parse(exported.payload.text) as Record<string, unknown>).rolls) {
      expect(typeof roll["label_key"]).toBe("string");
      expect(roll).not.toHaveProperty("label");
    }
  });

  it.each(["es", "en"] as const)("shows the canonical caption in %s", async (locale) => {
    const raw = fixture();
    const parsed = adapter.parseCampaignFile(JSON.stringify(raw));
    if (!parsed.ok) throw new Error(parsed.message);
    const service = createService(knowledge);
    const imported = await service.importCampaign({ text: JSON.stringify(raw) });
    if (!imported.ok) throw new Error(imported.message);

    const view = render(
      <CampaignAppProvider service={service} locale={locale}>
        <ExplorationPanel document={parsed.document as never} knowledge={knowledge} locale={locale} />
      </CampaignAppProvider>,
    );
    try {
      const history = await screen.findByRole("region", { name: ROLLS_REGION[locale] });
      expect(history).toHaveTextContent(`${CAPTION[locale].reward}4 → 4`);
      expect(history).toHaveTextContent(`${CAPTION[locale].test}3 → 3`);
      expect(history).not.toHaveTextContent(GENERIC[locale]);
      expect(document.body.textContent).not.toContain(GENERIC[locale]);
    } finally {
      view.unmount();
    }
  });
});

describe("earlier-format follow-up captions are rejected before render", () => {
  it.each(["es", "en"] as const)(
    "rejects a campaign whose caption is captured text (%s)",
    async (locale) => {
      const raw = fixture();
      exploration(raw).rolls[0] = { label: "Gold Crowns Reward", dice: [4], total: 4 };
      expectCaptionRejection(raw);

      const { service, alert, view } = await importThroughApp(JSON.stringify(raw), locale);
      try {
        expect(alert.textContent).toBe(INCOMPATIBLE[locale]);
        expect(document.body.textContent).not.toContain(GENERIC[locale]);
        // The document never reached a component: no campaign is loaded and
        // nothing rendered from it.
        expect(screen.queryByTestId("loaded")).not.toBeInTheDocument();
        expect(service.current()).toBeNull();
      } finally {
        view.unmount();
      }
    },
  );

  const LOCALE_OBJECTS: readonly { readonly name: string; readonly label: Record<string, string> }[] = [
    { name: "an English-only locale object", label: { en: "Gold Crowns Reward" } },
    { name: "a Spanish-only locale object", label: { es: "Recompensa de Coronas de Oro" } },
    { name: "a two-locale object", label: { en: "Gold Crowns Reward", es: "Recompensa de Coronas de Oro" } },
  ];

  it.each(LOCALE_OBJECTS)("rejects $name without label_key", ({ label }) => {
    const raw = fixture();
    exploration(raw).rolls[0] = { label, dice: [4], total: 4 };
    expectCaptionRejection(raw);
  });

  it("rejects an unknown canonical key specifically", () => {
    const raw = fixture();
    exploration(raw).rolls[0] = { label_key: "mystery_reward", dice: [4], total: 4 };
    expectCaptionRejection(raw);
  });

  it("rejects an earlier document version", async () => {
    const raw = fixture();
    raw["format_version"] = 4;
    const text = JSON.stringify(raw);
    const parsed = adapter.parseCampaignFile(text);
    expect(parsed.ok).toBe(false);
    if (parsed.ok) throw new Error("a retired version must be rejected");
    expect(parsed.reason).toBe("retired_version");

    const { service, alert, view } = await importThroughApp(text, "es");
    try {
      expect(alert.textContent).toBe(String(translate({ key: "error.retired-version", args: { version: textNumber(4, "es") } }, "es")));
      expect(document.body.textContent).not.toContain(GENERIC.es);
      expect(screen.queryByTestId("loaded")).not.toBeInTheDocument();
      expect(service.current()).toBeNull();
    } finally {
      view.unmount();
    }
  });

  it("rejects an unsupported future version", async () => {
    const raw = fixture();
    raw["format_version"] = 6;
    const text = JSON.stringify(raw);
    const parsed = adapter.parseCampaignFile(text);
    expect(parsed.ok).toBe(false);
    if (parsed.ok) throw new Error("a future version must be rejected");
    expect(parsed.reason).toBe("unsupported_version");

    const { service, alert, view } = await importThroughApp(text, "en");
    try {
      expect(alert.textContent).toBe(String(translate({ key: "error.unsupported-version", args: { version: textNumber(6, "en") } }, "en")));
      expect(document.body.textContent).not.toContain(GENERIC.en);
      expect(screen.queryByTestId("loaded")).not.toBeInTheDocument();
      expect(service.current()).toBeNull();
    } finally {
      view.unmount();
    }
  });
});
