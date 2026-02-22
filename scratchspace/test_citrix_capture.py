"""
Quick test: find Citrix window and save a screenshot to scratchspace.
Run from repo root: python scratchspace/test_citrix_capture.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
os.chdir(REPO_ROOT)

def main():
    title = os.environ.get("CITRIX_WINDOW_TITLE", "RDSH Agenten YMMD - Desktop Viewer")
    print(f"Looking for window containing: {title!r}")

    from windows_use.desktop.window_utils import get_window_region_by_title
    region = get_window_region_by_title(title)
    if not region:
        print("ERROR: Citrix window not found. Is the session open on the second monitor?")
        return 1

    left, top, width, height = region
    print(f"Found window at ({left}, {top}), size {width}x{height}")

    import pyautogui
    img = pyautogui.screenshot(region=(left, top, width, height))
    out = os.path.join(REPO_ROOT, "scratchspace", "citrix_test_screenshot.png")
    img.save(out)
    print(f"Screenshot saved to: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
