#!/usr/bin/env python3
"""Validate a local AudioGen path setup without changing it."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
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
EXPECTED_MODEL_FILES = [
    "state_dict.bin",
    "compression_state_dict.bin",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a local AudioGen setup.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="AudioGen root path.")
    parser.add_argument("--python", dest="python_path", default=str(DEFAULT_PYTHON), help="AudioGen venv Python path.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL), help="AudioGen model directory.")
    parser.add_argument("--check-import", action="store_true", help="Run a lightweight audiocraft import check.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    python_path = Path(args.python_path).expanduser().resolve()
    model_path = Path(args.model).expanduser().resolve()

    result: dict[str, object] = {
        "root": str(root),
        "python": str(python_path),
        "model": str(model_path),
        "checks": {},
    }

    checks: dict[str, object] = {}
    checks["root_exists"] = root.exists()
    checks["python_exists"] = python_path.is_file()
    checks["model_exists"] = model_path.is_dir()
    checks["model_files"] = {
        name: (model_path / name).is_file()
        for name in EXPECTED_MODEL_FILES
    }

    if python_path.is_file():
        version = subprocess.run(
            [str(python_path), "--version"],
            capture_output=True,
            text=True,
        )
        checks["python_version"] = (version.stdout or version.stderr).strip()

    if args.check_import and python_path.is_file():
        probe = subprocess.run(
            [
                str(python_path),
                "-c",
                "from audiocraft.models import AudioGen; print('AudioGen import OK')",
            ],
            capture_output=True,
            text=True,
        )
        checks["import_check"] = {
            "ok": probe.returncode == 0,
            "stdout": probe.stdout.strip(),
            "stderr": probe.stderr.strip(),
        }

    result["checks"] = checks
    print(json.dumps(result, indent=2, ensure_ascii=False))

    failed = not (
        checks["root_exists"]
        and checks["python_exists"]
        and checks["model_exists"]
        and all(checks["model_files"].values())
    )
    if args.check_import and isinstance(checks.get("import_check"), dict):
        failed = failed or not bool(checks["import_check"]["ok"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
