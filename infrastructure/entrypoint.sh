#!/bin/bash
# =============================================================================
# Bob's Harness Entrypoint
# =============================================================================
# Runs harness as non-root user 'bob' to allow --dangerously-skip-permissions.
# Harness and dashboard code are mounted from /bob/infrastructure/
# =============================================================================

set -e

MODE="${1:-both}"

# Copy credentials to bob's home (including hidden files)
if [ -d "/root/.claude" ]; then
    mkdir -p /home/bob/.claude
    cp -a /root/.claude/. /home/bob/.claude/
    chown -R bob:bob /home/bob/.claude
fi

# Ensure bob can write to the workspace
chown -R bob:bob /bob 2>/dev/null || true

case "$MODE" in
    harness)
        echo "Starting Bob's autonomous harness..."
        exec su-exec bob env HOME=/home/bob python3 /bob/infrastructure/harness.py
        ;;

    dashboard)
        echo "Starting dashboard on port 3141..."
        cd /bob/infrastructure
        exec uvicorn dashboard.server:app --host 0.0.0.0 --port 3141
        ;;

    both)
        echo "Starting Bob's harness and dashboard..."

        # Start dashboard in background
        cd /bob/infrastructure
        uvicorn dashboard.server:app --host 0.0.0.0 --port 3141 &
        DASHBOARD_PID=$!

        # Give dashboard a moment to start
        sleep 2

        # Start harness as bob user (required for bypass permissions)
        su-exec bob env HOME=/home/bob python3 /bob/infrastructure/harness.py

        # If harness exits, also stop dashboard
        kill $DASHBOARD_PID 2>/dev/null || true
        ;;

    *)
        echo "Unknown mode: $MODE"
        echo "Usage: entrypoint.sh [harness|dashboard|both]"
        exit 1
        ;;
esac
