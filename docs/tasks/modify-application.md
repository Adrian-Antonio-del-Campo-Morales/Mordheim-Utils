# Modify the application

1. Model the use case in `application/` without Tkinter.
2. Reuse `mordheim_construction` for legality and `combat.vectorized` for analysis.
3. Return explicit types and accept cancellation/progress for long jobs.
4. Keep the thread, `after` and presentation in `ui/`.
5. Version persisted changes without breaking the reading of existing workbooks.

Done when it is tested without a window and the persisted round-trips still pass.
