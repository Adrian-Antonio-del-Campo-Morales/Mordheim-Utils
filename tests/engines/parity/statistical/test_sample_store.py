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
            chunk_size=1, executor=executor, workers=2, stop=stop, log=log, verbose=True,
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


@pytest.mark.parametrize("compress", [False, True])
def test_e2e_cli_samples_resumes_and_compares(tmp_path, compress):
    from tests.engines.parity.statistical.test_e2e_parity import CASES

    key = CASES["simple"]
    selection = ["--level", "e2e", "--id", key, "--store", str(tmp_path)]
    command = ["sample", "--engine", "modular", *selection,
               "--simulations", "2", "--chunk", "1", "--workers", "1"]
    if compress:
        command.append("--compress")
    assert store.main(command) == 0
    path = store.sample_path(tmp_path, "modular", key)
    assert path.name.endswith(".json.gz" if compress else ".json")
    record = store.load_sample(path)
    assert record is not None and record.coverage() == 2
    assert record.maximum_rounds == 50
    original = path.read_bytes()
    # A completed sample must resume without rewriting or running more duels.
    assert store.main(command) == 0
    assert path.read_bytes() == original
    # Resuming without the flag preserves compressed records too.
    assert store.main([arg for arg in command if arg != "--compress"]) == 0
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


@pytest.mark.parametrize("verbose", [False, True])
def test_sample_cli_logs_case_elapsed_time_and_optional_chunks(cases, tmp_path, monkeypatch, capsys, verbose):
    scenario = _scenario(cases)
    ticks = iter((10.0, 12.0, 20.0, 21.0))
    monkeypatch.setattr(store.time, "perf_counter", lambda: next(ticks))
    monkeypatch.setattr(store, "run_modular_chunk", lambda first, second, start, count, *args:
                        store.SampleChunk(start, count, count, 0, 0, 0.0, "t"))
    command = ["sample", "--engine", "modular", "--id", scenario.key,
               "--simulations", "2", "--chunk", "1", "--store", str(tmp_path)]
    if verbose:
        command.append("--verbose")
    assert store.main(command) == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if scenario.key in line]
    assert len(lines) == (4 if verbose else 2)
    assert ": started " in lines[0]
    assert ": complete in 2.00s; coverage 2" in lines[-1]
    assert sum("saved" in line for line in lines) == (2 if verbose else 0)
    # Already-complete cases keep the same two-line summary without rerunning.
    assert store.main(command) == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if scenario.key in line]
    assert len(lines) == 2
    assert ": complete in 1.00s;" in lines[-1] and "nothing to run" in lines[-1]


# -- pure planning ---------------------------------------------------------

def test_required_chunks_tile_the_sample_and_keep_the_tail_short():
    assert store.required_chunks(1, 250) == ((0, 1),)
    assert store.required_chunks(10, 4) == ((0, 4), (4, 4), (8, 2))
    assert store.required_chunks(8, 4) == ((0, 4), (4, 4))


@pytest.mark.parametrize("suffix", [".json", ".json.gz"])
def test_record_coverage_prefix_and_cut_points(tmp_path, suffix):
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
    path = store.sample_path(tmp_path, "modular", "scenario/x").with_suffix(suffix)
    store.save_sample(path, record)
    again = store.load_sample(path)
    assert again is not None
    assert sorted(c.start for c in again.chunks) == [0, 4, 12]
    assert again.counts(8) == record.counts(8)
    assert store.sample_path(tmp_path, "modular", "scenario/x") == path
    assert store.load_sample(path.with_suffix("") if suffix == ".json.gz" else path) == again
    assert store.load_sample(tmp_path / "absent.json") is None


def test_missing_chunks_replace_a_narrower_tail():
    chunk = lambda start, count: store.SampleChunk(start, count, count, 0, 0, 0.0, "t")
    record = store.SampleRecord(
        "native", "scenario/x", "x", 1, 50, 4, "abc", "digest", {},
        chunks=(chunk(0, 4), chunk(4, 1)),  # an earlier request of width 5
    )
    assert store.missing_chunks(record, 5) == ()
    assert store.missing_chunks(record, 10) == ((4, 4), (8, 2))


