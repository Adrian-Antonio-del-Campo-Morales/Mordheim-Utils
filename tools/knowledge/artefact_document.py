"""Load the generated web KB artefact completely (T12 fase D).

The generator publishes the artefact as an initial document plus fragments:

* ``knowledge-web.json`` — the initial download (bands, profiles, skills,
  mechanics, prose reference and the presentation index);
* ``knowledge-catalogue.json`` — the deferred campaign catalogue (equipment rows
  plus campaign sections), addressed by ``catalogue_url`` + ``catalogue_digest``
  and fetched by the product on demand (``ensureCatalogue``);
* ``rules-prose.json`` and ``display-text.json`` — the prose and presentation
  fragments, already referenced that way before the partition.

The browser merges those fragments through the adapter's URL + digest contract;
this module is the explicit whole-artefact path for tools and tests that
legitimately need every family, reading the same files the same directory
publishes. A directory that still ships the pre-partition document (items and
campaign inline, no ``catalogue_url``) is returned exactly as it is, so both
layouts load.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_artefact_document(path: str | Path) -> dict[str, Any]:
    """Return the generated artefact with every referenced fragment merged."""
    document_path = Path(path)
    document: dict[str, Any] = json.loads(document_path.read_text(encoding="utf-8"))

    def fragment(reference: Any) -> dict[str, Any]:
        if not isinstance(reference, str) or not reference:
            return {}
        candidate = document_path.with_name(reference)
        if not candidate.exists():
            return {}
        return json.loads(candidate.read_text(encoding="utf-8"))

    prose = fragment(document.get("rules_prose_url"))
    document = {
        **document,
        **fragment(document.get("display_text_url")),
        **fragment(document.get("catalogue_url")),
    }
    if prose:
        document["rules_prose"] = prose
    return document
