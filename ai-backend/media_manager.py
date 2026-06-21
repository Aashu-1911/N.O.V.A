import webbrowser
from urllib.parse import quote_plus


def play_media(query: str):
    if not query:
        return False

    url = (
        "https://open.spotify.com/search/"
        + quote_plus(query)
    )

    webbrowser.open(url)

    return True