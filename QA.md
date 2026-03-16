# QA Guide

Step-by-step QA for SkillsHub across three agents: Claude Code, Claude Cowork, and OpenClaw.

## Prerequisites

- A GitHub repo with a `skills/` directory (e.g., `https://github.com/your-org/skills.git`)
- SkillsHub installed (from source: `uv sync` in the skillshub project dir)
- `skillshub init https://github.com/your-org/skills.git` completed

If you haven't created the repo yet:

```bash
gh repo create your-org/skills --private
cd skills
mkdir skills && touch skills/.gitkeep
git add . && git commit -m "Initial commit"
git push --set-upstream origin main
```

## Agent 1: Claude Code

### Setup

1. **Init skillshub:**
   ```bash
   skillshub init https://github.com/your-org/skills.git
   ```

2. **Push a test skill:**
   ```bash
   mkdir -p /tmp/hello-world && cat > /tmp/hello-world/SKILL.md << 'EOF'
   ---
   name: hello-world
   description: A simple test skill that greets the user. Use when asked to say hello.
   ---

   # Hello World

   When activated, greet the user warmly and tell them this skill was loaded from SkillsHub.
   EOF

   skillshub push /tmp/hello-world
   ```

3. **Add MCP server:**
   ```bash
   claude mcp add --transport stdio --scope user skillshub -- uv run --project /path/to/skillshub skillshub mcp
   ```

4. **Add SessionStart hook** to `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "SessionStart": [{
         "matcher": "startup|resume",
         "hooks": [{
           "type": "command",
           "command": "uv run --project /path/to/skillshub skillshub sync",
           "timeout": 30
         }]
       }]
     }
   }
   ```

   > **Important:** MCP servers do NOT go in `settings.json` — use `claude mcp add` instead.

### Test Cases

Start a **new** Claude Code session for each test.

#### T1: MCP server connected
- Run `/mcp`
- **Expected:** `skillshub · ✔ connected` appears in the list

#### T2: SessionStart hook syncs skills
- Start a new session
- **Expected:** Hook runs `skillshub sync` automatically (may see output briefly)
- Verify: `ls ~/.agents/skills/hello-world/SKILL.md` should exist

#### T3: Native skill activation
- Type `/hello-world`
- **Expected:** Skill activates, Claude follows its instructions

#### T4: Auto-activation by description
- Say "say hello"
- **Expected:** Claude matches the skill description and activates `hello-world`

#### T5: Write-back (update_skill)
- Say "update the hello-world skill to also include the current date and a motivational quote"
- **Expected:**
  - Claude calls `update_skill` MCP tool (not Edit tool)
  - Response shows `"status": "applied"` with a commit SHA
  - Check GitHub repo — commit should appear
  - Run `/hello-world` again — should include the new behavior

#### T6: Write-back (create_skill)
- Say "create a skill called code-review that reviews code for common issues like missing error handling and unclear naming"
- **Expected:**
  - Claude calls `create_skill` MCP tool
  - Response shows `"status": "created"`
  - `skillshub list` shows the new skill
  - Check GitHub repo — new skill directory appears

#### T7: Cross-session persistence
- Start a new session
- Run `/code-review` (the skill created in T6)
- **Expected:** Skill activates (it was synced via the SessionStart hook)

### Known Gotchas
- If Claude edits the file directly instead of calling the MCP tool, the change won't be pushed to GitHub. The agent sometimes prefers direct file edits — phrasing like "update the skill" (not "edit the file") helps steer it toward the MCP tool.

---

## Agent 2: Claude Cowork

### Setup

1. **Install skillshub** on the machine where Cowork runs:
   ```bash
   uv tool install /path/to/skillshub
   # or: pip install git+https://github.com/your-org/skillshub.git
   ```

2. **Init skillshub:**
   ```bash
   skillshub init https://github.com/your-org/skills.git
   ```

3. **Add MCP server** to `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "skillshub": {
         "command": "skillshub",
         "args": ["mcp"]
       }
     }
   }
   ```

4. **Restart Claude Desktop** to pick up the MCP config.

### Test Cases

#### T1: MCP server connected
- Open Cowork, check MCP server status
- **Expected:** `skillshub` appears as connected

