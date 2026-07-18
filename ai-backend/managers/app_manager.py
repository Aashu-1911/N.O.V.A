import json
import subprocess

from rapidfuzz import process
import psutil

START_MENU_APPS = {}

KNOWN_APPS = {
	"vs code": "code",
	"vscode": "code",
	"visual studio code": "code",
	"microsoft store": "microsoft store",
	"chrome": "chrome",
	"google chrome": "chrome",
	"notepad": "notepad",
	"calculator": "calc",
	"calc": "calc",
	"cmd": "cmd",
	"command prompt": "cmd",
	"powershell": "powershell",
	"discord": "discord",
	"spotify": "spotify",
}


def find_app(app_name):
	app_name = app_name.lower().strip()

	if app_name in START_MENU_APPS:
		return START_MENU_APPS[app_name]

	match = process.extractOne(
		app_name,
		START_MENU_APPS.keys()
	)

	if match and match[1] >= 80:
		print(f"[APP] Fuzzy matched {app_name} -> {match[0]}")
		return START_MENU_APPS[match[0]]

	return None


def load_start_menu_apps():
	global START_MENU_APPS

	command = """
	Get-StartApps |
	Select-Object Name, AppID |
	ConvertTo-Json
	"""

	result = subprocess.run(
		["powershell", "-Command", command],
		capture_output=True,
		text=True
	)

	try:
		apps = json.loads(result.stdout)

		if isinstance(apps, dict):
			apps = [apps]

		START_MENU_APPS = {
			app["Name"].lower(): app["AppID"]
			for app in apps
		}

		print(f"[APP] Loaded {len(START_MENU_APPS)} apps")

	except Exception as e:
		print("[APP CACHE ERROR]", e)


def open_application(app_name: str) -> bool:
	"""
	Launch application using:
	1. Known aliases
	2. PATH executable lookup
	3. Cached Start Menu search (exact/partial/fuzzy)
	"""

	if not app_name:
		return False

	app_name = app_name.lower().strip()

	command = KNOWN_APPS.get(app_name, app_name)

	print(f"[APP] Requested: {app_name}")
	print(f"[APP] Command: {command}")

	try:
		result = subprocess.run(
			f'where "{command}"',
			shell=True,
			capture_output=True,
			text=True
		)

		if result.returncode == 0:
			print("[APP] Found executable in PATH")

			subprocess.Popen(
				command,
				shell=True
			)

			return True

		print("[APP] Not found in PATH")

		app_id = find_app(app_name)

		if app_id:
			print(f"[APP] Found AppID: {app_id}")

			subprocess.Popen(
				f'explorer.exe "shell:AppsFolder\\{app_id}"',
				shell=True
			)

			return True

		print(f"[APP] Could not locate application: {app_name}")
		return False

	except Exception as e:
		print("[APP ERROR]", e)
		return False


def close_application(app_name: str) -> bool:
	app_name = app_name.lower().strip()

	# Broad mapping from aliases/names to process executables
	PROCESS_MAP = {
		"chrome": ["chrome.exe"],
		"google chrome": ["chrome.exe"],
		"browser": ["chrome.exe", "msedge.exe", "firefox.exe"],
		"telegram": ["telegram.exe"],
		"telegram desktop": ["telegram.exe"],
		"spotify": ["spotify.exe"],
		"discord": ["discord.exe"],
		"notepad": ["notepad.exe"],
		"vs code": ["code.exe"],
		"vscode": ["code.exe"],
		"visual studio code": ["code.exe"],
		"code": ["code.exe"],
		"calculator": ["calculator.exe", "calc.exe"],
		"calc": ["calculator.exe", "calc.exe"],
	}

	target_exes = PROCESS_MAP.get(app_name, [])
	if not target_exes:
		target_exes = [f"{app_name}.exe", app_name]

	target_exes_lower = [exe.lower() for exe in target_exes]

	import os
	ignored_pids = {os.getpid()}
	try:
		ignored_pids.add(os.getppid())
	except Exception:
		pass

	closed_any = False
	for proc in psutil.process_iter(["pid", "name"]):
		try:
			pid = proc.info["pid"]
			if pid in ignored_pids:
				continue

			name = proc.info["name"]
			if not name:
				continue
			name_lower = name.lower()
			
			matched = False
			for target in target_exes_lower:
				if name_lower == target or name_lower.replace(".exe", "") == target:
					matched = True
					break

			if matched:
				proc.terminate()
				closed_any = True
		except Exception:
			pass

	return closed_any