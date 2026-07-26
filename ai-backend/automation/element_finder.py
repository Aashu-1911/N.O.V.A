import re
import time
from typing import Any, List, Optional
import uiautomation as auto
from automation.selectors import Selector
from automation.exceptions import ElementNotFoundError

def matches_client_criteria(control: Any, selector: Selector) -> bool:
    """Apply client-side filtering on UIA control properties (e.g. visibility, state, regex names)."""
    try:
        # 1. Check partial name
        if selector.partial_name:
            if selector.partial_name.lower() not in (control.Name or "").lower():
                return False
                
        # 2. Check regex name
        if selector.regex_name:
            if not re.search(selector.regex_name, control.Name or "", re.IGNORECASE):
                return False
                
        # 3. Check visible
        if selector.visible is not None:
            is_visible = not control.IsOffscreen and control.BoundingRectangle.width() > 0
            if is_visible != selector.visible:
                return False
                
        # 4. Check enabled
        if selector.enabled is not None:
            if bool(control.IsEnabled) != selector.enabled:
                return False
                
        # 5. Check focusable
        if selector.focusable is not None:
            if bool(control.IsKeyboardFocusable) != selector.focusable:
                return False

        # 6. Check clickable
        if selector.clickable is not None:
            # clickable requires visibility and enabled
            is_clickable = not control.IsOffscreen and control.BoundingRectangle.width() > 0 and bool(control.IsEnabled)
            if is_clickable != selector.clickable:
                return False

        return True
    except Exception:
        return False

class ElementFinder:
    """Locates elements semantic criteria within UIA tree with optimized COM searches."""

    @staticmethod
    def find_element(
        parent_control: Any,
        selector: Selector,
        timeout_ms: int = 5000
    ) -> Any:
        """Find a single UIA control satisfying selector criteria, or raise ElementNotFoundError."""
        start_time = time.time()
        timeout_sec = timeout_ms / 1000.0

        # Construct native UIA search arguments for COM speedup
        uia_args = {}
        if selector.automation_id:
            uia_args["AutomationId"] = selector.automation_id
        if selector.name:
            uia_args["Name"] = selector.name
        if selector.class_name:
            uia_args["ClassName"] = selector.class_name
        if selector.control_type:
            target_type_id = selector.control_type.to_uia_type() if hasattr(selector.control_type, "to_uia_type") else selector.control_type
            uia_args["ControlType"] = target_type_id

        # Set search depth
        search_depth = 1 if selector.search_scope == "children" else selector.depth
        uia_args["searchDepth"] = search_depth
        uia_args["searchFromControl"] = parent_control

        while True:
            try:
                # Find all controls matching basic native attributes
                controls = auto.Control.GetControls(**uia_args)
                
                # Apply client-side filters
                matched_controls = []
                for ctrl in controls:
                    if matches_client_criteria(ctrl, selector):
                        matched_controls.append(ctrl)

                # Return by index
                if len(matched_controls) > selector.index:
                    return matched_controls[selector.index]

            except Exception:
                pass

            if time.time() - start_time >= timeout_sec:
                raise ElementNotFoundError(
                    action="find_element",
                    target=str(selector.to_dict()),
                    reason=f"Element matching criteria not found within {timeout_ms}ms."
                )
            time.sleep(0.1)
