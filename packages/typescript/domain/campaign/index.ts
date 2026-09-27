/**
 * Public surface of the campaign domain (P3.4 freeze).
 * Feature blocks (P6.x) extend this barrel; they never deep-import internals
 * of each other.
 */
export * from "./kernel/state";
export * from "./kernel/ports";
export * from "./kernel/usecases";
export * from "./band-variants";
// T09 construction contracts shared by the campaign (T10) and the web interface
// (T11): facts, stable issue codes, hiring decisions and open clauses.
export * from "./construction";
