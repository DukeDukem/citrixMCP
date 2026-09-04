@echo off
cd /d "%~dp0\..\.."
uv run python .cursor/hooks/re_complete_sound_hook.py
