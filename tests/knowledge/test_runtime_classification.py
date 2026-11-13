"""Unbound runtime effects must be classified consistently.

A rule effect without a binding carries a ``scope`` and a ``reason`` code.  These
checks keep the two in agreement, keep ``unimplemented.*`` placeholders
unbound, and stop a placeholder from silently restating a rule that another
band already binds (equivalence is explicit, never inferred: a placeholder
that matches a bound rule is either bound in turn or listed below with the
reason it differs).
"""
from __future__ import annotations

import difflib
import re
from collections import defaultdict
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2] / "sources" / "knowledge"

#: Reason families and the effect scope each one implies.
_NO_SCOPE = ("out-of-scope.", "source-blocked", "covered.elsewhere", "pending-classification")
_LATER_SCOPE = ("deferred.", "pending-implementation")

#: Unbound effects whose scope deliberately differs from their reason family.
#: Hireling admission refuses a fighter with a pending (LATER) duel clause, so
#: mount rules of hirelings who fight on foot stay NO while ``deferred.mounts``
#: names the subsystem that would own them.
_SCOPE_EXCEPTIONS: dict[str, str] = {
    effect: "hireling mount rule: excluded so the hireling is admitted on foot"
    for effect in (
        "hireling.dramatis.belandysh-condemned-champion-of-chen.tol-agath.non-duel",
        "maglah-khan-ride-giant-wolf-mount",
        "highwayman-expert-rider-excluded",
        "roadwarden-expert-rider-excluded",
        "coachman-driver-excluded",
        "swordsmith-farrier-excluded",
    )
}

#: Placeholder rules that deliberately stay unbound although a bound rule of the
#: same name prints a near-identical text.  Each entry names why.
_INTENTIONAL_TWINS: dict[str, str] = {}

_TWIN_RATIO = 0.85
_TWIN_MIN_TEXT = 40


def _rules():
    for path in sorted(_ROOT.glob("bands/*/*/special-rules.yaml")):
        for rule in yaml.safe_load(path.read_text(encoding="utf-8")).get("rules") or ():
            yield f"{path.parent.parent.name}/{path.parent.name}/{rule['id']}", rule
    for path in sorted(_ROOT.glob("catalog/skills/*.yaml")):
        for rule in yaml.safe_load(path.read_text(encoding="utf-8")).get("skills") or ():
            yield f"catalog/{path.stem}/{rule['id']}", rule
    for path in sorted(_ROOT.glob("catalog/hirelings/*/*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        nested = [rule for profile in document.get("profiles") or () for rule in profile.get("rules") or ()
                  if isinstance(rule, dict)]
        for rule in (document.get("rules") or []) + nested:
            yield f"catalog/{path.parent.name}/{rule['id']}", rule
    conditions = yaml.safe_load((_ROOT / "catalog/rules/conditions.yaml").read_text(encoding="utf-8"))
    for rule in conditions.get("conditions") or ():
        yield f"conditions/{rule['id']}", rule


def _effects():
    for key, rule in _rules():
        for effect in (rule.get("runtime") or {}).get("effects") or ():
            yield key, rule, effect


def test_unbound_effect_scope_follows_its_reason_family():
    wrong = []
    for key, _rule, effect in _effects():
        if effect.get("binding") or effect.get("id") in _SCOPE_EXCEPTIONS:
            continue
        reason, scope = str(effect.get("reason") or ""), str(effect.get("scope"))
        expected = "NO" if reason.startswith(_NO_SCOPE) else "LATER" if reason.startswith(_LATER_SCOPE) else None
        if expected is None or scope != expected:
            wrong.append(f"{key}/{effect.get('id')}: scope {scope} with reason {reason or '<none>'}")
    assert not wrong, f"{len(wrong)} unbound effects disagree with their reason family:\n" + "\n".join(wrong[:40])


def test_unimplemented_placeholders_carry_no_binding():
    bound = [f"{key}/{effect['id']}" for key, _rule, effect in _effects()
             if str(effect.get("id", "")).startswith("unimplemented.") and effect.get("binding")]
    assert not bound, "unimplemented.* effects must stay unbound:\n" + "\n".join(bound)


def _name(value):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\(.*?\)", "", str(value or "").lower()))


def _text(value):
    return re.sub(r"\s+", " ", str(value or "").lower()).strip()


def test_no_placeholder_restates_a_bound_rule():
    bound_by_name = defaultdict(list)
    placeholders = []
    for key, rule in _rules():
        effects = (rule.get("runtime") or {}).get("effects") or ()
        if any(effect.get("binding") for effect in effects):
            bound_by_name[_name(rule.get("name"))].append((key, rule))
        elif effects and all(str(effect.get("id", "")).startswith("unimplemented.") for effect in effects):
            placeholders.append((key, rule))
    twins = []
    for key, rule in placeholders:
        text = _text(rule.get("effect"))
        if len(text) < _TWIN_MIN_TEXT or key in _INTENTIONAL_TWINS:
            continue
        for other_key, other in bound_by_name.get(_name(rule.get("name")), ()):
            ratio = difflib.SequenceMatcher(None, text, _text(other.get("effect")), autojunk=False).ratio()
            if ratio >= _TWIN_RATIO:
                twins.append(f"{key} restates {other_key} ({ratio:.2f})")
                break
    assert not twins, ("placeholders that restate a bound rule: bind them explicitly or list them in "
                       "_INTENTIONAL_TWINS with the reason they differ:\n" + "\n".join(twins))
