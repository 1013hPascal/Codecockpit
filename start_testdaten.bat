@echo off
rem CodeCockpit mit Testdaten starten (eigener Datenordner, echte Daten bleiben unberuehrt)
rem In einem Branch-Ordner ohne eigene .venv gilt die Umgebung aus dem Ordner main
cd /d "%~dp0"
set "PY=.venv\Scripts\pythonw.exe"
if not exist "%PY%" set "PY=..\main\.venv\Scripts\pythonw.exe"
start "" "%PY%" main.py --testdaten
