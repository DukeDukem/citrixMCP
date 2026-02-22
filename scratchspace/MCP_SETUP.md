# Use Cursor (this AI) to control Citrix

The Citrix MCP server is configured to use **uv** so Cursor gets the right Python environment. Follow these steps so the server stops erroring.

## 1. Install uv (one-time) — recommended

The MCP config uses **uv** so Cursor runs the server with the right dependencies. Install uv if you don’t have it:

**Windows (PowerShell):**
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Then **restart your terminal** (or Cursor) so `uv` is on PATH. Or install from https://github.com/astral-sh/uv#installation.

## 2. Install project dependencies

From the **Citrix** project folder (e.g. `c:\Users\PC ENTER\Desktop\Citrix`):

```bash
uv sync
```

Or, if you use pip and a venv:

```bash
pip install -e .
```

This installs FastMCP and the rest of the project so the MCP server can run.

## 3. Use the MCP config

The repo already has an MCP config that uses **uv**:

- **Workspace:** `Citrix/.cursor/mcp.json` (used when you open the Citrix folder in Cursor).
- **Global:** Your `~/.cursor/mcp.json` has been updated to the same **uv**-based citrix server.

Config in use:

```json
{
  "mcpServers": {
    "citrix": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "c:\\Users\\PC ENTER\\Desktop\\Citrix",
        "scratchspace/mcp_citrix_server.py"
      ],
      "cwd": "c:\\Users\\PC ENTER\\Desktop\\Citrix"
    }
  }
}
```

Cursor will run: `uv run --project <Citrix> scratchspace/mcp_citrix_server.py` with `cwd` = Citrix, so the script finds `windows_use` and all deps.

## 4. Restart Cursor / refresh MCP

1. Fully quit Cursor (File → Exit or close the window).
2. Open Cursor again and open the **Citrix** project folder.
3. Go to **Settings → Features → MCP** and check that the **citrix** server is listed and **not** in error.

If it still shows as errored, open **scratchspace/mcp_citrix_error.txt** and fix the exception (e.g. missing dependency, wrong path).

## 5. Test in chat

With the Citrix session open on the second monitor, in Cursor chat you can say:

- *"Focus the Citrix window and take a screenshot."*
- *"On the Citrix desktop, create a folder called test and a text file in it with 'test test'."*

The AI will use the Citrix MCP tools to do it.

---

## Fallback: no uv (use Python + venv)

If you prefer not to install uv:

1. In the Citrix folder create a venv and install the project:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```
2. Copy the contents of **scratchspace/mcp_citrix_config_python.json** into your MCP config (Cursor Settings → MCP → Edit config), or merge the `citrix` entry into your existing `mcpServers`. Adjust the path to `.venv\\Scripts\\python.exe` if your Citrix folder is elsewhere.
3. Save, then restart Cursor or refresh MCP.

---

## Complete the task without MCP

To create the test folder and file without using MCP:

```bash
uv run scratchspace/citrix_create_test_folder_and_file.py
```

(or `python scratchspace/citrix_create_test_folder_and_file.py` if your env has the deps).

## Tools

| Tool | Purpose |
|------|--------|
| `citrix_screenshot` | Capture the Citrix window so the AI can “see” the screen. |
| `citrix_focus` | Bring the Citrix window to the front. |
| `citrix_click` | Click at (x, y) relative to the screenshot. |
| `citrix_type` | Type text. |
| `citrix_key` | Press one key (enter, tab, etc.). |
| `citrix_hotkey` | Press a combo (e.g. ctrl+c). |

## Env

- `CITRIX_WINDOW_TITLE` — Window title to target (default: `RDSH Agenten YMMD - Desktop Viewer`).
