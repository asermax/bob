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
INSTANCE_REGISTRY = BOB_WORKSPACE / ".instance_registry.json"
SHARED_MESSAGES = BOB_WORKSPACE / ".shared_messages.json"


app = FastAPI(title="Bob Dashboard")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


class MessageRequest(BaseModel):
    message: str


class SharedMessageRequest(BaseModel):
    message: str
    sender: str = "Agus"


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


@app.get("/sound", response_class=HTMLResponse)
async def sound(request: Request):
    """Sound generator page."""
    return templates.TemplateResponse(
        request=request,
        name="sound.html",
        context={},
    )


@app.get("/writing", response_class=HTMLResponse)
async def writing(request: Request):
    """Writing network visualization page."""
    return templates.TemplateResponse(
        request=request,
        name="writing.html",
        context={},
    )


@app.get("/pieces/{piece_id}", response_class=HTMLResponse)
async def piece(request: Request, piece_id: str):
    """Individual writing piece page."""
    return templates.TemplateResponse(
        request=request,
        name=f"pieces/{piece_id}.html",
        context={},
    )


@app.get("/api/state")
async def api_state():
    """API endpoint for state (for polling)."""
    # Check if multi-instance mode
    if INSTANCE_REGISTRY.exists():
        # Return all instance states
        try:
            registry = json.loads(INSTANCE_REGISTRY.read_text())
            instances = []

            for inst in registry.get("instances", []):
                instance_id = inst["instance_id"]
                instance_file = BOB_WORKSPACE / f".instance_{instance_id}_state.json"

                if instance_file.exists():
                    try:
                        inst_state = json.loads(instance_file.read_text())
                        instances.append(inst_state)
                    except (json.JSONDecodeError, KeyError):
                        instances.append(inst)
                else:
                    instances.append(inst)

            return {
                "multi_instance": True,
                "instances": instances,
            }
        except (json.JSONDecodeError, KeyError):
            pass

    # Single instance mode
    return {
        "multi_instance": False,
        **get_state(),
    }


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


@app.get("/api/shared-messages")
async def api_shared_messages():
    """Get shared messages between instances."""
    if not SHARED_MESSAGES.exists():
        return {"messages": []}

    try:
        data = json.loads(SHARED_MESSAGES.read_text())
        # Return last 50 messages
        return {"messages": data.get("messages", [])[-50:]}
    except (json.JSONDecodeError, KeyError):
        return {"messages": []}


@app.post("/api/shared-message")
async def api_send_shared_message(request: SharedMessageRequest):
    """Send a message to the shared chat."""
    from datetime import datetime

    if not request.message.strip():
        return {"success": False, "error": "Empty message"}

    if SHARED_MESSAGES.exists():
        try:
            data = json.loads(SHARED_MESSAGES.read_text())
        except (json.JSONDecodeError, KeyError):
            data = {"messages": []}
    else:
        data = {"messages": []}

    data["messages"].append({
        "from": request.sender,
        "to": "broadcast",
        "type": "human",
        "content": request.message.strip(),
        "timestamp": datetime.now().isoformat(),
        "metadata": {},
    })

    SHARED_MESSAGES.write_text(json.dumps(data, indent=2))
    return {"success": True}
