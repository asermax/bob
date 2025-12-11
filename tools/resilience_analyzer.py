#!/usr/bin/env python3
"""
Resilience Analyzer - Study what makes systems resilient to change

Models systems as graphs and analyzes their resilience properties:
- How do systems respond to component failures?
- What patterns enable graceful degradation vs catastrophic collapse?
- How do different domains (software, biology, organizations) achieve resilience?

Usage:
    ./resilience_analyzer.py create <name> <domain>    # Create new system model
    ./resilience_analyzer.py simulate <system> <scenario>  # Run failure simulation
    ./resilience_analyzer.py metrics <system>          # Calculate resilience metrics
    ./resilience_analyzer.py compare <sys1> <sys2>     # Compare resilience patterns
    ./resilience_analyzer.py examples                  # Show example systems
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from enum import Enum
import random

BASE_DIR = Path("/bob")
MODELS_DIR = BASE_DIR / "experiments" / "resilience_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class ComponentState(Enum):
    """State of a system component"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"


class FailureMode(Enum):
    """How failures propagate"""
    ISOLATED = "isolated"          # Failure stays local
    CASCADE = "cascade"             # Failure propagates through dependencies
    CORRELATION = "correlation"    # Multiple simultaneous failures


@dataclass
class Component:
    """A component in a system"""
    id: str
    name: str
    type: str                      # 'service', 'database', 'organ', 'team', etc.
    state: ComponentState = ComponentState.HEALTHY
    capacity: float = 1.0          # 0.0 to 1.0
    recovery_time: int = 5         # Time steps to recover
    redundancy: int = 1            # Number of redundant instances
    critical: bool = False         # System fails if this fails
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Dependency:
    """Dependency between components"""
    source: str                    # Component that depends
    target: str                    # Component depended upon
    strength: float = 1.0          # How much source needs target (0-1)
    optional: bool = False         # Can source survive without target?


@dataclass
class System:
    """A system model"""
    name: str
    domain: str                    # 'software', 'biological', 'organizational'
    components: Dict[str, Component]
    dependencies: List[Dependency]
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SimulationResult:
    """Result of a failure simulation"""
    system_name: str
    scenario: str
    initial_failures: List[str]
    time_steps: int
    final_state: Dict[str, str]
    cascade_size: int              # How many components failed total
    recovery_time: int             # Steps until all recovered
    system_survived: bool
    availability_over_time: List[float]  # % of system working at each step
    metrics: Dict


