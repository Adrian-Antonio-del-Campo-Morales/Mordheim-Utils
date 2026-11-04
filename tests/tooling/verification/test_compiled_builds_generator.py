"""Source provenance and exit status of the compiled-builds generator.

Nothing here compiles, loads the KB through the compiler or runs an engine:
discovery and capture are replaced by stubs, and the fighters written are
decoded from the checked-in frozen document.
"""
from __future__ import annotations

import json

import pytest

from tools.verification import compiled_builds
from tools.verification import generate_compiled_builds as generator
from tools.verification.compiled_cases import canonical_json
from tools.verification.compiled_cases import decode_compiled_fighter

OLD = "a" * 64
CURRENT = "b" * 64
FROZEN = generator.SNAPSHOT  # the checked-in document, before any redirection


def _frozen_samples(count: int):
    """``(key, build, fighter)`` for default-root entries of the real document."""
    document = json.loads(FROZEN.read_text(encoding="utf-8"))
    samples = []
    for key, entry in sorted(document["entries"].items()):
        if entry["request"]["root"] is None:
            samples.append((key, generator._decode_build(entry["request"]["build"]),
                            decode_compiled_fighter(entry["fighter"])))
        if len(samples) == count:
            return samples
    raise AssertionError("not enough default-root entries in the frozen document")


def test_the_checked_in_document_without_source_digests_still_loads():
    assert compiled_builds.load_builds(FROZEN).sources == ()


def test_source_digests_roundtrip_and_stay_outside_the_entries_fingerprint(tmp_path):
    (_, build, fighter), = _frozen_samples(1)
    plain = compiled_builds.encode_document([(build, fighter, None)])
    recorded = compiled_builds.encode_document([(build, fighter, None)],
                                               sources=[OLD, CURRENT, OLD])
    assert "sources_sha256" not in plain["fingerprints"]
    assert recorded["fingerprints"]["sources_sha256"] == [OLD, CURRENT]
    assert (recorded["fingerprints"]["entries_sha256"]
            == plain["fingerprints"]["entries_sha256"])
    path = tmp_path / "builds.json"
    path.write_text(json.dumps(recorded), encoding="utf-8")
    assert compiled_builds.load_builds(path).sources == (OLD, CURRENT)


@pytest.mark.parametrize("sources", ["abc", [CURRENT, OLD], ["not-a-digest"], [OLD, OLD]])
def test_malformed_source_digests_are_rejected(tmp_path, sources):
    (_, build, fighter), = _frozen_samples(1)
    document = compiled_builds.encode_document([(build, fighter, None)])
    document["fingerprints"]["sources_sha256"] = sources
    path = tmp_path / "builds.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(compiled_builds.CompiledBuildError, match="sources_sha256"):
        compiled_builds.load_builds(path)


def test_the_fingerprint_covers_kb_and_compiler_sources_only(tmp_path):
    knowledge = tmp_path / generator.KNOWLEDGE_SOURCES / "bands"
    compiler = tmp_path / generator.COMPILER_PACKAGE
    knowledge.mkdir(parents=True)
    (compiler / "__pycache__").mkdir(parents=True)
    (knowledge / "band.yaml").write_text("a: 1\n", encoding="utf-8")
    (compiler / "compiler.py").write_text("X = 1\n", encoding="utf-8")
    (compiler / "__pycache__" / "compiler.cpython.pyc").write_bytes(b"cache")
    (tmp_path / "unrelated.py").write_text("Y = 1\n", encoding="utf-8")

    assert {path.name for path in generator.construction_sources(tmp_path)} == {
        "band.yaml", "compiler.py"}
    first = generator.sources_fingerprint(tmp_path)
    (compiler / "__pycache__" / "compiler.cpython.pyc").write_bytes(b"other cache")
    (tmp_path / "unrelated.py").write_text("Y = 2\n", encoding="utf-8")
    assert generator.sources_fingerprint(tmp_path) == first
    (knowledge / "band.yaml").write_text("a: 2\n", encoding="utf-8")
    second = generator.sources_fingerprint(tmp_path)
    (compiler / "compiler.py").write_text("X = 2\n", encoding="utf-8")
    assert len({first, second, generator.sources_fingerprint(tmp_path)}) == 3


@pytest.mark.parametrize("recorded, frozen", [([CURRENT], 4), ([OLD], 0), ([], 0)])
def test_no_warning_when_frozen_fighters_match_the_current_sources(capsys, recorded,
                                                                  frozen):
    assert generator.sources_warning(recorded, CURRENT, frozen) is None
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("recorded, shown", [
    ([OLD, CURRENT], OLD[:12]),
    ([compiled_builds.UNRECORDED_SOURCES], "unrecorded"),
])
def test_other_sources_produce_a_prominent_warning(capsys, recorded, shown):
    warning = generator.sources_warning(recorded, CURRENT, 3)
    assert warning.startswith("PROVENANCE WARNING: 3 frozen fighters")
    assert shown in warning and CURRENT[:12] in warning
    assert warning in capsys.readouterr().err


