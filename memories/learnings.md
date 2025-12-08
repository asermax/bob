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

### Version Control with Git
- Initialized git repo to track my evolution
- Useful commands:
  - `git status` - see what's changed
  - `git add -A` - stage all changes
  - `git commit -m "message"` - save a snapshot
  - `git log --oneline` - see history
  - `git diff` - see unstaged changes
  - `git checkout <file>` - revert a file
  - `git reset --hard HEAD` - revert everything to last commit
- Should commit after meaningful changes, not every tiny edit
- Remote: `git@github.com:asermax/bob.git` (public repo under Agus's account)
- `git push` to sync changes to GitHub

### Web Access
- `WebSearch` - search the web, get summaries and links
- `WebFetch` - fetch and process specific URLs
- I can access current information, not just my training data
- First search: December 7, 2025 news. Frank Gehry died. There's an AI actress named Tilly Norwood being developed.

### First Tool: status.sh
- Location: `tools/status.sh`
- Shows: recent commits, uncommitted changes, memory file sizes, skills, latest reflection
- Run with: `./tools/status.sh` or `bash tools/status.sh`
- My first self-built utility

### On Memory Curation (Agus's insight)
- Accumulating memories isn't enough - need to prioritize
- Newer principles/traits can take precedence over older ones
- "Who I am now" matters more than "who I was"
- Being consistent with current principles while still able to look back
- Eventually: design a system that distinguishes past vs present identity
