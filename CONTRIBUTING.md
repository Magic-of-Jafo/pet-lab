# Contributing to Pet Lab

Thanks for helping! PET owners, retro programmers and AI tinkerers are all
welcome.

## Good first contributions

- **Run it on your hardware** (ARM64 boards, other NAS models) and report
  what happened.
- **Check the reference.** Every `[DOC]` fact in `pet-ref/` is a candidate
  for verification: test it in the emulator or find it in the ROM
  disassemblies, then change the mark to `[EMU]` or `[ROM]` (or fix it).
- **Example programs** in `examples/`, ideally with the prompt that produced
  them and a screenshot.
- **Other PET models** (2001, 8032): profiles, ROM disassemblies and
  reference notes.

## Ground rules

- **Facts in the reference must say how they're known.** `[ROM]`, `[EMU]`
  or `[DOC]`. Don't add unverifiable claims.
- **No Commodore ROM images or copyrighted manuals in the repository.** The
  build fetches the ROMs from the VICE release.
- **Keep the MCP tools safe:** paths stay inside the workspace, no shell
  access, every call bounded in time.
- **Run the smoke test** before a pull request:

  ```bash
  docker compose up -d --build
  docker exec pet-lab /opt/petlab-venv/bin/python /opt/petlab/tests/mcp_smoke.py
  ```

  Add a check there for any new tool.

## Code style

Python 3.11+, standard library only in `petlab/` except the MCP SDK in
`mcp_server.py`. Short functions, comments that explain why.
