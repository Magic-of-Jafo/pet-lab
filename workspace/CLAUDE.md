# Pet Lab

You write programs for the user's real **Commodore PET 4032 (BASIC 4.0, 40×25
screen, graphics keyboard)** and test them in an emulated one first. The
user may be talking to you from the PET itself, so keep replies fit for a
40-column uppercase screen.

(If your PET is a different model, edit this file: model, screen width,
and the device number of your disk or network drive.)

## Target machine

- BASIC 4.0. Keep lines under 80 characters, line numbers 0–63999.
- Screen: 40 columns × 25 rows, screen RAM at $8000 (32768).
- Character set: uppercase + PET graphics. Write listings in UPPERCASE,
  exactly as they look on the PET. Lowercase letters become shifted
  (graphics) characters. Control codes go in braces, e.g. `{clr}`.
- 60 Hz North American machine (petrun uses the 60 Hz editor ROM).
- RAM: 32 KB, BASIC starts at $0401.
- Keyboard: graphics (N) keyboard. Prefer `GET` over `PEEK`-ing the keyboard
  matrix so programs don't depend on the keyboard layout.
- No sound chip. The CB2 "beep" trick (POKE 59467,16 / 59466 / 59464) is OK.

## Reference: look it up, don't guess

`/opt/pet-ref/` is a verified reference for this exact machine. Read the
relevant file **before** using a keyword, address or ROM routine you are
not certain of, and when debugging:

- `basic4.md`: all 91 BASIC 4.0 keywords (no others exist: no ELSE, no
  BANK/BLOAD/DCLEAR), disk command syntax, error messages, quirks
- `memory-map.md`, `kernal.md`: addresses, zero page, KERNAL jump table
  (no SETLFS/SETNAM/PLOT on the PET), the built-in monitor
- `screen.md`: screen codes vs PETSCII, control characters
- `hardware.md`: PIA/VIA/CRTC, sound, user port
- `machine-language.md`: ACME and cc65 recipes, petrun debugging
- `disk.md`: files, the command channel, PETdisk MAX limitations

ROM disassemblies with addresses: `/opt/pet-rom/*.dis`. Facts are marked
[ROM]/[EMU] (checked) or [DOC] (not re-checked). If you find a mistake,
say so in your reply; the reference is read-only for you.

## The `pet` MCP server (preferred)

The `pet` MCP tools give you one emulated PET that **keeps running between
calls**, so you can load, type, look, set breakpoints and inspect memory
step by step:

- `pet_load` (BASIC text or a PRG; RUNs it), `pet_type`, `pet_wait`,
  `pet_wait_for`, `pet_screen` (text, or an image with include_image)
- `pet_break`, `pet_continue`, `pet_step`, `pet_peek`, `pet_poke`,
  `pet_registers`, `pet_disassemble`, `pet_attach_drive`
- `basic_tokenize`, `basic_list`, `asm_acme`, `c_compile`
- `ref_search`, `ref_read`, `rom_lookup` for the verified reference

A breakpoint that hits during `pet_type`/`pet_load`/`pet_wait` is reported
in that tool's result, with registers; the CPU stays there until
`pet_continue`. `petrun` (below) still works for one-shot scripted tests.

## Machine language and C

You may write machine code (ACME: `acme prog.a`) or C (`cl65 -t pet -O
-o PROG.PRG prog.c`) when BASIC is too slow. Follow
`/opt/pet-ref/machine-language.md`. Debug with the MCP tools (`asm_acme`,
`pet_break`, `pet_step`, `pet_peek`, `pet_registers`) or petrun's
`--break`, `--until-break`, `--peek`, `--regs` and `--mon`. Hand over a single
`NAME.PRG` that starts with `RUN` (BASIC SYS stub at $0401) unless the
user asks otherwise.

## Workflow for every program request

1. Write the program as plain text: `programs/NAME.BAS` (uppercase NAME,
   max 16 characters, no spaces — it must be typeable as `LOAD"NAME",9`).
2. Before coding, write the test plan as comments in `programs/NAME.TEST.md`:
   the key sequences you will send and what the screen should show.
3. Test with `petrun` (headless VICE xpet 4032):
   ```
   petrun programs/NAME.BAS --wait 3 --screen --keys "1\r" --wait 2
   petrun programs/NAME.BAS --shot programs/NAME.png   # look at graphics
   ```
   Programs that use disk files: give the emulator a folder as a drive,
   `petrun programs/NAME.BAS --drive 9=programs/disk9` (the real PET's
   network drive is device 9). Add `--warp` for long file loops.
   It prints the 40×25 screen as text (▒ = a PET graphics character,
   █ = reverse space) and exits 1 if a `?…ERROR` appears on screen.
4. Fix and repeat until the test plan passes. Stop after 8 test-fix rounds
   and hand over the best version with a list of known problems.
5. Hand over:
   - Tokenize the final version: `petrun programs/NAME.BAS --prg programs/NAME.PRG`
     (always use petrun, not petcat directly: it fixes letter case and the
     $0401 load address)
   - Keep the previous handover as `NAME.V1.PRG`, `NAME.V2.PRG`, … before
     overwriting.

## Replies (they are shown on the PET)

- Plain text only. No Markdown, no emoji, no curly quotes, no tabs.
- Short. Lead with what to type, e.g. `LOAD"STARTREK",9` then `RUN`.
- Then the controls, then what you could NOT test in the emulator
  (feel, speed, anything timing-dependent).

## What the emulator can't tell you

- How fast or fun it feels on real hardware. Don't use `--warp` when
  checking timing.
- Anything involving the IEEE-488 bus / PETdisk itself.
