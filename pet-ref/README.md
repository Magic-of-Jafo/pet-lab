# PET 4032 programmer's reference

Reference for writing BASIC and machine language programs for a
**Commodore PET 4032**: BASIC 4.0, 40×25 screen with a CRTC, graphics
(N) keyboard, 60 Hz North American editor ROM, 32 KB RAM.

Written for the pet-lab agent and for people. It is plain text, short,
and says how each fact is known.

| File | Contents |
|---|---|
| [basic4.md](basic4.md) | BASIC 4.0: every keyword (from the ROM), statement syntax, disk commands, errors, quirks |
| [memory-map.md](memory-map.md) | Memory map and the zero page / low RAM locations that matter |
| [kernal.md](kernal.md) | KERNAL jump table, calling ROM routines from machine code, the built-in monitor |
| [hardware.md](hardware.md) | I/O chips (PIA, VIA, CRTC), keyboard, sound, user port, IEEE-488 |
| [screen.md](screen.md) | Screen memory, screen codes vs PETSCII, control characters |
| [machine-language.md](machine-language.md) | Toolchain recipes (ACME, cc65), where to put code, debugging with petrun |
| [disk.md](disk.md) | Disk and PETdisk MAX usage, DOS commands, PETdisk limitations |

## How facts are marked

| Mark | Meaning |
|---|---|
| **[ROM]** | Read from the actual ROM images in this container (`/usr/share/vice/PET`, disassemblies in `/opt/pet-rom`) |
| **[EMU]** | Checked by running code in VICE xpet configured as this machine |
| **[DOC]** | From chip datasheets or long-standing community documentation; not re-checked here |

If something here disagrees with what the ROM or the emulator does, trust
the ROM and the emulator, and fix this reference.

## Checking things yourself

- ROM disassemblies: `/opt/pet-rom/basic4-b000.dis`, `kernal4-f000.dis`,
  `edit4-40n-60hz-e000.dis` (`grep -n 'E840' /opt/pet-rom/*.dis`).
- Run a probe program: `petrun PROBE.BAS --wait 3` printing `PEEK`s, or
  `petrun CODE.PRG --peek '$0000-$00ff'` for raw memory.

## ROM set

| ROM | File | Address |
|---|---|---|
| BASIC 4.0 | `basic-4.901465-23-20-21.bin` | $B000–$DFFF |
| Editor, 40 columns, graphics keyboard, 60 Hz, CRTC | `edit-4-40-n-60Hz.901499-01.bin` | $E000–$E7FF |
| KERNAL 4.0 | `kernal-4.901465-22.bin` | $F000–$FFFF |
| Character generator | `characters-2.901447-10.bin` | (not CPU visible) |

Early 4032s with a 9" screen have no CRTC and a different editor ROM. If
your PET has a 9" screen, screen timing and the CRTC notes don't apply.
