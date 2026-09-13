export function NumberStepper({ value, onChange, min = 0, max = Infinity, label, disabled = false }: { value: number; onChange: (value: number) => void; min?: number; max?: number; label: string; disabled?: boolean }) {
  const set = (next: number) => onChange(Math.min(max, Math.max(min, Math.trunc(next))));
  return <span className="number-stepper"><button className="stepper-button" type="button" aria-label={`${label} −`} disabled={disabled || value <= min} onClick={() => set(value - 1)}>−</button><output aria-label={label}>{value}</output><button className="stepper-button" type="button" aria-label={`${label} +`} disabled={disabled || value >= max} onClick={() => set(value + 1)}>+</button></span>;
}
