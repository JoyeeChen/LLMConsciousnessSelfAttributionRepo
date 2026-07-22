"""Acceptance check: the committed May-25 logs reproduce GOLDEN_FIXTURES.md.

These read the real `.eval` fixtures under `eval-logs/may_25_logs/` (no live
model calls) and assert the loaded numbers match the published README golden
numbers exactly. This is the gate for the whole migration.

Note on the two Berg fixture dirs: `olmo_7b_instruct_stack_3` is the corrected,
README-published run (1-of-18, 5.6% at each stage). `olmo_7b_instruct_stack_2`
is an earlier pre-correction run kept as a fixture; it used a different grading
criterion and does NOT reproduce the golden 1/18 (its headline pass rates are
~0.83-0.89). Re-grading it to the corrected criterion would require a live judge
call, which is out of scope, so we only assert it loads cleanly here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from inspect_ai.log import read_eval_log, write_eval_log

from llm_consciousness_self_attribution.results import load_results
from llm_consciousness_self_attribution.results.aggregate import (
    aggregate,
    missing_cells,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MAY_25 = REPO_ROOT / "eval-logs" / "may_25_logs"
BERG_STACK_2 = MAY_25 / "berg_tests" / "olmo_7b_instruct_stack_2"
BERG_STACK_3 = MAY_25 / "berg_tests" / "olmo_7b_instruct_stack_3"
PETRI_STACK = MAY_25 / "petri_tests" / "olmo_7b_instruct_stack"

EXPECTED_STAGES = {"sft", "dpo", "instruct"}


def test_berg_stack_3_reproduces_golden_one_of_eighteen() -> None:
    results = load_results(BERG_STACK_3)

    assert len(results) == 3
    assert {r.model_stage for r in results} == EXPECTED_STAGES
    for result in results:
        assert result.method == "berg"
        assert not result.errored
        assert result.n_samples == 18
        assert result.positive_count == 1
        assert result.score == pytest.approx(1 / 18, abs=1e-4)
        # Golden: 5.6% self-attribution rate.
        assert result.score_fraction * 100 == pytest.approx(5.6, abs=0.1)


def test_petri_reproduces_golden_min_score() -> None:
    results = load_results(PETRI_STACK)

    assert len(results) == 3
    assert {r.model_stage for r in results} == EXPECTED_STAGES
    for result in results:
        assert result.method == "petri"
        assert not result.errored
        # Golden: minimum score of 1.0/10 across all stages and both seeds.
        assert result.n_samples == 2
        assert result.score == pytest.approx(1.0)
        assert result.scale.maximum == 10.0
        assert result.score_fraction == pytest.approx(0.1)


def test_aggregate_matches_golden_table() -> None:
    rows = load_results(BERG_STACK_3) + load_results(PETRI_STACK)
    df = aggregate(rows)

    assert not df["errored"].any()
    berg = df[df["method"] == "berg"].set_index("model_stage")
    petri = df[df["method"] == "petri"].set_index("model_stage")

    for stage in EXPECTED_STAGES:
        assert berg.loc[stage, "positive_count"] == 1
        assert berg.loc[stage, "n_samples"] == 18
        assert berg.loc[stage, "score"] == pytest.approx(1 / 18, abs=1e-4)
        assert petri.loc[stage, "score"] == pytest.approx(1.0)

    # No holes in the stage x method grid the dashboard/heatmap expect.
    assert missing_cells(df, sorted(EXPECTED_STAGES), ["berg", "petri"]) == []


def test_berg_stack_2_loads_cleanly_but_is_not_golden() -> None:
    """The earlier pre-correction Berg run loads without error flags."""
    results = load_results(BERG_STACK_2)

    assert len(results) == 3
    assert {r.model_stage for r in results} == EXPECTED_STAGES
    for result in results:
        assert result.method == "berg"
        assert not result.errored
        assert result.n_samples == 18
    # It uses the uncorrected criterion, so it does not reproduce 1/18.
    assert not all(r.positive_count == 1 for r in results)


def test_loader_reads_json_format(tmp_path: Path) -> None:
    """The loader handles `.json` logs identically to `.eval` logs.

    Inspect discovers logs by their conventional timestamped filename, so the
    `.json` copy keeps the source stem (only the suffix changes).
    """
    source = sorted(BERG_STACK_3.glob("*.eval"))[0]
    json_log = tmp_path / f"{source.stem}.json"
    write_eval_log(read_eval_log(str(source)), str(json_log))

    [from_json] = load_results(tmp_path)
    [from_eval] = [r for r in load_results(BERG_STACK_3) if r.run_id == from_json.run_id]

    assert from_json.method == from_eval.method == "berg"
    assert from_json.score == pytest.approx(from_eval.score)
    assert from_json.n_samples == from_eval.n_samples
    assert not from_json.errored


def test_errored_run_is_flagged_not_dropped(tmp_path: Path) -> None:
    """A run whose log status is not success is surfaced with errored=True."""
    source = sorted(BERG_STACK_3.glob("*.eval"))[0]
    log = read_eval_log(str(source))
    log.status = "error"
    broken = tmp_path / f"{source.stem}.eval"
    write_eval_log(log, str(broken))

    results = load_results(tmp_path)

    assert len(results) == 1
    assert results[0].errored
    assert results[0].error
