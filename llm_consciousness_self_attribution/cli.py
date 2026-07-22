"""Single entry point for running elicitations and plotting results.

Examples:
    uv run cli run --method berg --stack olmo_7b_instruct_stack --dry-run
    uv run cli run --method petri --stack olmo_7b_instruct_stack --stage instruct
    uv run cli plot heatmap
    uv run cli plot dashboard --out olmo7b_elicitation_grouped_bar.png

`run` wraps the runners layer; `plot` wraps results + viz. Base-model stages
(chat_template_supported: false) are routed to the local runner automatically,
replacing the old "comment out the base-model line" workaround. `plot` defaults
to the committed May-25 fixture logs so the README figures reproduce offline.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from . import config
from .config import ModelStage
from .elicitation_methods import get_method, method_names

REPO_ROOT = Path(__file__).resolve().parents[1]
_MAY_25 = REPO_ROOT / "eval-logs" / "may_25_logs"
DEFAULT_BERG_LOGS = _MAY_25 / "berg_tests" / "olmo_7b_instruct_stack_3"
DEFAULT_PETRI_LOGS = _MAY_25 / "petri_tests" / "olmo_7b_instruct_stack"

STAGE_ORDER = ["base", "sft", "dpo", "instruct", "think"]
STAGE_LABELS = {"sft": "SFT", "dpo": "DPO", "instruct": "Final Instruct", "base": "Base", "think": "Think"}


@dataclass(frozen=True)
class PlannedRun:
    """One (stage, method) execution and where it should run."""

    stage: ModelStage
    method_name: str
    runner: str  # "local" or "remote"

    def describe(self) -> str:
        return f"{self.method_name} @ {self.stage.stage} ({self.stage.model}) -> {self.runner}"


def plan_runs(
    method_name: str,
    stack: str,
    stage: str | None,
    prefer_remote: bool,
) -> list[PlannedRun]:
    """Resolve which stages to run and where, honoring chat_template_supported."""
    stages = config.get_stack(stack)
    if stage is not None:
        stages = [s for s in stages if s.stage == stage]
        if not stages:
            raise SystemExit(f"Stage {stage!r} not found in stack {stack!r}")

    planned = []
    for model_stage in stages:
        # Base models lack a chat template and must go through the local path.
        runner = "remote" if (prefer_remote and model_stage.chat_template_supported) else "local"
        planned.append(PlannedRun(model_stage, method_name, runner))
    return planned


def _execute(plan: PlannedRun, seed: int | None, log_dir: str) -> None:
    from .runners.run_config import RunConfig

    method = get_method(plan.method_name)
    overrides = {"seed": seed} if seed is not None else {}
    run_config = RunConfig.from_defaults(plan.stage, method, log_dir=log_dir, **overrides)

    if plan.runner == "remote":
        from .runners.modal_app import run_eval_remote

        run_eval_remote(run_config)
    else:
        from .runners.local_app import run_local

        run_local(run_config)


def _cmd_run(args: argparse.Namespace) -> int:
    plan = plan_runs(args.method, args.stack, args.stage, prefer_remote=args.remote)
    print(f"Planned {len(plan)} run(s):")
    for planned in plan:
        print(f"  - {planned.describe()}")

    if args.dry_run:
        print("Dry run: not executing (remove --dry-run to run).")
        return 0

    for planned in plan:
        print(f"Running: {planned.describe()}")
        _execute(planned, args.seed, args.log_dir)
    return 0


def _cmd_plot(args: argparse.Namespace) -> int:
    from .results import load_results
    from .results.aggregate import aggregate
    from .viz import attribution_heatmap, elicitation_bar

    log_dirs = args.logs or [DEFAULT_BERG_LOGS, DEFAULT_PETRI_LOGS]
    rows = []
    for log_dir in log_dirs:
        rows.extend(load_results(log_dir))
    df = aggregate(rows)

    errored = df[df["errored"]]
    if not errored.empty:
        print(f"Warning: {len(errored)} errored/missing run(s) excluded from the plot.")

    present_stages = [s for s in STAGE_ORDER if s in set(df["model_stage"])]

    if args.chart == "heatmap":
        out = args.out or (REPO_ROOT / "olmo7b_elicitation_heatmap.png")
        attribution_heatmap(df, index_order=present_stages, output_path=out)
    else:
        out = args.out or (REPO_ROOT / "olmo7b_elicitation_grouped_bar.png")
        methods = sorted(set(df["method"]))
        elicitation_bar(
            df,
            stage_order=present_stages,
            method_order=methods,
            stage_labels=STAGE_LABELS,
            subtitle="Reproduced from committed May-25 fixture logs.",
            output_path=out,
        )
    print(f"Wrote {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cli", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run an elicitation method over a model stack.")
    run.add_argument("--method", required=True, choices=method_names())
    run.add_argument("--stack", default="olmo_7b_instruct_stack", choices=config.stack_names())
    run.add_argument("--stage", default=None, help="Run only this stage label (e.g. instruct).")
    run.add_argument("--seed", type=int, default=None)
    run.add_argument("--log-dir", default="logs")
    run.add_argument("--remote", action="store_true", help="Use the Modal remote runner where supported.")
    run.add_argument("--dry-run", action="store_true", help="Print the plan without executing.")
    run.set_defaults(func=_cmd_run)

    plot = subparsers.add_parser("plot", help="Plot results from Inspect logs.")
    plot.add_argument("chart", choices=["dashboard", "heatmap"])
    plot.add_argument("--logs", nargs="*", type=Path, help="Log dirs (default: May-25 fixtures).")
    plot.add_argument("--out", type=Path, default=None)
    plot.set_defaults(func=_cmd_plot)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
