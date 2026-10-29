"""Contracts of the separate-engine sample store (``parity_samples``).

The store must (1) reproduce each engine's own sample exactly when a sample
is stored chunk by chunk, (2) resume an interrupted sample by running only the
missing chunks, (3) keep an oracle sample valid across native-only changes and
refuse a sample whose identity moved.  The engine samples here are tiny (tens
of duels on ``basic``); nothing is a statistical comparison.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from tests.engines.fixtures.precompiled_catalog import scenario_key
from tools.verification import parity_samples as store
from tools.verification.parity_catalog import CampaignScenario


def _scenario(cases, name="basic") -> CampaignScenario:
    key = scenario_key(name)
    return CampaignScenario(key, name, cases[key])


# -- pure planning ---------------------------------------------------------

def test_required_chunks_tile_the_sample_and_keep_the_tail_short():
    assert store.required_chunks(1, 250) == ((0, 1),)
    assert store.required_chunks(10, 4) == ((0, 4), (4, 4), (8, 2))
    assert store.required_chunks(8, 4) == ((0, 4), (4, 4))


def test_record_coverage_prefix_and_cut_points(tmp_path):
    chunk = lambda start, count: store.SampleChunk(start, count, count, 0, 0, 0.0, "t")
    record = store.SampleRecord(
        "modular", "scenario/x", "x", 1, 50, 4, "abc", "digest", {},
        chunks=(chunk(4, 4), chunk(0, 4), chunk(12, 2)),  # gap at 8
    )
    assert record.coverage() == 8
    assert record.counts(8) == (8, 0, 0)
    assert record.counts(4) == (4, 0, 0)
    with pytest.raises(store.SampleStoreError, match="cannot be cut at 6"):
        record.counts(6)
    with pytest.raises(store.SampleStoreError, match="fewer than the 12"):
        record.counts(12)
    # Round trip through the on-disk document.
    path = tmp_path / "r.json"
    store.save_sample(path, record)
    again = store.load_sample(path)
    assert again is not None
    assert sorted(c.start for c in again.chunks) == [0, 4, 12]
    assert again.counts(8) == record.counts(8)
    assert store.load_sample(tmp_path / "absent.json") is None


def test_missing_chunks_replace_a_narrower_tail():
    chunk = lambda start, count: store.SampleChunk(start, count, count, 0, 0, 0.0, "t")
    record = store.SampleRecord(
        "native", "scenario/x", "x", 1, 50, 4, "abc", "digest", {},
        chunks=(chunk(0, 4), chunk(4, 1)),  # an earlier request of width 5
    )
    assert store.missing_chunks(record, 5) == ()
    assert store.missing_chunks(record, 10) == ((4, 4), (8, 2))


# -- engine digests ---------------------------------------------------------

def _source_tree(tmp_path, monkeypatch):
    combat = tmp_path / "combat"
    for directory in (combat / "native", combat / "modular", tmp_path / "core"):
        directory.mkdir(parents=True, exist_ok=True)
    (combat / "native" / "_combat_native.pyx").write_text("# native source\n")
    monkeypatch.setattr(store, "_ROOT", tmp_path)
    monkeypatch.setattr(store, "_COMBAT", combat)
    monkeypatch.setattr(store, "_CORE", tmp_path / "core")


def test_modular_digest_sources_exclude_the_native_package_and_kernel(tmp_path, monkeypatch):
    _source_tree(tmp_path, monkeypatch)
    modular = {p.as_posix() for p in store._modular_sources()}
    assert not any("/native/" in p or p.endswith("/kernel.py") for p in modular)
    native = {p.as_posix() for p in store._native_sources()}
    assert any("/native/_combat_native.pyx" in p for p in native)
    assert any(p.endswith("/kernel.py") for p in native)
    assert not any("/modular/" in p for p in native)
    assert store.engine_digest("modular") != store.engine_digest("native")


def test_native_only_change_keeps_the_modular_digest(tmp_path, monkeypatch):
    _source_tree(tmp_path, monkeypatch)
    before_modular = store.engine_digest("modular")
    before_native = store.engine_digest("native")
    probe = store._COMBAT / "native" / "_zz_digest_probe.py"
    assert not probe.exists()
    probe.write_text("# temporary native-only change\n")
    try:
        assert store.engine_digest("modular") == before_modular
        assert store.engine_digest("native") != before_native
    finally:
        probe.unlink()
    assert store.engine_digest("native") == before_native


# -- engine samples (tiny) ---------------------------------------------------

def test_stored_modular_chunks_reproduce_the_sequential_oracle(cases, tmp_path):
    from mordheim_combat.modular.duel import simulate_duel_reference

    scenario = _scenario(cases)
    record = store.sample_scenario(
        "modular", scenario, tmp_path, simulations=30, seed=7, maximum_rounds=50,
        chunk_size=8,
    )
    assert [(c.start, c.count) for c in sorted(record.chunks, key=lambda c: c.start)] == [
        (0, 8), (8, 8), (16, 8), (24, 6),
    ]
    direct = simulate_duel_reference(
        scenario.case.first, scenario.case.second, 30, seed=7, maximum_rounds=50,
    )
    assert record.counts(30) == (direct.first_wins, direct.second_wins, direct.unresolved)


def test_stored_native_chunks_preserve_batch_seeds(cases, tmp_path, monkeypatch):
    import mordheim_combat

    requests = []

    def simulate(request):
        requests.append(request)
        return SimpleNamespace(first_wins=request.simulations, second_wins=0, unresolved=0)

    # Exercise the sampling adapter without adding or executing a native engine
    # on this pre-migration branch.
    monkeypatch.setattr(mordheim_combat, "native", SimpleNamespace(simulate_duel=simulate), raising=False)

    scenario = _scenario(cases)
    record = store.sample_scenario(
        "native", scenario, tmp_path, simulations=30, seed=7, maximum_rounds=50,
        chunk_size=8,
    )
    assert record.counts(30) == (30, 0, 0)
    assert [request.simulations for request in requests] == [8, 8, 8, 6]
    assert [request.seed for request in requests] == [
        (7 + store.NATIVE_SEED_OFFSET + i * store.NATIVE_BATCH_STRIDE) & ((1 << 64) - 1)
        for i in range(4)
    ]


@pytest.mark.parametrize("engine", store.ENGINES)
def test_interrupted_sample_resumes_with_only_the_missing_chunks(cases, tmp_path, engine, monkeypatch):
    if engine == "native":
        monkeypatch.setattr(store, "run_native_chunk", _native_chunk)
    scenario = _scenario(cases)
    full = store.sample_scenario(
        engine, scenario, tmp_path, simulations=20, seed=11, maximum_rounds=50,
        chunk_size=5,
    )
    path = store.sample_path(tmp_path, engine, scenario.key)
    # Simulate an interruption: drop the second and last chunks from disk.
    raw = json.loads(path.read_text())
    raw["chunks"] = [c for c in raw["chunks"] if c["start"] not in (5, 15)]
    path.write_text(json.dumps(raw))
    partial = store.load_sample(path)
    assert partial is not None and partial.coverage() == 5
    assert store.missing_chunks(partial, 20) == ((5, 5), (15, 5))
    seen: list[str] = []
    resumed = store.sample_scenario(
        engine, scenario, tmp_path, simulations=20, seed=11, maximum_rounds=50,
        chunk_size=5, log=seen.append,
    )
    assert sum("saved" in line for line in seen) == 2
    assert resumed.coverage() == 20
    assert resumed.counts(20) == full.counts(20)
    # A second run has nothing to do.
    seen.clear()
    store.sample_scenario(
        engine, scenario, tmp_path, simulations=20, seed=11, maximum_rounds=50,
        chunk_size=5, log=seen.append,
    )
    assert any("nothing to run" in line for line in seen)


def test_stale_or_mismatched_sample_is_refused_unless_replaced(cases, tmp_path):
    scenario = _scenario(cases)
    store.sample_scenario(
        "modular", scenario, tmp_path, simulations=2, seed=1, maximum_rounds=50,
        chunk_size=2,
    )
    with pytest.raises(store.SampleStoreError, match="seed 1 != 2"):
        store.open_sample("modular", scenario, tmp_path, seed=2, maximum_rounds=50, chunk_size=2)
    with pytest.raises(store.SampleStoreError, match="chunk_size"):
        store.open_sample("modular", scenario, tmp_path, seed=1, maximum_rounds=50, chunk_size=3)
    path = store.sample_path(tmp_path, "modular", scenario.key)
    raw = json.loads(path.read_text())
    raw["engine_digest"] = "0" * 64
    path.write_text(json.dumps(raw))
    with pytest.raises(store.SampleStoreError, match="engine digest changed"):
        store.open_sample("modular", scenario, tmp_path, seed=1, maximum_rounds=50, chunk_size=2)
    _path, fresh = store.open_sample(
        "modular", scenario, tmp_path, seed=1, maximum_rounds=50, chunk_size=2,
        replace_stale=True,
    )
    assert fresh.chunks == ()


def _native_chunk(first, second, start, count, seed, chunk_size, maximum_rounds, context=None):
    return store.SampleChunk(start, count, count, 0, 0, 0.0, "test")


def test_compare_stored_reports_missing_samples_as_not_run_and_pairs_as_rows(cases, tmp_path, monkeypatch):
    monkeypatch.setattr(store, "run_native_chunk", _native_chunk)
    scenario = _scenario(cases)
    row, _ = store.compare_stored(scenario, tmp_path)
    assert row.status == "NOT_RUN" and "no stored modular and native sample" in row.detail
    store.sample_scenario("modular", scenario, tmp_path, simulations=4, seed=5, maximum_rounds=50, chunk_size=2)
    store.sample_scenario("native", scenario, tmp_path, simulations=6, seed=5, maximum_rounds=50, chunk_size=2)
    row, provenance = store.compare_stored(scenario, tmp_path)
    assert row.compared and row.simulations == 4  # widest common prefix
    assert provenance["compared_simulations"] == 4
    assert row.status in ("PASS", "DIVERGENCE")
    row, _ = store.compare_stored(scenario, tmp_path, simulations=3)
    assert row.status == "NOT_RUN" and "cannot be cut at 3" in row.detail
