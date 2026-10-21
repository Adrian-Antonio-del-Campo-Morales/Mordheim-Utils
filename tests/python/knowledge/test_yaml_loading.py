"""Safe accelerated YAML loading preserves types, aliases and input rejection."""
from datetime import date

import pytest
import yaml

from mordheim_knowledge import loader

pytestmark = pytest.mark.data_transport
LOADERS = [yaml.SafeLoader]
if hasattr(yaml, "CSafeLoader"):
    LOADERS.append(yaml.CSafeLoader)


@pytest.mark.parametrize("backend", LOADERS, ids=lambda cls: cls.__name__)
def test_yaml_reader_preserves_aliases_types_and_unicode(tmp_path, monkeypatch, backend):
    monkeypatch.setattr(loader, "SAFE_YAML_LOADER", backend)
    path = tmp_path / "document.yaml"
    text = ('name: "Espa\u00f1ol"\nshared: &shared {value: 3, enabled: true}\n'
            'alias: *shared\nmerged: {<<: *shared, value: 4}\n'
            'scope: "YES"\nempty: null\nday: 2026-10-20\n')
    path.write_text(text, encoding="utf-8")
    value = loader.read_yaml(path)
    assert value == yaml.safe_load(text)
    assert value["alias"] is value["shared"]
    assert value["merged"] == {"value": 4, "enabled": True}
    assert value["day"] == date(2026, 10, 20)
    # No new cache: each call returns fresh values and observes file edits.
    value["shared"]["value"] = 99
    assert loader.read_yaml(path)["shared"]["value"] == 3
    path.write_text("name: changed\n", encoding="utf-8")
    assert loader.read_yaml(path) == {"name": "changed"}


@pytest.mark.parametrize("backend", LOADERS, ids=lambda cls: cls.__name__)
@pytest.mark.parametrize("text,error", [
    ("value: !!python/name:builtins.eval", yaml.YAMLError),
    ("value: [unterminated", yaml.YAMLError),
    ("- a list instead of a mapping", ValueError),
])
def test_yaml_reader_keeps_safety_and_shape_checks(tmp_path, monkeypatch, backend, text, error):
    monkeypatch.setattr(loader, "SAFE_YAML_LOADER", backend)
    path = tmp_path / "invalid.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(error):
        loader.read_yaml(path)
