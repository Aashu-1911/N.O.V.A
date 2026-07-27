from typing import List, Tuple, Optional
from managers.window.model import WindowInfo
from managers.window.cache import WindowCache, filter_standard_windows
from managers.window.matcher import WindowMatcher
from managers.window.history import WindowHistory

class WindowResolver:
    """Resolves a window query into the best matching candidate from the system."""
    def __init__(self, cache: WindowCache, matcher: WindowMatcher, history: WindowHistory) -> None:
        self.cache = cache
        self.matcher = matcher
        self.history = history

    def resolve_candidates(self, query: str, include_hidden: bool = False) -> List[Tuple[WindowInfo, float]]:
        """Scans running windows and filters candidates matching the query."""
        all_wins = self.cache.get_all_windows()
        filtered = filter_standard_windows(all_wins, include_hidden=include_hidden)
        
        scored: List[Tuple[WindowInfo, float]] = []
        for w in filtered:
            score = self.matcher.score(w, query)
            if score >= 0.40:  # Matching threshold
                scored.append((w, score))
                
        # Sort primarily by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def choose_best_window(self, query: str, include_hidden: bool = False) -> Tuple[Optional[WindowInfo], List[Tuple[WindowInfo, float]], Optional[str]]:
        """Selects the best single window candidate or reports ambiguity/not found."""
        # 0. Check if the query is a destroyed HWND
        try:
            is_hwnd_query = False
            val = None
            if isinstance(query, int):
                is_hwnd_query = True
                val = query
            elif isinstance(query, str) and (query.isdigit() or query.startswith("0x")):
                is_hwnd_query = True
                val = int(query, 16) if query.startswith("0x") else int(query)
            
            if is_hwnd_query and val is not None:
                import win32gui
                if not win32gui.IsWindow(val):
                    return None, [], "WINDOW_DESTROYED"
        except Exception:
            pass

        scored = self.resolve_candidates(query, include_hidden=include_hidden)
        if not scored:
            return None, [], "WINDOW_NOT_FOUND"

        # Group candidates with the highest match score
        max_score = scored[0][1]
        winners = [w for w, s in scored if abs(s - max_score) < 0.001]

        if len(winners) == 1:
            return winners[0], scored, None

        # Resolve ambiguity using priorities:
        # 1. Current context / active window
        active_hwnd = self.history.current_hwnd
        for w in winners:
            if w.hwnd == active_hwnd:
                return w, scored, None

        # 2. Most recently focused window from focus stack
        for hwnd in reversed(self.history.recent_stack):
            for w in winners:
                if w.hwnd == hwnd:
                    return w, scored, None

        # 3. Z-order (topmost active window first)
        winners.sort(key=lambda w: w.z_order)
        return winners[0], scored, None
