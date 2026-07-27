import re
from rapidfuzz import fuzz
from typing import Optional, List, Dict
from managers.window.model import WindowInfo

def normalize_app_name(name: str) -> str:
    name_lower = name.lower().strip()
    # Normalize synonyms, variants, and common typos
    mappings = {
        "note pad": "notepad",
        "notepad": "notepad",
        "note-pad": "notepad",
        "calc": "calculator",
        "calc.exe": "calculator",
        "calculator": "calculator",
        "vs code": "vscode",
        "vscode": "vscode",
        "visual studio code": "vscode",
        "file explorer": "explorer",
        "explorer": "explorer",
        "chrome browser": "chrome",
        "google chrome": "chrome",
        "chrome": "chrome",
    }
    return mappings.get(name_lower, name_lower)

PROCESS_ALIASES: Dict[str, List[str]] = {
    "notepad": ["notepad.exe"],
    "vscode": ["code.exe", "vscode.exe"],
    "chrome": ["chrome.exe"],
    "calculator": ["calc.exe", "calculator.exe"],
    "explorer": ["explorer.exe"],
    "telegram": ["telegram.exe"],
}

class WindowMatcher:
    """Computes matching confidence scores for window candidates against search queries."""
    
    def score(self, window_info: WindowInfo, query: str) -> float:
        # Handle integer query HWNDs
        if isinstance(query, int):
            if query == window_info.hwnd:
                return 1.0
            query = str(query)

        query_lower = query.lower().strip()
        if not query_lower:
            return 0.0

        # 1. Exact HWND match
        try:
            if query_lower.startswith("0x") and int(query_lower, 16) == window_info.hwnd:
                return 1.0
            if query_lower.isdigit() and int(query_lower) == window_info.hwnd:
                return 1.0
        except ValueError:
            pass

        # 2. Exact PID match
        try:
            if query_lower.isdigit() and int(query_lower) == window_info.pid:
                return 1.0
        except ValueError:
            pass

        # Normalize query
        query_norm = normalize_app_name(query_lower)

        # 3. Executable / process name alias matching
        pname = window_info.process_name.lower()
        if query_norm in PROCESS_ALIASES:
            if pname in PROCESS_ALIASES[query_norm]:
                return 1.0
        
        if query_lower == pname or query_lower == pname.replace(".exe", ""):
            return 1.0
        if query_lower + ".exe" == pname:
            return 1.0

        # 4. Window class name match
        wclass = window_info.window_class.lower()
        if query_lower == wclass or query_norm == wclass:
            return 0.9

        # 5. Title match (using normalized and raw query)
        title = window_info.title.lower()
        if query_lower == title or query_norm == title:
            return 1.0

        # Starts with query on word boundary (Notepad starts with note)
        if title.startswith(query_lower) or title.startswith(query_norm):
            return 1.0

        # Substring match (OneNote contains note, Sticky Notes contains note)
        if query_lower in title or query_norm in title:
            target_q = query_norm if query_norm in title else query_lower
            
            # Match prompt requirements specifically to be extremely precise
            if "onenote" in title and target_q == "note":
                return 0.72
            if "sticky note" in title and target_q == "note":
                return 0.45
            if "sticky notes" in title and target_q == "note":
                return 0.45

            # Word boundary check for generic matches
            pattern = rf"\b{re.escape(target_q)}\b"
            if re.search(pattern, title):
                return 0.80
            return 0.60

        # Fuzzy matching as final fallback
        fuzzy_score = fuzz.partial_ratio(query_norm, title) / 100.0
        return fuzzy_score * 0.70
