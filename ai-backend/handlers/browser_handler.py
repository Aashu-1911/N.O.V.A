"""
Browser handlers - handles open_website and search_web intents.

All functions in this module accept an ``entities`` dict (extracted by the intent
parser) and an optional ``context`` dict.  They return a ``ResponseDict`` built with
:mod:`core.response_builder` helpers.

This module has NO voice imports and NO HTTP framework imports.
"""

from typing import Any, Dict, Optional
from urllib.parse import quote_plus

from core.response_builder import success, error
from managers.browser_manager import open_website

# Convenience alias for the structured response dict returned by every handler.
ResponseDict = Dict[str, Any]


def handle_open_website(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``open_website`` intent — open the browser at a URL or default homepage.

    When no URL is provided the handler opens ``https://www.google.com`` as the
    default browser homepage.  Bare hostnames (without a scheme) are upgraded to
    ``https://`` automatically; single-word names without a dot are expanded to
    ``https://www.<name>.com``.

    Args:
        entities: Intent entities.  Expected keys:

            - ``url`` *(str, optional)* — URL or hostname to open.  When absent, the
              default browser is opened to Google.

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and the resolved URL in
        ``payload["url"]``, or ``status="error"`` on failure.

    Example::

        result = handle_open_website({"url": "youtube"})
        # {"status": "success", "reply": "Opening youtube.com", "payload": {"url": "https://www.youtube.com"}}

        result = handle_open_website({})
        # {"status": "success", "reply": "Opening browser", "payload": {"url": "https://www.google.com"}}
    """
    url = entities.get("url")

    # If no URL provided, open default browser
    if not url:
        try:
            result = open_website("https://www.google.com")
            if result:
                return success("Opening browser", payload={"url": "https://www.google.com"})
            else:
                return error("Failed to open browser")
        except Exception as e:
            return error(f"Failed to open browser: {str(e)}", payload={"error": str(e)})

    # Handle website/URL opening
    try:
        formatted_url = url
        if not url.startswith(("http://", "https://")):
            if "." not in url:
                formatted_url = f"https://www.{url}.com"
            else:
                formatted_url = f"https://{url}"

        result = open_website(formatted_url)

        if result:
            display_url = formatted_url.replace("https://", "").replace("http://", "")
            return success(f"Opening {display_url}", payload={"url": formatted_url})
        else:
            return error(f"Could not open {url}", payload={"url": url})

    except Exception as e:
        return error(
            f"Failed to open website: {str(e)}",
            payload={"error": str(e), "url": url},
        )


def handle_search_web(
    entities: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> ResponseDict:
    """Handle the ``search_web`` intent — perform a Google web search.

    Constructs a ``https://www.google.com/search?q=<query>`` URL and opens it
    in the default browser.

    Args:
        entities: Intent entities.  Expected keys:

            - ``search_query`` *(str, required)* — the search terms to look up.

        context: Optional session / request context (not used by this handler).

    Returns:
        ResponseDict with ``status="success"`` and the search query and URL in
        ``payload``, or ``status="error"`` when the query is missing or the
        browser fails to open.

    Example::

        result = handle_search_web({"search_query": "Python tutorials"})
        # {
        #   "status": "success",
        #   "reply": "Searching for Python tutorials",
        #   "payload": {"query": "Python tutorials", "url": "https://www.google.com/search?q=Python+tutorials"}
        # }
    """
    search_query = entities.get("search_query")

    if not search_query:
        return error("I couldn't determine what to search for")

    try:
        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
        result = open_website(search_url)

        if result:
            return success(
                f"Searching for {search_query}",
                payload={"query": search_query, "url": search_url},
            )
        else:
            return error(
                f"Failed to search for {search_query}",
                payload={"query": search_query},
            )

    except Exception as e:
        return error(
            f"Failed to perform search: {str(e)}",
            payload={"error": str(e), "query": search_query},
        )
