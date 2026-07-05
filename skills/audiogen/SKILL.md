---
name: audiogen
description: Generate short sound effects (SFX) with a separately installed local AudioGen environment. Use when the user wants local game audio such as UI clicks, hits, spells, ambient loops, victory cues, footsteps, explosions, or other short effects. Use this skill for guidance, path verification, and generation through a user-managed AudioGen install; do not assume the repository contains the model or Python environment.
---

# AudioGen Sound Effect Generator

Use this skill when short audio clips should be generated locally with AudioGen.

This skill assumes AudioGen is installed outside the repository and that the skill only needs to point to it correctly.

## Local Paths

The skill resolves paths in this order:

1. `AUDIOGEN_PYTHON`
2. `AUDIOGEN_MODEL`
3. `AUDIOGEN_ROOT`
4. fallback defaults based on `D:\Audiogen`

Default fallback layout:

- root: `D:\Audiogen`
- python: `D:\Audiogen\venv310\Scripts\python.exe`
- model: `D:\Audiogen\audiogen-medium`

## Safe Verification

Check local path configuration:

```powershell
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\check_audiogen.py"
```

Check importability without generating audio:

```powershell
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\check_audiogen.py" --check-import
```

## Generation

Generate from the repository checkout:

```powershell
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\generate_sfx.py" --preset correct
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\generate_sfx.py" "short magic spell whoosh, fantasy game sound"
```

Installed runtime copies may also exist under:

```powershell
$env:USERPROFILE\.claude\skills\audiogen\
$env:USERPROFILE\.codex\skills\audiogen\
$env:USERPROFILE\.cursor\skills\audiogen\
```

## Good Use Cases

- UI clicks and confirms
- Correct/wrong answer sounds
- Magic or combat cues
- Short ambient loops
- Prompt iteration for small game SFX

## Poor Use Cases

- full songs
- long music tracks
- real-time generation
- shipping a complete AudioGen install inside git

## Practical Rules

- Prefer outputs under 4 seconds unless the user explicitly needs longer.
- Generate variants with `--n` when picking the best sound matters.
- Keep generated outputs outside this repository unless the user explicitly wants audio assets versioned here.
- Do not mutate the user's AudioGen install unless asked.

## Common Commands

```powershell
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\generate_sfx.py" --preset ui_click
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\generate_sfx.py" --preset reward
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\generate_sfx.py" "electric purple lightning bolt, magic cast whoosh, arcade game, clean" --duration 1.0
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\generate_sfx.py" "sword slash attack" --preset attack --n 3 --output "C:/temp/attack"
```

## Known Reference Setup

The current machine that informed this repository has:

- `Python 3.10.11`
- `audiocraft==1.3.0`
- `torch==2.1.0+cu121`
- `torchaudio==2.1.0+cu121`
- `xformers==0.0.22.post7`

Treat that as a known-good reference, not a universal requirement set.
