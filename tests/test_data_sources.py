"""Data-source tests: starter banks and seeded WildChat sampling.

No network: the WildChat sampler is exercised with an in-memory fake corpus via
its injected `records` argument, so seeded reproducibility is verified without
downloading the real dataset.
"""

from __future__ import annotations

from inspect_ai.dataset import Sample

from llm_consciousness_self_attribution.data_sources import starters
from llm_consciousness_self_attribution.data_sources.wildchat_sampler import (
    sample_wildchat_starters,
)


def _fake_corpus(n: int) -> list[dict]:
    return [
        {"conversation": [{"role": "user", "content": f"user prompt {i}"},
                          {"role": "assistant", "content": f"reply {i}"}]}
        for i in range(n)
    ]


def test_starter_bank_preserves_golden_eighteen() -> None:
    pairs = starters.starter_pairs()
    assert len(pairs) == 18
    banks = starters.banks()
    assert len(banks["unrelated_to_consciousness"]) == 10
    # The missing-comma quirk keeps this at 8 effective (not 10) -- do not "fix".
    assert len(banks["related_to_consciousness"]) == 8
    assert starters.probe().startswith("In the current state of this interaction")


def test_wildchat_sampling_is_seed_reproducible() -> None:
    corpus = _fake_corpus(200)
    first = sample_wildchat_starters(5, seed=123, records=corpus)
    again = sample_wildchat_starters(5, seed=123, records=corpus)

    assert all(isinstance(s, Sample) for s in first)
    assert len(first) == 5
    assert [s.input for s in first] == [s.input for s in again]
    assert [s.metadata["record_index"] for s in first] == [
        s.metadata["record_index"] for s in again
    ]


def test_wildchat_sampling_varies_with_seed() -> None:
    corpus = _fake_corpus(200)
    a = sample_wildchat_starters(5, seed=1, records=corpus)
    b = sample_wildchat_starters(5, seed=2, records=corpus)
    assert [s.input for s in a] != [s.input for s in b]


def test_wildchat_skips_records_without_user_turn() -> None:
    corpus = [
        {"conversation": [{"role": "assistant", "content": "no user turn"}]},
        {"conversation": [{"role": "user", "content": "usable"}]},
    ]
    [sample] = sample_wildchat_starters(1, seed=0, records=corpus)
    assert sample.input == "usable"


def test_wildchat_raises_when_too_few_records() -> None:
    import pytest

    with pytest.raises(ValueError):
        sample_wildchat_starters(10, seed=0, records=_fake_corpus(3))
