# AudioGenSkill

Local skill project for using a separately installed AudioGen setup from Claude, Codex, and Cursor.

This repository is the source of truth for:

- a canonical `audiogen` skill
- lightweight install/sync scripts for local tool runtimes
- practical Windows notes for getting a local AudioGen install working

This repository does **not** vendor:

- the AudioGen model
- a Python virtual environment
- PyTorch wheels
- FFmpeg

Those stay outside git and are owned by the user machine.

## Scope

This project is meant to solve one narrow problem well:

1. A user installs AudioGen locally in their own path.
2. The `audiogen` skill points to that install through configurable paths.
3. Claude, Codex, or Cursor can call the skill without hard-coding the whole install into the repository.

## Current Known-Good Local Reference

This machine currently has a working local reference install at:

- AudioGen root: `D:\Audiogen`
- venv Python: `D:\Audiogen\venv310\Scripts\python.exe`
- model path: `D:\Audiogen\audiogen-medium`
- Python version: `3.10.11`

This repo should treat that as a reference example, not a mandatory path.

## Repository Layout

```text
AudioGenSkill/
  README.md
  AGENTS.md
  .cursor/
    rules/
      agent-routing.mdc
    skills/
      audiogen/
        SKILL.md
  skills/
    audiogen/
      SKILL.md
      agents/
        openai.yaml
      scripts/
        check_audiogen.py
        generate_sfx.py
  scripts/
    sync.py
    install_claude_skill.ps1
    install_codex_skill.ps1
    install_cursor_skill.ps1
```

## Path Configuration

The skill uses these environment variables when present:

- `AUDIOGEN_ROOT`
- `AUDIOGEN_PYTHON`
- `AUDIOGEN_MODEL`

If they are not set, the current defaults are:

- `D:\Audiogen`
- `D:\Audiogen\venv310\Scripts\python.exe`
- `D:\Audiogen\audiogen-medium`

Recommended user-level setup in PowerShell:

```powershell
[System.Environment]::SetEnvironmentVariable("AUDIOGEN_ROOT", "D:\Audiogen", "User")
[System.Environment]::SetEnvironmentVariable("AUDIOGEN_PYTHON", "D:\Audiogen\venv310\Scripts\python.exe", "User")
[System.Environment]::SetEnvironmentVariable("AUDIOGEN_MODEL", "D:\Audiogen\audiogen-medium", "User")
```

For the current shell only:

```powershell
$env:AUDIOGEN_ROOT = "D:\Audiogen"
$env:AUDIOGEN_PYTHON = "D:\Audiogen\venv310\Scripts\python.exe"
$env:AUDIOGEN_MODEL = "D:\Audiogen\audiogen-medium"
```

## Verify Local AudioGen

This repo includes a safe check that does not generate audio unless you explicitly extend it yourself.
It verifies:

- configured paths exist
- the chosen Python exists
- the model directory exists
- expected model files exist
- optional import check against `audiocraft`

Run:

```powershell
cd C:\vscode\AudioGenSkill
python .\skills\audiogen\scripts\check_audiogen.py
python .\skills\audiogen\scripts\check_audiogen.py --check-import
```

## Install The Skill Into Tool Runtimes

Claude:

```powershell
cd C:\vscode\AudioGenSkill
python .\scripts\sync.py --tool claude
```

Codex:

```powershell
cd C:\vscode\AudioGenSkill
python .\scripts\sync.py --tool codex
```

Cursor:

```powershell
cd C:\vscode\AudioGenSkill
python .\scripts\sync.py --tool cursor
```

PowerShell wrappers are also provided:

```powershell
.\scripts\install_claude_skill.ps1
.\scripts\install_codex_skill.ps1
.\scripts\install_cursor_skill.ps1
```

## Use The Skill

Canonical repo script:

```powershell
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\generate_sfx.py" --preset correct
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\generate_sfx.py" "short magic spell whoosh, fantasy game sound"
```

Installed runtime copy:

```powershell
python "$env:USERPROFILE\.claude\skills\audiogen\scripts\generate_sfx.py" --preset correct
python "$env:USERPROFILE\.codex\skills\audiogen\scripts\generate_sfx.py" --preset correct
python "$env:USERPROFILE\.cursor\skills\audiogen\scripts\generate_sfx.py" --preset correct
```

## Windows Notes

This was apparently a delicate Windows setup. The repository should preserve the lessons without pretending to be a universal installer.

Known practical points from the current working machine:

- Python `3.10` matters.
- A dedicated `venv310` was used instead of the generic `venv`.
- `Activate.ps1` may require:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

- CUDA/PyTorch wheel compatibility matters.
- `av` and `xformers` are the kind of packages that can derail the setup if versions drift.
- The working environment currently contains `audiocraft==1.3.0` and `xformers==0.0.22.post7`.

## One Known-Good Install Sequence

This is included as a reference for documentation and troubleshooting, not as a promise that every Windows machine will behave the same way:

```powershell
cd D:\Audiogen
py -3.10 -m venv venv310
.\venv310\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel

pip install torch==2.1.0 torchaudio==2.1.0 torchvision==0.16.0 torchtext==0.16.0 --index-url https://download.pytorch.org/whl/cu121
pip install av==12.3.0 --only-binary=:all:

pip install audiocraft==1.3.0 --no-deps
pip install encodec demucs gradio huggingface_hub librosa protobuf torchmetrics transformers soundfile datasets
pip install einops flashy hydra-core hydra_colorlog julius num2words sentencepiece spacy==3.7.6
pip install xformers==0.0.22.post7 --no-deps
```

You still need to place or clone the model at the path you intend to use, for example:

- `D:\Audiogen\audiogen-medium`

Expected large model files in that directory include:

- `state_dict.bin`
- `compression_state_dict.bin`

## What To Keep Out Of Git

Do not commit:

- the model directory
- any venv
- generated `.wav` outputs
- machine-specific caches

## Next Step

The next safe step after cloning this repo on another machine is:

1. install AudioGen locally
2. set the three path env vars
3. run `check_audiogen.py`
4. sync the `audiogen` skill into the target runtime
