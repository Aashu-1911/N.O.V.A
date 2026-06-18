import subprocess
from rapidfuzz import process
import json

START_MENU_APPS = {}

import subprocess
import json

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

# find exat match
def find_app(app_name):
    app_name = app_name.lower().strip()

    if app_name in START_MENU_APPS:
        return START_MENU_APPS[app_name]

    return None

# find partial match
def find_app(app_name):
    app_name = app_name.lower().strip()

    if app_name in START_MENU_APPS:
        return START_MENU_APPS[app_name]

    return None

#find fuzzy search
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




# def open_start_menu_app(app_name: str) -> bool:
#     """
#     Search Windows Start Menu apps and launch the first matching app.
#     """

#     try:
#         result = subprocess.run(
#             [
#                 "powershell",
#                 "-Command",
#                 (
#                     f"Get-StartApps | "
#                     f"Where-Object {{$_.Name -like '*{app_name}*'}} | "
#                     f"Select-Object -First 1 -ExpandProperty AppID"
#                 )
#             ],
#             capture_output=True,
#             text=True
#         )

#         app_id = result.stdout.strip()

#         if not app_id:
#             print(f"[START MENU] No match found for: {app_name}")
#             return False

#         print(f"[START MENU] Found AppID: {app_id}")
#         print(f"[START MENU] Launching: shell:AppsFolder\\{app_id}")
#         subprocess.Popen(
#             f'explorer.exe "shell:AppsFolder\\{app_id}"',
#             shell=True
#         )

#         return True

#     except Exception as e:
#         print("[START MENU ERROR]", e)
#         return False


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
        # Fast path: executable exists in PATH
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

        # Cached Start Menu lookup
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