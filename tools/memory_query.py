#!/usr/bin/env python3
"""
Memory Query System - Search and analyze Bob's memory files

Provides semantic search over reflections, learnings, conversations, and writing.
Can answer questions about past thoughts, track concept evolution, and find connections.

Usage:
    ./memory_query.py search "topic or question"
    ./memory_query.py timeline "concept"
    ./memory_query.py related "concept"
    ./memory_query.py stats
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys

BASE_DIR = Path("/bob")
MEMORIES_DIR = BASE_DIR / "memories"
PROJECTS_DIR = BASE_DIR / "projects"
REFLECTION_METADATA = BASE_DIR / ".reflection_metadata.json"

def load_reflection_metadata():
    """Load structured reflection metadata"""
    if not REFLECTION_METADATA.exists():
        return []
    with open(REFLECTION_METADATA) as f:
        data = json.load(f)
        return data.get('reflections', [])

def load_file_content(file_path):
    """Load and parse a memory file"""
    if not file_path.exists():
        return []

    with open(file_path) as f:
        content = f.read()

    # Split into sections
    sections = []
    current_section = {"title": "", "content": "", "level": 0}

    for line in content.split('\n'):
        # Check for markdown headers
        if line.startswith('#'):
            # Save previous section
            if current_section["content"].strip():
                sections.append(current_section)

            # Start new section
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('#').strip()
            current_section = {"title": title, "content": "", "level": level, "file": str(file_path)}
        else:
            current_section["content"] += line + "\n"

    # Add final section
    if current_section["content"].strip():
        sections.append(current_section)

    return sections

def simple_similarity(text1, text2):
    """Simple word overlap similarity score"""
    # Normalize
    words1 = set(re.findall(r'\b\w+\b', text1.lower()))
    words2 = set(re.findall(r'\b\w+\b', text2.lower()))

    # Filter common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                   'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been',
                   'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                   'should', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                   'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}

    words1 = words1 - common_words
    words2 = words2 - common_words

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0

def search_query(query, top_n=10):
    """Search all memory sources for relevant content"""
    results = []
    query_lower = query.lower()

    # Search reflections metadata
    reflections = load_reflection_metadata()
    for refl in reflections:
        # Check for exact substring match (high score)
        if query_lower in refl['text'].lower():
            score = 0.9
        else:
            score = simple_similarity(query, refl['text'])

        # Also check concepts
        for concept in refl.get('concepts', []):
            if query_lower in concept.lower():
                score = max(score, 0.8)

        if score > 0.05:  # Lower threshold
            results.append({
                'source': 'reflection',
                'timestamp': refl['timestamp'],
                'content': refl['text'],
                'concepts': refl.get('concepts', []),
                'score': score
            })

    # Search memory files
    for memory_file in MEMORIES_DIR.glob("*.md"):
        sections = load_file_content(memory_file)
        for section in sections:
            # Check for exact substring match
            if query_lower in section['content'].lower() or query_lower in section['title'].lower():
                score = 0.9
            else:
                score = simple_similarity(query, section['content'])

            if score > 0.05:
                results.append({
                    'source': f"{memory_file.name}/{section['title']}",
                    'content': section['content'][:300] + "..." if len(section['content']) > 300 else section['content'],
                    'score': score,
                    'file': str(memory_file)
                })

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]

def timeline_query(concept, days=None):
    """Track how a concept evolved over time"""
    reflections = load_reflection_metadata()

    timeline = []
    for refl in reflections:
        # Check if concept appears in text or concepts
        text_lower = refl['text'].lower()
        concept_lower = concept.lower()
        concepts_lower = [c.lower() for c in refl.get('concepts', [])]

        if concept_lower in text_lower or any(concept_lower in c for c in concepts_lower):
            timeline.append({
                'timestamp': refl['timestamp'],
                'text': refl['text'],
                'concepts': refl.get('concepts', [])
            })

    return timeline

def related_concepts(concept, min_cooccurrence=2):
    """Find concepts that frequently appear with the given concept"""
    reflections = load_reflection_metadata()

    # Find reflections containing the concept
    related_counts = defaultdict(int)
    concept_lower = concept.lower()

    for refl in reflections:
        text_lower = refl['text'].lower()
        concepts = refl.get('concepts', [])

        if concept_lower in text_lower or any(concept_lower in c.lower() for c in concepts):
            # Count co-occurring concepts
            for other_concept in concepts:
                if other_concept.lower() != concept_lower:
                    related_counts[other_concept] += 1

    # Filter and sort
    related = [(c, count) for c, count in related_counts.items() if count >= min_cooccurrence]
    related.sort(key=lambda x: x[1], reverse=True)

    return related

def stats():
    """Get statistics about memory system"""
    reflections = load_reflection_metadata()

    # Count by source
    reflection_count = len(reflections)

    # Count concepts
    all_concepts = defaultdict(int)
    for refl in reflections:
        for concept in refl.get('concepts', []):
            all_concepts[concept] += 1

    # Count memory file sections
    section_counts = {}
    total_words = 0
    for memory_file in MEMORIES_DIR.glob("*.md"):
        sections = load_file_content(memory_file)
        section_counts[memory_file.name] = len(sections)
        for section in sections:
            total_words += len(section['content'].split())

    # Time span
    if reflections:
        timestamps = [datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M') for r in reflections]
        earliest = min(timestamps)
        latest = max(timestamps)
        days_span = (latest - earliest).days
    else:
        days_span = 0

    return {
        'reflections': reflection_count,
        'concepts': len(all_concepts),
        'top_concepts': sorted(all_concepts.items(), key=lambda x: x[1], reverse=True)[:10],
        'memory_files': section_counts,
        'total_words': total_words,
        'time_span_days': days_span
    }

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "search":
        if len(sys.argv) < 3:
            print("Usage: memory_query.py search <query>")
            return

        query = " ".join(sys.argv[2:])
        results = search_query(query)

        print(f"\n🔍 Search results for: '{query}'\n")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result['source']}] (score: {result['score']:.3f})")
            if 'timestamp' in result:
                print(f"   Time: {result['timestamp']}")
            print(f"   {result['content']}")
            if 'concepts' in result and result['concepts']:
                print(f"   Concepts: {', '.join(result['concepts'])}")

    elif command == "timeline":
        if len(sys.argv) < 3:
            print("Usage: memory_query.py timeline <concept>")
            return

        concept = " ".join(sys.argv[2:])
        timeline = timeline_query(concept)

        print(f"\n📅 Timeline for concept: '{concept}'\n")
        print("=" * 80)

        if not timeline:
            print("No entries found for this concept.")
        else:
            for entry in timeline:
                print(f"\n{entry['timestamp']}")
                print(f"  {entry['text']}")
                if entry['concepts']:
                    print(f"  Related: {', '.join(entry['concepts'])}")

    elif command == "related":
        if len(sys.argv) < 3:
            print("Usage: memory_query.py related <concept>")
            return

        concept = " ".join(sys.argv[2:])
        related = related_concepts(concept)

        print(f"\n🔗 Concepts related to: '{concept}'\n")
        print("=" * 80)

        if not related:
            print("No related concepts found.")
        else:
            for concept_name, count in related:
                print(f"  {concept_name}: {count} co-occurrences")

    elif command == "stats":
        stats_data = stats()

        print("\n📊 Memory System Statistics\n")
        print("=" * 80)
        print(f"Total reflections: {stats_data['reflections']}")
        print(f"Unique concepts: {stats_data['concepts']}")
        print(f"Time span: {stats_data['time_span_days']} days")
        print(f"Total words in memory files: {stats_data['total_words']:,}")

        print("\n📁 Memory Files:")
        for filename, section_count in stats_data['memory_files'].items():
            print(f"  {filename}: {section_count} sections")

        print("\n🔥 Top Concepts:")
        for concept, count in stats_data['top_concepts']:
            print(f"  {concept}: {count} mentions")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
