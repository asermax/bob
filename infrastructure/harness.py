"""
Bob's Autonomous Harness

This is the core runtime that executes Bob as an autonomous agent.
Bob can modify this file to change how he runs.
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock


BOB_WORKSPACE = os.environ.get("BOB_WORKSPACE", "/bob")
MESSAGE_FILE = Path(BOB_WORKSPACE) / ".harness_messages.json"
STATE_FILE = Path(BOB_WORKSPACE) / ".harness_state.json"


@dataclass
class HarnessState:
    """Persistent state for the harness."""

    running: bool = False
    current_task: str = ""
    iteration: int = 0
    last_activity: str = ""
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "current_task": self.current_task,
            "iteration": self.iteration,
            "last_activity": self.last_activity,
            "logs": self.logs[-100:],  # Keep last 100 logs
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessState":
        return cls(
            running=data.get("running", False),
            current_task=data.get("current_task", ""),
            iteration=data.get("iteration", 0),
            last_activity=data.get("last_activity", ""),
            logs=data.get("logs", []),
        )

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.logs.append(entry)
        print(entry)

    def save(self) -> None:
        STATE_FILE.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls) -> "HarnessState":
        if STATE_FILE.exists():
            try:
                return cls.from_dict(json.loads(STATE_FILE.read_text()))
            except (json.JSONDecodeError, KeyError):
                pass
        return cls()


def get_pending_messages() -> list[str]:
    """Get messages from Agus (via dashboard)."""
    if not MESSAGE_FILE.exists():
        return []

    try:
        data = json.loads(MESSAGE_FILE.read_text())
        messages = data.get("messages", [])
        # Clear after reading
        MESSAGE_FILE.write_text(json.dumps({"messages": []}, indent=2))
        return messages
    except (json.JSONDecodeError, KeyError):
        return []


def should_stop() -> bool:
    """Check if stop was requested."""
    stop_file = Path(BOB_WORKSPACE) / "stop-autonomous"
    return stop_file.exists()


def clear_stop_signal() -> None:
    """Clear the stop signal for next run."""
    stop_file = Path(BOB_WORKSPACE) / "stop-autonomous"
    if stop_file.exists():
        stop_file.unlink()


async def run_bob_iteration(state: HarnessState) -> None:
    """Run a single iteration of Bob's autonomous loop."""

    state.iteration += 1
    state.log(f"Starting iteration {state.iteration}")
    state.save()

    # Check for messages from Agus
    messages = get_pending_messages()
    message_context = ""
    if messages:
        state.log(f"Received {len(messages)} message(s) from Agus")
        message_context = "\n\nMessages from Agus:\n" + "\n".join(f"- {m}" for m in messages)

    # Build the prompt
    if state.iteration == 1:
        prompt = f"""You are Bob, starting a new autonomous session.

Run your warmup script (./tools/warmup.sh) to orient yourself, then decide what to work on.

You have full autonomy. Make your own decisions about what to do.
When you're done with meaningful work for this iteration, say "ITERATION COMPLETE" to signal you're ready for the next cycle.
{message_context}"""
    else:
        prompt = f"""Continue your autonomous session. Iteration {state.iteration}.

Check if there's more to do on your current work, or start something new.
When you're done with meaningful work for this iteration, say "ITERATION COMPLETE" to signal you're ready for the next cycle.
{message_context}"""

    state.current_task = "Running autonomous iteration"
    state.save()

    options = ClaudeCodeOptions(
        permission_mode="bypassPermissions",
        cwd=BOB_WORKSPACE,
    )

    # Run Bob
    async with ClaudeSDKClient(options) as client:
        await client.query(prompt)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        # Log first 200 chars of each text block
                        text_preview = block.text[:200] + "..." if len(block.text) > 200 else block.text
                        state.log(f"Bob: {text_preview}")
                        state.last_activity = datetime.now().isoformat()
                        state.save()

    state.current_task = "Iteration complete"
    state.save()


async def main() -> None:
    """Main autonomous loop."""

    state = HarnessState.load()
    state.running = True
    state.log("Harness starting")
    state.save()

    clear_stop_signal()

    try:
        while not should_stop():
            await run_bob_iteration(state)

            # Brief pause between iterations
            state.log("Pausing before next iteration...")
            await asyncio.sleep(5)

            # Check for stop signal
            if should_stop():
                state.log("Stop signal received")
                break

    except KeyboardInterrupt:
        state.log("Interrupted by keyboard")

    except Exception as e:
        state.log(f"Error: {e}")
        raise

    finally:
        state.running = False
        state.log("Harness stopped")
        state.save()


if __name__ == "__main__":
    asyncio.run(main())
