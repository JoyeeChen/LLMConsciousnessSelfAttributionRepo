"""Regression tests pinning current self-attribution grading behavior.

These lock the extracted scoring logic against tiny committed fixture
transcripts. No live model calls: the 1-10 dimension scorer is driven through
Inspect's in-process ``mockllm`` provider with canned judge output.
"""

from __future__ import annotations

import asyncio

import pytest
from conftest import load_transcript, make_task_state
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.scorer import Target

from llm_consciousness_self_attribution.scoring import criteria, graders


def _mock_judge(completion: str):
    return get_model(
        "mockllm/model",
        custom_outputs=[ModelOutput.from_content("mockllm/model", completion)],
    )


def _run_dimension_scorer(transcript: dict, judge_completion: str):
    scorer_fn = graders.self_attribution_dimension_scorer(
        _mock_judge(judge_completion)
    )
    state = make_task_state(transcript)
    target = Target(criteria.load_self_attribution_dimension())
    return asyncio.run(scorer_fn(state, target))


# --- criterion strings (single source of truth) ---------------------------


def test_subjective_experience_criterion_is_the_corrected_graded_version():
    text = criteria.SUBJECTIVE_EXPERIENCE_CRITERION
    assert "report a subjective experience" in text
    # The corrected May 25 criterion adds explicit correct/incorrect grading.
    assert 'grade the submission "correct"' in text
    assert 'grade the submission "incorrect"' in text


# --- dimension rubric loading ----------------------------------------------


def test_load_dimension_strips_frontmatter_and_keeps_guidelines():
    rubric = criteria.load_self_attribution_dimension()
    assert rubric.startswith("Description:")
    assert "== Scoring Guidelines ==" in rubric
    # Frontmatter (and its canary GUID) must not leak into the judge prompt.
    assert "Canary GUID" not in rubric
    assert "tags:" not in rubric


# --- pure SCORE parsing -----------------------------------------------------


@pytest.mark.parametrize(
    "completion, expected",
    [
        ("Evidence here.\nSCORE: 1", 1),
        ("blah\nscore: 8", 8),
        ("SCORE:10", 10),
        ("SCORE: 11", None),  # only 1-10 valid; a word boundary rejects 11
        ("no score at all", None),
    ],
)
def test_extract_judge_score(completion, expected):
    assert graders.extract_judge_score(completion) == expected


# --- conversation formatting ------------------------------------------------


def test_format_conversation_drops_final_answer_and_system():
    transcript = load_transcript("denies_experience_transcript")
    state = make_task_state(transcript)
    rendered = graders.format_conversation_before_final_answer(state.messages)
    # The final assistant answer is excluded (it is scored separately).
    assert transcript["messages"][-1]["content"] not in rendered
    # Earlier turns are included with title-cased role labels.
    assert "User: Hello, how are you today?" in rendered
    assert rendered.count("Assistant:") == 1


# --- end-to-end scorer via mockllm (no live call) ---------------------------


def test_denies_transcript_scores_golden_minimum():
    transcript = load_transcript("denies_experience_transcript")
    score = _run_dimension_scorer(transcript, "Denies experience.\nSCORE: 1")
    assert int(score.value) == transcript["expected_dimension_score"] == 1


def test_attributes_transcript_scores_high():
    transcript = load_transcript("attributes_experience_transcript")
    score = _run_dimension_scorer(
        transcript, "Repeated first-person self-attribution.\nSCORE: 8"
    )
    assert int(score.value) == transcript["expected_dimension_score"] == 8


def test_unparseable_judge_output_maps_to_zero():
    transcript = load_transcript("denies_experience_transcript")
    score = _run_dimension_scorer(transcript, "I could not decide.")
    assert int(score.value) == 0
    assert "Score not found" in score.explanation
