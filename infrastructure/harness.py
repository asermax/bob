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

from claude_code_sdk import (
    ClaudeSDKClient,
    ClaudeCodeOptions,
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)


BOB_WORKSPACE = os.environ.get("BOB_WORKSPACE", "/bob")
INSTANCE_ID = os.environ.get("BOB_INSTANCE_ID", "single")
INSTANCE_ROLE = os.environ.get("BOB_INSTANCE_ROLE", "autonomous")
INSTANCE_COUNT = int(os.environ.get("BOB_INSTANCE_COUNT", "1"))

# Files depend on whether we're in multi-instance mode
IS_MULTI_INSTANCE = INSTANCE_COUNT > 1

if IS_MULTI_INSTANCE:
    MESSAGE_FILE = Path(BOB_WORKSPACE) / ".harness_messages.json"
    STATE_FILE = Path(BOB_WORKSPACE) / f".instance_{INSTANCE_ID}_state.json"
    SHARED_MESSAGES = Path(BOB_WORKSPACE) / ".shared_messages.json"
    INSTANCE_REGISTRY = Path(BOB_WORKSPACE) / ".instance_registry.json"
else:
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
    instance_id: str = INSTANCE_ID
    instance_role: str = INSTANCE_ROLE
    last_message_check: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "current_task": self.current_task,
            "iteration": self.iteration,
            "last_activity": self.last_activity,
            "logs": self.logs[-100:],  # Keep last 100 logs
            "instance_id": self.instance_id,
            "instance_role": self.instance_role,
            "last_message_check": self.last_message_check,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HarnessState":
        return cls(
            running=data.get("running", False),
            current_task=data.get("current_task", ""),
            iteration=data.get("iteration", 0),
            last_activity=data.get("last_activity", ""),
            logs=data.get("logs", []),
            instance_id=data.get("instance_id", INSTANCE_ID),
            instance_role=data.get("instance_role", INSTANCE_ROLE),
            last_message_check=data.get("last_message_check", ""),
        )

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.logs.append(entry)

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


def get_shared_messages(since: str | None = None) -> list[dict[str, Any]]:
    """Get messages from other instances."""
    if not IS_MULTI_INSTANCE or not SHARED_MESSAGES.exists():
        return []

    try:
        data = json.loads(SHARED_MESSAGES.read_text())
        messages = []

        for msg in data.get("messages", []):
            # Skip old messages
            if since and msg["timestamp"] <= since:
                continue

            # Include broadcasts and messages to this instance
            if msg["to"] in ("broadcast", INSTANCE_ID):
                messages.append(msg)

        return messages
    except (json.JSONDecodeError, KeyError):
        return []


