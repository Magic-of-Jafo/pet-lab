# PET 4032 memory map (BASIC 4.0)

## Overview

| Range | Use | |
|---|---|---|
| $0000–$00FF | Zero page (BASIC and KERNAL variables, below) | |
| $0100–$01FF | 6502 stack | |
| $0200–$03FF | KERNAL/editor work area, file tables, keyboard buffer, cassette buffers | |
| $0400–$7FFF | User RAM: BASIC program, variables, strings (32 KB machine) | [EMU] |
| $8000–$83E7 | Screen memory, 40×25 = 1000 bytes | [EMU] |
| $9000–$AFFF | Expansion ROM sockets (empty on a stock 4032) | [DOC] |
| $B000–$DFFF | BASIC 4.0 ROM, including the machine language monitor | [ROM] |
| $E000–$E7FF | Screen editor ROM | [ROM] |
| $E800–$EFFF | I/O: PIA1 $E810, PIA2 $E820, VIA $E840, CRTC $E880 (see [hardware.md](hardware.md)) | [ROM] |
| $F000–$FFFF | KERNAL ROM, jump table at $FFC0, vectors at $FFFA | [ROM] |

## BASIC memory pointers (two bytes, low first) [EMU]

| Address | Dec | Name | Value after RUN of a small program |
|---|---|---|---|
| $28 | 40 | Start of BASIC text (TXTTAB) | 1025 ($0401) |
| $2A | 42 | Start of variables (VARTAB) | end of program |
| $2C | 44 | Start of arrays (ARYTAB) | |
| $2E | 46 | End of arrays (STREND) | |
| $30 | 48 | Bottom of strings (FRETOP); strings grow down from MEMSIZ | 32768 |
| $34 | 52 | Top of BASIC memory (MEMSIZ) | 32768 |

To reserve memory for machine code at the top of RAM, lower MEMSIZ and
FRETOP before any strings are made, then `CLR`:
`POKE 52,0:POKE 53,112:POKE 48,0:POKE 49,112:CLR` (BASIC keeps out of
$7000–$7FFF; `FRE(0)` drops accordingly). [EMU] `CLR` also erases all
variables, so do this first thing in the program.

## Zero page and low RAM

| Address | Dec | Meaning | |
|---|---|---|---|
| $00–$02 | 0–2 | `USR` jump: $4C (JMP) then address, default $C373 | [EMU] |
| $8D–$8F | 141–143 | Jiffy clock, 3 bytes high to low, = `TI` | [EMU] |
| $90–$91 | 144–145 | IRQ vector, default $E455 | [EMU][ROM] |
| $92–$93 | 146–147 | BRK vector, default $D478 (monitor) | [EMU][ROM] |
| $94–$95 | 148–149 | NMI vector, default $B3FF | [EMU] |
| $96 | 150 | `ST` I/O status | [EMU] |
| $9E | 158 | Number of characters in the keyboard buffer | [EMU] |
| $9F | 159 | Reverse video flag (18 when on) | [EMU] |
| $A7–$AA | 167–170 | Cursor blink: switch, countdown, character under cursor, phase | [ROM] |
| $AE | 174 | Number of open files | [EMU] |
| $C4–$C5 | 196–197 | Pointer to the start of the cursor's screen line | [ROM] |
| $C6 | 198 | Cursor column | [EMU] |
| $D1 | 209 | Length of the current file name | [EMU] |
| $D2 | 210 | Current logical file number | [EMU] |
| $D3 | 211 | Current secondary address, stored OR $60 (15 → 111) | [EMU] |
| $D4 | 212 | Current device number | [EMU] |
| $D5 | 213 | Screen line length − 1 (39) | [EMU] |
| $D8 | 216 | Cursor row | [EMU] |
| $DA–$DB | 218–219 | Pointer to the current file name | [EMU] |
| $0251–$025A | 593–602 | Logical file numbers of open files | [EMU] |
| $025B–$0264 | 603–612 | Device numbers of open files | [EMU] |
| $0265–$026E | 613–622 | Secondary addresses of open files (OR $60) | [EMU] |
| $026F–$0278 | 623–632 | Keyboard buffer, 10 characters (count in $9E) | [EMU] |
| $027A–$0339 | 634–825 | Cassette buffer #1 | [DOC] |
| $033A–$03F9 | 826–1017 | Cassette buffer #2 (referenced by the KERNAL) | [ROM] |

Feeding keys from a program: put PETSCII codes at 623.. and the count in
158, e.g. `POKE 623,13:POKE 158,1` types RETURN. [EMU]

## Free space for small machine code routines

- **Cassette buffer #2, $033A–$03F9 (192 bytes)**, safe when tape drive #2
  isn't used [DOC]; code POKEd at 826 and started with `SYS 826` runs
  [EMU]. Buffer #1 ($027A–$0339) is safe when no tape is used at all [DOC].
- **Top of RAM**, protected by lowering MEMSIZ (above). Best for anything
  larger.
- **After a BASIC program**: a BASIC loader with a `SYS` line at $0401 and
  the machine code following it (see [machine-language.md](machine-language.md)).
- Zero page is almost entirely used by BASIC and the KERNAL. Save and
  restore any zero page bytes you borrow.
