"""web.p7_5.kb-artefact-performance: the KB artefact stays web-deliverable.

T12 fase D split the published artefact into two downloads:

* ``knowledge-web.json`` is the **initial document** the browser fetches at
  startup: bands, profiles, skills, mechanics, prose and the presentation index,
  which is what opening the application and choosing a warband needs;
* ``knowledge-catalogue.json`` is the **deferred campaign catalogue** (equipment
  rows + campaign sections), addressed by ``catalogue_url`` + ``catalogue_digest``
  and fetched by the first flow that needs it through
  ``ensureCatalogue("items" | "campaign")``: construction and starting
  equipment, the market, equipment transfers, the campaign inventory, the PDF
  writer or any item/campaign name or effect resolver.

The delivery budget applies to the initial download, which is what a visitor
pays before the application is usable. The deferred fragment is measured and
reported separately: it is paid once, on the flow that needs it, and never as
part of the initial load.

Also verifies the canonical search index can be built from the artefact in
process quickly enough for page load (indexing cost, over both documents).

Skips cleanly when the artefact has not been generated yet so CI can run the
suite before the generation step.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
from pathlib import Path

import pytest

INITIAL = Path("outputs/web-public/knowledge/knowledge-web.json")
CATALOGUE = INITIAL.with_name("knowledge-catalogue.json")

# Delivery budget for the **initial download**:
# the artefact must stay under 350 kB gzipped so GitHub Pages serves it in
# well under one second on a mid-range connection. Measured today: 209 kB for
# the pre-2A/2B catalogue; the merged document of the 2A/2B delivery measured
# 641.5 kB gzip, so T12 fase D partitioned it instead of raising the budget:
# the initial document now measures 282.6 kB gzip and the deferred campaign
# catalogue 360.6 kB gzip (paid on demand). The combined 643.2 kB is 1.7 kB
# over the unsplit document: the cost of splitting, not of new content.
GZIP_BUDGET_BYTES = 350 * 1024

# Whole-artefact index build budget: the adapter builds Maps for bands,
# profiles and skills at import and for items/campaign when the deferred
# catalogue loads. A full rebuild from the parsed JSON must stay far below one
# page-load frame budget (generous 2 s wall-clock bound on CI; measured ~50 ms
# locally).
INDEX_BUDGET_SECONDS = 2.0


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _gzip_size(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), 9))


@pytest.mark.skipif(not INITIAL.exists(), reason="KB artefact not generated yet")
class TestKbArtefactPerformance:
    def test_initial_download_within_delivery_budget(self) -> None:
        """The startup download — and only it — is what the budget bounds."""
        gzipped = _gzip_size(INITIAL)
        assert gzipped < GZIP_BUDGET_BYTES, (
            f"KB initial artefact gzip size {gzipped / 1024:.0f} kB exceeds the "
            f"{GZIP_BUDGET_BYTES // 1024} kB delivery budget — defer another "
            "section (architecture change) instead of raising the budget."
        )

    def test_deferred_catalogue_is_not_part_of_the_initial_download(self) -> None:
        """Items and campaign sections must be absent from the initial document."""
        document = _load(INITIAL)
        assert "items" not in document, "the equipment catalogue must travel in the deferred fragment"
        assert "campaign" not in document, "the campaign sections must travel in the deferred fragment"
        reference = document.get("catalogue_url")
        assert isinstance(reference, str) and reference
        fragment_path = INITIAL.with_name(reference)
        assert fragment_path.exists(), f"deferred catalogue {reference} was not generated"
        fragment = _load(fragment_path)
        assert fragment["items"] and fragment["campaign"], "the deferred fragment must carry both families"

    def test_deferred_catalogue_digest_matches_the_published_fragment(self) -> None:
        """The fragment is addressed by digest; a drift is a broken delivery."""
        document = _load(INITIAL)
        fragment = _load(CATALOGUE)
        serialized = json.dumps(fragment, ensure_ascii=False, separators=(",", ":")).encode()
        digest = hashlib.sha256(serialized).hexdigest()
        assert digest == document.get("catalogue_digest"), (
            "knowledge-catalogue.json does not match catalogue_digest: regenerate, never hand-edit"
        )

    def test_initial_and_deferred_sizes_are_measured_separately(self) -> None:
        """Report both downloads and their combined cost explicitly."""
        assert CATALOGUE.exists(), "the deferred catalogue was not generated"
        initial_gzip, catalogue_gzip = _gzip_size(INITIAL), _gzip_size(CATALOGUE)
        initial_raw, catalogue_raw = INITIAL.stat().st_size, CATALOGUE.stat().st_size
        assert initial_gzip > 0 and catalogue_gzip > 0
        assert initial_raw > 0 and catalogue_raw > 0
        # The deferred part is the heavy one: the split is what buys the budget.
        assert catalogue_gzip > initial_gzip, (
            "the deferred catalogue should carry the bulk of the payload "
            f"(initial {initial_gzip / 1024:.0f} kB, deferred {catalogue_gzip / 1024:.0f} kB)"
        )

    def test_index_build_cost_within_budget(self) -> None:
        artefact = _load(INITIAL)
        catalogue = _load(CATALOGUE)
        start = time.perf_counter()
        # Canonical indexing cost, mirroring what the adapter does on import:
        # one Map/dict per family plus the composite profile key. The item and
        # campaign maps are built when the deferred catalogue arrives.
        band_ids = {row["id"] for row in artefact["bands"]}
        profile_index = {
            f"{row['collection']}/{row['band_id']}/{row['id']}": row
            for row in artefact["profiles"]
        }
        skill_ids = {row["id"] for row in artefact["skills"]}
        item_ids = {row["item_id"] for row in catalogue["items"]}
        scenario_ids = {row["id"] for row in catalogue["campaign"]["scenarios"]["scenarios"]}
        elapsed = time.perf_counter() - start
        assert band_ids and item_ids and profile_index and skill_ids and scenario_ids
        assert elapsed < INDEX_BUDGET_SECONDS, (
            f"Indexing the artefact took {elapsed:.2f}s, over the "
            f"{INDEX_BUDGET_SECONDS}s budget."
        )

    def test_size_metrics_are_stable_and_reported(self) -> None:
        """The generator output size is deterministic run to run (P4.2)."""
        artefact = _load(INITIAL)
        catalogue = _load(CATALOGUE)
        counts = {
            "bands": len(artefact["bands"]),
            "profiles": len(artefact["profiles"]),
            "skills": len(artefact["skills"]),
            "items": len(catalogue["items"]),
            "campaign_sections": len(catalogue["campaign"]),
        }
        # Reference stats from the last accepted delivery; a change here is a
        # deliberate KB/catalogue change and must update this test. Updated by
        # T12 for the 2A/2B catalogue delivery (campaign bands, variants and the
        # promoted campaign contracts) and split across the initial document and
        # the deferred campaign catalogue. `items` is 388 since the campaign
        # inventory fix published `holy_relic` as a catalogue item (387 + 1).
        assert counts == {
            "bands": 161,
            "profiles": 1056,
            "skills": 82,
            "items": 388,
            "campaign_sections": 16,
        }
