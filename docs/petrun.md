# petrun

`petrun` boots a fresh PET, loads a program, does what you tell it, prints
the screen and exits. It's for scripted tests and quick checks; for
interactive work use the [MCP server](mcp.md).

```
petrun PROGRAM [steps...] [options]
```

`PROGRAM` is a BASIC listing (`.BAS`, any other extension) or a `.PRG`. A
program that loads at $0401 is `RUN`; machine code elsewhere is only
loaded.

## Steps (run in the order given)

| Step | |
|---|---|
| `--wait S` | Let the PET run S seconds (default if no steps: `--wait 3`) |
| `--keys TEXT` | Type. `\r` = RETURN; named keys like `{CLR}`, `{DOWN}` |
| `--screen` | Print the screen now |
| `--sys ADDR` | Type `SYS ADDR` (`$7000` or `28672`) |
| `--peek A-B` | Hex dump |
| `--regs` | CPU registers |
| `--mon CMD` | Any VICE monitor command, e.g. `--mon 'd 7000 7020'` |
| `--break ADDR` | Stop when the CPU executes ADDR... |
| `--until-break S` | ...and wait up to S seconds for it, then print the registers |

## Options

| Option | |
|---|---|
| `--shot FILE.png` | Save a screenshot at the end |
| `--prg OUT.PRG` | Only tokenize the BASIC listing and exit |
| `--drive N=DIR` | Use a folder as disk drive N (8–11) |
| `--model 4032` | PET model |
| `--hz 60` | 60 (North America) or 50 (Europe) editor ROM |
| `--warp` | Run flat out (timing not realistic) |

## Output and exit codes

The final screen is always printed, then `NO BASIC ERRORS ON SCREEN` or
`BASIC ERRORS: ...`.

| Exit code | |
|---|---|
| 0 | OK |
| 1 | A `?... ERROR` is on the screen |
| 2 | Tokenizing failed or bad arguments |
| 3 | The emulator failed |

## Writing BASIC listings

Write them as they look on the PET: UPPERCASE keywords and text. Lowercase
letters become shifted (graphics) characters. Control characters go in
braces: `{CLR}`, `{HOME}`, `{RVS ON}`, `{DOWN}`.

## Examples

```bash
petrun GAME.BAS --wait 2 --keys "1\r" --wait 2 --screen --keys "Q" --wait 1
petrun FILES.BAS --drive 9=disk9 --warp --wait 30
petrun MOVE.PRG --break '$7012' --sys '$7000' --until-break 5 --peek '$033a-$033d'
petrun GAME.BAS --prg GAME.PRG
```
