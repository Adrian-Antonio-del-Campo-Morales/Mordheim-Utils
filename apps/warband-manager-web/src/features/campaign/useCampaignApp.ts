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
import { withOperationProgress } from "../common/OperationProgress";

const CampaignServiceContext = createContext<{ service: CampaignAppService; locale: "es" | "en" } | null>(null);
const CAMPAIGN_ERROR_EVENT = "warband-manager:campaign-error";

function publishCampaignError(message: string | null): void {
  window.dispatchEvent(new CustomEvent<string | null>(CAMPAIGN_ERROR_EVENT, { detail: message }));
}

export function CampaignAppProvider({ service, locale = "en", children }: { service: CampaignAppService; locale?: "es" | "en"; children: ReactNode }) {
  return createElement(CampaignServiceContext.Provider, { value: { service, locale } }, children);
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

export function localizeErrorMessage(message: string, locale: "es" | "en"): string {
  if (locale !== "es") return message;
  if (/^(Abre|Debes|El|Ella|Espera|Esta|Este|Introduce|La|Las|Los|No |Selecciona|Se |Ya )/.test(message)) return message;
  const exact: Record<string, string> = {
    "Roster or group limit reached for this recruit.": "Se ha alcanzado el límite permitido para este recluta o grupo.",
    "Historical moments are read-only.": "Los momentos históricos son de solo lectura.",
    "A name is required.": "Es obligatorio introducir un nombre.",
    "Recruit Heroes individually.": "Los Héroes deben contratarse individualmente.",
    "Rejected import": "No se pudo importar el archivo.",
    "Export failed": "No se pudo exportar la campaña.",
    "Rename rejected": "No se pudo cambiar el nombre.",
    "Replace the currently loaded campaign? Unsaved changes will be lost.": "¿Quieres sustituir la campaña cargada? Se perderán los cambios sin exportar.",
    "Resolve every serious injury and its follow-ups before continuing.": "Falta resolver el paso «Heridas graves» y sus seguimientos.",
    "Resolve experience, every advance and follow-up before continuing.": "Falta resolver el paso «Experiencia y avances».",
    "Resolve exploration and its follow-ups before continuing.": "Falta resolver el paso «Exploración» y sus seguimientos.",
    "Resolve the wyrdstone sale before continuing.": "Falta resolver el paso «Venta de piedra bruja».",
    "Resolve veteran availability before continuing.": "Falta resolver el paso «Veteranos».",
    "Resolve every rare-search and Dramatis follow-up before continuing.": "Falta resolver el paso «Objetos raros y Dramatis».",
    "Resolve all pending post-battle follow-ups first.": "Falta resolver los seguimientos de postbatalla.",
    "Confirm the next state from the review after resolving equipment obligations.": "Falta resolver el paso «Equipo».",
    "This warrior cannot wear armour, shields or bucklers.": "Este guerrero no puede llevar armadura, escudo ni rodela.",
    "There is no pending post-battle sequence.": "No hay ninguna secuencia de postbatalla pendiente.",
    "The post-battle sequence is already finished.": "La secuencia de postbatalla ya está terminada.",
    "Trading is only available during post-battle.": "El comercio solo está disponible durante la postbatalla.",
    "Draft stash is only available during initial creation.": "La reserva de la banda solo está disponible durante la creación inicial.",
    "Only a draft can be composed.": "Solo se puede modificar una banda en creación.",
    "Only draft warriors can buy creation equipment.": "Solo los guerreros de una banda en creación pueden comprar equipo inicial.",
    "Only a draft can remove creation equipment.": "Solo se puede retirar equipo inicial de una banda en creación.",
    "Buy through the draft equipment panel; trading opens after the warband is committed.": "Compra desde el panel de equipo inicial; el comercio se abre al confirmar la banda.",
    "Purchase quantity must be a positive integer.": "La cantidad de compra debe ser un número entero positivo.",
    "Removal quantity must be a positive integer.": "La cantidad que se va a retirar debe ser un número entero positivo.",
    "Sale quantity must be a positive integer.": "La cantidad de venta debe ser un número entero positivo.",
    "Assignment quantity must be a positive integer.": "La cantidad que se va a asignar debe ser un número entero positivo.",
    "Row quantity must be positive.": "La cantidad de la fila debe ser positiva.",
    "Composition batch needs at least one row.": "La composición debe incluir al menos una fila.",
    "The warband needs at least one hero to commit.": "La banda necesita al menos un Héroe para confirmarse.",
    "The draft exceeds the starting treasury.": "La banda en creación supera el tesoro inicial.",
    "The draft is not legal.": "La banda en creación no es válida.",
    "Result must be win, loss or draw.": "El resultado debe ser victoria, derrota o empate.",
    "An opponent is required.": "Es obligatorio indicar un oponente.",
    "Battle numbers must be non-negative.": "Los números de batalla no pueden ser negativos.",
    "Battle numbers must be unique.": "Los números de batalla deben ser únicos.",
    "Post-battle records must have unique battle numbers.": "Los registros de postbatalla deben tener números de batalla únicos.",
    "Hired Swords do not take advances.": "Los Espadas de alquiler no reciben avances.",
    "Only weapons can receive this upgrade.": "Solo las armas pueden recibir esta mejora.",
    "The selected base weapon is not available in the stash.": "El arma base seleccionada no está disponible en la reserva.",
    "Resolve a valid creation price before buying this item.": "Indica un precio inicial válido antes de comprar este objeto.",
    "Resolve variable price before buying.": "Resuelve el precio variable antes de comprar.",
    "Resolve the hiring fee before hiring.": "Resuelve el coste de contratación antes de contratar.",
    "Not enough wyrdstone shards for this hire.": "No hay suficientes fragmentos de piedra bruja para esta contratación.",
    "Not enough declared hiring resources.": "No hay suficientes recursos para esta contratación.",
    "This transferable equipment is not available.": "Este equipo transferible no está disponible.",
    "Source and destination are the same warrior.": "El guerrero de origen y el de destino son el mismo.",
  };
  if (exact[message]) return exact[message];
  let match = message.match(/^(.+): Rejected import$/);
  if (match) return `No se pudo importar ${match[1]}.`;
  match = message.match(/^(.+): Invalid campaign$/);
  if (match) return `No se pudo importar ${match[1]}: la campaña no es válida.`;
  match = message.match(/^Roster limit reached \((\d+)\/(\d+)\)\.$/);
  if (match) return `Se ha alcanzado el límite de la lista (${match[1]}/${match[2]}).`;
  match = message.match(/^Cannot exceed (\d+) heroes\.$/);
  if (match) return `La banda no puede superar el límite de ${match[1]} Héroes.`;
  match = message.match(/^Cannot exceed (\d+) warband members\.$/);
  if (match) return `La banda no puede superar el límite de ${match[1]} miembros.`;
  match = message.match(/^Not enough gold: (\d+) gc needed, (\d+) (?:gc )?available\.$/);
  if (match) return `No hay suficientes CO: se necesitan ${match[1]} y hay ${match[2]} disponibles.`;
  match = message.match(/^Not enough gold: (\d+) gc needed\.$/);
  if (match) return `No hay suficientes CO: se necesitan ${match[1]}.`;
  match = message.match(/^Not enough (wyrdstone shard\(s\)|treasure\(s\)|campaign point\(s\)): (\d+) needed, (\d+) available\.$/);
  if (match) {
    const resource = { "wyrdstone shard(s)": "fragmentos de piedra bruja", "treasure(s)": "tesoros", "campaign point(s)": "puntos de campaña" }[match[1]];
    return `No hay suficientes ${resource}: se necesitan ${match[2]} y hay ${match[3]} disponibles.`;
  }
  match = message.match(/^(.+) holds at most (\d+) members\.$/);
  if (match) return `${match[1]} puede tener como máximo ${match[2]} miembros.`;
  match = message.match(/^Unknown (.+) id: (.+)\.$/);
  if (match) {
    const kind = { warrior: "guerrero", profile: "perfil", warband: "banda", item: "objeto", scenario: "escenario", "inventory item": "objeto del inventario", "upgrade item": "mejora" }[match[1]] ?? match[1];
    return `No se encuentra el identificador de ${kind}: ${match[2]}.`;
  }
  match = message.match(/^Unknown (.+?): (.+)\.$/);
  if (match) return `No se encuentra ${match[1]}: ${match[2]}.`;
  match = message.match(/^Profile "(.+)" is not available to this warband\.$/);
  if (match) return `El perfil «${match[1]}» no está disponible para esta banda.`;
  match = message.match(/^Groups of "(.+)" hold at most (\d+) models\.$/);
  if (match) return `Los grupos de «${match[1]}» pueden tener como máximo ${match[2]} miniaturas.`;
  match = message.match(/^Roster limit for "(.+)" is (\d+) models\.$/);
  if (match) return `El límite de lista para «${match[1]}» es de ${match[2]} miniaturas.`;
  match = message.match(/^Only (\d+) unassigned copy\/copies are available\.$/);
  if (match) return `Solo hay ${match[1]} copia(s) sin asignar disponible(s).`;
  match = message.match(/^Invalid (?:price|upgrade price): (.+)\.$/);
  if (match) return `El precio indicado no es válido: ${match[1]}.`;
  match = message.match(/^(.+) already has this upgrade\.$/);
  if (match) return `${match[1]} ya tiene esta mejora.`;
  match = message.match(/^(.+) already knows "(.+)"\.$/);
  if (match) return `${match[1]} ya conoce «${match[2]}».`;
  match = message.match(/^(.+) is not missing any games\.$/);
  if (match) return `${match[1]} no tiene partidas que perder.`;
  if (/^No pending\b|^There is no pending\b/.test(message)) return "No hay ninguna resolución pendiente para esta acción.";
  if (/^Resolve\b|^Complete\b/.test(message)) return "Falta resolver algún paso anterior de la postbatalla.";
  if (/^Choose\b|^Select\b|^Enter\b|^Use a valid\b/.test(message)) return "La selección o el valor introducido no es válido para esta acción.";
  if (/already been|has already/i.test(message)) return "Esta acción ya se había resuelto anteriormente.";
  return `No se pudo completar la acción: ${message}`;
}

function messageOf(err: AppError, locale: "es" | "en"): string {
  const detail = err.detail as Record<string, unknown> | undefined;
  const fileReason = detail?.file_reason;
  if (fileReason === "retired_version") {
    return locale === "es" ? `Este archivo usa un formato antiguo (versión ${String(detail?.found_version)}). Solo se admiten archivos de versión 4; vuelve a guardarlo primero con el gestor de escritorio.` : `This file uses an old format (version ${String(detail?.found_version)}). Only version 4 files are supported — re-save it with the desktop manager first.`;
  }
  if (fileReason === "unsupported_version") {
    return locale === "es" ? `Este archivo usa la versión ${String(detail?.found_version)}, que es más reciente que la versión admitida por la aplicación (4).` : `This file uses format version ${String(detail?.found_version)}, which is newer than this application supports (4).`;
  }
  if (fileReason === "invalid_json") {
    return locale === "es" ? "El archivo no contiene un JSON válido. Comprueba si realmente es una campaña .mordheim." : "This file is not valid JSON. Is it really a .mordheim campaign file?";
  }
  if (fileReason === "bad_marker") {
    return locale === "es" ? "El archivo no es una campaña de Mordheim: su identificador no es válido." : "This file is not a Mordheim campaign file (wrong marker).";
  }
  if (fileReason === "schema_violation") {
    const location = detail?.location ? ` (at ${String(detail.location)})` : "";
    return locale === "es" ? `El archivo incumple el formato de campaña${detail?.location ? ` (en ${String(detail.location)})` : ""}: ${localizeErrorMessage(err.message, locale)}` : `This file violates the campaign format${location}: ${err.message}`;
  }
  return localizeErrorMessage(err.message, locale);
}

export function useCampaignApp(service?: CampaignAppService): CampaignAppView {
  const shared = useContext(CampaignServiceContext);
  service ??= shared?.service;
  const locale = shared?.locale ?? "en";
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
  useEffect(() => {
    const receive = (event: Event) => setError((event as CustomEvent<string | null>).detail);
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
        setError(localizeErrorMessage("Replace the currently loaded campaign? Unsaved changes will be lost.", locale));
      } else {
        setError(messageOf(result as AppError, locale));
      }
    },
    [app, locale],
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
      setError(messageOf(result as AppError, locale));
    }
  }, [app, locale]);

  const runAction = useCallback(
    async (action: string, input: Record<string, unknown>) => {
      return withOperationProgress(async () => { try {
        const result = await app.run(action, input);
        if (result.ok) {
          setDocument(result.document);
          setError(null);
          setDirty(app.isDirty());
          publishCampaignError(null);
          return true;
        }
        const message = messageOf(result, locale);
        setError(message);
        publishCampaignError(message);
        return false;
      } catch (cause) {
        const message = localizeErrorMessage(cause instanceof Error ? cause.message : String(cause), locale);
        setError(message);
        publishCampaignError(message);
        return false;
      } });
    },
    [app, locale],
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
        setError(messageOf(result, locale));
      }
    },
    [app, locale],
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
