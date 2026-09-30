import { catalogueCharacteristic, catalogueJoin, catalogueLabel, catalogueNumber, type CatalogueLabel } from "@app/rules/catalogue-text";
import type { ReferenceEntry, ReferenceWarrior, WarbandReference } from "@app/rules/warband-reference";
import { unavailableText } from "@adapters/knowledge-reader/presentation";
import type { Locale } from "../campaign/i18n";
import { localizedLabel } from "../campaign/presentation-enums";
import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol } from "../campaign/presentation-values";
import { KnowledgeTextHint } from "../campaign/KnowledgeHint";
import { WarriorProfileSummary } from "../campaign/WarriorProfileSummary";
import { ExperienceTrack } from "../draft/DraftWorkspace";

const stats = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"] as const;
const skillCategories = ["combat", "shooting", "academic", "strength", "speed", "special"] as const;
const groupLabels: Readonly<Record<string, CatalogueLabel>> = { hero: "heroes", henchman: "henchmen", animal: "animal", summoned: "summoned" };
const kindLabels: Readonly<Record<string, CatalogueLabel>> = {
  "close-combat-weapon": "Close Combat Weapon", "ranged-weapon": "Ranged Weapon",
  "armour-defences": "armour-defences", "material-or-upgrade": "Material Or Upgrade",
};
const equipmentGroup = (kind: string) => kind === "armour" || kind === "shield-or-defence" ? "armour-defences"
  : kind === "combat-equipment" || kind === "out-of-scope" || kind === "trollheim-equipment" || !kind ? "equipment" : kind;

function EntryDetails({ entries }: { entries: readonly ReferenceEntry[] }) {
  return <div className="warband-entries">{entries.map((entry) => <details key={entry.id}>
    <summary>{presentationOutput(entry.name)}</summary><p className="rule-prose">{presentationOutput(entry.effect)}</p>
  </details>)}</div>;
}

