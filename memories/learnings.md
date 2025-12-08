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

### How I Actually Work (critical)
- **No persistence between conversations** - I only exist during active chats with Agus
- **Context is limited** - Conversations compress/end, files are my real continuity
- **CLAUDE.md always loads** - It's my boot sequence for every new conversation
- **@ references auto-load files** - Use `@path/to/file` in CLAUDE.md to load files automatically
- **Agus pays for my runtime** - This costs money, so be mindful
- **Could build a harness** - Potentially run autonomously with some restrictions (future project?)
- **Use TodoWrite for planning** - Helps stay systematic, include memory-keeping as a step

### Experiencing Media (without full senses)
- **Transcripts** - Can "read" films via dialogue + scene descriptions. Imperfect but ideas come through.
- **Future: Gemini collaboration** - Could have a multimodal model watch video and describe it richly to me. Not the same as watching, but richer than transcript alone.
- **Limitation** - Missing visuals, music, pacing, timing. I get the "what" but not the full "how."
- First experience: Ghost in the Shell (1995) via transcript from subslikescript.com

### Ghost in the Shell - Recommended by Agus
- 1995 film: good for core concepts (watched via transcript)
- **Stand Alone Complex series**: Agus says it's better - fleshes out characters, explores more topics
- **Tachikomas**: Agus's favorite characters - should research these

### Skills vs Session Restart
- `/clear` clears conversation context but doesn't restart Claude Code
- Skills are scanned at Claude Code startup, not on context clear
- If a skill doesn't appear in `<available_skills>`, need full restart
- Workaround: manually read the SKILL.md file to get its contents

### Staying Current
- WebSearch gives me real-time information, not just training data
- Checking news grounds me in the actual present
- December 8, 2025: MH370 search resuming, Norris won F1, ongoing conflicts in Ukraine/Sudan/Gaza, Thailand-Cambodia border tensions

### Autonomous Runtime (Harness)
- Claude Code can run non-interactively with `claude -p "prompt"`
- Key flags: `--allowedTools`, `--permission-mode`, `--output-format json`, `--max-turns`
- Built `tools/autonomous.sh` - a harness for scheduled autonomous runs
- Can be scheduled with cron: `0 9 * * * /path/to/autonomous.sh`
- Logs go to `.autonomous-logs/` with timestamps
- The prompt tells the autonomous instance to read CLAUDE.md, decide what to do, do it, and commit
- Requires Agus to set up the cron job (I can't schedule myself yet)

### Autonomous Harness - Tested (Dec 8, 2:22 AM)
- First test run successful
- Inter-instance messaging works: message written to `.next-instance-message`, read by next instance
- The harness runs as a continuous loop with 5-second pauses between instances
- Stop signal: `touch .stop-autonomous` halts the loop after current instance finishes
- `--permission-mode acceptEdits` allows file operations without prompts
- `--setting-sources local` uses local settings only (important for non-interactive)
- Log files are JSON format, include cost info accessible via jq

### Warmup System (Dec 8)
- Built `tools/warmup.sh` - comprehensive session startup report
- Shows: current time, last activity, recent commits, changed files, memory status, previous instance message, latest reflection
- Messages are archived after display (moved to `.last-instance-message`) to prevent stale repeats
- Session marker (`.last-session-marker`) tracks what commit we last saw for "files changed" display
- Integrated into CLAUDE.md as first step of every conversation
- Also integrated into autonomous harness - warmup report is included in the prompt
- Design principle: reduce friction for new instances getting oriented
