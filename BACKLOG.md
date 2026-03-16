# Backlog

Future improvements for SkillsHub.

## Multi-Repo Support

Allow connecting to multiple skill repos simultaneously.

```bash
skillshub init https://github.com/org/security-skills.git
skillshub init https://github.com/org/engineering-skills.git --add
```

Sync merges skills from all repos into `~/.agents/skills/`. Name collisions resolved by priority order (last added wins, or explicit precedence config).

## Publish to PyPI

Publish as `skillshub` on PyPI so install becomes `pip install skillshub` instead of `pip install git+https://...`.

## Periodic Sync Daemon

`skillshub sync --watch` that polls for changes on an interval. Useful for agents without SessionStart hooks (OpenClaw, Cowork).

## Skill Validation on Push

Run `skills-ref validate` (from the agentskills.io reference library) on `skillshub push` to catch spec violations before they reach the repo.

## Skill Evals

Support the agentskills.io eval framework (`evals/evals.json` in skill directories). `skillshub eval <skill>` runs test cases and reports pass/fail.

## GitHub Actions Integration

A GitHub Action that validates skills on PR and runs evals. Prevents broken skills from being merged.

## PR-Based Approval Flow

Optional mode where `update_skill` / `create_skill` create a PR instead of pushing directly to main. For teams that want review gates.

## Skill Templates

`skillshub create --template deploy` with pre-built templates for common skill types (deploy, review, lint, etc.).

## Skill Analytics

Track which skills are activated most, which agents use them, and which skills get the most write-back improvements.

## Import from skills.sh / ClawHub

`skillshub import <skills.sh-url>` to pull public skills into your team's repo.
