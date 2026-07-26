import time
from typing import Callable, Any, Optional
from automation.exceptions import ActionTimeoutError

class Wait:
    """Provides smart polling-based wait mechanisms for windows and UI controls."""
    
    @staticmethod
    def wait_until(
        condition_fn: Callable[[], bool],
        timeout_ms: int = 5000,
        poll_interval_ms: int = 100,
        action_name: str = "wait",
        target_name: str = "condition"
    ) -> None:
        """Poll the given condition function until it returns True, or raise timeout error."""
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0
        poll_sec = poll_interval_ms / 1000.0
        
        while True:
            try:
                if condition_fn():
                    return
            except Exception:
                pass
                
            if time.time() - start_time >= timeout_sec:
                raise ActionTimeoutError(
                    action=action_name,
                    target=target_name,
                    reason=f"Condition not met within {timeout_ms}ms timeout",
                    suggestions="Verify target application state, visible region, or focus properties match requirements."
                )
            time.sleep(poll_sec)

    @staticmethod
    def wait_for_window(
        find_fn: Callable[[], Optional[Any]],
        timeout_ms: int = 5000
    ) -> Any:
        """Poll find_fn until a valid window object is resolved."""
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0
        while True:
            win = find_fn()
            if win is not None:
                return win
            if time.time() - start_time >= timeout_sec:
                raise ActionTimeoutError(
                    action="wait_for_window",
                    target="window",
                    reason=f"Window not found within {timeout_ms}ms"
                )
            time.sleep(0.1)

    @staticmethod
    def wait_for_element(
        find_fn: Callable[[], Optional[Any]],
        timeout_ms: int = 5000
    ) -> Any:
        """Poll find_fn until a valid element object is resolved."""
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0
        while True:
            elem = find_fn()
            if elem is not None:
                return elem
            if time.time() - start_time >= timeout_sec:
                raise ActionTimeoutError(
                    action="wait_for_element",
                    target="element",
                    reason=f"Element not found within {timeout_ms}ms"
                )
            time.sleep(0.1)

    @staticmethod
    def wait_until_visible(element: Any, timeout_ms: int = 5000) -> None:
        """Wait until the element's is_visible property becomes True."""
        Wait.wait_until(
            lambda: bool(getattr(element, "is_visible", False)),
            timeout_ms=timeout_ms,
            action_name="wait_until_visible",
            target_name=getattr(element, "name", "element")
        )

    @staticmethod
    def wait_until_enabled(element: Any, timeout_ms: int = 5000) -> None:
        """Wait until the element's is_enabled property becomes True."""
        Wait.wait_until(
            lambda: bool(getattr(element, "is_enabled", False)),
            timeout_ms=timeout_ms,
            action_name="wait_until_enabled",
            target_name=getattr(element, "name", "element")
        )

    @staticmethod
    def wait_until_clickable(element: Any, timeout_ms: int = 5000) -> None:
        """Wait until the element becomes both visible and enabled."""
        Wait.wait_until(
            lambda: bool(getattr(element, "is_enabled", False) and getattr(element, "is_visible", False)),
            timeout_ms=timeout_ms,
            action_name="wait_until_clickable",
            target_name=getattr(element, "name", "element")
        )

    @staticmethod
    def wait_until_disappears(check_fn: Callable[[], bool], timeout_ms: int = 5000) -> None:
        """Wait until the control is no longer present/valid in the target scope."""
        Wait.wait_until(
            lambda: not check_fn(),
            timeout_ms=timeout_ms,
            action_name="wait_until_disappears",
            target_name="element"
        )

    @staticmethod
    def wait_until_property(element: Any, prop_name: str, expected_val: Any, timeout_ms: int = 5000) -> None:
        """Wait until a specific element property equals the expected value."""
        Wait.wait_until(
            lambda: getattr(element, prop_name) == expected_val,
            timeout_ms=timeout_ms,
            action_name="wait_until_property",
            target_name=f"{getattr(element, 'name', 'element')}.{prop_name}"
        )

    @staticmethod
    def wait_until_focus(element: Any, timeout_ms: int = 5000) -> None:
        """Wait until the element gains input focus."""
        Wait.wait_until(
            lambda: bool(getattr(element, "has_focus", False)),
            timeout_ms=timeout_ms,
            action_name="wait_until_focus",
            target_name=getattr(element, "name", "element")
        )
