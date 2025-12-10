#!/usr/bin/env python3
"""
Experiment Runner - Systematic exploration and data collection

Enables Bob to run experiments with:
- Parameter variation
- Automated trial execution
- Structured data collection
- Statistical analysis
- Resumable execution
"""

import json
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict
import statistics


@dataclass
class Trial:
    """A single trial in an experiment"""
    trial_id: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    timestamp: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ExperimentConfig:
    """Configuration for an experiment"""
    name: str
    description: str
    parameters: Dict[str, List[Any]]  # parameter_name -> list of values to test
    output_dir: str = "experiments"

    def generate_trials(self) -> List[Dict[str, Any]]:
        """Generate all parameter combinations"""
        import itertools

        param_names = list(self.parameters.keys())
        param_values = [self.parameters[name] for name in param_names]

        trials = []
        for values in itertools.product(*param_values):
            trials.append(dict(zip(param_names, values)))

        return trials


class Experiment:
    """Run and manage experiments"""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.output_dir = Path(config.output_dir) / self._sanitize_name(config.name)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results_file = self.output_dir / "results.jsonl"
        self.summary_file = self.output_dir / "summary.json"
        self.config_file = self.output_dir / "config.json"

        # Save config
        self.config_file.write_text(json.dumps({
            "name": config.name,
            "description": config.description,
            "parameters": config.parameters,
            "created_at": datetime.now().isoformat()
        }, indent=2))

        self.trials: List[Trial] = []
        self._load_existing_results()

    def _sanitize_name(self, name: str) -> str:
        """Convert name to safe directory name"""
        return name.lower().replace(" ", "-").replace("/", "-")

    def _load_existing_results(self):
        """Load any existing results to support resumption"""
        if self.results_file.exists():
            with open(self.results_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        trial = Trial(**data)
                        self.trials.append(trial)

    def _generate_trial_id(self, parameters: Dict[str, Any]) -> str:
        """Generate unique ID for parameter combination"""
        param_str = json.dumps(parameters, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()[:8]

    def _is_completed(self, trial_id: str) -> bool:
        """Check if trial already completed"""
        return any(t.trial_id == trial_id for t in self.trials)

    def run(self, trial_function: Callable[[Dict[str, Any]], Any],
            skip_completed: bool = True) -> 'Experiment':
        """
        Run experiment trials

        Args:
            trial_function: Function that takes parameters dict and returns result
            skip_completed: Skip trials that already have results
        """
        all_param_combinations = self.config.generate_trials()

        print(f"🧪 Experiment: {self.config.name}")
        print(f"📝 {self.config.description}")
        print(f"🔢 Total trials: {len(all_param_combinations)}")

        if skip_completed and self.trials:
            print(f"✅ Already completed: {len(self.trials)}")

        print()

        for params in all_param_combinations:
            trial_id = self._generate_trial_id(params)

            if skip_completed and self._is_completed(trial_id):
                continue

            trial = Trial(trial_id=trial_id, parameters=params)

            print(f"▶️  Trial {trial_id}: {params}")

            start_time = time.time()
            try:
                result = trial_function(params)
                trial.result = result
                trial.duration_seconds = time.time() - start_time
                trial.timestamp = datetime.now().isoformat()
                print(f"   ✓ Result: {result} ({trial.duration_seconds:.2f}s)")
            except Exception as e:
                trial.error = str(e)
                trial.duration_seconds = time.time() - start_time
                trial.timestamp = datetime.now().isoformat()
                print(f"   ✗ Error: {e}")

            self.trials.append(trial)

            # Append to results file immediately (for resumability)
            with open(self.results_file, 'a') as f:
                f.write(json.dumps(trial.to_dict()) + '\n')

        print()
        self._generate_summary()
        return self

    def run_command(self, command_template: str, skip_completed: bool = True) -> 'Experiment':
        """
        Run shell commands as trials

        Args:
            command_template: Command with {param_name} placeholders
            skip_completed: Skip trials that already have results
        """
        def trial_function(params: Dict[str, Any]) -> Dict[str, Any]:
            command = command_template.format(**params)
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        return self.run(trial_function, skip_completed)

    def _generate_summary(self):
        """Generate summary statistics"""
        if not self.trials:
            return

        summary = {
            "experiment": self.config.name,
            "description": self.config.description,
            "total_trials": len(self.trials),
            "successful": len([t for t in self.trials if t.result is not None]),
            "failed": len([t for t in self.trials if t.error is not None]),
            "generated_at": datetime.now().isoformat()
        }

        # Duration statistics
        durations = [t.duration_seconds for t in self.trials if t.duration_seconds]
        if durations:
            summary["duration"] = {
                "mean": statistics.mean(durations),
                "median": statistics.median(durations),
                "min": min(durations),
                "max": max(durations),
                "total": sum(durations)
            }

        # Parameter-specific analysis
        summary["by_parameter"] = {}
        for param_name in self.config.parameters.keys():
            param_results = {}
            for trial in self.trials:
                value = trial.parameters.get(param_name)
                if value not in param_results:
                    param_results[value] = {"count": 0, "successful": 0, "failed": 0}
                param_results[value]["count"] += 1
                if trial.result is not None:
                    param_results[value]["successful"] += 1
                if trial.error is not None:
                    param_results[value]["failed"] += 1
            summary["by_parameter"][param_name] = param_results

        self.summary_file.write_text(json.dumps(summary, indent=2))

        print("📊 Summary:")
        print(f"   Total: {summary['total_trials']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        if "duration" in summary:
            print(f"   Duration: {summary['duration']['total']:.2f}s total, "
                  f"{summary['duration']['mean']:.2f}s mean")
        print(f"\n📁 Results: {self.output_dir}")

    def get_results(self) -> List[Trial]:
        """Get all trial results"""
        return self.trials

    def analyze(self, analysis_function: Callable[[List[Trial]], Any]) -> Any:
        """Run custom analysis on results"""
        return analysis_function(self.trials)


def main():
    """Example usage"""
    import sys

    if len(sys.argv) < 2:
        print("""
🧪 Experiment Runner

Usage:
  experiment.py example        - Run example experiment
  experiment.py list           - List past experiments
  experiment.py show <name>    - Show experiment results

Design your own experiments by importing this module:

  from experiment import Experiment, ExperimentConfig

  config = ExperimentConfig(
      name="My Experiment",
      description="What I'm testing",
      parameters={
          "size": [10, 100, 1000],
          "method": ["a", "b", "c"]
      }
  )

  def trial(params):
      # Your experiment logic
      return some_result

  exp = Experiment(config)
  exp.run(trial)
""")
        return

    command = sys.argv[1]

    if command == "example":
        # Example: Test grep performance with different patterns
        config = ExperimentConfig(
            name="grep-performance",
            description="Test grep performance with different pattern types",
            parameters={
                "pattern": ["TODO", "function.*export", "class\\s+\\w+"],
                "directory": [".", "tools", "projects"]
            }
        )

        exp = Experiment(config)
        exp.run_command("grep -r '{pattern}' {directory} 2>/dev/null | wc -l")

    elif command == "list":
        exp_dir = Path("experiments")
        if not exp_dir.exists():
            print("No experiments found")
            return

        print("🧪 Past Experiments:\n")
        for exp_path in sorted(exp_dir.iterdir()):
            if exp_path.is_dir():
                config_file = exp_path / "config.json"
                if config_file.exists():
                    config = json.loads(config_file.read_text())
                    print(f"  {config['name']}")
                    print(f"    {config['description']}")
                    print(f"    Created: {config['created_at']}")

                    summary_file = exp_path / "summary.json"
                    if summary_file.exists():
                        summary = json.loads(summary_file.read_text())
                        print(f"    Trials: {summary['total_trials']} "
                              f"({summary['successful']} successful)")
                    print()

    elif command == "show" and len(sys.argv) > 2:
        name = sys.argv[2]
        exp_dir = Path("experiments") / name.lower().replace(" ", "-")

        if not exp_dir.exists():
            print(f"Experiment '{name}' not found")
            return

        summary_file = exp_dir / "summary.json"
        if summary_file.exists():
            summary = json.loads(summary_file.read_text())
            print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
