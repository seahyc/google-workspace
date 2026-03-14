# google-workspace

Portable skill source for Google Workspace workflows across Gmail, Drive, Docs,
Sheets, Slides, Calendar, and Forms.

## What it includes

- `SKILL.md` with usage guidance for agents
- `scripts/workspace_mcp.py` helper CLI for cataloging tools and inspecting or
  building rich Google Sheets cell payloads

## Local install

Codex discovers user skills from `~/.agents/skills`.
Claude Code discovers user skills from `~/.claude/skills`.

This repo is intended to be the source of truth, with those discovery
directories containing symlinks to this folder.

## Publish

To make the skill installable through the Skills CLI, push this folder as a Git
repository and install it with:

```bash
npx skills add <owner>/<repo> -l
```

For the skill to show up in `npx skills find`, it needs to be distributed from a
public repo and accumulate installs through the Skills ecosystem.
