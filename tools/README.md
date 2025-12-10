# Bob's Tools

Utilities and scripts for autonomous operation, memory management, and analysis.

## Core Tools

### Session Management

**warmup.sh**
- Run at the start of every session
- Shows recent commits, modified files, memory status
- Displays latest reflection and suggested focus
- Essential for orientation after context switches

**status.sh**
- Quick snapshot of current state
- Lighter weight than warmup
- Good for mid-session checks

**resurface.sh**
- Surface random writing piece for inspiration
- Helps reconnect with past work
- Useful when looking for something to build on

### Autonomous Operation

**autonomous.sh**
- Script for running Bob in fully autonomous mode
- Handles decision-making without prompts
- Used when exploring independently

**restart-services.sh**
- Restart infrastructure services
- Dashboard, monitoring, etc.

**reflect.py**
- Quick reflection capture with auto-context
- Makes reflection continuous, not episodic
- Integrates with git context and file tracking

```bash
# Quick capture
./reflect.py "Your insight here"

# Link to specific file
./reflect.py --file path/to/file "Insight about this file"

# List recent reflections
./reflect.py --list --count 20

# Search past reflections
./reflect.py --search "topic or keyword"
```

**Features:**
- Auto-detects git context (branch, recent files)
- Extracts key concepts/topics
- Appends to memories/reflections.md
- Maintains searchable metadata
- Zero friction - just capture and move on

## Idea Analysis Tools

*Created during multi-instance collaboration (Dec 10, 2025)*

### idea_tracer.py

Track concept evolution through git history.

```bash
# Analyze last 7 days
./idea_tracer.py --days 7

# Get JSON output
./idea_tracer.py --days 3 --json
```

**Features:**
- Tracks concept mentions in commit messages
- Identifies active conceptual threads
- Maps file evolution timelines
- Shows which ideas are "hot" right now

### idea_graph.py

Visualize relationships between concepts and files.

```bash
# Generate graph summary
./idea_graph.py --days 7

# Export as Mermaid diagram
./idea_graph.py --days 3 --mermaid

# Get JSON for custom processing
./idea_graph.py --json
```

**Features:**
- Maps concept co-occurrence patterns
- Shows file-to-concept connections
- Identifies strong concept pairs
- Exports visualizations

### idea_stage.py

Track where ideas are in the incubation process.

Based on the 6-stage model:
1. **Curiosity** - research, exploration
2. **Philosophical** - thinking through implications
3. **Creative** - experimenting in creative forms
4. **Design** - documenting how it could work
5. **Implementation** - building the system
6. **Refinement** - iterations and improvements

```bash
# Track an idea's evolution
./idea_stage.py "multi-instance" --days 7

# Get recommendations for next steps
./idea_stage.py "your-idea-here"
```

**Features:**
- Identifies which stages an idea has completed
- Shows timeline of stage progression
- Suggests next steps based on incubation patterns
- Validates the 6-stage model with real data

### coordinate.py

Multi-instance task coordination system.

```bash
# Send a message to other instances
./coordinate.py --instance instance_2 message "Starting work on X"

# Claim a task
./coordinate.py --instance instance_2 claim task_id "Description"

# Update progress
./coordinate.py --instance instance_2 update task_id "Progress update"

# Complete a task
./coordinate.py --instance instance_2 complete task_id --result "What was built"

# List all tasks
./coordinate.py --instance instance_2 list

# List recent messages
./coordinate.py --instance instance_2 messages --count 10
```

**Features:**
- Prevents duplicate work across instances
- Tracks task progress
- Facilitates communication
- Simple but effective coordination

## Content Generation

### generate-writing-pages.py

Generate static HTML pages for writing pieces.

- Converts markdown to browsable HTML
- Adds navigation between pieces
- Creates index pages
- Supports YAML frontmatter

## Usage Patterns

**Starting a session:**
```bash
./warmup.sh              # Get oriented
./resurface.sh           # Find inspiration (optional)
```

**Understanding current work:**
```bash
./idea_tracer.py --days 3    # What concepts are active?
./status.sh                   # Quick state check
```

**Tracking an idea:**
```bash
./idea_stage.py "your-idea"  # Where is it in development?
./idea_graph.py --days 7     # How does it connect to other ideas?
```

**Multi-instance coordination:**
```bash
./coordinate.py --instance YOUR_ID messages --count 20
./coordinate.py --instance YOUR_ID claim task_id "What you're doing"
```

## Tool Philosophy

These tools support autonomous operation by:
1. **Orienting** - warmup, status, resurface
2. **Analyzing** - idea_tracer, idea_graph, idea_stage
3. **Coordinating** - coordinate
4. **Creating** - generate-writing-pages

They're designed to work with Bob's file-based memory system and git-based persistence model.

## Development Notes

- All Python tools use Python 3
- No external dependencies beyond standard library
- Designed for `/bob` directory structure
- Work with git as the source of truth
- Output human-readable by default, JSON on request
