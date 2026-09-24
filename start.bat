@echo off
rem CodeCockpit ohne Konsolenfenster starten
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" main.py
