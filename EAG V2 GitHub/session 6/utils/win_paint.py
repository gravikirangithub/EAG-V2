import time, subprocess
import pyautogui as pag
from pywinauto import Application, Desktop

pag.FAILSAFE = True

# Absolute screen coordinates provided by user via getCoords.py
# Defaults work on many 1080p, 100% DPI setups; we now also compute
# relative positions from the Paint window rectangle when possible.
ABS_TEXT_TOOL_POS = (515, 130)
ABS_COLOR_CLICK_POS = (800, 520)

# Approximate color palette grid relative to the Paint window's top-left.
# These offsets are conservative and should work on standard layouts.
# If DPI/layout differs, we gracefully fall back to ABS_COLOR_CLICK_POS.
_PALETTE_OFFSET_X = 1195  # relative to window left
_PALETTE_OFFSET_Y = 125  # relative to window top
_PALETTE_CELL_W = 28
_PALETTE_CELL_H = 28

# A best-effort mapping of common color names to palette grid indices (col, row)
# based on the classic MS Paint default palette ordering.
_COLOR_TO_INDEX = {
    "black": (0, 0),
    "gray": (1, 0),
    "brown": (2, 0),
    "red": (3, 0),
    "orange": (4, 0),
    "yellow": (5, 0),
    "green": (8, 0),
    "blue": (11, 0),
    "purple": (12, 0),
    "white": (0, 1),
    "pink": (3, 1),
}

def launch_paint():
    try:
        subprocess.Popen(["mspaint.exe"])  # resolves via PATH / system32
    except FileNotFoundError:
        # Fallback to shell if PATH resolution fails
        subprocess.Popen(["cmd", "/c", "start", "", "mspaint"])  # non-blocking
    time.sleep(3.5)

def _get_app_and_window():
    title_regex = ".*Paint.*"
    for _ in range(40):
        # Try process path
        try:
            app = Application(backend="uia").connect(path="mspaint.exe", timeout=1.0)
            win = app.top_window()
            if win and "Paint" in win.window_text():
                return app, win
            for w in app.windows():
                if "Paint" in w.window_text():
                    return app, w
        except Exception:
            pass
        # Try title regex
        try:
            app = Application(backend="uia").connect(title_re=title_regex, timeout=1.0)
            for w in app.windows():
                if "Paint" in w.window_text():
                    return app, w
        except Exception:
            pass
        # Desktop enumeration
        try:
            desk = Desktop(backend="uia")
            for w in desk.windows():
                text = w.window_text()
                if text and "Paint" in text:
                    try:
                        app = Application(backend="uia").connect(handle=w.handle)
                    except Exception:
                        app = None
                    return app, w
        except Exception:
            pass
        time.sleep(0.3)
    return None, None

def _canvas_rect(win):
    try:
        rect = win.rectangle()
        left = rect.left + 120
        top = rect.top + 160
        right = rect.right - 40
        bottom = rect.bottom - 80
        return (left, top, right, bottom)
    except Exception:
        scr = pag.size()
        return (80, 160, scr.width-80, scr.height-120)

def center_of(rect):
    l,t,r,b = rect
    return (int((l+r)/2), int((t+b)/2))

def _ensure_focus(win):
    try:
        win.set_focus()
        time.sleep(0.1)
    except Exception:
        pass

def _color_pos_from_name(win, color_name: str):
    try:
        rect = win.rectangle()
        base_x = rect.left + _PALETTE_OFFSET_X
        base_y = rect.top + _PALETTE_OFFSET_Y
        idx = _COLOR_TO_INDEX.get(color_name.lower())
        if idx is None:
            return None
        col, row = idx
        x = base_x + col * _PALETTE_CELL_W
        y = base_y + row * _PALETTE_CELL_H
        return (x, y)
    except Exception:
        return None

def click_palette_color(win, color_name: str):
    _ensure_focus(win)
    pos = _color_pos_from_name(win, color_name)
    if pos is None:
        pos = ABS_COLOR_CLICK_POS
    try:
        pag.moveTo(pos[0], pos[1], duration=0.15)
        pag.click()
        time.sleep(0.1)
        return True
    except Exception:
        # Fallback to absolute position as a last resort
        try:
            pag.moveTo(ABS_COLOR_CLICK_POS[0], ABS_COLOR_CLICK_POS[1], duration=0.15)
            pag.click()
            time.sleep(0.1)
            return True
        except Exception:
            return False

def write_text(win, text: str):
    _ensure_focus(win)
    # Select Text tool
    pag.moveTo(ABS_TEXT_TOOL_POS[0], ABS_TEXT_TOOL_POS[1], duration=0.15)
    pag.click()
    time.sleep(0.12)
    # After selecting the text tool, click the color again so it applies to text
    # We reuse the last selected color by clicking near the palette area; the
    # action layer ensures the desired color is chosen just before this call.
    try:
        pag.moveTo(ABS_COLOR_CLICK_POS[0], ABS_COLOR_CLICK_POS[1], duration=0.15)
        pag.click()
    except Exception:
        pass
    time.sleep(0.12)
    # Create a minimal text box to guarantee caret in some Paint versions
    cx, cy = center_of(_canvas_rect(win))
    pag.moveTo(cx, cy, duration=0.15)
    pag.mouseDown()
    pag.moveTo(cx + 10, cy + 8, duration=0.15)
    pag.mouseUp()
    time.sleep(0.12)
    # Click inside the tiny box to focus caret and type
    pag.click()
    time.sleep(0.06)
    try:
        pag.typewrite(text, interval=0.03)
    except Exception:
        # Fallback: slower typing
        for ch in str(text):
            pag.typewrite(ch)
            time.sleep(0.01)

def close_paint(win):
    try:
        rect = win.rectangle()
        r, t = rect.right, rect.top
        pag.moveTo(r-20, t+15, duration=0.2)
        pag.click()
        time.sleep(0.3)
    except Exception:
        pass
