# Bauanleitung für die Exe von CodeCockpit (PyInstaller, Phase 10).
# Das Cockpit baut sich damit selbst: Exe, "Exe aus dem Code erstellen". Pfade sind relativ zum
# Ordner Code. Features und Adapter werden erst zur Laufzeit geladen, deshalb stehen alle Module
# von cockpit ausdrücklich in hiddenimports. Tests und Checklisten kommen nicht in die Exe.
from pathlib import Path

from PyInstaller.utils.hooks import (collect_data_files, collect_dynamic_libs, collect_submodules,
                                     copy_metadata)

root = Path(SPECPATH)
datas = [(str(root / "anleitungen"), "anleitungen"),
         (str(root / "cockpit" / "ai" / "prompts"), "cockpit/ai/prompts")]
for intro in root.glob("cockpit/*/*/EINFUEHRUNG.md"):
    datas.append((str(intro), str(intro.parent.relative_to(root)).replace("\\", "/")))
datas += copy_metadata("keyring")
# Spracheingabe (8d): Whisper braucht seine Dateien (Sprachpausen-Erkennung) und die DLLs von
# CTranslate2 und PortAudio. Die Modelle selbst kommen nicht in die Exe.
datas += collect_data_files("faster_whisper") + collect_data_files("_sounddevice_data")
binaries = collect_dynamic_libs("ctranslate2") + collect_dynamic_libs("_sounddevice_data")

a = Analysis(["main.py"], pathex=[str(root)], binaries=binaries, datas=datas,
             hiddenimports=collect_submodules("cockpit") + ["keyring.backends.Windows",
                                                            "sounddevice", "faster_whisper"],
             excludes=["pytest", "pytestqt", "tests"])
pyz = PYZ(a.pure)

exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="CodeCockpit",
          console=False, icon=None, upx=False)
