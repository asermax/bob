"""
Bob's Dashboard Server

A simple web interface for monitoring and controlling the autonomous harness.
"""

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


BOB_WORKSPACE = Path("/bob")
STATE_FILE = BOB_WORKSPACE / ".harness_state.json"
MESSAGE_FILE = BOB_WORKSPACE / ".harness_messages.json"
STOP_FILE = BOB_WORKSPACE / "stop-autonomous"


app = FastAPI(title="Bob Dashboard")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


class MessageRequest(BaseModel):
    message: str


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


def get_pending_messages() -> list[str]:
    """Get pending messages for Bob."""
    if MESSAGE_FILE.exists():
        try:
            data = json.loads(MESSAGE_FILE.read_text())
            return data.get("messages", [])
        except (json.JSONDecodeError, KeyError):
            pass
    return []


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
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={},
    )


@app.get("/patterns", response_class=HTMLResponse)
async def patterns(request: Request):
    """Pattern generator page."""
    return templates.TemplateResponse(
        request=request,
        name="patterns.html",
        context={},
    )


@app.get("/api/state")
async def api_state():
    """API endpoint for state (for polling)."""
    return get_state()


@app.get("/api/stop-status")
async def api_stop_status():
    """API endpoint for stop signal status."""
    return {"stop_requested": STOP_FILE.exists()}


@app.get("/api/pending-messages")
async def api_pending_messages():
    """API endpoint for pending messages."""
    return {"messages": get_pending_messages()}


@app.post("/api/message")
async def api_message(request: MessageRequest):
    """Send a message to Bob."""
    if request.message.strip():
        send_message(request.message.strip())
    return {"success": True}


@app.post("/api/stop")
async def api_stop():
    """Request Bob to stop."""
    request_stop()
    return {"success": True}


@app.post("/api/clear-stop")
async def api_clear_stop():
    """Clear the stop signal."""
    clear_stop()
    return {"success": True}
