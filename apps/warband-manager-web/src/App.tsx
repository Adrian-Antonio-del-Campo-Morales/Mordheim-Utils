// P5.2 vertical slice: import → display → edit → export.
// The shell renders the slice; campaign logic still lives in
// packages/typescript/{domain,application} via the feature's hook.
import { ProductApp } from "./ProductApp";

export function App() {
  return <ProductApp />;
}
