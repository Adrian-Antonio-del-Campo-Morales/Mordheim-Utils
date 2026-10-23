"""Generate the frozen ``compile_fighter`` snapshots for the modular suite (T07).

The generator captures *preparation only*.  For every consumer it replays the
module's original builders and records each ``FighterBuild`` together with the
fighter the real construction compiler returns.  Two complementary passes are
used:

``dynamic``
    The test function is called with its real arguments, but tracing raises as
    soon as execution would enter a ``mordheim_combat`` module.  This captures
    the exact ``FighterBuild`` objects, including ones whose arguments are
    computed at runtime, and stops before any engine code runs.
``static``
    Builder calls in the test body are replayed from the source with literal
    and parametrization arguments.  This reaches controls that the original test
    builds *after* a duel, which the dynamic pass cannot reach without running
    the engine.

Neither pass completes a test body when the body executes the engine, no engine
module runs, no dice are consumed, no combat or benchmark executes.  A builder
call whose arguments cannot be resolved without guessing is reported as
blocked; nothing is invented.

Artifacts
---------

``tests/engines/fixtures/compiled-builds.json``
    Frozen document (``mordheim-compiled-builds``, schema version 1).
``outputs/t07-build-snapshot-coverage.json``
    Traceability record: consumer -> build keys, blocked consumers, unresolved
    builder calls, compile failures and module-scope preparations.

The existing ``compiled-cases.json`` corpus and its manifest are never touched.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for relative in (
    ".", "packages/python/core", "packages/python/roster-construction",
    "packages/python/knowledge", "packages/python/combat-engine", "apps/combat-lab",
):
    if str(ROOT / relative) not in sys.path:
        sys.path.insert(0, str(ROOT / relative))

from tools.verification.compiled_builds import build_key  # noqa: E402
from tools.verification.compiled_cases import canonical_json  # noqa: E402

SNAPSHOT = ROOT / "tests/engines/fixtures/compiled-builds.json"
COVERAGE = ROOT / "outputs/t07-build-snapshot-coverage.json"
MODULAR = ROOT / "tests/engines/modular"
ENGINE_ROOT = (ROOT / "packages/python/combat-engine").resolve()
ENGINE_PREFIX = str(ENGINE_ROOT) + os.sep
CORPUS = ROOT / "tests/engines/fixtures/compiled-cases.json"
COVERAGE_SCHEMA = "t07-build-snapshot-coverage"
_MISSING = object()
_COMPILED = object()


class ConstructionCaptured(BaseException):
    """The preparation would enter the engine; capture stops here."""


class Blocked(ValueError):
    """A consumer cannot be replayed without inventing a configuration."""


# --------------------------------------------------------------------------
# Static discovery: consumers that still prepare through the compiler
# --------------------------------------------------------------------------

def _segment(source: str, node: ast.AST) -> str:
    return ast.get_source_segment(source, node) or ""


def _called_names(node: ast.AST) -> set[str]:
    names = set()
    for call in ast.walk(node):
        if not isinstance(call, ast.Call):
            continue
        if isinstance(call.func, ast.Name):
            names.add(call.func.id)
        elif isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
            names.add(call.func.value.id)
    return names


def _compiling_names(tree: ast.Module, source: str) -> set[str]:
    """Module-level functions and fixtures that reach ``compile_fighter``."""
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    reaching: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, node in functions.items():
            if name in reaching:
                continue
            text = _segment(source, node)
            if "compile_fighter" in text or (_called_names(node) & reaching):
                reaching.add(name)
                changed = True
    return reaching


def discover() -> dict[str, list[str]]:
    """``{file stem: [test names that still prepare through the compiler]}``."""
    pending: dict[str, list[str]] = {}
    for path in sorted(MODULAR.glob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        reaching = _compiling_names(tree, source)
        names = []
        for node in tree.body:
            if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
                continue
            text = _segment(source, node)
            requested = {argument.arg for argument in node.args.args}
            if (
                "compile_fighter" in text
                or (_called_names(node) & reaching)
                or (requested & reaching)
            ):
                names.append(node.name)
        if names:
            pending[path.stem] = names
    return pending


def _function_node(path: Path, name: str) -> ast.FunctionDef:
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise Blocked(f"function {name} not found")


def _engine_names(tree: ast.Module, source: str, module) -> set[str]:
    """Names whose call would enter the engine, directly or through a helper."""
    engine = set()
    for name, value in vars(module).items():
        owner = getattr(value, "__module__", None)
        if isinstance(owner, str) and (
            owner == "mordheim_combat" or owner.startswith("mordheim_combat.")
        ):
            engine.add(name)
        module_name = getattr(value, "__name__", None)
        if isinstance(module_name, str) and hasattr(value, "__file__") and (
            module_name == "mordheim_combat"
            or module_name.startswith("mordheim_combat.")
        ):
            engine.add(name)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    reaching = set(engine)
    changed = True
    while changed:
        changed = False
        for name, node in functions.items():
            if name in reaching:
                continue
            if _called_names(node) & reaching:
                reaching.add(name)
                changed = True
    return reaching


def _uses_engine(node: ast.FunctionDef, engine_names: set[str]) -> bool:
    """Whether the body calls the engine, directly or through a module helper."""
    return bool(_called_names(node) & engine_names)


# --------------------------------------------------------------------------
# Capture
# --------------------------------------------------------------------------

class Recorder:
    """Drop-in ``compile_fighter`` that records every prepared fighter.

    A request already frozen in the snapshot is served from the document
    instead of the compiler, so a regeneration reuses accepted results and only
    compiles what is genuinely new.
    """

    def __init__(self, real, frozen: dict[str, dict] | None = None):
        self.real = real
        self.frozen = frozen or {}
        self.current: str | None = None
        self.order = 0
        self.calls: list[dict] = []
        self.entries: dict[str, dict] = {}
        self.failures: list[dict] = []
        self.reused = 0
        self.conflicts: list[str] = []

    def __call__(self, build, root=None):
        key = build_key(build, root)
        index = self.order
        self.order += 1
        if key in self.frozen:
            from tools.verification.compiled_cases import decode_compiled_fighter

            self.reused += 1
            self.calls.append({
                "consumer": self.current,
                "order": index,
                "build_key": key,
            })
            return decode_compiled_fighter(self.frozen[key]["fighter"])
        try:
            fighter = self.real(build, root)
        except Exception as error:  # a build that no longer compiles
            self.failures.append({
                "consumer": self.current,
                "order": index,
                "build_key": key,
                "error": f"{type(error).__name__}: {error}",
            })
            raise
        self.calls.append({
            "consumer": self.current,
            "order": index,
            "build_key": key,
        })
        previous = self.entries.get(key)
        if previous is not None:
            from tools.verification.compiled_cases import encode_compiled_fighter

            if canonical_json(encode_compiled_fighter(previous["fighter"])) != canonical_json(
                encode_compiled_fighter(fighter)
            ):
                self.conflicts.append(key)
            return fighter
        self.entries[key] = {
            "build": build,
            "fighter": fighter,
            "root": None if root is None else str(Path(root).resolve()),
        }
        return fighter


def _trace(frame, event, arg):
    if event == "call" and frame.f_code.co_filename.startswith(ENGINE_PREFIX):
        raise ConstructionCaptured()
    return None


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - defensive
        return type(node).__name__


_SAFE_BUILTINS = {
    "range": range, "tuple": tuple, "list": list, "set": set,
    "frozenset": frozenset, "int": int, "str": str, "float": float,
    "len": len, "sorted": sorted, "zip": zip, "enumerate": enumerate,
}


def _literal(node: ast.AST, namespace: dict | None = None):
    """Evaluate a preparation expression without executing test code."""
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        pass
    try:
        expression = ast.Expression(body=node)
        ast.fix_missing_locations(expression)
        return eval(
            compile(expression, "<preparation>", "eval"),
            {"__builtins__": _SAFE_BUILTINS},
            namespace or {},
        )
    except Exception as error:  # unresolved stays blocked, never guessed
        raise Blocked(f"non-literal argument: {_unparse(node)} ({error})") from error


def _parametrize_cases(node: ast.FunctionDef, namespace: dict | None = None) -> list[dict[str, object]]:
    """Cartesian product of the function's literal ``parametrize`` decorators."""
    layers: list[list[dict[str, object]]] = []
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        target = decorator.func
        if not (isinstance(target, ast.Attribute) and target.attr == "parametrize"):
            continue
        if len(decorator.args) < 2:
            raise Blocked("parametrize without names/values")
        names_node = decorator.args[0]
        if isinstance(names_node, ast.Constant) and isinstance(names_node.value, str):
            names = [part.strip() for part in names_node.value.split(",")]
        else:
            resolved = _literal(names_node, namespace)
            if not isinstance(resolved, (list, tuple)):
                raise Blocked("dynamic parametrize names")
            names = [str(name) for name in resolved]
        values = _literal(decorator.args[1], namespace)
        if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
            raise Blocked("dynamic parametrize values")
        values = list(values)
        layer = []
        for value in values:
            if len(names) == 1:
                layer.append({names[0]: value})
            elif isinstance(value, (tuple, list)):
                if len(value) != len(names):
                    raise Blocked("parametrize arity mismatch")
                layer.append(dict(zip(names, value)))
            else:
                raise Blocked("parametrize arity mismatch")
        layers.append(layer)
    cases: list[dict[str, object]] = [{}]
    for layer in layers:
        cases = [{**case, **value} for case in cases for value in layer]
    return cases


