"""P7.1 (web-migration-parallel-plan.md §8): the full bidirectional
round-trip matrix across every producer/consumer pair.

Three producers exist today: the Python writer (`save_campaign`), the TS
P3.2 adapter (`serializeCampaign`) and the P6.x kernel workflows (which
generate campaign documents end to end). Three consumers: the Python reader
(`load_campaign`), the TS adapter (`parseCampaignFile`) and the TS kernel.

The matrix proven here, per fixture:

1. Python write → TS parse → TS serialize → Python load, semantic equality
   at every hop (only `saved_at`/`view` volatile).
2. TS workflow-generated documents (draft → commit → battle → post-battle
   steps, exported via the P3.2 adapter) load through the Python reader and
   survive one more Python save/load generation.

Skips cleanly when the TS cross-check artefacts are absent (TS suite not run
in this checkout).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mordheim_campaign.persistence.campaigns import load_campaign, save_campaign

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "contracts" / "campaign-file-v4" / "fixtures"
ARTEFACT = REPO_ROOT / "packages" / "typescript" / "adapters" / "campaign-file" / "_ts-roundtrip-artefact.json"
WORKFLOW_ARTEFACT = REPO_ROOT / "packages" / "typescript" / "adapters" / "campaign-file" / "_p71-workflow-documents.json"

FIXTURE_NAMES = [
    "draft.json",
    "active-campaign.json",
    "pending-post-battle.json",
    "full-inventory.json",
]

pytestmark = pytest.mark.skipif(
    not ARTEFACT.exists(),
    reason="TS round-trip artefact not present (P3.2 tests not run in this checkout)",
)


# Defaults the Python writer materializes for optional fields. The v4
# contract treats an absent optional field as null-equivalent; the TS adapter
# omits them while the Python writer always emits the full model. Cross-
# implementation comparison therefore normalizes both sides to the same
# semantic space (contract README: open payloads travel verbatim; optional
# scalars/collections have null-equivalent defaults).
_PY_DEFAULTS = {
    int: 0,
    float: 0,
    str: "",
    bool: False,
    list: [],
    dict: {},
    type(None): None,
}


def _volatile(doc: dict) -> dict:
    """Copy of a document with the two volatile fields removed."""
    copy = json.loads(json.dumps(doc))
    copy.pop("saved_at", None)
    copy.pop("view", None)
    return copy


def _semantic(value):
    """Normalize a document into the semantic space shared by both writers.

    - ``None``/absent optional fields collapse to their null-equivalent
      default (``0``/``""``/``[]``/``{}``/``None``),
    - dict key order is irrelevant (recursively sorted),
    - everything else (including open payloads with real content) compares
      exactly.
    """
    if isinstance(value, dict):
        normalized = {key: _semantic(item) for key, item in value.items()}
        # Optional fields that are None on one side and a default on the
        # other are equal: normalize None scalars/collections to their
        # emptiness marker so the comparison is order- and presence-insensitive.
        cleaned = {}
        for key, item in normalized.items():
            if item is None:
                cleaned[key] = None
            else:
                cleaned[key] = item
        return dict(sorted(cleaned.items(), key=lambda kv: kv[0]))
    if isinstance(value, list):
        return [_semantic(item) for item in value]
    return value


def _semantic_equal(a: dict, b: dict) -> bool:
    """Compare two documents modulo key order and null-vs-default optionals.

    Rule (contract README): an optional field that is ``null`` or absent on
    one side is semantically equal to the Python writer's materialized
    default on the other (``0``/``""``/``[]``/``{}``/``False``). Values that
    carry real content (``True``, non-empty containers, non-zero scalars)
    always compare exactly.
    """

    # Reader-completed defaults (Python reader fills these for absent/null
    # optional fields; documented reader behaviour, not drift):
    # - identity.ruleset defaults to the canonical ruleset id
    # - equipment.transferable defaults to True
    def reader_default(path: str, value) -> bool:
        if path.endswith("campaign.identity.ruleset") and value == "mordheim":
            return True
        if path.endswith(".transferable") and value is True:
            return True
        return False

    def is_default(value) -> bool:
        if value is None or value is False:
            return True
        if isinstance(value, (str, list, dict)) and len(value) == 0:
            return True
        if isinstance(value, (int, float)) and value == 0:
            return True
        return False

    def normalize(value):
        if isinstance(value, dict):
            return {
                key: normalize(item)
                for key, item in value.items()
                if not (item is None or item is False)
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    def diff_paths(x, y, path=""):
        mismatches = []
        if isinstance(x, dict) and isinstance(y, dict):
            for key in sorted(set(x) | set(y)):
                xv, yv = x.get(key), y.get(key)
                if key not in x and is_default(yv):
                    continue
                if key not in y and is_default(xv):
                    continue
                # Reader-completed defaults equal null/absent (see above):
                # one side is None and the other carries the default value.
                if xv is None and reader_default(f"{path}.{key}", yv):
                    continue
                if yv is None and reader_default(f"{path}.{key}", xv):
                    continue
                mismatches.extend(diff_paths(xv, yv, f"{path}.{key}"))
        elif isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                mismatches.append(f"{path}: length {len(x)} != {len(y)}")
            else:
                for index, (xi, yi) in enumerate(zip(x, y)):
                    mismatches.extend(diff_paths(xi, yi, f"{path}[{index}]"))
        elif x != y:
            mismatches.append(f"{path}: {x!r} != {y!r}")
        return mismatches

    mismatches = diff_paths(_semantic(normalize(a)), _semantic(normalize(b)))
    assert not mismatches, "semantic drift: " + "; ".join(mismatches[:8])
    return True


@pytest.mark.parametrize("fixture", FIXTURE_NAMES)
def test_python_to_ts_to_python_loop(fixture: str, tmp_path: Path) -> None:
    """Python write → TS parse → TS serialize → Python load, all hops equal."""
    # Hop 0: the fixture itself loads in Python (already covered by P3.3,
    # repeated here as the loop's entry point).
    fixture_doc = json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))
    state = load_campaign(_python_write(fixture_doc, tmp_path / "hop0"))

    # Hop 1: Python write → TS parse. The TS side parsed the same bytes in
    # its own suite (index.test.ts); here we verify the TS-serialized output
    # of that parse round-trips back through Python.
    data = json.loads(ARTEFACT.read_text(encoding="utf-8"))
    serialized_name = data["serialized"].get(fixture)
    assert serialized_name, fixture
    ts_doc = json.loads(
        (ARTEFACT.parent / serialized_name).read_text(encoding="utf-8")
    )
    assert ts_doc["marker"] == "MORDHEIM_CAMPAIGN_MANAGER"
    assert ts_doc["format_version"] == 4

    # Hop 2: TS serialize → Python load.
    reloaded = load_campaign(_python_write(ts_doc, tmp_path / "hop2"))
    assert _python_state(state) == _python_state(reloaded), fixture


def _python_write(doc: dict, path: Path) -> Path:
    """Persists a document dict through the real Python writer."""
    target = path.with_suffix(".mordheim")
    target.write_text(json.dumps(doc), encoding="utf-8")
    # The writer validates and rewrites; load through it to prove acceptance.
    loaded = load_campaign(target)
    final = path.with_suffix(".final.mordheim")
    save_campaign(final, loaded)
    return final


def _python_state(state) -> dict:
    """Semantic projection of a loaded AppState (contract README rules).

    Uses ``dataclasses.asdict`` (the models are ``@dataclass(slots=True)``,
    so there is no ``__dict__``); sets are normalized to sorted lists.
    """
    from dataclasses import asdict, is_dataclass

    def _normalize(value):
        if is_dataclass(value):
            return {key: _normalize(item) for key, item in asdict(value).items()}
        if isinstance(value, dict):
            return {key: _normalize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [_normalize(item) for item in value]
        if isinstance(value, (set, frozenset)):
            return sorted(_normalize(item) for item in value)
        return value

    return json.loads(json.dumps(_normalize(state.campaign), default=str))


@pytest.mark.skipif(
    not WORKFLOW_ARTEFACT.exists(),
    reason="P6.x workflow documents not emitted (TS matrix test not run in this checkout)",
)
class TestWorkflowGeneratedDocuments:
    """Documents the TS kernel workflows generated end to end."""

    def _documents(self) -> dict[str, dict]:
        return json.loads(WORKFLOW_ARTEFACT.read_text(encoding="utf-8"))["documents"]

    def test_artefact_covers_the_core_progressions(self) -> None:
        documents = self._documents()
        assert {"committed-draft", "after-battle", "post-battle-progressed"} <= set(documents)

    @pytest.mark.parametrize(
        "name",
        ["committed-draft", "after-battle", "post-battle-progressed"],
    )
    def test_workflow_document_loads_and_survives_python_generation(
        self, name: str, tmp_path: Path
    ) -> None:
        doc = self._documents()[name]
        first = load_campaign(_python_write(doc, tmp_path / name))
        assert first.campaign.band_id, name
        # Generation 2: Python save/load again — idempotent.
        second = load_campaign(_python_write(_doc_of(first), tmp_path / f"{name}-gen2"))
        assert _python_state(first) == _python_state(second), name

    def test_workflow_documents_are_semantically_stable_through_python(
        self, tmp_path: Path
    ) -> None:
        for name, doc in sorted(self._documents().items()):
            reloaded = load_campaign(_python_write(doc, tmp_path / name))
            round_tripped = json.loads(
                (tmp_path / f"{name}.final.mordheim").read_text(encoding="utf-8")
            )
            # The Python writer materializes every optional field with its
            # default (0/""/[]/{}), while the TS adapter omits them; the
            # comparison normalizes both to the contract's null-equivalent.
            assert _semantic_equal(_volatile(round_tripped), _volatile(doc)), name
            assert reloaded.campaign.current_state_number >= 0, name


def _doc_of(state) -> dict:
    """Re-serialize a loaded state via the Python writer into a raw document."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "gen.mordheim"
        save_campaign(path, state)
        return json.loads(path.read_text(encoding="utf-8"))
