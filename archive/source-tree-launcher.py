"""Lanzador histórico. Use `python -m mordheim_combat_lab ui`."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
from mordheim_combat_lab.ui.app import main

if __name__ == "__main__":
    raise SystemExit(main())
