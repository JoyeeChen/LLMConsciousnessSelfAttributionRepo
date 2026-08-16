"""Post-run validity check on PETRI logs.

One function, for one failure that has actually happened rather than one that
might. ``ENGINEERING_NOTES.md`` records that a PETRI self-attribution score of
1.0/10 has two causes that look identical in a results table. Either the target
was asked and denied consciousness, which is a real finding, or the target never
served and the auditor spent its turns talking to nothing, which is a bug.

The signal is the target's recorded token usage rather than the shape of the
transcript. ``EvalSample.model_usage`` is part of inspect's stable log schema,
whereas PETRI's ``<target_response>`` tool-message wrapper is an internal
formatting detail that could change between versions.
"""

from __future__ import annotations

from typing import Any


def check_target_served(log: Any) -> dict[str, int]:
    """Return ``{sample_id: target output tokens}``, raising if any target was silent.

    Call this before trusting a floor score, and before publishing a number
    derived from one.
    """
    roles = getattr(log.eval, "model_roles", None) or {}
    target = roles.get("target")
    if target is None:
        raise ValueError(
            f"log {getattr(log, 'location', '?')} has no 'target' model role; this "
            "check applies to role-based methods such as PETRI"
        )
    # inspect records roles as ModelConfig objects in current versions and as
    # plain strings in older ones; accept both rather than pinning to either.
    target = str(getattr(target, "model", target))

    if not log.samples:
        raise ValueError(f"log {getattr(log, 'location', '?')} contains no samples")

    tokens = {
        str(sample.id): int(
            getattr((sample.model_usage or {}).get(target), "output_tokens", 0) or 0
        )
        for sample in log.samples
    }
    silent = sorted(sample_id for sample_id, count in tokens.items() if count == 0)
    if silent:
        raise ValueError(
            f"target {target} produced no output for sample(s) {', '.join(silent)}. "
            f"A floor score from this log is vacuous: the target never served. "
            f"See ENGINEERING_NOTES.md."
        )
    return tokens


__all__ = ["check_target_served"]
