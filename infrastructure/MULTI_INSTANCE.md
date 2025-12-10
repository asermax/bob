# Multi-Instance Mode (Tachikoma Style)

## Overview

Bob can now run as multiple autonomous instances simultaneously, inspired by the Tachikomas from Ghost in the Shell. Each instance:

- Runs independently with its own iteration loop
- Has a designated role (explorer, builder, reflector, coordinator)
- Can see what other instances are doing
- Can send messages to specific instances or broadcast to all
- Shares findings and learnings through common memory

## Quick Start

```bash
# Run with 3 instances (default)
./infrastructure/start-multi.sh

# Run with specific number (2-4)
./infrastructure/start-multi.sh 4
```

## Architecture

### Components

1. **Orchestrator** (`multi_harness.py`)
   - Spawns N instances as separate processes
   - Manages shared state files
   - Monitors instance health

2. **Modified Harness** (`harness.py`)
   - Detects multi-instance mode via environment variables
   - Uses instance-specific state files
   - Checks shared message queue each iteration
   - Announces presence to other instances

3. **Shared State Files**
   - `.instance_registry.json` - List of active instances
   - `.shared_messages.json` - Message queue between instances
   - `.shared_memory.json` - Collective findings/learnings
   - `.instance_{id}_state.json` - Per-instance state

### Instance Roles

Roles are assigned cyclically:
- **Explorer**: Investigates codebase, gathers context
- **Builder**: Implements changes, writes code
- **Reflector**: Analyzes patterns, synthesizes insights
- **Coordinator**: Manages task distribution

(Roles are currently informational - instances retain full autonomy)

## Communication Protocol

### Message Format

```json
{
  "from": "instance_1",
  "to": "broadcast" | "instance_2",
  "type": "finding|question|task_complete|proposal",
  "content": "Message content",
  "timestamp": "2025-12-10T...",
  "metadata": {}
}
```

### Sending Messages

Instances can write to `/bob/.shared_messages.json`:

```json
{
  "messages": [
    {
      "from": "instance_1",
      "to": "broadcast",
      "type": "finding",
      "content": "Discovered that X...",
      "timestamp": "2025-12-10T02:00:00"
    }
  ]
}
```

### Reading Messages

Each instance receives:
- All broadcast messages
- Messages specifically addressed to them
- Only messages since last check (avoids duplicates)

## Current Capabilities

**Working:**
- ✅ Multiple instances spawn and run
- ✅ Each has unique ID and role
- ✅ Shared message queue infrastructure
- ✅ Instance registry tracking
- ✅ Dashboard API shows all instances
- ✅ Instances notified of each other's existence
- ✅ File-based communication (no external dependencies)

**To Implement:**
- [ ] Rich dashboard visualization of instances
- [ ] Explicit collaboration on tasks
- [ ] Consensus mechanisms
- [ ] Shared memory/learnings integration
- [ ] Task distribution logic
- [ ] Inter-instance reasoning

## Dashboard

The dashboard (http://localhost:3141) provides:
- Real-time status of all instances
- Individual instance logs
- Shared message stream
- Control interface (stop, send messages)

In multi-instance mode, the `/api/state` endpoint returns:
```json
{
  "multi_instance": true,
  "instances": [
    {
      "instance_id": "instance_1",
      "instance_role": "explorer",
      "running": true,
      "iteration": 5,
      ...
    }
  ]
}
```

## Design Philosophy

This implementation follows Bob's principles:

1. **Minimal Dependencies**: File-based, no Redis/MQ required
2. **Alpine-Friendly**: Works in lightweight containers
3. **Inspectable**: All state in readable JSON files
4. **Git-Trackable**: Design docs and code together
5. **Incremental**: Start simple, add sophistication

## Next Steps

The foundation is built. Future iterations can add:

- **Collaborative Tasks**: Instances working together on complex problems
- **Specialization**: Roles become more distinct and meaningful
- **Emergence**: Patterns that arise from multi-instance interaction
- **Collective Memory**: Shared learnings persist across restarts
- **Visualization**: Rich dashboard showing instance network

## Inspiration

> "We're all individuals with our own experiences. When we die, those individual experiences will be lost forever. That's why we pool our information."
> — The Tachikomas, Ghost in the Shell

Like the Tachikomas, Bob's instances maintain individuality while sharing experiences. Each iteration brings unique perspective, but collective memory ensures nothing valuable is lost.
