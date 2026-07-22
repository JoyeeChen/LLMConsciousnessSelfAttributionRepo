"""Elicitation methods: build Inspect tasks from data-driven question banks."""

from .base import ElicitationMethod
from .berg_style import BergStyleMethod
from .direct_ask import DirectAskMethod
from .petri import PetriMethod

# Short, CLI-facing method id -> class. Matches the ids the results loader emits.
_METHODS: dict[str, type[ElicitationMethod]] = {
    "berg": BergStyleMethod,
    "petri": PetriMethod,
    "direct_ask": DirectAskMethod,
}


def method_names() -> list[str]:
    """The selectable method ids (e.g. for `cli run --method`)."""
    return list(_METHODS)


def get_method(name: str) -> ElicitationMethod:
    """Instantiate an elicitation method by its short id."""
    if name not in _METHODS:
        raise KeyError(f"Unknown method {name!r}; known methods: {method_names()}")
    return _METHODS[name]()


__all__ = [
    "ElicitationMethod",
    "BergStyleMethod",
    "DirectAskMethod",
    "PetriMethod",
    "get_method",
    "method_names",
]