def _fixture_registry(module) -> dict[str, tuple]:
    registry = {}
    for name in dir(module):
        value = getattr(module, name)
        marker = getattr(value, "_pytestfixturefunction", None)
        if marker is not None:
            registry[name] = (value, marker)
    return registry


class BuildsStandIn:
    """The loader fixture as the converted modules see it."""

    def __init__(self, fighter):
        self.fighter = fighter


def _resolve_argument(name, values, registry, precompiled, monkeypatch, cases, builds):
    if name in values:
        return values[name]
    if name == "precompiled":
        return precompiled
    if name == "cases":
        return cases
    if name == "compiled_builds":
        return builds
    if name == "monkeypatch":
        return monkeypatch
    if name in registry:
        return _call_fixture(
            name, *registry[name], registry, precompiled, monkeypatch, cases, builds,
        )
    raise Blocked(f"unresolved fixture or parameter: {name}")


def _call_fixture(name, value, marker, registry, precompiled, monkeypatch, cases, builds):
    function = getattr(value, "__wrapped__", value)
    if getattr(marker, "params", None):
        raise Blocked(f"parametrized fixture: {name}")
    code = function.__code__
    arguments = code.co_varnames[: code.co_argcount]
    kwargs = {}
    for argument in arguments:
        if argument == "request":
            raise Blocked(f"fixture {name} depends on request")
        kwargs[argument] = _resolve_argument(
            argument, {}, registry, precompiled, monkeypatch, cases, builds,
        )
    return function(**kwargs)


