"""Self-contained artifact loaders used by RICO provenance stages."""

from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path) -> object:
    """Load one UTF-8 JSON artifact."""

    return json.loads(path.read_text(encoding="utf-8"))
