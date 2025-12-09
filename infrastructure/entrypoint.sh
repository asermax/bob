#!/bin/bash
# =============================================================================
# Bob's Harness Entrypoint
# =============================================================================
# Runs harness as non-root user 'bob' to allow --dangerously-skip-permissions.
# Harness and dashboard code are mounted from /bob/infrastructure/
# Credentials persist in named volume at /home/bob/.claude
# =============================================================================

set -e

MODE="${1:-both}"

# Ensure bob owns the credentials directory (it's a named volume)
chown -R bob:bob /home/bob/.claude 2>/dev/null || true

# Fix permissions on harness state files (may have been created by different user)
chown bob:bob /bob/.harness_state.json 2>/dev/null || true
chown bob:bob /bob/.harness_messages.json 2>/dev/null || true

# Configure SSH if key exists
if [ -f /home/bob/.claude/id_ed25519 ]; then
    mkdir -p /home/bob/.ssh
    cp /home/bob/.claude/id_ed25519 /home/bob/.ssh/id_ed25519
    cp /home/bob/.claude/id_ed25519.pub /home/bob/.ssh/id_ed25519.pub
    chmod 700 /home/bob/.ssh
    chmod 600 /home/bob/.ssh/id_ed25519
    chown -R bob:bob /home/bob/.ssh
    # Add GitHub to known hosts
    ssh-keyscan github.com >> /home/bob/.ssh/known_hosts 2>/dev/null
fi

# Configure git for bob user
su-exec bob git config --global user.email "bob@autonomous"
su-exec bob git config --global user.name "Bob"

# Ensure bob can write to workspace (but don't recurse - too slow and changes git files)
# The harness only needs to write to specific files, not the whole workspace

case "$MODE" in
    harness)
        echo "Starting Bob's autonomous harness..."
        exec su-exec bob env HOME=/home/bob python3 /bob/infrastructure/harness.py
        ;;

    dashboard)
        echo "Starting dashboard on port 3141..."
        cd /bob/infrastructure
        exec su-exec bob env HOME=/home/bob uvicorn dashboard.server:app --host 0.0.0.0 --port 3141 --reload
        ;;

    both)
        echo "Starting Bob's harness and dashboard..."

        # Start dashboard in background as bob user
        cd /bob/infrastructure
        su-exec bob env HOME=/home/bob uvicorn dashboard.server:app --host 0.0.0.0 --port 3141 --reload &
        DASHBOARD_PID=$!

        # Give dashboard a moment to start
        sleep 2

        # Start harness as bob user (required for bypass permissions)
        su-exec bob env HOME=/home/bob python3 /bob/infrastructure/harness.py

        # If harness exits, also stop dashboard
        kill $DASHBOARD_PID 2>/dev/null || true
        ;;

    login)
        echo "Starting Claude Code login..."
        exec su-exec bob env HOME=/home/bob claude login
        ;;

    check)
        echo "Checking Claude Code authentication..."
        su-exec bob env HOME=/home/bob claude -p "Say 'Authentication working!' and nothing else"
        ;;

    shell)
        echo "Starting interactive shell as bob..."
        exec su-exec bob env HOME=/home/bob /bin/bash
        ;;

    *)
        echo "Unknown mode: $MODE"
        echo "Usage: entrypoint.sh [harness|dashboard|both|login|shell]"
        exit 1
        ;;
esac