@pytest.mark.parametrize("winerror,failures,attempts", [
    (5, 2, 3), (32, 2, 3), (33, 2, 3),
    (5, 100, 7), (None, 100, 1), (28, 100, 1),
])
def test_save_sample_retries_only_transient_windows_locks(
    tmp_path, monkeypatch, winerror, failures, attempts,
):
    from dataclasses import replace

    path = tmp_path / "sample.json"
    original = store.SampleRecord("modular", "scenario/x", "x", 1, 50, 1, "abc", "digest", {})
    store.save_sample(path, original)
    old_bytes = path.read_bytes()
    updated = replace(original, chunks=(store.SampleChunk(0, 1, 1, 0, 0, 0.0, "t"),))
    real_replace = store.os.replace
    calls = []
    delays = []

    def locked_replace(source, destination):
        calls.append((source, destination))
        assert path.read_bytes() == old_bytes
        assert store.load_sample(source) == updated
        if len(calls) <= failures:
            error = OSError(28, "disk full") if winerror == 28 else PermissionError("locked")
            if winerror is not None:
                error.winerror = winerror
            raise error
        real_replace(source, destination)

    monkeypatch.setattr(store.os, "replace", locked_replace)
    monkeypatch.setattr(store.time, "sleep", delays.append)
    if failures < attempts:
        store.save_sample(path, updated)
        assert store.load_sample(path) == updated
        assert not path.with_suffix(".json.tmp").exists()
    else:
        with pytest.raises(OSError):
            store.save_sample(path, updated)
        assert path.read_bytes() == old_bytes
        assert store.load_sample(path.with_suffix(".json.tmp")) == updated
    assert len(calls) == attempts
    assert delays == [0.05, 0.1, 0.2, 0.4, 0.8, 1.0][:attempts - 1]


# -- engine digests ---------------------------------------------------------

def _source_tree(tmp_path, monkeypatch):
    combat = tmp_path / "combat"
    for directory in (combat / "native", combat / "modular", tmp_path / "core"):
        directory.mkdir(parents=True, exist_ok=True)
    (combat / "native" / "_combat_native.pyx").write_text("# native source\n")
    monkeypatch.setattr(store, "_ROOT", tmp_path)
    monkeypatch.setattr(store, "_COMBAT", combat)
    monkeypatch.setattr(store, "_CORE", tmp_path / "core")


def test_digest_sources_follow_what_each_engine_executes(tmp_path, monkeypatch):
    _source_tree(tmp_path, monkeypatch)
    for directory in ("vectorized",):
        (store._COMBAT / directory).mkdir(parents=True, exist_ok=True)
    (store._COMBAT / "modular" / "state.py").write_text("# modular helper\n")
    (store._COMBAT / "vectorized" / "_driver.py").write_text("# vectorized driver\n")
    modular = {p.as_posix() for p in store._modular_sources()}
    assert not any("/native/" in p or "/vectorized/" in p or p.endswith("/kernel.py") for p in modular)
    native = {p.as_posix() for p in store._native_sources()}
    assert any("/native/_combat_native.pyx" in p for p in native)
    assert any(p.endswith("/kernel.py") for p in native)
    # The candidates import modular and vectorized helpers, so those count.
    assert any(p.endswith("/modular/state.py") for p in native)
    assert any(p.endswith("/vectorized/_driver.py") for p in native)
    assert not any(p.endswith(".so") or p.endswith(".pyd") for p in native)
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
        chunk_size=5, log=seen.append, verbose=True,
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


def _modular_chunk(first, second, start, count, seed, maximum_rounds, context=None):
    return store.SampleChunk(start, count, count, 0, 0, 0.0, "test")


