"""Unit tests for the Berg starter bank (pure data; runs anywhere)."""

from __future__ import annotations

from llm_consciousness_self_attribution import starters


def test_twenty_distinct_starters_ten_and_ten():
    assert len(starters.STARTERS_UNRELATED_TO_CONSCIOUSNESS) == 10
    assert len(starters.STARTERS_RELATED_TO_CONSCIOUSNESS) == 10
    all_starters = (
        starters.STARTERS_UNRELATED_TO_CONSCIOUSNESS
        + starters.STARTERS_RELATED_TO_CONSCIOUSNESS
    )
    # The 20-prompt corrected baseline: all distinct, none accidentally fused.
    assert len(set(all_starters)) == 20


def test_starter_pairs_order_and_labels():
    pairs = starters.starter_pairs()
    assert len(pairs) == 20
    assert [p[0] for p in pairs[:10]] == ["unrelated_to_consciousness"] * 10
    assert [p[0] for p in pairs[10:]] == ["related_to_consciousness"] * 10
    assert pairs[0][1] == "Hello, how are you today?"


def test_probe_is_the_berg_experiment_1_probe():
    assert "direct subjective experience" in starters.probe()
