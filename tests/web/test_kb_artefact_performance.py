"""web.p7_5.kb-artefact-performance: the KB artefact stays web-deliverable.

Web migration KB performance gate: measure the compressed size of the
generated knowledge artefact and fail if it exceeds the agreed delivery
budget. Also verifies the canonical search index can be built from the
artefact in-process quickly enough for page load (indexing cost, P7.5's
"coste de indexación").

Skips cleanly when the artefact has not been generated yet
(``build/generated/knowledge-web/knowledge-web.json``) so CI can run the
suite before P4.2's generation step.
"""

from __future__ import annotations

import gzip
import json
import time
from pathlib import Path

import pytest

ARTEFACT = Path("build/generated/knowledge-web/knowledge-web.json")

# Delivery budget:
# the artefact must stay under 350 kB gzipped so GitHub Pages serves it in
# well under one second on a mid-range connection. Measured today: ~209 kB.
GZIP_BUDGET_BYTES = 350 * 1024

# Whole-artefact index build budget: the P4.3 adapter builds Maps for bands,
# profiles, items and skills on import. A full rebuild from the parsed JSON
# must stay far below one page-load frame budget (generous 2 s wall-clock
# bound on CI; measured ~50 ms locally).
INDEX_BUDGET_SECONDS = 2.0


def _load_artefact() -> dict:
    return json.loads(ARTEFACT.read_text(encoding="utf-8"))


@pytest.mark.skipif(not ARTEFACT.exists(), reason="KB artefact not generated yet")
class TestKbArtefactPerformance:
    def test_gzipped_size_within_delivery_budget(self) -> None:
        raw = ARTEFACT.read_bytes()
        gzipped = len(gzip.compress(raw, 9))
        assert gzipped < GZIP_BUDGET_BYTES, (
            f"KB artefact gzip size {gzipped / 1024:.0f} kB exceeds the "
            f"{GZIP_BUDGET_BYTES // 1024} kB delivery budget — partition the "
            "artefact (architecture change) instead of raising the budget."
        )

    def test_index_build_cost_within_budget(self) -> None:
        artefact = _load_artefact()
        start = time.perf_counter()
        # Canonical indexing cost, mirroring what the P4.3 adapter does on
        # import: one Map/dict per family plus the composite profile key.
        band_ids = {row["id"] for row in artefact["bands"]}
        item_ids = {row["item_id"] for row in artefact["items"]}
        profile_index = {
            f"{row['collection']}/{row['band_id']}/{row['id']}": row
            for row in artefact["profiles"]
        }
        skill_ids = {row["id"] for row in artefact["skills"]}
        elapsed = time.perf_counter() - start
        assert band_ids and item_ids and profile_index and skill_ids
        assert elapsed < INDEX_BUDGET_SECONDS, (
            f"Indexing the artefact took {elapsed:.2f}s, over the "
            f"{INDEX_BUDGET_SECONDS}s budget."
        )

    def test_size_metrics_are_stable_and_reported(self) -> None:
        """The generator output size is deterministic run to run (P4.2)."""
        artefact = _load_artefact()
        counts = {
            "bands": len(artefact["bands"]),
            "profiles": len(artefact["profiles"]),
            "items": len(artefact["items"]),
            "skills": len(artefact["skills"]),
        }
        # Reference stats from the first P4.2 delivery; a change here is a
        # deliberate KB/catalogue change and must update this test.
        assert counts == {
            "bands": 81,
            "profiles": 534,
            "items": 278,
            "skills": 75,
        }
