"""
Citrix MCP server for Cursor. Exposes tools to see and control the Citrix session.
Uses FastMCP. Do NOT print to stdout (reserved for MCP protocol).

Install: pip install fastmcp  (or: uv sync / pip install -e .)
Run: uv run scratchspace/mcp_citrix_server.py  (or python -u scratchspace/mcp_citrix_server.py)
"""
import os
import sys
import base64
from io import BytesIO

# Bootstrap path and cwd from script location (Cursor may run with different cwd)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)

# Log errors to file only (never stdout/stderr in production - stderr can break some MCP clients)
_ERR_LOG = os.path.join(_REPO_ROOT, "scratchspace", "mcp_citrix_error.txt")


def _err(msg: str) -> None:
    try:
        with open(_ERR_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


try:
    from fastmcp import FastMCP
except ImportError as e:
    _err(f"ImportError: {e}")
    _err("Run: pip install fastmcp  or  uv sync")
    raise

try:
    import pyautogui
except ImportError as e:
    _err(f"pyautogui: {e}")
    raise

_cursor = None
try:
    from humancursor import SystemCursor
    _cursor = SystemCursor()
except Exception:
    pass

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.3

CITRIX_WINDOW_TITLE = os.environ.get("CITRIX_WINDOW_TITLE", "RDSH Agenten YMMD - Desktop Viewer")
_last_region: tuple[int, int, int, int] | None = None

mcp = FastMCP(
    name="citrix-control",
    instructions="See and control the Citrix session. Follow Windows UI: right-click and double-click inside the File Explorer window (content area) when creating/opening files in a folder. Use citrix_click_explorer_content for that.",
)


def _get_desktop():
    from windows_use.desktop import Desktop
    return Desktop(target_window_title=CITRIX_WINDOW_TITLE)


def _get_region():
    from windows_use.desktop.window_utils import get_window_region_by_title
    return get_window_region_by_title(CITRIX_WINDOW_TITLE)


def _to_screen(x: int, y: int) -> tuple[int, int]:
    global _last_region
    if _last_region is None:
        _last_region = _get_region()
    if _last_region is None:
        return (x, y)
    left, top, _, _ = _last_region
    return (left + x, top + y)


def _move_and_click(x: int, y: int, button: str = "left", clicks: int = 1):
    sx, sy = _to_screen(x, y)
    if _cursor:
        try:
            _cursor.move_to((sx, sy))
            for _ in range(clicks):
                pyautogui.mouseDown(button=button)
                pyautogui.mouseUp(button=button)
            return
        except Exception:
            pass  # fall back to pyautogui
    pyautogui.click(sx, sy, button=button, clicks=clicks)


def _content_area_xy(frac_x: float = 0.72, frac_y: float = 0.42) -> tuple[int, int]:
    """Coordinates inside the File Explorer content area (file list, right side). Use for right-click New and double-click to open."""
    global _last_region
    if _last_region is None:
        _last_region = _get_region()
    if _last_region is None:
        return (960, 400)
    _, _, w, h = _last_region
    return (int(w * frac_x), int(h * frac_y))


_SCREENSHOT_PATH = os.path.join(_REPO_ROOT, "scratchspace", "citrix_current.png")


@mcp.tool
def citrix_screenshot() -> str:
    """Capture the Citrix session window. Returns an image. Call this first; coordinates in other tools are relative to this image (top-left = 0,0)."""
    global _last_region
    try:
        desktop = _get_desktop()
        img = desktop.get_screenshot(scale=0.8)
        _last_region = getattr(desktop, "_last_capture_region", None)
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        data_url = f"data:image/png;base64,{b64}"
        return f"Citrix screenshot:\n\n![screenshot]({data_url})"
    except Exception as e:
        _err(str(e))
        return f"Error capturing screenshot: {e}"


@mcp.tool
def citrix_screenshot_save() -> str:
    """Capture the Citrix window and save to scratchspace/citrix_current.png. Returns the file path so the image can be read to verify state after each action."""
    global _last_region
    try:
        desktop = _get_desktop()
        img = desktop.get_screenshot(scale=1.0)
        _last_region = getattr(desktop, "_last_capture_region", None)
        img.save(_SCREENSHOT_PATH)
        return _SCREENSHOT_PATH
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_focus() -> str:
    """Bring the Citrix window to the foreground so it receives keyboard and mouse input."""
    try:
        desktop = _get_desktop()
        desktop.get_state(use_vision=False)
        msg, status = desktop.switch_app(CITRIX_WINDOW_TITLE)
        return msg if status == 0 else f"Warning: {msg}"
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """Click at (x, y) on the Citrix screen. Coordinates are in pixels relative to the Citrix window (same as in the screenshot)."""
    try:
        _move_and_click(x, y, button=button, clicks=clicks)
        return f"Clicked at ({x},{y}) with {button}, {clicks} click(s)."
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_click_explorer_content(right_click: bool = False, double_click: bool = False) -> str:
    """Click inside the File Explorer content area (file list, right side of window). Call this when a folder is open so actions apply inside that folder. right_click=True for context menu (New -> Text Document). double_click=True to open the selected file (standard Windows pattern)."""
    try:
        x, y = _content_area_xy()
        button = "right" if right_click else "left"
        clicks = 2 if double_click else 1
        try:
            _move_and_click(x, y, button=button, clicks=clicks)
        except Exception:
            x, y = _content_area_xy(0.62, 0.38)  # fallback if first coords fail (e.g. cursor lib)
            _move_and_click(x, y, button=button, clicks=clicks)
        return f"Clicked in Explorer content at ({x},{y}) with {button}, {clicks} click(s)."
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_type(text: str) -> str:
    """Type the given text. Use after focusing the target (e.g. click in a text field). For special keys use citrix_key."""
    try:
        pyautogui.typewrite(text, interval=0.05)
        return f"Typed: {text!r}"
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_key(key: str) -> str:
    """Press a single key. Examples: enter, tab, escape, backspace, up, down, left, right, home, end."""
    try:
        pyautogui.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_hotkey(keys: list[str]) -> str:
    """Press a key combination. Pass keys as a list, e.g. [\"ctrl\", \"c\"] for copy."""
    try:
        pyautogui.hotkey(*keys)
        return f"Pressed: {'+'.join(keys)}"
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as e:
        _err(str(e))
        import traceback
        _err(traceback.format_exc())
        raise