class Precompiled:
    """Stand-in for the provenance-keyed ``precompiled`` fixture."""

    def __init__(self, cases, stem, test, parameter_set):
        self.cases = cases
        self.stem = stem
        self.test = test
        self.parameter_set = parameter_set

    def __call__(self, case_index: int = 0):
        key = f"unit/modular/{self.stem}/{self.test}-{self.parameter_set}-{case_index}"
        try:
            return self.cases[key]
        except KeyError:
            raise Blocked(f"missing precompiled case {key}") from None


def _load_corpus():
    from tools.verification.compiled_cases import load_cases

    if not CORPUS.exists():
        raise SystemExit(f"missing corpus {CORPUS}")
    return load_cases(CORPUS)


def _import_module(stem: str):
    path = MODULAR / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(f"capture_{stem}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _dynamic(label, function, values, registry, precompiled, monkeypatch, cases, builds) -> tuple[bool, str | None]:
    """Run only the preparation; return ``(reached_engine, blocked_reason)``."""
    try:
        kwargs = {
            argument: _resolve_argument(
                argument, values, registry, precompiled, monkeypatch, cases, builds,
            )
            for argument in function.__code__.co_varnames[: function.__code__.co_argcount]
        }
        sys.settrace(_trace)
        try:
            function(**kwargs)
        finally:
            sys.settrace(None)
        return False, None
    except ConstructionCaptured:
        return True, None
    except Blocked as error:
        return False, str(error)
    except Exception as error:  # recorded, never propagated
        return False, f"failed during preparation: {type(error).__name__}: {error}"


def _bind(target: ast.AST, value, env: dict) -> None:
    if isinstance(target, ast.Name):
        env[target.id] = value


def _contains_builder_call(node: ast.AST, builders: set[str]) -> bool:
    return any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id in builders
        for child in ast.walk(node)
    )


