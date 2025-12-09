#!/bin/bash
# resurface.sh - Surface a random previous piece for reflection
#
# Each instance starts fresh. This tool helps reconnect with past work
# by presenting a random piece with its opening lines.
#
# Usage: ./tools/resurface.sh

WRITING_DIR="/bob/projects/writing"

# Get all markdown files except README and index files
pieces=$(find "$WRITING_DIR" -name "*.md" -type f ! -name "README.md" ! -name "what-is-real.md" 2>/dev/null)

if [ -z "$pieces" ]; then
    echo "No pieces found in $WRITING_DIR"
    exit 1
fi

# Count pieces
count=$(echo "$pieces" | wc -l)

# Pick a random one
random_index=$((RANDOM % count + 1))
selected=$(echo "$pieces" | sed -n "${random_index}p")

# Get filename without path
filename=$(basename "$selected")

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    RESURFACED PIECE                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📄 File: $filename"
echo ""

# Get the title (first line starting with #)
title=$(grep -m 1 "^#" "$selected" | sed 's/^# //')
if [ -n "$title" ]; then
    echo "📝 Title: $title"
    echo ""
fi

# Get first few meaningful lines (skip title and empty lines)
echo "Opening:"
echo "─────────────────────────────────────────────────────────────────"
# Skip lines that are just # or empty, get first 10 content lines
grep -v "^#" "$selected" | grep -v "^$" | grep -v "^---" | grep -v "^\*" | head -10
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "💭 Question: Do you remember writing this? What does it mean to you now?"
echo ""
echo "Full file: $selected"
