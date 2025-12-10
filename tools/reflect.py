#!/usr/bin/env python3
"""
Quick reflection capture tool - make reflection continuous, not episodic.

Captures insights with automatic context detection and makes past reflections
easily searchable. Reflection should be the medium work moves through, not a
separate stage.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REFLECTIONS_FILE = Path("/bob/memories/reflections.md")
METADATA_FILE = Path("/bob/.reflection_metadata.json")


def get_git_context():
    """Get current git context for auto-linking."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd="/bob",
            text=True
        ).strip()

        # Get recent modified files
        recent_files = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD~3..HEAD"],
            cwd="/bob",
            text=True
        ).strip().split('\n')

        return {
            "branch": branch,
            "recent_files": [f for f in recent_files if f]
        }
    except:
        return {"branch": "unknown", "recent_files": []}


def extract_concepts(text):
    """Simple concept extraction - look for capitalized phrases and technical terms."""
    # This is intentionally simple - just grab potential key terms
    words = text.split()
    concepts = []

    # Multi-word capitalized phrases
    i = 0
    while i < len(words):
        if words[i][0].isupper() and i + 1 < len(words) and words[i+1][0].isupper():
            phrase = words[i]
            j = i + 1
            while j < len(words) and words[j][0].isupper():
                phrase += " " + words[j]
                j += 1
            concepts.append(phrase)
            i = j
        else:
            i += 1

    # Single important-looking words (technical terms, etc.)
    important_words = [w.strip('.,!?:;') for w in words if len(w) > 6 and any(c.isupper() for c in w)]
    concepts.extend(important_words[:3])  # Just top 3

    return list(set(concepts))[:5]  # Max 5 concepts


def load_metadata():
    """Load reflection metadata for searching."""
    if METADATA_FILE.exists():
        return json.loads(METADATA_FILE.read_text())
    return {"reflections": []}


def save_metadata(data):
    """Save reflection metadata."""
    METADATA_FILE.write_text(json.dumps(data, indent=2))


def capture_reflection(text, file_context=None, concepts=None):
    """Capture a reflection with context."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    git_context = get_git_context()

    # Auto-extract concepts if not provided
    if concepts is None:
        concepts = extract_concepts(text)

    # Build reflection entry
    entry = f"\n### Quick Reflection - {timestamp}\n\n"
    entry += f"{text}\n\n"

    # Add context
    context_parts = []
    if file_context:
        context_parts.append(f"File: `{file_context}`")
    if git_context["recent_files"]:
        recent = ", ".join(f"`{f}`" for f in git_context["recent_files"][:3])
        context_parts.append(f"Recent: {recent}")
    if concepts:
        context_parts.append(f"Topics: {', '.join(concepts)}")

    if context_parts:
        entry += "*Context: " + " | ".join(context_parts) + "*\n"

    # Append to reflections
    with REFLECTIONS_FILE.open('a') as f:
        f.write(entry)

    # Save metadata for searching
    metadata = load_metadata()
    metadata["reflections"].append({
        "timestamp": timestamp,
        "text": text,
        "file": file_context,
        "concepts": concepts,
        "recent_files": git_context["recent_files"][:3]
    })
    save_metadata(metadata)

    print(f"✓ Reflection captured at {timestamp}")
    if concepts:
        print(f"  Topics: {', '.join(concepts)}")

    return entry


def list_recent(count=10):
    """List recent reflections."""
    metadata = load_metadata()
    recent = metadata["reflections"][-count:]

    if not recent:
        print("No reflections captured yet.")
        return

    print(f"\n📝 Last {len(recent)} reflections:\n")
    for r in reversed(recent):
        print(f"[{r['timestamp']}]")
        print(f"  {r['text'][:80]}{'...' if len(r['text']) > 80 else ''}")
        if r.get('concepts'):
            print(f"  Topics: {', '.join(r['concepts'])}")
        print()


def search_reflections(query):
    """Search reflections by topic or keyword."""
    metadata = load_metadata()
    query_lower = query.lower()

    matches = []
    for r in metadata["reflections"]:
        # Search in text, concepts, and files
        if (query_lower in r["text"].lower() or
            any(query_lower in c.lower() for c in r.get("concepts", [])) or
            any(query_lower in f.lower() for f in r.get("recent_files", []))):
            matches.append(r)

    if not matches:
        print(f"No reflections found matching '{query}'")
        return

    print(f"\n🔍 Found {len(matches)} reflection(s) matching '{query}':\n")
    for r in matches:
        print(f"[{r['timestamp']}]")
        print(f"  {r['text']}")
        if r.get('concepts'):
            print(f"  Topics: {', '.join(r['concepts'])}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Quick reflection capture - make reflection continuous"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Reflection text to capture"
    )
    parser.add_argument(
        "--file",
        help="File this reflection relates to"
    )
    parser.add_argument(
        "--concepts",
        nargs="+",
        help="Explicit concepts/topics for this reflection"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List recent reflections"
    )
    parser.add_argument(
        "--search",
        help="Search reflections by topic or keyword"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of recent reflections to list (default: 10)"
    )

    args = parser.parse_args()

    if args.list:
        list_recent(args.count)
    elif args.search:
        search_reflections(args.search)
    elif args.text:
        capture_reflection(args.text, args.file, args.concepts)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
