import win32gui
import win32con
import uiautomation as auto
import time
from typing import Any, List, Optional, Tuple

from automation.element import UIElement
from automation.selectors import Selector
from automation.element_finder import ElementFinder
from automation.exceptions import WindowNotFoundError, ElementNotFoundError
from automation.types import WindowState

class WindowManager:
    """Handles OS-level window finding, listing, state control, and positioning."""
    
    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def find_window(
        self,
        title: str,
        class_name: Optional[str] = None,
        timeout_ms: int = 5000
    ) -> UIElement:
        """Find a top-level window matching title (exact or partial) and optional class name."""
        # 1. Attempt using UIA root children search
        root = auto.GetRootControl()
        sel = Selector(
            partial_name=title,
            class_name=class_name,
            control_type=auto.ControlType.WindowControl,
            search_scope="children"
        )
        try:
            ctrl = ElementFinder.find_element(root, sel, timeout_ms)
            return UIElement(ctrl, self.engine)
        except ElementNotFoundError as e:
            # Fallback to win32 window search
            hwnd = win32gui.FindWindow(class_name, title)
            if not hwnd:
                # Fuzzy partial window title scan using win32
                def enum_cb(h, hwnds):
                    if win32gui.IsWindowVisible(h):
                        txt = win32gui.GetWindowText(h)
                        if title.lower() in txt.lower():
                            hwnds.append(h)
                    return True
                matched_hwnds = []
                win32gui.EnumWindows(enum_cb, matched_hwnds)
                if matched_hwnds:
                    hwnd = matched_hwnds[0]

            if hwnd:
                try:
                    ctrl = auto.ControlFromHWND(hwnd)
                    if ctrl:
                        return UIElement(ctrl, self.engine)
                except Exception:
                    pass
            
            raise WindowNotFoundError(
                action="find_window",
                target=title,
                reason=f"Window was not found or visible after {timeout_ms}ms.",
                suggestions="Verify target application is running and exposes a standard window title."
            ) from e

    def list_windows(self) -> List[UIElement]:
        """List all visible top-level windows currently running on the system."""
        root = auto.GetRootControl()
        windows = []
        try:
            for child in root.GetChildren():
                if child.ControlType == auto.ControlType.WindowControl and not child.IsOffscreen:
                    windows.append(UIElement(child, self.engine))
        except Exception:
            pass
        return windows

    def get_active_window(self) -> UIElement:
        """Get the currently focused foreground window on the system."""
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            try:
                ctrl = auto.ControlFromHWND(hwnd)
                if ctrl:
                    return UIElement(ctrl, self.engine)
            except Exception:
                pass
        
        # Fallback to UIA active element focus
        root = auto.GetRootControl()
        for child in root.GetChildren():
            if child.ControlType == auto.ControlType.WindowControl and child.HasKeyboardFocus:
                return UIElement(child, self.engine)
                
        raise ElementNotFoundError(
            action="get_active_window",
            target="foreground",
            reason="Unable to determine active system window."
        )

    # Window Specific State Modifiers
    def activate(self, element: UIElement) -> None:
        """Activate the window and restore it if minimized."""
        hwnd = element.control.NativeWindowHandle
        if hwnd:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
        else:
            element.control.SetActive()
        time.sleep(0.1)

    def restore(self, element: UIElement) -> None:
        """Restore window to normal state from maximized or minimized."""
        try:
            pat = element.control.GetWindowPattern()
            pat.SetWindowVisualState(auto.WindowVisualState.Normal)
        except Exception:
            hwnd = element.control.NativeWindowHandle
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    def minimize(self, element: UIElement) -> None:
        """Minimize the window."""
        try:
            pat = element.control.GetWindowPattern()
            pat.SetWindowVisualState(auto.WindowVisualState.Minimized)
        except Exception:
            hwnd = element.control.NativeWindowHandle
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

    def maximize(self, element: UIElement) -> None:
        """Maximize the window."""
        try:
            pat = element.control.GetWindowPattern()
            pat.SetWindowVisualState(auto.WindowVisualState.Maximized)
        except Exception:
            hwnd = element.control.NativeWindowHandle
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

    def close(self, element: UIElement) -> None:
        """Close the window element."""
        try:
            pat = element.control.GetWindowPattern()
            pat.Close()
        except Exception:
            hwnd = element.control.NativeWindowHandle
            if hwnd:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

    def focus(self, element: UIElement) -> None:
        """Set focus to window."""
        element.focus()

    def bring_to_front(self, element: UIElement) -> None:
        """Bring window foreground to front."""
        self.activate(element)

    def get_child_windows(self, element: UIElement) -> List[UIElement]:
        """List all child windows of the given window."""
        children = []
        try:
            for child in element.control.GetChildren():
                if child.ControlType == auto.ControlType.WindowControl:
                    children.append(UIElement(child, self.engine))
        except Exception:
            pass
        return children

    def get_window_state(self, element: UIElement) -> WindowState:
        """Get window visual state (Normal, Minimized, Maximized)."""
        try:
            pat = element.control.GetWindowPattern()
            state = pat.WindowVisualState
            if state == auto.WindowVisualState.Maximized:
                return WindowState.MAXIMIZED
            elif state == auto.WindowVisualState.Minimized:
                return WindowState.MINIMIZED
            return WindowState.NORMAL
        except Exception:
            hwnd = element.control.NativeWindowHandle
            if hwnd:
                if win32gui.IsIconic(hwnd):
                    return WindowState.MINIMIZED
                if win32gui.IsZoomed(hwnd):
                    return WindowState.MAXIMIZED
            return WindowState.NORMAL
