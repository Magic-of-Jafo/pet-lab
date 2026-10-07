# Examples

Programs written and tested by an AI agent in Pet Lab. Each one is a
`.PRG` you can load on a real PET 4032.

## SPLASH

![SPLASH](../docs/images/hero.png)

The Pet Lab title card (also the picture at the top of the main README).
Pure BASIC: one `PRINT` per screen row, with reverse video and PET
graphics characters written as `{166}`-style codes. The agent's first
version POKEd the screen from `DATA` and took over 5 seconds to draw, so it
rewrote it with `PRINT`s.

**Prompt** (Claude Code, `pet` MCP tools only):

> Make a program called SPLASH: a striking full-screen title card for a
> project called PET LAB, using only PET graphics characters and reverse
> video in the default graphics mode. Requirements: the words PET LAB in
> large block letters near the top, a decorative border around the whole
> 40x25 screen, a small drawing of a PET computer or a circuit/lab motif in
> the middle area, and the line AI PAIR PROGRAMMING FOR THE COMMODORE PET
> near the bottom. It draws once and then waits for a key. Make it look
> great: check it with pet_screen include_image=true and refine the layout
> until it looks balanced.

| File | |
|---|---|
| `SPLASH.PRG` | `LOAD"SPLASH",8` then `RUN` |
| `SPLASH.BAS` | Source |
| `SPLASH.TEST.md` | The agent's test plan |
| `SPLASH.png` | Screenshot (native size) |

## BOUNCE

![BOUNCE](BOUNCE.png)

A ball bounces around the screen. BASIC calls a 102-byte machine code
routine (in the second cassette buffer, `SYS 830`) once per step until you
press a key.

**Prompt** (Claude Code, `pet` MCP tools only, no shell):

> Make a program called BOUNCE: a BASIC program with an embedded machine
> code routine that moves a ball character (screen code 81) diagonally
> across the screen, bouncing off the edges, once per call; BASIC calls it
> in a loop until a key is pressed. Develop and debug it with the pet MCP
> tools: use pet_break and pet_step on the routine at least once and check
> the ball position with pet_peek.

| File | |
|---|---|
| `BOUNCE.PRG` | Load and run: `LOAD"BOUNCE",8` then `RUN` |
| `BOUNCE.BAS` | The BASIC part (it POKEs the routine into memory) |
| `BOUNCE.A` | The routine in ACME assembly |
| `BOUNCE.TEST.md` | The agent's test plan |
| `BOUNCE.png` | Screenshot |

Try it in Pet Lab:

```bash
docker cp examples/BOUNCE.PRG pet-lab:/workspace/programs/
docker exec pet-lab petrun /workspace/programs/BOUNCE.PRG --wait 3 --shot /workspace/programs/bounce.png
```
