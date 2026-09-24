import { textNumber, textSymbol, type PresentationValue } from "./presentation-values";
import { localizedLabel } from "./presentation-enums";
import { useLocale } from "./i18n-context";
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
import { withOperationProgress } from "../common/operationProgressEvents";
import { isUiMessageKey, translate, type UiText } from "./i18n-core";

const CampaignServiceContext = createContext<{ service: CampaignAppService; locale: "es" | "en"; profileName?: (id: string) => PresentationValue } | null>(null);
const CAMPAIGN_ERROR_EVENT = "warband-manager:campaign-error";

type CampaignError = AppError | string | null;

function publishCampaignError(message: CampaignError): void {
  window.dispatchEvent(new CustomEvent<CampaignError>(CAMPAIGN_ERROR_EVENT, { detail: message }));
}

/** Closes transient UI that would otherwise hide a campaign action error. */
export function useCloseOnCampaignError(close: () => void): void {
  useEffect(() => {
    const onError = (event: Event) => {
      if ((event as CustomEvent<CampaignError>).detail) close();
    };
    window.addEventListener(CAMPAIGN_ERROR_EVENT, onError);
    return () => window.removeEventListener(CAMPAIGN_ERROR_EVENT, onError);
  }, [close]);
}

export function CampaignAppProvider({ service, locale: requestedLocale, profileName, children }: { service: CampaignAppService; locale?: "es" | "en"; profileName?: (id: string) => PresentationValue; children: ReactNode }) {
  const locale = useLocale(requestedLocale);
  return createElement(CampaignServiceContext.Provider, { value: { service, locale, profileName } }, children);
}

