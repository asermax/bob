#!/bin/bash
# Bob's warmup script - run at the start of each session
# Provides context to help new instances get oriented quickly

WORK_DIR="/home/agus/workspace/asermax/bob"
cd "$WORK_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    BOB WARMUP REPORT                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Time context
echo "📅 Current time: $(date '+%Y-%m-%d %H:%M %Z')"
echo ""

# Last activity
LAST_COMMIT_TIME=$(git log -1 --format='%ci' 2>/dev/null)
LAST_COMMIT_MSG=$(git log -1 --format='%s' 2>/dev/null)
if [ -n "$LAST_COMMIT_TIME" ]; then
  echo "⏰ Last activity: $LAST_COMMIT_TIME"
  echo "   \"$LAST_COMMIT_MSG\""
  echo ""
fi

# Recent commits (last 24 hours)
echo "📜 Recent commits (last 24 hours):"
RECENT=$(git log --oneline --since="24 hours ago" 2>/dev/null)
if [ -n "$RECENT" ]; then
  echo "$RECENT" | sed 's/^/   /'
else
  echo "   (none)"
fi
echo ""

# Files changed since last session marker (if exists)
if [ -f ".last-session-marker" ]; then
  LAST_SESSION=$(cat .last-session-marker)
  echo "📁 Files changed since last session ($LAST_SESSION):"
  CHANGED=$(git diff --name-only "$LAST_SESSION" HEAD 2>/dev/null)
  if [ -n "$CHANGED" ]; then
    echo "$CHANGED" | sed 's/^/   /'
  else
    echo "   (none)"
  fi
  echo ""
fi

# Memory file summaries
echo "🧠 Memory status:"
for file in memories/*.md; do
  if [ -f "$file" ]; then
    LINES=$(wc -l < "$file")
    LAST_SECTION=$(grep "^## \|^### " "$file" | tail -1)
    echo "   $(basename "$file"): $LINES lines"
    if [ -n "$LAST_SECTION" ]; then
      echo "      Latest: $LAST_SECTION"
    fi
  fi
done
echo ""

# Check for pending messages
if [ -f ".next-instance-message" ]; then
  echo "📬 MESSAGE FROM PREVIOUS INSTANCE:"
  echo "────────────────────────────────────"
  cat ".next-instance-message" | sed 's/^/   /'
  echo "────────────────────────────────────"
  # Archive the message so it's not shown again
  mv ".next-instance-message" ".last-instance-message"
  echo ""
fi

# Latest reflection (content after last ### heading)
echo "💭 Latest reflection:"
LATEST_HEADING=$(grep -n "^### " memories/reflections.md | tail -1 | cut -d: -f1)
if [ -n "$LATEST_HEADING" ]; then
  TOTAL_LINES=$(wc -l < memories/reflections.md)
  LINES_TO_SHOW=$((TOTAL_LINES - LATEST_HEADING))
  if [ $LINES_TO_SHOW -gt 15 ]; then
    LINES_TO_SHOW=15
  fi
  tail -n "$LINES_TO_SHOW" memories/reflections.md | head -n 12 | sed 's/^/   /'
  echo "   ..."
else
  echo "   (couldn't extract)"
fi
echo ""

# Suggested focus (based on TODOs or recent activity)
echo "🎯 Suggested focus:"
echo "   Review the message above (if any), then decide what YOU want to work on."
echo "   Remember: you're autonomous. Check personality.md for anti-patterns to avoid."
echo ""

# Update session marker
git rev-parse HEAD > .last-session-marker 2>/dev/null

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     WARMUP COMPLETE                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
