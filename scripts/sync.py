#!/usr/bin/env python3
"""Sync the audiogen skill into a local Claude/Codex/Cursor runtime."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


SKILLS: dict[str, list[str]] = {
    "claude": ["audiogen"],
    "codex": ["audiogen"],
    "cursor": ["audiogen"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync AudioGenSkill into a local runtime.")
    parser.add_argument("--tool", choices=["claude", "codex", "cursor"], required=True, help="Target runtime.")
    return parser.parse_args()


def runtime_root(tool: str) -> Path:
    home = Path.home()
    if tool == "cursor":
        return home / ".cursor"
    return home / f".{tool}"


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    skills_dst = runtime_root(args.tool) / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)

    for skill in SKILLS[args.tool]:
        src = repo_root / "skills" / skill
        if not src.is_dir():
            print(f"ERROR: missing source skill: {src}", file=sys.stderr)
            return 1
        dst = skills_dst / skill
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"Synced {skill} -> {dst}")

    print(f"{args.tool.capitalize()} AudioGen skill is in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
