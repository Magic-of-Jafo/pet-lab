# KERNAL and ROM routines (BASIC 4.0 PET)

## Jump table [ROM]

Read from `kernal-4.901465-22.bin`. Call these addresses, not the targets;
the targets differ between ROM versions.

| Address | Dec | Name | Target | Use |
|---|---|---|---|---|
| $FFC0 | 65472 | OPEN | $F560 | Open the file described by $D1–$D4, $DA |
| $FFC3 | 65475 | CLOSE | $F2DD | Close logical file in A |
| $FFC6 | 65478 | CHKIN | $F7AF | Make logical file X the input channel |
| $FFC9 | 65481 | CHKOUT | $F7FE | Make logical file X the output channel |
| $FFCC | 65484 | CLRCHN | $F2A6 | Restore keyboard/screen as input/output |
| $FFCF | 65487 | CHRIN | $F215 | Read a character from the input channel into A |
| $FFD2 | 65490 | CHROUT | $F266 | Write the character in A to the output channel |
| $FFD5 | 65493 | LOAD | $F401 | |
| $FFD8 | 65496 | SAVE | $F6DD | |
| $FFDB | 65499 | VERIFY | $F4F6 | |
| $FFDE | 65502 | SYS | $F6C3 | |
| $FFE1 | 65505 | STOP | $F343 | Z set if the STOP key is pressed |
| $FFE4 | 65508 | GETIN | $F205 | Get a key from the keyboard buffer into A (0 if none) |
| $FFE7 | 65511 | CLALL | $F2A2 | Close all files |
| $FFEA | 65514 | UDTIM | $F768 | Advance the jiffy clock (called by the IRQ) |

Hardware vectors: NMI $FD49, RESET $FD16, IRQ/BRK $E442 [ROM].

**Differences from the C64:** there is no SETLFS, SETNAM, PLOT, SCREEN,
IOBASE or MEMTOP call. Set the file parameters in zero page instead
(table below). Move the cursor by printing control characters.

## Opening a file from machine code

Set these, then `JSR $FFC0` [EMU: addresses and values observed after a
BASIC OPEN]:

| Address | Set to |
|---|---|
| $D2 | logical file number |
| $D4 | device number (8, 9, ...) |
| $D3 | secondary address OR $60 (e.g. 2 → $62, 15 → $6F) |
| $D1 | file name length |
| $DA–$DB | address of the file name |

Then `LDX #lf : JSR $FFC9` (CHKOUT) and write bytes with `JSR $FFD2`, or
`JSR $FFC6` (CHKIN) and read with `JSR $FFCF`, checking `ST` ($96) after
each read (bit 6 = end of file). Finish with `JSR $FFCC`, then
`LDA #lf : JSR $FFC3`.

Easier and safer for most programs: open the file in BASIC
(`OPEN 2,9,2,"DATA,S,W"`) and only do the transfer loop in machine code,
or use BASIC for all file work.

## The IRQ [ROM]

The CPU's IRQ vector points to $E442 in the editor ROM. It saves A, X, Y,
checks the B flag and jumps through ($0092) for BRK or ($0090) for an IRQ.
The default IRQ handler at $E455 calls UDTIM, blinks the cursor and scans
the keyboard. To add your own 60 Hz routine, point $90/$91 at it (with
`SEI`/`CLI` around the change) and end it with `JMP $E455`.

## The built-in monitor (TIM) [EMU]

BASIC 4 has a small machine language monitor. Location $0400 holds 0 (a
BRK), so `SYS 1024` enters it:

```
B*
     PC  IRQ  SR AC XR YR SP
.;  0401 E455 32 04 5E 00 F8
.
```

Commands include `M` (memory), `R` (registers), `G` (go), `L`/`S`
(load/save), `X` (exit to BASIC) [DOC]. In pet-lab, prefer VICE's
monitor through petrun (`--peek`, `--regs`, `--break`, `--mon`), which
doesn't change the PET's state.

## Useful BASIC ROM facts

- Keyword table at $B0B2, error messages at $B20D [ROM].
- Disassemblies with addresses: `/opt/pet-rom/basic4-b000.dis`.
  Search them rather than trusting remembered entry points for BASIC
  internals; BASIC 4 routines are at different addresses from BASIC 2 and
  from the C64.
