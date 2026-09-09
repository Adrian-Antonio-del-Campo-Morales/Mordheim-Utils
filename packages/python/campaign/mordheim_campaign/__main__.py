"""App launcher. Absolute import: works with `python -m` and as the
PyInstaller entry script (no parent package)."""
from mordheim_campaign.app import main

raise SystemExit(main())
