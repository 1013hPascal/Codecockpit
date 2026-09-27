"""KI-Adapter für Ollama auf diesem Rechner (Konzept 11.1). Vorbild: Chatbot und Tagebuch.

- Läuft Ollama schon, wird es mitbenutzt. Sonst startet das Cockpit es bei Bedarf selbst.
- Beim Beenden stoppt das Cockpit nur ein Ollama, das es selbst gestartet hat.
- Ollama braucht kein Konto. Es wird in der KI-Verwaltung als lokales Werkzeug eingerichtet.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Sequence

import httpx

from cockpit.adapters.base import TestResult
from cockpit.ai.base import AIError, AIProvider
from cockpit.ai.streaming import stream_lines
from cockpit.core import paths
from cockpit.core.errors import CockpitError
from cockpit.core.http import make_client

log = logging.getLogger(__name__)

DEFAULT_HOST = "http://127.0.0.1:11434"
NOT_RUNNING = "Ollama ist nicht erreichbar."
NOT_INSTALLED = "Ollama ist nicht installiert."
GUIDE = "anleitungen/ollama-installieren.md"
ANSWER_TIMEOUT = 600                 # Sekunden: das erste Laden eines Modells dauert


def find_exe() -> Path | None:
    found = shutil.which("ollama")
    if found:
        return Path(found)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidate = Path(local) / "Programs" / "Ollama" / "ollama.exe"
        if candidate.is_file():
            return candidate
    return None


class OllamaServer:
    """Startet "ollama serve" bei Bedarf und beendet nur einen selbst gestarteten Server."""

    def __init__(self, host: str = DEFAULT_HOST) -> None:
        self.host = host
        self.process: subprocess.Popen | None = None
        self.lock = threading.Lock()

    @property
    def owned(self) -> bool:
        return self.process is not None

    def is_running(self) -> bool:
        try:
            return httpx.get(f"{self.host}/api/version", timeout=2).status_code == 200
        except httpx.HTTPError:
            return False

    def start(self, timeout: float = 60) -> None:
        """Wirft AIError, wenn Ollama fehlt oder nicht rechtzeitig antwortet."""
        with self.lock:
            if self.is_running():
                return
            exe = find_exe()
            if exe is None:
                raise AIError(NOT_INSTALLED)
            log_path = paths.logs_dir() / "ollama.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "w", encoding="utf-8") as log_file:
                self.process = subprocess.Popen(
                    [str(exe), "serve"], stdout=log_file, stderr=log_file,
                    stdin=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            log.info("Ollama gestartet")
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    self.process = None
                    raise AIError("Ollama wurde gleich wieder beendet.", f"Siehe {log_path}")
                if self.is_running():
                    return
                time.sleep(0.3)
            raise AIError("Ollama antwortet nach dem Start nicht.", f"{timeout} Sekunden")

    def stop(self) -> None:
        """Nur einen selbst gestarteten Server beenden, mit allem, was er gestartet hat."""
        with self.lock:
            process, self.process = self.process, None
        if process is None or process.poll() is not None:
            return
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError:
            process.kill()
        log.info("Selbst gestartetes Ollama beendet")


_server = OllamaServer()


def server() -> OllamaServer:
    return _server


def state() -> str:
    """Kurzer Zustand für die KI-Verwaltung. Blockiert kurz, also im Hintergrund aufrufen."""
    if _server.is_running():
        return "Ollama läuft."
    if find_exe() is None:
        return NOT_INSTALLED
    return "Ollama ist installiert und startet bei Bedarf."


class OllamaProvider(AIProvider):
    kind = "ollama"
    display_name = "Ollama"
    is_local = True

    def __init__(self, host: str = DEFAULT_HOST,
                 transport: httpx.BaseTransport | None = None) -> None:
        self.host = host
        self.manage_server = transport is None and host == DEFAULT_HOST
        self.no_think: set[str] = set()              # Modelle ohne Schalter für das Nachdenken
        self.client = make_client(host, transport=transport)
        self.client.timeout = httpx.Timeout(ANSWER_TIMEOUT, connect=5)

    def start(self) -> None:
        if self.manage_server:
            _server.start()

    def test_connection(self) -> TestResult:
        try:
            self.start()
            models = self.models()
        except CockpitError as exc:
            return TestResult(False, exc.message, exc.details)
        if not models:
            return TestResult(True, "Ollama läuft, aber es ist noch kein Modell installiert.")
        return TestResult(True, f"Ollama läuft. Installierte Modelle: {len(models)}.")

    def models(self) -> list[str]:
        try:
            response = self.client.get("/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AIError(NOT_RUNNING, repr(exc)) from None
        return sorted(m["name"] for m in data.get("models", []) if m.get("name"))

    def complete(self, messages: Sequence[dict], *, model: str, system: str = "",
                 schema: dict | None = None, max_tokens: int | None = None,
                 cancel: threading.Event | None = None) -> str | dict[str, Any]:
        chat = ([{"role": "system", "content": system}] if system else []) + list(messages)
        # Ohne Nachdenken: Modelle wie gemma4 verbrauchen sonst die ganze Länge der Antwort mit
        # Überlegungen, und die eigentliche Antwort bleibt leer (Test mit gemma4:12b in 8b).
        payload: dict[str, Any] = {"model": model, "messages": chat, "stream": True}
        if model not in self.no_think:
            payload["think"] = False
        if max_tokens:
            payload["options"] = {"num_predict": max_tokens}
        if schema is not None:
            payload["format"] = schema
        try:
            return self._chat(payload, schema, cancel)
        except AIError as exc:
            if "think" in payload and "does not support thinking" in exc.details:
                self.no_think.add(model)                  # einmal merken, ohne Schalter neu
                payload.pop("think")
                return self._chat(payload, schema, cancel)
            raise

    def _chat(self, payload: dict, schema: dict | None,
              cancel: threading.Event | None) -> str | dict[str, Any]:
        parts: list[str] = []
        for line in stream_lines(self.client, "/api/chat", payload, NOT_RUNNING, cancel):
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if data.get("error"):
                raise AIError("Ollama meldet einen Fehler.", str(data["error"]))
            parts.append(data.get("message", {}).get("content", ""))
            if data.get("done"):
                break
        text = "".join(parts).strip()
        if schema is None:
            return text
        try:
            return json.loads(text)
        except ValueError:
            raise AIError("Die Antwort der KI war unvollständig.", text[:300]) from None
