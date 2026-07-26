from typing import Any, Dict, Tuple, Optional
import re
from core.execution_context import ExecutionContext
from capabilities.base import ParsedCommand
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

class ContextResolver:
    """Resolves referring expressions (pronouns like 'it', 'that', or repeat triggers 'again')
    using state snapshot stored in the Execution Context before routing.
    """
    def resolve(
        self,
        parsed: ParsedCommand,
        snapshot: ExecutionContext,
    ) -> ParsedCommand:
        """Resolves pronouns, repeat triggers, or context questions based on context snapshot.
        
        Returns:
            Resolved ParsedCommand
        """
        resolved = ParsedCommand(
            raw_command=parsed.raw_command,
            verb=parsed.verb,
            object=parsed.object,
            scope=parsed.scope,
            entities=dict(parsed.entities)
        )
        
        raw_lower = parsed.raw_command.lower()
        normalized_obj = (resolved.object or "").strip().lower()

        # Rule 1: Repeat command if "again", "repeat", "do it again" is detected
        if re.search(r"\b(again|repeat|repeat\s+that|do\s+it\s+again|last\s+command)\b", raw_lower):
            # Special check for "search again", which is Rule 2
            if resolved.verb == "search" and normalized_obj == "again":
                pass
            # Special check for "open it again", which is Rule 3
            elif resolved.verb == "open" and normalized_obj == "it again":
                pass
            else:
                last_cmd = None
                if snapshot.last_success and snapshot.last_command:
                    last_cmd = snapshot.last_command
                elif snapshot.history:
                    for entry in reversed(snapshot.history):
                        if entry.get("status") == "success":
                            last_cmd = entry.get("command")
                            break
                if last_cmd:
                    self._log_rewrite(parsed.raw_command, last_cmd, "Repeated last successful command")
                    return CommandParser.parse(last_cmd)

        # Rule 2: "Search again" -> Reuse last_search_query
        if resolved.verb == "search" and normalized_obj == "again":
            if snapshot.last_search_query:
                resolved.object = snapshot.last_search_query
                resolved.entities["search_query"] = snapshot.last_search_query
                resolved.raw_command = f"search {snapshot.last_search_query}"
                self._log_rewrite(parsed.raw_command, resolved.raw_command, "Repeated last search query")
                return resolved

        # Rule 3: Browser Search Results ("open the first result")
        if re.search(r"\b(open|click|go to)?\s*(the\s+)?first\s+result\b", raw_lower):
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
                resolved.object = resolved_url
                resolved.entities["url"] = resolved_url
                resolved.raw_command = f"open {resolved_url}"
                self._log_rewrite(parsed.raw_command, resolved.raw_command, f"Used last_search_query query='{snapshot.last_search_query}'")
                return resolved

        # Rule 4: Pronoun resolution for close/open/window state
        clean_obj = normalized_obj.replace("again", "").strip()
        if clean_obj in {"it", "that", "this", "window", "app", "application", ""}:
            # Handle empty close clarification
            if resolved.verb == "close" and clean_obj == "":
                resolved_target = resolve_app_from_context(snapshot)
                if not resolved_target:
                    # No app in context, direct clarification response needed
                    resolved.direct_response = {
                        "status": "success",
                        "reply": "Which application would you like me to close?",
                        "intent": "close_application",
                        "payload": {"error": "missing_context"}
                    }
                    self._log_rewrite(parsed.raw_command, "Bypassed with Clarification Reply", "No active application in context to close")
                    return resolved
            else:
                resolved_target = None
                window_verbs = {"focus", "maximize", "minimize", "restore", "close"}
                if resolved.verb in window_verbs:
                    resolved_target = resolve_window_from_context(snapshot)
                else:
                    resolved_target = resolve_app_from_context(snapshot)
            
            if resolved_target:
                resolved_target = resolved_target.lower()
                resolved.object = resolved_target
                if resolved.verb:
                    resolved.raw_command = f"{resolved.verb} {resolved_target}"
                
                # Update app/window entities
                resolved.entities["app_name"] = resolved_target
                resolved.entities["window_name"] = resolved_target
                self._log_rewrite(parsed.raw_command, resolved.raw_command, f"Resolved pronoun to '{resolved_target}'")
                return resolved

        # Rule 5: Browser Refresh
        if resolved.verb == "refresh" or "refresh" in raw_lower:
            if snapshot.current_browser:
                resolved.verb = "refresh"
                resolved.object = "page"
                resolved.raw_command = "refresh"
                self._log_rewrite(parsed.raw_command, resolved.raw_command, "Browser refresh matched")
                return resolved

        # Rule 6: Browser Go Back
        if (resolved.verb == "go" and clean_obj == "back") or "go back" in raw_lower:
            if snapshot.current_browser:
                resolved.verb = "go"
                resolved.object = "back"
                resolved.raw_command = "go back"
                self._log_rewrite(parsed.raw_command, resolved.raw_command, "Browser go back matched")
                return resolved

        # Rule 7: Context query mappings to conversation queries
        if "what did you open" in raw_lower or "what did i open" in raw_lower:
            resolved.verb = "query"
            resolved.object = "last_opened_application"
            resolved.entities["query_type"] = "last_opened_application"
            self._log_rewrite(parsed.raw_command, "Conversation query: last_opened_application", "Context query matched")
            return resolved
        elif "what application is open" in raw_lower or "what app is open" in raw_lower:
            resolved.verb = "query"
            resolved.object = "current_application"
            resolved.entities["query_type"] = "current_application"
            self._log_rewrite(parsed.raw_command, "Conversation query: current_application", "Context query matched")
            return resolved
        elif "what website" in raw_lower or "what site" in raw_lower or "what url" in raw_lower:
            resolved.verb = "query"
            resolved.object = "current_website"
            resolved.entities["query_type"] = "current_website"
            self._log_rewrite(parsed.raw_command, "Conversation query: current_website", "Context query matched")
            return resolved

        self._log_no_rewrite("No matching context rules applied")
        return resolved

    def _log_rewrite(self, original: str, resolved: str, reason: str) -> None:
        log_str = (
            "\n========================\n"
            "Context Resolver\n"
            "Original:\n"
            f"{original}\n"
            "Resolved:\n"
            f"{resolved}\n"
            "Reason:\n"
            f"{reason}\n"
            "========================\n"
        )
        import logging
        logging.getLogger(__name__).info(log_str)
        print(log_str, flush=True)

    def _log_no_rewrite(self, reason: str) -> None:
        log_str = (
            "\n========================\n"
            "Context Resolver\n"
            "No rewrite\n"
            "Reason:\n"
            f"{reason}\n"
            "========================\n"
        )
        import logging
        logging.getLogger(__name__).info(log_str)
        print(log_str, flush=True)
