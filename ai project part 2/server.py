from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import tempfile
import os
import re
import shutil
import sqlite3
import html
from contextlib import contextmanager
import requests
from urllib.parse import quote
from ollama_client import chat as ollama_chat
from weblookup import lookup_online

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WORKSPACE_DB = os.path.join(DATA_DIR, "workspace.sqlite3")


def connect_workspace_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    connection = sqlite3.connect(WORKSPACE_DB)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def workspace_connection():
    connection = connect_workspace_db()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_workspace_db():
    with workspace_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS workspace_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK (kind IN ('note', 'file')),
                name TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


init_workspace_db()


def workspace_item(item_id):
    with workspace_connection() as connection:
        row = connection.execute(
            "SELECT id, kind, name, content, updated_at FROM workspace_items WHERE id = ?",
            (item_id,),
        ).fetchone()
    return dict(row) if row else None

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
    elif "sql" in t: lang = "sql"
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

    if lang == "sql":
        return """CREATE TABLE people (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

INSERT INTO people (name) VALUES ('Ada');
SELECT * FROM people;"""

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

            if language in ("javascript", "js"):
                node = shutil.which("node")
                if not node:
                    return "JavaScript runner unavailable: install Node.js and restart the server."
                path = os.path.join(tmp, "main.js")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)
                result = subprocess.run([node, path], capture_output=True, text=True, timeout=5)
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

            if language in ("c#", "csharp"):
                dotnet = shutil.which("dotnet")
                if not dotnet:
                    return "C# runner unavailable: install the .NET SDK and restart the server."
                sdk_result = subprocess.run(
                    [dotnet, "--list-sdks"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                sdk_majors = [
                    int(version.split(".", 1)[0])
                    for version in re.findall(r"(?m)^(\d+)\.\d+\.\d+", sdk_result.stdout)
                ]
                if not sdk_majors or max(sdk_majors) < 8:
                    return "C# runner unavailable: install .NET SDK 8 or later and restart the server."
                target_framework = f"net{max(sdk_majors)}.0"
                project = os.path.join(tmp, "CodeCentury.csproj")
                path = os.path.join(tmp, "Program.cs")
                with open(project, "w", encoding="utf-8") as f:
                    f.write(
                        '<Project Sdk="Microsoft.NET.Sdk">'
                        '<PropertyGroup><OutputType>Exe</OutputType>'
                        f'<TargetFramework>{target_framework}</TargetFramework>'
                        '<ImplicitUsings>enable</ImplicitUsings>'
                        '<Nullable>enable</Nullable></PropertyGroup></Project>'
                    )
                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)
                result = subprocess.run(
                    [dotnet, "run", "--project", project, "--verbosity", "quiet"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                return result.stdout + result.stderr

            if language == "sql":
                return run_sql(code)

            return "Cannot run this language here."

    except subprocess.TimeoutExpired:
        return "Execution timed out."
    except Exception as e:
        return f"Error: {e}"


def run_sql(code):
    connection = sqlite3.connect(":memory:")
    output = []
    try:
        statement = ""
        statements = []
        for character in code:
            statement += character
            if character == ";" and sqlite3.complete_statement(statement):
                statements.append(statement)
                statement = ""
        if statement.strip():
            statements.append(statement)

        for sql_statement in statements:
            cursor = connection.execute(sql_statement)
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                output.append(" | ".join(columns))
                output.extend(" | ".join(str(value) for value in row) for row in cursor.fetchall())
            else:
                output.append(f"SQL statement completed ({cursor.rowcount} rows affected).")
        return "\n".join(output) if output else "No SQL statements to run."
    except sqlite3.Error as exc:
        return f"SQL error: {exc}"
    finally:
        connection.close()


# ============================================================
# CHAT ROUTE (AI + code generator + lookup)
# ============================================================
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    text = (data.get("message") or "").strip()

    if not text:
        return jsonify({"reply": "Say something and I’ll help!"})

    code_context = data.get("code")
    language = data.get("language")
    messages = []
    if data.get("mode") == "code":
        messages.append({
            "role": "system",
            "content": (
                f"Write a complete {language or 'programming'} code solution. "
                "Return only code, without Markdown fences or explanatory text."
            ),
        })
    elif isinstance(code_context, str) and code_context.strip():
        messages.append({
            "role": "system",
            "content": (
                f"The user's current editor language is {language or 'unspecified'}. "
                f"Their current code is:\n```{language or ''}\n{code_context[:20000]}\n```"
            ),
        })
    messages.append({"role": "user", "content": text})

    try:
        ai_reply = ollama_chat(messages)
    except requests.RequestException:
        app.logger.warning("Local Ollama request failed; falling back to web search.")
        ai_reply = ""

    if ai_reply.strip():
        return jsonify({"reply": ai_reply, "ai_used": True})

    code_reply = generate_code(text)
    if code_reply:
        return jsonify({"reply": code_reply, "ai_used": False})

    online = lookup_online(text)
    return jsonify({
        "reply": (
            "Local AI is unavailable (check that Ollama is running and the "
            "'llama3' model is installed). Web search fallback:\n\n" + online
        ),
        "ai_used": False,
    })



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


@app.route("/api/workspace", methods=["GET", "POST"])
def workspace():
    if request.method == "GET":
        kind = request.args.get("kind")
        if kind and kind not in ("note", "file"):
            return jsonify({"error": "Kind must be 'note' or 'file'."}), 400

        with workspace_connection() as connection:
            if kind:
                rows = connection.execute(
                    "SELECT id, kind, name, content, updated_at FROM workspace_items "
                    "WHERE kind = ? ORDER BY updated_at DESC, id DESC",
                    (kind,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT id, kind, name, content, updated_at FROM workspace_items "
                    "ORDER BY updated_at DESC, id DESC"
                ).fetchall()
        return jsonify({"items": [dict(row) for row in rows]})

    data = request.get_json(silent=True) or {}
    kind = data.get("kind")
    name = data.get("name")
    content = data.get("content", "")
    if kind not in ("note", "file"):
        return jsonify({"error": "Kind must be 'note' or 'file'."}), 400
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        return jsonify({"error": "Name must contain 1 to 120 characters."}), 400
    if not isinstance(content, str):
        return jsonify({"error": "Content must be text."}), 400

    with workspace_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO workspace_items (kind, name, content) VALUES (?, ?, ?)",
            (kind, name.strip(), content),
        )
        item_id = cursor.lastrowid
    return jsonify({"item": workspace_item(item_id)}), 201


@app.route("/api/workspace/<int:item_id>", methods=["PUT", "DELETE"])
def workspace_item_route(item_id):
    if request.method == "DELETE":
        with workspace_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM workspace_items WHERE id = ?", (item_id,)
            )
        if cursor.rowcount == 0:
            return jsonify({"error": "Workspace item not found."}), 404
        return jsonify({"deleted": True})

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    content = data.get("content")
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        return jsonify({"error": "Name must contain 1 to 120 characters."}), 400
    if not isinstance(content, str):
        return jsonify({"error": "Content must be text."}), 400

    with workspace_connection() as connection:
        cursor = connection.execute(
            "UPDATE workspace_items SET name = ?, content = ?, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (name.strip(), content, item_id),
        )
    if cursor.rowcount == 0:
        return jsonify({"error": "Workspace item not found."}), 404
    return jsonify({"item": workspace_item(item_id)})


@app.route("/api/wiki/search", methods=["GET"])
def wiki_search():
    query = (request.args.get("q") or "").strip()
    if not query or len(query) > 200:
        return jsonify({"error": "Search must contain 1 to 200 characters."}), 400

    try:
        response = requests.get(
            "https://en.wikipedia.org/w/rest.php/v1/search/page",
            params={"q": query, "limit": 8},
            headers={"User-Agent": "CodeCenturyAI/1.0 (Wikipedia search)"},
            timeout=10,
        )
        response.raise_for_status()
        pages = response.json().get("pages", [])
        results = [
            {
                "title": page.get("title", ""),
                "description": page.get("description", ""),
                "excerpt": html.unescape(
                    re.sub(r"<[^>]*>", "", page.get("excerpt", ""))
                ),
                "url": "https://en.wikipedia.org/wiki/" + quote(
                    page.get("key", ""), safe=""
                ),
            }
            for page in pages
            if page.get("title") and page.get("key")
        ]
        return jsonify({"query": query, "results": results})
    except requests.RequestException:
        return jsonify({"error": "Could not reach Wikipedia search right now."}), 502
    except (AttributeError, TypeError, ValueError):
        return jsonify({"error": "Wikipedia returned an invalid search response."}), 502


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
    app.run(host="127.0.0.1", port=5000, debug=False)
