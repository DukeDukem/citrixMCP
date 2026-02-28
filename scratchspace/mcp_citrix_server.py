"""
Citrix MCP server for Cursor. Exposes tools to see and control the Citrix session.
Uses FastMCP. Do NOT print to stdout (reserved for MCP protocol).

Install: pip install fastmcp  (or: uv sync / pip install -e .)
Run: uv run scratchspace/mcp_citrix_server.py  (or python -u scratchspace/mcp_citrix_server.py)
"""
import os
import sys
import base64
import time
import string
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

try:
    from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
except ImportError as e:
    _err(f"Pillow: {e}")
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
_previous_screenshot: Image.Image | None = None

_MCP_INSTRUCTIONS = """\
Citrix Vision-Aware MCP Server -- tools to see, understand, and control a Citrix remote desktop session.

IMPORTANT: The Citrix session is a remote desktop rendered as a flat image. There is NO accessibility
tree inside it. All interaction is coordinate-based, so you MUST use vision tools to understand the
screen before acting.

== RECOMMENDED WORKFLOW ==

1. SURVEY: Call citrix_screenshot or citrix_grid_screenshot to see the full Citrix screen.
   - citrix_grid_screenshot overlays a labeled grid (A1, B2, ...) so you can refer to regions.
   - All coordinates in other tools are relative to the Citrix window (top-left = 0,0).

2. LOCATE: Use citrix_find_text to extract visible text labels and their approximate positions.
   - This helps you find buttons, menus, fields by their text without guessing coordinates.

3. INSPECT: Before clicking, call citrix_inspect_point(x, y) to see a zoomed-in view of that
   coordinate with a crosshair marker. This lets you verify you are targeting the correct element.

4. ACT: Use citrix_click, citrix_type, citrix_key, citrix_hotkey to interact.
   - citrix_click supports verify=true to automatically capture before/after screenshots.

5. VERIFY: After acting, call citrix_diff to compare the screen before and after your action.
   - This highlights exactly what changed, helping you detect focus shifts, new dialogs, errors.
   - Repeat from step 1 or 3 as needed.

== TIPS ==
- Use right-click (button="right") inside File Explorer content area to get context menus.
- Use double-click (clicks=2) to open files/folders.
- When unsure what is at a coordinate, ALWAYS inspect before clicking.
- After every action, verify the result before proceeding to the next step.
"""

