import time
import ctypes
from ctypes import wintypes
import win32gui
import win32con
import win32process
import win32api
from typing import Tuple, Optional

# FlashWindowEx structures and flags
class FLASHWINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("hwnd", wintypes.HWND),
        ("dwFlags", wintypes.DWORD),
        ("uCount", wintypes.UINT),
        ("dwTimeout", wintypes.DWORD)
    ]

FLASHW_ALL = 3
FLASHW_TIMERNOFG = 12

def flash_window(hwnd: int) -> None:
    finfo = FLASHWINFO()
    finfo.cbSize = ctypes.sizeof(FLASHWINFO)
    finfo.hwnd = hwnd
    finfo.dwFlags = FLASHW_ALL | FLASHW_TIMERNOFG
    finfo.uCount = 5
    finfo.dwTimeout = 0
    ctypes.windll.user32.FlashWindowEx(ctypes.byref(finfo))

class WindowActivator:
    """Controls the Windows foreground and input focus activation pipeline."""
    
    def activate(self, hwnd: int) -> Tuple[bool, Optional[str]]:
        if not win32gui.IsWindow(hwnd):
            return False, "WINDOW_DESTROYED"

        # 1. Restore the window if iconic (minimized)
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.05)

        # 2. Show the window if hidden
        if not win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            time.sleep(0.05)

        # 3. Allow SetForegroundWindow on target thread
        try:
            ctypes.windll.user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass

        # 4. Bring Window to Top
        win32gui.BringWindowToTop(hwnd)

        success = False
        reason = None

        # 5. Try 3 attempts with thread input attachment
        for attempt in range(3):
            fore_hwnd = win32gui.GetForegroundWindow()
            if fore_hwnd == hwnd:
                success = True
                break

            # Try direct set first
            try:
                win32gui.SetForegroundWindow(hwnd)
                if win32gui.GetForegroundWindow() == hwnd:
                    success = True
                    break
            except Exception as e:
                reason = str(e)

            # Get target and current foreground thread IDs
            fore_thread_id, _ = win32process.GetWindowThreadProcessId(fore_hwnd)
            curr_thread_id = win32api.GetCurrentThreadId()
            target_thread_id, _ = win32process.GetWindowThreadProcessId(hwnd)

            attached_fore = False
            attached_target = False

            try:
                # Attach current thread to foreground window thread
                if fore_thread_id != curr_thread_id and fore_thread_id > 0:
                    win32process.AttachThreadInput(fore_thread_id, curr_thread_id, True)
                    attached_fore = True

                # Attach current thread to target window thread
                if target_thread_id != curr_thread_id and target_thread_id > 0:
                    win32process.AttachThreadInput(curr_thread_id, target_thread_id, True)
                    attached_target = True

                # Perform activation sequence
                win32gui.BringWindowToTop(hwnd)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                win32gui.SetActiveWindow(hwnd)
                win32gui.SetFocus(hwnd)
                
                if win32gui.GetForegroundWindow() == hwnd:
                    success = True
                    break
            except Exception as e:
                reason = str(e)
            finally:
                # Always detach threads cleanly
                if attached_fore:
                    try:
                        win32process.AttachThreadInput(fore_thread_id, curr_thread_id, False)
                    except Exception:
                        pass
                if attached_target:
                    try:
                        win32process.AttachThreadInput(curr_thread_id, target_thread_id, False)
                    except Exception:
                        pass

            # Flash window if OS blocks focus
            if not success:
                try:
                    flash_window(hwnd)
                except Exception:
                    pass
            time.sleep(0.05)

        # Final check
        if not success:
            if win32gui.GetForegroundWindow() == hwnd:
                success = True
            else:
                return False, "FOREGROUND_RESTRICTED"

        return True, None