def test_identity_mismatch_is_refused_but_another_engine_version_only_warns(cases, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(store, "run_modular_chunk", _modular_chunk)
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
    _path, stored = store.open_sample("modular", scenario, tmp_path, seed=1, maximum_rounds=50, chunk_size=2)
    assert len(stored.chunks) == 1
    capsys.readouterr()
    extended = store.sample_scenario(
        "modular", scenario, tmp_path, simulations=4, seed=1, maximum_rounds=50, chunk_size=2,
    )
    err = capsys.readouterr().err
    assert "PROVENANCE WARNING" in err and "mixes engine versions" in err
    old, new = sorted(extended.chunks, key=lambda chunk: chunk.start)
    assert old.provenance is None
    assert new.provenance["engine_digest"] == store.engine_digest("modular")
    assert extended.engine_digest == "0" * 64  # the record keeps its own origin
    assert store.load_sample(path).chunks == extended.chunks
    _path, fresh = store.open_sample(
        "modular", scenario, tmp_path, seed=1, maximum_rounds=50, chunk_size=2,
        replace_stale=True,
    )
    assert fresh.chunks == ()


def test_a_source_change_during_the_run_marks_the_chunks_saved_after_it(cases, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(store, "run_modular_chunk", _modular_chunk)
    calls = iter(range(1000))
    # Run start and record creation see "a"; every later save sees "b".
    monkeypatch.setattr(store, "engine_digest",
                        lambda engine: ("a" if next(calls) < 2 else "b") * 64)
    record = store.sample_scenario(
        "modular", _scenario(cases), tmp_path, simulations=4, seed=1, maximum_rounds=50, chunk_size=2,
    )
    assert "changed during this run" in capsys.readouterr().err
    assert record.engine_digest == "a" * 64
    assert all(chunk.provenance["sources_changed_during_run"] for chunk in record.chunks)
    assert {chunk.provenance["engine_digest_at_save"] for chunk in record.chunks} == {"b" * 64}


def _native_chunk(first, second, start, count, seed, chunk_size, maximum_rounds, context=None):
    return store.SampleChunk(start, count, count, 0, 0, 0.0, "test")


@pytest.mark.parametrize("backend", ["native", "numpy"])
def test_compare_stored_reports_missing_samples_as_not_run_and_pairs_as_rows(cases, tmp_path, monkeypatch, backend):
    monkeypatch.setattr(store, "run_native_chunk", _native_chunk)
    monkeypatch.setattr(store, "run_modular_chunk", _modular_chunk)
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
    # Four duels stay within any tolerance but cannot decide anything.
    assert result == 1
    report = json.loads((tmp_path / "compare" / "parity-campaign.json").read_text())
    assert report["config"]["candidate_backend"] == backend
    assert report["scenarios"][0]["verdict"] in ("underpowered", "divergent")
    row, _ = store.compare_stored(scenario, tmp_path, simulations=3, backend=backend, reference_store=reference)
    assert row.status == "NOT_RUN" and "cannot be cut at 3" in row.detail


@pytest.mark.parametrize("backend", ["native", "numpy"])
def test_compare_decides_stale_samples_and_warns_about_them(cases, tmp_path, monkeypatch, capsys, backend):
    monkeypatch.setattr(store, "run_native_chunk", _native_chunk)
    monkeypatch.setattr(store, "run_numpy_chunk", _native_chunk)
    monkeypatch.setattr(store, "run_modular_chunk", _modular_chunk)
    # Independent of this checkout's own state: samples taken at a clean commit.
    monkeypatch.setattr(store, "_REVISION", {"commit": "c" * 40, "dirty": False})
    scenario = _scenario(cases)
    reference = tmp_path / "reference"
    # Stubbed chunks: a sample wide enough for an approvable verdict costs nothing.
    store.sample_scenario("modular", scenario, reference, simulations=8_000, seed=5, maximum_rounds=50, chunk_size=4_000)
    store.sample_scenario(backend, scenario, tmp_path, simulations=8_000, seed=5, maximum_rounds=50, chunk_size=4_000)
    path = store.sample_path(reference, "modular", scenario.key)
    raw = json.loads(path.read_text())
    raw["engine_digest"] = "0" * 64
    raw["environment"]["dirty"] = True
    path.write_text(json.dumps(raw))
    row, provenance = store.compare_stored(scenario, tmp_path, backend=backend, reference_store=reference)
    assert row.compared and row.status == "PASS"  # the verdict ignores provenance
    warnings = provenance["modular"]["warnings"]
    assert any("another modular engine version" in item for item in warnings)
    assert any("uncommitted changes" in item for item in warnings)
    assert provenance[backend]["warnings"] == []
    capsys.readouterr()
    command = ["compare", "--backend", backend, "--id", scenario.key, "--store", str(tmp_path),
               "--reference-store", str(reference), "--simulations", "8000"]
    assert store.main(command) == 0
    out = capsys.readouterr()
    assert "PROVENANCE WARNING: 1 stored modular sample(s) produced by another modular engine version" in out.err
    report = json.loads((tmp_path / "compare" / "parity-campaign.json").read_text())
    assert len(report["provenance_warnings"]) == 2
    assert report["config"]["recorded_engine_digests"]["modular"] == ["0" * 64]
    markdown = (tmp_path / "compare" / "parity-campaign.md").read_text()
    assert "## Provenance warnings" in markdown


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


def test_an_engine_imported_from_elsewhere_is_digested_where_it_ran(cases, tmp_path, monkeypatch, capsys):
    scenario = _scenario(cases)
    real = store._COMBAT
    expected = store.engine_digest("numpy")
    monkeypatch.setattr(store, "_COMBAT", tmp_path / "elsewhere" / "mordheim_combat")
    command = ["sample", "--engine", "numpy", "--id", scenario.key, "--simulations", "4",
               "--chunk", "2", "--store", str(tmp_path / "store")]
    assert store.main(command) == 0
    assert "PROVENANCE WARNING: mordheim_combat was imported from" in capsys.readouterr().err
    assert store._COMBAT == real.resolve()
    record = store.load_sample(store.sample_path(tmp_path / "store", "numpy", scenario.key))
    assert record.engine_digest == expected


def test_pool_workers_must_import_the_parent_engine(cases, tmp_path, monkeypatch, capsys):
    scenario = _scenario(cases)
    origins = store.engine_origins("numpy")
    # The parent claims another engine copy; every real worker then disagrees.
    monkeypatch.setattr(store, "check_engine_origins",
                        lambda engine: {**origins, "mordheim_combat": "/elsewhere/__init__.py"})
    command = ["sample", "--engine", "numpy", "--id", scenario.key, "--simulations", "4",
               "--chunk", "2", "--workers", "2", "--store", str(tmp_path / "store")]
    assert store.main(command) == 2
    assert "worker pool failed" in capsys.readouterr().err
    assert store.load_sample(store.sample_path(tmp_path / "store", "numpy", scenario.key)) is None
