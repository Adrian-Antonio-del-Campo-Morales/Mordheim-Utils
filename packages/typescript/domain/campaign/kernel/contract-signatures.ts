/**
 * T10 (post-review): compile-time contracts of the kernel entry points.
 *
 * The commit gate must not have a signature that lets a caller skip the whole
 * T09 construction contract: minimums, the mandatory variant, the equipment
 * verdicts, the compulsory kit and the owed creation rolls are all decided by the
 * reader `commitInitialWarband` is given. `tests/typescript/**` is compiled by
 * vitest only (esbuild strips types without checking them) and is not part of any
 * `tsconfig.json`, so the assertion lives in the typechecked package: making
 * `knowledge` optional again breaks `tsc --noEmit` here instead of slipping
 * through a test that passes `undefined`.
 *
 * Purity: no React, no DOM, no filesystem. Emits nothing at runtime.
 */

import type { KnowledgeReader } from "./ports";
import { commitInitialWarband } from "./commit-warband";
import { createDraft } from "./create-draft";

/** Compiles only while `T` is `true`. */
type Expect<T extends true> = T;
/** Whether a parameter type still demands a value (`false` once it is optional). */
type IsRequired<T> = undefined extends T ? false : true;

/** `commitInitialWarband(document, knowledge)` — the reader is not optional. */
export type COMMIT_REQUIRES_READER = Expect<
  IsRequired<Parameters<typeof commitInitialWarband>[1]>
>;
/** `createDraft(bandId, knowledge, …)`: composing a draft always needs the reader. */
export type DRAFT_REQUIRES_READER = Expect<
  IsRequired<Parameters<typeof createDraft>[1]>
>;
/** The reader the commit gate demands is the one the contract was written for. */
export type COMMIT_READER_IS_KNOWLEDGE_READER = Expect<
  Parameters<typeof commitInitialWarband>[1] extends KnowledgeReader ? true : false
>;
