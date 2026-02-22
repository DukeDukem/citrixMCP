"""
Fallback: create folder 'test' and a text file with 'test test' on the Citrix desktop
using a fixed sequence of mouse/keyboard actions. Use this if MCP is not available.
Run from repo root: python scratchspace/citrix_create_test_folder_and_file.py

Requires: Citrix session open (window title contains CITRIX_WINDOW_TITLE).
"""
import os
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
os.chdir(REPO_ROOT)

CITRIX_WINDOW_TITLE = os.environ.get("CITRIX_WINDOW_TITLE", "RDSH Agenten YMMD - Desktop Viewer")


def main():
    from windows_use.desktop import Desktop
    from windows_use.desktop.window_utils import get_window_region_by_title
    import pyautogui

    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.4

    region = get_window_region_by_title(CITRIX_WINDOW_TITLE)
    if not region:
        print("ERROR: Citrix window not found. Is the session open?")
        return 1

    left, top, width, height = region
    desktop = Desktop(target_window_title=CITRIX_WINDOW_TITLE)
    desktop.get_state(use_vision=False)
    msg, status = desktop.switch_app(CITRIX_WINDOW_TITLE)
    print(msg)
    time.sleep(0.8)

    # Coordinates relative to Citrix window (approximate center of desktop area)
    cx = left + width // 2
    cy = top + height // 3

    # Right-click on desktop -> New -> Folder
    pyautogui.click(cx, cy, button="right")
    time.sleep(0.6)
    pyautogui.press("w")  # New (English); German: "n" for "Neu"
    time.sleep(0.3)
    pyautogui.press("f")  # Folder (English); German: "o" for "Ordner"
    time.sleep(0.8)

    # Type folder name and Enter
    pyautogui.typewrite("test", interval=0.08)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.8)

    # Double-click the new folder to open it (it's usually in the center/top area)
    pyautogui.doubleClick(cx, cy)
    time.sleep(0.8)

    # Right-click inside folder -> New -> Text Document
    pyautogui.click(cx, cy, button="right")
    time.sleep(0.6)
    pyautogui.press("w")
    time.sleep(0.3)
    pyautogui.press("t")  # Text Document (English); German: "t" for "Textdokument"
    time.sleep(0.8)

    # Name the file (e.g. test.txt)
    pyautogui.typewrite("test", interval=0.08)
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(0.6)

    # Double-click to open the file
    pyautogui.doubleClick(cx, cy)
    time.sleep(1.0)

    # Type content and save
    pyautogui.typewrite("test test", interval=0.08)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "s")
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(0.3)

    print("Done. Check the Citrix desktop for folder 'test' and the text file with 'test test'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