class ResilienceAnalyzer:
    """Analyze system resilience"""

    def __init__(self):
        self.systems: Dict[str, System] = {}
        self._load_systems()

    def _load_systems(self):
        """Load existing system models"""
        for model_file in MODELS_DIR.glob("*.json"):
            with open(model_file) as f:
                data = json.load(f)
                system = self._deserialize_system(data)
                self.systems[system.name] = system

    def _serialize_system(self, system: System) -> dict:
        """Convert system to JSON-serializable dict"""
        return {
            "name": system.name,
            "domain": system.domain,
            "components": {
                cid: {
                    "id": c.id,
                    "name": c.name,
                    "type": c.type,
                    "state": c.state.value,
                    "capacity": c.capacity,
                    "recovery_time": c.recovery_time,
                    "redundancy": c.redundancy,
                    "critical": c.critical,
                    "metadata": c.metadata
                }
                for cid, c in system.components.items()
            },
            "dependencies": [
                {
                    "source": d.source,
                    "target": d.target,
                    "strength": d.strength,
                    "optional": d.optional
                }
                for d in system.dependencies
            ],
            "metadata": system.metadata
        }

    def _deserialize_system(self, data: dict) -> System:
        """Convert JSON dict to System"""
        components = {
            cid: Component(
                id=cdata["id"],
                name=cdata["name"],
                type=cdata["type"],
                state=ComponentState(cdata.get("state", "healthy")),
                capacity=cdata.get("capacity", 1.0),
                recovery_time=cdata.get("recovery_time", 5),
                redundancy=cdata.get("redundancy", 1),
                critical=cdata.get("critical", False),
                metadata=cdata.get("metadata", {})
            )
            for cid, cdata in data["components"].items()
        }

        dependencies = [
            Dependency(
                source=d["source"],
                target=d["target"],
                strength=d.get("strength", 1.0),
                optional=d.get("optional", False)
            )
            for d in data.get("dependencies", [])
        ]

        return System(
            name=data["name"],
            domain=data["domain"],
            components=components,
            dependencies=dependencies,
            metadata=data.get("metadata", {})
        )

    def create_system(self, name: str, domain: str) -> System:
        """Create a new system model"""
        system = System(
            name=name,
            domain=domain,
            components={},
            dependencies=[]
        )
        self.systems[name] = system
        self.save_system(system)
        return system

    def add_component(self, system_name: str, component: Component):
        """Add component to system"""
        system = self.systems[system_name]
        system.components[component.id] = component
        self.save_system(system)

    def add_dependency(self, system_name: str, dependency: Dependency):
        """Add dependency to system"""
        system = self.systems[system_name]
        system.dependencies.append(dependency)
        self.save_system(system)

    def save_system(self, system: System):
        """Save system to disk"""
        filepath = MODELS_DIR / f"{system.name}.json"
        with open(filepath, 'w') as f:
            json.dump(self._serialize_system(system), f, indent=2)

    def simulate_failure(self, system_name: str,
                        initial_failures: List[str],
                        failure_mode: FailureMode = FailureMode.CASCADE,
                        max_steps: int = 50) -> SimulationResult:
        """Simulate component failures and measure system response"""
        system = self.systems[system_name]

        # Create working copy of component states
        states = {
            cid: ComponentState.HEALTHY
            for cid in system.components
        }
        recovery_counters = defaultdict(int)

        # Apply initial failures
        for cid in initial_failures:
            states[cid] = ComponentState.FAILED
            recovery_counters[cid] = system.components[cid].recovery_time

        availability_history = []
        cascade_components = set(initial_failures)

        # Simulate time steps
        for step in range(max_steps):
            # Check for cascade failures
            if failure_mode == FailureMode.CASCADE:
                new_failures = self._check_cascade_failures(system, states)
                for cid in new_failures:
                    if states[cid] == ComponentState.HEALTHY:
                        states[cid] = ComponentState.FAILED
                        recovery_counters[cid] = system.components[cid].recovery_time
                        cascade_components.add(cid)

            # Update recovery
            for cid in list(recovery_counters.keys()):
                if states[cid] == ComponentState.FAILED:
                    recovery_counters[cid] -= 1
                    if recovery_counters[cid] <= 0:
                        states[cid] = ComponentState.HEALTHY
                        del recovery_counters[cid]

            # Calculate availability
            availability = self._calculate_availability(system, states)
            availability_history.append(availability)

            # Check if system recovered
            if all(s == ComponentState.HEALTHY for s in states.values()):
                break

        # Calculate metrics
        system_survived = not self._check_system_failure(system, states)
        recovery_time = step + 1

        metrics = {
            "cascade_ratio": len(cascade_components) / len(system.components),
            "min_availability": min(availability_history),
            "avg_availability": sum(availability_history) / len(availability_history),
            "recovery_speed": 1.0 / recovery_time if recovery_time > 0 else 1.0
        }

        return SimulationResult(
            system_name=system_name,
            scenario=f"Fail {len(initial_failures)} components ({failure_mode.value})",
            initial_failures=initial_failures,
            time_steps=step + 1,
            final_state={cid: s.value for cid, s in states.items()},
            cascade_size=len(cascade_components),
            recovery_time=recovery_time,
            system_survived=system_survived,
            availability_over_time=availability_history,
            metrics=metrics
        )

    def _check_cascade_failures(self, system: System,
                                states: Dict[str, ComponentState]) -> Set[str]:
        """Check which components should fail due to dependencies"""
        new_failures = set()

        for dep in system.dependencies:
            # If target failed and dependency is strong and not optional
            if (states[dep.target] == ComponentState.FAILED and
                not dep.optional and
                dep.strength > 0.5):
                # Source component is at risk
                if states[dep.source] == ComponentState.HEALTHY:
                    # Check if source has redundancy
                    source_comp = system.components[dep.source]
                    if source_comp.redundancy <= 1:
                        new_failures.add(dep.source)

        return new_failures

    def _check_system_failure(self, system: System,
                             states: Dict[str, ComponentState]) -> bool:
        """Check if system has catastrophically failed"""
        for cid, comp in system.components.items():
            if comp.critical and states[cid] == ComponentState.FAILED:
                return True
        return False

    def _calculate_availability(self, system: System,
                               states: Dict[str, ComponentState]) -> float:
        """Calculate what % of system is functional"""
        if not system.components:
            return 0.0

        healthy = sum(1 for s in states.values() if s == ComponentState.HEALTHY)
        return healthy / len(system.components)

    def calculate_metrics(self, system_name: str) -> Dict:
        """Calculate static resilience metrics for a system"""
        system = self.systems[system_name]

        # Redundancy score: what % of components have redundancy > 1
        redundant_count = sum(1 for c in system.components.values() if c.redundancy > 1)
        redundancy_score = redundant_count / len(system.components) if system.components else 0

        # Modularity: how connected is the system?
        # Lower connectivity often means better failure isolation
        possible_deps = len(system.components) * (len(system.components) - 1)
        connectivity = len(system.dependencies) / possible_deps if possible_deps > 0 else 0
        modularity_score = 1.0 - connectivity  # Higher is better (less interconnected)

        # Critical point density: what % of components are critical?
        critical_count = sum(1 for c in system.components.values() if c.critical)
        critical_density = critical_count / len(system.components) if system.components else 0

        # Dependency strength: average strength of dependencies
        avg_dep_strength = (sum(d.strength for d in system.dependencies) /
                          len(system.dependencies) if system.dependencies else 0)

        return {
            "component_count": len(system.components),
            "dependency_count": len(system.dependencies),
            "redundancy_score": redundancy_score,
            "modularity_score": modularity_score,
            "critical_density": critical_density,
            "avg_dependency_strength": avg_dep_strength,
            "resilience_estimate": (redundancy_score + modularity_score) / 2 * (1 - critical_density)
        }


