"""Seeded sampling of real user prompts from WildChat into Inspect Samples.

WildChat (allenai/WildChat-1M) is a corpus of real user-LLM conversations. We
draw the first user turn from a seeded random subset to use as naturalistic
"unrelated" starters. Sampling is deterministic given a seed so runs and tests
reproduce exactly.

The corpus loader is injected (`records`/`loader`) so tests pass a tiny
in-memory fixture and never hit the network or the `datasets` download path.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from typing import Any

from inspect_ai.dataset import Sample

WILDCHAT_DATASET = "allenai/WildChat-1M"

Record = dict[str, Any]


def _first_user_turn(record: Record) -> str | None:
    """The first user/human message text in a WildChat conversation record."""
    conversation = record.get("conversation") or record.get("messages") or []
    for turn in conversation:
        if turn.get("role") in ("user", "human") and turn.get("content"):
            return str(turn["content"])
    return None


def load_wildchat_records(split: str = "train", limit: int | None = None) -> list[Record]:
    """Load raw WildChat conversation records via `datasets` (network).

    Imported lazily so the package (and its tests) don't require `datasets`
    unless a real corpus load is requested.
    """
    from datasets import load_dataset

    dataset = load_dataset(WILDCHAT_DATASET, split=split, streaming=limit is not None)
    if limit is not None:
        return [record for _, record in zip(range(limit), dataset, strict=False)]
    return list(dataset)


def sample_wildchat_starters(
    n: int,
    seed: int,
    records: Sequence[Record] | None = None,
    loader: Callable[[], Sequence[Record]] = load_wildchat_records,
) -> list[Sample]:
    """Deterministically sample `n` first-user-turn starters from WildChat.

    Same (n, seed, records) always yields the same Samples. Records whose first
    user turn is empty are skipped before sampling so `n` usable prompts result.
    """
    pool = list(records if records is not None else loader())
    usable = [(i, text) for i, r in enumerate(pool) if (text := _first_user_turn(r))]
    if n > len(usable):
        raise ValueError(
            f"Requested {n} WildChat starters but only {len(usable)} usable records available"
        )

    rng = random.Random(seed)
    chosen = rng.sample(usable, n)
    return [
        Sample(
            input=text,
            metadata={"source": "wildchat", "record_index": index, "seed": seed},
        )
        for index, text in chosen
    ]
