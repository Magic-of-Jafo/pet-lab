# The PET MCP server

`pet-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io)
server that gives an AI client one emulated Commodore PET 4032, the build
tools and the PET reference. The PET **keeps running between calls**.

## Connecting a client

The server speaks MCP over stdio. Start it with `pet-mcp` inside the
container.

**Claude Code inside the container:** already set up by
`workspace/.mcp.json`.

**Claude Desktop, Cursor, or any client on the Docker host:**

```json
{
  "mcpServers": {
    "pet": { "command": "docker", "args": ["exec", "-i", "pet-lab", "pet-mcp"] }
  }
}
```

**A client on another machine** (Docker runs on a NAS or server):

```json
{
  "mcpServers": {
    "pet": { "command": "ssh", "args": ["you@nas", "docker", "exec", "-i", "pet-lab", "pet-mcp"] }
  }
}
```

The SSH login must work without a password prompt (use a key). On
Synology, use the full path and sudo rights for docker as in
`deploy.env.example`.

**Claude Code outside the container:**
`claude mcp add pet -- docker exec -i pet-lab pet-mcp`

Each connection starts its own server process and its own PET.

## Tools

### Running the PET

| Tool | What it does |
|---|---|
| `pet_reset(model, hz, warp)` | Power-cycle the PET and wait for `READY.` Defaults: 4032, 60 Hz |
| `pet_load(basic_source \| prg_path, run, wait_seconds)` | Load a BASIC listing (text) or a `.PRG`/`.BAS` file and `RUN` it. Machine code that doesn't load at $0401 is only loaded |
| `pet_type(keys, wait_seconds)` | Type on the keyboard. `\r` or `{RETURN}`, and `{CLR}` `{HOME}` `{UP}` `{DOWN}` `{LEFT}` `{RIGHT}` `{RVS ON}` `{RVS OFF}` `{DEL}` `{INST}` `{n}` |
| `pet_wait(seconds)` | Let it run |
| `pet_wait_for(pattern, timeout_seconds)` | Run until a screen line matches a regular expression |
| `pet_screen(include_image)` | The screen as text, optionally also as a PNG |

Every result that shows the screen also says whether a BASIC error
(`?... ERROR`) is on it.

### Debugging

| Tool | What it does |
|---|---|
| `pet_break(address)` | Stop when the CPU executes an address |
| `pet_clear_breaks()` | Delete all breakpoints |
| `pet_continue(wait_for_break_seconds)` | Continue; optionally wait for the next breakpoint |
| `pet_step(count)` | Execute instructions one at a time and list them |
| `pet_registers()` | PC, A, X, Y, SP, flags |
| `pet_peek(address, length)` | Hex dump |
| `pet_poke(address, values)` | Write bytes |
| `pet_disassemble(address, length)` | Disassemble memory |
| `pet_attach_drive(device, folder)` | Make a workspace folder disk drive 8–11 (restarts the PET) |

Addresses can be `$7000`, `0x7000` or `28672`.

**How breakpoints behave.** Tools that run the PET (`pet_load`,
`pet_type`, `pet_wait`, `pet_wait_for`) never continue past a breakpoint.
If one hits while they run, their result says `CPU STOPPED AT BREAKPOINT`
with the stop message and the registers, and the CPU stays there. Inspect
with `pet_peek`, `pet_registers` and `pet_step`; only `pet_continue` moves
on. A typical session:

```
asm_acme("programs/move.a")                 -> OK, listing programs/move.lst
pet_load(prg_path="programs/MOVE.PRG")       -> Loaded $7000-$7065
pet_break("$7012")
pet_type("SYS 28672\r")                      -> CPU STOPPED AT BREAKPOINT ... X:0E
pet_peek("$033A", 4)                         -> $033A  0E 0A 01 FF
pet_step(3)                                  -> .C:7012 ... .C:7014 ... .C:7017 ...
pet_continue()
```

### Building

| Tool | What it does |
|---|---|
| `basic_tokenize(source_path, out_path)` | `.BAS` listing (UPPERCASE, `{controls}`) to a `.PRG` at $0401 |
| `basic_list(prg_path)` | `.PRG` back to a listing |
| `asm_acme(source_path)` | Assemble with ACME; the source names its output (`!to "X.PRG", cbm`). Writes a `.lst` listing with addresses |
| `c_compile(source_path, out_path)` | cc65 for the PET (`cl65 -t pet -O`); runs with `RUN` |

### Reference

| Tool | What it does |
|---|---|
| `ref_list()` | The reference documents |
| `ref_read(name)` | One document, e.g. `basic4.md` |
| `ref_search(query)` | Lines matching a keyword, address or phrase, with their section |
| `rom_lookup(address)` | The ROM disassembly from a routine's address, e.g. `$FFD2` or `$E442` |

The reference is also available as resources: `pet-ref://basic4.md` etc.

## Limits and safety

- File tools only work inside `/workspace`. There's no shell tool.
- Waits are capped at 120 seconds per call, and a PET left idle for 30
  minutes is shut down (it starts again on the next call).
- One PET per connection.

Settings (environment variables for `pet-mcp`): `PETLAB_WORKSPACE`,
`PETLAB_REF`, `PETLAB_ROMDIS`, `PETLAB_IDLE` (seconds).