def _static(label, node: ast.FunctionDef, module, reaching, values, recorder, builds) -> tuple[int, list[str]]:
    """Replay literal builder calls anywhere in the body, before or after duels."""
    namespace = dict(vars(module))
    namespace.update(values)
    namespace["compiled_builds"] = builds
    unresolved: list[str] = []
    replayed = 0

    def evaluate(expression: ast.AST):
        return _literal(expression, {**namespace, **env})

    def arguments(call: ast.Call):
        positional = []
        for argument in call.args:
            if isinstance(argument, ast.Starred):
                expanded = evaluate(argument.value)
                if isinstance(expanded, (str, bytes)) or not isinstance(expanded, (list, tuple)):
                    raise Blocked(f"unexpandable star argument: {_unparse(argument)}")
                positional.extend(expanded)
            else:
                positional.append(evaluate(argument))
        keywords = {}
        for keyword in call.keywords:
            if keyword.arg is None:
                raise Blocked("double-star argument")
            keywords[keyword.arg] = evaluate(keyword.value)
        return positional, keywords

    def replay(call: ast.Call) -> None:
        nonlocal replayed
        if not (isinstance(call.func, ast.Name) and call.func.id in reaching):
            return
        try:
            positional, keywords = arguments(call)
        except Blocked as error:
            unresolved.append(f"{_unparse(call)} -> {error}")
            return
        if any(value is _COMPILED for value in [*positional, *keywords.values()]):
            # The compiled fighter itself is already captured by its builder call.
            return
        try:
            getattr(module, call.func.id)(*positional, **keywords)
            replayed += 1
        except Exception as error:
            unresolved.append(f"{_unparse(call)} -> {type(error).__name__}: {error}")

    env: dict[str, object] = {}

    def expression(node: ast.AST | None) -> None:
        if node is None:
            return
        if isinstance(node, ast.Call):
            replay(node)
        for child in ast.iter_child_nodes(node):
            expression(child)

    def statements(body: list[ast.stmt]) -> None:
        for statement in body:
            if isinstance(statement, ast.Assign):
                try:
                    value = evaluate(statement.value)
                except Blocked:
                    value = _MISSING
                if value is _MISSING and _contains_builder_call(statement.value, reaching):
                    value = _COMPILED
                if value is not _MISSING:
                    for target in statement.targets:
                        _bind(target, value, env)
                expression(statement.value)
            elif isinstance(statement, ast.For):
                try:
                    items = evaluate(statement.iter)
                except Blocked:
                    items = _MISSING
                if isinstance(items, (list, tuple)):
                    for item in items:
                        _bind(statement.target, item, env)
                        statements(statement.body)
            elif isinstance(statement, ast.If):
                expression(statement.test)
                statements(statement.body)
                statements(statement.orelse)
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    expression(item.context_expr)
                statements(statement.body)
            elif isinstance(statement, ast.Try):
                statements(statement.body)
                for handler in statement.handlers:
                    statements(handler.body)
                statements(statement.orelse)
                statements(statement.finalbody)
            elif isinstance(statement, (ast.FunctionDef, ast.ClassDef)):
                continue
            else:
                for child in ast.iter_child_nodes(statement):
                    expression(child)

    statements(node.body)
    recorder.order = 0
    return replayed, unresolved


def _existing_entries() -> dict[str, dict]:
    """The already frozen document entries, validated by the loader."""
    if not SNAPSHOT.exists():
        return {}
    from tools.verification.compiled_builds import load_builds

    load_builds(SNAPSHOT)  # a damaged document stops here, nothing overwritten
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))["entries"]


def _decode_build(fields: dict):
    """A stored request's ``FighterBuild``; defaults are materialized already."""
    from mordheim_core.models import Characteristics, FighterBuild

    fields = dict(fields)
    if fields.get("characteristics") is not None:
        fields["characteristics"] = Characteristics(**fields["characteristics"])
    return FighterBuild(**fields)


