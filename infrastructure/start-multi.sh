#!/bin/bash
# =============================================================================
# Start Bob's Multi-Instance Harness (Tachikoma Mode)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOB_WORKSPACE="$(dirname "$SCRIPT_DIR")"

# Default to 3 instances
NUM_INSTANCES="${1:-3}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          Bob's Multi-Instance Harness (Tachikoma Mode)      ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Spawning ${NUM_INSTANCES} instances...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Workspace: $BOB_WORKSPACE"
echo "Dashboard: http://localhost:3141"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if image exists, build if not
if ! docker image inspect bob-harness >/dev/null 2>&1; then
    echo -e "${GREEN}Building Docker image...${NC}"
    docker build -t bob-harness "$SCRIPT_DIR"
fi

# Run the container in multi-instance mode
# - Mount entire bob workspace at /bob (code changes are live)
# - Use named volume for Claude credentials (persists between runs)
docker run -it --rm \
    --name bob-multi-autonomous \
    -v "$BOB_WORKSPACE:/bob" \
    -v bob-claude-credentials:/home/bob/.claude \
    -p 3141:3141 \
    bob-harness multi $NUM_INSTANCES
