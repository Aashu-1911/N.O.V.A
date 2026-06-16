from difflib import get_close_matches

KNOWN_WEBSITES = [
    "youtube",
    "google",
    "github",
    "chatgpt",
    "leetcode",
    "linkedin",
    "reddit",
    "codeforces",
]

def match_website(name: str):
    if not name:
        return None

    match = get_close_matches(
        name.lower(),
        KNOWN_WEBSITES,
        n=1,
        cutoff=0.75
    )

    return match[0] if match else None