# Email Automation Script (from debugg export)

Full Sprinklr Console email automation: connect to Chrome via CDP, login, set status to "Verfügbar", monitor for new emails, extract content, query Cursor AI (cursor-agent), write responses to the composition area.

## Prerequisites

1. **Chrome with remote debugging**  
   Close all Chrome windows, then run:
   ```cmd
   scratchspace\launch_chrome_remote_debug.bat
   ```
   Or: `chrome.exe --remote-debugging-port=9222`

2. **Playwright** (for CDP connection)
   ```bash
   uv pip install playwright
   playwright install chromium
   ```

3. **Optional: config.json** (in project root or scratchspace)  
   Example:
   ```json
   {
     "url": "https://telefonica-germany.sprinklr.com/app/console/c/69427bf4de56da19fa9f3efe",
     "cdp_endpoint": "http://localhost:9222",
     "check_interval_seconds": 5,
     "login_email": "harun.husic.external@telefonica.com",
     "login_password": "YOUR_PASSWORD",
     "cursor_cli_path": "wsl://cursor-agent",
     "cursor_api_key": "YOUR_CURSOR_API_KEY"
   }
   ```
   If omitted, script uses defaults (login from script, CDP on 9222).

4. **Optional: cursor-agent** (for AI responses)  
   For generating replies the script calls cursor-agent (e.g. via WSL). Without it, script can still connect, login, and monitor.

## Run

From **project root** (`c:\Users\PC ENTER\Desktop\Citrix`):

```bash
uv run python scratchspace/email_automation.py
```

Or with system Python (with playwright installed):

```bash
python scratchspace/email_automation.py
```

- Log file: `scratchspace/email_automation.log`
- Processed case IDs: `processed_case_ids.json` (in cwd)
- Output files: `output/<case_id>.txt`

## What it does

1. Connects to Chrome at `http://localhost:9222` (CDP).
2. Uses smart detection: skips login if already logged in, skips "Verfügbar" if already set.
3. Ensures Console tab is open.
4. Polls for new emails (collapsed-case-item), extracts thread, calls Cursor AI for handling instructions and customer reply.
5. Writes the reply into the Sprinklr composition area (or creates output files).

Source: exported from `C:\Users\PC ENTER\Downloads\debugg (2).md` (first full Python block).