export interface CampaignAppView {
  /** Current document, or null before the first import. */
  document: CampaignDocument | null;
  /** Resolved display error of the last failed operation, if any. */
  error: PresentationValue | null;
  /** True when there are unexported campaign changes. */
  dirty: boolean;
  /** P5.2 acceptance: true while the real KB artefact is being fetched. */
  kbLoading: boolean;
  /** P5.2 acceptance: degraded-KB notice (fetch failed; fake data in use). */
  kbError: PresentationValue | null;
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

export function localizeErrorMessage(message: string, locale: "es" | "en", profileName: (id: string) => PresentationValue = () => translate({ key: "knowledge.unavailable" }, locale)): UiText {
  const exact = {
    "Roster or group limit reached for this recruit.": "error.legacy.36e60dfb0630",
    "Historical moments are read-only.": "error.legacy.53754a37f21a",
    "A name is required.": "error.legacy.54d33a418d04",
    "Recruit Heroes individually.": "error.legacy.4f971932f736",
    "Rejected import": "error.legacy.48eebb9caf47",
    "Export failed": "error.legacy.e94d3ee06ecf",
    "Rename rejected": "error.legacy.79a6db8edd2d",
    "Replace the currently loaded campaign? Unsaved changes will be lost.": "error.legacy.71789b2b20bb",
    "Resolve every serious injury and its follow-ups before continuing.": "error.legacy.543317eb1a9e",
    "Resolve experience, every advance and follow-up before continuing.": "error.legacy.c591f53512f0",
    "Resolve exploration and its follow-ups before continuing.": "error.legacy.de5882498313",
    "Resolve the wyrdstone sale before continuing.": "error.legacy.393ab60691b8",
    "Resolve veteran availability before continuing.": "error.legacy.e56902c7ac53",
    "Resolve every rare-search and Dramatis follow-up before continuing.": "error.legacy.049111df5fae",
    "Resolve all pending post-battle follow-ups first.": "error.legacy.1973fff6b5df",
    "Confirm the next state from the review after resolving equipment obligations.": "error.legacy.76f63aceedef",
    "This warrior cannot wear armour, shields or bucklers.": "error.legacy.07e68a229f30",
    "There is no pending post-battle sequence.": "error.legacy.635a6eccbfb8",
    "The post-battle sequence is already finished.": "error.legacy.b17a68e78a84",
    "Trading is only available during post-battle.": "error.legacy.0403834aa8b6",
    "Draft stash is only available during initial creation.": "error.legacy.7eeba1efa74a",
    "Only a draft can be composed.": "error.legacy.6580fe8e087e",
    "Only draft warriors can buy creation equipment.": "error.legacy.8165e540f20b",
    "Only a draft can remove creation equipment.": "error.legacy.bb855f4af360",
    "Buy through the draft equipment panel; trading opens after the warband is committed.": "error.legacy.8a8aa694ffcf",
    "Purchase quantity must be a positive integer.": "error.legacy.51ced59e1ebe",
    "Removal quantity must be a positive integer.": "error.legacy.e46671ad3091",
    "Sale quantity must be a positive integer.": "error.legacy.c9ce56e58cff",
    "Assignment quantity must be a positive integer.": "error.legacy.0d659171e3d1",
    "Row quantity must be positive.": "error.legacy.93718c460bc9",
    "Composition batch needs at least one row.": "error.legacy.d4075b826dea",
    "The warband needs at least one hero to commit.": "error.legacy.17323f5b2777",
    "The draft exceeds the starting treasury.": "error.legacy.4f8f65f5a998",
    "The draft is not legal.": "error.legacy.f274f0b4246d",
    "Result must be win, loss or draw.": "error.legacy.fac17b4497bf",
    "An opponent is required.": "error.legacy.44a932989b7b",
    "Battle numbers must be non-negative.": "error.legacy.af14f32d2c43",
    "Battle numbers must be unique.": "error.legacy.26d18b6bbfcc",
    "Post-battle records must have unique battle numbers.": "error.legacy.fc89f064d9cf",
    "Hired Swords do not take advances.": "error.legacy.c858cc85794d",
    "Only weapons can receive this upgrade.": "error.legacy.f6642fa9c998",
    "The selected base weapon is not available in the stash.": "error.legacy.f447150961a5",
    "Resolve a valid creation price before buying this item.": "error.legacy.2fbca0697570",
    "Resolve variable price before buying.": "error.legacy.0be17e27c686",
    "Resolve the hiring fee before hiring.": "error.legacy.16e5d1b15db4",
    "Not enough wyrdstone shards for this hire.": "error.legacy.24fda479059c",
    "Not enough declared hiring resources.": "error.legacy.81062f0be2e3",
    "This transferable equipment is not available.": "error.legacy.9d7e82eaa482",
    "Source and destination are the same warrior.": "error.legacy.22d03256b346",
  } as const;
  if (Object.hasOwn(exact, message)) return translate({ key: exact[message as keyof typeof exact] }, locale);
  
  let match = message.match(/^(.+): Rejected import$/);
  if (match) return translate({ key: "ui.95b83565ade4" }, locale);
  match = message.match(/^(.+): Invalid campaign$/);
  if (match) return translate({ key: "error.import-invalid" }, locale);
  match = message.match(/^Roster limit reached \((\d+)\/(\d+)\)\.$/);
  if (match) return translate({ key: "error.roster-limit", args: { count: Number(match[1]), limit: Number(match[2]) } }, locale);
  match = message.match(/^Cannot exceed (\d+) heroes\.$/);
  if (match) return translate({ key: "error.hero-limit", args: { limit: Number(match[1]) } }, locale);
  match = message.match(/^Cannot exceed (\d+) warband members\.$/);
  if (match) return translate({ key: "error.member-limit", args: { limit: Number(match[1]) } }, locale);
  match = message.match(/^Not enough gold: (\d+) gc needed, (\d+) (?:gc )?available\.$/);
  if (match) return translate({ key: "error.gold-balance", args: { amount: Number(match[1]), count: Number(match[2]) } }, locale);
  match = message.match(/^Not enough gold: (\d+) gc needed\.$/);
  if (match) return translate({ key: "error.gold-needed", args: { amount: Number(match[1]) } }, locale);
  match = message.match(/^Not enough (wyrdstone shard\(s\)|treasure\(s\)|campaign point\(s\)): (\d+) needed, (\d+) available\.$/);
  if (match) {
    const resource = { "wyrdstone shard(s)": "wyrdstone_fragments", "treasure(s)": "treasures", "campaign point(s)": "campaign_points" }[match[1]];
    return translate({ key: "error.resource-balance", args: { resource: localizedLabel(resource, locale), amount: Number(match[2]), count: Number(match[3]) } }, locale);
  }
  match = message.match(/^(.+) holds at most (\d+) members\.$/);
  if (match) return translate({ key: "error.group-limit", args: { limit: Number(match[2]) } }, locale);
  match = message.match(/^Profile "(.+)" is not available to this warband\.$/);
  if (match) return translate({ key: "error.profile-unavailable", args: { name: profileName(match[1]) } }, locale);
  match = message.match(/^Groups of "(.+)" hold at most (\d+) models\.$/);
  if (match) return translate({ key: "error.profile-group-limit", args: { name: profileName(match[1]), limit: Number(match[2]) } }, locale);
  match = message.match(/^Roster limit for "(.+)" is (\d+) models\.$/);
  if (match) return translate({ key: "error.profile-roster-limit", args: { name: profileName(match[1]), limit: Number(match[2]) } }, locale);
  match = message.match(/^Only (\d+) unassigned copy\/copies are available\.$/);
  if (match) return translate({ key: "error.copies", args: { count: Number(match[1]) } }, locale);
  match = message.match(/^Invalid (?:price|upgrade price): (.+)\.$/);
  if (match) return translate({ key: "error.price" }, locale);
  match = message.match(/^(.+) already has this upgrade\.$/);
  if (match) return translate({ key: "error.upgrade-known" }, locale);
  match = message.match(/^(.+) already knows "(.+)"\.$/);
  if (match) return translate({ key: "error.skill-known" }, locale);
  match = message.match(/^(.+) is not missing any games\.$/);
  if (match) return translate({ key: "error.not-absent" }, locale);
  if (/^No pending\b|^There is no pending\b/.test(message)) return translate({ key: "error.no-pending" }, locale);
  if (/^Resolve\b|^Complete\b/.test(message)) return translate({ key: "error.previous-step" }, locale);
  if (/^Choose\b|^Select\b|^Enter\b|^Use a valid\b/.test(message)) return translate({ key: "error.selection" }, locale);
  if (/already been|has already/i.test(message)) return translate({ key: "error.already-resolved" }, locale);
  return translate({ key: "error.action-failed" }, locale);
}

function messageOf(err: AppError, locale: "es" | "en", profileName?: (id: string) => PresentationValue): UiText {
  if (isUiMessageKey(err.message_key)) {
    return translate({ key: err.message_key }, locale);
  }
  const detail = err.detail as Record<string, unknown> | undefined;
  const fileReason = detail?.file_reason;
  const version = typeof detail?.found_version === "number" && Number.isSafeInteger(detail.found_version) ? textNumber(detail.found_version, locale) : textSymbol("—");
  if (fileReason === "retired_version") {
    return translate({ key: "error.retired-version", args: { version } }, locale);
  }
  if (fileReason === "unsupported_version") {
    return translate({ key: "error.unsupported-version", args: { version } }, locale);
  }
  if (fileReason === "invalid_json") {
    return translate({ key: "ui.3dd48426cd7a" }, locale);
  }
  if (fileReason === "bad_marker") {
    return translate({ key: "ui.36333fc93e4b" }, locale);
  }
  if (fileReason === "schema_violation") {
    return translate({ key: "ui.95b83565ade4" }, locale);
  }
  return localizeErrorMessage(err.message, locale, profileName);
}

export function useCampaignApp(service?: CampaignAppService): CampaignAppView {
  const shared = useContext(CampaignServiceContext);
  service ??= shared?.service;
  const locale = useLocale(shared?.locale);
  const profileName = shared?.profileName;
  // P5.2 acceptance: when no service is injected, start on the synchronous
  // fake-composed service (tests and first paint) and upgrade to the real
  // KB reader once the artefact fetch resolves. A load failure surfaces
  // through the error seam; the fake stays active so the app degrades
  // gracefully (the artefact-shaped fake covers the same surfaces).
  const [upgraded, setUpgraded] = useState<CampaignAppService | null>(null);
  const [kbLoading, setKbLoading] = useState(!service);
  const [kbFailed, setKbFailed] = useState(false);
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
      .catch(() => {
        if (!cancelled) {
          setKbLoading(false);
          // A degraded KB is a status notice, not a user-action error: it
          // must never compete with import/operation alerts in the seam.
          setKbFailed(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [service]);
  const app = upgraded ?? fallback;
  const [document, setDocument] = useState<CampaignDocument | null>(() => app.current());
  const [error, setError] = useState<CampaignError>(null);
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
  useEffect(() => {
    const receive = (event: Event) => setError((event as CustomEvent<CampaignError>).detail);
    window.addEventListener(CAMPAIGN_ERROR_EVENT, receive);
    return () => window.removeEventListener(CAMPAIGN_ERROR_EVENT, receive);
  }, []);

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
        setError(result as AppError);
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
      setError(result as AppError);
    }
  }, [app]);

  const runAction = useCallback(
    async (action: string, input: Record<string, unknown>) => {
      const run = async () => { try {
        const result = await app.run(action, input);
        if (result.ok) {
          setDocument(result.document);
          setError(null);
          setDirty(app.isDirty());
          publishCampaignError(null);
          return true;
        }
        const message = result;
        setError(message);
        publishCampaignError(message);
        return false;
      } catch (cause) {
        const message = cause instanceof Error ? cause.message : String(cause);
        setError(message);
        publishCampaignError(message);
        return false;
      } };
      if (action === "saveBattleDraft") {
        await new Promise<void>((resolve) => setTimeout(resolve, 0));
        return run();
      }
      return withOperationProgress(run);
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
        setError(result);
      }
    },
    [app],
  );

  return {
    document,
    error: error === null ? null : typeof error === "string" ? localizeErrorMessage(error, locale, profileName) : messageOf(error, locale, profileName),
    dirty,
    kbLoading,
    kbError: kbFailed ? (translate({ key: "ui.5d3df48f8f3f" }, locale)) : null,
    importFile,
    confirmReplace,
    exportFile,
    runAction,
    selectMoment,
    clearError: () => setError(null),
  };
}
