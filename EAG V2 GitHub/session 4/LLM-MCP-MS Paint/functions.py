# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics
import win32clipboard as clipboard
import win32con as wcon
from collections import namedtuple

# instantiate an MCP server client
mcp = FastMCP("PaintMCP")

# Global handle for Paint application instance
paint_app = None
last_rectangle = None  # (x1, y1, x2, y2) normalized to top-left -> bottom-right

# Fixed coordinates for 14" laptop (provided by user)
TOOL_RECT_COORDS = (795, 125)
TOOL_TEXT_COORDS = (515, 130)
CANVAS_TOP_LEFT = (355, 325)
CANVAS_BOTTOM_RIGHT = (1555, 880)
CanvasRect = namedtuple('CanvasRect', 'left top right bottom')

def resolve_canvas(paint_window):
    """Return (canvas_element, canvas_rect). Falls back to user-provided absolute coords."""
    try:
        canvas = paint_window.child_window(title_re=".*Canvas.*", control_type="Pane")
        if canvas.exists(timeout=1.0):
            try:
                rect = canvas.rectangle()
                return canvas, rect
            except Exception:
                pass
    except Exception:
        pass
    try:
        canvas = paint_window.child_window(class_name='MSPaintView')
        # Even if this exists, prefer fixed rect for reliability
    except Exception:
        canvas = paint_window
    rect = CanvasRect(
        left=CANVAS_TOP_LEFT[0],
        top=CANVAS_TOP_LEFT[1],
        right=CANVAS_BOTTOM_RIGHT[0],
        bottom=CANVAS_BOTTOM_RIGHT[1],
    )
    return canvas, rect

def set_clipboard_text(text: str) -> None:
    """Place plain text onto the Windows clipboard."""
    clipboard.OpenClipboard()
    try:
        clipboard.EmptyClipboard()
        clipboard.SetClipboardData(wcon.CF_UNICODETEXT, text)
    finally:
        clipboard.CloseClipboard()

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    global paint_app, last_rectangle
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        try:
            paint_window = paint_app.window(title_re=".*Paint")
        except Exception:
            paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.2)
        
        # Select Rectangle tool via fixed coords (user-provided); then UIA; then approximate
        try:
            paint_window.click_input(coords=TOOL_RECT_COORDS)
        except Exception:
            pass
        # Select Rectangle tool via UIA when available; fallback to approximate region
        try:
            rect_btn = paint_window.child_window(title_re=".*Rectangle.*", control_type="Button")
            if rect_btn.exists(timeout=1.0):
                rect_btn.click_input()
            else:
                raise RuntimeError("Rectangle button not found")
        except Exception:
            try:
                win_rect = paint_window.rectangle()
                # Try a few likely toolbar locations (smaller 14" screens often pack toolbar tighter)
                candidates = [
                    (int(win_rect.left + 0.24 * (win_rect.right - win_rect.left)), int(win_rect.top + 0.10 * (win_rect.bottom - win_rect.top))),
                    (int(win_rect.left + 0.28 * (win_rect.right - win_rect.left)), int(win_rect.top + 0.12 * (win_rect.bottom - win_rect.top))),
                    (int(win_rect.left + 0.32 * (win_rect.right - win_rect.left)), int(win_rect.top + 0.14 * (win_rect.bottom - win_rect.top))),
                ]
                clicked = False
                for cx, cy in candidates:
                    try:
                        paint_window.click_input(coords=(cx, cy))
                        clicked = True
                        break
                    except Exception:
                        continue
                if not clicked:
                    raise RuntimeError("Failed to click Rectangle tool")
            except Exception:
                pass
        time.sleep(0.2)
        
        # Get the canvas area and rect (prefer fixed rect for reliability)
        canvas, c_rect = resolve_canvas(paint_window)
        
        # Normalize coordinates to top-left and bottom-right
        tlx, tly = min(x1, x2), min(y1, y2)
        brx, bry = max(x1, x2), max(y1, y2)

        # Convert canvas-relative to absolute screen coordinates and clamp within canvas
        start_x, start_y = c_rect.left + tlx, c_rect.top + tly
        end_x, end_y = c_rect.left + brx, c_rect.top + bry
        start_x = max(c_rect.left + 2, min(start_x, c_rect.right - 2))
        start_y = max(c_rect.top + 2, min(start_y, c_rect.bottom - 2))
        end_x = max(c_rect.left + 2, min(end_x, c_rect.right - 2))
        end_y = max(c_rect.top + 2, min(end_y, c_rect.bottom - 2))

        # Ensure canvas has focus then perform drag using the main window
        try:
            paint_window.click_input(coords=(start_x, start_y))
            time.sleep(0.05)
        except Exception:
            pass
        paint_window.press_mouse_input(coords=(start_x, start_y))
        time.sleep(0.05)
        paint_window.move_mouse_input(coords=(end_x, end_y))
        time.sleep(0.05)
        paint_window.release_mouse_input(coords=(end_x, end_y))

        # Remember last rectangle
        last_rectangle = (tlx, tly, brx, bry)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({tlx},{tly}) to ({brx},{bry})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        try:
            paint_window = paint_app.window(title_re=".*Paint")
        except Exception:
            paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # Ensure Home tab is active, then select Text tool via UIA or keyboard accelerator
        try:
            paint_window.type_keys('%h')  # Alt+H for Home tab
            time.sleep(0.2)
        except Exception:
            pass
        try:
            text_btn = paint_window.child_window(title_re="^Text$|.*Text.*", control_type="Button")
            if text_btn.exists(timeout=1.0):
                text_btn.click_input()
            else:
                raise RuntimeError("Text button not found")
        except Exception:
            try:
                paint_window.type_keys('t')  # Accelerator for Text tool on Home tab
            except Exception:
                pass
        time.sleep(0.5)
        
        # Get the canvas area and rect (prefer fixed rect)
        canvas, c_rect = resolve_canvas(paint_window)
        
        # Click on canvas to place text box using canvas-relative converted to screen coords
        inset_x, inset_y = 150, 120
        canvas_click_x = max(c_rect.left + 4, min(c_rect.right - 4, c_rect.left + inset_x))
        canvas_click_y = max(c_rect.top + 4, min(c_rect.bottom - 4, c_rect.top + inset_y))
        paint_window.click_input(coords=(canvas_click_x, canvas_click_y))
        time.sleep(0.5)
        
        
        # Paste the text passed from client via clipboard to avoid hotkey interpretation
        set_clipboard_text(text)
        time.sleep(0.05)
        paint_window.type_keys('^v')
    
        time.sleep(0.5)
        
        # Click to exit text mode near canvas bottom-right
        exit_x = c_rect.right - 8
        exit_y = c_rect.bottom - 8
        paint_window.click_input(coords=(exit_x, exit_y))
    
      
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def get_last_rectangle_center() -> dict:
    """Get the center coordinates (x,y) of the last drawn rectangle"""
    global last_rectangle
    try:
        if not last_rectangle:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="No rectangle found. Draw a rectangle first."
                    )
                ]
            }

        x1, y1, x2, y2 = last_rectangle
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        return {
            "content": [
                TextContent(type="text", text=f"{cx},{cy}")
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(type="text", text=f"Error: {str(e)}")
            ]
        }

