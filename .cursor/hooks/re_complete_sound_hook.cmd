@echo off
REM Cursor pipes JSON on stdin. Prefer venv python so stdin is not swallowed by `uv run`.
cd /d "%~dp0\..\.."
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -u ".cursor\hooks\re_complete_sound_hook.py"
) else (
  uv run python -u ".cursor\hooks\re_complete_sound_hook.py"
)
