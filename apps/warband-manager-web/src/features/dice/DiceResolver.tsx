import { presentationOutput, type PresentationText } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol, textDice } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import { useEffect, useState, type ReactElement } from "react";
import { NumberStepper } from "../common/NumberStepper";

export function DiceResolver({ count, sides, label, onResolve, locale: requestedLocale, disabled=false }: { count: number; sides: number; label: PresentationText | ReactElement; onResolve: (dice: number[]) => void; locale?:"es"|"en"; disabled?: boolean }) {
  const locale = useLocale(requestedLocale);
  const [mode, setMode] = useState<"auto" | "manual">("auto");
  const [values, setValues] = useState<number[]>(Array.from({ length: count }, () => 1));
  const [result, setResult] = useState<number[] | null>(null);
  useEffect(() => {
    setValues(Array.from({ length: count }, () => 1));
    setResult(null);
  }, [count, sides, label]);
  const t=({ auto: translate({ key: "ui.6e784e37bee3" }, locale), manual: translate({ key: "ui.cb60670695ad" }, locale), roll: translate({ key: "ui.5bd1be157cde" }, locale), die: translate({ key: "ui.3db4955b00c6" }, locale), use: translate({ key: "ui.2666189b5f03" }, locale), result: translate({ key: "ui.0a91171a8d9f" }, locale) });
  const resolve = (dice: number[]) => { setResult(dice); onResolve(dice); };
  return <div className="dice-resolver"><strong>{typeof label === "string" ? presentationOutput(label) : label}</strong><div className="tabs"><button type="button" disabled={disabled} className={mode === "auto" ? "active" : ""} onClick={() => setMode("auto")}>{presentationOutput(t.auto)}</button><button type="button" disabled={disabled} className={mode === "manual" ? "active" : ""} onClick={() => setMode("manual")}>{presentationOutput(t.manual)}</button></div>
    {mode === "auto" ? <button type="button" disabled={disabled} className="primary" onClick={() => resolve(Array.from({ length: count }, () => Math.floor(Math.random() * sides) + 1))}>{presentationOutput(textJoin([t.roll, textJoin([textNumber(count, locale), textDice(1, sides, locale)], "")]))}</button> : <div className="manual-dice">{values.map((value, index) => <div className="warrior-control-row" key={index}><span>{presentationOutput(textJoin([t.die, textNumber(index + 1, locale)]))}</span><NumberStepper locale={locale} label={textJoin([translate({ key: "number.die" }, locale), textNumber(index + 1, locale)])} value={value} min={1} max={sides} onChange={(next) => setValues((current) => current.map((item, position) => position === index ? next : item))}/></div>)}<button type="button" className="primary" disabled={disabled || values.some((value) => !Number.isInteger(value) || value < 1 || value > sides)} data-disabled-reason={values.some((value) => !Number.isInteger(value) || value < 1 || value > sides) ? presentationOutput(translate({ key: "dice.invalid", args: { sides } }, locale)) : undefined} onClick={() => resolve(values)}>{presentationOutput(t.use)}</button></div>}
    {result && <output role="status">{presentationOutput(textJoin([textJoin([t.result, textSymbol(":")], ""), textJoin(result.map((value) => textNumber(value, locale)), ", ")]))}</output>}</div>;
}
