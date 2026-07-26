from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import uiautomation as auto
import time

from automation.types import ControlType
from automation.selectors import Selector
from automation.exceptions import (
    ElementDisabledError,
    ElementInvisibleError,
    VerificationError
)
from automation.keyboard import Keyboard
from automation.mouse import Mouse
from automation.clipboard import Clipboard
from automation.verifier import Verifier

class UIElement:
    """A Playwright-like semantic wrapper around Microsoft UI Automation controls."""
    
    def __init__(self, control: Any, engine: Any) -> None:
        self.control = control
        self.engine = engine

    @property
    def name(self) -> str:
        """Returns the control name (label/text title)."""
        return self.control.Name or ""

    @property
    def automation_id(self) -> str:
        """Returns the Control Automation ID."""
        return self.control.AutomationId or ""

    @property
    def control_type(self) -> str:
        """Returns string representation of Control Type."""
        return self.control.ControlTypeName or ""

    @property
    def class_name(self) -> str:
        """Returns UI element class name."""
        return self.control.ClassName or ""

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Returns bounding rectangle coordinates (left, top, right, bottom)."""
        rect = self.control.BoundingRectangle
        return (rect.left, rect.top, rect.right, rect.bottom)

    @property
    def center(self) -> Tuple[int, int]:
        """Returns center coordinates (x, y) of element bounds."""
        rect = self.control.BoundingRectangle
        return (rect.centerX(), rect.centerY())

    @property
    def is_visible(self) -> bool:
        """Checks if the control is currently visible (not offscreen, bounds > 0)."""
        try:
            return not self.control.IsOffscreen and self.control.BoundingRectangle.width() > 0
        except Exception:
            return False

    @property
    def is_enabled(self) -> bool:
        """Checks if the control is enabled."""
        try:
            return bool(self.control.IsEnabled)
        except Exception:
            return False

    @property
    def has_focus(self) -> bool:
        """Checks if the control has keyboard input focus."""
        try:
            return bool(self.control.HasKeyboardFocus)
        except Exception:
            return False

    @property
    def text_value(self) -> str:
        """Returns value pattern value, legacy accessibility value, or control Name."""
        try:
            val_pat = self.control.GetValuePattern()
            if val_pat:
                return val_pat.Value or ""
        except Exception:
            pass
        try:
            leg_pat = self.control.GetLegacyIAccessiblePattern()
            if leg_pat:
                return leg_pat.Value or ""
        except Exception:
            pass
        return self.control.Name or ""

    @property
    def selected_item(self) -> str:
        """Returns name of the currently selected item in a List or ComboBox."""
        try:
            sel_pat = self.control.GetSelectionPattern()
            if sel_pat:
                items = sel_pat.GetSelection()
                if items:
                    return items[0].Name or ""
        except Exception:
            pass
        return self.text_value

    def _ensure_interactable(self) -> None:
        """Raises exception if element is not visible or enabled."""
        if not self.is_visible:
            raise ElementInvisibleError("interact", self.name, "Element is offscreen or invisible.")
        if not self.is_enabled:
            raise ElementDisabledError("interact", self.name, "Element is disabled.")

    # Element Actions
    def click(self, verify: bool = True, timeout_ms: int = 5000) -> None:
        """Perform a left click on the center of the control."""
        self._ensure_interactable()
        x, y = self.center
        t0 = time.time()
        Mouse.click(x, y)
        if verify:
            Verifier.verify_click(self, timeout_ms)
        self.engine.logger.info("click", self.name, (time.time() - t0) * 1000)

    def double_click(self, verify: bool = True, timeout_ms: int = 5000) -> None:
        """Perform a double click on the center of the control."""
        self._ensure_interactable()
        x, y = self.center
        t0 = time.time()
        Mouse.double_click(x, y)
        if verify:
            Verifier.verify_click(self, timeout_ms)
        self.engine.logger.info("double_click", self.name, (time.time() - t0) * 1000)

    def right_click(self, verify: bool = True, timeout_ms: int = 5000) -> None:
        """Perform a right click on the center of the control."""
        self._ensure_interactable()
        x, y = self.center
        t0 = time.time()
        Mouse.right_click(x, y)
        if verify:
            Verifier.verify_click(self, timeout_ms)
        self.engine.logger.info("right_click", self.name, (time.time() - t0) * 1000)

    def hover(self) -> None:
        """Move mouse cursor to the center of the control."""
        self._ensure_interactable()
        x, y = self.center
        t0 = time.time()
        Mouse.hover(x, y)
        self.engine.logger.info("hover", self.name, (time.time() - t0) * 1000)

    def focus(self) -> None:
        """Set keyboard focus to the control."""
        self._ensure_interactable()
        t0 = time.time()
        self.control.SetFocus()
        self.engine.logger.info("focus", self.name, (time.time() - t0) * 1000)

    def invoke(self) -> None:
        """Perform native UIA Invoke action pattern (bypasses mouse movement)."""
        self._ensure_interactable()
        t0 = time.time()
        try:
            pat = self.control.GetInvokePattern()
            pat.Invoke()
        except Exception:
            # Fallback to click
            self.click(verify=False)
        self.engine.logger.info("invoke", self.name, (time.time() - t0) * 1000)

    def type_text(self, text: str, verify: bool = True, timeout_ms: int = 5000) -> None:
        """Types the given text into an editable element, using ValuePattern where possible."""
        self._ensure_interactable()
        t0 = time.time()
        try:
            # Programmatic value write (very fast and robust)
            val_pat = self.control.GetValuePattern()
            val_pat.SetValue(text)
        except Exception:
            # Fallback to physical keystroke typing
            self.click(verify=False)
            self.clear_text(verify=False)
            Keyboard.type_text(text)
            
        if verify:
            Verifier.verify_typing(self, text, timeout_ms)
        self.engine.logger.info("type_text", self.name, (time.time() - t0) * 1000)

    def clear_text(self, verify: bool = True) -> None:
        """Clear all text in an editable element."""
        self._ensure_interactable()
        t0 = time.time()
        try:
            val_pat = self.control.GetValuePattern()
            val_pat.SetValue("")
        except Exception:
            self.focus()
            Keyboard.send_shortcut("{Ctrl}a")
            Keyboard.type_text("{Delete}")
            
        if verify:
            Verifier.verify_typing(self, "", 2000)
        self.engine.logger.info("clear_text", self.name, (time.time() - t0) * 1000)

    def append_text(self, text: str, verify: bool = True) -> None:
        """Append text to the end of the current text value."""
        new_val = self.text_value + text
        self.type_text(new_val, verify=verify)

    def press_enter(self) -> None:
        """Press enter key on the control."""
        self.focus()
        Keyboard.press_enter()

    def press_escape(self) -> None:
        """Press escape key on the control."""
        self.focus()
        Keyboard.press_escape()

    def press_tab(self) -> None:
        """Press tab key on the control."""
        self.focus()
        Keyboard.press_tab()

    def select(self, item_name: str, verify: bool = True, timeout_ms: int = 5000) -> None:
        """Select item name in a ComboBox or List element."""
        self._ensure_interactable()
        t0 = time.time()
        try:
            # Check if SelectionItemPattern is supported directly on matching child
            # Expand container first
            try:
                self.control.GetExpandCollapsePattern().Expand()
            except Exception:
                pass
                
            # Iterate children to find item matching name
            found = False
            for child in self.control.GetChildren():
                if child.Name == item_name:
                    child.GetSelectionItemPattern().Select()
                    found = True
                    break
            if found:
                if verify:
                    Verifier.verify_selection(self, item_name, timeout_ms)
                self.engine.logger.info("select", self.name, (time.time() - t0) * 1000)
                return
        except Exception:
            pass

        # Fallback to mouse click/expansion selection
        self.click(verify=False)
        time.sleep(0.2)
        # Search dropdown ListItem children
        from automation.element_finder import ElementFinder
        item_sel = Selector(name=item_name, control_type=ControlType.LISTITEM)
        item_ctrl = ElementFinder.find_element(self.control, item_sel, timeout_ms=3000)
        auto.Click(item_ctrl.BoundingRectangle.centerX(), item_ctrl.BoundingRectangle.centerY())
        
        if verify:
            Verifier.verify_selection(self, item_name, timeout_ms)
        self.engine.logger.info("select", self.name, (time.time() - t0) * 1000)

    def expand(self) -> None:
        """Expand control supporting ExpandCollapsePattern (e.g. TreeItem, ComboBox)."""
        t0 = time.time()
        self.control.GetExpandCollapsePattern().Expand()
        self.engine.logger.info("expand", self.name, (time.time() - t0) * 1000)

    def collapse(self) -> None:
        """Collapse control supporting ExpandCollapsePattern."""
        t0 = time.time()
        self.control.GetExpandCollapsePattern().Collapse()
        self.engine.logger.info("collapse", self.name, (time.time() - t0) * 1000)

    def check(self, verify: bool = True) -> None:
        """Set checkbox state to checked."""
        t0 = time.time()
        try:
            pat = self.control.GetTogglePattern()
            if pat.ToggleState != auto.ToggleState.On:
                pat.Toggle()
        except Exception:
            self.click(verify=False)
            
        self.engine.logger.info("check", self.name, (time.time() - t0) * 1000)

    def uncheck(self, verify: bool = True) -> None:
        """Set checkbox state to unchecked."""
        t0 = time.time()
        try:
            pat = self.control.GetTogglePattern()
            if pat.ToggleState != auto.ToggleState.Off:
                pat.Toggle()
        except Exception:
            self.click(verify=False)
            
        self.engine.logger.info("uncheck", self.name, (time.time() - t0) * 1000)

    def toggle(self, verify: bool = True) -> None:
        """Toggle element check/active state."""
        t0 = time.time()
        try:
            pat = self.control.GetTogglePattern()
            pat.Toggle()
        except Exception:
            self.click(verify=False)
            
        self.engine.logger.info("toggle", self.name, (time.time() - t0) * 1000)

    def scroll_into_view(self) -> None:
        """Scroll element into visible view rectangle."""
        t0 = time.time()
        try:
            self.control.GetScrollItemPattern().ScrollIntoView()
        except Exception:
            pass
        self.engine.logger.info("scroll_into_view", self.name, (time.time() - t0) * 1000)

    def copy(self) -> None:
        """Copy active focus/selection to Windows clipboard."""
        self.focus()
        Keyboard.send_shortcut("{Ctrl}c")

    def paste(self) -> None:
        """Paste active clipboard contents into control."""
        self.focus()
        Keyboard.send_shortcut("{Ctrl}v")

    def shortcut_keys(self, keys: str) -> None:
        """Execute key sequence shortcut combination (e.g. '{Ctrl}s')."""
        self.focus()
        Keyboard.send_shortcut(keys)

    # Sub-Element Searching
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
        """Search for a single child/descendant UI element matching criteria."""
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
        cache_key = f"{id(self.control)}_{str(sel.to_dict())}"
        cached = self.engine.cache.get_element(cache_key)
        if cached:
            return UIElement(cached, self.engine)

        # Walk/Find element
        from automation.element_finder import ElementFinder
        ctrl = ElementFinder.find_element(self.control, sel, timeout_ms)
        self.engine.cache.cache_element(cache_key, ctrl)
        self.engine.cache.cache_parent(cache_key, self.control)
        
        return UIElement(ctrl, self.engine)
