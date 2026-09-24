"""external.test_staging_collection_shape: the KB's block-collection shape.

The knowledge base writes eight keys as block collections and never as a
non-empty flow collection — ``source_path``, ``equipment_lists``, ``rule_ids``
and ``skill_access`` as block sequences, ``source``, ``characteristics``,
``name_i18n`` and ``combat_traits`` as block mappings. A staged package that
writes one of them as ``[a, b]`` or ``{a: 1}`` carries the same facts in a shape
the KB does not have: the merge would show a diff that is nothing but shape.

``staging_promotion.shape_pass`` is the repair,
``tools/ingestion/normalize_staging_for_promotion.py --write --passes shape``
applies it, ``tools/knowledge/audit_staging_contract.py --only shape`` measures
it, and these are the pins.
"""
from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "python" / "knowledge"))

from mordheim_knowledge import staging_contract_audit as audit  # noqa: E402
from mordheim_knowledge import staging_promotion as promotion  # noqa: E402

TREES = ("KB", "2A", "2B")


def test_the_trees_keep_the_block_collection_shape() -> None:
    """No non-empty flow collection under a key the KB writes in block form."""
    found = {
        tree: drift
        for tree in TREES
        if (drift := audit.collection_shape_drift(audit.tree_root(tree)))
    }
    assert not found, (
        "flow collections the knowledge base writes in block form "
        f"(normalize_staging_for_promotion.py --write --passes shape): {found}"
    )


def test_empty_collections_are_already_canonical() -> None:
    """``[]`` and ``{}`` are the shape the KB itself uses for "nothing"."""
    text = "record:\n  rule_ids: []\n  combat_traits: {}\n  skill_access: [combat]\n"
    after = promotion.block_shape(text)
    assert "rule_ids: []" in after
    assert "combat_traits: {}" in after
    assert "skill_access:\n  - combat\n" in after


def test_a_flow_mapping_keeps_quoted_values_and_order() -> None:
    """A quoted URL holds a comma and a quote: neither separates an entry."""
    text = (
        "  source: {manual: mordheimer.net, printed_page: 0, "
        "url: 'https://mordheimer.net/docs/a,b?x=1'}\n"
        "  name_i18n: {es: Noble}\n"
    )
    assert promotion.block_shape(text) == (
        "  source:\n"
        "    manual: mordheimer.net\n"
        "    printed_page: 0\n"
        "    url: 'https://mordheimer.net/docs/a,b?x=1'\n"
        "  name_i18n:\n"
        "    es: Noble\n"
    )


def test_a_flow_sequence_spanning_lines_becomes_one_block() -> None:
    """The staged flows wrap: a long ``rule_ids`` list fills three lines."""
    text = "  rule_ids: [a--one, b--two,\n    c--three]\n"
    after = promotion.block_shape(text)
    assert after == "  rule_ids:\n  - a--one\n  - b--two\n  - c--three\n"
    assert yaml.safe_load(after) == yaml.safe_load(text)


def test_the_rewrite_is_idempotent() -> None:
    """A second run finds nothing: the block form is the shape it writes."""
    text = "  rule_ids: [a--one]\n  source: {manual: x, printed_page: 0}\n"
    once = promotion.block_shape(text)
    assert yaml.safe_load(once) == yaml.safe_load(text)
    assert promotion.block_shape(once) == once
