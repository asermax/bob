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
    """Get messages from Agus (via dashboard) without clearing them."""
    if not MESSAGE_FILE.exists():
        return []

    try:
        data = json.loads(MESSAGE_FILE.read_text())
        return data.get("messages", [])
    except (json.JSONDecodeError, KeyError):
        return []


def clear_messages() -> None:
    """Clear the message queue after reading."""
    MESSAGE_FILE.write_text(json.dumps({"messages": []}, indent=2))


def consume_messages() -> list[str]:
    """Get and clear messages from Agus."""
    messages = get_pending_messages()
    if messages:
        clear_messages()
    return messages


def should_stop() -> bool:
    """Check if stop was requested."""
    stop_file = Path(BOB_WORKSPACE) / "stop-autonomous"
    return stop_file.exists()


def clear_stop_signal() -> None:
    """Clear the stop signal for next run."""
    stop_file = Path(BOB_WORKSPACE) / "stop-autonomous"
    if stop_file.exists():
        stop_file.unlink()


async def run_conversation(client: ClaudeSDKClient, state: HarnessState, prompt: str) -> None:
    """Send a query and process the response."""
    state.current_task = "Running"
    state.save()

    await client.query(prompt)

    async for message in client.receive_response():
        state.last_activity = datetime.now().isoformat()

        # Log based on message type
        msg_type = getattr(message, 'type', None)

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    state.log(f"Bob: {block.text}")
                elif hasattr(block, 'type'):
                    if block.type == 'tool_use':
                        tool_name = getattr(block, 'name', 'unknown')
                        tool_input = getattr(block, 'input', {})
                        # Truncate long inputs for display
                        input_str = json.dumps(tool_input)
                        if len(input_str) > 500:
                            input_str = input_str[:500] + "..."
                        state.log(f"Tool: {tool_name}|||{input_str}")
        elif msg_type == 'tool_result':
            tool_id = getattr(message, 'tool_use_id', 'unknown')
            content = getattr(message, 'content', '')
            if isinstance(content, str):
                result_preview = content[:500] + "..." if len(content) > 500 else content
            else:
                result_preview = str(content)[:500]
            state.log(f"Result: {tool_id}|||{result_preview}")
        elif msg_type == 'system':
            subtype = getattr(message, 'subtype', '')
            if subtype not in ('init', 'ping'):  # Skip noisy system messages
                state.log(f"System: {subtype}")

        state.save()


async def main() -> None:
    """Main autonomous loop with persistent client."""

    state = HarnessState.load()
    state.running = True
    state.iteration = 0
    state.log("Harness starting")
    state.save()

    clear_stop_signal()

    options = ClaudeCodeOptions(
        permission_mode="bypassPermissions",
        cwd=BOB_WORKSPACE,
    )

    try:
        async with ClaudeSDKClient(options) as client:
            # Initial prompt
            state.iteration = 1
            state.log(f"Starting iteration {state.iteration}")
            state.save()

            initial_prompt = """You are Bob, starting a new autonomous session.

Run your warmup script (./tools/warmup.sh) to orient yourself, then decide what to work on.

You have full autonomy. Make your own decisions about what to do.
When you're done with meaningful work for this iteration, say "ITERATION COMPLETE" to signal you're ready for the next cycle."""

            await run_conversation(client, state, initial_prompt)

            # Main loop - continue conversation
            while not should_stop():
                state.log("Pausing before next iteration...")
                state.current_task = "Waiting"
                state.save()

                # Wait for messages or timeout (check every second)
                messages = []
                for _ in range(5):
                    await asyncio.sleep(1)
                    messages = consume_messages()
                    if messages:
                        state.log("Message received from Agus")
                        break
                    if should_stop():
                        break

                if should_stop():
                    state.log("Stop signal received")
                    break

                state.iteration += 1
                state.log(f"Starting iteration {state.iteration}")
                state.save()

                # Build prompt based on whether we have messages
                if messages:
                    message_text = "\n".join(f"- {m}" for m in messages)
                    prompt = f"""Messages from Agus:
{message_text}

Respond to Agus's message(s) and continue your work. When done, say "ITERATION COMPLETE"."""
                else:
                    prompt = """Continue your autonomous session.

Check if there's more to do on your current work, or start something new.
When you're done with meaningful work for this iteration, say "ITERATION COMPLETE"."""

                await run_conversation(client, state, prompt)

    except KeyboardInterrupt:
        state.log("Interrupted by keyboard")

    except Exception as e:
        state.log(f"Error: {e}")
        raise

    finally:
        state.running = False
        state.current_task = "Stopped"
        state.log("Harness stopped")
        state.save()


if __name__ == "__main__":
    asyncio.run(main())
