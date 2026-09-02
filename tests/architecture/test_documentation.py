from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]


def test_local_markdown_links_resolve():
    missing = []
    for document in (ROOT / "docs").rglob("*.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", document.read_text(encoding="utf-8")):
            if "://" not in target and not (document.parent / target).resolve().exists():
                missing.append(f"{document.relative_to(ROOT)} -> {target}")
    assert missing == []
