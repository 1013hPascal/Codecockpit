@echo off
rem CodeCockpit mit Testdaten starten (eigener Datenordner, echte Daten bleiben unberuehrt)
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" main.py --testdaten
