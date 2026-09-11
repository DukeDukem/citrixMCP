@echo off
cd /d "%~dp0\..\.."
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -u ".cursor\hooks\extract_auto_continue_hook.py"
) else (
  uv run python -u ".cursor\hooks\extract_auto_continue_hook.py"
)
