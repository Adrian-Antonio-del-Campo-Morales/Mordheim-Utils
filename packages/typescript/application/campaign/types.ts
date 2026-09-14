/**
 * P3.4: frozen public interface of the application service (implemented by
 * P5.1). The UI (P5.2) depends only on this — it never touches the file port,
 * the KB adapter or JSON directly.
 *
 * The service keeps everything in memory: no browser storage of any kind
 * (permanent exclusion): campaigns stay in memory and are exported explicitly.
 */

import type {
  CampaignDocument,
  CampaignFilePort,
  KnowledgeReader,
  MomentSelection,
} from "../../domain/campaign/index";

/** Why an application-level operation failed. */
export type AppErrorReason =
  | "no_campaign_loaded"
  | "already_loaded"
  | "file_error"
  | "rejected"
  | "unknown";

/** Presentation identity travels separately from the diagnostic English message. */
export interface UiMessage {
  readonly key: string;
  readonly args?: Readonly<Record<string, string | number>>;
}

export interface AppError {
  readonly ok: false;
  readonly reason: AppErrorReason;
  readonly message: string;
  /** New callers render this stable key; legacy callers may still use message. */
  readonly message_key?: UiMessage["key"];
  readonly message_args?: UiMessage["args"];
  /** Present when the failure came from the file port or a use case. */
  readonly detail?: Readonly<Record<string, unknown>>;
}

export type AppResult =
  | { readonly ok: true; readonly document: CampaignDocument }
  | AppError;

export interface ImportRequest {
  /** Raw `.mordheim` file text (from a File input, already read in memory). */
  readonly text: string;
  /** Replace an already loaded campaign only when explicitly confirmed. */
  readonly confirm_replace?: boolean;
}

/** Export payload handed to the UI for a download. */
export interface ExportPayload {
  readonly filename: string;
  readonly text: string;
}

/**
 * Application service contract. History/undo stays internal to the
 * implementation; the UI only sees results and `dirty` state.
 */
export interface CampaignAppService {
  createCampaign(input: { readonly band_id: string; readonly campaign_name: string; readonly warband_name: string; readonly variant?: string }): Promise<AppResult>;
  canUndo(): boolean;
  subscribe(listener: () => void): () => void;
  prepareExport(): Promise<AppResult & { payload?: ExportPayload }>;
  markExported(document: CampaignDocument): void;
  /** Import a campaign file; rejects unconfirmed replacement. */
  importCampaign(request: ImportRequest): Promise<AppResult>;

  /** Export the current campaign as `.mordheim` v5 text. */
  exportCampaign(): Promise<AppResult & { payload?: ExportPayload }>;

  /** Run one domain use case by id (P6.x actions dispatch through here). */
  run(action: string, input: Readonly<Record<string, unknown>>): Promise<AppResult>;

  /** Move the view selection (never mutates campaign state). */
  selectMoment(moment: MomentSelection): AppResult;

  /** True when there are unexported campaign changes. */
  isDirty(): boolean;

  /** Currently loaded document, if any. */
  current(): CampaignDocument | null;
}

/** Dependencies injected by composition (P5.2 wires the real ones). */
export interface CampaignAppDeps {
  readonly files: CampaignFilePort;
  readonly knowledge: KnowledgeReader;
  /** Optional use-case override for feature blocks (P6.x); defaults apply. */
  readonly useCases?: import("../../domain/campaign/index").CampaignUseCases;
}
