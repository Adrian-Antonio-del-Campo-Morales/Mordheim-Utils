import { useEffect, useState, type ReactNode } from "react";
import { NumberStepper } from "../common/NumberStepper";

export function DiceResolver({ count, sides, label, onResolve, locale="en", disabled=false }: { count: number; sides: number; label: ReactNode; onResolve: (dice: number[]) => void; locale?:"es"|"en"; disabled?: boolean }) {
  const [mode, setMode] = useState<"auto" | "manual">("auto");
  const [values, setValues] = useState<number[]>(Array.from({ length: count }, () => 1));
  const [result, setResult] = useState<number[] | null>(null);
  useEffect(() => {
    setValues(Array.from({ length: count }, () => 1));
    setResult(null);
  }, [count, sides, label]);
  const t=locale==="es"?{auto:"Tirar en la Aplicación",manual:"Introducir Dados Físicos",roll:"Tirar",die:"Dado",use:"Usar Resultado",result:"Resultado"}:{auto:"Roll in App",manual:"Enter Physical Dice",roll:"Roll",die:"Die",use:"Use Result",result:"Result"};
  const resolve = (dice: number[]) => { setResult(dice); onResolve(dice); };
  return <div className="dice-resolver"><strong>{label}</strong><div className="tabs"><button disabled={disabled} className={mode === "auto" ? "active" : ""} onClick={() => setMode("auto")}>{t.auto}</button><button disabled={disabled} className={mode === "manual" ? "active" : ""} onClick={() => setMode("manual")}>{t.manual}</button></div>
    {mode === "auto" ? <button disabled={disabled} className="primary" onClick={() => resolve(Array.from({ length: count }, () => Math.floor(Math.random() * sides) + 1))}>{t.roll} {count}D{sides}</button> : <div className="manual-dice">{values.map((value, index) => <div className="warrior-control-row" key={index}><span>{t.die} {index + 1}</span><NumberStepper label={`${t.die} ${index + 1}`} value={value} min={1} max={sides} onChange={(next) => setValues((current) => current.map((item, position) => position === index ? next : item))}/></div>)}<button className="primary" disabled={disabled || values.some((value) => !Number.isInteger(value) || value < 1 || value > sides)} data-disabled-reason={values.some((value) => !Number.isInteger(value) || value < 1 || value > sides) ? (locale === "es" ? `Cada dado debe tener un valor entre 1 y ${sides}.` : `Each die must have a value from 1 to ${sides}.`) : undefined} onClick={() => resolve(values)}>{t.use}</button></div>}
    {result && <output role="status">{t.result}: {result.join(", ")}</output>}</div>;
}
