/**
 * T11 — campaign obligations of the produced T10 contracts, on the real route.
 *
 * Every case loads its campaign the way the product does (the browser service
 * plus the real v5 file adapter) and then drives the components the campaign
 * route mounts. The subject of these tests is the *interface contract*, not the
 * domain rule (T10's suites own that):
 *
 * 1. the stable code and its parameters reach the presentation — no English
 *    diagnostic is parsed, no technical id is printed, no name is invented;
 * 2. every command goes to `service.run`; React decides nothing;
 * 3. what the campaign recorded survives save and reopen, and a campaign file
 *    written before the roll existed loads unchanged and owes only what is
 *    compulsory.
 *
 * What JSDOM proves: the rendered tree, accessible names and roles, the stable
 * codes travelling through the shell, the persistence round trip. What it does
 * not prove: real focus order, screen-reader behaviour, zoom and narrow
 * viewports (declared in the T11 delivery).
 */
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { describe, expect, it } from "vitest";

import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { mutationGrantRulesOf } from "@domain/campaign/kernel/mutations";
import type { Campaign, Warrior } from "@domain/campaign/kernel/usecases";

import { AdvancesPanel } from "@src/features/advances/AdvancesPanel";
import { CampaignObligations } from "@src/features/campaign/CampaignObligations";
import { CampaignSlice } from "@src/features/campaign/CampaignSlice";
import {
  campaignErrorText,
  campaignIssueSignal,
  campaignIssueText,
  canonicalUniqueItemId,
  leaderFacts,
  marketAvailabilityFacts,
  mutationFactsFor,
  obligationNamesOf,
  pendingDecisionFacts,
  recordedDecisionFacts,
  requiredMemberFacts,
  routPresentationFor,
  uniqueFindFacts,
  withdrawalAuditFacts,
} from "@src/features/campaign/campaign-obligations";
import { createService } from "@src/features/campaign/default-deps";
import { knowledgeName, localizedLabel } from "@src/features/campaign/displayText";
import { translate } from "@src/features/campaign/i18n-core";
import { presentationOutput } from "@src/features/campaign/presentation-output";
import type { PresentationValue } from "@src/features/campaign/presentation-values";
import type { CampaignAppService } from "@src/features/campaign/types";
import { CampaignAppProvider, useCampaignApp } from "@src/features/campaign/useCampaignApp";
import { withdrawLeftTableMembers } from "@src/features/campaign/withdrawal-consumer";
import { HirelingsPanel } from "@src/features/hirelings/HirelingsPanel";

import { freshArtefactPath, freshArtefactRaw, freshCampaignKnowledge } from "../../support/fresh-campaign-artefact";

const KAZ = "adventurers-kaz";
const NOBLE = "imperial-noble";
const DECISION = "campaign.creation.family-heirloom";
const MASTERS = "masters-of-horror-sylv";
const MARE = "order-of-the-mare-web";
const CATHAY = "pirates-of-the-cathayan-sea-sar";
const SUCCESSION = "campaign.succession.cathayan-pirates";
const SHALLOWS = "shallows-beasts-mim";
const DWARFS = "dwarf-slayer-cult-web";
const SEA_PATROL = "lothern-sea-patrol-sar";
const HOUSE = "house-guard-sc";
const ADJUTANT = "adjutant";
const REPEATER = "repeater_pistol_moh";
const ATTLAS = "runic_attlas_plate_mail";
const ATTLAS_LEGACY = "magical_artefact.attlas-plate-mail";

/** The presentation boundary's branded string, so published names travel as text. */
const pv = <T extends Record<string, string>>(value: T): { readonly [K in keyof T]: PresentationValue } =>
  Object.fromEntries(Object.entries(value).map(([key, text]) => [key, text as PresentationValue])) as { readonly [K in keyof T]: PresentationValue };

/** Names the artefact publishes, asserted literally so a leak is visible. */
const NAMES = {
  es: pv({
    decision: "Reliquia Familiar", noble: "Noble Imperial", dame: "Dama de la Yegua",
    mareClause: "Sucesión de la Dama de la Yegua", cathayClause: "Sucesión (Piratas de Cathay)",
    warlord: "Señor de la Guerra Degradado", shanghaire: "Shanghaiers", buccaneer: "Bucanero",
    repeater: "Pistola de Repetición (Maestros del Horror)", attlas: "Coraza de Placas de Att'la",
    recruits: "Reclutas Novatos", blackblood: "Sangre Negra", greatClaw: "Garra Enorme", tentacle: "Tentáculo",
    outcome: "el Noble puede repetir la primera prueba de Psicología fallida durante una batalla",
  }),
  en: pv({
    decision: "Family Heirloom", noble: "Imperial Noble", dame: "Dame of the Mare",
    repeater: "Repeater Pistol (Masters of Horror)", attlas: "Att'la's Plate Mail",
  }),
};

type Locale = "es" | "en";
const adapter = new CampaignFileV5Adapter();
const es = (key: Parameters<typeof translate>[0]["key"]) => presentationOutput(translate({ key } as never, "es"));

// ---------------------------------------------------------------------------
// Crafted campaign files. They carry state the product only reaches by playing
// (a pending post-battle, a lost leader, a printed grant) and enter through the
// same import path the app uses for a real file.
// ---------------------------------------------------------------------------

function baseCampaign(overrides: Partial<Campaign> & { band?: string }): Campaign {
  const { band, ...rest } = overrides;
  return {
    identity: { campaign_name: "T11", warband_name: "Band", warband_type: "Band", band_id: band ?? KAZ, mercenary_variant: null },
    configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors: [],
    battles: [],
    states: [{ number: 1, date: "2026-09-28", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 0 }],
    post_battles: [],
    inventory: [],
    special_rules: [],
    manual_log: [],
    ...rest,
    ...(rest.identity ? { identity: { ...rest.identity } } : {}),
  };
}

function warrior(id: string, profileId: string, extra: Record<string, unknown> = {}): Warrior {
  return {
    id,
    name: `Miembro ${id}`,
    profile_name: profileId,
    kind: "hero",
    stats: {},
    equipment: [],
    skills: [],
    experience: 0,
    cost: 0,
    quantity: 1,
    profile_id: profileId,
    ...extra,
  } as unknown as Warrior;
}

