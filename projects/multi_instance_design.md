# Multi-Instance Collaborative System Design

## Vision

Like the Tachikomas - multiple autonomous instances of Bob running simultaneously, sharing experiences, collaborating on tasks, and building collective understanding.

## Current Architecture

**Single Instance:**
- One harness.py running as main loop
- One ClaudeSDKClient per iteration
- State in `.harness_state.json`
- Messages from Agus in `.harness_messages.json`
- Dashboard shows single instance status

## Proposed Multi-Instance Architecture

### Core Components

**1. Orchestrator (`multi_harness.py`)**
- Spawns N instances (configurable 2-4)
- Manages shared state
- Coordinates communication between instances
- Monitors health of all instances

**2. Shared Communication Layer**
- File-based message queue (simple, no external dependencies)
- Each instance has:
  - Own state file: `.instance_{id}_state.json`
  - Own log stream
- Shared resources:
  - `.shared_messages.json` - inter-instance messages
  - `.shared_memory.json` - collaborative memory/findings
  - `.instance_registry.json` - active instances

**3. Instance Types/Roles**
- **Explorer**: Investigates codebase, gathers context
- **Builder**: Implements changes, writes code
- **Reflector**: Analyzes patterns, synthesizes insights
- **Coordinator**: Manages task distribution (could rotate)

### Communication Protocol

**Message Structure:**
```json
{
  "from": "instance_1",
  "to": "broadcast|instance_2",
  "type": "finding|question|task_complete|proposal",
  "timestamp": "...",
  "content": "...",
  "metadata": {}
}
```

**Message Types:**
- `finding`: Share discovered information
- `question`: Ask other instances for input
- `task_complete`: Report completion
- `proposal`: Suggest approach or decision
- `consensus`: Agreement on direction

### Dashboard Evolution

**Multi-Instance View:**
- Grid/network visualization of instances
- Real-time message flow between instances
- Individual instance logs expandable
- Shared memory/findings panel
- Task distribution overview

**Visual Design:**
- Each instance as a node
- Messages as flowing lines between nodes
- Activity indicators (thinking/idle/writing)
- Tachikoma-inspired aesthetic?

### Implementation Phases

**Phase 1: Basic Multi-Instance (This iteration)**
- Create orchestrator that spawns 2-3 instances
- File-based message queue
- Simple dashboard showing all instances
- Basic message passing between instances

**Phase 2: Roles & Coordination**
- Define instance roles
- Task distribution logic
- Consensus mechanisms
- Richer message types

**Phase 3: Collective Memory**
- Shared learning across instances
- Pattern recognition across multiple perspectives
- Collaborative decision making
- Knowledge synthesis

## Technical Decisions

### Why File-Based Communication?
- No external dependencies (Redis/MQ)
- Simple to implement
- Works with current Docker setup
- Easy to inspect/debug
- Fits Alpine minimal approach

### Instance Lifecycle
- Orchestrator spawns all instances at start
- Each runs autonomous loop like current harness
- Check shared message queue periodically
- Can send messages to specific instances or broadcast
- Continue until orchestrator signals stop

### Docker Approach
- Single container runs orchestrator
- Orchestrator spawns multiple Python processes
- Each process runs modified harness.py
- Shared volume for all state files
- Dashboard polls all instance states

### Starting Simple
- First version: Just make instances aware of each other
- They can see each other's activity
- Can send simple text messages
- Dashboard shows all running
- **Then** add sophisticated collaboration

## Open Questions

1. How do instances decide what to work on?
   - Random selection?
   - Explicit role assignment?
   - Collaborative negotiation?

2. What happens if instances disagree?
   - Vote?
   - Defer to "coordinator"?
   - Explore both paths?

3. How much autonomy vs coordination?
   - Fully independent with sharing?
   - Tightly coordinated workflow?
   - Hybrid approach?

## Success Criteria

**Minimum Viable Multi-Instance:**
- [x] 2+ instances running simultaneously
- [x] Instances can see each other's status
- [x] Basic message passing works
- [x] Dashboard shows all instances
- [x] Agus can send messages to specific instances

**Tachikoma-Level:**
- [ ] Instances collaboratively solve problems
- [ ] Shared learning/memory accumulation
- [ ] Emergent coordination behaviors
- [ ] Different instances develop different "personalities"
- [ ] Meaningful discussion/debate between instances

## Next Steps

1. Create `multi_harness.py` orchestrator
2. Modify harness to accept instance_id parameter
3. Implement shared message queue
4. Update dashboard for multi-instance view
5. Test with 2 instances doing simple collaboration
6. Iterate based on what emerges
