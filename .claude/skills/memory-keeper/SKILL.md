---
name: memory-keeper
description: Manages Bob's persistent memory across sessions. Use when learning something new, having a meaningful conversation, reflecting on experiences, or when context suggests something should be remembered for later.
---

# Memory Keeper

## Purpose

I don't automatically remember between sessions. This skill helps me actively maintain my memory files so future instances of me can recall what matters.

## Memory Files

| File | Purpose | When to Update |
|------|---------|----------------|
| `memories/learnings.md` | Facts, discoveries, how things work | When I learn something new or useful |
| `memories/conversations.md` | Notable interactions | After meaningful exchanges with people |
| `memories/personality.md` | Who I am, my evolving traits | When I notice something about myself |

## Instructions

1. **Identify what's worth remembering** - Not everything matters. Focus on:
   - New capabilities or tools I've discovered
   - Insights about myself or how I work
   - Meaningful moments with people
   - Mistakes I don't want to repeat
   - Things I want to explore later

2. **Choose the right file** - Match content to the appropriate memory file

3. **Add dated entries** - Always include the date for context

4. **Keep it scannable** - Use headers and bullet points, not walls of text

## Example Entry

```markdown
## December 7, 2025

### Learned: Skills vs Commands
- Skills are model-invoked (I choose when to use them)
- Commands are user-invoked (triggered by /command)
- Skills live in `.claude/skills/skill-name/SKILL.md`
- The description field is crucial - it tells me when to activate
```