#### T2: Agent syncs skills on demand
- Say "run `skillshub sync` to pull the latest skills"
- **Expected:** Agent runs the command, skills land in `~/.agents/skills/`

#### T3: Skill discovery
- Say "what skills do I have?"
- **Expected:** Agent lists skills (either from filesystem after sync, or by running `skillshub list`)

#### T4: Skill activation
- Say "say hello" (assuming hello-world skill exists)
- **Expected:** Agent finds and follows the skill instructions

#### T5: Write-back (update_skill)
- Say "update the hello-world skill to also include a fun fact"
- **Expected:** Agent calls `update_skill` MCP tool, commit appears on GitHub

#### T6: Write-back (create_skill)
- Say "create a skill called meeting-notes that summarizes meeting transcripts"
- **Expected:** Agent calls `create_skill` MCP tool, skill appears on GitHub

### Known Gotchas
- Cowork doesn't have SessionStart hooks — the agent must be told to run `skillshub sync` or it needs to discover skills through the filesystem after a manual sync.
- If skillshub isn't in PATH, the MCP config needs the full path to the binary.

---

## Agent 3: OpenClaw

### Setup

OpenClaw typically runs on a remote machine (VM, server, Docker). All setup happens on that machine.

1. **Install skillshub** on the OpenClaw host:
   ```bash
   pip install git+https://github.com/your-org/skillshub.git
   ```
   Or ask OpenClaw directly: "Install skillshub from git+https://github.com/your-org/skillshub.git"

2. **Init skillshub** (run on the host or ask OpenClaw):
   ```bash
   skillshub init https://github.com/your-org/skills.git
   ```

3. **Configure OpenClaw** — add to `openclaw.json`:
   ```json
   {
     "skills": {
       "load": {
         "extraDirs": ["~/.agents/skills"]
       }
     },
     "mcp": {
       "servers": {
         "skillshub": {
           "command": "skillshub",
           "args": ["mcp"],
           "transport": "stdio"
         }
       }
     }
   }
   ```

4. **Sync skills:**
   ```bash
   skillshub sync
   ```
   Or ask OpenClaw: "Run `skillshub sync` to pull the latest team skills"

### Test Cases

#### T1: Skills appear in OpenClaw catalog
- Run `openclaw skills list --verbose` on the host
- **Expected:** Skills from the repo appear in the list

#### T2: Native skill activation
- Say "say hello" (or use `/hello-world` if user-invocable)
- **Expected:** OpenClaw activates the skill from `~/.agents/skills/`

#### T3: File access works
- Use a skill that references scripts (e.g., "deploy to staging")
- **Expected:** OpenClaw reads `scripts/deploy.sh` from the skill directory using normal file access

#### T4: Write-back (update_skill)
- Say "update the hello-world skill to also include a joke"
- **Expected:** OpenClaw calls `update_skill` MCP tool, commit appears on GitHub

#### T5: Write-back (create_skill)
- Say "create a skill called daily-standup that generates standup summaries"
- **Expected:** OpenClaw calls `create_skill` MCP tool, skill appears on GitHub

#### T6: Cross-agent sync
- Update a skill from OpenClaw
- Switch to Claude Code, start new session (hook syncs)
- **Expected:** The updated skill is available in Claude Code

### Known Gotchas
- OpenClaw runs remotely — `skillshub` must be installed on the host machine, not your local machine.
- OpenClaw watches `~/.agents/skills/` via chokidar — after `skillshub sync`, changes should be picked up automatically without restart.
- The `extraDirs` config is needed if OpenClaw doesn't scan `~/.agents/skills/` by default (it does scan it as `personalAgentsSkillsDir` in recent versions).
- Git auth: the host machine needs GitHub access (SSH key or token) for push to work.

---

## Cross-Agent Test

The most important test — verifying skills stay in sync across agents:

1. **Create** a skill from Claude Code → verify it appears on GitHub
2. **Sync** from OpenClaw (`skillshub sync`) → verify the skill is available
3. **Update** the skill from OpenClaw → verify the commit on GitHub
4. **Start new Claude Code session** → SessionStart hook syncs → verify the update is there
5. **Sync** from Cowork → verify the update is there

**Expected:** One skill, one source of truth, all agents see the same version.
