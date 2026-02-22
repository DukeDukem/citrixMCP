@echo off
REM Run from Citrix project root. Tests capture then starts MCP server for Cursor.
cd /d "%~dp0\.."

echo [1/2] Testing Citrix window capture...
python scratchspace\test_citrix_capture.py
if errorlevel 1 (
    echo Make sure the Citrix session is open on the second monitor.
    pause
    exit /b 1
)
echo.
echo [2/2] Starting MCP server. Keep this window open and add the server in Cursor MCP settings.
echo       See scratchspace\MCP_SETUP.md for Cursor config.
echo.
python scratchspace\mcp_citrix_server.py
pause
