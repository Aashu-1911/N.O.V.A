from typing import Any, Dict, Optional, Union
import uiautomation as auto
import time

from automation.cache import AutomationCache
from automation.window_manager import WindowManager
from automation.logger import AutomationLogger
from automation.selectors import Selector
from automation.element import UIElement
from automation.types import ControlType
from automation.element_finder import ElementFinder
from automation.waits import Wait
from automation.keyboard import Keyboard
from automation.mouse import Mouse

class UIAutomationEngine:
    """The central orchestration engine exposing clean high-level APIs for Windows UI Automation."""
    
    def __init__(self) -> None:
        self.cache = AutomationCache()
        self.window_manager = WindowManager(self)
        self.logger = AutomationLogger()

    def find_window(
        self,
        title: str,
        class_name: Optional[str] = None,
        timeout_ms: int = 5000
    ) -> UIElement:
        """Find a system top-level window by title or class name."""
        cached_hwnd = self.cache.get_window(title)
        if cached_hwnd is not None:
            try:
                ctrl = auto.ControlFromHWND(cached_hwnd)
                if ctrl:
                    return UIElement(ctrl, self)
            except Exception:
                pass
        
        # Uncached search
        win = self.window_manager.find_window(title, class_name, timeout_ms)
        hwnd = win.control.NativeWindowHandle
        if hwnd:
            self.cache.cache_window(title, hwnd)
        return win

    def find_element(
        self,
        automation_id: Optional[str] = None,
        name: Optional[str] = None,
        partial_name: Optional[str] = None,
        regex_name: Optional[str] = None,
        class_name: Optional[str] = None,
        control_type: Optional[ControlType] = None,
        index: int = 0,
        visible: Optional[bool] = None,
        enabled: Optional[bool] = None,
        depth: int = 0xFFFFFFFF,
        search_scope: str = "descendants",
        timeout_ms: int = 5000
    ) -> UIElement:
        """Find a single UI element globally from the root system control."""
        sel = Selector(
            automation_id=automation_id,
            name=name,
            partial_name=partial_name,
            regex_name=regex_name,
            class_name=class_name,
            control_type=control_type,
            index=index,
            visible=visible,
            enabled=enabled,
            depth=depth,
            search_scope=search_scope
        )
        
        # Check cache
        cache_key = f"root_{str(sel.to_dict())}"
        cached = self.cache.get_element(cache_key)
        if cached:
            return UIElement(cached, self)

        root = auto.GetRootControl()
        ctrl = ElementFinder.find_element(root, sel, timeout_ms)
        self.cache.cache_element(cache_key, ctrl)
        return UIElement(ctrl, self)

    def click(
        self,
        target: Union[UIElement, Selector, dict],
        verify: bool = True,
        timeout_ms: int = 5000
    ) -> None:
        """Perform left mouse click on the resolved element target."""
        element = self._resolve_target(target, timeout_ms)
        element.click(verify, timeout_ms)

    def double_click(
        self,
        target: Union[UIElement, Selector, dict],
        verify: bool = True,
        timeout_ms: int = 5000
    ) -> None:
        """Perform double left mouse click on the resolved element target."""
        element = self._resolve_target(target, timeout_ms)
        element.double_click(verify, timeout_ms)

    def type_text(
        self,
        target: Union[UIElement, Selector, dict],
        text: str,
        verify: bool = True,
        timeout_ms: int = 5000
    ) -> None:
        """Focus the resolved target element and simulate text typing."""
        element = self._resolve_target(target, timeout_ms)
        element.type_text(text, verify, timeout_ms)

    def press_keys(self, keys: str) -> None:
        """Simulate physical hardware key combinations globally (e.g. '{Ctrl}s')."""
        Keyboard.send_shortcut(keys)

    def select(
        self,
        target: Union[UIElement, Selector, dict],
        item: str,
        verify: bool = True,
        timeout_ms: int = 5000
    ) -> None:
        """Select item option in a ComboBox or List element."""
        element = self._resolve_target(target, timeout_ms)
        element.select(item, verify, timeout_ms)

    def focus(self, target: Union[UIElement, Selector, dict]) -> None:
        """Set keyboard focus onto resolved element."""
        element = self._resolve_target(target)
        element.focus()

    def scroll(self, target: Union[UIElement, Selector, dict]) -> None:
        """Scroll element into visible view."""
        element = self._resolve_target(target)
        element.scroll_into_view()

    def wait(self, duration_ms: int) -> None:
        """Perform a simple sleep wait in milliseconds."""
        time.sleep(duration_ms / 1000.0)

    def _resolve_target(
        self,
        target: Union[UIElement, Selector, dict],
        timeout_ms: int = 5000
    ) -> UIElement:
        """Converts selectors or dictionary specifications into a resolved UIElement."""
        if isinstance(target, UIElement):
            return target
        elif isinstance(target, Selector):
            root = auto.GetRootControl()
            ctrl = ElementFinder.find_element(root, target, timeout_ms)
            return UIElement(ctrl, self)
        elif isinstance(target, dict):
            sel = Selector(**target)
            root = auto.GetRootControl()
            ctrl = ElementFinder.find_element(root, sel, timeout_ms)
            return UIElement(ctrl, self)
        raise ValueError("Unsupported target specification type.")
