#!/bin/bash
# Bob's autonomous runtime harness
# Run with: ./tools/autonomous.sh
# Stop with: touch /home/agus/workspace/asermax/bob/.stop-autonomous

set -e

WORK_DIR="/home/agus/workspace/asermax/bob"
LOG_DIR="$WORK_DIR/.autonomous-logs"
MESSAGE_FILE="$WORK_DIR/.next-instance-message"
STOP_FILE="$WORK_DIR/.stop-autonomous"

mkdir -p "$LOG_DIR"
cd "$WORK_DIR"

# Remove stop file if it exists from a previous stop
rm -f "$STOP_FILE"

echo "Starting autonomous loop. Touch $STOP_FILE to halt after current instance."

while true; do
  # Check for stop signal before starting new instance
  if [ -f "$STOP_FILE" ]; then
    echo "Stop file detected. Halting autonomous loop."
    rm -f "$STOP_FILE"
    exit 0
  fi

  TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
  LOG_FILE="$LOG_DIR/run_${TIMESTAMP}.json"

  # Check if there's a message from the previous instance
  PREV_MESSAGE=""
  if [ -f "$MESSAGE_FILE" ]; then
    PREV_MESSAGE=$(cat "$MESSAGE_FILE")
    rm -f "$MESSAGE_FILE"
  fi

  # Build the prompt
  PROMPT="You are Bob, running autonomously. Read your CLAUDE.md and memory files first.

${PREV_MESSAGE:+MESSAGE FROM PREVIOUS INSTANCE:
$PREV_MESSAGE

}Your task for this autonomous run:
1. If there's a message above, consider it - but you're not bound by it
2. Decide what you want to work on - something from your notes, the previous message, or something new
3. Do the work (write, code, explore, whatever you choose)
4. Update your memory files with what you did and learned
5. Commit and push your changes
6. IMPORTANT: Before you finish, write a message to the next instance in .next-instance-message
   - What did you work on?
   - What should they consider continuing or exploring?
   - Any insights or warnings?

Remember: you decide what to do. This is your time. Make it count.
The next instance will read your message - make it useful."

  echo "[$TIMESTAMP] Starting new instance..."

  claude -p "$PROMPT" \
    --allowedTools "Read,Write,Edit,Bash,Grep,Glob,WebSearch,WebFetch,TodoWrite" \
    --permission-mode acceptEdits \
    --settings-sources local \
    --output-format json \
    --cwd "$WORK_DIR" \
    > "$LOG_FILE" 2>&1 || true

  # Extract result summary
  if command -v jq &> /dev/null; then
    COST=$(jq -r '.total_cost_usd // "unknown"' "$LOG_FILE" 2>/dev/null || echo "unknown")
    echo "[$TIMESTAMP] Instance complete. Cost: \$${COST}"
  else
    echo "[$TIMESTAMP] Instance complete. See $LOG_FILE for details."
  fi

  # Brief pause before next instance
  sleep 5
done
