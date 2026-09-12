import { useEffect, useState, type ReactNode } from "react";

export function DiceResolver({ count, sides, label, onResolve, locale="en" }: { count: number; sides: number; label: ReactNode; onResolve: (dice: number[]) => void; locale?:"es"|"en" }) {
  const [mode, setMode] = useState<"auto" | "manual">("auto");
  const [values, setValues] = useState<number[]>(Array.from({ length: count }, () => 1));
  const [result, setResult] = useState<number[] | null>(null);
  useEffect(() => {
    setValues(Array.from({ length: count }, () => 1));
    setResult(null);
  }, [count, sides, label]);
  const t=locale==="es"?{auto:"Tirar en la Aplicación",manual:"Introducir Dados Físicos",roll:"Tirar",die:"Dado",use:"Usar Resultado",result:"Resultado"}:{auto:"Roll in App",manual:"Enter Physical Dice",roll:"Roll",die:"Die",use:"Use Result",result:"Result"};
  const resolve = (dice: number[]) => { setResult(dice); onResolve(dice); };
  return <div className="dice-resolver"><strong>{label}</strong><div className="tabs"><button className={mode === "auto" ? "active" : ""} onClick={() => setMode("auto")}>{t.auto}</button><button className={mode === "manual" ? "active" : ""} onClick={() => setMode("manual")}>{t.manual}</button></div>
    {mode === "auto" ? <button className="primary" onClick={() => resolve(Array.from({ length: count }, () => Math.floor(Math.random() * sides) + 1))}>{t.roll} {count}D{sides}</button> : <div className="manual-dice">{values.map((value, index) => <label key={index}>{t.die} {index + 1}<input type="number" min="1" max={sides} value={value} onChange={(event) => setValues((current) => current.map((item, position) => position === index ? Number(event.target.value) : item))} /></label>)}<button className="primary" disabled={values.some((value) => !Number.isInteger(value) || value < 1 || value > sides)} data-disabled-reason={values.some((value) => !Number.isInteger(value) || value < 1 || value > sides) ? (locale === "es" ? `Cada dado debe tener un valor entre 1 y ${sides}.` : `Each die must have a value from 1 to ${sides}.`) : undefined} onClick={() => resolve(values)}>{t.use}</button></div>}
    {result && <output role="status">{t.result}: {result.join(", ")}</output>}</div>;
}
