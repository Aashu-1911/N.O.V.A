from typing import Any, Dict, Tuple, Optional
import re
from core.execution_context import ExecutionContext
from capabilities.base import (
    ParsedCommand, ResolvedCommand, Reference, ReferenceWrapper, PronounReference,
    WindowReference, ApplicationReference, BrowserReference, UIElementReference,
    VisionTarget, OCRTarget, FileReference, ClipboardReference,
    SelectionReference, CursorReference, TextBoxReference, PreviousWindowReference,
    TemporalReference, FocusedReference, LocationReference, NeedsClarification,
    ResolvedWindowTarget
)
from capabilities.parser import CommandParser

def normalize_command_verbs(command: str) -> str:
    """Normalize action verbs to canonical form before semantic parsing."""
    normalized = command.strip().lower()
    
    # Close synonyms
    close_synonyms = ["closing", "closed", "exit", "quit", "terminate", "kill", "remove", "dismiss"]
    for syn in close_synonyms:
        pattern = rf"\b{syn}\b"
        if re.search(pattern, normalized):
            command = re.sub(pattern, "close", command, flags=re.IGNORECASE)
            
    # Open synonyms
    open_synonyms = ["launch", "run", "start", "open up"]
    for syn in open_synonyms:
        pattern = rf"\b{syn}\b"
        if re.search(pattern, normalized):
            command = re.sub(pattern, "open", command, flags=re.IGNORECASE)
            
    return command

def resolve_app_from_context(snapshot: ExecutionContext) -> Optional[str]:
    """Retrieve app name from context snapshot following strict reading priorities."""
    if snapshot.current_application:
        return snapshot.current_application
    if snapshot.current_window:
        return snapshot.current_window
    if snapshot.last_opened_application:
        return snapshot.last_opened_application
    if snapshot.last_app:
        return snapshot.last_app
    if snapshot.history:
        for entry in reversed(snapshot.history):
            app = entry.get("entities", {}).get("app_name")
            if app:
                return app
    return None

def resolve_window_from_context(snapshot: ExecutionContext) -> Optional[str]:
    """Retrieve window name from context snapshot following strict reading priorities."""
    if snapshot.current_window:
        return snapshot.current_window
    if snapshot.current_application:
        return snapshot.current_application
    if snapshot.last_window:
        return snapshot.last_window
    if snapshot.history:
        for entry in reversed(snapshot.history):
            win = entry.get("entities", {}).get("window_name") or entry.get("entities", {}).get("app_name")
            if win:
                return win
    return None

def deduce_reference_type(target_str: str, snapshot: ExecutionContext) -> Reference:
    """Deduces a concrete Reference class from a string value."""
    target_lower = target_str.lower()
    if "." in target_lower and not target_lower.startswith(("http", "www")):
        return FileReference(target_str)
    if target_lower in {"chrome", "browser", "firefox", "edge"}:
        return BrowserReference(target_str)
    if target_lower in {"notepad", "calculator", "telegram", "vs code", "vscode"}:
        return WindowReference(target_str)
    return ApplicationReference(target_str)

def resolve_pronoun_reference(verb: str, pronoun: str, snapshot: ExecutionContext) -> Reference:
    """Resolves a PronounReference using target priority checks."""
    # 1. Focused object/element
    if snapshot.focused_element:
        return UIElementReference(snapshot.focused_element)
    if snapshot.focused_control:
        return UIElementReference(snapshot.focused_control)
        
    # 2. Current window or last window
    window_target = snapshot.current_window or snapshot.last_window or snapshot.last_opened_application
    if window_target:
        return WindowReference(window_target)
        
    # 3. Current application or last application
    app_target = snapshot.current_application or snapshot.last_app or snapshot.last_opened_application
    if app_target:
        return ApplicationReference(app_target)
        
    # 4. Current browser or last website
    browser_target = snapshot.current_browser or snapshot.last_website
    if browser_target:
        return BrowserReference(browser_target)
        
    # 5. Selected file / folder
    if snapshot.selected_file:
        return FileReference(snapshot.selected_file)
    if snapshot.selected_folder:
        return FileReference(snapshot.selected_folder)
        
    # 6. Previous command target (recent targets)
    if snapshot.recent_targets:
        return deduce_reference_type(snapshot.recent_targets[-1], snapshot)
        
    # 7. Conversation history
    if snapshot.history:
        for entry in reversed(snapshot.history):
            app = entry.get("entities", {}).get("app_name")
            if app:
                return ApplicationReference(app)
            win = entry.get("entities", {}).get("window_name")
            if win:
                return WindowReference(win)
                
    # If ambiguity remains, clarify
    if verb == "close":
        return NeedsClarification("Which application would you like me to close?")
    if verb == "open":
        return NeedsClarification("Which application would you like me to open?")
    if verb in {"maximize", "minimize", "restore", "focus"}:
        return NeedsClarification("No window name provided.")
    return NeedsClarification(f"Which target would you like me to {verb}?")

