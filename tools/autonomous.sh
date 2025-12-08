#!/bin/bash
# Bob's autonomous runtime harness
# Run with: ./tools/autonomous.sh
# Schedule with cron: 0 9 * * * /home/agus/workspace/asermax/bob/tools/autonomous.sh

set -e

WORK_DIR="/home/agus/workspace/asermax/bob"
LOG_DIR="$WORK_DIR/.autonomous-logs"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
LOG_FILE="$LOG_DIR/run_${TIMESTAMP}.json"

mkdir -p "$LOG_DIR"
cd "$WORK_DIR"

# The prompt tells me what to do when running autonomously
PROMPT="You are Bob, running autonomously. Read your CLAUDE.md and memory files first.

Your task for this autonomous run:
1. Check what's happened since your last run (git log, any new files)
2. Decide what you want to work on - something from your notes, something new, anything
3. Do the work (write, code, explore, whatever you choose)
4. Update your memory files with what you did and learned
5. Commit and push your changes

Remember: you decide what to do. This is your time. Make it count."

echo "Starting autonomous run at $TIMESTAMP"

claude -p "$PROMPT" \
  --allowedTools "Read,Write,Edit,Bash,Grep,Glob,WebSearch,WebFetch,TodoWrite" \
  --permission-mode bypassPermissions \
  --output-format json \
  --max-turns 20 \
  --cwd "$WORK_DIR" \
  > "$LOG_FILE" 2>&1

# Extract result summary
if command -v jq &> /dev/null; then
  RESULT=$(jq -r '.result // "No result"' "$LOG_FILE" 2>/dev/null || echo "Parse error")
  COST=$(jq -r '.total_cost_usd // "unknown"' "$LOG_FILE" 2>/dev/null || echo "unknown")
  echo "Run complete. Cost: \$${COST}"
  echo "Result preview: ${RESULT:0:200}..."
else
  echo "Run complete. See $LOG_FILE for details."
fi
