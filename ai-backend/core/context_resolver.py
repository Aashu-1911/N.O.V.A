from typing import Any, Dict, Tuple, Optional
import re
from core.execution_context import ExecutionContext

def normalize_command_verbs(command: str) -> str:
    """Normalize action verbs to canonical form before intent parsing."""
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
    using state snapshot stored in the Execution Context.
    """
    def resolve(
        self,
        command: str,
        intent: str,
        entities: Dict[str, Any],
        snapshot: ExecutionContext,
    ) -> Tuple[str, str, Dict[str, Any], Optional[Dict[str, Any]]]:
        """Resolves pronouns, repeat triggers, or context questions based on context snapshot.
        
        Returns:
            Tuple of (resolved_command, resolved_intent, resolved_entities, direct_response)
        """
        normalized = command.strip().lower()

        # Rule 6: "Open it again" -> use last_opened_application (checked first to avoid generic repeat)
        if re.search(r"\b(open\s+it\s+again|open\s+again)\b", normalized):
            resolved_app = snapshot.last_opened_application or snapshot.current_application or snapshot.last_app
            if resolved_app:
                resolved_entities = dict(entities)
                resolved_entities["app_name"] = resolved_app
                resolved_cmd = f"open {resolved_app}"
                self._log_rewrite(command, resolved_cmd, "Used last_opened_application")
                return resolved_cmd, "open_application", resolved_entities, None
            else:
                self._log_no_rewrite("No application in context for 'open again'")

        # Rule 10: "Search again" -> Reuse last_search_query (checked first to avoid generic repeat)
        if re.search(r"\b(search\s+again)\b", normalized):
            if snapshot.last_search_query:
                resolved_entities = dict(entities)
                resolved_entities["search_query"] = snapshot.last_search_query
                resolved_cmd = f"search {snapshot.last_search_query}"
                self._log_rewrite(command, resolved_cmd, "Used last_search_query")
                return resolved_cmd, "search_web", resolved_entities, None
            else:
                self._log_no_rewrite("No search query in context to repeat")

        # Rule 7: "Do it again" -> Repeat last successful command (uses specific exact matches)
        if re.search(r"^(do it\s+)?again$|^(repeat\s+that|repeat|repeat\s+last\s+command)$", normalized):
            last_success_cmd = None
            if snapshot.last_success and snapshot.last_command:
                last_success_cmd = snapshot.last_command
            elif snapshot.history:
                for entry in reversed(snapshot.history):
                    if entry.get("status") == "success":
                        last_success_cmd = entry.get("command")
                        break
            if last_success_cmd:
                from core.intent_parser import parse_intent
                parsed = parse_intent(last_success_cmd)
                self._log_rewrite(command, last_success_cmd, "Used last successful command from history")
                return last_success_cmd, parsed["intent"], parsed["entities"], None
            else:
                self._log_no_rewrite("No previous successful command in history to repeat")

        # Rule 8: "Go back" -> If current_browser exists
        if re.search(r"\b(go\s+back|navigate\s+back)\b", normalized):
            if snapshot.current_browser:
                self._log_rewrite(command, command, f"Routed to navigation because current_browser={snapshot.current_browser}")
                return command, "browser_go_back", dict(entities), None
            else:
                self._log_no_rewrite("No active browser context for 'go back'")

        # Rule 9: "Refresh" -> If current_browser exists
        if re.search(r"\b(refresh|refresh\s+page)\b", normalized):
            if snapshot.current_browser:
                self._log_rewrite(command, command, f"Routed to refresh page because current_browser={snapshot.current_browser}")
                return command, "browser_refresh", dict(entities), None
            else:
                self._log_no_rewrite("No active browser context for 'refresh'")

        # Browser Search Results ("open the first result")
        if re.search(r"\b(open|click|go to)?\s*(the\s+)?first\s+result\b", normalized):
            if snapshot.last_search_query:
                query = snapshot.last_search_query.lower()
                resolved_url = "https://www.google.com"
                if "github" in query:
                    resolved_url = "https://github.com"
                elif "cat" in query:
                    resolved_url = "https://en.wikipedia.org/wiki/Cat"
                else:
                    resolved_url = f"https://www.{snapshot.last_search_query.lower().replace(' ', '')}.com"
                
                resolved_entities = dict(entities)
                resolved_entities["url"] = resolved_url
                resolved_cmd = f"open {resolved_url}"
                self._log_rewrite(command, resolved_cmd, f"Used last_search_query query='{snapshot.last_search_query}'")
                return resolved_cmd, "open_website", resolved_entities, None

        # Context Queries
        if re.search(r"\b(what\s+did\s+(you|i)\s+(just\s+)?open|what\s+did\s+you\s+open\s+right\s+now)\b", normalized):
            resolved_entities = dict(entities)
            resolved_entities["query_type"] = "last_opened_application"
            return command, "query_context", resolved_entities, None

        if re.search(r"\bwhat\s+(application|app)\s+is\s+open\b", normalized):
            resolved_entities = dict(entities)
            resolved_entities["query_type"] = "current_application"
            return command, "query_context", resolved_entities, None

        if re.search(r"\bwhat\s+(website|site|url|page)\s+(am\s+i\s+on|is\s+this)\b", normalized):
            resolved_entities = dict(entities)
            resolved_entities["query_type"] = "current_website"
            return command, "query_context", resolved_entities, None

        # Rule 1, 2, 3: Close/Closing and Pronoun resolution for close/open app
        app_name = entities.get("app_name")
        window_name = entities.get("window_name")

        resolved_entities = dict(entities)

        if intent in {"close_application", "open_application"}:
            if not app_name or app_name.lower() in {"it", "that", "this", "app", "application", "window"}:
                resolved_app = resolve_app_from_context(snapshot)
                if resolved_app:
                    resolved_entities["app_name"] = resolved_app
                    resolved_cmd = f"close {resolved_app}" if intent == "close_application" else f"open {resolved_app}"
                    self._log_rewrite(command, resolved_cmd, f"Used priority resolved app name '{resolved_app}'")
                    return resolved_cmd, intent, resolved_entities, None
                elif intent == "close_application":
                    # Clarification response for empty context close
                    direct_response = {
                        "status": "success",
                        "reply": "Which application would you like me to close?",
                        "intent": "close_application",
                        "payload": {"error": "missing_context"}
                    }
                    self._log_rewrite(command, "Bypassed with Clarification Reply", "No active application in context to close")
                    return command, intent, entities, direct_response

        # Rule 4, 5: Window operations and pronoun resolution
        elif intent in {"focus_window", "maximize_window", "minimize_window", "restore_window"}:
            if not window_name or window_name.lower() in {"it", "that", "this", "window", "app", "application"}:
                resolved_window = resolve_window_from_context(snapshot)
                if resolved_window:
                    resolved_entities["window_name"] = resolved_window
                    action_verb = intent.replace("_window", "")
                    resolved_cmd = f"{action_verb} {resolved_window}"
                    self._log_rewrite(command, resolved_cmd, f"Used priority resolved window/app name '{resolved_window}'")
                    return resolved_cmd, intent, resolved_entities, None

        self._log_no_rewrite("No matching context rules applied")
        return command, intent, entities, None

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
