/**
 * Public surface of the campaign domain (P3.4 freeze).
 * Feature blocks (P6.x) extend this barrel; they never deep-import internals
 * of each other.
 */
export * from "./kernel/state";
export * from "./kernel/ports";
export * from "./kernel/usecases";
export * from "./band-variants";
