"""
Browser handlers - handles open_browser (open_website) and search_web intents.
"""

from typing import Dict, Optional
from urllib.parse import quote_plus

from core.response_builder import success, error
from managers.browser_manager import open_website


def handle_open_website(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for open_website intent - opens browser, websites, or performs web searches."""
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


def handle_search_web(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for search_web intent - performs web searches using Google."""
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
