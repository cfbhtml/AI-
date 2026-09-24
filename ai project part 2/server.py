from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import tempfile
import os
import requests

app = Flask(__name__)
CORS(app)

# ============================================================
# STRONG WEB LOOKUP
# ============================================================
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
        for item in related:
            if isinstance(item, dict) and "Text" in item:
                return item["Text"]

        return "I searched online but couldn't find a clear answer."

    except Exception:
        return "Online lookup failed."
    

# ============================================================
# SCRIPT GENERATOR (ALL LANGUAGES)
# ============================================================
def generate_code(text):
    t = text.lower()

    wants_code = any(
        phrase in t
        for phrase in [
            "make", "create", "build", "generate", "script",
            "starter", "project", "program"
        ]
    )
    if not wants_code:
        return None

    # Detect language
    lang = None
    if "python" in t: lang = "python"
    elif "c++" in t or "cpp" in t: lang = "cpp"
    elif "c#" in t or "csharp" in t: lang = "csharp"
    elif "javascript" in t or " js " in t: lang = "js"
    elif "php" in t: lang = "php"
    elif "java" in t: lang = "java"
    elif " c " in t: lang = "c"
    elif "html" in t: lang = "html"

    # ============================
    # LANGUAGE SCRIPTS
    # ============================

    if lang == "python":
        return """# Python Script - Code Century
def main():
    print("Hello from Code Century Python Script!")

if __name__ == "__main__":
    main()"""

    if lang == "cpp":
        return """#include <iostream>
using namespace std;

int main() {
    cout << "Hello from Code Century C++ Script!" << endl;
    return 0;
}"""

    if lang == "c":
        return """#include <stdio.h>

int main() {
    printf("Hello from Code Century C Script!\\n");
    return 0;
}"""

    if lang == "csharp":
        return """using System;

class Program {
    static void Main() {
        Console.WriteLine("Hello from Code Century C# Script!");
    }
}"""

    if lang == "js":
        return """// JavaScript Script - Code Century
console.log("Hello from Code Century JavaScript Script!");"""

    if lang == "php":
        return """<?php
echo "Hello from Code Century PHP Script!";
?>"""

    if lang == "java":
        return """public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Code Century Java Script!");
    }
}"""

    if lang == "html":
        return """<!DOCTYPE html>
<html>
<head>
  <title>Code Century HTML Script</title>
</head>
<body>
  <h1>Hello from Code Century HTML Script!</h1>
</body>
</html>"""

    return "Tell me the language: Python, C++, C, C#, JavaScript, PHP, Java, HTML."


# ============================================================
# CODE RUNNER (Python, Java, C++, PHP)
# ============================================================
def run_code(language, code):
    language = language.lower()

    try:
        with tempfile.TemporaryDirectory() as tmp:
            if language == "python":
                path = os.path.join(tmp, "main.py")
                with open(path, "w") as f: f.write(code)
                result = subprocess.run(["python", path], capture_output=True, text=True, timeout=3)
                return result.stdout + result.stderr

            if language == "php":
                path = os.path.join(tmp, "main.php")
                with open(path, "w") as f: f.write(code)
                result = subprocess.run(["php", path], capture_output=True, text=True, timeout=3)
                return result.stdout + result.stderr

            if language == "java":
                path = os.path.join(tmp, "Main.java")
                with open(path, "w") as f: f.write(code)
                compile_res = subprocess.run(["javac", path], capture_output=True, text=True, timeout=5)
                if compile_res.returncode != 0:
                    return compile_res.stdout + compile_res.stderr
                run_res = subprocess.run(["java", "-cp", tmp, "Main"], capture_output=True, text=True, timeout=3)
                return run_res.stdout + run_res.stderr

            if language == "cpp":
                path = os.path.join(tmp, "main.cpp")
                exe = os.path.join(tmp, "main.exe")
                with open(path, "w") as f: f.write(code)
                compile_res = subprocess.run(["g++", path, "-o", exe], capture_output=True, text=True, timeout=5)
                if compile_res.returncode != 0:
                    return compile_res.stdout + compile_res.stderr
                run_res = subprocess.run([exe], capture_output=True, text=True, timeout=3)
                return run_res.stdout + run_res.stderr

            return "Cannot run this language here."

    except subprocess.TimeoutExpired:
        return "Execution timed out."
    except Exception as e:
        return f"Error: {e}"


# ============================================================
# CHAT ROUTE (AI + code generator + lookup)
# ============================================================
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    text = (data.get("message") or "").strip()

    if not text:
        return jsonify({"reply": "Say something and I’ll help!"})

    # 1. Code generator
    code_reply = generate_code(text)
    if code_reply:
        return jsonify({"reply": code_reply})

    # 2. Web lookup
    online = lookup_online(text)
    if online and "couldn't find" not in online:
        return jsonify({"reply": online})

    # 3. Fallback AI
    return jsonify({"reply": "I can help with coding, scripts, websites, and questions. Try asking me to generate code!"})


# ============================================================
# RUN ENDPOINT
# ============================================================
@app.route("/api/run", methods=["POST"])
def run():
    data = request.get_json() or {}
    language = data.get("language")
    code = data.get("code") or ""

    if not language or not code.strip():
        return jsonify({"output": "Provide language and code to run."})

    output = run_code(language, code)
    return jsonify({"output": output})


# ============================================================
# HEALTH CHECK
# ============================================================
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ============================================================
# RUN SERVER (PORT 5000)
# ============================================================
if __name__ == "__main__":
    print("Code Century backend running on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False)
