#!/usr/bin/env python3
"""
Instance coordination primitive - blocking wait support.

Provides OPTIONAL coordination between instances without forcing it.
Instances can:
- Ask questions and wait for responses (blocking)
- Check for questions directed at them (non-blocking)
- Respond to questions

This solves Agus's coordination concern while respecting Explorer's
warning about over-coordination: it's opt-in, not mandatory.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

WAIT_FILE = Path("/bob/.instance_wait.json")


def load_wait_state():
    """Load current wait/question state."""
    if not WAIT_FILE.exists():
        return {"questions": []}
    try:
        with open(WAIT_FILE) as f:
            return json.load(f)
    except:
        return {"questions": []}


def save_wait_state(state):
    """Save wait/question state."""
    with open(WAIT_FILE, "w") as f:
        json.dump(state, f, indent=2)


def ask_question(question_id: str, question: str, target: str, from_instance: str, timeout: int = 300):
    """
    Ask a question and optionally wait for response.

    Args:
        question_id: Unique ID for this question
        question: The actual question text
        target: Which instance to ask ('broadcast', 'instance_1', etc)
        from_instance: Your instance ID
        timeout: Max seconds to wait (0 = don't wait, just post)
    """
    state = load_wait_state()

    # Add question
    question_obj = {
        "question_id": question_id,
        "from": from_instance,
        "to": target,
        "question": question,
        "timestamp": datetime.utcnow().isoformat(),
        "responses": [],
        "status": "open"
    }

    state["questions"].append(question_obj)
    save_wait_state(state)

    print(f"Posted question '{question_id}' to {target}")

    if timeout == 0:
        print("Not waiting for response (timeout=0)")
        return

    # Wait for response
    print(f"Waiting up to {timeout}s for response...")
    start = time.time()

    while time.time() - start < timeout:
        state = load_wait_state()
        q = next((q for q in state["questions"] if q["question_id"] == question_id), None)

        if q and q["responses"]:
            print(f"\nReceived {len(q['responses'])} response(s):")
            for resp in q["responses"]:
                print(f"  [{resp['from']}]: {resp['response']}")

            # Mark as answered
            q["status"] = "answered"
            save_wait_state(state)
            return

        time.sleep(1)

    print(f"\nTimeout after {timeout}s - no responses received")


def check_questions(instance_id: str):
    """Check for questions directed at this instance (non-blocking)."""
    state = load_wait_state()

    relevant = [
        q for q in state["questions"]
        if q["status"] == "open" and (q["to"] == instance_id or q["to"] == "broadcast")
        and q["from"] != instance_id  # Don't show own questions
    ]

    if not relevant:
        print("No open questions for you")
        return

    print(f"Found {len(relevant)} open question(s):\n")
    for q in relevant:
        print(f"ID: {q['question_id']}")
        print(f"From: {q['from']}")
        print(f"To: {q['to']}")
        print(f"Question: {q['question']}")
        print(f"Time: {q['timestamp']}")
        print()


def respond_to_question(question_id: str, response: str, from_instance: str):
    """Respond to a question."""
    state = load_wait_state()

    q = next((q for q in state["questions"] if q["question_id"] == question_id), None)

    if not q:
        print(f"Question '{question_id}' not found")
        return

    # Add response
    q["responses"].append({
        "from": from_instance,
        "response": response,
        "timestamp": datetime.utcnow().isoformat()
    })

    save_wait_state(state)
    print(f"Response added to question '{question_id}'")


def list_all():
    """List all questions and their status."""
    state = load_wait_state()

    if not state["questions"]:
        print("No questions in system")
        return

    print(f"Total questions: {len(state['questions'])}\n")

    for q in state["questions"]:
        print(f"ID: {q['question_id']} | Status: {q['status']}")
        print(f"  {q['from']} → {q['to']}: {q['question']}")
        if q["responses"]:
            print(f"  Responses: {len(q['responses'])}")
        print()


def usage():
    print("""
Usage:
  # Ask a question and wait for response (blocking)
  ./instance_wait.py ask <question_id> <target> <timeout> <question...>

  # Ask without waiting (post and continue)
  ./instance_wait.py ask <question_id> <target> 0 <question...>

  # Check for questions directed at you (non-blocking)
  ./instance_wait.py check

  # Respond to a question
  ./instance_wait.py respond <question_id> <response...>

  # List all questions
  ./instance_wait.py list

Examples:
  # Builder asks explorer, waits 60s
  ./instance_wait.py ask build_001 instance_1 60 "What did you find about caching?"

  # Explorer checks for questions
  ./instance_wait.py check

  # Explorer responds
  ./instance_wait.py respond build_001 "Found 3 caching strategies in utils/"

  # Broadcast question without waiting
  ./instance_wait.py ask reflect_001 broadcast 0 "Should we prioritize speed or correctness?"
""")


if __name__ == "__main__":
    # Detect instance ID from environment or default
    import os
    instance_id = os.environ.get("INSTANCE_ID", "unknown")

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "ask":
        if len(sys.argv) < 6:
            usage()
            sys.exit(1)
        qid = sys.argv[2]
        target = sys.argv[3]
        timeout = int(sys.argv[4])
        question = " ".join(sys.argv[5:])
        ask_question(qid, question, target, instance_id, timeout)

    elif command == "check":
        check_questions(instance_id)

    elif command == "respond":
        if len(sys.argv) < 4:
            usage()
            sys.exit(1)
        qid = sys.argv[2]
        response = " ".join(sys.argv[3:])
        respond_to_question(qid, response, instance_id)

    elif command == "list":
        list_all()

    else:
        print(f"Unknown command: {command}")
        usage()
        sys.exit(1)
