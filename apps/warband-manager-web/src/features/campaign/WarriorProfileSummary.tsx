import type { ReactNode } from "react";
import { translate, type Locale } from "./i18n-core";
import { localizedLabel } from "./presentation-enums";
import { presentationOutput, type PresentationText } from "./presentation-output";

/** Shared profile presentation for campaign warriors and the warband reference. */
export function WarriorProfileSummary({ identity, stats, equipment, rules, locale, children }: {
  identity: ReactNode;
  stats: Readonly<Record<string, PresentationText>>;
  equipment: ReactNode;
  rules: ReactNode;
  locale: Locale;
  children?: ReactNode;
}) {
  return <div className="draft-card-body">
    <section className="draft-card-identity">{identity}<div className="stats">{Object.entries(stats).map(([key, value]) => <span key={key}><small>{presentationOutput(localizedLabel(key, locale))}</small>{presentationOutput(value)}</span>)}</div></section>
    <section className="draft-card-box"><h4>{presentationOutput(translate({ key: "ui.c0081f2540bc" }, locale))}</h4>{equipment}</section>
    <section className="draft-card-box"><h4>{presentationOutput(translate({ key: "ui.bee89842c456" }, locale))}</h4>{rules}</section>
    {children}
  </div>;
}
