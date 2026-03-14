# google-workspace

Agent skill for Google Workspace workflows across Gmail, Drive, Docs, Sheets,
Slides, Calendar, and Forms.

## Quick Start

```bash
npx skills add seahyc/google-workspace
```

## What This Skill Does

This skill helps an agent choose the right Google Workspace tool and use it
correctly for common read and write tasks.

Full capability range:
- Gmail:
  - search messages
  - read individual messages or full threads
  - read attachments
  - create drafts and reply drafts
  - inspect filters
  - create or modify labels
  - add or remove labels from messages
- Drive:
  - search files and folders
  - list folder contents
  - read file content
  - inspect permissions and shareable links
  - create files and folders
  - copy and move files
  - export files
  - inspect revision history
  - trash or delete files
- Docs:
  - read document content
  - edit text
  - perform find and replace
  - insert lists, tables, images, page breaks, section breaks, and footnotes
  - update paragraph style and document style
  - inspect document structure
  - create, reply to, resolve, edit, and delete comments
  - export to PDF
- Sheets:
  - read and write plain values
  - create, delete, duplicate, and rename tabs
  - format ranges
  - sort ranges
  - set validation
  - manage conditional formatting
  - freeze rows and columns
  - merge cells
  - insert and delete rows and columns
  - auto-resize dimensions
  - manage named ranges, filter views, and protected ranges
  - manage spreadsheet comments and replies
  - inspect and update structured cells with inline rich text formatting
  - preserve or modify notes and hyperlinks inside cells
- Slides:
  - create presentations
  - inspect presentations and pages
  - fetch thumbnails
  - perform structured updates
  - create, reply to, resolve, edit, and delete comments
- Calendar:
  - list calendars
  - read events
  - create, modify, and delete events
- Forms:
  - create forms
  - inspect forms
  - list responses
  - read individual responses
  - change publish settings

## Why This Skill Exists

Google Workspace tasks often look simple but split into very different tool
paths:
- simple value updates versus structured cell updates in Sheets
- plain text edits versus structural edits in Docs
- reading a Gmail thread versus drafting a reply

This skill gives the agent a service map and a default workflow so it does not
pick the wrong tool or lose formatting.

## Standout Capability: Rich Google Sheets Cells

The most distinctive part of this skill is Sheets support for structured cell
inspection and updates.

It can help an agent:
- inspect inline formatting inside a single cell
- preserve mixed font colors and styles
- preserve or update notes
- preserve or update hyperlinks inside cell text
- generate or validate patch payloads before writing

That matters for spreadsheets where one cell contains multiple formatted text
segments rather than just a plain scalar value.

## Setup

This skill assumes you already have the Google Workspace server available
locally. The skill itself is only the agent instruction layer plus a helper CLI.

Server repo:
- https://github.com/seahyc/hardened-google-workspace-mcp

### 1. Install the skill

```bash
npx skills add seahyc/google-workspace
```

### 2. Install and configure the Google Workspace server

You need a local checkout of the server plus Google OAuth credentials. The full
server setup lives in the server repo and should be treated as the source of
truth.

At a high level, setup requires:
- a checkout of `seahyc/hardened-google-workspace-mcp`
- Python and `uv`
- a Google Cloud project
- the relevant Google APIs enabled
- an OAuth client ID and client secret
- a configured Google Workspace server entry in your agent config

Follow the setup and OAuth instructions in the server repo for the exact Google
Cloud and credential steps.

In Codex, the working shape looks like this:

```toml
[mcp_servers.google-workspace]
command = "uv"
args = ["run", "--directory", "/ABS/PATH/TO/hardened-google-workspace-mcp", "python", "main.py", "--single-user", "--tools", "gmail", "drive", "docs", "sheets"]

[mcp_servers.google-workspace.env]
USER_GOOGLE_EMAIL = "you@example.com"
GOOGLE_OAUTH_CLIENT_ID = "YOUR_CLIENT_ID"
GOOGLE_OAUTH_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
WORKSPACE_MCP_PORT = "51771"
GOOGLE_MCP_OAUTH_STATE_FILE = "/ABS/PATH/TO/oauth_states.json"
```

If you are using Claude Code, add the same server with its Google Workspace
integration config or MCP config flow.

### 3. Authenticate once through the browser flow

On first use, the Google Workspace server will open a browser-based OAuth flow.
Complete that flow once so the local credential store is populated.

### 4. Optional: set the helper CLI server path explicitly

The helper CLI can auto-discover the server path from `~/.codex/config.toml`,
but you can also set it directly:

```bash
export GOOGLE_WORKSPACE_SERVER_DIR=/ABS/PATH/TO/hardened-google-workspace-mcp
```

Then helper commands like these will work consistently:

```bash
python3 scripts/workspace_mcp.py service-summary --service sheets
```

```bash
uv run --directory "$GOOGLE_WORKSPACE_SERVER_DIR" \
  python3 scripts/workspace_mcp.py sheets-inspect-range \
  --file-id SPREADSHEET_ID \
  --range "'Sheet 1'!B2:B8"
```

## When To Use This Skill

Use it when the task is primarily about Google Workspace data or documents:
- email triage, search, or draft creation
- Drive search, file inspection, export, or permissions checks
- Docs editing and structural document changes
- spreadsheet editing, especially when notes or intra-cell formatting matter
- Slides inspection or updates
- Calendar event management
- Forms inspection or response access

Do not use it when the task is really about local files, raw HTTP calls, or a
non-Google productivity suite.

## What’s In The Repo

- [SKILL.md](./SKILL.md): the agent instructions
- [scripts/workspace_mcp.py](./scripts/workspace_mcp.py): helper CLI for
  cataloging tools and building or inspecting structured Google Sheets payloads

## Local Layout

Codex discovers user skills from `~/.agents/skills`.
Claude Code discovers user skills from `~/.claude/skills`.

This repo is intended to be the source of truth, with those discovery
directories containing symlinks to this folder.

## Publish

To make the skill installable through the Skills CLI, push this folder as a Git
repository. The install command is:

```bash
npx skills add <owner>/<repo>
```

For the skill to show up in `npx skills find`, it needs to be distributed from a
public repo and accumulate installs through the Skills ecosystem.
