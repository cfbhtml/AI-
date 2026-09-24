import requests

def lookup_online(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        res = requests.get(url, params=params, timeout=5)
        data = res.json()

        # Main summary
        if data.get("AbstractText"):
            return data["AbstractText"]

        # Related topics fallback
        related = data.get("RelatedTopics", [])
        if related:
            for item in related:
                if "Text" in item:
                    return item["Text"]

        return "I searched online but couldn't find a clear answer."

    except Exception:
        return "Online lookup failed."
