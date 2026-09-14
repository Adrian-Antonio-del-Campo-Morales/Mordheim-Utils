"""Campaign-file contract harness.

Shared evidence for Python and TypeScript consumers of the `.mordheim` v5
contract and the generated knowledge artefact. This harness reads the
contract sources directly and verifies the rejection, semantic-comparison and
preserve-in-place payload policies so both implementations are tested against
the same scenarios.

The TypeScript mirror lives in
`packages/typescript/adapters/campaign-file/`; both sides must stay green on
the same document set.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "contracts" / "campaign-file-v5"
SCHEMA_PATH = CONTRACT / "campaign-file-v5.schema.json"
FIXTURES = sorted((CONTRACT / "fixtures").glob("*.json"))
PYTHONPATH_ROOTS = (
    ROOT / "packages" / "python" / "combat-engine",
    ROOT / "packages" / "python" / "roster-construction",
    ROOT / "packages" / "python" / "core",
    ROOT / "packages" / "python" / "knowledge",
    ROOT / "packages" / "python" / "adapters" / "desktop-ui",
    ROOT / "packages" / "python" / "campaign",
    ROOT / "apps" / "combat-lab",
    ROOT / "apps" / "warband-manager-desktop",
)


def _ensure_pythonpath() -> None:
    for package_root in reversed(PYTHONPATH_ROOTS):
        if str(package_root) not in sys.path:
            sys.path.insert(0, str(package_root))

SUPPORTED_VERSION = 5
RETIRED_VERSIONS = (1, 2, 3, 4)


def _fixture(name: str) -> dict:
    return json.loads((CONTRACT / "fixtures" / name).read_text(encoding="utf-8"))


def _python_load(document: dict, tmp_path: Path):
    """Load a document through the Python reference reader."""
    import sys

    _ensure_pythonpath()
    from mordheim_campaign.persistence import load_campaign

    path = tmp_path / "probe.mordheim"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return load_campaign(path)


# --------------------------------------------------------------- rejection cases


@pytest.mark.parametrize("version", RETIRED_VERSIONS, ids=lambda v: f"v{v}")
def test_harness_retired_versions_are_rejected_the_same_way(tmp_path, version):
    """Case 3 of the contract README: retired versions get an explicit,
    actionable message naming the found and supported versions."""
    document = copy.deepcopy(_fixture("draft.json"))
    document["format_version"] = version
    with pytest.raises(Exception) as excinfo:
        _python_load(document, tmp_path)
    message = str(excinfo.value)
    assert str(version) in message
    assert str(SUPPORTED_VERSION) in message


def test_harness_wrong_marker_is_rejected_before_version_check(tmp_path):
    """Case 2: a wrong marker is 'not a campaign file' regardless of version."""
    document = copy.deepcopy(_fixture("draft.json"))
    document["marker"] = "SOME_OTHER_TOOL"
    with pytest.raises(Exception) as excinfo:
        _python_load(document, tmp_path)
    assert "marker" in str(excinfo.value).lower()


def test_harness_invalid_json_is_rejected(tmp_path):
    """Case 1: unreadable/invalid JSON is a distinct, actionable error."""
    path = tmp_path / "broken.mordheim"
    path.write_text("{not json", encoding="utf-8")
    import sys

    _ensure_pythonpath()
    from mordheim_campaign.persistence import load_campaign

    with pytest.raises(Exception):
        load_campaign(path)


def test_harness_schema_violations_name_a_location(tmp_path):
    """Case 4: schema violations report where the document is wrong."""
    document = copy.deepcopy(_fixture("draft.json"))
    document["campaign"].pop("identity")
    with pytest.raises(Exception) as excinfo:
        _python_load(document, tmp_path)
    assert "identity" in str(excinfo.value)


def test_harness_unresolvable_band_id_is_a_reference_concern(tmp_path):
    """Case 5: reference validation happens against the KB, not the schema.
    The schema only guarantees the identity carries a non-empty band_id; the
    harness documents that the *consumer* (Python app, TS domain via
    KnowledgeReader) must reject an unresolvable band — here via the
    KnowledgePort contract the desktop uses for the same purpose."""
    import sys

    _ensure_pythonpath()
    from mordheim_campaign.application.knowledge_port import KnowledgePort, KnowledgePortError

    port = KnowledgePort()
    with pytest.raises(KnowledgePortError):
        port.warband("mordheim", "no-such-warband")
    # Schema-level: the document itself still validates (band_id present),
    # so the two validation layers are independent — that is the contract.
    document = copy.deepcopy(_fixture("draft.json"))
    document["campaign"]["identity"]["band_id"] = "no-such-warband"
    _python_load(document, tmp_path)  # schema accepts; reference resolution is a KB concern


# --------------------------------------------------------- semantic comparison


@pytest.mark.parametrize("fixture_path", FIXTURES, ids=lambda path: path.name)
def test_harness_saved_at_is_the_only_semantic_difference(tmp_path, fixture_path):
    """Two saves of the same campaign differ *only* in `saved_at`; the harness
    freezes this policy for both implementations."""
    import sys

    _ensure_pythonpath()
    from mordheim_campaign.persistence import load_campaign, save_campaign

    document = json.loads(fixture_path.read_text(encoding="utf-8"))
    identity = document["campaign"]["identity"]
    sys.modules.pop("mordheim_campaign.persistence", None)  # fresh import guard
    # Rebuild state from the fixture through the reference reader, save twice.
    first_path = tmp_path / f"first-{fixture_path.name}"
    first_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    state = load_campaign(first_path)
    first = save_campaign(tmp_path / "first.mordheim", state)
    second = save_campaign(tmp_path / "second.mordheim", state)
    doc_a = json.loads(first.read_text(encoding="utf-8"))
    doc_b = json.loads(second.read_text(encoding="utf-8"))
    doc_a.pop("saved_at")
    doc_b.pop("saved_at")
    assert doc_a == doc_b, f"non-volatile drift in {fixture_path.name} (identity={identity.get('band_id')})"


# --------------------------------------------------- preserve-in-place payloads


def test_harness_open_payloads_survive_a_python_round_trip(tmp_path):
    """The contract's open-payload maps travel verbatim: unknown keys inside
    `step_state`, `participants` etc. must not be dropped or rewritten."""
    import sys

    _ensure_pythonpath()
    from mordheim_campaign.persistence import load_campaign, save_campaign

    document = _fixture("pending-post-battle.json")
    open_marker = {"future_field": {"nested": [1, 2, 3]}, "another": "keep-me"}
    post_battles = document["campaign"]["post_battles"]
    assert post_battles, "fixture must carry a pending post-battle"
    post_battles[0].setdefault("step_state", {})["999"] = open_marker
    source = tmp_path / "open-payload.mordheim"
    source.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    state = load_campaign(source)
    exported = save_campaign(tmp_path / "back.mordheim", state)
    round_tripped = json.loads(exported.read_text(encoding="utf-8"))
    round_tripped.pop("saved_at")
    reference = copy.deepcopy(document)
    reference.pop("saved_at")
    assert round_tripped == reference, "open payload was altered by the reader"


def test_harness_fixtures_and_artefact_band_ids_agree():
    """The KB artefact inventory (P4.1) and the contract fixtures (P1) must
    agree on stable ids: every fixture band exists in the KB source tree."""
    import yaml

    band_ids = set()
    for band_file in (ROOT / "sources" / "knowledge" / "bands").glob("*/*/band.yaml"):
        document = yaml.safe_load(band_file.read_text(encoding="utf-8")) or {}
        if document.get("id"):
            band_ids.add(str(document["id"]))
    for fixture in FIXTURES:
        document = json.loads(fixture.read_text(encoding="utf-8"))
        band_id = document["campaign"]["identity"].get("band_id")
        assert band_id in band_ids, f"{fixture.name}: band {band_id!r} not in KB"
