import { presentationOutput, type PresentationText } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol } from "../campaign/presentation-values";
import { useLocale } from "../campaign/i18n-context";

export function NumberStepper({ value, onChange, min = 0, max = Infinity, label, disabled = false, locale: requestedLocale }: { value: number; onChange: (value: number) => void; min?: number; max?: number; label: PresentationText; disabled?: boolean; locale?: "es" | "en" }) {
  const locale = useLocale(requestedLocale);
  const set = (next: number) => onChange(Math.min(max, Math.max(min, Math.trunc(next))));
  return <span className="number-stepper"><button className="stepper-button" type="button" aria-label={presentationOutput(textJoin([label, textSymbol("−")]))} disabled={disabled || !Number.isFinite(value) || value <= min} onClick={() => set(value - 1)}>{presentationOutput(textSymbol("−"))}</button><output aria-label={presentationOutput(label)}>{presentationOutput(textNumber(value, locale))}</output><button className="stepper-button" type="button" aria-label={presentationOutput(textJoin([label, textSymbol("+")]))} disabled={disabled || !Number.isFinite(value) || value >= max} onClick={() => set(value + 1)}>{presentationOutput(textSymbol("+"))}</button></span>;
}
