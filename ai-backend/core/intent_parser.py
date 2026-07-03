import re
from difflib import get_close_matches
from typing import Dict, Optional
from urllib.parse import urlparse

from utils.entity_matcher import match_website


KNOWN_APPS = [
    "vs code",
    "vscode",
    "visual studio code",
    "microsoft store",
    "chrome",
    "google chrome",
    "edge",
    "microsoft edge",
    "firefox",
    "discord",
    "spotify",
    "notepad",
    "calculator",
    "calc",
    "cmd",
    "command prompt",
    "powershell",
    "task manager",
    "steam",
]


def _extract_url(text: str) -> Optional[str]:
    url_match = re.search(
        r"(https?://[^\s]+|www\.[^\s]+)",
        text,
        flags=re.IGNORECASE,
    )

    if url_match:
        candidate = url_match.group(1)

        if not candidate.startswith(("http://", "https://")):
            candidate = f"https://{candidate}"

        parsed = urlparse(candidate)

        if parsed.netloc:
            return candidate

    website_name = match_website(text)

    if website_name:
        return website_name

    return None


def _extract_search_query(text: str) -> Optional[str]:
    """Extract search query from search commands."""
    # Patterns like "search google for X", "search for X", "google X"
    patterns = [
        r"search\s+(?:google|web|online)?\s*(?:for\s+)?(.+)",
        r"(?:google|search)\s+(.+)",
        r"look up\s+(.+)",
        r"find\s+(.+\s+on\s+(?:google|web))",
    ]
    
    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower, flags=re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            # Remove trailing punctuation
            query = re.sub(r'[.!?]+$', '', query)
            return query if query else None
    
    return None


def _extract_priority(text: str) -> Optional[str]:
    priority_match = re.search(r"\b(low|medium|high|urgent)\b", text, flags=re.IGNORECASE)
    return priority_match.group(1).lower() if priority_match else None


def _extract_category(text: str) -> Optional[str]:
    category_patterns = [
        r"(?:category|for)\s+(?:is\s+)?([a-zA-Z][a-zA-Z0-9_-]+)",
        r"\b(work|personal|study|health|home|shopping|finance)\b",
    ]
    for pattern in category_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return None


