/**
 * Shared rejection constructor for the default use cases. Kept in its own
 * module so feature blocks (P6.x) reuse the exact same shape.
 */

import type { UseCaseRejectionReason, UseCaseResult } from "../index";

export function rejected(reason: UseCaseRejectionReason, message: string): UseCaseResult {
  return { ok: false, reason, message };
}