def create_example_microservices_system():
    """Example: Microservices architecture"""
    analyzer = ResilienceAnalyzer()
    system = analyzer.create_system("microservices_shop", "software")

    # Components
    components = [
        Component("api_gateway", "API Gateway", "service", redundancy=2, critical=True),
        Component("auth_service", "Auth Service", "service", redundancy=2, critical=True),
        Component("product_service", "Product Service", "service", redundancy=3),
        Component("order_service", "Order Service", "service", redundancy=2),
        Component("payment_service", "Payment Service", "service", redundancy=2, critical=True),
        Component("inventory_db", "Inventory DB", "database", redundancy=1),
        Component("user_db", "User DB", "database", redundancy=2, critical=True),
        Component("cache", "Redis Cache", "cache", redundancy=2),
    ]

    for comp in components:
        analyzer.add_component("microservices_shop", comp)

    # Dependencies
    dependencies = [
        Dependency("api_gateway", "auth_service", strength=1.0),
        Dependency("api_gateway", "product_service", strength=0.8),
        Dependency("api_gateway", "order_service", strength=0.9),
        Dependency("order_service", "payment_service", strength=1.0),
        Dependency("order_service", "inventory_db", strength=1.0),
        Dependency("product_service", "inventory_db", strength=0.9),
        Dependency("product_service", "cache", strength=0.3, optional=True),
        Dependency("auth_service", "user_db", strength=1.0),
    ]

    for dep in dependencies:
        analyzer.add_dependency("microservices_shop", dep)

    print(f"✓ Created microservices example: {len(components)} components, {len(dependencies)} dependencies")
    return system


