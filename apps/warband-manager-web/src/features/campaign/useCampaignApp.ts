/**
 * P5.2 vertical slice: React wiring of the P5.1 application service.
 * This is the only place the shell touches service internals; components
 * consume the hook and stay presentational.
 *
 * No browser storage: campaign text comes from a File input, export goes
 * out through a Blob download on explicit user action.
 */

import { createContext, createElement, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

import type {
  AppError,
  CampaignDocument,
  CampaignAppService,
  ExportPayload,
  MomentSelection,
} from "./types";
import { createDefaultDeps, createDefaultDepsAsync } from "./default-deps";

const CampaignServiceContext = createContext<CampaignAppService | null>(null);

export function CampaignAppProvider({ service, children }: { service: CampaignAppService; children: ReactNode }) {
  return createElement(CampaignServiceContext.Provider, { value: service }, children);
}

export interface CampaignAppView {
  /** Current document, or null before the first import. */
  document: CampaignDocument | null;
  /** Resolved display error of the last failed operation, if any. */
  error: string | null;
  /** True when there are unexported campaign changes. */
  dirty: boolean;
  /** P5.2 acceptance: true while the real KB artefact is being fetched. */
  kbLoading: boolean;
  /** P5.2 acceptance: degraded-KB notice (fetch failed; fake data in use). */
  kbError: string | null;
  importFile(file: File): Promise<void>;
  confirmReplace(): Promise<void>;
  exportFile(): Promise<void>;
  runAction(action: string, input: Record<string, unknown>): Promise<boolean>;
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
  const sharedService = useContext(CampaignServiceContext);
  service ??= sharedService ?? undefined;
  // P5.2 acceptance: when no service is injected, start on the synchronous
  // fake-composed service (tests and first paint) and upgrade to the real
  // KB reader once the artefact fetch resolves. A load failure surfaces
  // through the error seam; the fake stays active so the app degrades
  // gracefully (the artefact-shaped fake covers the same surfaces).
  const [upgraded, setUpgraded] = useState<CampaignAppService | null>(null);
  const [kbLoading, setKbLoading] = useState(!service);
  const [kbError, setKbError] = useState<string | null>(null);
  const fallback = useMemo(() => service ?? createDefaultDeps(), [service]);
  useEffect(() => {
    if (service) return; // injected service: nothing to upgrade
    let cancelled = false;
    createDefaultDepsAsync()
      .then((real) => {
        if (!cancelled) {
          setUpgraded(real);
          setKbLoading(false);
        }
      })
      .catch((cause: Error) => {
        if (!cancelled) {
          setKbLoading(false);
          // A degraded KB is a status notice, not a user-action error: it
          // must never compete with import/operation alerts in the seam.
          setKbError(`Knowledge base failed to load — running with the built-in sample data. (${cause.message})`);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [service]);
  const app = upgraded ?? fallback;
  const [document, setDocument] = useState<CampaignDocument | null>(() => app.current());
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(() => app.isDirty());
  const pendingFile = useRef<File | null>(null);

  useEffect(() => {
    // A different session is a different service instance. Refresh immediately;
    // otherwise the previous campaign remains visible until the new one emits.
    setDocument(app.current());
    setDirty(app.isDirty());
    setError(null);
    return app.subscribe?.(() => {
      setDocument(app.current());
      setDirty(app.isDirty());
    });
  }, [app]);

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
      try {
        const result = await app.run(action, input);
        if (result.ok) {
          setDocument(result.document);
          setError(null);
          setDirty(app.isDirty());
          return true;
        }
        setError(messageOf(result));
        return false;
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : String(cause));
        return false;
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
    kbLoading,
    kbError,
    importFile,
    confirmReplace,
    exportFile,
    runAction,
    selectMoment,
    clearError: () => setError(null),
  };
}
