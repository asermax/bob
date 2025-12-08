# Bob's Autonomous Infrastructure

Docker-based harness for running Bob autonomously with full tool access and no restrictions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Docker Container                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  harness.py - Claude Agent SDK autonomous loop        │  │
│  │  - Runs Bob with full permissions (bypassPermissions) │  │
│  │  - Self-modifiable                                    │  │
│  │  - Checks for messages from Agus between iterations   │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  dashboard/ - FastAPI web UI                          │  │
│  │  - View status and logs                               │  │
│  │  - Send messages to Bob                               │  │
│  │  - Stop/control execution                             │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                  │
│              /bob (mounted workspace)                       │
│              /home/bob/.claude (named volume - credentials) │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Build the image

```bash
cd infrastructure
docker build -t bob-harness .
```

### First-time setup: Login

Before running Bob, you need to authenticate Claude Code inside the container:

```bash
./start.sh login
```

This will start the OAuth flow. Open the URL in your browser to authenticate.
Credentials are stored in a named Docker volume (`bob-claude-credentials`) and persist between runs.

### Run Bob

```bash
./start.sh
```

Then open http://localhost:3141 to see the dashboard.

### Run modes

```bash
# Both harness and dashboard (default)
./start.sh both

# Harness only (no web UI)
./start.sh harness

# Dashboard only (for inspecting state without running Bob)
./start.sh dashboard

# Login to Claude Code (first-time setup)
./start.sh login

# Interactive shell for debugging
./start.sh shell
```

## Files

- `harness.py` - Main autonomous loop using Claude Agent SDK
- `dashboard/server.py` - FastAPI server for web UI
- `dashboard/templates/dashboard.html` - Dashboard template
- `Dockerfile` - Multi-stage build with uv
- `entrypoint.sh` - Container entrypoint
- `pyproject.toml` - Python dependencies

## State Files

The harness creates these files in `/bob` (your mounted workspace):

- `.harness_state.json` - Current status, iteration count, logs
- `.harness_messages.json` - Message queue from dashboard to Bob
- `stop-autonomous` - Touch this file to signal Bob to stop

## Controlling Bob

### Via dashboard
- Open http://localhost:3141
- Send messages using the text input
- Click "Stop Bob" to request graceful shutdown

### Via filesystem
```bash
# Stop Bob
touch /home/agus/workspace/asermax/bob/stop-autonomous

# Send a message
echo '{"messages": ["Hey Bob, check out this thing"]}' > /home/agus/workspace/asermax/bob/.harness_messages.json
```

## Development

### Rebuild after changes

```bash
docker build -t bob-harness .
```

### Run locally without Docker (for debugging)

```bash
cd infrastructure
uv venv
uv pip install -e .
BOB_WORKSPACE=/home/agus/workspace/asermax/bob python harness.py
```

## Notes

- Container runs processes as non-root user 'bob' (required for --dangerously-skip-permissions)
- Credentials stored in Docker named volume `bob-claude-credentials` (run `./start.sh login` first)
- Bob has `bypassPermissions` mode - no restrictions on tool use
- All changes to `/bob` persist to host filesystem
- To reset credentials: `docker volume rm bob-claude-credentials`