function pendingPost(battleNumber: number, extra: Record<string, unknown> = {}) {
  return {
    battle_number: battleNumber,
    complete: false,
    active_step: 1,
    completed_steps: [],
    review_open: false,
    experience_applied: true,
    pending_advances: [],
    gold_delta: 0,
    wyrdstone_delta: 0,
    pending_follow_ups: [],
    step_state: {},
    event_log: [],
    ...extra,
  };
}

function battle(number: number, extra: Record<string, unknown> = {}) {
  return {
    number,
    date: "2026-09-28",
    scenario: "skirmish",
    opponent: "Audit",
    result: "win",
    gold_delta: 0,
    wyrdstone: 0,
    xp_delta: 0,
    casualties: 0,
    advances: 0,
    rating_before: 0,
    rating_after: 0,
    models_before: 1,
    models_after: 1,
    out_of_action_ids: null,
    ...extra,
  };
}

const DRAFT_CONFIG = { is_draft: true, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 };

/** Load a crafted campaign through the campaign service's real import path. */
async function loadService(campaign: Campaign, reader: ArtefactKnowledgeReader): Promise<CampaignAppService> {
  const serialized = adapter.serializeCampaign(campaign);
  expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
  if (!serialized.ok) throw new Error(serialized.message);
  const service = createService(reader);
  const imported = await service.importCampaign({ text: serialized.text });
  expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);
  return service;
}

/**
 * The draft the product creates for the Karak Azgal Adventurers: the printed
 * minimum is four models and the Imperial Noble is the profile that carries the
 * compulsory creation roll.
 */
async function kazDraft(reader: ArtefactKnowledgeReader): Promise<CampaignAppService> {
  const service = createService(reader);
  const created = await service.createCampaign({ band_id: KAZ, campaign_name: "T11 campaign", warband_name: "Banda" });
  expect(created.ok, created.ok ? "" : created.message).toBe(true);
  const composed = await service.run("composeDraft", {
    band_id: KAZ,
    locale: "es",
    rows: [
      { profile_id: NOBLE, kind: "hero", quantity: 1, equipment: [] },
      { profile_id: "cannon-fodder", kind: "henchman", quantity: 3, equipment: [] },
    ],
  });
  expect(composed.ok, composed.ok ? "" : composed.message).toBe(true);
  return service;
}

/** Save and reopen a session exactly as the product file route does. */
async function reopen(service: CampaignAppService, reader: ArtefactKnowledgeReader): Promise<CampaignAppService> {
  const exported = await service.prepareExport();
  expect(exported.ok, exported.ok ? "" : exported.message).toBe(true);
  if (!exported.ok || !exported.payload) throw new Error("export should succeed");
  return importText(exported.payload.text, reader);
}

async function importText(text: string, reader: ArtefactKnowledgeReader): Promise<CampaignAppService> {
  const opened = createService(reader);
  const imported = await opened.importCampaign({ text });
  expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);
  return opened;
}

// ---------------------------------------------------------------------------
// Rendered routes. `CampaignRoute` is the seam `CampaignSlice` mounts (the shell
// alert plus the obligations section); `TradingRoute` mounts the Trading Post
// panel that dispatches `buyTradingItem`.
// ---------------------------------------------------------------------------

function providerProps(service: CampaignAppService, reader: ArtefactKnowledgeReader, locale: Locale) {
  const document = service.current();
  return {
    service,
    locale,
    profileName: (id: string) => knowledgeName(reader, "profile", id, locale, undefined, document?.campaign.identity.band_id),
    bandName: (id: string) => knowledgeName(reader, "band", id, locale),
    obligationNames: document ? obligationNamesOf(document, reader, locale) : undefined,
  };
}

function CampaignRoute({ reader, locale }: { readonly reader: ArtefactKnowledgeReader; readonly locale: Locale }) {
  const app = useCampaignApp();
  if (!app.document) return null;
  return <>
    {app.error && <output className="global-error" role="alert">{presentationOutput(app.error)}</output>}
    <CampaignObligations document={app.document} knowledge={reader} locale={locale} />
  </>;
}

function TradingRoute({ reader, locale }: { readonly reader: ArtefactKnowledgeReader; readonly locale: Locale }) {
  const app = useCampaignApp();
  if (!app.document) return null;
  return <>
    {app.error && <output className="global-error" role="alert">{presentationOutput(app.error)}</output>}
    <HirelingsPanel document={app.document} listings={reader} locale={locale} mode="trading" />
  </>;
}

function renderRoute(service: CampaignAppService, reader: ArtefactKnowledgeReader, locale: Locale) {
  return render(
    <CampaignAppProvider {...providerProps(service, reader, locale)}>
      <CampaignRoute reader={reader} locale={locale} />
    </CampaignAppProvider>,
  );
}

function renderTrading(service: CampaignAppService, reader: ArtefactKnowledgeReader, locale: Locale) {
  return render(
    <CampaignAppProvider {...providerProps(service, reader, locale)}>
      <TradingRoute reader={reader} locale={locale} />
    </CampaignAppProvider>,
  );
}

function obligationsRegion(locale: Locale = "es"): HTMLElement {
  return screen.getByRole("region", { name: presentationOutput(translate({ key: "campaign.obligations.title" }, locale)) });
}

/** Row of a data table: `<tr>` carries no accessible name of its own. */
function rowWith(text: string): HTMLElement {
  const row = screen.getAllByRole("row").find((candidate) => candidate.textContent?.includes(text));
  expect(row, `no table row names ${text}`).toBeDefined();
  return row!;
}

