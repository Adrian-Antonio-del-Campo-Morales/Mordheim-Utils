import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { WarriorCard } from "@src/features/campaign/WarriorCard";
import { PostBattleHistory } from "@src/features/review/PostBattleHistory";
import { localizedLedger, localizedRoster } from "@src/features/review/readable-exports";
import type { CampaignDocument } from "@src/features/campaign/types";

const marker = "RAW_KB_POISON_";
const fixtures = ["draft", "active-campaign", "pending-post-battle", "full-inventory"] as const;
const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [] });

describe("real v5 importer: unsafe captures must never become presentation fallbacks", () => {
  it.each(fixtures)("preserves but never renders poisoned captures in %s", (fixture) => {
    const raw = JSON.parse(readFileSync(resolve("../../contracts/campaign-file-v5/fixtures", `${fixture}.json`), "utf8"));
    const poison = (value: unknown): void => {
      if (!value || typeof value !== "object") return;
      for (const [key, child] of Object.entries(value)) {
        if (["profile_name", "warband_type", "description", "message", "applied_label"].includes(key) && typeof child === "string") Reflect.set(value, key, marker + key);
        else poison(child);
      }
    };
    poison(raw.campaign);
    raw.campaign.identity.warband_type = marker + "warband_type";
    const adapter = new CampaignFileV5Adapter();
    const parsed = adapter.parseCampaignFile(JSON.stringify(raw));
    expect(parsed.ok, JSON.stringify(parsed)).toBe(true);
    if (!parsed.ok) return;
    const document = parsed.document as unknown as CampaignDocument;
    const saved = adapter.serializeCampaign(document.campaign);
    expect(saved.ok, JSON.stringify(saved)).toBe(true);
    if (!saved.ok) return;
    expect(saved.text).toContain(marker);
    const imported = adapter.parseCampaignFile(saved.text);
    expect(imported.ok).toBe(true);
    if (!imported.ok) return;
    const restored = imported.document as unknown as CampaignDocument;
    function Probe({ locale }: { locale: "es" | "en" }) {
      return <>{restored.campaign.warriors.map((warrior) => <WarriorCard key={warrior.id} warrior={warrior} knowledge={reader} locale={locale}/>)}{restored.campaign.post_battles.map((post) => <PostBattleHistory key={post.battle_number} document={restored} battleNumber={post.battle_number} knowledge={reader} locale={locale}/>)}</>;
    }
    const view = render(<Probe locale="es"/>);
    for (const locale of ["es", "en", "es"] as const) {
      view.rerender(<Probe locale={locale}/>);
      expect(view.container.textContent).not.toContain(marker);
      for (const node of view.container.querySelectorAll("*")) for (const attr of ["title", "aria-label", "aria-description", "data-tooltip"]) expect(node.getAttribute(attr) ?? "").not.toContain(marker);
      expect(localizedLedger(restored, locale, reader)).not.toContain(marker);
      expect(localizedRoster(restored, locale, reader)).not.toContain(marker);
      for (const warrior of restored.campaign.warriors) expect(view.container.textContent).toContain(warrior.name);
    }
  });
});
