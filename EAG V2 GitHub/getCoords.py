import pyautogui
import time

print("Click anywhere on the screen to get the coordinates...")

# Run this loop until a click is detected
while True:
    # Get the current mouse position
    x, y = pyautogui.position()

    # Check for mouse click (this checks for left-click)
    if pyautogui.mouseInfo() == "left":
        print(f"Mouse clicked at coordinates: ({x}, {y})")
        break

    time.sleep(0.1)  # Add a small delay to avoid excessive CPU usage
