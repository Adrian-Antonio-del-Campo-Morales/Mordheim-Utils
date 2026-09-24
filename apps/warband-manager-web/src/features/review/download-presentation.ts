import { presentationOutput, type PresentationText } from "../campaign/presentation-output";

/** The filename identifies a download; only validated content enters its body. */
export function downloadPresentation(filename: string, content: PresentationText): void {
  const blob = new Blob([presentationOutput(content)], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
  } finally {
    URL.revokeObjectURL(url);
  }
}
