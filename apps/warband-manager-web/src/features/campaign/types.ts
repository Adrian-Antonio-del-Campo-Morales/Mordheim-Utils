/**
 * App-side aggregate of the public domain/application types. Feature code
 * imports from "./types" (or "@domain"/"@app" directly) and never deep-imports
 * across package boundaries — the alias targets are the only coupling points.
 */
export * from "@domain/campaign/index";
export { createCampaignAppService } from "@app/campaign/service";
export type {
  CampaignAppService,
  AppError,
  AppResult,
  ExportPayload,
  ImportRequest,
  CampaignAppDeps,
} from "@app/campaign/types";
