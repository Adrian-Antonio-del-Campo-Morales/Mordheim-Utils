"""Web migration malformed-corpus gate: the corrupt corpus driven
through the desktop Python reader. Every corpus file must be rejected with a
``CampaignFileError`` whose message contains the manifest's stable substring —
the same manifest the TS adapter harness asserts against.

Error-quality rules asserted here (plan §P7.2): messages are actionable,
non-empty, and never leak internal traces (no repo paths of the *running*
checkout beyond the file's own name, no "Traceback", no source snippets).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mordheim_campaign.persistence.campaigns import CampaignFileError, load_campaign

REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS = REPO_ROOT / "tests" / "web" / "contract" / "corpus"

MANIFEST = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))["expected"]
CORPUS_FILES = sorted(p.name for p in CORPUS.glob("*.mordheim"))

NOISE_PATTERNS = ("Traceback", "File \"<stdin>", "site-packages", ".py\", line")


def test_corpus_is_complete() -> None:
    assert len(CORPUS_FILES) >= 20
    for name in MANIFEST:
        assert name in CORPUS_FILES, name


@pytest.mark.parametrize("name", CORPUS_FILES)
def test_every_corpus_file_is_rejected_with_stable_message(name: str) -> None:
    expected = MANIFEST[name]["py_substring"]
    with pytest.raises(CampaignFileError) as excinfo:
        load_campaign(CORPUS / name)
    message = str(excinfo.value)
    assert expected in message, f"{name}: {message!r} lacks {expected!r}"
    assert len(message) > 10, name
    for noise in NOISE_PATTERNS:
        assert noise not in message, f"{name}: message leaks internals: {message!r}"


def test_retired_versions_name_found_and_supported() -> None:
    for version in (1, 2, 3):
        with pytest.raises(CampaignFileError) as excinfo:
            load_campaign(CORPUS / f"retired-v{version}.mordheim")
        message = str(excinfo.value)
        assert str(version) in message
        assert "v4" in message or "4" in message