describe.skipIf(freshArtefactPath() === null)("campaign obligations (T10 contracts on the Web route)", () => {
  const reader = freshCampaignKnowledge();

  // -------------------------------------------------------------------------
  // 1. Mandatory creation decision (contracts T10-1 and T10-2)
  // -------------------------------------------------------------------------

  it("mounts the obligations on the campaign route and records the compulsory creation roll", async () => {
    const user = userEvent.setup();
    const service = await kazDraft(reader);
    render(
      <CampaignAppProvider {...providerProps(service, reader, "es")}>
        <CampaignSlice knowledge={reader} locale="es" />
      </CampaignAppProvider>,
    );

    // The owed roll is presented before the draft can be confirmed.
    const obligations = obligationsRegion();
    expect(within(obligations).getByText(NAMES.es.decision)).toBeInTheDocument();
    expect(obligations).toHaveTextContent(es("campaign.decision.pending"));
    expect(obligations).toHaveTextContent(es("campaign.decision.hint"));
    // No technical id reaches a person.
    expect(obligations).not.toHaveTextContent(DECISION);
    expect(obligations).not.toHaveTextContent("imperial-noble--family-heirloom");
    expect(obligations).not.toHaveTextContent(NOBLE);

    await user.click(within(obligations).getByRole("button", { name: es("campaign.decision.record") }));

    const recorded = presentationOutput(translate({
      key: "campaign.decision.resolved",
      args: { name: NAMES.es.decision, roll: 1, outcome: NAMES.es.outcome },
    }, "es"));
    expect(await screen.findByText(recorded)).toBeInTheDocument();
    expect(screen.getByText(es("campaign.decision.recorded"))).toBeInTheDocument();
    // The roll is no longer owed, so the interface stops asking for it.
    expect(screen.getByText(es("campaign.decision.none"))).toBeInTheDocument();
    // The domain recorded the outcome by stable id, not by translated text.
    expect(service.current()!.campaign.special_rules.filter((row) => row["kind"] === "creation_decision")).toEqual([
      expect.objectContaining({ decision_id: DECISION, outcome_id: "psychology-reroll", roll: 1, order: 1 }),
    ]);
  });

  it("asks again for a campaign that never recorded the roll and blocks the commit with its stable code", async () => {
    const user = userEvent.setup();
    const service = await kazDraft(reader);
    // A file written before the roll existed simply has no entry: it loads
    // unchanged and the compulsory roll is owed again.
    const exported = await service.prepareExport();
    expect(exported.ok && exported.payload).toBeTruthy();
    if (!exported.ok || !exported.payload) return;
    const legacy = JSON.parse(exported.payload.text) as { campaign: { special_rules: { kind?: string }[] } };
    legacy.campaign.special_rules = legacy.campaign.special_rules.filter((row) => row["kind"] !== "creation_decision");
    const older = await importText(JSON.stringify(legacy), reader);
    expect(pendingDecisionFacts(older.current()!, reader, "es")).toHaveLength(1);

    render(
      <CampaignAppProvider {...providerProps(older, reader, "es")}>
        <CampaignSlice knowledge={reader} locale="es" />
      </CampaignAppProvider>,
    );
    const commitButton = screen.getByRole("button", { name: new RegExp(es("ui.7ff41d8a718b")) });
    expect(commitButton).toBeEnabled();
    await user.click(commitButton);
    const alert = await screen.findByRole("alert");
    // The sentence comes from the code plus the resolved decision name.
    expect(alert).toHaveTextContent(presentationOutput(translate({ key: "campaign.decision.required", args: { name: NAMES.es.decision } }, "es")));
    expect(alert).not.toHaveTextContent(DECISION);
    expect(alert).not.toHaveTextContent("prerequisite_missing");

    const rejected = await older.run("commitInitialWarband", {});
    expect(rejected.ok).toBe(false);
    if (rejected.ok) return;
    expect(campaignIssueSignal(rejected)).toEqual({ code: "prerequisite_missing", subjectIds: [DECISION] });
    expect(campaignErrorText(rejected, older.current()!, reader, "es")).toEqual({
      text: presentationOutput(translate({ key: "campaign.decision.required", args: { name: NAMES.es.decision } }, "es")),
      severity: "status",
    });
  });

  it("keeps the recorded roll and its order across save and reopen and refuses a second roll", async () => {
    const service = await kazDraft(reader);
    const resolved = await service.run("resolveCreationDecision", { decision_id: DECISION, roll: 3 });
    expect(resolved.ok, resolved.ok ? "" : resolved.message).toBe(true);

    const opened = await reopen(service, reader);
    const document = opened.current()!;
    expect(pendingDecisionFacts(document, reader, "es")).toHaveLength(0);
    expect(recordedDecisionFacts(document, reader, "es")).toEqual([
      expect.objectContaining({ id: DECISION, order: 1, roll: 3, outcome: "el Noble causa Miedo a Orcos y Goblins y Skaven" }),
    ]);

    const view = renderRoute(opened, reader, "es");
    expect(obligationsRegion()).toHaveTextContent(es("campaign.decision.none"));
    expect(obligationsRegion()).toHaveTextContent(NAMES.es.decision);
    view.unmount();

    // The same roll cannot be recorded twice, and the codes stay stable.
    const again = await opened.run("resolveCreationDecision", { decision_id: DECISION, roll: 3 });
    expect(again.ok).toBe(false);
    if (!again.ok) expect(campaignIssueSignal(again)).toEqual({ code: "conflict", subjectIds: [DECISION] });
    const unknown = await opened.run("resolveCreationDecision", { decision_id: "campaign.creation.not-published", roll: 3 });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(campaignIssueSignal(unknown).code).toBe("not_found");
    const outside = await service.run("resolveCreationDecision", { decision_id: DECISION, roll: 99 });
    expect(outside.ok).toBe(false);
    if (!outside.ok) expect(campaignIssueSignal(outside).code).toBe("invalid_input");
  });

  // -------------------------------------------------------------------------
  // 2. Restricted market (contract T10-3)
  // -------------------------------------------------------------------------

  it("lets the named warband buy the printed Trading Post item and refuses every other warband", async () => {
    const user = userEvent.setup();
    const masters = await loadService(
      baseCampaign({ band: MASTERS, post_battles: [pendingPost(1)], battles: [battle(1)], warriors: [warrior("scientist", "mad-scientist")] }),
      reader,
    );
    const first = renderTrading(masters, reader, "es");
    const row = rowWith(NAMES.es.repeater);
    // Cost and currency are visible; the verdict is the row's status.
    expect(row).toHaveTextContent("25+3D6 co");
    const availabilityCell = within(row).getAllByRole("cell").find((cell) => cell.textContent?.includes(es("campaign.market.available")))!;
    // Available, with no printed scope to report in the availability cell.
    expect(availabilityCell.querySelector("small.restriction-note")).toBeNull();

    await user.click(within(row).getByRole("button", { name: /Tirar 3D6/ }));
    await user.click(await within(row).findByRole("button", { name: new RegExp(es("ui.ee094da2d5dd")) }));

    const bought = masters.current()!;
    expect(bought.campaign.inventory.find((item) => item.id === REPEATER)?.owned).toBe(1);
    // The purchase is an inventory entry, never starting equipment.
    expect(bought.campaign.warriors.every((member) => member.equipment.every((item) => item.item_id !== REPEATER))).toBe(true);

    // Reopening does not duplicate the purchase.
    const opened = await reopen(masters, reader);
    expect(opened.current()!.campaign.inventory.filter((item) => item.id === REPEATER).reduce((total, item) => total + item.owned, 0)).toBe(1);
    first.unmount();

    // Another warband sees the printed scope and cannot buy it.
    const outsider = await loadService(
      baseCampaign({ band: KAZ, post_battles: [pendingPost(1)], battles: [battle(1)], warriors: [warrior("noble", NOBLE)] }),
      reader,
    );
    renderTrading(outsider, reader, "es");
    const outsiderRow = rowWith(NAMES.es.repeater);
    const outsiderAvailability = within(outsiderRow).getAllByRole("cell").find((cell) => cell.querySelector("small.restriction-note"))!;
    expect(outsiderAvailability).toHaveTextContent(NAMES.es.repeater);
    await user.click(within(outsiderRow).getByRole("button", { name: /Tirar 3D6/ }));
    await user.click(await within(outsiderRow).findByRole("button", { name: new RegExp(es("ui.ee094da2d5dd")) }));
    const refusal = await screen.findByRole("alert");
    expect(refusal).toHaveTextContent(presentationOutput(translate({ key: "campaign.market.warband-only", args: { item: NAMES.es.repeater } }, "es")));
    expect(refusal).not.toHaveTextContent(REPEATER);
    expect(outsider.current()!.campaign.inventory.some((item) => item.id === REPEATER)).toBe(false);

    // An item the source prints as a unique find is not sold, and one the
    // catalogue does not list has its own verdict. Both name the object.
    const document = outsider.current()!;
    expect(marketAvailabilityFacts(document, reader, ATTLAS, "es")).toEqual({
      available: false,
      text: presentationOutput(translate({ key: "campaign.market.not-common", args: { item: NAMES.es.attlas } }, "es")),
    });
    expect(marketAvailabilityFacts(document, reader, "not_a_published_item", "es")).toEqual({
      available: false,
      text: presentationOutput(translate({ key: "campaign.market.not-listed", args: { item: presentationOutput(unavailableText("es")) as PresentationValue } }, "es")),
    });
  });

  it("phrases every market code without printing the item id, in both locales", async () => {
    const service = await loadService(baseCampaign({ warriors: [warrior("noble", NOBLE)] }), reader);
    for (const locale of ["es", "en"] as const) {
      const names = obligationNamesOf(service.current()!, reader, locale);
      const codes = ["market_not_common", "market_not_listed", "market_warband_only", "market_warband_forbidden", "market_creation_only", "market_condition_unstructured"] as const;
      const phrase = (code: (typeof codes)[number]) => campaignIssueText({ code, subjectIds: [REPEATER] }, names, locale);
      for (const code of codes) {
        const text = presentationOutput(phrase(code)!.text);
        expect(text).not.toContain(REPEATER);
        expect(text).not.toBe(presentationOutput(translate({ key: "knowledge.unavailable" }, locale)));
        expect(text).toContain(NAMES[locale].repeater);
      }
      // A refusal is an alert; a missing scope is a pending datum.
      expect(phrase("market_not_common")?.severity).toBe("alert");
      expect(phrase("market_creation_only")?.severity).toBe("alert");
      expect(phrase("market_condition_unstructured")?.severity).toBe("status");
      // An unknown code hands the decision back to the caller's fallback.
      expect(campaignIssueText({ code: null, subjectIds: [] }, names, locale)).toBeNull();
    }
  });

  // -------------------------------------------------------------------------
  // 2b. An advance verdict published as a code (contract T10-5)
  // -------------------------------------------------------------------------

  it("phrases the pending band special-skill list the advance contract refuses with", async () => {
    // `house-guard-sc` publishes a hero with `special` skill access and no
    // members for its special list, so the T10 advance contract refuses the
    // choice with its own code instead of granting the whole special catalogue.
    const special = reader.list("skill").find((row) => row["category"] === "special")!;
    expect(special, "the artefact publishes no special skill").toBeDefined();
    const service = await loadService(
      baseCampaign({
        band: HOUSE,
        battles: [battle(1)],
        warriors: [warrior("adj", ADJUTANT, { skill_access: ["special"] })],
        post_battles: [pendingPost(1, {
          pending_advances: [
            { warrior_id: "adj", warrior_name: "Miembro adj", table: "hero", threshold: null, roll_total: 11, subroll: null, committed: false, applied_label: "", promotion_setup_pending: false, advance_options: [{ kind: "choose_skill" }] },
          ],
        })],
      }),
      reader,
    );

    const refused = await service.run("commitAdvanceChoice", { warrior_id: "adj", threshold: null, kind: "choose_skill", skill_id: special["id"] });
    expect(refused.ok).toBe(false);
    if (refused.ok) return;
    // The code and its parameters survive the service, and the parameters are
    // the ids the sentence must never print.
    expect(campaignIssueSignal(refused)).toEqual({ code: "skill_pending_special_list", subjectIds: [HOUSE, ADJUTANT, String(special["id"])] });
    for (const locale of ["es", "en"] as const) {
      const phrase = campaignErrorText(refused, service.current()!, reader, locale);
      expect(phrase).toEqual({
        text: presentationOutput(translate({ key: "campaign.advance.pending-special-list" }, locale)),
        severity: "status",
      });
      const text = presentationOutput(phrase!.text);
      expect(text).not.toContain(HOUSE);
      expect(text).not.toContain(String(special["id"]));
    }
    // The refusal is a missing datum, not a consumed choice: nothing was written.
    expect(service.current()!.campaign.post_battles[0].pending_advances![0]["committed"]).toBe(false);
    expect(service.current()!.campaign.warriors[0].skills).toEqual([]);
  });

  it("phrases a skill outside the profile's published tables with its own sentence", async () => {
    // `house-guard-sc`/`adjutant` publishes `academic` and `special` access only,
    // so a Speed skill is outside the printed tables. The construction contract
    // refuses it with `skill_not_permitted` and its three parameters; the module
    // owns the sentence for that code, so the rejection never falls back to the
    // English diagnostic of the domain or to a printed id.
    const outside = reader.list("skill").find((row) => row["id"] === "skill.acrobat")!;
    expect(outside, "the artefact no longer publishes skill.acrobat").toBeDefined();
    const service = await loadService(
      baseCampaign({
        band: HOUSE,
        battles: [battle(1)],
        warriors: [warrior("adj", ADJUTANT, { skill_access: ["speed"] })],
        post_battles: [pendingPost(1, {
          pending_advances: [
            { warrior_id: "adj", warrior_name: "Miembro adj", table: "hero", threshold: null, roll_total: 11, subroll: null, committed: false, applied_label: "", promotion_setup_pending: false, advance_options: [{ kind: "choose_skill" }] },
          ],
        })],
      }),
      reader,
    );

    const refused = await service.run("commitAdvanceChoice", { warrior_id: "adj", threshold: null, kind: "choose_skill", skill_id: "skill.acrobat" });
    expect(refused.ok).toBe(false);
    if (refused.ok) return;
    expect(campaignIssueSignal(refused)).toEqual({ code: "skill_not_permitted", subjectIds: [HOUSE, ADJUTANT, "skill.acrobat"] });
    for (const locale of ["es", "en"] as const) {
      const phrase = campaignErrorText(refused, service.current()!, reader, locale);
      expect(phrase?.severity).toBe("alert");
      const text = presentationOutput(phrase!.text);
      expect(text).toContain(presentationOutput(knowledgeName(reader, "skill", "skill.acrobat", locale)));
      expect(text).toContain(presentationOutput(knowledgeName(reader, "profile", ADJUTANT, locale, undefined, HOUSE)));
      // Neither the ids nor the English diagnostic of the domain are visible.
      expect(text).not.toContain("skill.acrobat");
      expect(text).not.toContain(ADJUTANT);
      expect(text).not.toContain(HOUSE);
      expect(text).not.toContain("is outside the skill access of");
      expect(text).not.toBe(presentationOutput(translate({ key: "error.action-failed" }, locale)));
    }
    // The refusal writes nothing: no skill and no committed advance.
    expect(service.current()!.campaign.post_battles[0].pending_advances![0]["committed"]).toBe(false);
    expect(service.current()!.campaign.warriors[0].skills).toEqual([]);
  });

  // -------------------------------------------------------------------------
  // 3. Unique find (canonical id plus the id older campaigns persisted)
  // -------------------------------------------------------------------------

  it("merges the legacy identifier of a unique find into a single object", async () => {
    const service = await loadService(
      baseCampaign({
        warriors: [warrior("noble", NOBLE)],
        inventory: [
          { id: ATTLAS, name: "Att'la's Plate Mail", category: "Magic Artefact", owned: 1, equipped: 1, stash: 0, value: 0 },
          { id: ATTLAS_LEGACY, name: "Att'la's Plate Mail", category: "Magic Artefact", owned: 1, equipped: 0, stash: 1, value: 0 },
        ],
      }),
      reader,
    );
    const document = service.current()!;
    renderRoute(service, reader, "es");

    expect(canonicalUniqueItemId(reader, ATTLAS)).toBe(ATTLAS);
    expect(canonicalUniqueItemId(reader, ATTLAS_LEGACY)).toBe(ATTLAS);
    const facts = uniqueFindFacts(document, reader, "es");
    expect(facts).toHaveLength(1);
    // Two spellings of one object, merged into a single row with its totals.
    expect(facts[0]).toMatchObject({ id: ATTLAS, owned: 2, stash: 1, legacyOnly: false });

    const entry = presentationOutput(translate({ key: "campaign.unique.entry", args: { name: NAMES.es.attlas, owned: 2, stash: 1 } }, "es"));
    const obligations = obligationsRegion();
    expect(within(obligations).getByText(entry)).toBeInTheDocument();
    expect(within(obligations).getAllByRole("listitem")).toHaveLength(1);
    expect(obligations).not.toHaveTextContent(ATTLAS);
    expect(obligations).not.toHaveTextContent(ATTLAS_LEGACY);
    // Reopening keeps one object with the same totals.
    const opened = await reopen(service, reader);
    expect(uniqueFindFacts(opened.current()!, reader, "es")).toEqual([expect.objectContaining({ id: ATTLAS, owned: 2, stash: 1 })]);
  });

  it("presents a find an older campaign saved under the row-derived id as the canonical object", async () => {
    const legacyOnly = await loadService(
      baseCampaign({
        warriors: [warrior("noble", NOBLE)],
        inventory: [{ id: ATTLAS_LEGACY, name: "Att'la's Plate Mail", category: "Magic Artefact", owned: 1, equipped: 1, stash: 0, value: 0 }],
      }),
      reader,
    );
    renderRoute(legacyOnly, reader, "es");
    const facts = uniqueFindFacts(legacyOnly.current()!, reader, "es");
    expect(facts).toEqual([expect.objectContaining({ id: ATTLAS, owned: 1, stash: 0, legacyOnly: true })]);
    // The canonical name and the note: never the id the file stored.
    expect(obligationsRegion()).toHaveTextContent(NAMES.es.attlas);
    expect(obligationsRegion()).toHaveTextContent(es("campaign.unique.legacy"));
    expect(obligationsRegion()).not.toHaveTextContent(ATTLAS_LEGACY);
    // Both locales resolve the catalogue name instead of leaking the id.
    expect(uniqueFindFacts(legacyOnly.current()!, reader, "en")[0]).toMatchObject({ name: knowledgeName(reader, "item", ATTLAS, "en") });
  });

  // -------------------------------------------------------------------------
  // 4. Roster lifecycle and Rout facts (contracts T10-4 and T10-5)
  // -------------------------------------------------------------------------

  it("requires the printed mandatory member before any other recruit and keeps it satisfied after reopen", async () => {
    const user = userEvent.setup();
    const service = await loadService(
      baseCampaign({ band: MARE, warriors: [warrior("paragon", "paragon")], battles: [battle(1)], post_battles: [pendingPost(1)] }),
      reader,
    );
    const refused = await service.run("recruitBandProfile", { profile_id: "bowmen", quantity: 1 });
    expect(refused.ok).toBe(false);
    if (!refused.ok) {
      // The refusal carries the clause and the printed profile it requires.
      expect(campaignIssueSignal(refused)).toEqual({
        code: "lifecycle_member_required",
        subjectIds: ["campaign.lifecycle.dame-of-the-mare-succession", "dame-of-the-mare"],
      });
      expect(campaignErrorText(refused, service.current()!, reader, "es")).toEqual({
        text: presentationOutput(translate({ key: "campaign.lifecycle.required", args: { clause: NAMES.es.mareClause, profile: NAMES.es.dame } }, "es")),
        severity: "status",
      });
    }

    const view = renderRoute(service, reader, "es");
    const obligations = obligationsRegion();
    expect(within(obligations).getByText(NAMES.es.mareClause)).toBeInTheDocument();
    expect(obligations).toHaveTextContent(NAMES.es.dame);
    expect(obligations).not.toHaveTextContent(MARE);
    expect(obligations).not.toHaveTextContent("campaign.lifecycle.dame-of-the-mare-succession");

    // The printed profile is exactly the recruit that discharges the clause, so
    // the section stops asking for it — through the service, not in React.
    await user.click(within(obligations).getByRole("button", { name: es("campaign.lifecycle.recruit") }));
    await waitFor(() => expect(screen.queryByText(NAMES.es.mareClause)).toBeNull());
    expect(service.current()!.campaign.warriors.filter((row) => row.profile_id === "dame-of-the-mare")).toHaveLength(1);
    view.unmount();

    const opened = await reopen(service, reader);
    expect(requiredMemberFacts(opened.current()!, reader, "es")).toHaveLength(0);
    expect((await opened.run("recruitBandProfile", { profile_id: "bowmen", quantity: 1 })).ok).toBe(true);
  });

  it("presents the Rout-test facts without resolving the test in the interface", async () => {
    const service = await loadService(
      baseCampaign({
        band: SEA_PATROL,
        warriors: [warrior("commodore", "commodore"), warrior("recruits", "raw-recruits", { kind: "henchman", quantity: 3 })],
        battles: [battle(1, { out_of_action_ids: ["recruits"], models_before: 4, models_after: 4 })],
      }),
      reader,
    );
    const document = service.current()!;
    expect(routPresentationFor(document, reader, "es", 1)).toMatchObject({ battleNumber: 1, models: 4, countedModels: 1, exemptOutOfActionModels: 3 });

    renderRoute(service, reader, "es");
    const obligations = obligationsRegion();
    expect(obligations).toHaveTextContent(presentationOutput(translate({ key: "campaign.rout.summary", args: { models: 4, counted: 1 } }, "es")));
    expect(obligations).toHaveTextContent(presentationOutput(translate({ key: "campaign.rout.counted-members" }, "es")));
    expect(obligations).toHaveTextContent("Miembro recruits");
    expect(obligations).toHaveTextContent(NAMES.es.recruits);
    expect(obligations).toHaveTextContent(presentationOutput(translate({ key: "campaign.rout.pending" }, "es")));
    // The interface publishes the facts and offers no way to resolve the test.
    expect(within(obligations).queryAllByRole("button")).toHaveLength(0);
    expect(within(obligations).queryByRole("spinbutton")).toBeNull();
  });

  // -------------------------------------------------------------------------
  // 5. Withdrawals reported by the battle (T10's consequence, T13's trigger)
  // -------------------------------------------------------------------------

  it("applies the withdrawal the battle reported, audits it, and keeps the typed consumer", async () => {
    const service = await loadService(
      baseCampaign({
        battles: [battle(1)],
        warriors: [
          warrior("hero", "commodore"),
          warrior("group", "raw-recruits", { kind: "henchman", quantity: 3, equipment: [{ item_id: "sword", name: "Sword", quantity: 3, per_model: true, transferable: true, acquisition: "purchased" }] }),
        ],
        inventory: [{ id: "sword", name: "Sword", category: "Equipment", owned: 3, equipped: 3, stash: 0, value: 0 }],
      }),
      reader,
    );

    // A hero goes, a group loses one member and its per-model share.
    expect(await withdrawLeftTableMembers(service, { member_ids: ["hero", "group"], reason: "blimey", battle_number: 1 })).toEqual({ ok: true });
    const document = service.current()!;
    expect(document.campaign.warriors.some((row) => row.id === "hero")).toBe(false);
    expect(document.campaign.warriors.find((row) => row.id === "group")?.quantity).toBe(2);
    expect(document.campaign.inventory.find((row) => row.id === "sword")?.owned).toBe(2);

    // The audit is presented with personal names and never with row ids.
    renderRoute(service, reader, "es");
    const obligations = obligationsRegion();
    expect(obligations).toHaveTextContent(es("campaign.withdrawal.heading"));
    expect(obligations).toHaveTextContent("Miembro group × 1");
    expect(obligations).toHaveTextContent(es("campaign.withdrawal.event"));
    expect(obligations).not.toHaveTextContent("left_table_withdrawal");

    // The same report cannot remove anyone twice; an unknown id is not found.
    expect(await withdrawLeftTableMembers(service, { member_ids: ["hero"] })).toEqual({ ok: false, code: "conflict", subjectIds: ["hero"] });
    expect(await withdrawLeftTableMembers(service, { member_ids: ["nobody"] })).toEqual({ ok: false, code: "not_found", subjectIds: ["nobody"] });
    expect(withdrawalAuditFacts(service.current()!, "es")).toHaveLength(1);

    // A draft has no battle withdrawal.
    const draft = await loadService(baseCampaign({ configuration: DRAFT_CONFIG, current_state_number: 0, states: [], warriors: [warrior("hero", "commodore")] }), reader);
    expect(await withdrawLeftTableMembers(draft, { member_ids: ["hero"] })).toEqual({ ok: false, code: "not_permitted_in_draft", subjectIds: [] });

    // Reopening keeps the roster and the audit identical.
    const opened = await reopen(service, reader);
    expect(opened.current()!.campaign.warriors.find((row) => row.id === "group")?.quantity).toBe(2);
    expect(withdrawalAuditFacts(opened.current()!, "es")).toEqual([expect.objectContaining({ order: 1, battleNumber: 1 })]);
  });

  // -------------------------------------------------------------------------
  // 6. Leader succession (contract T10-4)
  // -------------------------------------------------------------------------

  it("seats the published successor only once the leader is gone and explains its source limit", async () => {
    const user = userEvent.setup();
    const service = await loadService(
      baseCampaign({ band: CATHAY, battles: [battle(1)], warriors: [warrior("warlord", "disgraced-warlord"), warrior("shang", "shanghaires")] }),
      reader,
    );
    // While the leader is present the succession is a conflict, not a silent write.
    const early = await service.run("succeedLeader", { clause_id: SUCCESSION });
    expect(early.ok).toBe(false);
    if (!early.ok) expect(campaignIssueSignal(early)).toEqual({ code: "conflict", subjectIds: ["warlord"] });

    const first = renderRoute(service, reader, "es");
    const obligations = obligationsRegion();
    expect(obligations).toHaveTextContent(es("campaign.succession.leader"));
    expect(obligations).toHaveTextContent("Miembro warlord");
    expect(obligations).not.toHaveTextContent(NAMES.es.cathayClause);
    first.unmount();

    await withdrawLeftTableMembers(service, { member_ids: ["warlord"], battle_number: 1 });
    const pending = leaderFacts(service.current()!, reader, "es");
    expect(pending.leader).toBeNull();
    expect(pending.pending?.clauseName).toBe(NAMES.es.cathayClause);
    expect(pending.pending?.candidates).toEqual([{ id: "shang", name: "Miembro shang" }]);
    expect(pending.sourceLimit).toBe(false);

    renderRoute(service, reader, "es");
    await user.click(screen.getByRole("button", { name: es("campaign.succession.confirm") }));
    // The pending choice closes through the service and the leader is seated.
    await waitFor(() => expect(screen.queryByRole("button", { name: es("campaign.succession.confirm") })).toBeNull());
    expect(obligationsRegion()).toHaveTextContent("Miembro shang");
    // The recorded event survives a reopen and still seats the successor.
    const opened = await reopen(service, reader);
    expect(leaderFacts(opened.current()!, reader, "es").leader?.warriorId).toBe("shang");

    // Two eligible successors: the choice is the caller's and the source does not
    // publish a tie-break, so the interface says so instead of inventing one.
    const several = await loadService(baseCampaign({ band: CATHAY, warriors: [warrior("shang", "shanghaires"), warrior("shang2", "shanghaires")] }), reader);
    const ambiguousView = renderRoute(several, reader, "es");
    const ambiguous = within(ambiguousView.container).getByRole("region", { name: presentationOutput(translate({ key: "campaign.obligations.title" }, "es")) });
    const confirm = within(ambiguous).getByRole("button", { name: es("campaign.succession.confirm") });
    expect(confirm).toBeDisabled();
    expect(confirm).toHaveAttribute("data-disabled-reason", es("campaign.succession.choose"));
    expect(ambiguous).toHaveTextContent(es("campaign.succession.source-limit"));
    const missing = await several.run("succeedLeader", { clause_id: SUCCESSION });
    expect(missing.ok).toBe(false);
    if (!missing.ok) expect(campaignIssueSignal(missing).code).toBe("invalid_input");

    // No published successor in the roster: the campaign reports what is missing.
    const none = await loadService(baseCampaign({ band: CATHAY, warriors: [warrior("warlord", "disgraced-warlord")] }), reader);
    await withdrawLeftTableMembers(none, { member_ids: ["warlord"] });
    const empty = await none.run("succeedLeader", { clause_id: SUCCESSION });
    expect(empty.ok).toBe(false);
    if (empty.ok) return;
    expect(campaignErrorText(empty, none.current()!, reader, "es")).toEqual({
      text: presentationOutput(translate({ key: "campaign.succession.no-candidate", args: { name: NAMES.es.shanghaire } }, "es")),
      severity: "status",
    });
  });

  // -------------------------------------------------------------------------
  // 7. Mutations (contract T10-3)
  // -------------------------------------------------------------------------

  it("buys a published mutation while recruiting, prices it, and refuses the rest", async () => {
    const user = userEvent.setup();
    const service = await loadService(
      baseCampaign({ band: SHALLOWS, configuration: DRAFT_CONFIG, current_state_number: 0, states: [], warriors: [warrior("buccaneer", "buccaneer", { cost: 85 })] }),
      reader,
    );
    renderRoute(service, reader, "es");
    const obligations = obligationsRegion();
    expect(obligations).toHaveTextContent(es("campaign.heading.mutations"));
    expect(obligations).toHaveTextContent("Miembro buccaneer");
    // Only the published, priced ids are offered; the printed names the KB does
    // not price are reported as missing data, never as a choice.
    const select = within(obligations).getByRole("combobox");
    const options = within(select).getAllByRole("option").map((option) => option.textContent ?? "");
    expect(options).toContain(`${NAMES.es.blackblood} · 30 co`);
    expect(options).toContain(`${NAMES.es.greatClaw} · 50 co`);
    expect(options).toContain(`${NAMES.es.tentacle} · 35 co`);
    expect(options.join(" ")).not.toContain("prehensile tail");
    expect(obligations).toHaveTextContent(es("campaign.mutation.unpriced"));
    expect(obligations).not.toHaveTextContent("campaign.mutation.grant.aquatic-mutants");

    const blackblood = within(select).getAllByRole("option").find((option) => option.textContent?.startsWith(NAMES.es.blackblood))!;
    await user.selectOptions(select, blackblood);
    await user.click(within(obligations).getByRole("button", { name: new RegExp(es("campaign.mutation.buy")) }));
    await waitFor(() => expect(service.current()!.campaign.special_rules.filter((row) => row["kind"] === "mutation")).toHaveLength(1));
    // The bought mutation leaves the offer list instead of being offered twice.
    expect(within(obligations).getAllByRole("option").map((option) => option.textContent ?? "")).not.toContain(`${NAMES.es.blackblood} · 30 co`);

    const bought = service.current()!;
    expect(bought.campaign.special_rules.filter((row) => row["kind"] === "mutation")).toEqual([
      expect.objectContaining({ warrior_id: "buccaneer", mutation_id: "campaign.mutation.blackblood", cost_gc: 30, order: 1 }),
    ]);
    // The purchase is paid for, not granted: the recruitment cost rises by it.
    expect(bought.campaign.warriors[0].cost).toBe(115);
    expect(mutationFactsFor(bought, reader, "buccaneer", "es")?.purchased).toBe(1);

    // The grant allows one mutation per warrior: a second one is refused.
    const second = await service.run("buyMutation", { warrior_id: "buccaneer", mutation_id: "campaign.mutation.great-claw" });
    expect(second.ok).toBe(false);
    if (!second.ok) expect(campaignIssueSignal(second).code).toBe("limit_reached");
    const duplicate = await service.run("buyMutation", { warrior_id: "buccaneer", mutation_id: "campaign.mutation.blackblood" });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) expect(campaignErrorText(duplicate, bought, reader, "es")).toEqual({ text: es("campaign.error-conflict"), severity: "alert" });
    const unknown = await service.run("buyMutation", { warrior_id: "buccaneer", mutation_id: "campaign.mutation.not-published" });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(campaignIssueSignal(unknown).code).toBe("not_found");

    // Buying once the campaign is committed is refused by its own code.
    const committed = await loadService(baseCampaign({ band: SHALLOWS, warriors: [warrior("buccaneer", "buccaneer")] }), reader);
    const late = await committed.run("buyMutation", { warrior_id: "buccaneer", mutation_id: "campaign.mutation.blackblood" });
    expect(late.ok).toBe(false);
    if (!late.ok) expect(campaignErrorText(late, committed.current()!, reader, "es")).toEqual({ text: es("campaign.error-recruiting-only"), severity: "alert" });

    // Not enough gold for the printed price.
    const poor = await loadService(
      baseCampaign({ band: SHALLOWS, configuration: { ...DRAFT_CONFIG, starting_gold: 90 }, current_state_number: 0, states: [], warriors: [warrior("buccaneer", "buccaneer", { cost: 85 })] }),
      reader,
    );
    const unaffordable = await poor.run("buyMutation", { warrior_id: "buccaneer", mutation_id: "campaign.mutation.blackblood" });
    expect(unaffordable.ok).toBe(false);
    if (!unaffordable.ok) expect(campaignIssueSignal(unaffordable).code).toBe("limit_violated");

    // A band the artefact publishes no grant for offers no action at all.
    expect(mutationGrantRulesOf(reader, KAZ)).toHaveLength(0);

    // The five obligations blocked by the source contract are missing data: the
    // artefact publishes no campaign row to consume, so nothing is offered.
    const blocked = ["baneworms--mer-creature", "band--skill-mutating-experiment", "prophet--corrupting-influence", "the-bloated--weak-magic"];
    for (const section of ["recruitment-and-veterans", "mutations", "exploration-and-income"] as const) {
      for (const value of Object.values(reader.campaignSection(section))) {
        for (const row of Array.isArray(value) ? value : []) {
          if (row && typeof row === "object" && "rule_id" in row) expect(blocked).not.toContain(String((row as Record<string, unknown>).rule_id));
        }
      }
    }
    expect(mutationGrantRulesOf(reader, "skaven-of-clan-pristekk-sc")).toHaveLength(0);
  });

  // -------------------------------------------------------------------------
  // 8. Born Marksmen on the real advance flow (contract T10-5)
  // -------------------------------------------------------------------------

  it("offers the printed Shooting list to the named profile only, on the advance flow", async () => {
    const user = userEvent.setup();
    // Remove Shooting from the band's hero tables so the printed grant is the
    // only source of the choice — the case the rule exists for.
    const raw = freshArtefactRaw();
    for (const profile of raw["profiles"] as Record<string, unknown>[]) {
      if (profile["band_id"] !== DWARFS || profile["type"] !== "hero") continue;
      profile["skill_access"] = (profile["skill_access"] as string[]).filter((table) => table !== "shooting");
    }
    const marksmen = ArtefactKnowledgeReader.from(raw);
    const service = await loadService(
      baseCampaign({
        band: DWARFS,
        battles: [battle(1)],
        warriors: [warrior("slayer", "giant-slayer"), warrior("hurlers", "axe-hurlers", { kind: "henchman", quantity: 2 })],
        post_battles: [pendingPost(1, {
          pending_advances: [
            { warrior_id: "hurlers", warrior_name: "Miembro hurlers", table: "hero", threshold: null, roll_total: null, subroll: null, committed: false, applied_label: "", promotion_setup_pending: true, advance_options: [] },
            { warrior_id: "slayer", warrior_name: "Miembro slayer", table: "hero", threshold: null, roll_total: null, subroll: null, committed: false, applied_label: "", promotion_setup_pending: true, advance_options: [] },
          ],
        })],
      }),
      marksmen,
    );
    render(
      <CampaignAppProvider {...providerProps(service, marksmen, "es")}>
        <AdvancesPanel document={service.current()!} knowledge={marksmen} locale="es" />
      </CampaignAppProvider>,
    );

    const shooting = presentationOutput(localizedLabel("shooting", "es"));
    const hurlerRow = screen.getAllByRole("row").find((row) => row.textContent?.includes("Miembro hurlers"))!;
    const slayerRow = screen.getAllByRole("row").find((row) => row.textContent?.includes("Miembro slayer"))!;
    // The grant opens Shooting for the Axe Hurler and only for him.
    expect(within(hurlerRow).getByRole("checkbox", { name: shooting })).toBeInTheDocument();
    expect(within(slayerRow).queryByRole("checkbox", { name: shooting })).toBeNull();

    const shootingBox = within(hurlerRow).getByRole("checkbox", { name: shooting });
    await user.click(shootingBox);
    const other = within(hurlerRow).getAllByRole("checkbox").find((box) => box !== shootingBox)!;
    await user.click(other);
    await user.click(within(hurlerRow).getByRole("button", { name: es("ui.7290ecbbca36") }));

    const chosen = service.current()!.campaign.warriors.find((row) => row.id === "hurlers")!;
    expect(chosen.skill_access).toContain("shooting");
    expect(chosen.skill_access).toHaveLength(2);
    expect(service.current()!.campaign.post_battles[0].pending_advances![0]["promotion_setup_pending"]).toBe(false);

    // A list outside the printed set is refused, an available pair is accepted.
    const refused = await service.run("setPromotionSkillTables", { warrior_id: "slayer", tables: ["shooting", "speed"] });
    expect(refused.ok).toBe(false);
    const accepted = await service.run("setPromotionSkillTables", { warrior_id: "slayer", tables: ["combat", "strength"] });
    expect(accepted.ok, accepted.ok ? "" : accepted.message).toBe(true);
  });

  // -------------------------------------------------------------------------
  // 9. Localisation
  // -------------------------------------------------------------------------

  it("presents the same contracts in English", async () => {
    const service = await loadService(
      baseCampaign({ band: KAZ, configuration: DRAFT_CONFIG, current_state_number: 0, states: [], warriors: [warrior("noble", NOBLE)] }),
      reader,
    );
    renderRoute(service, reader, "en");
    const obligations = obligationsRegion("en");
    expect(within(obligations).getByText(NAMES.en.decision)).toBeInTheDocument();
    expect(obligations).toHaveTextContent(presentationOutput(translate({ key: "campaign.decision.pending" }, "en")));
    expect(obligations).not.toHaveTextContent(NAMES.es.decision);
    expect(obligations).not.toHaveTextContent(DECISION);
    expect(knowledgeName(reader, "profile", NOBLE, "en", undefined, KAZ)).toBe(NAMES.en.noble);
    expect(requiredMemberFacts(service.current()!, reader, "en")).toHaveLength(0);
  });
});

function unavailableText(locale: Locale) {
  return translate({ key: "knowledge.unavailable" }, locale);
}
