#!/usr/bin/env python3
"""Generate short sound effects through a user-managed local AudioGen install."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_ROOT = Path(os.environ.get("AUDIOGEN_ROOT", r"D:\Audiogen"))
DEFAULT_PYTHON = Path(
    os.environ.get(
        "AUDIOGEN_PYTHON",
        str(DEFAULT_ROOT / "venv310" / "Scripts" / "python.exe"),
    )
)
DEFAULT_MODEL = Path(
    os.environ.get(
        "AUDIOGEN_MODEL",
        str(DEFAULT_ROOT / "audiogen-medium"),
    )
)

PRESETS: dict[str, str] = {
    "ui_click": "Short clean click sound, UI button tap, crisp digital, 0.2 seconds",
    "ui_open": "Short whoosh panel opening sound, UI transition, light and airy, 0.5 seconds",
    "ui_confirm": "Positive chime, UI confirm button, pleasant two-note ding, 0.4 seconds",
    "ui_error": "Short negative buzzer, UI error sound, low digital thud, 0.3 seconds",
    "correct": "Cheerful correct-answer chime, children's game, bright ascending notes, 0.8 seconds",
    "wrong": "Wrong-answer buzzer, game feedback, low descending tones, 0.5 seconds",
    "reward": "Victory fanfare, short jingle, children's game, upbeat, 1.5 seconds",
    "progress": "Soft progress tick sound, level up indicator, subtle sparkle, 0.5 seconds",
    "hit": "Melee impact thud, sword hit on armor, game combat sound effect, 0.4 seconds",
    "attack": "Sword slash attack sound effect, whoosh and impact, game combat, 0.5 seconds",
    "spell": "Magic spell cast sound, electric buzz and crackle, fantasy game, 0.8 seconds",
    "heal": "Soft healing shimmer, health restore sound, gentle bell and whoosh, 0.7 seconds",
    "footstep": "Single footstep on stone floor, game movement sound, muffled thud, 0.3 seconds",
    "door": "Wooden door opening creak, dungeon game, slow groan, 0.8 seconds",
    "explosion": "Small explosion pop, game impact, distant rumble, 0.6 seconds",
    "ambient": "Soft fantasy dungeon ambient loop, wind and distant echoes, eerie, 3 seconds",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate short game SFX with a local AudioGen install.")
    parser.add_argument("prompt", nargs="?", default=None, help="Text description of the sound.")
    parser.add_argument("--preset", default=None, help="Use a built-in SFX preset.")
    parser.add_argument("--output", default=None, help="Output path without extension; saves .wav files.")
    parser.add_argument("--duration", type=float, default=2.0, help="Duration in seconds (default: 2.0, max: 10).")
    parser.add_argument("--model", default=str(DEFAULT_MODEL), help="Path to model weights.")
    parser.add_argument("--python", dest="python_path", default=str(DEFAULT_PYTHON), help="AudioGen venv Python path.")
    parser.add_argument("--n", type=int, default=1, help="Number of variants (default: 1).")
    parser.add_argument("--list-presets", action="store_true", help="List all presets and exit.")
    return parser.parse_args()


def choose_prompt(args: argparse.Namespace) -> str:
    prompt = args.prompt
    if args.preset:
        if args.preset not in PRESETS:
            raise SystemExit(f"Unknown preset '{args.preset}'. Use --list-presets to see options.")
        prompt = PRESETS[args.preset]
    if not prompt:
        raise SystemExit("Provide a prompt or --preset.")
    return prompt


def output_base(args: argparse.Namespace, prompt: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if args.output:
        return args.output
    if args.preset:
        return f"sfx_{args.preset}_{timestamp}"
    slug = prompt[:30].lower().replace(" ", "_").replace(",", "").replace(".", "")
    return f"sfx_{slug}_{timestamp}"


def main() -> int:
    args = parse_args()

    if args.list_presets:
        print("Available presets:")
        for name, prompt in PRESETS.items():
            print(f"  {name:15s}  {prompt[:70]}")
        return 0

    prompt = choose_prompt(args)
    duration = max(0.1, min(args.duration, 10.0))
    python_path = Path(args.python_path).expanduser().resolve()
    model_path = Path(args.model).expanduser().resolve()
    base_out = output_base(args, prompt)

    if not python_path.is_file():
        raise SystemExit(f"AudioGen Python not found: {python_path}")
    if not model_path.is_dir():
        raise SystemExit(f"AudioGen model directory not found: {model_path}")

    print(f"Prompt:   {prompt}")
    print(f"Duration: {duration}s  Variants: {args.n}")
    print(f"Python:   {python_path}")
    print(f"Model:    {model_path}")
    print(f"Output:   {base_out}.wav")
    print()

    prompts_json = json.dumps([prompt] * args.n)
    inline = f"""
from pathlib import Path
import sys
sys.path.insert(0, r"{model_path.parent.as_posix()}")
from audiocraft.models import AudioGen
from audiocraft.data.audio import audio_write

model = AudioGen.get_pretrained(r"{model_path.as_posix()}")
model.set_generation_params(duration={duration})
wavs = model.generate({prompts_json})
base = Path(r"{base_out}")
base.parent.mkdir(parents=True, exist_ok=True)

for i, wav in enumerate(wavs):
    suffix = f"_{{i}}" if len(wavs) > 1 else ""
    out = str(base) + suffix
    audio_write(out, wav.cpu(), model.sample_rate, strategy="loudness", loudness_compressor=True)
    print("SAVED:", out + ".wav")
"""

    result = subprocess.run([str(python_path), "-c", inline], capture_output=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
