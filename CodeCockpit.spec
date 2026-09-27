# Bauanleitung für die Exe von CodeCockpit (PyInstaller, Phase 10).
# Das Cockpit baut sich damit selbst: Exe, "Exe aus dem Code erstellen". Pfade sind relativ zum
# Ordner Code. Features und Adapter werden erst zur Laufzeit geladen, deshalb stehen alle Module
# von cockpit ausdrücklich in hiddenimports. Tests und Checklisten kommen nicht in die Exe.
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

root = Path(SPECPATH)
datas = [(str(root / "anleitungen"), "anleitungen"),
         (str(root / "cockpit" / "ai" / "prompts"), "cockpit/ai/prompts")]
for intro in root.glob("cockpit/*/*/EINFUEHRUNG.md"):
    datas.append((str(intro), str(intro.parent.relative_to(root)).replace("\\", "/")))
datas += copy_metadata("keyring")

a = Analysis(["main.py"], pathex=[str(root)], binaries=[], datas=datas,
             hiddenimports=collect_submodules("cockpit") + ["keyring.backends.Windows"],
             excludes=["pytest", "pytestqt", "tests"])
pyz = PYZ(a.pure)

exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="CodeCockpit",
          console=False, icon=None, upx=False)