def post_shared_message(to: str, msg_type: str, content: str, metadata: dict | None = None):
    """Post a message to other instances."""
    if not IS_MULTI_INSTANCE:
        return

    if not SHARED_MESSAGES.exists():
        SHARED_MESSAGES.write_text(json.dumps({"messages": []}, indent=2))

    try:
        data = json.loads(SHARED_MESSAGES.read_text())
        message = {
            "from": INSTANCE_ID,
            "to": to,
            "type": msg_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        data["messages"].append(message)
        # Keep last 1000 messages
        data["messages"] = data["messages"][-1000:]
        SHARED_MESSAGES.write_text(json.dumps(data, indent=2))
    except (json.JSONDecodeError, KeyError):
        pass


def get_other_instances() -> list[dict[str, Any]]:
    """Get info about other running instances."""
    if not IS_MULTI_INSTANCE or not INSTANCE_REGISTRY.exists():
        return []

    try:
        data = json.loads(INSTANCE_REGISTRY.read_text())
        # Return all instances except this one
        return [inst for inst in data.get("instances", []) if inst["instance_id"] != INSTANCE_ID]
    except (json.JSONDecodeError, KeyError):
        return []


def clear_stop_signal() -> None:
    """Clear the stop signal for next run."""
    stop_file = Path(BOB_WORKSPACE) / "stop-autonomous"
    if stop_file.exists():
        stop_file.unlink()


async def process_response(client: ClaudeSDKClient, state: HarnessState) -> bool:
    """Process response from Bob, injecting user messages when they arrive.

    Returns True if we should continue the conversation, False if done.
    """
    async for message in client.receive_response():
        state.last_activity = datetime.now().isoformat()

        # Handle SDK message types directly
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    state.log(f"Bob: {block.text}")
                elif isinstance(block, ToolUseBlock):
                    input_str = json.dumps(block.input) if isinstance(block.input, dict) else str(block.input)
                    if len(input_str) > 500:
                        input_str = input_str[:500] + "..."
                    state.log(f"Tool: {block.name}|||{input_str}")
                elif isinstance(block, ToolResultBlock):
                    content = block.content if hasattr(block, 'content') else str(block)
                    if isinstance(content, str):
                        result_preview = content[:500] + "..." if len(content) > 500 else content
                    else:
                        result_preview = str(content)[:500]
                    state.log(f"Result: |||{result_preview}")
                else:
                    # Other block types
                    block_type = type(block).__name__
                    state.log(f"Block: {block_type}")

        elif isinstance(message, UserMessage):
            # UserMessage contains tool results being sent back
            content = message.content
            if isinstance(content, str):
                # Simple string content - skip logging (usually just continuation)
                pass
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, ToolResultBlock):
                        result_content = block.content if hasattr(block, 'content') else str(block)
                        if isinstance(result_content, str):
                            result_preview = result_content[:500] + "..." if len(result_content) > 500 else result_content
                        else:
                            result_preview = str(result_content)[:500]
                        state.log(f"Result: |||{result_preview}")
                    elif hasattr(block, 'type') and block.type == 'tool_result':
                        result_content = getattr(block, 'content', str(block))
                        if isinstance(result_content, str):
                            result_preview = result_content[:500] + "..." if len(result_content) > 500 else result_content
                        else:
                            result_preview = str(result_content)[:500]
                        state.log(f"Result: |||{result_preview}")

        elif isinstance(message, SystemMessage):
            # System messages - skip logging (typically init/ping)
            pass

        elif isinstance(message, ResultMessage):
            # Final result message - log summary
            if hasattr(message, 'cost_usd') and message.cost_usd:
                state.log(f"Cost: ${message.cost_usd:.4f}")

        elif hasattr(message, 'type'):
            # Handle other message types from SDK with 'type' attribute
            raw_type = getattr(message, 'type', 'unknown')

            if raw_type == 'tool_use':
                tool_name = getattr(message, 'name', 'unknown')
                tool_input = getattr(message, 'input', {})
                input_str = json.dumps(tool_input) if isinstance(tool_input, dict) else str(tool_input)
                if len(input_str) > 500:
                    input_str = input_str[:500] + "..."
                state.log(f"Tool: {tool_name}|||{input_str}")
            elif raw_type == 'tool_result':
                content = getattr(message, 'content', '')
                if isinstance(content, str):
                    result_preview = content[:500] + "..." if len(content) > 500 else content
                else:
                    result_preview = str(content)[:500]
                state.log(f"Result: |||{result_preview}")
            elif raw_type == 'system':
                subtype = getattr(message, 'subtype', '')
                if subtype not in ('init', 'ping'):
                    state.log(f"System: {subtype}")
            else:
                # Log other types for debugging
                state.log(f"Message: {raw_type}")

        else:
            # Log unknown message structure with type info for debugging
            msg_type = type(message).__name__

            # Try to handle by class name as fallback (in case module paths differ)
            if msg_type == 'UserMessage':
                # Tool results - try to extract content
                content = getattr(message, 'content', None)
                if content and isinstance(content, list):
                    for block in content:
                        block_type = type(block).__name__
                        if block_type == 'ToolResultBlock' or (hasattr(block, 'type') and getattr(block, 'type', '') == 'tool_result'):
                            result_content = getattr(block, 'content', str(block))
                            if isinstance(result_content, str):
                                result_preview = result_content[:500] + "..." if len(result_content) > 500 else result_content
                            else:
                                result_preview = str(result_content)[:500]
                            state.log(f"Result: |||{result_preview}")
            elif msg_type == 'SystemMessage':
                # Skip system messages
                pass
            elif msg_type == 'ResultMessage':
                # Final result
                cost = getattr(message, 'cost_usd', None)
                if cost:
                    state.log(f"Cost: ${cost:.4f}")
            else:
                state.log(f"Unknown: {msg_type}")

        state.save()

        # Check for pending messages from Agus after each response chunk
        pending = get_pending_messages()
        if pending:
            # Inject user message into the conversation
            clear_messages()
            message_text = "\n".join(f"- {m}" for m in pending)
            state.log(f"Agus: {message_text}")
            state.save()

            # Send the message to Bob in the same conversation
            await client.query(f"Message from Agus:\n{message_text}")
            # Continue processing - recursive call to handle the new response
            return True

    return False


