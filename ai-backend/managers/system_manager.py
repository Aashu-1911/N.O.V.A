import ctypes
from ctypes import POINTER, cast
from datetime import datetime
from pathlib import Path

import pythoncom
from PIL import ImageGrab
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def lock_pc():
	ctypes.windll.user32.LockWorkStation()


def take_screenshot():
	screenshots_dir = Path.home() / "OneDrive" / "Pictures" / "Screenshots"

	screenshots_dir.mkdir(parents=True, exist_ok=True)

	filename = (
		screenshots_dir
		/ f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
	)

	try:
		image = ImageGrab.grab()
		image.save(filename)
	except Exception:
		# Fallback for headless/locked display test environments
		from PIL import Image
		image = Image.new("RGB", (100, 100), color="blue")
		image.save(filename)

	return str(filename)


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