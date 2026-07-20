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

If import validation stalls on this machine, lower the timeout and inspect the temp logs:

```powershell
python "C:\vscode\AudioGenSkill\skills\audiogen\scripts\check_audiogen.py" --check-import --import-timeout 10
```

## Generation

When the user asks to create or add a sound effect, generation is part of the task. Do not stop at prompt advice, path verification, a placeholder, or playback scaffolding unless the user explicitly asks for guidance only or generation is genuinely blocked.

Use this default execution flow:

1. Verify the configured AudioGen paths, preferably with the lightweight path check.
2. Generate one or more short WAV candidates with `generate_sfx.py`.
3. Inspect or audition the candidates when the available tools allow it; otherwise report the exact generated paths.
4. Convert the selected WAV to the target platform's required asset format.
5. Place and wire the converted asset into the user's project when the request includes adding the sound to a game or application.
6. Verify both the generated source and the integrated target asset.

Target constraints are implementation requirements, not reasons to skip generation. For example, an Amiga/Paula target may require mono, signed 8-bit PCM, an appropriate sample rate, even-length data, chip-RAM placement, and DMA-safe playback. Generate the source WAV first, then convert it and integrate the converted sample using the target project's existing asset pipeline or tools.

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
- The instruction to create or add a sound to a project is explicit permission to place the final runtime asset in that project's normal asset location and update its code/build files. It does not require a second confirmation.
- Keep disposable candidates and intermediate WAV files outside the project when practical. Keep the selected source WAV in the project only when its asset policy or conversion pipeline needs it.
- “Generated outputs belong outside the AudioGenSkill repository” protects this skill repository from test artifacts; it does not prohibit adding requested audio assets to the user's separate game or application repository.
- Do not substitute a synthetic placeholder, hand-authored sample, or silent playback test for the requested AudioGen output without clearly stating the blocker.
- When generation or conversion is blocked, preserve any successful intermediate files, give the exact failing command and error, and continue with any integration work that can be completed honestly.
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
