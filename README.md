# Offline AI Assistant

A lightweight browser-based assistant built with Flask. It runs locally, does
not require an API key, and includes basic chat, math, unit conversion,
time/date, jokes, fun facts, and a small built-in knowledge base.

## Requirements

- Python 3.9 or newer
- `pip` (normally included with Python)

## Download and run

1. Download this repository as a ZIP and extract it, or clone it with Git:

   ```bash
   git clone https://github.com/cfbhtml/AI-.git
   cd AI-
   ```

2. Open a terminal in the project folder and enter the application directory:

   ```bash
   cd "ai project part 2"
   ```

3. Install all required Python packages with one command:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the application:

   ```bash
   python server.py
   ```

5. Open <http://127.0.0.1:5000/> in a browser.

Stop the server by pressing `Ctrl+C` in the terminal.

## Optional: use a virtual environment

Using a virtual environment keeps this project's packages separate from other
Python projects.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python server.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 server.py
```

## Project files

- `ai project part 2/server.py` — Flask server and assistant logic
- `ai project part 2/webai.html` — browser interface
- `ai project part 2/requirements.txt` — Python dependencies

## API endpoints

- `GET /` — opens the chat interface
- `POST /api/chat` — sends a message to the assistant
- `POST /api/clear` — clears an in-memory conversation
- `GET /api/health` — checks whether the server is running

## Troubleshooting

### `python` is not recognized

Install Python from <https://www.python.org/downloads/> and enable the option
to add Python to your system PATH. On macOS or Linux, try `python3` instead of
`python`.

### `ModuleNotFoundError: No module named 'flask'`

Run this command from inside `ai project part 2`:

```bash
python -m pip install -r requirements.txt
```

### Port 5000 is already in use

Stop the other program using port 5000, or change the port number at the bottom
of `server.py`, restart the server, and open that new port in the browser.

## Notes

- Conversations are stored only in memory and disappear when the server stops.
- The assistant works offline after its Python dependencies have been installed.
- No API key or paid external service is required.
