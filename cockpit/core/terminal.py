"""Eingebautes Terminal (Konzept 9.9, Teilschritt 8a).

Befehle laufen in PowerShell im Ordner des Projekts. Die Ausgabe kommt Zeile für Zeile zurück,
Fehlermeldungen in derselben Reihenfolge wie im Terminal.

Damit nichts hängen bleibt:
- Befehle bekommen keine Eingabe (stdin ist leer). Git fragt nie nach einem Passwort und öffnet
  weder Pager noch Editor.
- Ein laufender Befehl lässt sich abbrechen. Dabei endet auch alles, was er gestartet hat.

Sicherheit (CLAUDE.md):
- Git bekommt die Zugangsdaten des Kontos über Umgebungsvariablen, nie über die Befehlszeile.
- Tokens und andere Geheimnisse werden in jeder Zeile der Ausgabe verdeckt.
- Ein force push wird nie ausgeführt, auch nicht auf Wunsch.
"""
from __future__ import annotations

import base64
import logging
import os
import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from cockpit.core.errors import Cancelled, CockpitError
from cockpit.core.logging_setup import MASK, mask_secrets

log = logging.getLogger(__name__)

FORCE_PUSH = ("Ein force push überschreibt die Geschichte auf der Plattform. Das Cockpit führt "
              "ihn nie aus, auch nicht im Terminal. Holen Sie stattdessen die Änderungen und "
              "laden Sie danach normal hoch.")
WARNING = ("Befehle im Terminal laufen ohne Rückfrage und ohne Sicherheitskopie. Gesperrt ist nur "
           "der force push.")

_PUSH = re.compile(r"(?i)\bgit(?:\.exe)?\b[^;|&]*\bpush\b([^;|&]*)")
_FORCE = re.compile(r"(?i)(?:^|\s)(?:--force(?:-with-lease|-if-includes)?\b|-[a-z]*f[a-z]*\b|\+\S+)")


def is_force_push(command: str) -> bool:
    """Erkennt git push mit --force, -f, --force-with-lease oder +Branch."""
    for match in _PUSH.finditer(command):
        if _FORCE.search(match.group(1)):
            return True
    return False


def environment(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    """Umgebung für Befehle: nie warten, nie einen Pager oder Editor öffnen."""
    env = dict(os.environ)
    env.update({
        "GIT_TERMINAL_PROMPT": "0",           # nie nach Benutzername oder Passwort fragen
        "GCM_INTERACTIVE": "never",
        "GIT_PAGER": "cat",
        "PAGER": "cat",
        "GIT_EDITOR": ":",                    # kein Editor, zum Beispiel bei git commit ohne -m
        "GIT_SEQUENCE_EDITOR": ":",
        "LESS": "-FRX",
    })
    if extra:
        env.update(extra)
    return env


def _encoded(command: str) -> str:
    """PowerShell -EncodedCommand: UTF-16LE in Base64. So gibt es keine Probleme mit Anführungs-
    zeichen. Die Ausgabe wird auf UTF-8 gestellt, damit Umlaute stimmen."""
    # Fehler von PowerShell kämen sonst als XML. Deshalb laufen sie als Text durch die normale
    # Ausgabe, nur mit der Meldung selbst, ohne "In Zeile … Zeichen …".
    script = ("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
              "$OutputEncoding = [Text.Encoding]::UTF8; $ProgressPreference = 'SilentlyContinue'; "
              "$global:CockpitFailed = $false; $global:LASTEXITCODE = 0; "
              f"& {{ {command}\n}} 2>&1 | ForEach-Object {{ "
              "if ($_ -is [System.Management.Automation.ErrorRecord]) { "
              "if ($_.FullyQualifiedErrorId -ne 'NativeCommandError' -and "
              "$_.FullyQualifiedErrorId -ne 'NativeCommandErrorMessage') "
              "{ $global:CockpitFailed = $true }; $_.Exception.Message } else { $_ } } "
              "| Out-String -Stream -Width 4096; "
              "if ($global:LASTEXITCODE) { exit $global:LASTEXITCODE } "
              "elseif ($global:CockpitFailed) { exit 1 } else { exit 0 }")
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")


@dataclass
class Result:
    code: int
    lines: list[str]

    @property
    def ok(self) -> bool:
        return self.code == 0


_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")


def clean_line(raw: str) -> str:
    """Farb- und Steuerzeichen entfernen. Fortschrittsanzeigen (zum Beispiel bei ollama pull)
    überschreiben ihre Zeile mit Wagenrücklauf. Davon bleibt nur der letzte Stand."""
    text = _ANSI.sub("", raw).rstrip("\r\n")
    parts = [p for p in text.split("\r") if p.strip()]
    return (parts[-1] if parts else "").rstrip()


def _masker(extra: Mapping[str, str] | None) -> Callable[[str], str]:
    """Verdeckt bekannte Geheimnisse und die Werte der Zugangsdaten für Git."""
    values = [v for k, v in (extra or {}).items() if "VALUE" in k and len(v) > 8]

    def mask(line: str) -> str:
        for value in values:
            line = line.replace(value, MASK)
        return mask_secrets(line)
    return mask


def run(command: str, cwd: Path, on_line: Callable[[str], None] | None = None,
        extra_env: Mapping[str, str] | None = None,
        cancel: threading.Event | None = None) -> Result:
    """Befehl in PowerShell ausführen. Blockiert, also im Hintergrund aufrufen. on_line bekommt
    jede Zeile der Ausgabe, schon ohne Geheimnisse. Wirft Cancelled bei Abbruch."""
    command = command.strip()
    if not command:
        raise CockpitError("Bitte geben Sie einen Befehl ein.")
    if is_force_push(command):
        raise CockpitError(FORCE_PUSH)
    mask = _masker(extra_env)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        process = subprocess.Popen(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-OutputFormat", "Text",
             "-EncodedCommand", _encoded(command)],
            cwd=str(cwd), env=environment(extra_env), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags)
    except OSError as exc:
        raise CockpitError("PowerShell ließ sich nicht starten.", repr(exc)) from None
    lines: list[str] = []
    stopped = threading.Event()

    def watch() -> None:
        while not stopped.wait(0.2):
            if cancel is not None and cancel.is_set():
                _kill_tree(process)
                return

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        assert process.stdout is not None
        for raw in process.stdout:
            line = mask(clean_line(raw.decode("utf-8", "replace")))
            if not line.strip():
                continue                      # leere Zeilen stören auf der Braillezeile
            lines.append(line)
            if on_line is not None:
                on_line(line)
        code = process.wait()
    finally:
        stopped.set()
    if cancel is not None and cancel.is_set():
        raise Cancelled()
    log.info("Terminal in %s: Rückgabewert %s", cwd, code)
    return Result(code, lines)


def _kill_tree(process: subprocess.Popen) -> None:
    """Befehl samt allem, was er gestartet hat, beenden (taskkill /T)."""
    try:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError:
        process.kill()
