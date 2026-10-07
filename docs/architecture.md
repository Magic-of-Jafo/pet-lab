# How Pet Lab works

```
 AI client ──MCP (stdio)──► pet-mcp ─┐
                                     ├─► petlab (Python) ──TCP 6510──► VICE xpet ──► Xvfb
 you / scripts ──────────► petrun  ──┘        │                       (PET 4032)
                                              ├─► petcat (BASIC)
                                              ├─► acme / cl65 (assembly, C)
                                              └─► /opt/pet-ref, /opt/pet-rom (reference)
```

## The emulator

- **VICE xpet** from Debian, with the PET ROMs from the official VICE 3.9
  source release (Debian strips them).
- It runs headless against a virtual X display (Xvfb), because VICE's GTK
  interface needs one.
- The default machine is a PET 4032 with the 60 Hz North American editor
  ROM.

## Talking to VICE

`petlab/vice.py` drives VICE through its **remote text monitor** (a TCP
socket, port 6510 and up):

- **Memory reads** use the monitor's `save` command to a file, which is
  more robust than parsing hex dumps.
- **Typing** writes PETSCII codes into the PET's keyboard buffer ($026F)
  and count ($9E), 9 at a time, waiting for the PET to empty it. It's
  exactly what the KERNAL does with real key presses.
- **Loading** uses the monitor's `load`, then sets BASIC's end-of-program
  pointers ($2A/$2C/$2E) and types `RUN`. VICE's autostart is disabled for
  the 60 Hz ROM set, and doing it by hand works the same for every ROM.
- **Screen** is screen memory at $8000 decoded into text.

### Knowing whether the CPU is running

The monitor protocol has a catch: sending a command to a running emulator
stops it and prints an extra prompt, while a breakpoint that hits on its
own prints a stop message and a prompt with nobody asking. `Monitor` reads
anything the monitor sent unprompted before each command, so it always
knows whether the CPU is running, stopped by a command, or **held at a
breakpoint**. Held means: stay stopped until someone explicitly continues.

## Design rules

- **The PET never runs past a breakpoint by accident.** Only
  `pet_continue` (or petrun's `--wait`/`--keys`) continues. Every other
  tool reports the stop.
- **Everything is checked, not remembered.** The reference marks each fact
  [ROM], [EMU] or [DOC]; agents are told to look things up and to trust the
  ROM and the emulator over the reference.
- **Sandboxed files.** MCP file tools resolve paths inside the workspace
  only, and there is no shell tool.
- **Bounded calls.** Every wait is capped; idle emulators shut down.
- **No orphaned emulators.** Each `xpet` runs under a small shell watchdog
  that ends it as soon as the Python process that started it is gone, even
  after a crash or `kill -9`. The MCP server also stops its emulator when
  the client disconnects. The smoke test checks both.

## Files

| Path | |
|---|---|
| `petlab/vice.py` | Emulator and monitor control |
| `petlab/basic.py` | Tokenizing and listing BASIC with petcat |
| `petlab/screen.py` | Screen memory to text |
| `petlab/mcp_server.py` | The MCP server |
| `bin/petrun`, `bin/pet-mcp` | Command line entry points |
| `pet-ref/` | The reference (baked into the image at `/opt/pet-ref`) |
| `tests/mcp_smoke.py` | End-to-end test through a real MCP client |
