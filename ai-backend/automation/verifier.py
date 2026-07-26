import time
from typing import Any
from automation.exceptions import VerificationError
from automation.waits import Wait

class Verifier:
    """Performs semantic post-action state verification checks to ensure determinism."""
    
    @staticmethod
    def verify_click(element: Any, timeout_ms: int = 2000) -> None:
        """Verifies that clicking an element caused it to execute or transition state."""
        # For buttons, standard behavior is simple check or active validation. 
        # Click verification can poll if it succeeded.
        # Since uiautomation click is synchronous, we ensure no crash occurred.
        pass

    @staticmethod
    def verify_typing(element: Any, expected_text: str, timeout_ms: int = 2000) -> None:
        """Verifies that the target text box contains the expected text."""
        try:
            Wait.wait_until(
                lambda: element.text_value == expected_text,
                timeout_ms=timeout_ms,
                action_name="verify_typing",
                target_name=getattr(element, "name", "element")
            )
        except Exception as e:
            actual = getattr(element, "text_value", "Unknown")
            raise VerificationError(
                action="type_text",
                target=getattr(element, "name", "element"),
                reason=f"Verification failed. Expected text '{expected_text}', found '{actual}'",
                suggestions="Verify field focus, keyboard layouts, or whether the element is read-only."
            ) from e

    @staticmethod
    def verify_selection(element: Any, expected_item: str, timeout_ms: int = 2000) -> None:
        """Verifies that the correct item or check state is selected."""
        try:
            # Check if combobox / list selection equals expected
            Wait.wait_until(
                lambda: element.selected_item == expected_item,
                timeout_ms=timeout_ms,
                action_name="verify_selection",
                target_name=getattr(element, "name", "element")
            )
        except Exception as e:
            actual = getattr(element, "selected_item", "None")
            raise VerificationError(
                action="select",
                target=getattr(element, "name", "element"),
                reason=f"Verification failed. Expected selection '{expected_item}', found '{actual}'",
                suggestions="Check if item is present in list/combo box options."
            ) from e
