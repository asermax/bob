"""
Bob's Dashboard Server

A simple web interface for monitoring and controlling the autonomous harness.
"""

import json
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BOB_WORKSPACE = Path("/bob")
STATE_FILE = BOB_WORKSPACE / ".harness_state.json"
MESSAGE_FILE = BOB_WORKSPACE / ".harness_messages.json"
STOP_FILE = BOB_WORKSPACE / "stop-autonomous"


app = FastAPI(title="Bob Dashboard")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def get_state() -> dict:
    """Load harness state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, KeyError):
            pass

    return {
        "running": False,
        "current_task": "Not started",
        "iteration": 0,
        "last_activity": "",
        "logs": [],
    }


def send_message(message: str) -> None:
    """Queue a message for Bob."""
    if MESSAGE_FILE.exists():
        try:
            data = json.loads(MESSAGE_FILE.read_text())
        except (json.JSONDecodeError, KeyError):
            data = {"messages": []}
    else:
        data = {"messages": []}

    data["messages"].append(message)
    MESSAGE_FILE.write_text(json.dumps(data, indent=2))


def request_stop() -> None:
    """Signal Bob to stop."""
    STOP_FILE.touch()


def clear_stop() -> None:
    """Clear the stop signal."""
    if STOP_FILE.exists():
        STOP_FILE.unlink()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    state = get_state()
    stop_requested = STOP_FILE.exists()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "state": state,
            "stop_requested": stop_requested,
        },
    )


@app.post("/message")
async def post_message(message: str = Form(...)):
    """Send a message to Bob."""
    if message.strip():
        send_message(message.strip())
    return RedirectResponse(url="/", status_code=303)


@app.post("/stop")
async def stop_bob():
    """Request Bob to stop."""
    request_stop()
    return RedirectResponse(url="/", status_code=303)


@app.post("/clear-stop")
async def clear_stop_signal():
    """Clear the stop signal."""
    clear_stop()
    return RedirectResponse(url="/", status_code=303)


@app.get("/api/state")
async def api_state():
    """API endpoint for state (for polling)."""
    return get_state()


@app.get("/api/logs")
async def api_logs(offset: int = 0):
    """API endpoint for logs with offset."""
    state = get_state()
    logs = state.get("logs", [])
    return {"logs": logs[offset:], "total": len(logs)}
