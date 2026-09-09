/**
 * P5.2 vertical slice: React wiring of the P5.1 application service.
 * This is the only place the shell touches service internals; components
 * consume the hook and stay presentational.
 *
 * No browser storage: campaign text comes from a File input, export goes
 * out through a Blob download on explicit user action.
 */

import { useCallback, useMemo, useRef, useState } from "react";

import type {
  AppError,
  CampaignDocument,
  CampaignAppService,
  ExportPayload,
  MomentSelection,
} from "./types";
import { createDefaultDeps } from "./default-deps";

export interface CampaignAppView {
  /** Current document, or null before the first import. */
  document: CampaignDocument | null;
  /** Resolved display error of the last failed operation, if any. */
  error: string | null;
  /** True when there are unexported campaign changes. */
  dirty: boolean;
  importFile(file: File): Promise<void>;
  confirmReplace(): Promise<void>;
  exportFile(): Promise<void>;
  runAction(action: string, input: Record<string, unknown>): Promise<void>;
  /** P6.1: move the timeline selection (never dirties the document). */
  selectMoment(moment: MomentSelection): void;
  clearError(): void;
}

/** Read File text with a FileReader fallback (some jsdom builds lack `.text()`). */
async function readFileText(file: File): Promise<string> {
  if (typeof file.text === "function") {
    return file.text();
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error ?? new Error("Could not read file"));
    reader.readAsText(file);
  });
}

function messageOf(err: AppError): string {
  const detail = err.detail as Record<string, unknown> | undefined;
  const fileReason = detail?.file_reason;
  if (fileReason === "retired_version") {
    return `This file uses an old format (version ${String(detail?.found_version)}). Only version 4 files are supported — re-save it with the desktop manager first.`;
  }
  if (fileReason === "unsupported_version") {
    return `This file uses format version ${String(detail?.found_version)}, which is newer than this application supports (4).`;
  }
  if (fileReason === "invalid_json") {
    return "This file is not valid JSON. Is it really a .mordheim campaign file?";
  }
  if (fileReason === "bad_marker") {
    return "This file is not a Mordheim campaign file (wrong marker).";
  }
  if (fileReason === "schema_violation") {
    const location = detail?.location ? ` (at ${String(detail.location)})` : "";
    return `This file violates the campaign format${location}: ${err.message}`;
  }
  return err.message;
}

export function useCampaignApp(service?: CampaignAppService): CampaignAppView {
  const app = useMemo(() => service ?? createDefaultDeps(), [service]);
  const [document, setDocument] = useState<CampaignDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const pendingFile = useRef<File | null>(null);

  const loadText = useCallback(
    async (text: string, confirm: boolean) => {
      const result = await app.importCampaign({ text, confirm_replace: confirm });
      if (result.ok) {
        setDocument(result.document);
        setError(null);
        setDirty(app.isDirty());
      } else if (!confirm && (result as AppError).reason === "already_loaded") {
        // Remember the file; the UI asks for confirmation and calls confirmReplace.
        setError("Replace the currently loaded campaign? Unsaved changes will be lost.");
      } else {
        setError(messageOf(result as AppError));
      }
    },
    [app],
  );

  const importFile = useCallback(
    async (file: File) => {
      pendingFile.current = file;
      const text = await readFileText(file);
      await loadText(text, false);
    },
    [loadText],
  );

  const confirmReplace = useCallback(async () => {
    const file = pendingFile.current;
    if (!file) return;
    const text = await readFileText(file);
    await loadText(text, true);
    pendingFile.current = null;
  }, [loadText]);

  const exportFile = useCallback(async () => {
    const result = (await app.exportCampaign()) as {
      ok: boolean;
      payload?: ExportPayload;
    } & Partial<AppError>;
    if (result.ok && result.payload) {
      const blob = new Blob([result.payload.text], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");
      anchor.href = url;
      anchor.download = result.payload.filename;
      anchor.click();
      URL.revokeObjectURL(url);
      setDirty(app.isDirty());
      setError(null);
    } else {
      setError(messageOf(result as AppError));
    }
  }, [app]);

  const runAction = useCallback(
    async (action: string, input: Record<string, unknown>) => {
      const result = await app.run(action, input);
      if (result.ok) {
        setDocument(result.document);
        setError(null);
        setDirty(app.isDirty());
      } else {
        setError(messageOf(result));
      }
    },
    [app],
  );

  // P6.1: view selection only — refreshes the document snapshot in state;
  // the service guarantees no campaign mutation and no dirty flag.
  const selectMoment = useCallback(
    (moment: MomentSelection) => {
      const result = app.selectMoment(moment);
      if (result.ok) {
        setDocument(result.document);
        setError(null);
        setDirty(app.isDirty());
      } else {
        setError(messageOf(result));
      }
    },
    [app],
  );

  return {
    document,
    error,
    dirty,
    importFile,
    confirmReplace,
    exportFile,
    runAction,
    selectMoment,
    clearError: () => setError(null),
  };
}
