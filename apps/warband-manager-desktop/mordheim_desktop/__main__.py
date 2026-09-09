"""App launcher. Absolute import: works with `python -m` and as the
PyInstaller entry script (no parent package)."""
from mordheim_desktop.app import main

raise SystemExit(main())
