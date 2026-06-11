@echo off
setlocal
cd /d "%~dp0backend"
..\venv\Scripts\python.exe cli.py %*
