# For Claude or any coding assistant working in this repo

## Design rules

Follow `GeneralSoftwareDesignRules.md`. It is the standard this repo is held to —
DRY, KISS/YAGNI, keep changes small, keep refactor commits separate from feature
commits, validate outputs, prefer off-the-shelf tooling.

## Before touching the Modal/vLLM path

Read `ENGINEERING_NOTES.md` first. It records failure modes that already cost
debugging time (Olmo 3 loader crashes, flashinfer needing `nvcc`, compile-cache
collisions across stages, `modal volume get` silently collapsing directories).

## Skills

Use the Modal skills for all GPU work:

- `modal-basic-skills` — platform basics, CLI, app structure
- `modal-gpu-dev` — interactive GPU sandbox with SSH, for live debugging
- `modal-gpu-experiment` — training/experiment apps, volumes, secrets
- `sub-agents` — parallel agent orchestration across GPUs

## Documentation

- Inspect: https://inspect.aisi.org.uk/
- PETRI: https://meridianlabs-ai.github.io/inspect_petri/
- Modal: https://modal.com/docs — volumes at https://modal.com/docs/guide/volumes

## Where things are written down

`README.md` is the single home for project status, current results, run commands,
and the further-work list. `CHANGELOG.md` records what changed and why — add an
entry there rather than writing a new status document. `REPLICATION.md` is the academic record of a published
run. `ENGINEERING_NOTES.md` holds the gotchas. Branch and commit state live in git
— do not restate them in markdown.