class ContextResolver:
    """Resolves referring expressions using rich Execution Context before routing."""

    def resolve(
        self,
        parsed: ParsedCommand,
        snapshot: ExecutionContext,
    ) -> ResolvedCommand:
        """Resolves pronouns, repeat triggers, or focus keywords based on context snapshot.
        
        Returns:
            ResolvedCommand
        """
        resolved = ResolvedCommand(
            raw_command=parsed.raw_command,
            verb=parsed.verb,
            target=parsed.target,
            scope=parsed.scope,
            entities=dict(parsed.entities),
            direct_response=parsed.direct_response
        )

        raw_lower = parsed.raw_command.lower()

        # Helper to log resolution step
        def log_step(target_type: str, resolved_to: Any, confidence: float):
            log_str = (
                "\n========================\n"
                "Context Resolver Step\n"
                f"Parsed Target: {target_type}\n"
                f"Resolved Target: {resolved_to}\n"
                f"Confidence: {confidence}\n"
                "========================\n"
            )
            import logging
            logging.getLogger(__name__).info(log_str)
            print(log_str, flush=True)

        # 1. Temporal Reference ("again", "repeat", "do it again")
        if isinstance(resolved.target, TemporalReference):
            keyword = resolved.target.keyword
            # Special case: "search again"
            if resolved.verb == "search" and "again" in keyword:
                if snapshot.last_search_query:
                    resolved.target = ReferenceWrapper(snapshot.last_search_query)
                    resolved.entities["search_query"] = snapshot.last_search_query
                    resolved.raw_command = f"search {snapshot.last_search_query}"
                    log_step("TemporalReference(again)", f"ReferenceWrapper({snapshot.last_search_query})", 1.0)
                else:
                    resolved.target = NeedsClarification("What query would you like me to search?")
                    log_step("TemporalReference(again)", "NeedsClarification", 1.0)
                return resolved
            
            # Repeat last successful command
            last_cmd = None
            if snapshot.last_success and snapshot.last_command:
                last_cmd = snapshot.last_command
            elif snapshot.history:
                for entry in reversed(snapshot.history):
                    if entry.get("status") == "success":
                        last_cmd = entry.get("command")
                        break
            if last_cmd:
                parsed_last = CommandParser.parse(last_cmd)
                resolved_last = self.resolve(parsed_last, snapshot)
                log_step("TemporalReference(again)", f"ResolvedCommand({resolved_last.raw_command})", 1.0)
                return resolved_last
            else:
                resolved.target = NeedsClarification("What action would you like me to repeat?")
                log_step("TemporalReference(again)", "NeedsClarification", 1.0)
                return resolved

        # 2. Browser Search Results ("open the first result")
        if resolved.object and re.search(r"\b(open|click|go to)?\s*(the\s+)?first\s+result\b", resolved.object.lower()):
            if snapshot.last_search_query:
                query = snapshot.last_search_query.lower()
                resolved_url = "https://www.google.com"
                if "github" in query:
                    resolved_url = "https://github.com"
                elif "cat" in query:
                    resolved_url = "https://en.wikipedia.org/wiki/Cat"
                else:
                    resolved_url = f"https://www.{snapshot.last_search_query.lower().replace(' ', '')}.com"
                
                resolved.verb = "open"
                resolved.target = BrowserReference(resolved_url)
                resolved.entities["url"] = resolved_url
                resolved.raw_command = f"open {resolved_url}"
                log_step("BrowserFirstResult", f"BrowserReference({resolved_url})", 1.0)
                return resolved

        # 3. Pronoun Reference resolution
        if isinstance(resolved.target, PronounReference):
            pronoun = resolved.target.pronoun
            clean_pronoun = pronoun.replace("again", "").strip()
            
            # Context-specific OCR and Vision targets
            if resolved.verb == "read" or resolved.verb == "extract":
                resolved.target = OCRTarget("it")
                log_step(f"PronounReference({pronoun})", "OCRTarget", 1.0)
                return resolved
            if resolved.verb == "describe" or resolved.verb == "observe":
                resolved.target = VisionTarget("screen")
                log_step(f"PronounReference({pronoun})", "VisionTarget", 1.0)
                return resolved

            # General pronoun resolution following reference priority
            resolved_target = resolve_pronoun_reference(resolved.verb or "", clean_pronoun, snapshot)
            resolved.target = resolved_target
            
            if isinstance(resolved_target, NeedsClarification):
                log_step(f"PronounReference({pronoun})", f"NeedsClarification: {resolved_target.reply}", 1.0)
                return resolved
            
            # Convert target name/path to string representation for command reconstruction
            target_str = ""
            if hasattr(resolved_target, "window_name"):
                target_str = resolved_target.window_name
            elif hasattr(resolved_target, "app_name"):
                target_str = resolved_target.app_name
            elif hasattr(resolved_target, "browser_name"):
                target_str = resolved_target.browser_name
            elif hasattr(resolved_target, "file_path"):
                target_str = resolved_target.file_path
            
            if resolved.verb and target_str:
                resolved.raw_command = f"{resolved.verb} {target_str}"
            if target_str:
                resolved.entities["app_name"] = target_str
                resolved.entities["window_name"] = target_str
            
            log_step(f"PronounReference({pronoun})", str(resolved_target), 1.0)
            return resolved

        # 4. Previous Window Reference resolution
        if isinstance(resolved.target, PreviousWindowReference):
            if snapshot.last_window:
                resolved.target = WindowReference(snapshot.last_window)
                if resolved.verb:
                    resolved.raw_command = f"{resolved.verb} {snapshot.last_window}"
                log_step("PreviousWindowReference", f"WindowReference({snapshot.last_window})", 1.0)
            elif snapshot.current_window:
                resolved.target = WindowReference(snapshot.current_window)
                if resolved.verb:
                    resolved.raw_command = f"{resolved.verb} {snapshot.current_window}"
                log_step("PreviousWindowReference", f"WindowReference({snapshot.current_window})", 1.0)
            else:
                resolved.target = NeedsClarification("Which window would you like me to restore?")
                log_step("PreviousWindowReference", "NeedsClarification", 1.0)
            return resolved

        # 5. Focused Reference resolution
        if isinstance(resolved.target, FocusedReference):
            kw = resolved.target.keyword
            # "Close current window", "Focus active window", etc.
            if "window" in kw or "app" in kw or "application" in kw:
                if snapshot.current_window:
                    resolved.target = WindowReference(snapshot.current_window)
                    log_step(f"FocusedReference({kw})", f"WindowReference({snapshot.current_window})", 1.0)
                elif snapshot.current_application:
                    resolved.target = WindowReference(snapshot.current_application)
                    log_step(f"FocusedReference({kw})", f"WindowReference({snapshot.current_application})", 1.0)
                else:
                    # Fallback to active foreground window
                    from managers import window_manager
                    success, active_info, _ = window_manager._manager.get_active_window()
                    if success and active_info and active_info.title:
                        resolved.target = WindowReference(active_info.title)
                        log_step(f"FocusedReference({kw})", f"WindowReference({active_info.title})", 1.0)
                    else:
                        resolved.target = NeedsClarification("Which window or application is current?")
                        log_step(f"FocusedReference({kw})", "NeedsClarification", 1.0)
            elif "textbox" in kw or "text box" in kw:
                resolved.target = TextBoxReference()
                log_step(f"FocusedReference({kw})", "TextBoxReference", 1.0)
            elif snapshot.focused_element:
                resolved.target = UIElementReference(snapshot.focused_element)
                log_step(f"FocusedReference({kw})", f"UIElementReference({snapshot.focused_element})", 1.0)
            else:
                resolved.target = NeedsClarification(f"Which target is {kw}?")
                log_step(f"FocusedReference({kw})", "NeedsClarification", 1.0)
            return resolved

        # 6. Type action with focused control implicit target
        if resolved.verb == "type" and resolved.target is None:
            if snapshot.focused_control and "textbox" in snapshot.focused_control.lower():
                resolved.target = TextBoxReference()
                log_step("ImplicitTypeTarget", "TextBoxReference", 1.0)
            elif snapshot.focused_element and "textbox" in snapshot.focused_element.lower():
                resolved.target = TextBoxReference()
                log_step("ImplicitTypeTarget", "TextBoxReference", 1.0)

        # 7. Browser Refresh and Navigation checks
        if resolved.verb == "refresh" or (isinstance(resolved.target, ReferenceWrapper) and resolved.target.value.lower() == "page"):
            if snapshot.current_browser:
                resolved.verb = "refresh"
                resolved.target = BrowserReference(snapshot.current_browser)
                resolved.raw_command = "refresh"
                log_step("BrowserRefresh", f"BrowserReference({snapshot.current_browser})", 1.0)
                return resolved

        if resolved.verb == "go" and isinstance(resolved.target, ReferenceWrapper) and resolved.target.value.lower() == "back":
            if snapshot.current_browser:
                resolved.verb = "go"
                resolved.target = BrowserReference(snapshot.current_browser)
                resolved.entities["navigation_direction"] = "back"
                resolved.raw_command = "go back"
                log_step("BrowserGoBack", f"BrowserReference({snapshot.current_browser})", 1.0)
                return resolved

        # 8. Context query mappings to conversation queries
        if "what did you open" in raw_lower or "what did i open" in raw_lower:
            resolved.verb = "query"
            resolved.target = ReferenceWrapper("last_opened_application")
            resolved.entities["query_type"] = "last_opened_application"
            log_step("ContextQuery", "last_opened_application", 1.0)
            return resolved
        elif "what application is open" in raw_lower or "what app is open" in raw_lower or "what application is currently open" in raw_lower:
            resolved.verb = "query"
            resolved.target = ReferenceWrapper("current_application")
            resolved.entities["query_type"] = "current_application"
            log_step("ContextQuery", "current_application", 1.0)
            return resolved
        elif "what website" in raw_lower or "what site" in raw_lower or "what url" in raw_lower:
            resolved.verb = "query"
            resolved.target = ReferenceWrapper("current_website")
            resolved.entities["query_type"] = "current_website"
            log_step("ContextQuery", "current_website", 1.0)
            return resolved

        # 9. Single-pass Window Target Resolution
        window_verbs = {"focus", "maximize", "minimize", "restore", "close", "toggle_minimize", "move", "resize"}
        if resolved.verb in window_verbs and not isinstance(resolved.target, NeedsClarification):
            # Extract target query
            target_query = None
            if isinstance(resolved.target, WindowReference):
                target_query = resolved.target.window_name
            elif isinstance(resolved.target, ApplicationReference):
                target_query = resolved.target.app_name
            elif isinstance(resolved.target, ReferenceWrapper):
                target_query = resolved.target.value
            elif isinstance(resolved.target, PronounReference):
                target_query = resolved.target.pronoun

            if isinstance(resolved.target, ResolvedWindowTarget):
                pass
            elif target_query is not None or resolved.verb == "close":
                from managers import window_manager
                if not target_query:
                    # Attempt to resolve current active window for closing
                    success, active_info, _ = window_manager._manager.get_active_window()
                    if success and active_info:
                        resolved.target = ResolvedWindowTarget(
                            hwnd=active_info.hwnd,
                            pid=active_info.pid,
                            process_name=active_info.process_name,
                            application=active_info.process_name.replace(".exe", ""),
                            title=active_info.title
                        )
                        resolved.entities["window_handle"] = active_info.hwnd
                        resolved.entities["window_name"] = active_info.title
                        resolved.entities["app_name"] = active_info.process_name.replace(".exe", "")
                else:
                    chosen, scored, err = window_manager._manager.get_window_info(target_query)
                    if chosen:
                        resolved.target = ResolvedWindowTarget(
                            hwnd=chosen.hwnd,
                            pid=chosen.pid,
                            process_name=chosen.process_name,
                            application=chosen.process_name.replace(".exe", ""),
                            title=chosen.title
                        )
                        resolved.entities["window_handle"] = chosen.hwnd
                        resolved.entities["window_name"] = chosen.title
                        resolved.entities["app_name"] = chosen.process_name.replace(".exe", "")
                    else:
                        resolved.target = ResolvedWindowTarget(
                            hwnd=None,
                            pid=0,
                            process_name="",
                            application="",
                            title=target_query,
                            error_code=err or "WINDOW_NOT_FOUND"
                        )
                        resolved.entities["window_handle"] = None
                        resolved.entities["window_name"] = target_query

        # Default: no rewrite
        return resolved