mcp = FastMCP(
    name="citrix-control",
    instructions=_MCP_INSTRUCTIONS,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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
            pass
    pyautogui.click(sx, sy, button=button, clicks=clicks)


def _content_area_xy(frac_x: float = 0.72, frac_y: float = 0.42) -> tuple[int, int]:
    global _last_region
    if _last_region is None:
        _last_region = _get_region()
    if _last_region is None:
        return (960, 400)
    _, _, w, h = _last_region
    return (int(w * frac_x), int(h * frac_y))


def _capture_full(scale: float = 1.0) -> Image.Image:
    """Capture the Citrix window at the given scale and update _last_region."""
    global _last_region
    desktop = _get_desktop()
    img = desktop.get_screenshot(scale=scale)
    _last_region = getattr(desktop, "_last_capture_region", None)
    return img


def _img_to_data_url(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _load_font(size: int = 14):
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


_SCREENSHOT_PATH = os.path.join(_REPO_ROOT, "scratchspace", "citrix_current.png")


# ---------------------------------------------------------------------------
# Original tools (preserved)
# ---------------------------------------------------------------------------

@mcp.tool
def citrix_screenshot() -> str:
    """Capture the Citrix session window. Returns an image. Call this first; coordinates in other tools are relative to this image (top-left = 0,0)."""
    try:
        img = _capture_full(scale=0.8)
        data_url = _img_to_data_url(img)
        return f"Citrix screenshot ({img.width}x{img.height} at 0.8x scale):\n\n![screenshot]({data_url})"
    except Exception as e:
        _err(str(e))
        return f"Error capturing screenshot: {e}"


@mcp.tool
def citrix_screenshot_save() -> str:
    """Capture the Citrix window and save to scratchspace/citrix_current.png. Returns the file path so the image can be read to verify state after each action."""
    try:
        img = _capture_full(scale=1.0)
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
def citrix_click(x: int, y: int, button: str = "left", clicks: int = 1, verify: bool = False) -> str:
    """Click at (x, y) on the Citrix screen. Coordinates are in pixels relative to the Citrix window (same as in the screenshot). Set verify=true to capture before/after screenshots automatically -- the result will include both images so you can see what changed."""
    global _previous_screenshot
    try:
        before_url = None
        if verify:
            before_img = _capture_full(scale=0.8)
            _previous_screenshot = before_img
            before_url = _img_to_data_url(before_img)

        _move_and_click(x, y, button=button, clicks=clicks)

        result = f"Clicked at ({x},{y}) with {button}, {clicks} click(s)."

        if verify:
            time.sleep(0.5)
            after_img = _capture_full(scale=0.8)
            _previous_screenshot = after_img
            after_url = _img_to_data_url(after_img)
            result += f"\n\nBefore:\n![before]({before_url})\n\nAfter:\n![after]({after_url})"

        return result
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
            x, y = _content_area_xy(0.62, 0.38)
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
    """Press a key combination. Pass keys as a list, e.g. ["ctrl", "c"] for copy."""
    try:
        pyautogui.hotkey(*keys)
        return f"Pressed: {'+'.join(keys)}"
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# NEW: Vision-aware tools
# ---------------------------------------------------------------------------

@mcp.tool
def citrix_inspect_point(x: int, y: int, radius: int = 120) -> str:
    """Zoom into a specific coordinate on the Citrix screen and show a crosshair at the exact point. Use this BEFORE clicking to verify what UI element is at that location. The returned image is a cropped, 3x-zoomed view centered on (x, y). Coordinates are relative to the Citrix window (same as citrix_click)."""
    try:
        img = _capture_full(scale=1.0)
        w, h = img.size

        left = max(0, x - radius)
        top = max(0, y - radius)
        right = min(w, x + radius)
        bottom = min(h, y + radius)
        crop = img.crop((left, top, right, bottom))

        zoom = 3
        crop = crop.resize((crop.width * zoom, crop.height * zoom), Image.Resampling.NEAREST)

        draw = ImageDraw.Draw(crop)
        cx = (x - left) * zoom
        cy = (y - top) * zoom

        line_color = (255, 0, 0)
        draw.line([(cx, 0), (cx, crop.height)], fill=line_color, width=2)
        draw.line([(0, cy), (crop.width, cy)], fill=line_color, width=2)

        ring_r = 12
        draw.ellipse(
            [(cx - ring_r, cy - ring_r), (cx + ring_r, cy + ring_r)],
            outline=line_color, width=2,
        )

        font = _load_font(16)
        label = f"({x}, {y})"
        label_x = min(cx + 16, crop.width - 80)
        label_y = max(cy - 24, 4)
        draw.rectangle(
            [(label_x - 2, label_y - 2), (label_x + len(label) * 10, label_y + 18)],
            fill=(0, 0, 0, 180),
        )
        draw.text((label_x, label_y), label, fill=(255, 255, 255), font=font)

        data_url = _img_to_data_url(crop)
        return (
            f"Inspect point ({x},{y}) -- {zoom}x zoom, {radius}px radius:\n\n"
            f"![inspect]({data_url})"
        )
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_grid_screenshot(columns: int = 10, rows: int = 8) -> str:
    """Capture the Citrix screen with a labeled grid overlay. Each cell is labeled with a reference like A1, B3, etc. (columns = letters A-J, rows = numbers 1-8). Use this to get spatial awareness and refer to screen regions by grid cell. The grid coordinates are printed along the edges so you can map a cell label to pixel coordinates."""
    try:
        img = _capture_full(scale=0.8)
        overlay = img.copy()
        draw = ImageDraw.Draw(overlay)
        w, h = overlay.size
        font = _load_font(12)
        label_font = _load_font(11)

        cell_w = w / columns
        cell_h = h / rows

        grid_color = (255, 255, 0, 200)

        for col in range(1, columns):
            x = int(col * cell_w)
            draw.line([(x, 0), (x, h)], fill=grid_color, width=1)
        for row in range(1, rows):
            y = int(row * cell_h)
            draw.line([(0, y), (w, y)], fill=grid_color, width=1)

        col_letters = list(string.ascii_uppercase[:columns])
        cell_info_lines = []

        for row_idx in range(rows):
            for col_idx in range(columns):
                label = f"{col_letters[col_idx]}{row_idx + 1}"
                cx = int(col_idx * cell_w + cell_w / 2)
                cy = int(row_idx * cell_h + cell_h / 2)

                tw = draw.textlength(label, font=label_font)
                tx = cx - tw / 2
                ty = cy - 7

                draw.rectangle(
                    [(tx - 2, ty - 1), (tx + tw + 2, ty + 15)],
                    fill=(0, 0, 0, 160),
                )
                draw.text((tx, ty), label, fill=(255, 255, 0), font=label_font)

                px_left = int(col_idx * cell_w)
                px_top = int(row_idx * cell_h)
                px_right = int((col_idx + 1) * cell_w)
                px_bottom = int((row_idx + 1) * cell_h)
                cell_info_lines.append(
                    f"  {label}: pixels ({px_left},{px_top})-({px_right},{px_bottom}), center ({cx},{cy})"
                )

        data_url = _img_to_data_url(overlay)
        cell_map = "\n".join(cell_info_lines)

        return (
            f"Citrix grid screenshot ({columns}x{rows} grid, image {w}x{h}):\n\n"
            f"![grid]({data_url})\n\n"
            f"Grid cell pixel ranges:\n{cell_map}"
        )
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_diff(threshold: int = 30) -> str:
    """Compare the current Citrix screen to the previously captured screenshot. Highlights regions that changed with red overlays. Use this after performing an action (click, type, key) to see what changed on screen -- new dialogs, focus changes, text appearing, etc. The threshold controls sensitivity (lower = more sensitive, default 30). Returns the diff image and a list of changed region bounding boxes."""
    global _previous_screenshot
    try:
        current = _capture_full(scale=0.8)

        if _previous_screenshot is None:
            _previous_screenshot = current
            return "No previous screenshot to compare against. Take a screenshot first, perform an action, then call citrix_diff."

        prev = _previous_screenshot
        _previous_screenshot = current

        prev_resized = prev.resize(current.size, Image.Resampling.LANCZOS) if prev.size != current.size else prev

        diff = ImageChops.difference(current.convert("RGB"), prev_resized.convert("RGB"))
        gray_diff = diff.convert("L")

        binary = gray_diff.point(lambda p: 255 if p > threshold else 0)
        blurred = binary.filter(ImageFilter.MaxFilter(size=7))

        result = current.copy().convert("RGBA")
        red_overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        red_draw = ImageDraw.Draw(red_overlay)

        changed_regions = []
        region_size = 40
        w, h = blurred.size
        pixels = blurred.load()

        for ry in range(0, h, region_size):
            for rx in range(0, w, region_size):
                block_sum = 0
                count = 0
                for by in range(ry, min(ry + region_size, h)):
                    for bx in range(rx, min(rx + region_size, w)):
                        block_sum += pixels[bx, by]
                        count += 1
                if count > 0 and (block_sum / count) > 30:
                    r_right = min(rx + region_size, w)
                    r_bottom = min(ry + region_size, h)
                    red_draw.rectangle(
                        [(rx, ry), (r_right, r_bottom)],
                        outline=(255, 0, 0, 200), width=2,
                    )
                    changed_regions.append(
                        f"  ({rx},{ry})-({r_right},{r_bottom})"
                    )

        result = Image.alpha_composite(result, red_overlay)

        data_url = _img_to_data_url(result.convert("RGB"))

        if not changed_regions:
            summary = "No significant changes detected."
        else:
            summary = f"{len(changed_regions)} changed region(s):\n" + "\n".join(changed_regions)

        return (
            f"Screen diff (threshold={threshold}):\n\n"
            f"![diff]({data_url})\n\n"
            f"{summary}"
        )
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_find_text(scale: float = 1.0) -> str:
    """Extract visible text and approximate positions from the Citrix screen. Divides the screen into a grid of strips and uses OCR (if pytesseract is available) to find text. Falls back to returning a high-res screenshot for the AI to read visually. Each result includes the text, its bounding box, and center coordinates you can pass to citrix_click."""
    try:
        img = _capture_full(scale=scale)
        w, h = img.size

        try:
            import pytesseract
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            results = []
            n = len(data["text"])
            for i in range(n):
                text = data["text"][i].strip()
                if not text or len(text) < 2:
                    continue
                conf = int(data["conf"][i])
                if conf < 40:
                    continue
                bx = data["left"][i]
                by = data["top"][i]
                bw = data["width"][i]
                bh = data["height"][i]
                cx = bx + bw // 2
                cy = by + bh // 2
                results.append(
                    f'  "{text}" at ({cx},{cy}) box=({bx},{by},{bx+bw},{by+bh}) conf={conf}'
                )

            if results:
                return (
                    f"Found {len(results)} text element(s) on screen ({w}x{h}):\n"
                    + "\n".join(results)
                )
            else:
                data_url = _img_to_data_url(img)
                return (
                    f"OCR found no text. Here is the full screenshot for visual inspection:\n\n"
                    f"![screenshot]({data_url})"
                )
        except ImportError:
            data_url = _img_to_data_url(img)
            return (
                f"pytesseract not installed -- returning full screenshot ({w}x{h}) for visual text reading.\n"
                f"Install pytesseract + Tesseract-OCR for automatic text extraction.\n\n"
                f"![screenshot]({data_url})"
            )

    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


@mcp.tool
def citrix_snapshot() -> str:
    """Save the current screen state internally for later comparison with citrix_diff. Call this before performing an action, then call citrix_diff after to see what changed. This is lighter than citrix_screenshot -- it does not return an image, just stores it."""
    global _previous_screenshot
    try:
        _previous_screenshot = _capture_full(scale=0.8)
        return f"Snapshot saved ({_previous_screenshot.width}x{_previous_screenshot.height}). Perform an action, then call citrix_diff to see changes."
    except Exception as e:
        _err(str(e))
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as e:
        _err(str(e))
        import traceback
        _err(traceback.format_exc())
        raise
