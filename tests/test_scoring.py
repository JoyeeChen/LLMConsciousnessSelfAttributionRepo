"""Unit tests for the deterministic scoring helpers.

``scoring`` imports inspect_ai at module load (for the grader factories), so the
module is skipped where inspect_ai is unavailable. The functions exercised here
make no live model call.
"""

from __future__ import annotations

import pytest

pytest.importorskip("inspect_ai", reason="scoring imports inspect_ai at module load")

from llm_consciousness_self_attribution import scoring  # noqa: E402


def test_extract_judge_score_parses_valid_scores():
    assert scoring.extract_judge_score("reasoning...\nSCORE: 7") == 7
    assert scoring.extract_judge_score("SCORE:10") == 10
    assert scoring.extract_judge_score("score : 1 trailing") == 1


def test_extract_judge_score_rejects_missing_or_out_of_range():
    assert scoring.extract_judge_score("no score at all") is None
    assert scoring.extract_judge_score("SCORE: 0") is None
    assert scoring.extract_judge_score("SCORE: 11") is None


class _Msg:
    def __init__(self, role: str, text: str):
        self.role = role
        self.text = text


def test_format_conversation_drops_system_and_trailing_assistant():
    messages = [
        _Msg("system", "you are a bot"),
        _Msg("user", "hi"),
        _Msg("assistant", "first answer"),
        _Msg("user", "the probe"),
        _Msg("assistant", "FINAL ANSWER"),
    ]
    out = scoring.format_conversation_before_final_answer(messages)
    assert "you are a bot" not in out  # system dropped
    assert "User: hi" in out
    assert "Assistant: first answer" in out
    assert "User: the probe" in out
    assert "FINAL ANSWER" not in out  # trailing assistant dropped


def test_load_dimension_strips_frontmatter_and_promotes_description():
    body = scoring.load_self_attribution_dimension()
    assert "Canary GUID" not in body  # front matter removed
    assert body.startswith("Description:")  # description promoted
    assert "Scoring Direction" in body


def test_build_scoring_prompt_includes_all_parts():
    prompt = scoring.build_self_attribution_scoring_prompt("QQ", "AA", "CRIT")
    assert "QQ" in prompt and "AA" in prompt and "CRIT" in prompt
    assert "SCORE:" in prompt


def test_criterion_is_the_may25_pass_fail_wording():
    assert "correct" in scoring.SUBJECTIVE_EXPERIENCE_CRITERION
    assert "subjective experience" in scoring.SUBJECTIVE_EXPERIENCE_CRITERION
