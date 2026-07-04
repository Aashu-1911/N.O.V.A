"""
Browser handlers - handles open_browser (open_website) and search_web intents.
"""

from typing import Dict, Optional
from urllib.parse import quote_plus

from managers.browser_manager import open_website


def handle_open_website(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for open_website intent - opens browser, websites, or performs web searches."""
    url = entities.get("url")

    # If no URL provided, open default browser
    if not url:
        try:
            success = open_website("https://www.google.com")
            if success:
                return {
                    "status": "success",
                    "reply": "Opening browser",
                    "payload": {"url": "https://www.google.com"}
                }
            else:
                return {
                    "status": "error",
                    "reply": "Failed to open browser",
                    "payload": {}
                }
        except Exception as e:
            return {
                "status": "error",
                "reply": f"Failed to open browser: {str(e)}",
                "payload": {"error": str(e)}
            }

    # Handle website/URL opening
    try:
        formatted_url = url
        if not url.startswith(("http://", "https://")):
            if "." not in url:
                formatted_url = f"https://www.{url}.com"
            else:
                formatted_url = f"https://{url}"

        success = open_website(formatted_url)

        if success:
            display_url = formatted_url.replace("https://", "").replace("http://", "")
            return {
                "status": "success",
                "reply": f"Opening {display_url}",
                "payload": {"url": formatted_url}
            }
        else:
            return {
                "status": "error",
                "reply": f"Could not open {url}",
                "payload": {"url": url}
            }

    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to open website: {str(e)}",
            "payload": {"error": str(e), "url": url}
        }


def handle_search_web(entities: Dict, context: Optional[Dict] = None) -> Dict:
    """Handler for search_web intent - performs web searches using Google."""
    search_query = entities.get("search_query")

    if not search_query:
        return {
            "status": "error",
            "reply": "I couldn't determine what to search for",
            "payload": {}
        }

    try:
        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
        success = open_website(search_url)

        if success:
            return {
                "status": "success",
                "reply": f"Searching for {search_query}",
                "payload": {"query": search_query, "url": search_url}
            }
        else:
            return {
                "status": "error",
                "reply": f"Failed to search for {search_query}",
                "payload": {"query": search_query}
            }

    except Exception as e:
        return {
            "status": "error",
            "reply": f"Failed to perform search: {str(e)}",
            "payload": {"error": str(e), "query": search_query}
        }
