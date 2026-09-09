"""Loader for the browsable rules catalogues of ``catalog/rules``.

The RULES browser needs every prose rules document in one validated
catalogue: ``special-rules``, ``conditions``, ``core-combat``,
``resolution``, ``racial-maximums`` and ``implemented-canonical-families``.
The typed loaders that already exist (``load_skills``, ``load_items``,
``load_shared_rules``, ``load_racial_maximums``) stay canonical for their
domains; this module only adds the shared validation pass so one bad file
cannot silently drop out of the browser.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mordheim_knowledge.campaign import _assert_unique_ids
from mordheim_knowledge.loader import knowledge_root, read_yaml

RULES_CATALOGUE_DIR = "catalog/rules"


@dataclass(frozen=True, slots=True)
class RulesCatalog:
    """Validated rules documents keyed by catalogue file name stem."""

    documents: dict[str, dict]  # read-only by convention

    def document(self, name: str) -> dict:
        """Return one document by file name or stem (``special-rules``)."""
        stem = name[:-5] if name.endswith(".yaml") else name
        try:
            return self.documents[stem]
        except KeyError as exc:
            raise ValueError(f"unknown rules catalogue: {name}") from exc

    def stems(self) -> tuple[str, ...]:
        return tuple(sorted(self.documents))


def load_rules_catalog(
    ruleset: str = "mordheim", root: Path | None = None
) -> RulesCatalog:
    """Load every ``catalog/rules`` document with the header contract."""
    base = (root or knowledge_root()) / RULES_CATALOGUE_DIR
    documents: dict[str, dict] = {}
    for path in sorted(base.glob("*.yaml")):
        document = read_yaml(path)
        # Engineering manifests (e.g. implemented-canonical-families) carry no
        # ruleset header and are not browsable prose: skip them.
        if document.get("ruleset") is None:
            continue
        if document.get("ruleset") != ruleset:
            raise ValueError(
                f"rules document {path.name}: ruleset {document.get('ruleset')!r} "
                f"does not match {ruleset!r}"
            )
        _assert_unique_ids(document, path.name)
        documents[path.stem] = document
    return RulesCatalog(documents)
