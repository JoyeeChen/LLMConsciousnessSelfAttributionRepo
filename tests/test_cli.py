"""CLI tests: run planning (no execution) and offline plotting from fixtures."""

from __future__ import annotations

from pathlib import Path

from llm_consciousness_self_attribution import cli


def test_run_dry_run_plans_all_stages(capsys) -> None:
    exit_code = cli.main(
        ["run", "--method", "berg", "--stack", "olmo_7b_instruct_stack", "--dry-run"]
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Planned 4 run(s)" in out  # base, sft, dpo, instruct
    assert "Dry run" in out


def test_run_base_stage_routes_local_even_with_remote() -> None:
    plan = cli.plan_runs("berg", "olmo_7b_instruct_stack", stage=None, prefer_remote=True)
    by_stage = {p.stage.stage: p.runner for p in plan}
    # Base model lacks a chat template -> forced local; instruct honors --remote.
    assert by_stage["base"] == "local"
    assert by_stage["instruct"] == "remote"


def test_plot_heatmap_from_fixtures(tmp_path: Path) -> None:
    out = tmp_path / "heatmap.png"
    exit_code = cli.main(["plot", "heatmap", "--out", str(out)])
    assert exit_code == 0
    assert out.exists() and out.stat().st_size > 0


def test_plot_dashboard_from_fixtures(tmp_path: Path) -> None:
    out = tmp_path / "dashboard.png"
    exit_code = cli.main(["plot", "dashboard", "--out", str(out)])
    assert exit_code == 0
    assert out.exists() and out.stat().st_size > 0
