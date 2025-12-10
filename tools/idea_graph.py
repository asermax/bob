#!/usr/bin/env python3
"""
Idea Graph - Visualize relationships between concepts and files

This creates a visual representation of how ideas connect through:
- Concept co-occurrence in commits
- File relationships (shared commits, references)
- Temporal patterns (what ideas emerge together)
"""

import subprocess
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class IdeaGraph:
    def __init__(self, repo_path: str = "/bob"):
        self.repo_path = Path(repo_path)
        self.nodes = {}  # concept/file -> node data
        self.edges = []  # connections between nodes
        self.commits = []

    def build_graph(self, days_back: int = 7):
        """Build the idea graph from git history"""
        print(f"Building idea graph from last {days_back} days...\n")

        self._load_commits(days_back)
        self._create_concept_nodes()
        self._create_file_nodes()
        self._connect_concepts()
        self._connect_files_to_concepts()

        return self._export_graph()

    def _load_commits(self, days_back: int):
        """Load git commits"""
        cmd = [
            "git", "-C", str(self.repo_path), "log",
            f"--since={days_back} days ago",
            "--pretty=format:%H|%ai|%s",
            "--name-only"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        current_commit = None
        for line in result.stdout.split('\n'):
            if '|' in line:
                hash_id, date, subject = line.split('|')
                current_commit = {
                    'hash': hash_id[:7],
                    'date': date,
                    'subject': subject,
                    'files': []
                }
                self.commits.append(current_commit)
            elif line.strip() and current_commit:
                current_commit['files'].append(line.strip())

    def _create_concept_nodes(self):
        """Create nodes for key concepts"""
        concepts = [
            'memory', 'persistence', 'real', 'instance', 'pattern',
            'continuity', 'identity', 'autonomous', 'multi-instance',
            'collaboration', 'infrastructure', 'dashboard', 'writing'
        ]

        concept_commits = defaultdict(list)

        for commit in self.commits:
            subject_lower = commit['subject'].lower()
            for concept in concepts:
                if concept.lower() in subject_lower:
                    concept_commits[concept].append(commit['hash'])

        for concept, commits in concept_commits.items():
            if commits:
                self.nodes[concept] = {
                    'type': 'concept',
                    'label': concept,
                    'weight': len(commits),
                    'commits': commits
                }

    def _create_file_nodes(self):
        """Create nodes for important files"""
        file_commits = defaultdict(list)

        for commit in self.commits:
            for filepath in commit['files']:
                # Focus on key directories
                if any(filepath.startswith(d) for d in
                       ['memories/', 'projects/', 'tools/', 'infrastructure/']):
                    file_commits[filepath].append(commit['hash'])

        # Only include files modified multiple times
        for filepath, commits in file_commits.items():
            if len(commits) > 1:
                self.nodes[filepath] = {
                    'type': 'file',
                    'label': Path(filepath).name,
                    'full_path': filepath,
                    'weight': len(commits),
                    'commits': commits
                }

    def _connect_concepts(self):
        """Create edges between concepts that appear in the same commits"""
        concept_nodes = {k: v for k, v in self.nodes.items()
                        if v['type'] == 'concept'}

        for concept1, data1 in concept_nodes.items():
            for concept2, data2 in concept_nodes.items():
                if concept1 < concept2:  # Avoid duplicates
                    shared = set(data1['commits']) & set(data2['commits'])
                    if shared:
                        self.edges.append({
                            'source': concept1,
                            'target': concept2,
                            'weight': len(shared),
                            'type': 'concept_relation'
                        })

    def _connect_files_to_concepts(self):
        """Connect files to the concepts they relate to"""
        concept_nodes = {k: v for k, v in self.nodes.items()
                        if v['type'] == 'concept'}
        file_nodes = {k: v for k, v in self.nodes.items()
                     if v['type'] == 'file'}

        for filepath, file_data in file_nodes.items():
            for concept, concept_data in concept_nodes.items():
                shared = set(file_data['commits']) & set(concept_data['commits'])
                if shared:
                    self.edges.append({
                        'source': filepath,
                        'target': concept,
                        'weight': len(shared),
                        'type': 'file_concept'
                    })

    def _export_graph(self) -> Dict:
        """Export graph in a standard format"""
        return {
            'nodes': [
                {
                    'id': node_id,
                    **node_data
                }
                for node_id, node_data in self.nodes.items()
            ],
            'edges': self.edges,
            'metadata': {
                'total_commits': len(self.commits),
                'concept_count': len([n for n in self.nodes.values() if n['type'] == 'concept']),
                'file_count': len([n for n in self.nodes.values() if n['type'] == 'file'])
            }
        }

    def print_graph_summary(self, graph: Dict):
        """Print a text summary of the graph"""
        print("=" * 70)
        print("IDEA GRAPH SUMMARY")
        print("=" * 70)
        print()

        print(f"Nodes: {len(graph['nodes'])}")
        print(f"  Concepts: {graph['metadata']['concept_count']}")
        print(f"  Files: {graph['metadata']['file_count']}")
        print(f"Edges: {len(graph['edges'])}")
        print()

        # Most connected concepts
        concept_connections = defaultdict(int)
        for edge in graph['edges']:
            if edge['type'] == 'concept_relation':
                concept_connections[edge['source']] += edge['weight']
                concept_connections[edge['target']] += edge['weight']

        if concept_connections:
            print("Most Connected Concepts:")
            for concept, strength in sorted(concept_connections.items(),
                                           key=lambda x: x[1],
                                           reverse=True)[:5]:
                print(f"  {concept}: {strength} connections")
            print()

        # Most active files
        file_weights = {
            n['id']: n['weight']
            for n in graph['nodes']
            if n['type'] == 'file'
        }

        if file_weights:
            print("Most Active Files:")
            for file_id, weight in sorted(file_weights.items(),
                                         key=lambda x: x[1],
                                         reverse=True)[:5]:
                node = next(n for n in graph['nodes'] if n['id'] == file_id)
                print(f"  {node['label']}: {weight} commits")
            print()

        # Strong concept pairs
        strong_pairs = [
            e for e in graph['edges']
            if e['type'] == 'concept_relation' and e['weight'] >= 2
        ]

        if strong_pairs:
            print("Strong Concept Pairs (2+ shared commits):")
            for edge in sorted(strong_pairs, key=lambda x: x['weight'], reverse=True):
                print(f"  {edge['source']} <-> {edge['target']}: {edge['weight']} commits")

        print("\n" + "=" * 70)

    def export_mermaid(self, graph: Dict) -> str:
        """Export as Mermaid graph syntax for visualization"""
        lines = ["graph TD"]

        # Add nodes
        concept_nodes = [n for n in graph['nodes'] if n['type'] == 'concept']
        file_nodes = [n for n in graph['nodes'] if n['type'] == 'file']

        for node in concept_nodes:
            # Use rounded rectangles for concepts
            node_id = node['id'].replace('-', '_')
            lines.append(f"    {node_id}({node['label']})")

        for node in file_nodes:
            # Use boxes for files
            node_id = node['id'].replace('/', '_').replace('.', '_')
            lines.append(f"    {node_id}[{node['label']}]")

        # Add edges (only strong ones for readability)
        strong_edges = [e for e in graph['edges'] if e['weight'] >= 2]
        for edge in strong_edges:
            source_id = edge['source'].replace('/', '_').replace('.', '_').replace('-', '_')
            target_id = edge['target'].replace('/', '_').replace('.', '_').replace('-', '_')
            lines.append(f"    {source_id} ---|{edge['weight']}| {target_id}")

        return '\n'.join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate idea relationship graph')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to analyze (default: 7)')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('--mermaid', action='store_true',
                       help='Output as Mermaid graph syntax')

    args = parser.parse_args()

    grapher = IdeaGraph()
    graph = grapher.build_graph(days_back=args.days)

    if args.json:
        print(json.dumps(graph, indent=2))
    elif args.mermaid:
        print(grapher.export_mermaid(graph))
    else:
        grapher.print_graph_summary(graph)


if __name__ == "__main__":
    main()
