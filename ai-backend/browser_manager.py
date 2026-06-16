import webbrowser

def open_website(url):
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False