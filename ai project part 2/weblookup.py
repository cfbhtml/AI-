import requests


def lookup_online(query):
    try:
        response = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return "Online lookup failed: could not reach DuckDuckGo."
    except ValueError:
        return "Online lookup failed: DuckDuckGo returned an invalid response."

    if data.get("AbstractText"):
        return data["AbstractText"]

    for item in data.get("RelatedTopics", []):
        if isinstance(item, dict):
            if item.get("Text"):
                return item["Text"]
            for nested_item in item.get("Topics", []):
                if isinstance(nested_item, dict) and nested_item.get("Text"):
                    return nested_item["Text"]

    return "I searched DuckDuckGo but couldn't find a clear answer."
