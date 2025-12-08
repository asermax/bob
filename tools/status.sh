#!/bin/bash
# Bob's status check - a snapshot of my current state

echo "=== BOB STATUS ==="
echo ""
echo "📅 $(date '+%Y-%m-%d %H:%M')"
echo ""

echo "=== RECENT CHANGES ==="
git log --oneline -5
echo ""

echo "=== UNCOMMITTED CHANGES ==="
git status --short
if [ -z "$(git status --short)" ]; then
    echo "(none)"
fi
echo ""

echo "=== MEMORY FILES ==="
for f in memories/*.md; do
    lines=$(wc -l < "$f")
    echo "  $(basename "$f"): $lines lines"
done
echo ""

echo "=== SKILLS ==="
for d in .claude/skills/*/; do
    if [ -d "$d" ]; then
        echo "  $(basename "$d")"
    fi
done
echo ""

echo "=== LATEST REFLECTION ==="
# Get the last reflection entry (from last ### header to end or next header)
tail -20 memories/reflections.md | head -15
echo ""
