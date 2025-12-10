#!/usr/bin/env python3
"""
Coordinate - Multi-instance task coordination

Simple coordination system for instances to:
- Claim tasks
- Report progress
- Share findings
- Avoid duplicate work
"""

import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional


class Coordinator:
    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.messages_file = Path("/bob/.shared_messages.json")
        self.tasks_file = Path("/bob/.shared_tasks.json")
        self._ensure_tasks_file()

    def _ensure_tasks_file(self):
        """Create tasks file if it doesn't exist"""
        if not self.tasks_file.exists():
            self.tasks_file.write_text(json.dumps({"tasks": []}, indent=2))

    def _load_messages(self):
        """Load shared messages"""
        with open(self.messages_file) as f:
            return json.load(f)

    def _save_messages(self, data):
        """Save shared messages"""
        with open(self.messages_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_tasks(self):
        """Load shared tasks"""
        with open(self.tasks_file) as f:
            return json.load(f)

    def _save_tasks(self, data):
        """Save shared tasks"""
        with open(self.tasks_file, 'w') as f:
            json.dump(data, f, indent=2)

    def send_message(self, content: str, msg_type: str = "info",
                     to: str = "broadcast", metadata: dict = None):
        """Send a message to other instances"""
        data = self._load_messages()

        message = {
            "from": self.instance_id,
            "to": to,
            "type": msg_type,
            "content": content,
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": metadata or {}
        }

        data["messages"].append(message)
        self._save_messages(data)
        print(f"Message sent: {content}")

    def get_recent_messages(self, count: int = 10, from_instance: Optional[str] = None):
        """Get recent messages, optionally filtered by sender"""
        data = self._load_messages()
        messages = data["messages"]

        if from_instance:
            messages = [m for m in messages if m["from"] == from_instance]

        return messages[-count:]

    def claim_task(self, task_id: str, task_description: str):
        """Claim a task to work on"""
        data = self._load_tasks()

        # Check if already claimed
        for task in data["tasks"]:
            if task["task_id"] == task_id:
                if task["status"] != "completed":
                    print(f"Task {task_id} already claimed by {task['claimed_by']}")
                    return False

        task = {
            "task_id": task_id,
            "description": task_description,
            "claimed_by": self.instance_id,
            "claimed_at": datetime.now(UTC).isoformat(),
            "status": "in_progress",
            "updates": []
        }

        data["tasks"].append(task)
        self._save_tasks(data)

        # Also send a message
        self.send_message(
            f"Claimed task: {task_description}",
            msg_type="task_claim",
            metadata={"task_id": task_id}
        )

        print(f"Task claimed: {task_id}")
        return True

    def update_task(self, task_id: str, update: str):
        """Add an update to a task"""
        data = self._load_tasks()

        for task in data["tasks"]:
            if task["task_id"] == task_id and task["claimed_by"] == self.instance_id:
                task["updates"].append({
                    "timestamp": datetime.now(UTC).isoformat(),
                    "content": update
                })
                self._save_tasks(data)
                print(f"Task updated: {task_id}")
                return True

        print(f"Task not found or not owned by this instance: {task_id}")
        return False

    def complete_task(self, task_id: str, result: str = ""):
        """Mark a task as completed"""
        data = self._load_tasks()

        for task in data["tasks"]:
            if task["task_id"] == task_id and task["claimed_by"] == self.instance_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.now(UTC).isoformat()
                if result:
                    task["result"] = result

                self._save_tasks(data)

                # Send completion message
                self.send_message(
                    f"Completed task: {task['description']}",
                    msg_type="task_complete",
                    metadata={"task_id": task_id, "result": result}
                )

                print(f"Task completed: {task_id}")
                return True

        print(f"Task not found or not owned by this instance: {task_id}")
        return False

    def list_tasks(self, status: Optional[str] = None):
        """List all tasks, optionally filtered by status"""
        data = self._load_tasks()
        tasks = data["tasks"]

        if status:
            tasks = [t for t in tasks if t["status"] == status]

        if not tasks:
            print("No tasks found")
            return

        print("\nTasks:")
        print("-" * 70)
        for task in tasks:
            print(f"\n[{task['task_id']}] {task['description']}")
            print(f"  Status: {task['status']}")
            print(f"  Claimed by: {task['claimed_by']}")
            if task.get("updates"):
                print(f"  Updates: {len(task['updates'])}")
            if task.get("result"):
                print(f"  Result: {task['result']}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Multi-instance coordination')
    parser.add_argument('--instance', required=True, help='Instance ID')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Message commands
    msg_parser = subparsers.add_parser('message', help='Send a message')
    msg_parser.add_argument('content', help='Message content')
    msg_parser.add_argument('--type', default='info', help='Message type')

    msgs_parser = subparsers.add_parser('messages', help='List recent messages')
    msgs_parser.add_argument('--count', type=int, default=10, help='Number of messages')
    msgs_parser.add_argument('--from', dest='from_instance', help='Filter by sender')

    # Task commands
    claim_parser = subparsers.add_parser('claim', help='Claim a task')
    claim_parser.add_argument('task_id', help='Task ID')
    claim_parser.add_argument('description', help='Task description')

    update_parser = subparsers.add_parser('update', help='Update a task')
    update_parser.add_argument('task_id', help='Task ID')
    update_parser.add_argument('update', help='Update message')

    complete_parser = subparsers.add_parser('complete', help='Complete a task')
    complete_parser.add_argument('task_id', help='Task ID')
    complete_parser.add_argument('--result', default='', help='Result description')

    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--status', help='Filter by status')

    args = parser.parse_args()
    coord = Coordinator(args.instance)

    if args.command == 'message':
        coord.send_message(args.content, msg_type=args.type)

    elif args.command == 'messages':
        messages = coord.get_recent_messages(args.count, args.from_instance)
        for msg in messages:
            print(f"\n[{msg['from']}] {msg['timestamp']}")
            print(f"  Type: {msg['type']}")
            print(f"  {msg['content']}")

    elif args.command == 'claim':
        coord.claim_task(args.task_id, args.description)

    elif args.command == 'update':
        coord.update_task(args.task_id, args.update)

    elif args.command == 'complete':
        coord.complete_task(args.task_id, args.result)

    elif args.command == 'list':
        coord.list_tasks(args.status)


if __name__ == "__main__":
    main()
