import { useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import { useCampaignApp } from "./useCampaignApp";
import { presentationOutput } from "./presentation-output";
import { translate } from "./i18n-core";
import { useLocale } from "./i18n-context";
import { textJoin, textNumber, textSymbol, textDice, warriorPersonalName } from "./presentation-values";
import { KnowledgeHint } from "./KnowledgeHint";
import { NumberStepper } from "../common/NumberStepper";
import type { CampaignDocument } from "./types";
import {
  leaderFacts,
  mutationFactsFor,
  mutationPurchaseWindow,
  pendingDecisionFacts,
  recordedDecisionFacts,
  requiredMemberFacts,
  routPresentationFor,
  uniqueFindFacts,
  withdrawalAuditFacts,
} from "./campaign-obligations";

/**
 * T11: campaign obligations of the produced campaign contracts (T10).
 *
 * Every section reads the facts the domain resolves (creation decisions,
 * lifecycle clauses, succession, mutations, Rout facts, withdrawal audit, unique
 * finds) and dispatches the published command. No rule is reproduced here: the
 * interface phrases the published facts and the service keeps the authority, so
 * a refused action still reaches the shell's alert seam with its stable code.
 */
export function CampaignObligations({ document, knowledge, locale: requestedLocale }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader; readonly locale?: "es" | "en" }) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const [rolls, setRolls] = useState<Record<string, number>>({});
  const [successor, setSuccessor] = useState("");
  const [mutations, setMutations] = useState<Record<string, string>>({});

  const isDraft = document.campaign.configuration?.is_draft === true;
  const warriors = document.campaign.warriors ?? [];
  const postBattles = document.campaign.post_battles ?? [];
  const battles = document.campaign.battles ?? [];
  const pending = pendingDecisionFacts(document, knowledge, locale);
  const recorded = recordedDecisionFacts(document, knowledge, locale);
  const required = requiredMemberFacts(document, knowledge, locale);
  const leader = leaderFacts(document, knowledge, locale);
  const pendingBattle = postBattles.find((row) => !row.complete)?.battle_number;
  const battleNumber = pendingBattle ?? battles.at(-1)?.number;
  const rout = battleNumber === undefined ? null : routPresentationFor(document, knowledge, locale, battleNumber);
  const withdrawals = withdrawalAuditFacts(document, locale);
  const unique = uniqueFindFacts(document, knowledge, locale);
  const mutationWindow = mutationPurchaseWindow(document);
  const mutationRows = mutationWindow
    ? warriors.map((warrior) => ({ warrior, facts: mutationFactsFor(document, knowledge, warrior.id, locale) })).filter((row) => row.facts !== null)
    : [];

  const t = ({
    heading: translate({ key: "campaign.lifecycle.heading" }, locale),
    recruit: translate({ key: "campaign.lifecycle.recruit" }, locale),
    pendingDecision: translate({ key: "campaign.decision.pending" }, locale),
    rollLabel: translate({ key: "campaign.decision.roll-label" }, locale),
    record: translate({ key: "campaign.decision.record" }, locale),
    nothingPending: translate({ key: "campaign.decision.none" }, locale),
    recordedTitle: translate({ key: "campaign.decision.recorded" }, locale),
    decisionHint: translate({ key: "campaign.decision.hint" }, locale),
    leader: translate({ key: "campaign.succession.leader" }, locale),
    noLeader: translate({ key: "campaign.succession.none" }, locale),
    chooseSuccessor: translate({ key: "campaign.succession.choose" }, locale),
    confirmSuccession: translate({ key: "campaign.succession.confirm" }, locale),
    sourceLimit: translate({ key: "campaign.succession.source-limit" }, locale),
    mutations: translate({ key: "campaign.heading.mutations" }, locale),
    mutationList: translate({ key: "campaign.mutation.list" }, locale),
    buyMutation: translate({ key: "campaign.mutation.buy" }, locale),
    owned: translate({ key: "campaign.mutation.owned" }, locale),
    unpriced: translate({ key: "campaign.mutation.unpriced" }, locale),
    mutationWindow: translate({ key: "campaign.mutation.window" }, locale),
    noMutationRule: translate({ key: "campaign.mutation.none" }, locale),
    routHeading: translate({ key: "campaign.rout.heading" }, locale),
    routNone: translate({ key: "campaign.rout.none" }, locale),
    routCounted: translate({ key: "campaign.rout.counted-members" }, locale),
    routExempt: translate({ key: "campaign.rout.exempt" }, locale),
    routPending: translate({ key: "campaign.rout.pending" }, locale),
    withdrawalHeading: translate({ key: "campaign.withdrawal.heading" }, locale),
    withdrawalNone: translate({ key: "campaign.withdrawal.none" }, locale),
    withdrawalEvent: translate({ key: "campaign.withdrawal.event" }, locale),
    uniqueHeading: translate({ key: "campaign.unique.heading" }, locale),
    uniqueNone: translate({ key: "campaign.unique.none" }, locale),
    uniqueLegacy: translate({ key: "campaign.unique.legacy" }, locale),
  });

  return <section className="campaign-obligations" aria-label={presentationOutput(translate({ key: "campaign.obligations.title" }, locale))}>
    {(isDraft || recorded.length > 0) && <article aria-labelledby="campaign-decisions-title">
      <h3 id="campaign-decisions-title">{presentationOutput(translate({ key: "campaign.decision.heading" }, locale))}</h3>
      <p>{presentationOutput(t.decisionHint)}</p>
      {pending.length === 0 ? <p role="status">{presentationOutput(t.nothingPending)}</p> : <ul className="obligation-list">{pending.map((decision) => {
        const roll = rolls[decision.id] ?? decision.dice.count;
        return <li key={decision.id}>
          <strong>{presentationOutput(decision.name)}</strong>
          <small role="status">{presentationOutput(t.pendingDecision)}</small>
          <KnowledgeHint knowledge={knowledge} kind="rule" id={decision.ruleId} locale={locale} />
          <div className="obligation-row">
            <span>{presentationOutput(textJoin([t.rollLabel, textDice(decision.dice.count, decision.dice.sides, locale)], " · "))}</span>
            <NumberStepper locale={locale} label={translate({ key: "campaign.decision.roll-label" }, locale)} value={roll} min={decision.dice.count} max={decision.dice.count * decision.dice.sides} onChange={(value) => setRolls((current) => ({ ...current, [decision.id]: value }))} />
            <button type="button" className="primary" onClick={() => void app.runAction("resolveCreationDecision", { decision_id: decision.id, roll })}>{presentationOutput(t.record)}</button>
          </div>
        </li>;
      })}</ul>}
      {recorded.length > 0 && <><h4>{presentationOutput(t.recordedTitle)}</h4><ul className="obligation-list">{recorded.map((entry) => <li key={entry.id}>{presentationOutput(translate({ key: "campaign.decision.resolved", args: { name: entry.name, roll: entry.roll, outcome: entry.outcome } }, locale))}</li>)}</ul></>}
    </article>}

    {required.length > 0 && <article aria-labelledby="campaign-lifecycle-title">
      <h3 id="campaign-lifecycle-title">{presentationOutput(t.heading)}</h3>
      <ul className="obligation-list">{required.map((clause) => <li key={clause.clauseId}>
        <strong>{presentationOutput(clause.clauseName)}</strong>
        <KnowledgeHint knowledge={knowledge} kind="rule" id={clause.ruleId} locale={locale} />
        <ul>{clause.profiles.map((profile) => <li key={profile.id}><span>{presentationOutput(profile.name)}</span>{pendingBattle !== undefined && <button type="button" onClick={() => void app.runAction("recruitBandProfile", { profile_id: profile.id, quantity: 1, locale })}>{presentationOutput(t.recruit)}</button>}</li>)}</ul>
      </li>)}</ul>
    </article>}

    {(leader.leader !== null || leader.pending !== null) && <article aria-labelledby="campaign-succession-title">
      <h3 id="campaign-succession-title">{presentationOutput(translate({ key: "campaign.succession.heading" }, locale))}</h3>
      {leader.leader && <p role="status">{presentationOutput(textJoin([t.leader, textSymbol(":"), leader.leader.name], " "))}</p>}
      {leader.pending && <>
        <p role="status">{presentationOutput(textJoin([t.noLeader, textSymbol("·"), leader.pending.clauseName], " "))}</p>
        <KnowledgeHint knowledge={knowledge} kind="rule" id={leader.pending.ruleId} locale={locale} />
        {leader.pending.candidates.length > 0 && <fieldset className="obligation-choice"><legend>{presentationOutput(t.chooseSuccessor)}</legend>{leader.pending.candidates.map((candidate) => <label key={candidate.id}><input type="radio" name="successor" value={candidate.id} checked={successor === candidate.id} onChange={(event) => setSuccessor(event.target.value)} /><span>{presentationOutput(candidate.name)}</span></label>)}</fieldset>}
        <button type="button" className="primary" disabled={leader.pending.candidates.length > 1 && !successor} data-disabled-reason={leader.pending.candidates.length > 1 && !successor ? presentationOutput(t.chooseSuccessor) : undefined} onClick={() => void app.runAction("succeedLeader", successor ? { clause_id: leader.pending!.clauseId, successor_warrior_id: successor } : { clause_id: leader.pending!.clauseId })}>{presentationOutput(t.confirmSuccession)}</button>
        {leader.sourceLimit && <p role="status">{presentationOutput(t.sourceLimit)}</p>}
      </>}
    </article>}

    {mutationWindow && <article aria-labelledby="campaign-mutations-title">
      <h3 id="campaign-mutations-title">{presentationOutput(t.mutations)}</h3>
      {mutationRows.length === 0 ? <p role="status">{presentationOutput(t.noMutationRule)}</p> : <ul className="obligation-list">{mutationRows.map(({ warrior, facts }) => {
        const row = facts!;
        const choice = mutations[warrior.id] ?? "";
        const offer = row.offers.find((candidate) => candidate.id === choice);
        return <li key={warrior.id}>
          <strong>{presentationOutput(warriorPersonalName(warrior, locale))}</strong>
          <KnowledgeHint knowledge={knowledge} kind="rule" id={row.ruleId} locale={locale} />
          {row.offers.filter((candidate) => !candidate.owned).length === 0 ? <p role="status">{presentationOutput(t.owned)}</p> : <div className="obligation-row">
            <label>{presentationOutput(t.mutationList)}<select value={choice} onChange={(event) => setMutations((current) => ({ ...current, [warrior.id]: event.target.value }))}><option value="">{presentationOutput(t.mutationList)}</option>{row.offers.filter((candidate) => !candidate.owned).map((candidate) => <option key={candidate.id} value={candidate.id}>{presentationOutput(candidate.price === null ? candidate.name : textJoin([candidate.name, textJoin([textNumber(candidate.price, locale), translate({ key: "unit.gold" }, locale)], " ")], " · "))}</option>)}</select></label>
            <button type="button" className="primary" disabled={!offer} data-disabled-reason={!offer ? presentationOutput(t.mutationList) : undefined} onClick={() => offer && void app.runAction("buyMutation", { warrior_id: warrior.id, mutation_id: offer.id })}>{presentationOutput(offer && offer.price !== null ? textJoin([t.buyMutation, textJoin([textNumber(offer.price, locale), translate({ key: "unit.gold" }, locale)], " ")], " · ") : t.buyMutation)}</button>
          </div>}
          {row.unpricedCount > 0 && <p role="status">{presentationOutput(t.unpriced)}</p>}
        </li>;
      })}</ul>}
      {!isDraft && pendingBattle === undefined && <p role="status">{presentationOutput(t.mutationWindow)}</p>}
    </article>}

    {rout ? <article aria-labelledby="campaign-rout-title">
      <h3 id="campaign-rout-title">{presentationOutput(t.routHeading)}</h3>
      <p role="status">{presentationOutput(translate({ key: "campaign.rout.summary", args: { models: rout.models, counted: rout.countedModels } }, locale))}</p>
      <h4>{presentationOutput(t.routCounted)}</h4>
      <ul className="obligation-list">{rout.members.filter((member) => member.countedModels > 0).map((member) => <li key={member.warriorId}>{presentationOutput(translate({ key: "campaign.rout.member", args: { name: member.name, counted: member.countedModels } }, locale))}</li>)}</ul>
      {rout.members.some((member) => member.exempt) && <><h4>{presentationOutput(t.routExempt)}</h4><ul className="obligation-list">{rout.members.filter((member) => member.exempt).map((member) => <li key={member.warriorId}>{presentationOutput(textJoin([member.name, member.profileName ?? translate({ key: "knowledge.unavailable" }, locale), textNumber(member.quantity, locale)], " · "))}</li>)}</ul></>}
      <p role="status">{presentationOutput(t.routPending)}</p>
    </article> : <article aria-labelledby="campaign-rout-title"><h3 id="campaign-rout-title">{presentationOutput(t.routHeading)}</h3><p role="status">{presentationOutput(t.routNone)}</p></article>}

    <article aria-labelledby="campaign-withdrawals-title">
      <h3 id="campaign-withdrawals-title">{presentationOutput(t.withdrawalHeading)}</h3>
      {withdrawals.length === 0 ? <p role="status">{presentationOutput(t.withdrawalNone)}</p> : <ul className="obligation-list">{withdrawals.map((entry) => <li key={entry.order}>
        <strong>{presentationOutput(translate({ key: "campaign.withdrawal.entry", args: { order: entry.order, members: textJoin(entry.members.map((member) => translate({ key: "campaign.withdrawal.member", args: { name: member.name, quantity: member.quantity } }, locale)), ", ") } }, locale))}</strong>
        <small>{presentationOutput(entry.battleNumber === null ? t.withdrawalEvent : textJoin([t.withdrawalEvent, textSymbol("#"), textNumber(entry.battleNumber, locale)], " "))}</small>
      </li>)}</ul>}
    </article>

    <article aria-labelledby="campaign-unique-title">
      <h3 id="campaign-unique-title">{presentationOutput(t.uniqueHeading)}</h3>
      {unique.length === 0 ? <p role="status">{presentationOutput(t.uniqueNone)}</p> : <ul className="obligation-list">{unique.map((finding) => <li key={finding.id}>
        {presentationOutput(translate({ key: "campaign.unique.entry", args: { name: finding.name, owned: finding.owned, stash: finding.stash } }, locale))}
        {finding.legacyOnly && <small> {presentationOutput(t.uniqueLegacy)}</small>}
      </li>)}</ul>}
    </article>
  </section>;
}
