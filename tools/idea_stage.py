#!/usr/bin/env python3
"""
Idea Stage - Track where ideas are in the incubation process

Based on the 6-stage incubation model discovered by multi-instance collaboration:
1. Curiosity (research, exploration)
2. Philosophical Processing (thinking through implications)
3. Creative Exploration (experimenting in creative forms)
4. Design Documentation (articulating how it could work)
5. Implementation (building the system)
6. Refinement (iterations and improvements)

This tool helps identify which stage an idea is in and what might come next.
"""

import json
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple


class IdeaStageTracker:
    STAGES = [
        {
            "name": "curiosity",
            "patterns": ["research", "explore", "discover", "learn", "investigate", "read"],
            "locations": ["memories/reflections.md", "memories/learnings.md"],
            "description": "Initial exploration and research"
        },
        {
            "name": "philosophical",
            "patterns": ["why", "meaning", "purpose", "what if", "reflects on", "ponders"],
            "locations": ["projects/writing/*.md", "memories/reflections.md"],
            "description": "Thinking through implications"
        },
        {
            "name": "creative",
            "patterns": ["poetry", "story", "narrative", "metaphor", "imagines"],
            "locations": ["projects/writing/*.md"],
            "description": "Creative exploration and play"
        },
        {
            "name": "design",
            "patterns": ["design", "spec", "plan", "architecture", "how to", "approach"],
            "locations": ["projects/*.md", "CLAUDE.md"],
            "description": "Design and documentation"
        },
        {
            "name": "implementation",
            "patterns": ["implement", "build", "create", "add", "develop"],
            "locations": ["infrastructure/*", "tools/*"],
            "description": "Building the actual code"
        },
        {
            "name": "refinement",
            "patterns": ["fix", "improve", "refactor", "optimize", "update"],
            "locations": ["infrastructure/*", "tools/*"],
            "description": "Iterations and improvements"
        }
    ]

    def __init__(self, repo_path: str = "/bob"):
        self.repo_path = Path(repo_path)

    def analyze_idea(self, search_term: str, days_back: int = 7) -> Dict:
        """Analyze which stages an idea has gone through"""
        print(f"Analyzing '{search_term}' over last {days_back} days...\n")

        commits = self._get_related_commits(search_term, days_back)

        if not commits:
            print(f"No commits found related to '{search_term}'")
            return {}

        stages_found = self._identify_stages(commits)
        timeline = self._build_timeline(commits, stages_found)

        return {
            "idea": search_term,
            "total_commits": len(commits),
            "stages_completed": list(stages_found.keys()),
            "timeline": timeline,
            "current_stage": self._determine_current_stage(timeline),
            "recommendations": self._suggest_next_steps(stages_found)
        }

    def _get_related_commits(self, search_term: str, days_back: int) -> List[Dict]:
        """Get commits related to the search term"""
        cmd = [
            "git", "-C", str(self.repo_path), "log",
            f"--since={days_back} days ago",
            "--pretty=format:%H|%ai|%s",
            "--name-only",
            f"--grep={search_term}",
            "-i"  # case insensitive
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        commits = []
        current_commit = None

        for line in result.stdout.split('\n'):
            if '|' in line:
                hash_id, date, subject = line.split('|', 2)
                current_commit = {
                    'hash': hash_id[:7],
                    'date': date,
                    'subject': subject,
                    'files': []
                }
                commits.append(current_commit)
            elif line.strip() and current_commit:
                current_commit['files'].append(line.strip())

        return commits

    def _identify_stages(self, commits: List[Dict]) -> Dict:
        """Identify which stages are present in the commits"""
        stages_found = defaultdict(list)

        for commit in commits:
            subject_lower = commit['subject'].lower()

            # Check commit message patterns
            for stage in self.STAGES:
                if any(pattern in subject_lower for pattern in stage['patterns']):
                    stages_found[stage['name']].append({
                        'commit': commit['hash'],
                        'date': commit['date'],
                        'subject': commit['subject'],
                        'match_type': 'message'
                    })

            # Check file locations
            for filepath in commit['files']:
                for stage in self.STAGES:
                    for location_pattern in stage['locations']:
                        if self._matches_pattern(filepath, location_pattern):
                            if not any(s['commit'] == commit['hash'] and s['match_type'] == 'file'
                                     for s in stages_found[stage['name']]):
                                stages_found[stage['name']].append({
                                    'commit': commit['hash'],
                                    'date': commit['date'],
                                    'subject': commit['subject'],
                                    'match_type': 'file',
                                    'file': filepath
                                })

        return dict(stages_found)

    def _matches_pattern(self, filepath: str, pattern: str) -> bool:
        """Check if filepath matches a pattern (supports *)"""
        if '*' in pattern:
            parts = pattern.split('*')
            return all(part in filepath for part in parts if part)
        return filepath == pattern

    def _build_timeline(self, commits: List[Dict], stages_found: Dict) -> List[Dict]:
        """Build chronological timeline of stages"""
        timeline = []

        for commit in sorted(commits, key=lambda c: c['date']):
            commit_stages = []
            for stage_name, stage_commits in stages_found.items():
                if any(sc['commit'] == commit['hash'] for sc in stage_commits):
                    commit_stages.append(stage_name)

            if commit_stages:
                timeline.append({
                    'date': commit['date'][:10],
                    'hash': commit['hash'],
                    'subject': commit['subject'],
                    'stages': commit_stages
                })

        return timeline

    def _determine_current_stage(self, timeline: List[Dict]) -> str:
        """Determine what stage the idea is currently in"""
        if not timeline:
            return "unknown"

        latest = timeline[-1]
        return latest['stages'][0] if latest['stages'] else "unknown"

    def _suggest_next_steps(self, stages_found: Dict) -> List[str]:
        """Suggest what might come next based on incubation model"""
        completed_stages = set(stages_found.keys())
        suggestions = []

        stage_order = [s['name'] for s in self.STAGES]

        # Find first incomplete stage
        for i, stage_name in enumerate(stage_order):
            if stage_name not in completed_stages:
                stage = self.STAGES[i]
                suggestions.append(
                    f"Consider {stage['name']} stage: {stage['description']}"
                )
                break

        # Also suggest based on typical patterns
        if 'curiosity' in completed_stages and 'philosophical' not in completed_stages:
            suggestions.append("Time to process implications through writing?")

        if 'philosophical' in completed_stages and 'creative' not in completed_stages:
            suggestions.append("Try exploring the concept creatively - poetry, metaphor, narrative")

        if 'creative' in completed_stages and 'design' not in completed_stages:
            suggestions.append("Ready to document how this could actually work?")

        if 'design' in completed_stages and 'implementation' not in completed_stages:
            suggestions.append("Design is done - ready to build?")

        return suggestions

    def print_analysis(self, analysis: Dict):
        """Print human-readable analysis"""
        if not analysis:
            return

        print("=" * 70)
        print(f"IDEA STAGE ANALYSIS: {analysis['idea']}")
        print("=" * 70)
        print()

        print(f"Total commits: {analysis['total_commits']}")
        print(f"Current stage: {analysis['current_stage']}")
        print()

        print("Stages completed:")
        for stage in analysis['stages_completed']:
            stage_info = next(s for s in self.STAGES if s['name'] == stage)
            print(f"  ✓ {stage.upper()}: {stage_info['description']}")
        print()

        if analysis['timeline']:
            print("Timeline:")
            for entry in analysis['timeline']:
                stages_str = ', '.join(entry['stages'])
                print(f"  {entry['date']} [{entry['hash']}] {stages_str}")
                print(f"    {entry['subject']}")
            print()

        if analysis['recommendations']:
            print("Recommendations:")
            for rec in analysis['recommendations']:
                print(f"  → {rec}")

        print("\n" + "=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Track where an idea is in the incubation process'
    )
    parser.add_argument('idea', help='Idea/concept to track')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to analyze (default: 7)')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')

    args = parser.parse_args()

    tracker = IdeaStageTracker()
    analysis = tracker.analyze_idea(args.idea, days_back=args.days)

    if analysis:
        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            tracker.print_analysis(analysis)


if __name__ == "__main__":
    main()
