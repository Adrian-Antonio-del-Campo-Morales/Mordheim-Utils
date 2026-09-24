import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName } from "../features/campaign/displayText";
import { presentationOutput } from "../features/campaign/presentation-output";
import { KnowledgeHint } from "../features/campaign/KnowledgeHint";
import { WarriorCard } from "../features/campaign/WarriorCard";
import { PostBattleHistory } from "../features/review/PostBattleHistory";
import { localizedLedger, localizedRoster } from "../features/review/readable-exports";
import type { CampaignDocument, Warrior } from "../features/campaign/types";

const marker = "RAW_KB_POISON_";
const id = `${marker}ID`;
const rawName = `${marker}NAME`;
const rawEffect = `${marker}EFFECT`;
const translated = { es: "Espada de prueba", en: "Test sword" };
const knowledge = ArtefactKnowledgeReader.from({
  schema_version: 1, ruleset: "test", bands: [], profiles: [], skills: [],
  items: [{ item_id: id, name: rawName, effect: rawEffect, names: translated, effect_i18n: { es: "Descripción de prueba", en: "Test description" } }],
});

/** Scan presentation, not selection values, React keys or action identifiers. */
function visibleMarkers(container: HTMLElement) {
  const values = [container.textContent ?? ""];
  for (const element of container.querySelectorAll("*")) {
    for (const name of ["title", "alt", "placeholder", "aria-label", "aria-description", "data-tooltip", "data-title", "data-disabled-reason"]) values.push(element.getAttribute(name) ?? "");
    if (element instanceof HTMLTextAreaElement || (element instanceof HTMLInputElement && !["hidden", "checkbox", "radio", "file"].includes(element.type))) values.push(element.value);
  }
  return values.filter((value) => value.includes(marker));
}

describe("poisoned KB presentation probes", () => {
  it("protects a real roster card, completed history and readable exports after JSON round trip", () => {
    const bandId = `${marker}BAND`, profileId = `${marker}PROFILE`;
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test",
      bands: [{ id: bandId, name: rawName, names: { es: "Banda de prueba", en: "Test warband" } }],
      profiles: [{ id: profileId, name: rawName, names: { es: "Capitana de prueba", en: "Test captain" } }],
      items: [{ item_id: id, name: rawName, names: translated, effect: rawEffect, effect_i18n: { es: "Descripción de prueba", en: "Test description" } }], skills: [],
    });
    const warrior: Warrior = { id: "personal-warrior", name: "Mi_nombre_personal", profile_id: profileId, profile_name: rawName, kind: "hero", stats: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 }, equipment: [{ item_id: id, name: rawName, quantity: 1 }], skills: [], experience: 0, cost: 20 };
    const saved = { campaign: { identity: { campaign_name: "Campaña personal", warband_name: "Banda personal", band_id: bandId, warband_type: rawName }, current_state_number: 1, warriors: [warrior], states: [], battles: [], manual_log: [], post_battles: [{ battle_number: 1, complete: true, completed_steps: [0,1,2,3,4,5,6,7], event_log: [{ step: 6, type: "buy_item", item_id: id, quantity: 1, gold: 10, description: rawEffect }, { step: 0, type: `${marker}UNKNOWN`, description: rawEffect }] }] } };
    // JSON boundary deliberately preserves stale captures and unknown open payloads.
    const document: CampaignDocument = JSON.parse(JSON.stringify(saved));
    function Probe({ locale }: { locale: "es" | "en" }) {
      return <><WarriorCard warrior={document.campaign.warriors[0]} knowledge={reader} bandId={bandId} locale={locale}/><PostBattleHistory document={document} battleNumber={1} knowledge={reader} locale={locale}/></>;
    }
    const view = render(<Probe locale="es"/>);
    for (const locale of ["es", "en", "es"] as const) {
      view.rerender(<Probe locale={locale}/>);
      expect(visibleMarkers(view.container)).toEqual([]);
      expect(view.container.textContent).toContain(translated[locale]);
      expect(view.container.textContent).toContain("Mi_nombre_personal");
      expect(view.container.textContent).toContain(locale === "es" ? "Información no disponible" : "Information unavailable");
      for (const output of [localizedLedger(document, locale, reader), localizedRoster(document, locale, reader)]) {
        expect(output).not.toContain(marker);
        expect(output).toContain(translated[locale]);
      }
    }
    expect(JSON.stringify(document)).toContain(rawEffect);
  });
  it("proves the probe catches raw names, attributes and input values", () => {
    const { container } = render(<><span title={rawEffect}>{rawName}</span><input value={rawName} readOnly /></>);
    expect(visibleMarkers(container)).toHaveLength(3);
  });

  it("keeps raw KB markers out of a selector and its tooltip across es/en/es", () => {
    function Probe({ locale }: { locale: "es" | "en" }) {
      return <><select aria-label="test selector"><option value={id}>{presentationOutput(knowledgeName(knowledge, "item", id, locale))}</option></select><KnowledgeHint knowledge={knowledge} kind="item" id={id} locale={locale} /></>;
    }
    const view = render(<Probe locale="es" />);
    for (const locale of ["es", "en", "es"] as const) {
      view.rerender(<Probe locale={locale} />);
      expect(visibleMarkers(view.container)).toEqual([]);
      expect(view.container.textContent).toContain(translated[locale]);
      expect(view.container.querySelector("option")?.value).toBe(id);
    }
  });

  it("does not replace a missing Spanish translation with poisoned English text", () => {
    const missing = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], skills: [], items: [{ item_id: id, name: rawName, effect: rawEffect }] });
    const { container } = render(<KnowledgeHint knowledge={missing} kind="item" id={id} locale="es" />);
    expect(visibleMarkers(container)).toEqual([]);
    expect(container.textContent).toContain("Información no disponible");
  });
});
