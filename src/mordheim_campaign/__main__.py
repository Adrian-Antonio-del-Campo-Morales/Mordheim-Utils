"""Arranque de la app. Import absoluto: funciona con `python -m` y como
script de entrada de PyInstaller (sin paquete padre)."""
from mordheim_campaign.app import main

raise SystemExit(main())
