"""Fehlende Importe (Rückmeldung vom 02.10.2026): Die KI baute sys.executable in die Vokabel-App
ein, ohne "import sys". Die Exe stürzte mit NameError ab. Das Cockpit erkennt und ergänzt so etwas
jetzt selbst, ohne KI, und schreibt keinen Code, der nicht übersetzt.
"""
from __future__ import annotations

import pytest

from cockpit.core import exe
from cockpit.core.errors import CockpitError
from cockpit.features.exe_build import ai_fix, imports_check, setup_check

ENGINE = '''"""Vokabeln lernen."""
import csv
from pathlib import Path


class VocabEngine:
    def __init__(self, base_dir="Meine-Vokabeln"):
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).parent / base_dir
'''


def test_missing_sys_is_found():
    assert imports_check.missing(ENGINE) == ["import sys"]
    assert imports_check.missing("import sys\nprint(sys.argv)\n") == []
    assert imports_check.missing("import os, sys\nsys.exit()\n") == []
    assert imports_check.missing("from sys import argv\nsys.exit()\n") == []


def test_text_and_comments_do_not_count():
    assert imports_check.missing('text = "nutze sys.argv"\n# os.path ist toll\n') == []
    assert imports_check.missing("self.os.path = 1\nfotos.append(1)\n") == []


def test_os_and_path():
    assert imports_check.missing("os.makedirs('x')\nPath('y')\n") == [
        "import os", "from pathlib import Path"]
    assert imports_check.missing("from pathlib import Path, PurePath\nPath('y')\n") == []
    assert imports_check.missing("from pathlib import (\n    Path,\n)\nPath('y')\n") == []


def test_import_goes_before_the_first_import():
    fixed, added = imports_check.add_imports(ENGINE)
    assert added == ["import sys"]
    assert fixed.splitlines()[:3] == ['"""Vokabeln lernen."""', "import sys", "import csv"]
    future = "from __future__ import annotations\nx = sys.argv\n"
    assert imports_check.add_imports(future)[0] == (
        "from __future__ import annotations\nimport sys\nx = sys.argv\n")


def test_small_change_shows_only_the_spot():
    old, new, added = imports_check.small_change(ENGINE)
    assert (old, new, added) == ("import csv\n", "import sys\nimport csv\n", ["import sys"])
    assert imports_check.small_change("import sys\nsys.exit()\n") is None


def test_compile_problem():
    assert imports_check.compile_problem("x = 1\n", "a.py") == ""
    assert imports_check.compile_problem("def f(:\n", "a.py").startswith("a.py, Zeile 1:")


def test_fixed_part_proposes_the_import(tmp_path):
    (tmp_path / "engine.py").write_text(ENGINE, encoding="utf-8")
    (tmp_path / "gui.py").write_text("import sys\nprint(sys.argv)\n", encoding="utf-8")
    proposal = ai_fix.fixed_part(tmp_path, exe.BuildSettings("gui.py", "V"))
    changes = [c for c in proposal.changes if c.file == "engine.py"]
    assert len(changes) == 1 and changes[0].reason.startswith("import sys fehlt")
    ai_fix.check_changes(tmp_path, proposal)
    assert not changes[0].problem                                # passt genau


def test_apply_adds_the_import_the_ai_forgot(tmp_path, home):
    (tmp_path / "engine.py").write_text("import csv\n\nBASE = 'Meine-Vokabeln'\n",
                                        encoding="utf-8")
    proposal = ai_fix.Proposal(changes=[ai_fix.Change(
        "engine.py", "Ordner neben der Exe", "BASE = 'Meine-Vokabeln'\n",
        "BASE = Path(sys.executable).parent / 'Meine-Vokabeln'\n")])
    ai_fix.apply("V", tmp_path, proposal)
    text = (tmp_path / "engine.py").read_text(encoding="utf-8")
    assert text.splitlines()[:3] == ["import sys", "from pathlib import Path", "import csv"]
    assert proposal.notes == ["Ergänzt in engine.py: import sys, from pathlib import Path."]


def test_apply_writes_nothing_when_the_code_is_broken(tmp_path, home):
    original = "import csv\n\nBASE = 1\n"
    (tmp_path / "engine.py").write_text(original, encoding="utf-8")
    proposal = ai_fix.Proposal(changes=[ai_fix.Change("engine.py", "kaputt", "BASE = 1\n",
                                                      "def f(:\n")])
    with pytest.raises(CockpitError) as raised:
        ai_fix.apply("V", tmp_path, proposal)
    assert raised.value.message.startswith("Die Änderungen der KI ergeben fehlerhaften Code.")
    assert "engine.py, Zeile" in raised.value.details
    assert (tmp_path / "engine.py").read_text(encoding="utf-8") == original


def test_setup_check_names_the_missing_import(tmp_path):
    (tmp_path / "engine.py").write_text(ENGINE, encoding="utf-8")
    (tmp_path / "gui.py").write_text("import engine\n", encoding="utf-8")
    lines = setup_check.check_for(tmp_path, exe.BuildSettings("gui.py", "V"))
    assert any(line.startswith("Problem: engine.py benutzt etwas, ohne es zu importieren. "
                               "Es fehlt: import sys.") for line in lines)