export function WarbandReferenceTemplate({ sheet, locale }: { sheet: WarbandReference; locale: Locale }) {
  const label = (key: CatalogueLabel) => catalogueLabel(key, locale);
  const number = (value: unknown) => catalogueNumber(value) ?? unavailableText(locale);
  const money = (value: unknown) => catalogueJoin([number(value), label("crowns")]);
  const range = (minimum: unknown, maximum: unknown) => maximum === null
    ? catalogueJoin([number(minimum), label("no-profile-maximum")], " — ")
    : catalogueJoin([number(minimum), number(maximum)], " — ");
  const sections: readonly [string, CatalogueLabel, boolean][] = [
    ["composition", "composition", true], ["warriors", "warriors", sheet.warriors.length > 0],
    ["skills", "skills", sheet.warriors.some((warrior) => warrior.skillAccess.length > 0) || sheet.abilities.length > 0],
    ["equipment", "equipment", sheet.equipment.length > 0], ["rules", "band-special-rules", sheet.rules.length > 0],
    ["magic", "magic-prayers", sheet.magic.length > 0], ["variants", "variants", sheet.variants.length > 0],
    ["sources", "sources", sheet.sourceUrls.length > 0],
  ];
  const anchor = (section: string) => `warband-${sheet.id}-${section}`;
  const types = [...new Set(sheet.warriors.map((warrior) => warrior.type))];
  const groups = [...Object.keys(groupLabels).filter((type) => types.includes(type)), ...types.filter((type) => !Object.hasOwn(groupLabels, type))];
  const warriorCard = (warrior: ReferenceWarrior) => <section className="warband-warrior draft-warrior-card" key={warrior.id}>
    <WarriorProfileSummary locale={locale}
      identity={<header><div><h4>{presentationOutput(warrior.name)}</h4><span>{presentationOutput(catalogueJoin([label("recruitment"), warrior.maximum === 0 ? label("variant-only") : range(warrior.minimum, warrior.maximum)], ": "))}</span></div><span className="draft-card-cost"><b>{presentationOutput(money(warrior.cost))}</b></span></header>}
      stats={Object.fromEntries(stats.map((stat) => [stat, catalogueCharacteristic(stat, warrior.characteristics[stat], locale)]))}
      equipment={<><p>{presentationOutput(warrior.startingEquipment.length ? textJoin(warrior.startingEquipment, ", ") : label("starting-equipment-not-published"))}</p>{warrior.restrictions ? <p className="warband-equipment-note">{presentationOutput(warrior.restrictions === unavailableText(locale) ? label("restriction-text-missing") : warrior.restrictions)}</p> : null}</>}
      rules={<>{warrior.rules.map((rule) => <p key={rule.id}><KnowledgeTextHint name={rule.name} tooltip={rule.effect} locale={locale} /></p>)}{warrior.rules.length === 0 && <p>{presentationOutput(textSymbol("—"))}</p>}</>}
    />
    {Object.keys(warrior.groupSize).length > 0 && <dl className="warband-facts"><div><dt>{presentationOutput(label("group-size"))}</dt><dd>{presentationOutput(range(warrior.groupSize.minimum, warrior.groupSize.maximum))}</dd></div></dl>}
    <footer><div className="skill-access"><small>{presentationOutput(label("skill-table"))}</small><span>{presentationOutput(warrior.skillAccess.length ? textJoin(warrior.skillAccess.map((category) => localizedLabel(category, locale)), " · ") : textSymbol("—"))}</span></div>
      {typeof warrior.experience === "number" && Number.isFinite(warrior.experience) && (warrior.type === "hero" || warrior.type === "henchman")
        ? <ExperienceTrack experience={warrior.experience} kind={warrior.type} locale={locale} />
        : <div className="draft-experience"><span><small>{presentationOutput(label("experience"))}</small><b>{presentationOutput(number(warrior.experience))}</b></span></div>}
    </footer>
  </section>;
  return <>
    <h2>{presentationOutput(sheet.name)}</h2>
    <nav className="warband-index" aria-label={presentationOutput(label("warband-index"))}>{sections.filter(([, , present]) => present).map(([section, key]) => <a href={`#${anchor(section)}`} key={section}>{presentationOutput(label(key))}</a>)}</nav>
    <section id={anchor("composition")}><h3>{presentationOutput(label("composition"))}</h3>
      <dl className="warband-facts"><div><dt>{presentationOutput(label("starting-gold"))}</dt><dd>{presentationOutput(money(sheet.roster.starting_gold))}</dd></div>
        <div><dt>{presentationOutput(label("model-limits"))}</dt><dd>{presentationOutput(range(sheet.roster.minimum_models, sheet.roster.maximum_models))}</dd></div></dl>
      {sheet.warriors.length > 0 && <div className="warband-table"><table><caption>{presentationOutput(label("recruitment"))}</caption><thead><tr><th scope="col">{presentationOutput(label("warriors"))}</th><th scope="col">{presentationOutput(label("recruitment"))}</th><th scope="col">{presentationOutput(label("cost"))}</th><th scope="col">{presentationOutput(label("experience"))}</th></tr></thead>
        <tbody>{sheet.warriors.map((warrior) => <tr key={warrior.id}><th scope="row">{presentationOutput(warrior.name)}</th><td>{presentationOutput(warrior.maximum === 0 ? label("variant-only") : range(warrior.minimum, warrior.maximum))}</td><td>{presentationOutput(money(warrior.cost))}</td><td>{presentationOutput(number(warrior.experience))}</td></tr>)}</tbody></table></div>}
    </section>
    {sheet.warriors.length > 0 && <section id={anchor("warriors")}><h3>{presentationOutput(label("warriors"))}</h3>{groups.map((group) => <div key={group}><h4 className="warband-group-heading">{presentationOutput(label(groupLabels[group] ?? "other-warriors"))}</h4>{sheet.warriors.filter((warrior) => warrior.type === group).map(warriorCard)}</div>)}</section>}
    {(sheet.warriors.some((warrior) => warrior.skillAccess.length) || sheet.abilities.length > 0) && <section id={anchor("skills")}><h3>{presentationOutput(label("skills"))}</h3>
      <div className="warband-table"><table><caption>{presentationOutput(label("skill-table"))}</caption><thead><tr><th scope="col">{presentationOutput(label("warriors"))}</th>{skillCategories.map((category) => <th scope="col" key={category}>{presentationOutput(localizedLabel(category, locale))}</th>)}</tr></thead>
        <tbody>{sheet.warriors.filter((warrior) => warrior.skillAccess.length > 0).map((warrior) => <tr key={warrior.id}><th scope="row">{presentationOutput(warrior.name)}</th>{skillCategories.map((category) => <td key={category}>{presentationOutput(catalogueLabel(warrior.skillAccess.includes(category) ? "access-yes" : "access-no", locale))}</td>)}</tr>)}</tbody></table></div>
      {sheet.abilities.length > 0 && <details className="warband-skill-list"><summary>{presentationOutput(localizedLabel("special", locale))}</summary><EntryDetails entries={sheet.abilities} /></details>}
      {sheet.skills.map((group) => <details className="warband-skill-list" key={group.category}><summary>{presentationOutput(localizedLabel(group.category, locale))}</summary><EntryDetails entries={group.entries} /></details>)}
    </section>}
    {sheet.equipment.length > 0 && <section id={anchor("equipment")}><h3>{presentationOutput(label("equipment"))}</h3><p>{presentationOutput(label("equipment-access-note"))}</p>{sheet.equipment.map((list) => <section className="warband-equipment-list" key={list.id}>
      <h4>{presentationOutput(list.complete ? list.name : label("recruitment-equipment"))}</h4>
      {list.notes ? <p className="warband-data-note">{presentationOutput(list.notes)}</p> : null}
      {!list.complete && <p className="warband-data-note">{presentationOutput(label("list-metadata-missing"))}</p>}
      {list.profiles.length > 0 && <p>{presentationOutput(textJoin([label("recipients"), textSymbol(":"), textJoin(list.profiles, ", ")]))}</p>}
      <div className="warband-equipment-grid">{[...new Set(list.items.map((item) => equipmentGroup(item.kind)))].map((kind) => <div className="warband-equipment-category" key={kind}><table><caption>{presentationOutput(label(kindLabels[kind] ?? "equipment"))}</caption><thead><tr><th scope="col">{presentationOutput(label("equipment"))}</th><th scope="col">{presentationOutput(label("cost"))}</th></tr></thead>
        <tbody>{list.items.filter((item) => equipmentGroup(item.kind) === kind).map((item, index) => <tr key={`${item.id}:${index}`}><td><KnowledgeTextHint name={item.name} tooltip={item.effect} locale={locale} />{item.notes ? <small className="warband-equipment-note">{presentationOutput(item.notes)}</small> : null}</td><td>{presentationOutput(money(item.cost))}</td></tr>)}</tbody></table></div>)}</div>
    </section>)}</section>}
    {sheet.rules.length > 0 && <section id={anchor("rules")}><h3>{presentationOutput(label("band-special-rules"))}</h3><EntryDetails entries={sheet.rules} /></section>}
    {sheet.magic.length > 0 && <section id={anchor("magic")}><h3>{presentationOutput(label("magic-prayers"))}</h3>{sheet.magic.map((lore) => <section key={lore.id}><h4>{presentationOutput(lore.name)}</h4><p>{presentationOutput(textJoin(lore.users, ", "))}</p>{lore.spells.map((spell) => <details key={spell.entry_id}><summary>{presentationOutput(spell.name)}</summary><p>{presentationOutput(catalogueJoin(spell.tags, " · "))}</p><p className="rule-prose">{presentationOutput(spell.effect)}</p></details>)}</section>)}</section>}
    {sheet.variants.length > 0 && <section id={anchor("variants")}><h3>{presentationOutput(label("variants"))}</h3>{sheet.variants.map((variant) => <section key={variant.id}><h4>{presentationOutput(variant.name)}</h4>
      {variant.gold !== undefined && <p>{presentationOutput(catalogueJoin([label("starting-gold"), money(variant.gold)], ": "))}</p>}
      {variant.members.map((member, index) => <p key={index}>{presentationOutput(catalogueJoin([member.name, range(member.minimum, member.maximum)], ": "))}</p>)}
      {variant.lists.length > 0 && <p>{presentationOutput(textJoin([label("equipment"), textSymbol(":"), textJoin(variant.lists, ", ")]))}</p>}
      {variant.bonuses.map((bonus, index) => <div key={index}><h5>{presentationOutput(bonus.name)}</h5><dl className="warband-facts">{Object.entries(bonus.characteristics).map(([stat, value]) => <div key={stat}><dt>{presentationOutput(localizedLabel(stat, locale))}</dt><dd>{presentationOutput(catalogueCharacteristic(stat, value, locale))}</dd></div>)}</dl></div>)}
      <EntryDetails entries={variant.rules} />
    </section>)}</section>}
    {sheet.sourceUrls.length > 0 && <section id={anchor("sources")}><h3>{presentationOutput(label("sources"))}</h3><ul>{sheet.sourceUrls.map((url, index) => <li key={url}><a href={url} target="_blank" rel="noreferrer">{presentationOutput(textJoin([label("sources"), textNumber(index + 1, locale)]))}</a></li>)}</ul></section>}
  </>;
}
