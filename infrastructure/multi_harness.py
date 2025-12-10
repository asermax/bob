"""
Bob's Multi-Instance Orchestrator

Spawns multiple instances of Bob running simultaneously, Tachikoma-style.
Manages shared communication and collective state.
"""

import asyncio
import json
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


BOB_WORKSPACE = Path("/bob")
INSTANCE_REGISTRY = BOB_WORKSPACE / ".instance_registry.json"
SHARED_MESSAGES = BOB_WORKSPACE / ".shared_messages.json"
SHARED_MEMORY = BOB_WORKSPACE / ".shared_memory.json"
STOP_FILE = BOB_WORKSPACE / "stop-autonomous"


@dataclass
class InstanceInfo:
    """Info about a running instance."""

    instance_id: str
    role: str
    pid: int
    started_at: str
    status: str = "starting"
    last_heartbeat: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "role": self.role,
            "pid": self.pid,
            "started_at": self.started_at,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
        }


@dataclass
class SharedMessage:
    """Message passed between instances."""

    from_instance: str
    to_instance: str  # "broadcast" or specific instance_id
    msg_type: str
    content: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "from": self.from_instance,
            "to": self.to_instance,
            "type": self.msg_type,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SharedMessage":
        return cls(
            from_instance=data["from"],
            to_instance=data["to"],
            msg_type=data["type"],
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )


class SharedState:
    """Manages shared state between instances."""

    @staticmethod
    def init_files():
        """Initialize shared state files."""
        if not INSTANCE_REGISTRY.exists():
            INSTANCE_REGISTRY.write_text(json.dumps({"instances": []}, indent=2))

        if not SHARED_MESSAGES.exists():
            SHARED_MESSAGES.write_text(json.dumps({"messages": []}, indent=2))

        if not SHARED_MEMORY.exists():
            SHARED_MEMORY.write_text(json.dumps({
                "findings": [],
                "decisions": [],
                "learnings": [],
            }, indent=2))

    @staticmethod
    def register_instance(info: InstanceInfo):
        """Register a new instance."""
        data = json.loads(INSTANCE_REGISTRY.read_text())
        data["instances"].append(info.to_dict())
        INSTANCE_REGISTRY.write_text(json.dumps(data, indent=2))

    @staticmethod
    def update_instance_status(instance_id: str, status: str):
        """Update instance status."""
        data = json.loads(INSTANCE_REGISTRY.read_text())
        for instance in data["instances"]:
            if instance["instance_id"] == instance_id:
                instance["status"] = status
                instance["last_heartbeat"] = datetime.now().isoformat()
                break
        INSTANCE_REGISTRY.write_text(json.dumps(data, indent=2))

    @staticmethod
    def get_instances() -> list[dict[str, Any]]:
        """Get all registered instances."""
        data = json.loads(INSTANCE_REGISTRY.read_text())
        return data.get("instances", [])

    @staticmethod
    def post_message(msg: SharedMessage):
        """Post a message to shared queue."""
        data = json.loads(SHARED_MESSAGES.read_text())
        data["messages"].append(msg.to_dict())
        # Keep last 1000 messages
        data["messages"] = data["messages"][-1000:]
        SHARED_MESSAGES.write_text(json.dumps(data, indent=2))

    @staticmethod
    def get_messages_for(instance_id: str, since: str | None = None) -> list[SharedMessage]:
        """Get messages for a specific instance since timestamp."""
        data = json.loads(SHARED_MESSAGES.read_text())
        messages = []

        for msg_data in data["messages"]:
            # Skip old messages if since provided
            if since and msg_data["timestamp"] <= since:
                continue

            # Include broadcasts and messages to this instance
            if msg_data["to"] in ("broadcast", instance_id):
                messages.append(SharedMessage.from_dict(msg_data))

        return messages

    @staticmethod
    def add_finding(instance_id: str, finding: str):
        """Add a finding to shared memory."""
        data = json.loads(SHARED_MEMORY.read_text())
        data["findings"].append({
            "instance": instance_id,
            "timestamp": datetime.now().isoformat(),
            "content": finding,
        })
        # Keep last 500 findings
        data["findings"] = data["findings"][-500:]
        SHARED_MEMORY.write_text(json.dumps(data, indent=2))


async def run_instance(instance_id: str, role: str, num_instances: int):
    """Run a single Bob instance."""
    import os

    # Set environment variable for this instance
    env = os.environ.copy()
    env["BOB_INSTANCE_ID"] = instance_id
    env["BOB_INSTANCE_ROLE"] = role
    env["BOB_INSTANCE_COUNT"] = str(num_instances)

    # Run the harness as subprocess
    proc = await asyncio.create_subprocess_exec(
        "python3",
        "/bob/infrastructure/harness.py",
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Register instance
    info = InstanceInfo(
        instance_id=instance_id,
        role=role,
        pid=proc.pid,
        started_at=datetime.now().isoformat(),
        status="running",
    )
    SharedState.register_instance(info)

    print(f"[Orchestrator] Started {instance_id} ({role}) - PID {proc.pid}")

    # Monitor the process
    try:
        await proc.wait()
        print(f"[Orchestrator] Instance {instance_id} exited with code {proc.returncode}")
    except Exception as e:
        print(f"[Orchestrator] Instance {instance_id} error: {e}")
        proc.kill()


async def main():
    """Main orchestrator - spawns and manages multiple instances."""

    # Parse command line args
    num_instances = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    if num_instances < 2 or num_instances > 4:
        print("Error: Number of instances must be between 2 and 4")
        sys.exit(1)

    print("=" * 70)
    print("Bob's Multi-Instance Orchestrator")
    print("=" * 70)
    print(f"Spawning {num_instances} instances...")
    print()

    # Initialize shared state
    SharedState.init_files()

    # Define roles (cycle through them)
    roles = ["explorer", "builder", "reflector", "coordinator"]

    # Start instances
    tasks = []
    for i in range(num_instances):
        instance_id = f"instance_{i+1}"
        role = roles[i % len(roles)]

        task = asyncio.create_task(run_instance(instance_id, role, num_instances))
        tasks.append(task)

        # Small delay between starts
        await asyncio.sleep(1)

    print()
    print("=" * 70)
    print("All instances started. Press Ctrl+C to stop.")
    print("Dashboard: http://localhost:3141")
    print("=" * 70)
    print()

    # Wait for all instances
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n[Orchestrator] Shutting down...")
        for task in tasks:
            task.cancel()

        # Signal all instances to stop
        STOP_FILE.touch()

        # Wait a bit for graceful shutdown
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