@mcp.tool()
async def add_text_in_paint_at(text: str, x: int, y: int) -> dict:
    """Add text in Paint at provided canvas coordinates (x,y)"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }

        paint_window = paint_app.window(class_name='MSPaintApp')

        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.3)

        # Select Text tool
        paint_window.click_input(coords=(290, 70))
        time.sleep(0.3)

        canvas = paint_window.child_window(class_name='MSPaintView')
        canvas.click_input(coords=(x, y))
        time.sleep(0.3)

        # Paste the text to avoid hotkey propagation
        set_clipboard_text(text)
        time.sleep(0.05)
        paint_window.type_keys('^v')
        time.sleep(0.3)

        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added at ({x},{y})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(type="text", text=f"Error: {str(e)}")
            ]
        }

@mcp.tool()
async def add_text_inside_last_rectangle(text: str) -> dict:
    """Create a text box constrained within the last drawn rectangle and type text"""
    global paint_app, last_rectangle
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        if not last_rectangle:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="No rectangle found. Draw a rectangle first."
                    )
                ]
            }

        x1, y1, x2, y2 = last_rectangle
        # Apply small margins to ensure the text box stays inside the border
        margin = 10
        left = x1 + margin
        top = y1 + margin
        right = max(left + 40, x2 - margin)
        bottom = max(top + 20, y2 - margin)

        try:
            paint_window = paint_app.window(title_re=".*Paint")
        except Exception:
            paint_window = paint_app.window(class_name='MSPaintApp')
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.3)

        # Ensure Home tab is active, then select Text tool via UIA or keyboard accelerator
        try:
            paint_window.type_keys('%h')  # Alt+H for Home tab
            time.sleep(0.2)
        except Exception:
            pass
        try:
            text_btn = paint_window.child_window(title_re="^Text$|.*Text.*", control_type="Button")
            if text_btn.exists(timeout=1.0):
                text_btn.click_input()
            else:
                raise RuntimeError("Text button not found")
        except Exception:
            try:
                paint_window.type_keys('t')
            except Exception:
                pass
        time.sleep(0.3)

        canvas, c_rect = resolve_canvas(paint_window)
        # Convert to absolute screen coords and drag to create text box
        abs_left, abs_top = c_rect.left + left, c_rect.top + top
        abs_right, abs_bottom = c_rect.left + right, c_rect.top + bottom
        abs_left = max(c_rect.left + 4, min(abs_left, c_rect.right - 8))
        abs_top = max(c_rect.top + 4, min(abs_top, c_rect.bottom - 8))
        abs_right = max(abs_left + 10, min(abs_right, c_rect.right - 4))
        abs_bottom = max(abs_top + 10, min(abs_bottom, c_rect.bottom - 4))
        paint_window.click_input(coords=(abs_left, abs_top))
        time.sleep(0.05)
        paint_window.press_mouse_input(coords=(abs_left, abs_top))
        time.sleep(0.05)
        paint_window.move_mouse_input(coords=(abs_right, abs_bottom))
        time.sleep(0.05)
        paint_window.release_mouse_input(coords=(abs_right, abs_bottom))
        time.sleep(0.25)

        # Click inside the created text region to ensure caret focus
        center_x = (abs_left + abs_right) // 2
        center_y = (abs_top + abs_bottom) // 2
        paint_window.click_input(coords=(center_x, center_y))
        time.sleep(0.15)
        paint_window.click_input(coords=(center_x + 5, center_y + 3))
        time.sleep(0.15)

        # Paste the text via clipboard to avoid hotkey interpretation
        set_clipboard_text(text)
        time.sleep(0.1)
        paint_window.type_keys('^v')
        time.sleep(0.3)

        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text inserted inside rectangle ({x1},{y1})-({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(type="text", text=f"Error: {str(e)}")
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on secondary monitor"""
    global paint_app
    try:
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.2)
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        # Bring to foreground explicitly
        try:
            win32gui.SetForegroundWindow(paint_window.handle)
        except Exception:
            pass
        time.sleep(0.2)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully and maximized"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }
# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING THE SERVER AT AMAZING LOCATION")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution