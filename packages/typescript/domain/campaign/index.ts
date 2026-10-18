/**
 * Public surface of the campaign domain (frozen contract).
 * Feature blocks (P6.x) extend this barrel; they never deep-import internals
 * of each other.
 */
export * from "./kernel/state";
export * from "./kernel/ports";
export * from "./kernel/usecases";
export * from "./band-variants";
// Construction contracts shared by the campaign and the web interface: facts,
// stable issue codes, hiring decisions and open clauses.
export * from "./construction";
