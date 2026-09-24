@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py %*
) else (
    echo Python environment is missing. Follow the setup instructions in README.md.
    pause
    exit /b 1
)
