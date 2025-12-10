#!/usr/bin/env python3
"""
Test experiment: Analyze code complexity across Bob's codebase
"""

import subprocess
from pathlib import Path
from tools.experiment import Experiment, ExperimentConfig


def analyze_file_complexity(params):
    """
    Analyze a Python file for complexity metrics

    Returns dict with:
    - lines: total lines
    - blank_lines: blank lines
    - comment_lines: comment lines
    - code_lines: actual code lines
    - functions: number of functions/methods
    - classes: number of classes
    - imports: number of imports
    """
    filepath = params["filepath"]
    path = Path(filepath)

    if not path.exists() or not path.is_file():
        raise ValueError(f"File not found: {filepath}")

    content = path.read_text()
    lines = content.split('\n')

    # Count metrics
    total_lines = len(lines)
    blank_lines = len([l for l in lines if not l.strip()])
    comment_lines = len([l for l in lines if l.strip().startswith('#')])
    code_lines = total_lines - blank_lines - comment_lines

    # Count structures
    functions = len([l for l in lines if l.strip().startswith('def ')])
    classes = len([l for l in lines if l.strip().startswith('class ')])
    imports = len([l for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')])

    # Calculate complexity score (simple heuristic)
    # More functions/classes per line of code = higher complexity
    complexity = (functions + classes * 2) / max(code_lines, 1) * 100

    return {
        "total_lines": total_lines,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "code_lines": code_lines,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "complexity_score": round(complexity, 2)
    }


# Find all Python files in the codebase
python_files = []
for pattern in ["tools/*.py", "projects/**/*.py", ".claude/**/*.py"]:
    python_files.extend([str(p) for p in Path(".").glob(pattern)])

# Filter out this test file
python_files = [f for f in python_files if f != "test_experiment.py"]

if not python_files:
    print("No Python files found!")
    exit(1)

print(f"Found {len(python_files)} Python files to analyze\n")

# Create experiment config
config = ExperimentConfig(
    name="code-complexity-analysis",
    description="Analyze complexity metrics across Bob's Python codebase",
    parameters={
        "filepath": python_files
    }
)

# Run experiment
exp = Experiment(config)
exp.run(analyze_file_complexity)

# Custom analysis
def complexity_analysis(trials):
    """Analyze complexity patterns"""
    successful = [t for t in trials if t.result]

    if not successful:
        return "No successful trials"

    # Sort by complexity
    by_complexity = sorted(successful, key=lambda t: t.result["complexity_score"], reverse=True)

    print("\n📈 Complexity Analysis:\n")
    print("Most Complex Files:")
    for trial in by_complexity[:5]:
        r = trial.result
        filepath = trial.parameters["filepath"]
        print(f"  {filepath}")
        print(f"    Complexity: {r['complexity_score']}")
        print(f"    Code lines: {r['code_lines']}, Functions: {r['functions']}, Classes: {r['classes']}")

    print("\nLeast Complex Files:")
    for trial in by_complexity[-5:]:
        r = trial.result
        filepath = trial.parameters["filepath"]
        print(f"  {filepath}")
        print(f"    Complexity: {r['complexity_score']}")
        print(f"    Code lines: {r['code_lines']}, Functions: {r['functions']}, Classes: {r['classes']}")

    # Overall stats
    import statistics
    complexities = [t.result["complexity_score"] for t in successful]
    code_lines = [t.result["code_lines"] for t in successful]

    print("\n📊 Overall Statistics:")
    print(f"  Mean complexity: {statistics.mean(complexities):.2f}")
    print(f"  Median complexity: {statistics.median(complexities):.2f}")
    print(f"  Mean code lines: {statistics.mean(code_lines):.1f}")
    print(f"  Total code lines: {sum(code_lines)}")

exp.analyze(complexity_analysis)

print("\n✅ Experiment complete!")
print(f"📁 Full results in: experiments/code-complexity-analysis/")
