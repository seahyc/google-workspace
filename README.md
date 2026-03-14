# google-workspace

Agent skill for Google Workspace workflows across Gmail, Drive, Docs, Sheets,
Slides, Calendar, and Forms.

## Quick Start

Install the skill for all supported local agents:

```bash
npx skills add seahyc/google-workspace -g -y --agent '*'
```

Then install and configure the Google Workspace server:
- https://github.com/seahyc/hardened-google-workspace-mcp

On first use, complete the browser OAuth flow once.

## Supported Operations By Service

| Service | Supported operations |
| --- | --- |
| Gmail | Search messages, read messages and threads, read attachments, create drafts and reply drafts, inspect filters, manage labels, label messages |
| Drive | Search files, list folders, read file content, inspect permissions and links, create files and folders, copy, move, export, inspect revisions, trash or delete files |
| Docs | Read and edit documents, find and replace, insert tables/images/lists/breaks/footnotes, update styles, inspect structure, manage comments, export to PDF |
| Sheets | Read and write values, manage tabs, format ranges, sort, validate, manage conditional formatting, freeze, merge, resize, manage named ranges/filter views/protected ranges/comments, inspect and update rich text cells with notes and hyperlinks |
| Slides | Create presentations, inspect presentations and pages, fetch thumbnails, run structured updates, manage comments |
| Calendar | List calendars, read events, create events, modify events, delete events |
| Forms | Create forms, inspect forms, list responses, read individual responses, update publish settings |

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

Recommended:

```bash
npx skills add seahyc/google-workspace -g -y --agent '*'
```

If you want to target specific agents explicitly:

```bash
npx skills add seahyc/google-workspace -g -y --agent claude-code codex
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

## Troubleshooting And Manual Install

### If `npx skills add` is enough

You do not need to create any symlinks manually. The Skills CLI should install
the skill into the correct agent discovery paths.

### If you want to install manually

Typical user skill discovery paths:
- Codex: `~/.agents/skills`
- Claude Code: `~/.claude/skills`

Clone the repo somewhere permanent:

```bash
git clone https://github.com/seahyc/google-workspace.git ~/Code/skills/google-workspace
```

Then create symlinks:

```bash
mkdir -p ~/.agents/skills ~/.claude/skills
ln -s ~/Code/skills/google-workspace ~/.agents/skills/google-workspace
ln -s ../../.agents/skills/google-workspace ~/.claude/skills/google-workspace
```

### If the skill installs but does not work

Check these in order:
- the Google Workspace server is installed locally
- the server is configured with Google OAuth credentials
- the server entry exists in your agent config
- you completed the first browser auth flow successfully
- your agent session has reloaded its skill list after installation
