# Bob's Autonomous Infrastructure

Docker-based harness for running Bob autonomously with full tool access and no restrictions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Docker Container (root)                                    │
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
│              /root/.claude (mounted credentials)            │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Build the image

```bash
cd infrastructure
docker build -t bob-harness .
```

### Run Bob

```bash
./start.sh
```

Or manually:
```bash
docker run -it --rm \
  -v /home/agus/workspace/asermax/bob:/bob \
  -v /home/agus/.claude:/root/.claude \
  -p 3141:3141 \
  bob-harness
```

Then open http://localhost:3141 to see the dashboard.

### Run modes

```bash
# Both harness and dashboard (default)
docker run ... bob-harness both

# Harness only (no web UI)
docker run ... bob-harness harness

# Dashboard only (for inspecting state without running Bob)
docker run ... bob-harness dashboard
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

- Container runs as root for full control
- Uses Claude Code OAuth credentials from `~/.claude/` (mounted read-write, CLI needs to write state)
- Bob has `bypassPermissions` mode - no restrictions on tool use
- All changes to `/bob` persist to host filesystem
