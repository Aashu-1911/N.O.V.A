from PIL import ImageGrab
from datetime import datetime
from pathlib import Path
import ctypes


def lock_pc():
    ctypes.windll.user32.LockWorkStation()


def take_screenshot():
    screenshots_dir = Path.home() / "OneDrive" / "Pictures" / "Screenshots"

    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    filename = (
        screenshots_dir
        / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )

    image = ImageGrab.grab()
    image.save(filename)

    return str(filename)