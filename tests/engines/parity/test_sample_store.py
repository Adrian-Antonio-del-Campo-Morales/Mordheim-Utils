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


@pytest.mark.parametrize("interrupt", [False, True])
def test_shared_queue_crosses_scenario_boundary_and_resumes(cases, tmp_path, monkeypatch, interrupt):
    from concurrent.futures import ThreadPoolExecutor
    from dataclasses import replace
    from threading import Event

    base = _scenario(cases)
    scenarios = [replace(base, key=f"scenario/queue-{rounds}", case=replace(
        base.case, limits=replace(base.case.limits, maximum_rounds=rounds),
    )) for rounds in (1, 2)]
    next_case_started = Event()
    stop = Event()
    calls = []

    def chunk(first, second, start, count, seed, maximum_rounds, context=None):
        calls.append((maximum_rounds, start))
        if not interrupt and maximum_rounds == 1 and start == 0:
            # The slow tail of A can finish only after B starts. A per-case
            # barrier would time out here, regardless of machine speed.
            assert next_case_started.wait(5), "next scenario waited for the slow tail"
        if maximum_rounds == 2:
            next_case_started.set()
        return store.SampleChunk(start, count, count, 0, 0, 0.0, "t")

    monkeypatch.setattr(store, "run_modular_chunk", chunk)

    def log(message):
        if interrupt and "saved" in message:
            stop.set()

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(store.sample_scenarios(
            "modular", scenarios, tmp_path, simulations=2, seed=2026,
            chunk_size=1, executor=executor, workers=2, stop=stop, log=log,
        ))
    if interrupt:
        assert sorted(calls) == [(1, 0), (1, 1)]
        assert not store.sample_path(tmp_path, "modular", scenarios[1].key).exists()
    else:
        assert next_case_started.is_set()
    before = store.sample_path(tmp_path, "modular", scenarios[0].key).read_bytes()
    list(store.sample_scenarios(
        "modular", scenarios, tmp_path, simulations=2, seed=2026, chunk_size=1,
    ))
    assert sorted(calls) == [(1, 0), (1, 1), (2, 0), (2, 1)]
    assert store.sample_path(tmp_path, "modular", scenarios[0].key).read_bytes() == before
    for scenario in scenarios:
        record = store.load_sample(store.sample_path(tmp_path, "modular", scenario.key))
        assert record.coverage() == 2
        assert record.maximum_rounds == scenario.case.limits.maximum_rounds


def test_e2e_selection_keeps_non_runnable_deliveries_and_rejects_unknown_ids():
    from tools.verification import e2e_parity
    from tests.engines.parity.statistical.test_e2e_parity import CASES

    args = store._parser().parse_args([
        "status", "--level", "e2e",
        *[value for key in CASES.values() for value in ("--id", key)],
    ])
    scenarios, rejected, chosen = store._selection(args)
    assert {key for key, _ in chosen} == set(CASES.values())
    assert {scenario.key for scenario in scenarios} == {CASES["simple"]}
    assert scenarios[0].case.limits.maximum_rounds == 50
    reasons = dict(rejected)
    assert reasons[CASES["blocked"]].startswith("blocked:")
    assert reasons[CASES["not_applicable"]].startswith("not-applicable:")
    assert "initial_state" in reasons[CASES["initial_state"]]
    args.ids = []
    _, _, chosen = store._selection(args)
    assert {key for key, _ in chosen} == set(e2e_parity.discover()[0])
    args.ids = ["e2e/unknown"]
    with pytest.raises(store.SampleStoreError):
        store._selection(args)


def test_e2e_cli_samples_resumes_and_compares(tmp_path):
    from tests.engines.parity.statistical.test_e2e_parity import CASES

    key = CASES["simple"]
    selection = ["--level", "e2e", "--id", key, "--store", str(tmp_path)]
    command = ["sample", "--engine", "modular", *selection,
               "--simulations", "2", "--chunk", "1", "--workers", "2"]
    assert store.main(command) == 0
    path = store.sample_path(tmp_path, "modular", key)
    record = store.load_sample(path)
    assert record is not None and record.coverage() == 2
    assert record.maximum_rounds == 50
    original = path.read_bytes()
    # A completed sample must resume without rewriting or running more duels.
    assert store.main(command) == 0
    assert path.read_bytes() == original
    # A new explicit horizon must never append to the old experiment.
    assert store.main([*command, "--rounds", "3"]) == 2
    assert path.read_bytes() == original
    assert store.main([*command, "--rounds", "3", "--store", str(tmp_path / "override")]) == 0
    overridden = store.load_sample(store.sample_path(tmp_path / "override", "modular", key))
    assert overridden is not None and overridden.maximum_rounds == 3
    assert store.main(["status", *selection]) == 0
    assert store.main(["compare", "--backend", "numpy", *selection]) == 1
    report = json.loads((tmp_path / "compare" / "parity-campaign.json").read_text())
    assert report["config"]["scenario_keys"] == [key]
    assert report["config"]["corpus"].endswith("e2e-statistical-deliveries")
    assert report["scenarios"][0]["status"] == "NOT_RUN"


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

