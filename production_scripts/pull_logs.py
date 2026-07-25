"""Pull Inspect eval logs off the Modal ``eval-logs`` volume and view them locally.

This removes the manual browser-download workflow: one command mirrors a run's
``.eval`` logs from the Modal Volume down to a local directory, and (optionally)
opens them in the Inspect viewer.

Design notes:
- **Reuse, don't reinvent.** It shells out to the off-the-shelf ``modal volume
  get`` (the idiomatic Volume-access command used across the Modal skills) and
  ``inspect view`` (the official log viewer, which also auto-refreshes). No custom
  sync daemon, FUSE mount, or bespoke viewer.
- **DRY.** The volume name, the remote path layout, and the local mirror location
  all come from the project config (``run_defaults.yaml`` ``logs:``) via
  ``llm_consciousness_self_attribution.config`` -- the same source the Modal
  launcher writes with -- so reader and writer cannot drift.

The local mirror is git-ignored; the Volume is the source of truth.

Examples (run under the project env so ``modal`` and ``inspect`` are on PATH)::

    # Mirror ALL runs, then print the viewer command:
    uv run python production_scripts/pull_logs.py

    # Mirror just the Berg 7B-instruct runs and open the Inspect viewer:
    uv run python production_scripts/pull_logs.py \\
        --method berg --stack olmo_7b_instruct_stack --view

    # Show the exact commands without running them:
    uv run python production_scripts/pull_logs.py --method berg --dry-run

Once mirrored, you can also point the plot scripts at the same local tree, e.g.
``--log-dir eval-logs/refactor_runs/berg/olmo_7b_instruct_stack``, or open the
folder in the Inspect VS Code extension's Logs pane.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path, PurePosixPath

from llm_consciousness_self_attribution import config

REPO_ROOT = Path(__file__).resolve().parents[1]


def selection_suffix(
    method: str | None, stack: str | None, stage: str | None
) -> str:
    """Join the chosen ``method/stack/stage`` levels into a path suffix.

    The levels are hierarchical, so a narrower selection requires the broader
    ones: you cannot pick a ``stage`` without a ``stack``, or a ``stack`` without
    a ``method``. Violations raise ``ValueError`` so the pulled path is never
    ambiguous. Returns ``""`` when nothing is selected (mirror everything).
    """
    levels = [("method", method), ("stack", stack), ("stage", stage)]
    parts: list[str] = []
    ended = False
    for name, value in levels:
        if value is None:
            ended = True
            continue
        if ended:
            raise ValueError(
                "--stage requires --stack, and --stack requires --method"
            )
        parts.append(value)
    return "/".join(parts)


def get_command(volume: str, remote_path: str, local_dest: Path, force: bool = True) -> list[str]:
    """The ``modal volume get`` command that mirrors ``remote_path`` -> ``local_dest``."""
    cmd = ["modal", "volume", "get", volume, remote_path, str(local_dest)]
    if force:
        cmd.append("--force")  # overwrite the local mirror on re-pull
    return cmd


def view_command(local_dest: Path) -> list[str]:
    """The ``inspect view`` command to browse the mirrored logs."""
    return ["inspect", "view", "--log-dir", str(local_dest)]


def _resolve_paths(method, stack, stage):
    """Return (volume, remote_path, local_dest) for the requested selection."""
    logs = config.logs_config()
    suffix = selection_suffix(method, stack, stage)
    remote_root = logs["remote_root"]
    local_root = REPO_ROOT / logs["local_dir"]
    if suffix:
        remote_path = f"{remote_root}/{suffix}"
        local_dest = local_root / suffix
    else:
        remote_path = remote_root
        local_dest = local_root
    return logs["volume"], remote_path, local_dest


def _run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        raise SystemExit(
            f"error: '{cmd[0]}' not found. Run this under the project env "
            f"(e.g. `uv run python production_scripts/pull_logs.py ...`) so that "
            f"modal and inspect are on PATH."
        )


def cli_destination(remote_path: str, local_dest: Path) -> Path:
    """The destination to hand ``modal volume get`` so the tree lands at ``local_dest``.

    ``modal volume get`` does NOT simply write the remote directory to the path
    you name. Measured against the real CLI (modal 1.4.x, 2026-07-25):

    * destination **exists as a directory** -> creates
      ``<destination>/<basename(remote_path)>/...`` -- the only well-defined case;
    * destination **absent**, remote holds exactly ONE file -> writes that file
      *as* the destination path (so ``.../sft`` becomes a binary file, not a
      directory -- the failure that produced an unopenable log);
    * destination **absent**, remote holds several entries -> fails outright with
      ``[Errno 21] Is a directory``.

    So always hand it the PARENT and let it append the basename. That is only
    correct while ``basename(remote_path) == local_dest.name``, which the shared
    ``selection_suffix`` guarantees -- and which this function asserts rather
    than assumes.
    """
    remote_name = PurePosixPath(remote_path).name
    if remote_name != local_dest.name:
        raise ValueError(
            f"remote basename {remote_name!r} != local destination name "
            f"{local_dest.name!r}; `modal volume get` would create "
            f"{local_dest.parent / remote_name} instead of {local_dest}"
        )
    return local_dest.parent


def eval_files(local_dest: Path) -> list[Path]:
    """Every ``.eval`` file under ``local_dest`` (recursively), sorted."""
    if not local_dest.is_dir():
        return []
    return sorted(local_dest.rglob("*.eval"))


def verify_mirror(local_dest: Path) -> list[Path]:
    """Check a completed pull actually produced openable logs; return them.

    ``modal volume get`` reports success even when the result is unusable. In
    particular, if the local destination does not already exist and the remote
    directory holds exactly ONE file, it writes that file *as* the destination
    path -- so ``.../sft`` ends up a 167KB binary file rather than a directory
    containing ``....eval``. The Inspect viewer then shows nothing and VS Code
    reports "binary or unsupported text encoding", while the terminal claims the
    mirror succeeded.

    This is the "validate inputs and outputs" rule earning its keep: the failure
    is silent at the CLI layer, so the tool has to check its own post-condition.
    """
    if local_dest.is_file():
        raise SystemExit(
            f"error: {local_dest} is a FILE, not a directory.\n"
            f"       `modal volume get` collapsed a single-file directory onto the\n"
            f"       destination path. Move it aside and re-run; the pull now hands\n"
            f"       the CLI the parent directory to prevent this."
        )
    doubled = local_dest / local_dest.name
    if doubled.is_dir() and eval_files(doubled):
        raise SystemExit(
            f"error: logs landed at {doubled}, one level too deep.\n"
            f"       `modal volume get` appended the remote basename to a destination\n"
            f"       that already ended with it. Move {doubled} aside and re-run."
        )
    found = eval_files(local_dest)
    if not found:
        raise SystemExit(
            f"error: no .eval logs under {local_dest} after the pull.\n"
            f"       Check the remote path exists: `modal volume ls eval-logs <path>`."
        )
    return found


def mirror(
    method: str | None = None,
    stack: str | None = None,
    stage: str | None = None,
    *,
    dry_run: bool = False,
) -> Path:
    """Mirror one selection's ``.eval`` logs off the Volume; return the local dir.

    The public "get these logs onto my disk" entry point, used both by this
    script's CLI and by ``run_and_pull.py`` (which calls it once per stage, as
    each stage finishes). Callers get the local destination back so they can open
    or plot it without re-deriving the path.

    The CLI is handed the *parent* directory, pre-created, because that is the
    only destination form ``modal volume get`` handles predictably (see
    ``cli_destination``). The result is then verified rather than assumed.

    Raises ``ValueError`` for an ambiguous selection (see ``selection_suffix``).
    """
    volume, remote_path, local_dest = _resolve_paths(method, stack, stage)
    dest = cli_destination(remote_path, local_dest)
    cmd = get_command(volume, remote_path, dest)
    if dry_run:
        print("# would run:")
        print("$", " ".join(cmd))
        # The command's destination is the PARENT; say where logs actually land,
        # so the printed command does not read like it targets the wrong place.
        print(f"# -> logs land in {local_dest}")
        return local_dest
    dest.mkdir(parents=True, exist_ok=True)
    _run(cmd)
    found = verify_mirror(local_dest)
    print(f"  {len(found)} .eval log(s) under {local_dest}")
    return local_dest


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--method", help="Narrow to one elicitation method (e.g. berg, petri).")
    parser.add_argument("--stack", help="Narrow to one model stack (requires --method).")
    parser.add_argument("--stage", help="Narrow to one stage: sft/dpo/instruct (requires --stack).")
    parser.add_argument("--view", action="store_true", help="Open the mirrored logs in `inspect view` after pulling.")
    parser.add_argument("--dry-run", action="store_true", help="Print the commands without running them.")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = _parse_args(argv)
    try:
        local_dest = mirror(args.method, args.stack, args.stage, dry_run=args.dry_run)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}")

    view_cmd = view_command(local_dest)

    if args.dry_run:
        print("$", " ".join(view_cmd), "  # (with --view)")
        return

    print(f"\nMirrored to {local_dest}")

    if args.view:
        _run(view_cmd)
    else:
        print(f"View it with:\n  uv run inspect view --log-dir {local_dest}")
        print("...or open that folder in the Inspect VS Code extension's Logs pane.")


if __name__ == "__main__":
    sys.exit(main())