def _extract_date(text: str) -> Optional[str]:
    patterns = [
        r"\b(today|tomorrow|tonight|weekend|next week|next month)\b",
        r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def _extract_task_name(text: str, intent: str) -> Optional[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    intent_patterns = {
        "add_task": [
            r"(?:add|create|make)\s+(?:a\s+)?task(?:\s+to)?[:\-]?\s*(.+)",
            r"(?:add)\s+task\s+(.+)",
            r"(?:add)\s+it\s+as\s+(?:a\s+)?task(?:\s+to)?\s*(.+)",
            r"(?:remember to|remind me to)\s+(.+)",
        ],
        "complete_task": [
            r"(?:complete|finish|mark done|mark as done)\s+(?:task\s+)?(.+)",
            r"(?:task\s+)?(.+?)\s+(?:is\s+)?(?:done|completed|finished)",
        ],
        "update_task": [
            r"(?:update|edit|change|modify)\s+(?:task\s+)?(.+)",
        ],
        "reminder": [
            r"(?:remind me to|set a reminder to)\s+(.+)",
        ],
    }

    for pattern in intent_patterns.get(intent, []):
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            task_name = match.group(1).strip(" .")
            task_name = re.sub(r"^(?:to\s+)+", "", task_name, flags=re.IGNORECASE)
            return task_name or None

    return None


def _extract_application(text: str):
    lower_text = text.lower()

    for app in KNOWN_APPS:
        if app in lower_text:
            return app

    return None


def _extract_volume_action(text: str):
    text = text.lower()

    if "unmute" in text:
        return "unmute"

    if "mute" in text:
        return "mute"

    if "volume up" in text or "increase volume" in text:
        return "up"

    if "volume down" in text or "decrease volume" in text:
        return "down"

    return None


def _extract_media_action(text: str):
    text = text.lower()

    if "pause" in text:
        return "pause"

    if "resume" in text:
        return "resume"

    if "next" in text or "skip" in text:
        return "next"

    if "previous" in text or "back" in text:
        return "previous"

    if text.startswith("play "):
        return "play"

    return None


def _extract_media_query(text: str):
    text = text.strip()
    lower = text.lower()

    if lower.startswith("play "):
        return text[5:].strip()

    return None


def parse_intent(text: str) -> Dict[str, Dict[str, Optional[str]]]:
    normalized = text.strip().lower()
    intent = "answer_question"

    if re.search(r"\b(complete|finish|done|mark done|mark as done|completed)\b", normalized):
        intent = "complete_task"
    elif re.search(r"\b(update|edit|change|modify)\b", normalized):
        intent = "update_task"
    elif re.search(r"\b(add|create|new task|remember to|remind me to)\b", normalized):
        intent = "add_task" if "remind me" not in normalized else "reminder"
    elif re.search(r"\b(stats|statistics|progress|summary|status)\b", normalized):
        intent = "show_stats"
    elif re.search(r"\b(search|look up|find|google)\b", normalized) and _extract_search_query(text):
        intent = "search_web"
    elif _extract_application(text):
        intent = "open_application"
    elif _extract_url(text) or re.search(r"\b(open|visit|website|site|browser)\b", normalized):
        intent = "open_website"
    elif re.search(r"\b(remind|reminder)\b", normalized):
        intent = "reminder"
    elif re.search(r"\b(screenshot|screen shot|capture screen)\b", normalized):
        intent = "take_screenshot"
    elif re.search(r"\b(lock computer|lock pc|lock system|lock screen|lock my computer|lock my pc)\b", normalized):
        intent = "lock_pc"
    elif re.search(r"\b(mute|unmute|volume up|volume down|increase volume|decrease volume)\b", normalized):
        intent = "volume_control"
    elif re.search(r"\b(play|pause|resume|next|previous|skip)\b", normalized):
        intent = "media_control"
    elif re.search(r"\b(close|exit|quit|terminate|kill)\b", normalized):
        intent = "close_application"

    entities = {
        "task_name": _extract_task_name(text, intent),
        "category": _extract_category(text),
        "priority": _extract_priority(text),
        "url": _extract_url(text),
        "search_query": _extract_search_query(text),
        "app_name": _extract_application(text),
        "date": _extract_date(text),
        "volume_action": _extract_volume_action(text),
        "media_action": _extract_media_action(text),
        "media_query": _extract_media_query(text),
    }

    task_name = entities.get("task_name")
    date_value = entities.get("date")

    if task_name and date_value:
        cleaned_task_name = re.sub(
            rf"\s*(?:on|by|for)?\s*{re.escape(date_value)}$",
            "",
            task_name,
            flags=re.IGNORECASE,
        ).strip(" .")

        entities["task_name"] = cleaned_task_name or task_name

    confidence = 0.5

    if intent == "add_task" and entities.get("task_name"):
        confidence = 0.9
    elif intent == "complete_task" and entities.get("task_name"):
        confidence = 0.9
    elif intent == "update_task" and entities.get("task_name"):
        confidence = 0.9
    elif intent == "open_website" and entities.get("url"):
        confidence = 0.9
    elif intent == "search_web" and entities.get("search_query"):
        confidence = 0.95
    elif intent == "open_application" and entities.get("app_name"):
        confidence = 0.9
    elif intent == "show_stats":
        confidence = 0.95
    elif intent == "reminder" and entities.get("task_name"):
        confidence = 0.9
    elif intent == "take_screenshot":
        confidence = 0.95
    elif intent == "lock_pc":
        confidence = 0.95
    elif intent == "volume_control":
        confidence = 0.95
    elif intent == "media_control" and entities.get("media_action"):
        confidence = 0.95
    elif intent == "close_application" and entities.get("app_name"):
        confidence = 0.95

    return {
        "intent": intent,
        "entities": entities,
        "confidence": confidence,
    }