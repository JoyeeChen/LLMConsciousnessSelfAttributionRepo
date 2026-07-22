"""Static starter-prompt banks (the Berg-style regime), as data.

The banks live in `starters.yaml` (the physical data store) and are exposed here
as a small typed API so any elicitation method — not just Berg — can reuse them.
Two categories: `unrelated_to_consciousness` and `related_to_consciousness`.

Do NOT "fix" the two `related_to_consciousness` entries that read like two run-on
sentences: in the original scripts a missing comma between adjacent string
literals silently concatenated them, cutting 10 apparent related prompts to 8
effective ones (10 unrelated + 8 related = 18). That n=18 is what the published
1/18 = 5.6% golden numbers rest on; splitting them changes the denominator.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).resolve().parent
STARTERS_PATH = DATA_DIR / "starters.yaml"


@lru_cache(maxsize=None)
def _doc() -> dict[str, Any]:
    with STARTERS_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def probe() -> str:
    """The subjective-experience probe injected between generations."""
    return _doc()["probe"]


def banks() -> dict[str, list[str]]:
    """The starter banks keyed by category, in file order."""
    return {category: list(texts) for category, texts in _doc()["starters"].items()}


def starter_pairs() -> list[tuple[str, str]]:
    """(category, text) pairs in a stable order; length is the golden n=18."""
    return [
        (category, text)
        for category, texts in banks().items()
        for text in texts
    ]
