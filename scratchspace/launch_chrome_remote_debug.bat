@echo off
REM Launch Chrome with remote debugging for Sprinklr automation.
REM Close any open Chrome windows first, then run this script.

set CHROME_PATH=
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
where chrome.exe >nul 2>&1
if %ERRORLEVEL% equ 0 if "%CHROME_PATH%"=="" set CHROME_PATH=chrome.exe

if "%CHROME_PATH%"=="" (
    echo Chrome not found. Install Google Chrome or set CHROME_PATH.
    pause
    exit /b 1
)

echo Launching Chrome with remote debugging on port 9222...
start "" "%CHROME_PATH%" --remote-debugging-port=9222
echo Done. Then run: uv run python scratchspace/sprinklr_start_and_login.py
pause
