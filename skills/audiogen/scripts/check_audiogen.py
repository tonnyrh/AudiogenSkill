#!/usr/bin/env python3
"""Validate a local AudioGen path setup without changing it."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
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
IMPORT_STDOUT_LOG = Path(tempfile.gettempdir()) / "audiogen-import-stdout.log"
IMPORT_STDERR_LOG = Path(tempfile.gettempdir()) / "audiogen-import-stderr.log"


def tail_text(text: str, limit: int = 80) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-limit:])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a local AudioGen setup.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="AudioGen root path.")
    parser.add_argument("--python", dest="python_path", default=str(DEFAULT_PYTHON), help="AudioGen venv Python path.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL), help="AudioGen model directory.")
    parser.add_argument("--check-import", action="store_true", help="Run a lightweight audiocraft import check.")
    parser.add_argument(
        "--import-timeout",
        type=int,
        default=30,
        help="Timeout in seconds for the optional import check (default: 30).",
    )
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
        probe_cmd = [
            str(python_path),
            "-X",
            "importtime",
            "-c",
            "from audiocraft.models import AudioGen; print('AudioGen import OK')",
        ]
        try:
            probe = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                timeout=args.import_timeout,
            )
            IMPORT_STDOUT_LOG.write_text(probe.stdout or "", encoding="utf-8")
            IMPORT_STDERR_LOG.write_text(probe.stderr or "", encoding="utf-8")
            checks["import_check"] = {
                "ok": probe.returncode == 0,
                "timed_out": False,
                "timeout_seconds": args.import_timeout,
                "stdout_tail": tail_text(probe.stdout.strip()),
                "stderr_tail": tail_text(probe.stderr.strip()),
                "stdout_log": str(IMPORT_STDOUT_LOG),
                "stderr_log": str(IMPORT_STDERR_LOG),
                "returncode": probe.returncode,
                "command": probe_cmd,
            }
        except subprocess.TimeoutExpired as exc:
            IMPORT_STDOUT_LOG.write_text(exc.stdout or "", encoding="utf-8")
            IMPORT_STDERR_LOG.write_text(exc.stderr or "", encoding="utf-8")
            checks["import_check"] = {
                "ok": False,
                "timed_out": True,
                "timeout_seconds": args.import_timeout,
                "stdout_tail": tail_text((exc.stdout or "").strip()),
                "stderr_tail": tail_text((exc.stderr or "").strip()),
                "stdout_log": str(IMPORT_STDOUT_LOG),
                "stderr_log": str(IMPORT_STDERR_LOG),
                "returncode": None,
                "command": probe_cmd,
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
