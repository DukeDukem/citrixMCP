"""
One-off: save Citrix window screenshot to scratchspace/citrix_desktop.png
and print window region (left, top, width, height). Coordinates in the image
match citrix_click(x, y) - origin top-left of window.
"""
import os
import sys
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _REPO_ROOT)
os.chdir(_REPO_ROOT)

from windows_use.desktop import Desktop
from windows_use.desktop.window_utils import get_window_region_by_title

CITRIX_WINDOW_TITLE = os.environ.get("CITRIX_WINDOW_TITLE", "RDSH Agenten YMMD - Desktop Viewer")
out_path = os.path.join(_REPO_ROOT, "scratchspace", "citrix_current.png")

from time import sleep
desktop = Desktop(target_window_title=CITRIX_WINDOW_TITLE)
desktop.get_state(use_vision=False)
# try to bring window to front so capture is not black
try:
    desktop.switch_app(CITRIX_WINDOW_TITLE)
except Exception:
    pass
sleep(1.2)
region = get_window_region_by_title(CITRIX_WINDOW_TITLE)
if not region:
    print("Citrix window not found", file=sys.stderr)
    sys.exit(1)
left, top, width, height = region
print(f"Region: left={left} top={top} width={width} height={height}")

img = desktop.get_screenshot(scale=1.0)  # full size so coords match citrix_click
img.save(out_path)
print(f"Saved: {out_path}")
