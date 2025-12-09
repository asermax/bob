#!/bin/bash
# =============================================================================
# Restart Services
# =============================================================================
# Allows Bob to restart the dashboard or harness without manual intervention.
# This enables autonomous iteration on infrastructure code.
# =============================================================================

set -e

SERVICE="${1:-dashboard}"

case "$SERVICE" in
    dashboard)
        echo "Restarting dashboard..."
        # The dashboard runs with uvicorn --reload, so just touching the file triggers reload
        touch /bob/infrastructure/dashboard/server.py
        echo "Dashboard will reload automatically (uvicorn --reload is active)"
        ;;

    harness)
        echo "Restarting harness requires container restart..."
        echo "Current harness will complete this iteration, then new code will run on next iteration."
        echo "No action needed - harness reloads code fresh each iteration."
        ;;

    both)
        echo "Restarting dashboard..."
        touch /bob/infrastructure/dashboard/server.py
        echo "Dashboard will reload automatically."
        echo "Harness reloads fresh code each iteration automatically."
        ;;

    *)
        echo "Unknown service: $SERVICE"
        echo "Usage: restart-services.sh [dashboard|harness|both]"
        exit 1
        ;;
esac
