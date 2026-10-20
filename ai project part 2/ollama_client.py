import requests

DEFAULT_MODEL = "llama3"

def chat(messages, model=DEFAULT_MODEL):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    response = requests.post(url, json=payload, timeout=(2, 60))
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "")

def check_connection():
    try:
        r = requests.get("http://localhost:11434")
        return True, "Ollama reachable"
    except Exception as e:
        return False, str(e)

def list_models():
    try:
        r = requests.get("http://localhost:11434/api/tags")
        return [m["name"] for m in r.json()]
    except:
        return []
