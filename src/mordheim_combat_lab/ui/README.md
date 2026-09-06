# Active interface

Tkinter presentation of the simulator. Keeps the Candidate, Enemy,
Improvements, Weapons, Equipment and House Rules navigation.

The UI owns windows, widgets, thread coordination and result adaptation. It
must not contain rules, construction validation or simulation loops:

- `application.catalogue` prepares the KB options.
- `application.analyses` runs comparisons without Tkinter.
- `persistence` saves versioned preferences and workbooks.
- `construction` compiles configurations and `combat.vectorized` simulates them.

The workbook keeps stable ids on a hidden sheet and readable summaries on the
visible sheets.

See [Modify an application](../../../../docs/guides/modify-application.md).