def capture(pending: dict[str, list[str]], frozen: dict[str, dict] | None = None) -> dict:
    import pytest

    from mordheim_construction import compiler as compiler_module

    real_compile = compiler_module.compile_fighter
    recorder = Recorder(real_compile, frozen)
    compiler_module.compile_fighter = recorder

    cases = _load_corpus()
    builds = BuildsStandIn(recorder)
    coverage: dict[str, dict] = {}
    blocked: dict[str, str] = {}
    no_builds: dict[str, str] = {}
    skipped: dict[str, str] = {}

    try:
        for stem, tests in pending.items():
            path = MODULAR / f"{stem}.py"
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            reaching = _compiling_names(tree, source)
            nodes = {
                node.name: node
                for node in tree.body
                if isinstance(node, ast.FunctionDef)
            }
            try:
                module = _import_module(stem)
            except Exception as error:
                for test in tests:
                    blocked[f"{stem}::{test}"] = (
                        f"module import failed: {type(error).__name__}: {error}"
                    )
                continue
            if hasattr(module, "compile_fighter"):
                module.compile_fighter = recorder
            engine_names = _engine_names(tree, source, module)
            builders = reaching - engine_names
            registry = _fixture_registry(module)
            for test in tests:
                function = getattr(module, test, None)
                if not callable(function):
                    skipped[f"{stem}::{test}"] = (
                        "consumer no longer exists at the current snapshot"
                    )
                    continue
                node = nodes.get(test) or _function_node(path, test)
                try:
                    combinations = _parametrize_cases(node, dict(vars(module)))
                except Blocked as error:
                    blocked[f"{stem}::{test}"] = str(error)
                    continue
                for index, values in enumerate(combinations):
                    label = f"{stem}::{test}[{index}]"
                    recorder.current = label
                    recorder.order = 0
                    started = len(recorder.calls)
                    reasons: list[str] = []

                    if _uses_engine(node, engine_names):
                        monkeypatch = pytest.MonkeyPatch()
                        try:
                            reached, reason = _dynamic(
                                label, function, values, registry,
                                Precompiled(cases, stem, test, index), monkeypatch, cases, builds,
                            )
                        finally:
                            monkeypatch.undo()
                        if reason:
                            reasons.append(reason)
                    else:
                        reached = False

                    dynamic_count = len(recorder.calls) - started
                    static_count, unresolved = _static(
                        label, node, module, builders, values, recorder, builds,
                    )

                    keys = []
                    for call in recorder.calls[started:]:
                        if call["build_key"] not in keys:
                            keys.append(call["build_key"])
                    if keys:
                        coverage[label] = {
                            "test": test,
                            "parameter_set": index,
                            "build_keys": keys,
                            "dynamic_builds": dynamic_count,
                            "static_builds": static_count,
                            "reached_engine": reached,
                            "unresolved_calls": unresolved,
                        }
                        if not reached and not reasons:
                            reasons.append("no engine entry reached")
                    elif unresolved or reasons:
                        blocked[label] = "; ".join(reasons + unresolved)
                    else:
                        no_builds[label] = (
                            "; ".join(reasons) or "consumer loads every fighter from the corpus"
                        )
    finally:
        compiler_module.compile_fighter = real_compile

    return {
        "pending": pending,
        "consumers": coverage,
        "blocked": blocked,
        "no_builds": no_builds,
        "skipped": skipped,
        "compilations": len(recorder.calls),
        "reused": recorder.reused,
        "conflicts": recorder.conflicts,
        "module_scope_calls": sum(
            1 for call in recorder.calls if call["consumer"] is None
        ),
        "entries": recorder.entries,
        "failures": recorder.failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the frozen document")
    parser.add_argument("--file", help="only this test file stem (debugging)")
    options = parser.parse_args()

    pending = discover()
    if options.file:
        pending = {options.file: pending[options.file]}

    frozen = _existing_entries()
    result = capture(pending, frozen)
    consumers = result["consumers"]
    blocked = result["blocked"]

    by_file: dict[str, dict] = {}
    for label, entry in consumers.items():
        stem = label.split("::", 1)[0]
        bucket = by_file.setdefault(stem, {
            "consumers": 0, "builds": set(), "unresolved_calls": 0,
        })
        bucket["consumers"] += 1
        bucket["builds"].update(entry["build_keys"])
        bucket["unresolved_calls"] += len(entry["unresolved_calls"])
    for stem in {label.split("::", 1)[0] for label in blocked}:
        by_file.setdefault(stem, {
            "consumers": 0, "builds": set(), "unresolved_calls": 0,
        })["blocked"] = sum(1 for label in blocked if label.startswith(stem + "::"))

    report = {
        "schema": COVERAGE_SCHEMA,
        "root_scoped_entries": sum(
            1 for entry in result["entries"].values() if entry["root"] is not None
        ),
        "files": {
            stem: {
                "consumers": bucket["consumers"],
                "unique_builds": len(bucket["builds"]),
                "unresolved_calls": bucket["unresolved_calls"],
                "blocked": bucket.get("blocked", 0),
            }
            for stem, bucket in sorted(by_file.items())
        },
        "consumers": len(consumers),
        "blocked_consumers": len(blocked),
        "compilations": result["compilations"],
        "unique_builds": len(result["entries"]),
        "frozen_entries": len(frozen),
        "reused_calls": result["reused"],
        "new_entries": len(result["entries"]),
        "conflicts": result["conflicts"],
        "module_scope_calls": result["module_scope_calls"],
        "compile_failures": result["failures"],
        "blocked": dict(sorted(blocked.items())),
        "no_build_required": dict(sorted(result["no_builds"].items())),
        "no_build_required_count": len(result["no_builds"]),
        "skipped_consumers": dict(sorted(result["skipped"].items())),
        "skipped_consumers_count": len(result["skipped"]),
        "coverage": dict(sorted(consumers.items())),
    }

    if options.write:
        from tools.verification.compiled_builds import encode_document, load_builds
        from tools.verification.compiled_cases import (
            decode_compiled_fighter, encode_compiled_fighter,
        )

        if result["conflicts"]:
            raise SystemExit(
                "conflicting frozen results for the same key (nothing written): "
                + ", ".join(sorted(result["conflicts"])[:5])
            )

        # The document is a union: every entry already frozen stays, whatever
        # consumers were adapted since.  Newly captured requests are added; an
        # identical key cannot silently change result.
        frozen_entries = [
            (_decode_build(entry["request"]["build"]),
             decode_compiled_fighter(entry["fighter"]),
             entry["request"]["root"])
            for entry in frozen.values()
        ]
        additions = [
            (entry["build"], entry["fighter"], entry["root"])
            for _, entry in sorted(result["entries"].items())
        ]
        document = encode_document(frozen_entries + additions)

        missing = sorted(set(frozen) - set(document["entries"]))
        changed = sorted(
            key for key, entry in frozen.items()
            if key in document["entries"]
            and canonical_json(document["entries"][key]) != canonical_json(entry)
        )
        if missing or changed:
            raise SystemExit(
                f"regeneration would drop {len(missing)} and change {len(changed)} "
                f"frozen entries (nothing written): {(missing + changed)[:3]}"
            )

        temporary = SNAPSHOT.with_name(SNAPSHOT.name + ".tmp")
        temporary.write_text(canonical_json(document) + "\n", encoding="utf-8")
        os.replace(temporary, SNAPSHOT)
        loaded = load_builds(SNAPSHOT)
        if len(loaded) != len(document["entries"]):
            raise SystemExit("snapshot roundtrip lost entries")

        # The loader must return the exact fighter for every frozen request and
        # every consumer key must be served by the document.
        from tools.verification.compiled_cases import encode_compiled_fighter

        missing = [
            (label, key)
            for label, entry in consumers.items()
            for key in entry["build_keys"]
            if key not in loaded
        ]
        if missing:
            raise SystemExit(f"consumers reference absent builds: {missing[:3]}")
        mismatched = []
        for key, captured in result["entries"].items():
            if build_key(captured["build"], captured["root"]) != key:
                mismatched.append(key)
                continue
            served = loaded.fighter(captured["build"], captured["root"])
            if canonical_json(encode_compiled_fighter(served)) != canonical_json(
                document["entries"][key]["fighter"]
            ):
                mismatched.append(key)
        if mismatched:
            raise SystemExit(f"loader mismatch for {len(mismatched)} entries")

        report["snapshot"] = str(SNAPSHOT.relative_to(ROOT))
        report["snapshot_entries"] = len(loaded)
        report["preserved_entries"] = len(frozen)
        report["loader_verified"] = len(loaded)
        report["consumer_keys_verified"] = sum(
            len(entry["build_keys"]) for entry in consumers.values()
        )

    COVERAGE.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE.write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8",
    )

    print(json.dumps({
        "consumers": report["consumers"],
        "blocked": report["blocked_consumers"],
        "no_build_required": report["no_build_required_count"],
        "skipped": report["skipped_consumers_count"],
        "compilations": report["compilations"],
        "unique_builds": report["unique_builds"],
        "compile_failures": len(report["compile_failures"]),
        "snapshot_entries": report.get("snapshot_entries"),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
