# Getting started

## Requirements

- Docker with Compose (Docker Desktop, or Docker Engine on Linux, or a NAS
  with a Docker app).
- About 1.5 GB of disk for the image.
- Any 64-bit x86 CPU. Pet Lab is developed on a Synology DS1517+ (Intel
  Atom C2538) and runs fine there. ARM64 should work (every package exists
  for it) but hasn't been tested yet; reports welcome.
- For the built-in agent: a Claude account for Claude Code. The MCP server
  and petrun don't need one.

## Install

```bash
git clone https://github.com/Magic-of-Jafo/pet-lab.git
cd pet-lab
docker compose up -d --build
```

The first build downloads Debian packages, the PET ROMs from the VICE
release, the MCP SDK and Claude Code. Later rebuilds are quick.

**Linux hosts:** files the lab writes into `./workspace` are owned by the
user inside the container (uid 1000 by default). If your own user has a
different id, build with yours so you can edit the files:

```bash
PETLAB_UID=$(id -u) PETLAB_GID=$(id -g) docker compose up -d --build
```

(or put `PETLAB_UID=...` and `PETLAB_GID=...` in a `.env` file next to
`compose.yaml`).

## Check it

```bash
docker exec pet-lab /opt/petlab-venv/bin/python /opt/petlab/tests/mcp_smoke.py
```

It starts the MCP server, boots the PET, runs BASIC, types, assembles and
debugs a machine code routine, searches the reference, and ends with
`ALL PASSED`. It leaves a `mcptest/` folder in your workspace.

## First session with the built-in agent

```bash
docker exec -it pet-lab claude
```

Claude Code asks you to log in the first time; the login is kept in
`./home`, so you only do this once. It starts in `/workspace`, where
`CLAUDE.md` tells it about the PET, the reference and the tools, and
`.mcp.json` connects it to the `pet` MCP server (Claude Code asks once
whether to trust it).

Things to try:

- *Write a BASIC program that draws a maze with PET graphics characters
  and lets me walk through it with the number keys.*
- *Make a machine code routine that scrolls the screen up one line, called
  from BASIC with SYS. Show me it working with a breakpoint.*
- *Write a C program for the PET that plays Tic Tac Toe.*
- *Why does `10 IF A THEN PRINT "X" ELSE PRINT "Y"` fail on my PET?*

### Running the agent without a conversation

For scripts and automation (for example from n8n or a bot):

```bash
docker exec pet-lab sh -c 'cd /workspace && claude -p "Make a program called CLOCK that shows the time from TI$ in big digits." \
  --mcp-config /workspace/.mcp.json --strict-mcp-config \
  --allowedTools mcp__pet Write Edit Read Glob Grep --max-turns 60'
```

`--strict-mcp-config` keeps the agent to the `pet` tools only, even if
your Claude account has other connectors.

## Workspace layout

`./workspace` on your machine is `/workspace` in the container:

| Path | |
|---|---|
| `CLAUDE.md` | Instructions for the agent: the target PET, the workflow, reply style. Edit it for your PET (model, drive numbers) |
| `.mcp.json` | Registers the `pet` MCP server for Claude Code |
| `programs/` | Where the agent puts programs (`.BAS`, `.A`, `.c`, `.PRG`, test plans) |

The MCP tools can only read and write inside `/workspace`.

## Updating

```bash
git pull
docker compose up -d --build
```

Your workspace and login are untouched.

### Running Pet Lab on another machine

To build and run on a NAS or home server from your desktop, copy
`deploy.env.example` to `deploy.env`, fill in the host, folder and Docker
commands, and run `scripts/deploy.sh`. It copies the sources over SSH,
rebuilds and restarts. `scripts/deploy.sh docs` only updates `CLAUDE.md`,
`.mcp.json` and the reference.
