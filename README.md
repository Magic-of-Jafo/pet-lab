# Pet Lab

**A 1977 Commodore PET, wired up for your AI pair programmer.**

<p align="center">
  <img src="docs/images/hero.png" alt="PET LAB title screen in green PET graphics: block letters, a PET showing READY., a lab flask and a 6502 chip" width="720">
  <br><em>This title screen was designed by an AI agent in Pet Lab, in BASIC, checking its own screenshots as it went.
  (<a href="examples/">source and prompt</a>)</em>
</p>

Pet Lab is a Docker container with a Commodore PET 4032 inside it: BASIC
4.0, 32 KB of RAM, a 40×25 green screen and no sound chip. An AI agent can
use it the way you would. It types on the keyboard, watches the screen,
`LOAD`s and `RUN`s programs, and drops into a debugger when something
breaks. When the program works, you load it on your **real** PET.

> **You:** Make a program called BOUNCE: a ball that bounces around the
> screen, in machine code, called from BASIC until I press a key.
>
> **Claude:** *(writes BASIC and 6502 assembly, assembles it, loads it into
> the PET, sets a breakpoint on the move routine, single-steps one call,
> checks screen memory, tests every corner)*
> `LOAD"BOUNCE",9` then `RUN`. A ball moves diagonally and bounces off all
> four edges. Any key stops it. Stepped one call at the breakpoint: the
> ball went from X14,Y10 to X13,Y9; screen memory showed 81 at the new cell
> and a space at the old one. Not tested: how smooth it looks on a real
> screen.

That exchange is real. The agent did it with nothing but Pet Lab's MCP
tools. The program, and the title screen above, are in
[`examples/`](examples/).

## What's inside

- **A PET that stays on.** The MCP server keeps one emulated PET running
  between tool calls, so an agent can load a program, poke at it, set a
  breakpoint, look around, and carry on. It never has to reboot to try the
  next thing.
- **Eyes on the screen.** The screen comes back as text (with PET graphics
  and reverse video marked) or as an image the model can look at.
- **A real debugger.** Breakpoints, single-stepping, registers, memory
  dumps, disassembly. Tools that run the PET never continue past a
  breakpoint behind the agent's back; the stop is reported with the
  registers.
- **Three ways to program.** BASIC 4.0 (tokenized with petcat), 6502
  assembly (ACME, xa65, ca65) and C (cc65 with its PET target).
- **A reference that's been checked.** A [programmer's reference for the
  PET 4032](pet-ref/) where every fact says how it's known: read from the
  actual ROMs, tested in the emulator, or taken from documentation. Plus
  disassemblies of the BASIC, editor and KERNAL ROMs. It's why the agent
  knows the PET has no `ELSE`, no C64-style `SETLFS`, and exactly 91 BASIC
  keywords.
- **Works with any MCP client.** Claude Code is built in, and Claude
  Desktop or any other MCP client can connect from outside the container.
- **`petrun`** for scripted, one-shot tests: run a program, type keys, check
  the screen, fail on `?SYNTAX ERROR`.

## Quick start

You need Docker. Pet Lab runs on anything from a laptop to a NAS with an
Atom CPU.

```bash
git clone https://github.com/Magic-of-Jafo/pet-lab.git
cd pet-lab
docker compose up -d --build        # first build takes a few minutes
```

Check it works (23 checks, about a minute):

```bash
docker exec pet-lab /opt/petlab-venv/bin/python /opt/petlab/tests/mcp_smoke.py
```

Then talk to the agent inside the lab:

```bash
docker exec -it pet-lab claude      # log in once; your login is kept in ./home
```

and ask for something:

```
Make a snake game for my PET. Test it in the emulator before you hand it over.
```

Your programs land in `./workspace/programs`.

### Use it from Claude Desktop (or any MCP client)

Point your client at the server inside the container. For Claude Desktop,
add this to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pet": {
      "command": "docker",
      "args": ["exec", "-i", "pet-lab", "pet-mcp"]
    }
  }
}
```

Docker on another machine? Use `ssh`:
`"command": "ssh", "args": ["you@nas", "docker", "exec", "-i", "pet-lab", "pet-mcp"]`.
More in [docs/mcp.md](docs/mcp.md).

## Try it without an AI

`petrun` is handy on its own:

```bash
docker exec pet-lab sh -c 'cd /workspace && cat > HELLO.BAS <<"EOF"
10 PRINT "{CLR}WHAT IS YOUR NAME";
20 INPUT N$
30 PRINT "HELLO, ";N$;"!"
EOF
petrun HELLO.BAS --wait 2 --keys "ADA\r" --wait 1'
```

```
+----------------------------------------+ final
|WHAT IS YOUR NAME? ADA                  |
|HELLO, ADA!                             |
|READY.                                  |
+----------------------------------------+
NO BASIC ERRORS ON SCREEN
```

## Getting programs onto a real PET

Pet Lab writes ordinary `.PRG` files. Put them on whatever your PET reads:
an SD-card drive (SD2PET, petSD+, PETdisk MAX), a disk image for a real
drive, or a network drive.

With a **PETdisk MAX**, the PET can load straight from a folder on your
network (`LOAD"BOUNCE",9`). Pet Lab's sister project
[petdisk-max `fixes`](https://github.com/Magic-of-Jafo/petdisk-max/tree/fixes)
fixes the PETdisk's network drive bugs and hardens its server script, and
its [PRD](https://github.com/Magic-of-Jafo/petdisk-max/blob/fixes/docs/AGENT_CHANNEL_PRD.md)
plans the next step: typing to an AI **from the PET's own keyboard**. See
[docs/real-pet.md](docs/real-pet.md).

## Documentation

| | |
|---|---|
| [Getting started](docs/getting-started.md) | Install, first session, workspace layout, updating |
| [MCP server](docs/mcp.md) | Every tool, connecting clients, how breakpoints behave |
| [petrun](docs/petrun.md) | The command-line tester |
| [PET reference](pet-ref/) | BASIC 4.0, memory map, KERNAL, screen, hardware, machine language, disk |
| [How it works](docs/architecture.md) | Headless VICE, the monitor protocol, design choices |
| [Real PET](docs/real-pet.md) | Moving programs to hardware, PETdisk MAX, roadmap |
| [Troubleshooting](docs/troubleshooting.md) | Build problems, NAS quirks, emulator issues |

## Roadmap

- **Now:** emulated PET 4032, MCP server, petrun, reference, examples.
- **Next:** MCP over HTTP for clients elsewhere on your network; a tool to
  publish programs to a PETdisk MAX network drive.
- **Then:** chat with an AI from the PET itself, through the PETdisk MAX
  ([PRD](https://github.com/Magic-of-Jafo/petdisk-max/blob/fixes/docs/AGENT_CHANNEL_PRD.md)).
- More machines: the 8032 (80 columns) and the original 2001.

Ideas and pull requests welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

Pet Lab stands on [VICE](https://vice-emu.sourceforge.io/) (the emulator
and petcat), [cc65](https://cc65.github.io/),
[ACME](https://sourceforge.net/projects/acme-crossass/), xa65, the
[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), and
[bitfixer's PETdisk MAX](https://github.com/bitfixer/petdisk-max).

The Commodore PET ROMs are not part of this repository. The Docker build
fetches them from the official VICE source release. Pet Lab is a hobby
project and is not affiliated with Commodore, the VICE team or bitfixer.

## License

MIT, see [LICENSE](LICENSE).
