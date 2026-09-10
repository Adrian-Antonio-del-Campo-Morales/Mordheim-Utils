import { useState } from "react";

export function DiceResolver({ count, sides, label, onResolve }: { count: number; sides: number; label: string; onResolve: (dice: number[]) => void }) {
  const [mode, setMode] = useState<"auto" | "manual">("auto");
  const [values, setValues] = useState<number[]>(Array.from({ length: count }, () => 1));
  const [result, setResult] = useState<number[] | null>(null);
  const resolve = (dice: number[]) => { setResult(dice); onResolve(dice); };
  return <div className="dice-resolver"><strong>{label}</strong><div className="tabs"><button className={mode === "auto" ? "active" : ""} onClick={() => setMode("auto")}>Roll in app</button><button className={mode === "manual" ? "active" : ""} onClick={() => setMode("manual")}>Enter physical dice</button></div>
    {mode === "auto" ? <button className="primary" onClick={() => resolve(Array.from({ length: count }, () => Math.floor(Math.random() * sides) + 1))}>Roll {count}D{sides}</button> : <div className="manual-dice">{values.map((value, index) => <label key={index}>Die {index + 1}<input type="number" min="1" max={sides} value={value} onChange={(event) => setValues((current) => current.map((item, position) => position === index ? Number(event.target.value) : item))} /></label>)}<button className="primary" disabled={values.some((value) => !Number.isInteger(value) || value < 1 || value > sides)} onClick={() => resolve(values)}>Use result</button></div>}
    {result && <output role="status">Result: {result.join(", ")}</output>}</div>;
}