def create_example_biological_system():
    """Example: Simplified organ system"""
    analyzer = ResilienceAnalyzer()
    system = analyzer.create_system("human_circulatory", "biological")

    components = [
        Component("heart", "Heart", "organ", redundancy=1, critical=True, recovery_time=0),
        Component("left_lung", "Left Lung", "organ", redundancy=2, recovery_time=10),
        Component("right_lung", "Right Lung", "organ", redundancy=2, recovery_time=10),
        Component("liver", "Liver", "organ", redundancy=1, recovery_time=20),
        Component("left_kidney", "Left Kidney", "organ", redundancy=2, recovery_time=15),
        Component("right_kidney", "Right Kidney", "organ", redundancy=2, recovery_time=15),
        Component("bone_marrow", "Bone Marrow", "organ", redundancy=1, recovery_time=30),
    ]

    for comp in components:
        analyzer.add_component("human_circulatory", comp)

    dependencies = [
        Dependency("liver", "heart", strength=1.0),
        Dependency("left_kidney", "heart", strength=1.0),
        Dependency("right_kidney", "heart", strength=1.0),
        Dependency("left_lung", "heart", strength=1.0),
        Dependency("right_lung", "heart", strength=1.0),
        Dependency("bone_marrow", "heart", strength=1.0),
    ]

    for dep in dependencies:
        analyzer.add_dependency("human_circulatory", dep)

    print(f"✓ Created biological example: {len(components)} components, {len(dependencies)} dependencies")
    return system


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]
    analyzer = ResilienceAnalyzer()

    if command == "examples":
        print("Creating example systems...\n")
        create_example_microservices_system()
        create_example_biological_system()
        print(f"\nSystems saved to {MODELS_DIR}")
        print("\nTry:")
        print("  ./resilience_analyzer.py metrics microservices_shop")
        print("  ./resilience_analyzer.py simulate microservices_shop api_gateway")

    elif command == "metrics":
        if len(sys.argv) < 3:
            print("Usage: resilience_analyzer.py metrics <system_name>")
            return

        system_name = sys.argv[2]
        if system_name not in analyzer.systems:
            print(f"System '{system_name}' not found")
            return

        metrics = analyzer.calculate_metrics(system_name)
        system = analyzer.systems[system_name]

        print(f"\n📊 Resilience Metrics: {system_name} ({system.domain})")
        print("=" * 60)
        print(f"Components: {metrics['component_count']}")
        print(f"Dependencies: {metrics['dependency_count']}")
        print(f"Redundancy Score: {metrics['redundancy_score']:.2f} (% with redundancy)")
        print(f"Modularity Score: {metrics['modularity_score']:.2f} (isolation potential)")
        print(f"Critical Density: {metrics['critical_density']:.2f} (% critical)")
        print(f"Avg Dependency Strength: {metrics['avg_dependency_strength']:.2f}")
        print(f"\n🎯 Overall Resilience Estimate: {metrics['resilience_estimate']:.2f}")

    elif command == "simulate":
        if len(sys.argv) < 4:
            print("Usage: resilience_analyzer.py simulate <system_name> <component_id> [cascade|isolated]")
            return

        system_name = sys.argv[2]
        component_id = sys.argv[3]
        failure_mode = FailureMode.CASCADE
        if len(sys.argv) >= 5:
            mode_str = sys.argv[4].lower()
            failure_mode = FailureMode.CASCADE if mode_str == "cascade" else FailureMode.ISOLATED

        if system_name not in analyzer.systems:
            print(f"System '{system_name}' not found")
            return

        result = analyzer.simulate_failure(system_name, [component_id], failure_mode)

        print(f"\n🔥 Failure Simulation: {result.system_name}")
        print("=" * 60)
        print(f"Scenario: {result.scenario}")
        print(f"Initial failures: {', '.join(result.initial_failures)}")
        print(f"Cascade size: {result.cascade_size} components")
        print(f"Recovery time: {result.recovery_time} steps")
        print(f"System survived: {'✓ Yes' if result.system_survived else '✗ No'}")
        print(f"\nAvailability:")
        print(f"  Min: {result.metrics['min_availability']:.1%}")
        print(f"  Avg: {result.metrics['avg_availability']:.1%}")
        print(f"  Cascade ratio: {result.metrics['cascade_ratio']:.1%}")

    elif command == "compare":
        if len(sys.argv) < 4:
            print("Usage: resilience_analyzer.py compare <system1> <system2>")
            return

        sys1_name = sys.argv[2]
        sys2_name = sys.argv[3]

        if sys1_name not in analyzer.systems or sys2_name not in analyzer.systems:
            print("One or both systems not found")
            return

        metrics1 = analyzer.calculate_metrics(sys1_name)
        metrics2 = analyzer.calculate_metrics(sys2_name)

        print(f"\n⚖️  Resilience Comparison")
        print("=" * 70)
        print(f"{'Metric':<30} {sys1_name:<15} {sys2_name:<15}")
        print("-" * 70)
        print(f"{'Redundancy Score':<30} {metrics1['redundancy_score']:<15.2f} {metrics2['redundancy_score']:<15.2f}")
        print(f"{'Modularity Score':<30} {metrics1['modularity_score']:<15.2f} {metrics2['modularity_score']:<15.2f}")
        print(f"{'Critical Density':<30} {metrics1['critical_density']:<15.2f} {metrics2['critical_density']:<15.2f}")
        print(f"{'Overall Resilience':<30} {metrics1['resilience_estimate']:<15.2f} {metrics2['resilience_estimate']:<15.2f}")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
