import fontkit from "@pdf-lib/fontkit";
import { PDFDocument, rgb } from "pdf-lib";

import type { CampaignDocument } from "../campaign/types";

const A4: [number, number] = [595.28, 841.89];

export async function createWarbandPdf(document: CampaignDocument, locale: "es" | "en"): Promise<Uint8Array> {
  const pdf = await PDFDocument.create();
  pdf.registerFontkit(fontkit);
  const fontBytes = await fetch(`${import.meta.env.BASE_URL}fonts/NotoSans.ttf`).then((response) => {
    if (!response.ok) throw new Error(`Font request failed: HTTP ${response.status}`);
    return response.arrayBuffer();
  });
  const font = await pdf.embedFont(fontBytes);
  const { campaign } = document;
  const labels = locale === "es"
    ? { roster: "Banda", treasury: "Tesorería", rating: "Valoración", inventory: "Almacén", xp: "EXP", equipment: "Equipo" }
    : { roster: "Warband", treasury: "Treasury", rating: "Rating", inventory: "Stash", xp: "XP", equipment: "Equipment" };
  let page = pdf.addPage(A4);
  let y = 790;
  const write = (text: string, size = 10, x = 42) => {
    if (y < 55) { page = pdf.addPage(A4); y = 790; }
    page.drawText(text.slice(0, 110), { x, y, size, font, color: rgb(.12, .12, .1) });
    y -= size + 7;
  };
  write(campaign.identity.warband_name, 24);
  write(`${campaign.identity.campaign_name} · ${campaign.identity.warband_type}`, 11);
  write(`${labels.treasury}: ${campaign.states.at(-1)?.gold ?? campaign.configuration.starting_gold} gc   ${labels.rating}: ${campaign.states.at(-1)?.rating ?? 0}`, 10);
  y -= 8;
  write(labels.roster.toUpperCase(), 13);
  for (const warrior of campaign.warriors) {
    write(`${warrior.name} · ${warrior.profile_name} · ${labels.xp} ${warrior.experience}`, 11);
    const stats = Object.entries(warrior.stats).map(([key, value]) => `${key} ${value}`).join("   ");
    if (stats) write(stats, 8, 54);
    const equipment = warrior.equipment.map((entry) => `${entry.quantity}× ${entry.name}`).join(", ");
    if (equipment) write(`${labels.equipment}: ${equipment}`, 8, 54);
    if (warrior.skills.length) write(warrior.skills.join(", "), 8, 54);
    y -= 5;
  }
  if (campaign.inventory.length) {
    write(labels.inventory.toUpperCase(), 13);
    for (const item of campaign.inventory) write(`${item.name}: ${item.stash} / ${item.owned}`, 9, 54);
  }
  return pdf.save();
}
