"""Fehlende Importe finden und ergänzen, ohne KI (Rückmeldung des Nutzers vom 02.10.2026).

Die KI baute in die Vokabel-App sys.executable ein, vergaß aber "import sys". Die Exe stürzte dann
beim Start mit NameError ab. Solche Fehler sind leicht zu erkennen: Ein Modul wird benutzt, aber
nirgends importiert. Dieses Modul findet das für sys, os und Path und fügt die Zeile ein, vor dem
ersten Import der Datei. Außerdem prüft es, ob der Code überhaupt übersetzt.
"""
from __future__ import annotations

import ast
import re

# Name: (Muster für die Benutzung, Muster für den Import, Zeile zum Ergänzen)
NAMES = {
    "sys": (r"(?<![.\w])sys\.", r"^\s*import\s+[^\n#]*\bsys\b|^\s*from\s+sys\s+import",
            "import sys"),
    "os": (r"(?<![.\w])os\.", r"^\s*import\s+[^\n#]*\bos\b|^\s*from\s+os\s+import",
           "import os"),
    "Path": (r"(?<![.\w])Path\(", r"^\s*from\s+pathlib\s+import\s+[^\n#]*\bPath\b"
             r"|^\s*from\s+pathlib\s+import\s*\([^)]*\bPath\b", "from pathlib import Path"),
}


def _code_only(text: str) -> str:
    """Text ohne Kommentare und Zeichenketten, damit "sys." in einem Text nicht zählt."""
    text = re.sub(r'("""|\'\'\')(?:.|\n)*?\1', "", text)
    text = re.sub(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', '""', text)
    return re.sub(r"#[^\n]*", "", text)


def missing(text: str) -> list[str]:
    """Import-Zeilen, die fehlen, zum Beispiel ["import sys"]."""
    code = _code_only(text)
    result = []
    for used, imported, line in NAMES.values():
        if re.search(used, code) and not re.search(imported, text, re.MULTILINE):
            result.append(line)
    return result


def _insert_at(text: str) -> int:
    """Zeilennummer (ab 0), vor der die Importe kommen: vor dem ersten normalen Import, sonst
    nach Modul-Docstring und from __future__."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    after = 0
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            after = node.end_lineno
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return node.lineno - 1
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str) and after == 0 and node is tree.body[0]):
            after = node.end_lineno
            continue
        break
    return after


def add_imports(text: str) -> tuple[str, list[str]]:
    """Fehlende Importe einfügen. Gibt den neuen Text und die eingefügten Zeilen zurück."""
    lines_needed = missing(text)
    if not lines_needed:
        return text, []
    lines = text.splitlines(keepends=True)
    index = _insert_at(text)
    newline = "\r\n" if "\r\n" in text else "\n"
    block = "".join(line + newline for line in lines_needed)
    return "".join(lines[:index]) + block + "".join(lines[index:]), lines_needed


def small_change(text: str) -> tuple[str, str, list[str]] | None:
    """Kleine Änderung zum Anzeigen: (alt, neu, eingefügte Zeilen). Alt ist die Zeile, vor der
    die Importe kommen, wenn sie nur einmal vorkommt, sonst der ganze Text. None: nichts fehlt."""
    fixed, added = add_imports(text)
    if not added:
        return None
    lines = text.splitlines(keepends=True)
    index = _insert_at(text)
    if index < len(lines) and lines[index].strip() and text.count(lines[index]) == 1:
        anchor = lines[index]
        newline = "\r\n" if "\r\n" in text else "\n"
        return anchor, "".join(line + newline for line in added) + anchor, added
    return text, fixed, added


def compile_problem(text: str, filename: str) -> str:
    """Leerer Text, wenn der Code übersetzt, sonst ein Satz mit Zeile und Grund."""
    try:
        compile(text, filename, "exec")
    except SyntaxError as exc:
        return f"{filename}, Zeile {exc.lineno}: {exc.msg}"
    except ValueError as exc:
        return f"{filename}: {exc}"
    return ""
