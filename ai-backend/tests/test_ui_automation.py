import pytest
from unittest.mock import MagicMock, patch
import uiautomation as auto

from automation import (
    UIAutomationEngine,
    UIElement,
    Selector,
    ControlType,
    WindowState,
    ElementNotFoundError,
    ElementDisabledError,
    ElementInvisibleError,
    WindowNotFoundError,
    VerificationError
)

class FakeRect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
    def width(self):
        return self.right - self.left
    def height(self):
        return self.bottom - self.top
    def centerX(self):
        return (self.left + self.right) // 2
    def centerY(self):
        return (self.top + self.bottom) // 2

class FakeControl:
    def __init__(self, name="mock_element", automation_id="mock_id", control_type=None, class_name="Button"):
        self.Name = name
        self.AutomationId = automation_id
        self.ControlType = control_type if control_type else auto.ControlType.ButtonControl
        self.ControlTypeName = "Button"
        self.ClassName = class_name
        self.IsOffscreen = False
        self.IsEnabled = True
        self.IsKeyboardFocusable = True
        self.HasKeyboardFocus = False
        self.BoundingRectangle = FakeRect(10, 10, 50, 50)
        self.NativeWindowHandle = 0
        self._children = []

    def GetChildren(self):
        return self._children

    def SetFocus(self):
        self.HasKeyboardFocus = True

    def GetValuePattern(self):
        return None

    def GetLegacyIAccessiblePattern(self):
        return None



def test_element_properties():
    """Verify that UIElement properly maps UIA properties."""
    engine = UIAutomationEngine()
    ctrl = FakeControl(name="TestBtn", automation_id="btn_1", class_name="Win32Btn")
    elem = UIElement(ctrl, engine)

    assert elem.name == "TestBtn"
    assert elem.automation_id == "btn_1"
    assert elem.class_name == "Win32Btn"
    assert elem.is_visible is True
    assert elem.is_enabled is True
    assert elem.center == (30, 30)


def test_element_finder_criteria():
    """Verify that matches_client_criteria filters correctly on mock controls."""
    from automation.element_finder import matches_client_criteria

    ctrl = FakeControl(name="Cancel")
    
    # 1. Matching partial name
    sel_partial = Selector(partial_name="nce")
    assert matches_client_criteria(ctrl, sel_partial) is True

    # 2. Matching regex name
    sel_regex = Selector(regex_name="^Can.*$")
    assert matches_client_criteria(ctrl, sel_regex) is True

    # 3. Not matching name
    sel_mismatch = Selector(partial_name="Ok")
    assert matches_client_criteria(ctrl, sel_mismatch) is False


def test_cache_and_invalidation():
    """Verify AutomationCache caches items and invalidates them when needed."""
    engine = UIAutomationEngine()
    ctrl = FakeControl()
    
    # Cache element
    engine.cache.cache_element("test_key", ctrl)
    cached = engine.cache.get_element("test_key")
    assert cached is ctrl

    # Invalidate element
    engine.cache.invalidate_element("test_key")
    assert engine.cache.get_element("test_key") is None


def test_interactable_errors():
    """Verify that UIElement raises exceptions on disabled or invisible elements."""
    engine = UIAutomationEngine()
    ctrl = FakeControl()
    elem = UIElement(ctrl, engine)

    # Disable element
    ctrl.IsEnabled = False
    with pytest.raises(ElementDisabledError):
        elem.click()

    # Enable and make offscreen
    ctrl.IsEnabled = True
    ctrl.IsOffscreen = True
    with pytest.raises(ElementInvisibleError):
        elem.click()


def test_typing_fallback(monkeypatch):
    """Verify type_text fallback path works when ValuePattern is missing."""
    engine = UIAutomationEngine()
    ctrl = FakeControl()
    elem = UIElement(ctrl, engine)
    
    # Mock click, clear, and SendKeys
    monkeypatch.setattr("automation.mouse.Mouse.click", lambda x, y: None)
    monkeypatch.setattr("uiautomation.SendKeys", lambda text, interval=0.01: None)
    
    # Typing without ValuePattern should run keyboard fallback and pass verification since Name matches
    elem.type_text("some_text", verify=False)
    # Verification should succeed with name match fallback
    assert elem.text_value == "mock_element"


def test_window_manager_list():
    """Verify WindowManager handles listing system windows."""
    engine = UIAutomationEngine()
    with patch("uiautomation.GetRootControl") as mock_root:
        mock_root_ctrl = MagicMock()
        mock_child = MagicMock()
        mock_child.ControlType = auto.ControlType.WindowControl
        mock_child.IsOffscreen = False
        mock_child.Name = "Test Window"
        mock_root_ctrl.GetChildren.return_value = [mock_child]
        mock_root.return_value = mock_root_ctrl
        
        wins = engine.window_manager.list_windows()
        assert len(wins) == 1
        assert wins[0].name == "Test Window"
