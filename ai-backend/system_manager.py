from PIL import ImageGrab
from datetime import datetime
from pathlib import Path
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import ctypes
import pythoncom



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


#volume control function
def _get_volume():
    pythoncom.CoInitialize()

    speakers = AudioUtilities.GetSpeakers()

    return speakers.EndpointVolume


def mute_volume():
    volume = _get_volume()
    volume.SetMute(1, None)
    
def unmute_volume():
    volume = _get_volume()
    volume.SetMute(0, None)
    
def volume_up():
    volume = _get_volume()

    current = volume.GetMasterVolumeLevelScalar()

    volume.SetMasterVolumeLevelScalar(
        min(1.0, current + 0.1),
        None
    )
    
def volume_down():
    volume = _get_volume()

    current = volume.GetMasterVolumeLevelScalar()

    volume.SetMasterVolumeLevelScalar(
        max(0.0, current - 0.1),
        None
    )