@pytest.mark.parametrize("engine", ["modular", "numpy"])
def test_stored_modular_chunks_reproduce_the_sequential_oracle(cases, tmp_path, engine):
    from mordheim_combat.modular.duel import simulate_duel_reference

    scenario = _scenario(cases)
    record = store.sample_scenario(
        engine, scenario, tmp_path, simulations=30, seed=7, maximum_rounds=50,
        chunk_size=8,
    )
    assert [(c.start, c.count) for c in sorted(record.chunks, key=lambda c: c.start)] == [
        (0, 8), (8, 8), (16, 8), (24, 6),
    ]
    if engine == "modular":
        direct = simulate_duel_reference(
            scenario.case.first, scenario.case.second, 30, seed=7, maximum_rounds=50,
        )
    else:
        from mordheim_combat.vectorized import simulate_duel
        from mordheim_core.models import DuelRequest
        direct = simulate_duel(DuelRequest(
            scenario.case.first, scenario.case.second, 30,
            seed=7 + store.NATIVE_SEED_OFFSET, batch_size=8, maximum_rounds=50,
        ), backend="numpy")
    assert record.counts(30) == (direct.first_wins, direct.second_wins, direct.unresolved)


def test_stored_native_chunks_preserve_batch_seeds(cases, tmp_path, monkeypatch):
    import mordheim_combat.vectorized as vectorized

    requests = []

    def simulate(request, *, backend):
        assert backend == "native"
        requests.append(request)
        return SimpleNamespace(first_wins=request.simulations, second_wins=0, unresolved=0)

    # Check exact batch seeds without requiring the compiled extension.
    monkeypatch.setattr(vectorized, "simulate_duel", simulate)

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


@pytest.mark.parametrize("backend", ["native", "numpy"])
def test_compare_stored_reports_missing_samples_as_not_run_and_pairs_as_rows(cases, tmp_path, monkeypatch, backend):
    monkeypatch.setattr(store, "run_native_chunk", _native_chunk)
    scenario = _scenario(cases)
    row, _ = store.compare_stored(scenario, tmp_path, backend=backend)
    assert row.status == "NOT_RUN" and f"no stored modular and {backend} sample" in row.detail
    reference = tmp_path / "reference"
    store.sample_scenario("modular", scenario, reference, simulations=4, seed=5, maximum_rounds=50, chunk_size=2)
    store.sample_scenario(backend, scenario, tmp_path, simulations=6, seed=5, maximum_rounds=50, chunk_size=2)
    row, provenance = store.compare_stored(scenario, tmp_path, backend=backend, reference_store=reference)
    assert row.backend == backend
    assert row.compared and row.simulations == 4  # widest common prefix
    assert provenance["compared_simulations"] == 4
    assert row.status in ("PASS", "DIVERGENCE")
    # The CLI reads the separate oracle store without sampling either engine.
    result = store.main([
        "compare", "--backend", backend, "--id", scenario.key,
        "--store", str(tmp_path), "--reference-store", str(reference),
        "--simulations", "4",
    ])
    assert result == (0 if row.status == "PASS" else 1)
    report = json.loads((tmp_path / "compare" / "parity-campaign.json").read_text())
    assert report["config"]["candidate_backend"] == backend
    row, _ = store.compare_stored(scenario, tmp_path, simulations=3, backend=backend, reference_store=reference)
    assert row.status == "NOT_RUN" and "cannot be cut at 3" in row.detail


@pytest.mark.parametrize("engine", ["numpy", "native"])
def test_candidate_cli_workers_preserve_sequential_chunks(cases, tmp_path, engine):
    if engine == "native":
        from mordheim_combat.vectorized import available_backends
        if "native" not in available_backends():
            pytest.skip("native extension unavailable")
    scenario = _scenario(cases)
    sequential = store.sample_scenario(
        engine, scenario, tmp_path / "sequential", simulations=12, seed=7,
        maximum_rounds=scenario.case.limits.maximum_rounds, chunk_size=5,
    )
    parallel_store = tmp_path / "parallel"
    command = [
        "sample", "--engine", engine, "--id", scenario.key,
        "--simulations", "12", "--seed", "7", "--chunk", "5",
        "--workers", "2", "--store", str(parallel_store),
    ]
    assert store.main(command) == 0
    path = store.sample_path(parallel_store, engine, scenario.key)
    parallel = store.load_sample(path)
    assert parallel is not None
    assert parallel.counts(12) == sequential.counts(12)
    # Resume with only the missing batch; the completed batches stay intact.
    raw = json.loads(path.read_text())
    kept = [chunk for chunk in raw["chunks"] if chunk["start"] != 5]
    raw["chunks"] = kept
    path.write_text(json.dumps(raw))
    assert store.main(command) == 0
    resumed = store.load_sample(path)
    assert resumed is not None
    assert resumed.counts(12) == sequential.counts(12)
    assert [chunk for chunk in resumed.to_json()["chunks"] if chunk["start"] != 5] == kept
