import re
from typing import Any, Dict, Optional
from capabilities.base import (
    ParsedCommand, Reference, ReferenceWrapper, PronounReference,
    WindowReference, ApplicationReference, BrowserReference, UIElementReference,
    VisionTarget, OCRTarget, FileReference, ClipboardReference,
    SelectionReference, CursorReference, TextBoxReference, PreviousWindowReference,
    TemporalReference, FocusedReference, LocationReference, NeedsClarification
)

class CommandParser:
    """Lightweight, capability-agnostic semantic parser for user commands."""

    @staticmethod
    def parse(command: str) -> ParsedCommand:
        """Parses raw text command to extract verb, object, scope, and semantic entities."""
        normalized = command.strip().lower()
        if not normalized:
            return ParsedCommand(raw_command=command)

        # 1. Normalize multi-word actions and contractions
        verb = ""
        obj = ""
        entities: Dict[str, Any] = {
            "task_name": None,
            "category": None,
            "priority": None,
            "url": None,
            "search_query": None,
            "app_name": None,
            "date": None,
            "volume_action": None,
            "media_action": None,
            "media_query": None,
            "window_name": None
        }

        # Check multi-word command patterns first
        if normalized.startswith("open up "):
            verb = "open"
            obj = command[len("open up "):]
        elif normalized.startswith("close down "):
            verb = "close"
            obj = command[len("close down "):]
        elif normalized.startswith("look at "):
            verb = "describe"
            obj = command[len("look at "):]
        elif normalized.startswith("what is on ") or normalized.startswith("what's on "):
            verb = "describe"
            if "screen" in normalized:
                obj = "screen"
            else:
                prefix_len = len("what's on ") if "what's on" in normalized else len("what is on ")
                obj = command[prefix_len:]
        elif normalized.startswith("read text from "):
            verb = "read"
            obj = "text"
            entities["source"] = command[len("read text from "):].strip()
        elif normalized.startswith("extract text from "):
            verb = "read"
            obj = "text"
            entities["source"] = command[len("extract text from "):].strip()
        else:
            # Fallback to first-word verb parsing
            words = command.split()
            verb = words[0].lower()
            obj = " ".join(words[1:])

        # 2. Map verb synonyms to canonical actions
        verb_mapping = {
            "launch": "open", "run": "open", "start": "open",
            "exit": "close", "quit": "close", "terminate": "close", "kill": "close", "dismiss": "close",
            "locate": "find",
            "press": "click", "select": "click",
            "write": "type", "enter": "type",
            "google": "search", "lookup": "search",
            "raise": "increase", "up": "increase",
            "lower": "decrease", "down": "decrease",
            "observe": "describe"
        }
        verb = verb_mapping.get(verb, verb)

        # 3. Clean up object string (strip leading articles)
        obj_clean = obj.strip()
        obj_lower = obj_clean.lower()
        for article in ["my ", "the ", "a ", "an "]:
            if obj_lower.startswith(article):
                obj_clean = obj_clean[len(article):]
                obj_lower = obj_lower[len(article):]
                break

        # Strip trailing/surrounding punctuation, quotes, and parentheses
        obj_clean = obj_clean.strip()
        obj_clean = re.sub(r'[.,!?\s]+$', '', obj_clean)
        # Strip surrounding quotes
        if (obj_clean.startswith('"') and obj_clean.endswith('"')) or (obj_clean.startswith("'") and obj_clean.endswith("'")):
            obj_clean = obj_clean[1:-1]
        obj_clean = obj_clean.strip()
        # Strip surrounding parentheses
        if obj_clean.startswith('(') and obj_clean.endswith(')'):
            obj_clean = obj_clean[1:-1]
        obj_clean = obj_clean.strip()
        obj_lower = obj_clean.lower()

        # 4. Resolve scope
        scope = None
        ui_indicators = {"button", "textbox", "label", "checkbox", "control", "item", "popup"}
        if verb in {"find", "click", "type", "focus", "select", "toggle"}:
            if any(ind in obj_lower for ind in ui_indicators):
                scope = "current application"

        # 5. Determine semantic target Reference class
        target = None
        if verb == "do" and obj_lower in {"it", "it again"}:
            target = TemporalReference("do it again")
        elif obj_lower in {"it", "this", "that", "those", "these", "it again", "this again", "that again"}:
            target = PronounReference(obj_lower)
        elif "previous window" in obj_lower or "last window" in obj_lower:
            target = PreviousWindowReference()
        elif obj_lower in {"again", "repeat that", "repeat", "last command", "do it again", "do it"}:
            target = TemporalReference(obj_lower)
        elif any(f in obj_lower for f in ["focused", "selected", "active", "current"]):
            target = FocusedReference(obj_lower)
        elif any(loc in obj_lower for loc in ["here", "there", "under cursor"]):
            target = LocationReference(obj_lower)
        elif verb in {"click", "type", "focus", "select", "toggle"} and any(ind in obj_lower for ind in ui_indicators):
            target = UIElementReference(obj_clean)
        elif "." in obj_clean and not obj_clean.startswith(("http", "www")):
            target = FileReference(obj_clean)
        else:
            if obj_clean == "":
                if verb == "close":
                    target = PronounReference("")
                else:
                    target = None
            elif verb == "type":
                target = None
            elif verb in {"open", "close"}:
                if obj_lower in {"browser", "firefox", "edge"}:
                    target = BrowserReference(obj_clean)
                elif obj_lower in {"chrome", "notepad", "calculator", "telegram", "vs code", "vscode"}:
                    target = WindowReference(obj_clean)
                else:
                    target = ApplicationReference(obj_clean)
            elif verb in {"focus", "maximize", "minimize", "restore"}:
                target = WindowReference(obj_clean)
            elif verb in {"click", "find"}:
                target = UIElementReference(obj_clean)
            else:
                target = ReferenceWrapper(obj_clean)

        # 6. Populate standard entity fields dynamically based on semantic category
        if verb == "open" or verb == "close":
            entities["app_name"] = obj_clean
            entities["window_name"] = obj_clean
            # Check if object is a URL
            if "." in obj_clean or "http" in obj_lower:
                entities["url"] = obj_clean if "://" in obj_clean else f"https://{obj_clean}"
        elif verb == "search":
            entities["search_query"] = obj_clean
        elif verb == "click" or verb == "find":
            entities["control_name"] = obj_clean
        elif verb == "type":
            entities["text"] = obj_clean
        elif verb in {"increase", "decrease"}:
            if "volume" in obj_lower:
                entities["volume_action"] = "up" if verb == "increase" else "down"
        elif verb in {"play", "pause", "skip", "stop"}:
            entities["media_action"] = "pause" if verb == "pause" else verb
            if obj_clean and "music" not in obj_lower:
                entities["media_query"] = obj_clean

        # Task Management entities handling
        if "task" in obj_lower:
            if verb in {"add", "complete"}:
                title_match = re.search(r"\btask\s+(.+)$", obj_lower, re.IGNORECASE)
                if title_match:
                    entities["title"] = obj_clean[title_match.start(1):]
                    entities["task_name"] = entities["title"]
            if verb == "complete":
                id_match = re.search(r"\b(?:task\s+)?(\d+)$", obj_clean)
                if id_match:
                    entities["task_id"] = int(id_match.group(1))

        return ParsedCommand(
            raw_command=command,
            verb=verb,
            target=target,
            scope=scope,
            entities=entities
        )
