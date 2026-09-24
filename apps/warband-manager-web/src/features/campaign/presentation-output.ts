import type { PresentationValue } from "./presentation-values";

/** Final extraction for text nodes, accessible attributes and readable exports. */
export type PresentationText = PresentationValue;
export function presentationOutput(value: PresentationText): string {
  return value;
}