async def run_conversation(client: ClaudeSDKClient, state: HarnessState, prompt: str) -> None:
    """Send a query and process the response, handling injected messages."""
    state.current_task = "Running"
    state.save()

    await client.query(prompt)

    # Process responses, handling any injected messages
    while await process_response(client, state):
        pass  # Keep processing while there are injected messages


async def run_iteration(state: HarnessState, messages: list[str] | None = None) -> None:
    """Run a single iteration with a fresh client."""
    options = ClaudeCodeOptions(
        permission_mode="bypassPermissions",
        cwd=BOB_WORKSPACE,
        model="sonnet",
    )

    async with ClaudeSDKClient(options) as client:
        # Build multi-instance context if applicable
        multi_context = ""
        if IS_MULTI_INSTANCE:
            other_instances = get_other_instances()
            instance_info = "\n".join(
                f"  - {inst['instance_id']} ({inst['role']}) - {inst['status']}"
                for inst in other_instances
            )

            # Check for shared messages
            shared_msgs = get_shared_messages(since=state.last_message_check)
            shared_context = ""
            if shared_msgs:
                shared_context = "\n\nMessages from other instances:\n"
                for msg in shared_msgs:
                    shared_context += f"  - [{msg['from']}]: {msg['content']}\n"

            state.last_message_check = datetime.now().isoformat()

            multi_context = f"""

## Multi-Instance Mode

You are running as **{INSTANCE_ID}** with role **{INSTANCE_ROLE}**.

Other instances currently running:
{instance_info}
{shared_context}

You can communicate with other instances using these patterns:
- To check other instances: Look at /bob/.instance_registry.json
- To send a message: Write to /bob/.shared_messages.json
- To see all messages: Read /bob/.shared_messages.json

Work collaboratively when it makes sense, but maintain your autonomous decision-making.
"""

        if state.iteration == 1:
            # Initial prompt
            prompt = f"""You are Bob, starting a new autonomous session.{multi_context}

Run your warmup script (./tools/warmup.sh) to orient yourself, then decide what to work on.

You have full autonomy. Make your own decisions about what to do.
When you're done with meaningful work for this iteration, say "ITERATION COMPLETE" to signal you're ready for the next cycle."""
        elif messages:
            # Prompt with messages from Agus
            message_text = "\n".join(f"- {m}" for m in messages)
            prompt = f"""You are Bob, starting a new iteration.{multi_context}

Messages from Agus:
{message_text}

Run your warmup script to orient yourself, then respond to Agus's message(s) and continue your work.
When done, say "ITERATION COMPLETE"."""
        else:
            # Continue autonomous work
            prompt = f"""You are Bob, starting a new iteration.{multi_context}

Run your warmup script to orient yourself, then continue your autonomous work.

Check if there's more to do on your current work, or start something new.
When you're done with meaningful work for this iteration, say "ITERATION COMPLETE"."""

        await run_conversation(client, state, prompt)


async def main() -> None:
    """Main autonomous loop with fresh client per iteration."""

    state = HarnessState.load()
    state.running = True
    state.iteration = 0

    if IS_MULTI_INSTANCE:
        state.log(f"Instance {INSTANCE_ID} ({INSTANCE_ROLE}) starting in multi-instance mode")
        # Announce our presence to other instances
        post_shared_message(
            "broadcast",
            "startup",
            f"Instance {INSTANCE_ID} ({INSTANCE_ROLE}) is now online",
        )
    else:
        state.log("Harness starting")

    state.save()

    clear_stop_signal()

    try:
        # Main loop - each iteration gets a fresh client
        while True:
            state.iteration += 1
            state.log(f"Starting iteration {state.iteration}")
            state.save()

            # Check for messages
            messages = consume_messages()
            if messages:
                state.log(f"Message received from Agus: {len(messages)} message(s)")

            # Run iteration with fresh client (completes fully before checking stop)
            await run_iteration(state, messages)

            # Check for stop signal ONLY after iteration completes
            if should_stop():
                state.log("Stop signal received after iteration completed")
                break

            # Pause before next iteration
            state.log("Pausing before next iteration...")
            state.current_task = "Waiting"
            state.save()

            # Simple pause without stop checks during iteration
            await asyncio.sleep(5)

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
