@echo off
rem CodeCockpit ohne Konsolenfenster starten
rem In einem Branch-Ordner ohne eigene .venv gilt die Umgebung aus dem Ordner main
cd /d "%~dp0"
set "PY=.venv\Scripts\pythonw.exe"
if not exist "%PY%" set "PY=..\main\.venv\Scripts\pythonw.exe"
start "" "%PY%" main.py
