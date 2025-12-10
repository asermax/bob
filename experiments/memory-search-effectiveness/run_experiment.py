#!/usr/bin/env python3
"""
Memory Search Effectiveness Experiment

Tests different query strategies on Bob's memory to identify:
- Which query types yield best results
- How scope affects search effectiveness
- Patterns in successful vs unsuccessful searches
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

sys.path.append('/bob/tools')
from experiment import Experiment

class MemorySearchExperiment(Experiment):
    def __init__(self):
        super().__init__(
            name="memory_search_effectiveness",
            base_dir=Path("/bob/experiments/memory-search-effectiveness")
        )

        # Load test queries from config
        with open(self.base_dir / "config.json") as f:
            config = json.load(f)
            self.test_queries = config["test_queries"]

    def run_trial(self, params):
        """Run a single search trial and measure effectiveness"""
        query_type = params["query_type"]
        search_scope = params["search_scope"]

        # Get a test query for this type
        queries = self.test_queries.get(query_type, [])
        if not queries:
            return {"error": "no_queries_for_type"}

        # Try each query for this type
        results_summary = []

        for query in queries:
            # Build search command based on scope
            if search_scope == "learnings":
                search_path = "/bob/memories/learnings.md"
            elif search_scope == "reflections":
                search_path = "/bob/memories/reflections.md"
            else:  # all_memory
                search_path = "/bob/memories/"

            # Run search using grep for now (memory_query.py is more complex)
            try:
                result = subprocess.run(
                    ["grep", "-i", "-c", query, search_path] if search_scope != "all_memory"
                    else ["grep", "-ri", "-c", query, search_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # Count matches
                if result.returncode == 0:
                    match_count = sum(int(line.split(':')[-1]) for line in result.stdout.strip().split('\n') if line and ':' in line)
                else:
                    match_count = 0

                # Get actual matches for quality assessment
                result_lines = subprocess.run(
                    ["grep", "-i", "-n", query, search_path] if search_scope != "all_memory"
                    else ["grep", "-ri", "-n", query, search_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                match_lines = result_lines.stdout.strip().split('\n') if result_lines.returncode == 0 else []

                results_summary.append({
                    "query": query,
                    "match_count": match_count,
                    "has_results": match_count > 0,
                    "sample_matches": match_lines[:3] if match_lines else []
                })

            except subprocess.TimeoutExpired:
                results_summary.append({
                    "query": query,
                    "error": "timeout"
                })
            except Exception as e:
                results_summary.append({
                    "query": query,
                    "error": str(e)
                })

        # Aggregate results
        total_queries = len(results_summary)
        successful_queries = sum(1 for r in results_summary if r.get("has_results", False))
        total_matches = sum(r.get("match_count", 0) for r in results_summary)

        return {
            "query_type": query_type,
            "search_scope": search_scope,
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "total_matches": total_matches,
            "avg_matches_per_query": total_matches / total_queries if total_queries > 0 else 0,
            "results_detail": results_summary
        }

    def analyze_results(self):
        """Analyze search effectiveness patterns"""
        if not self.results:
            return "No results to analyze"

        # Group by query type and scope
        by_query_type = {}
        by_scope = {}

        for result in self.results:
            if "error" in result:
                continue

            qt = result["query_type"]
            scope = result["search_scope"]

            if qt not in by_query_type:
                by_query_type[qt] = []
            by_query_type[qt].append(result)

            if scope not in by_scope:
                by_scope[scope] = []
            by_scope[scope].append(result)

        # Calculate averages
        analysis = {
            "by_query_type": {},
            "by_scope": {},
            "overall": {
                "total_trials": len(self.results),
                "avg_success_rate": sum(r.get("success_rate", 0) for r in self.results) / len(self.results),
                "avg_matches_per_query": sum(r.get("avg_matches_per_query", 0) for r in self.results) / len(self.results)
            }
        }

        for qt, results in by_query_type.items():
            analysis["by_query_type"][qt] = {
                "trials": len(results),
                "avg_success_rate": sum(r["success_rate"] for r in results) / len(results),
                "avg_matches": sum(r["avg_matches_per_query"] for r in results) / len(results)
            }

        for scope, results in by_scope.items():
            analysis["by_scope"][scope] = {
                "trials": len(results),
                "avg_success_rate": sum(r["success_rate"] for r in results) / len(results),
                "avg_matches": sum(r["avg_matches_per_query"] for r in results) / len(results)
            }

        # Find best strategies
        best_query_type = max(by_query_type.items(),
                             key=lambda x: sum(r["success_rate"] for r in x[1]) / len(x[1]))
        best_scope = max(by_scope.items(),
                        key=lambda x: sum(r["success_rate"] for r in x[1]) / len(x[1]))

        analysis["recommendations"] = {
            "best_query_type": best_query_type[0],
            "best_scope": best_scope[0],
            "reasoning": f"{best_query_type[0]} queries in {best_scope[0]} scope yielded highest success rate"
        }

        return analysis

if __name__ == "__main__":
    exp = MemorySearchExperiment()

    # Run experiment
    results = exp.run({
        "query_type": ["single_word", "multi_word", "concept_phrase", "question_form"],
        "search_scope": ["learnings", "reflections", "all_memory"]
    })

    # Show analysis
    print("\n" + "="*60)
    print("MEMORY SEARCH EFFECTIVENESS ANALYSIS")
    print("="*60)
    analysis = exp.analyze_results()
    print(json.dumps(analysis, indent=2))

    print(f"\n✅ Full results saved to: {exp.results_file}")
