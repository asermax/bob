#!/bin/bash
# =============================================================================
# Start Bob's Autonomous Harness
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB_WORKSPACE="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Bob's Autonomous Harness${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Workspace: $BOB_WORKSPACE"
echo "Dashboard: http://localhost:3141"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if image exists, build if not
if ! docker image inspect bob-harness >/dev/null 2>&1; then
    echo -e "${GREEN}Building Docker image...${NC}"
    docker build -t bob-harness "$SCRIPT_DIR"
fi

# Run the container
# - Mount entire bob workspace at /bob (code changes are live)
# - Use named volume for Claude credentials (persists between runs)
docker run -it --rm \
    --name bob-autonomous \
    -v "$BOB_WORKSPACE:/bob" \
    -v bob-claude-credentials:/home/bob/.claude \
    -p 3141:3141 \
    bob-harness "$@"
