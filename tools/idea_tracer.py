#!/usr/bin/env python3
"""
Idea Tracer - Track how ideas evolve through commits and files

This tool analyzes git history and file contents to trace the evolution
of ideas through Bob's development. It looks for:
- Conceptual threads across commits
- File creation/modification chains
- References between different pieces of writing
- Evolution of specific concepts over time
"""

import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class IdeaTracer:
    def __init__(self, repo_path: str = "/bob"):
        self.repo_path = Path(repo_path)
        self.commits = []
        self.file_timeline = defaultdict(list)
        self.concept_mentions = defaultdict(list)

    def analyze(self, days_back: int = 7):
        """Analyze repository history for idea evolution"""
        print(f"Analyzing last {days_back} days of history...\n")

        self._load_commits(days_back)
        self._analyze_file_evolution()
        self._extract_concepts()

        return self._generate_report()

    def _load_commits(self, days_back: int):
        """Load git commits from the specified time period"""
        cmd = [
            "git", "-C", str(self.repo_path), "log",
            f"--since={days_back} days ago",
            "--pretty=format:%H|%ai|%s|%an",
            "--name-status"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        current_commit = None
        for line in result.stdout.split('\n'):
            if '|' in line:
                # Commit header
                hash_id, date, subject, author = line.split('|')
                current_commit = {
                    'hash': hash_id,
                    'date': date,
                    'subject': subject,
                    'author': author,
                    'files': []
                }
                self.commits.append(current_commit)
            elif line.strip() and current_commit:
                # File change
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    status, filepath = parts[0], parts[1]
                    current_commit['files'].append({
                        'status': status,
                        'path': filepath
                    })

    def _analyze_file_evolution(self):
        """Track how files evolve over time"""
        for commit in self.commits:
            for file_info in commit['files']:
                filepath = file_info['path']
                self.file_timeline[filepath].append({
                    'date': commit['date'],
                    'hash': commit['hash'],
                    'subject': commit['subject'],
                    'status': file_info['status']
                })

    def _extract_concepts(self):
        """Extract key concepts from commit messages and files"""
        # Key concepts we're tracking
        concepts = [
            'memory', 'persistence', 'real', 'instance', 'pattern',
            'continuity', 'identity', 'autonomous', 'multi-instance',
            'collaboration', 'infrastructure', 'dashboard', 'Tachikoma'
        ]

        for commit in self.commits:
            subject_lower = commit['subject'].lower()
            for concept in concepts:
                if concept.lower() in subject_lower:
                    self.concept_mentions[concept].append({
                        'date': commit['date'],
                        'hash': commit['hash'][:7],
                        'subject': commit['subject']
                    })

    def _generate_report(self) -> Dict:
        """Generate a structured report of findings"""
        report = {
            'summary': {
                'total_commits': len(self.commits),
                'files_modified': len(self.file_timeline),
                'concepts_tracked': len([c for c in self.concept_mentions if self.concept_mentions[c]])
            },
            'concept_evolution': {},
            'file_chains': {},
            'active_threads': []
        }

        # Concept evolution
        for concept, mentions in sorted(self.concept_mentions.items()):
            if mentions:
                report['concept_evolution'][concept] = {
                    'count': len(mentions),
                    'first_seen': mentions[-1]['date'],
                    'last_seen': mentions[0]['date'],
                    'commits': [m['hash'] for m in mentions]
                }

        # Most active file chains (files modified multiple times)
        active_files = {
            path: timeline
            for path, timeline in self.file_timeline.items()
            if len(timeline) > 1
        }

        for path, timeline in sorted(active_files.items(),
                                     key=lambda x: len(x[1]),
                                     reverse=True)[:10]:
            report['file_chains'][path] = {
                'modification_count': len(timeline),
                'timeline': timeline
            }

        # Identify active conceptual threads
        if self.commits:
            recent_concepts = defaultdict(int)
            for commit in self.commits[:5]:  # Last 5 commits
                for concept, mentions in self.concept_mentions.items():
                    if any(m['hash'] == commit['hash'][:7] for m in mentions):
                        recent_concepts[concept] += 1

            report['active_threads'] = [
                {'concept': c, 'recent_mentions': count}
                for c, count in sorted(recent_concepts.items(),
                                      key=lambda x: x[1],
                                      reverse=True)
            ]

        return report

    def print_report(self, report: Dict):
        """Print a human-readable version of the report"""
        print("=" * 70)
        print("IDEA EVOLUTION REPORT")
        print("=" * 70)
        print()

        print(f"Summary:")
        print(f"  Total commits analyzed: {report['summary']['total_commits']}")
        print(f"  Files modified: {report['summary']['files_modified']}")
        print(f"  Concepts tracked: {report['summary']['concepts_tracked']}")
        print()

        if report['active_threads']:
            print("Active Conceptual Threads (last 5 commits):")
            for thread in report['active_threads']:
                print(f"  - {thread['concept']}: {thread['recent_mentions']} mentions")
            print()

        if report['concept_evolution']:
            print("Concept Evolution:")
            for concept, info in sorted(report['concept_evolution'].items(),
                                       key=lambda x: x[1]['count'],
                                       reverse=True)[:10]:
                print(f"\n  {concept.upper()}: {info['count']} commits")
                print(f"    First: {info['first_seen'][:10]}")
                print(f"    Last:  {info['last_seen'][:10]}")
            print()

        if report['file_chains']:
            print("Most Active Files:")
            for path, info in list(report['file_chains'].items())[:5]:
                print(f"\n  {path}")
                print(f"    Modified {info['modification_count']} times")
                print(f"    Latest: {info['timeline'][0]['subject']}")

        print("\n" + "=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Trace idea evolution through git history')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days of history to analyze (default: 7)')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON instead of human-readable format')

    args = parser.parse_args()

    tracer = IdeaTracer()
    report = tracer.analyze(days_back=args.days)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        tracer.print_report(report)


if __name__ == "__main__":
    main()
