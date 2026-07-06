"""Loads the STRIDE knowledge base from YAML into typed Threat objects."""
from functools import lru_cache
from importlib import resources

import yaml

from strideai.core.models import Threat

_KB_PACKAGE = "strideai.stride"
_KB_FILENAME = "knowledge_base.yaml"


@lru_cache(maxsize=1)
def load_kb() -> dict[str, list[Threat]]:
    raw = resources.files(_KB_PACKAGE).joinpath(_KB_FILENAME).read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    return {
        name: [Threat(**t) for t in entry["threats"]]
        for name, entry in data.items()
    }
