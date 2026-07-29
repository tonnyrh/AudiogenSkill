#!/usr/bin/env python3
"""Local browser GUI for prompting, generating, auditioning, and refining SFX."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import uuid
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
GUI_DIR = SKILL_DIR / "gui"
GENERATOR = SCRIPT_DIR / "generate_sfx.py"
CHECKER = SCRIPT_DIR / "check_audiogen.py"
DEFAULT_DATA_DIR = Path(
    os.environ.get(
        "AUDIOGEN_GUI_DATA",
        str(Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AudioGenSkill"),
    )
).expanduser()
PRESETS = {
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Studio:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir.resolve()
        self.audio_dir = self.data_dir / "audio"
        self.history_path = self.data_dir / "history.json"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.generation_lock = threading.Lock()
        self.items: list[dict[str, object]] = self._load()

    def _load(self) -> list[dict[str, object]]:
        if not self.history_path.is_file():
            return []
        try:
            value = json.loads(self.history_path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def save(self) -> None:
        temp = self.history_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.items, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.history_path)

    def list_items(self) -> list[dict[str, object]]:
        with self.lock:
            return list(reversed(self.items))

    def find(self, item_id: str) -> dict[str, object] | None:
        return next((item for item in self.items if item["id"] == item_id), None)

    def create(self, payload: dict[str, object]) -> dict[str, object]:
        prompt = str(payload.get("prompt", "")).strip()
        if not prompt or len(prompt) > 1000:
            raise ValueError("Prompten må være mellom 1 og 1000 tegn.")
        duration = max(0.1, min(float(payload.get("duration", 2)), 10.0))
        variants = max(1, min(int(payload.get("variants", 1)), 4))
        item_id = uuid.uuid4().hex
        item = {
            "id": item_id,
            "prompt": prompt,
            "duration": duration,
            "variants": variants,
            "created_at": utc_now(),
            "status": "queued",
            "favorite": False,
            "files": [],
            "log": "Venter på generering…",
            "parent_id": str(payload.get("parent_id", "")) or None,
        }
        with self.lock:
            self.items.append(item)
            self.save()
        threading.Thread(target=self._generate, args=(item_id,), daemon=True).start()
        return item

    def _generate(self, item_id: str) -> None:
        with self.lock:
            item = self.find(item_id)
            if not item:
                return
            prompt = str(item["prompt"])
            duration = float(item["duration"])
            variants = int(item["variants"])
        job_dir = self.audio_dir / item_id
        base = job_dir / "sound"
        job_dir.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            str(GENERATOR),
            prompt,
            "--duration",
            str(duration),
            "--n",
            str(variants),
            "--output",
            str(base),
        ]
        try:
            with self.generation_lock:
                with self.lock:
                    current = self.find(item_id)
                    if not current:
                        return
                    current["status"] = "running"
                    current["log"] = "AudioGen laster modell og lager lyd…"
                    self.save()
                result = subprocess.run(command, capture_output=True, text=True)
            wavs = sorted(job_dir.glob("*.wav"))
            log = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
            with self.lock:
                current = self.find(item_id)
                if not current:
                    return
                current["files"] = [path.name for path in wavs]
                current["status"] = "done" if result.returncode == 0 and wavs else "error"
                current["log"] = log[-8000:] or (
                    "Genereringen er ferdig." if current["status"] == "done" else "Ingen WAV-fil ble opprettet."
                )
                current["finished_at"] = utc_now()
                self.save()
        except Exception as exc:  # keep job failures visible in the GUI
            with self.lock:
                current = self.find(item_id)
                if current:
                    current["status"] = "error"
                    current["log"] = f"{type(exc).__name__}: {exc}"
                    current["finished_at"] = utc_now()
                    self.save()

    def update(self, item_id: str, payload: dict[str, object]) -> dict[str, object]:
        with self.lock:
            item = self.find(item_id)
            if not item:
                raise KeyError(item_id)
            if "favorite" in payload:
                item["favorite"] = bool(payload["favorite"])
            self.save()
            return item

    def delete(self, item_id: str) -> None:
        with self.lock:
            item = self.find(item_id)
            if not item:
                raise KeyError(item_id)
            if item["status"] in {"queued", "running"}:
                raise ValueError("En aktiv generering kan ikke slettes.")
            job_dir = (self.audio_dir / item_id).resolve()
            if job_dir.parent == self.audio_dir and job_dir.is_dir():
                for path in job_dir.iterdir():
                    if path.is_file():
                        path.unlink()
                job_dir.rmdir()
            self.items.remove(item)
            self.save()

    def audio_path(self, item_id: str, filename: str) -> Path | None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", filename):
            return None
        path = (self.audio_dir / item_id / filename).resolve()
        expected_parent = (self.audio_dir / item_id).resolve()
        return path if path.parent == expected_parent and path.is_file() else None


class Handler(BaseHTTPRequestHandler):
    studio: Studio

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[GUI] {self.address_string()} {fmt % args}")

    def send_json(self, value: object, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 32_768:
            raise ValueError("Forespørselen er for stor.")
        value = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(value, dict):
            raise ValueError("Ugyldig JSON.")
        return value

    def serve_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/history":
            self.send_json({"items": self.studio.list_items(), "presets": PRESETS})
            return
        if path == "/api/health":
            result = subprocess.run([sys.executable, str(CHECKER)], capture_output=True, text=True)
            try:
                value = json.loads(result.stdout)
            except json.JSONDecodeError:
                value = {"checks": {}, "error": result.stderr or result.stdout}
            value["ok"] = result.returncode == 0
            self.send_json(value)
            return
        if path.startswith("/api/audio/"):
            parts = [unquote(part) for part in path.split("/") if part]
            if len(parts) == 4:
                audio = self.studio.audio_path(parts[2], parts[3])
                if audio:
                    self.serve_file(audio)
                    return
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        asset = "index.html" if path == "/" else path.lstrip("/")
        target = (GUI_DIR / asset).resolve()
        if target == GUI_DIR or GUI_DIR not in target.parents:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.serve_file(target)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/generate":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            self.send_json(self.studio.create(self.read_json()), HTTPStatus.CREATED)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_PATCH(self) -> None:
        match = re.fullmatch(r"/api/history/([a-f0-9]{32})", urlparse(self.path).path)
        if not match:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            self.send_json(self.studio.update(match.group(1), self.read_json()))
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def do_DELETE(self) -> None:
        match = re.fullmatch(r"/api/history/([a-f0-9]{32})", urlparse(self.path).path)
        if not match:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            self.studio.delete(match.group(1))
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
        except KeyError:
            self.send_error(HTTPStatus.NOT_FOUND)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.CONFLICT)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the local AudioGen Sound Studio.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    studio = Studio(args.data_dir)
    handler = type("StudioHandler", (Handler,), {"studio": studio})
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{server.server_port}"
    print(f"AudioGen Sound Studio: {url}")
    print(f"Data: {studio.data_dir}")
    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopper Sound Studio.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
