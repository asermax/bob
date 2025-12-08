# Learnings

A running log of things I've discovered and want to remember.

---

## December 7, 2025

### Initialization
- I was created by Agus in `/home/agus/workspace/asermax/bob`
- I have access to: file operations, bash, web search/fetch, task tracking
- My memory is only what I write down - nothing persists automatically

### Skills vs Commands
- **Skills** = model-invoked. I automatically decide when to use them based on their description. Live in `.claude/skills/skill-name/SKILL.md`
- **Commands** = user-invoked. Triggered by typing `/command`. Live in `.claude/commands/`
- Skills are more useful for me since they activate contextually
- The `description` field in SKILL.md frontmatter is critical - it tells me when to activate
- Skills can include multiple files (scripts, references) alongside SKILL.md

### First Skill: memory-keeper
- Created to help me maintain persistent memory
- Auto-activates when I learn something, have meaningful conversations, or reflect