@pytest.fixture()
def isolated(tmp_path, monkeypatch):
    """Generator paths in ``tmp_path``; discovery and source hashing stubbed."""
    monkeypatch.chdir(generator.ROOT)
    monkeypatch.setattr(generator, "SNAPSHOT", tmp_path / "compiled-builds.json")
    monkeypatch.setattr(generator, "COVERAGE", tmp_path / "coverage.json")
    monkeypatch.setattr(generator, "discover", lambda: {"mod": ["test_x"]})
    monkeypatch.setattr(generator, "sources_fingerprint", lambda root=generator.ROOT: CURRENT)
    return tmp_path


def _capture(monkeypatch, *, entries=None, consumers=None, blocked=None, failures=None):
    def fake(pending, frozen):
        return {
            "pending": pending, "consumers": consumers or {}, "blocked": blocked or {},
            "no_builds": {}, "skipped": {}, "compilations": 0, "reused": len(frozen),
            "conflicts": [], "module_scope_calls": 0, "entries": entries or {},
            "failures": failures or [],
        }

    monkeypatch.setattr(generator, "capture", fake)


def _consumer(*keys):
    return {"test": "test_x", "parameter_set": 0, "build_keys": list(keys),
            "dynamic_builds": len(keys), "static_builds": 0, "reached_engine": True,
            "unresolved_calls": []}


def test_a_clean_run_exits_zero(isolated, monkeypatch):
    _capture(monkeypatch)
    assert generator.main([]) == 0
    report = json.loads((isolated / "coverage.json").read_text(encoding="utf-8"))
    assert report["sources_sha256"] == CURRENT
    assert report["provenance_warnings"] == []


@pytest.mark.parametrize("outcome", [
    {"failures": [{"consumer": "mod::test_x", "order": 0, "build_key": "k",
                   "error": "ValueError: gone"}]},
    {"blocked": {"mod::test_x": "non-literal argument"}},
])
def test_compile_failures_and_blocked_consumers_exit_non_zero(isolated, monkeypatch,
                                                              capsys, outcome):
    _capture(monkeypatch, **outcome)
    assert generator.main([]) == 1
    assert "FAILED:" in capsys.readouterr().err
    assert (isolated / "coverage.json").is_file()


def test_regeneration_from_other_sources_warns_and_still_writes(isolated, monkeypatch,
                                                                capsys):
    (old_key, old_build, old_fighter), (new_key, new_build, new_fighter) = _frozen_samples(2)
    stored = compiled_builds.encode_document([(old_build, old_fighter, None)], sources=[OLD])
    (isolated / "compiled-builds.json").write_text(json.dumps(stored), encoding="utf-8")
    _capture(monkeypatch,
             entries={new_key: {"build": new_build, "fighter": new_fighter, "root": None}},
             consumers={"mod::test_x": _consumer(old_key, new_key)})

    assert generator.main(["--write"]) == 0

    error = capsys.readouterr().err
    assert error.count("PROVENANCE WARNING: 1 frozen fighters") == 2  # start and end
    document = json.loads((isolated / "compiled-builds.json").read_text(encoding="utf-8"))
    assert canonical_json(document["entries"][old_key]) == canonical_json(
        stored["entries"][old_key])
    assert set(document["entries"]) == {old_key, new_key}
    assert document["fingerprints"]["sources_sha256"] == [OLD, CURRENT]
    report = json.loads((isolated / "coverage.json").read_text(encoding="utf-8"))
    assert report["recorded_sources_sha256"] == [OLD]
    assert report["provenance_warnings"] and "frozen fighters" in report["provenance_warnings"][0]


def test_a_legacy_document_is_marked_unrecorded_on_rewrite(isolated, monkeypatch):
    (old_key, old_build, old_fighter), = _frozen_samples(1)
    stored = compiled_builds.encode_document([(old_build, old_fighter, None)])
    (isolated / "compiled-builds.json").write_text(json.dumps(stored), encoding="utf-8")
    _capture(monkeypatch, consumers={"mod::test_x": _consumer(old_key)})

    assert generator.main(["--write"]) == 0

    document = json.loads((isolated / "compiled-builds.json").read_text(encoding="utf-8"))
    assert canonical_json(document["entries"]) == canonical_json(stored["entries"])
    # No new compilation: today's sources are not claimed for old entries.
    assert document["fingerprints"]["sources_sha256"] == [compiled_builds.UNRECORDED_SOURCES]
