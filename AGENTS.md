# AudioGenSkill — Agent Instructions

This repository is the source of truth for a local `audiogen` skill that depends on a user-managed AudioGen installation outside the repo.

## Boundaries

- Canonical skill logic lives in `skills/audiogen/`.
- Cursor discovery files in `.cursor/` must stay thin wrappers only.
- Do not vendor the AudioGen model, PyTorch wheels, FFmpeg, or a Python venv into this repository.
- Keep path handling configurable through environment variables instead of hard-coding one machine path into all logic.

## Local Reference

Known-good current machine reference:

- `D:\Audiogen`
- `D:\Audiogen\venv310\Scripts\python.exe`
- `D:\Audiogen\audiogen-medium`

Treat those as defaults and examples, not global truth.

## Editing Rules

- Update `skills/audiogen/SKILL.md` first when behavior changes.
- Update `skills/audiogen/scripts/*` when generation or verification logic changes.
- Update `.cursor/*` only when Cursor discovery/routing needs to change.
- Update `README.md` when local-install guidance or runtime-install commands change.

## Safety

- Avoid changes that mutate or reinstall the user's existing `D:\Audiogen` environment unless they explicitly ask.
- Prefer path checks and import checks over generation-heavy smoke tests by default.
- Generated audio belongs outside the repo.
