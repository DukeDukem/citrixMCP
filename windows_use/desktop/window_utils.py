"""
Helper to find a top-level window by title and return its screen region
for use with pyautogui.screenshot(region=(left, top, width, height)).
"""
from uiautomation import GetRootControl, IsTopLevelWindow


def get_window_region_by_title(title_substring: str) -> tuple[int, int, int, int] | None:
    """
    Find a top-level window whose title contains the given substring.
    Returns (left, top, width, height) in screen coordinates for use as
    pyautogui.screenshot(region=...), or None if not found.
    """
    if not title_substring or not title_substring.strip():
        return None
    try:
        desktop = GetRootControl()
        for element in desktop.GetChildren():
            if not IsTopLevelWindow(element.NativeWindowHandle):
                continue
            name = element.Name or ""
            if title_substring.strip() in name:
                box = element.BoundingRectangle
                if box.isempty():
                    continue
                left = box.left
                top = box.top
                width = box.width()
                height = box.height()
                if width > 0 and height > 0:
                    return (left, top, width, height)
    except Exception:
        pass
    return None
