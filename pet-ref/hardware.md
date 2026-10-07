# PET 4032 hardware: I/O chips, keyboard, sound, IEEE-488

The I/O area is $E800–$EFFF. The chip addresses below are the ones the
BASIC 4 ROMs use [ROM: counted references in `/opt/pet-rom/*.dis`].
Register meanings are from the chips' datasheets and long-standing PET
documentation [DOC].

| Chip | Address | Main jobs |
|---|---|---|
| PIA 1 (6520) | $E810–$E813 | Keyboard row select / column read, cassette sense, EOI in, video retrace interrupt (60 Hz IRQ) |
| PIA 2 (6520) | $E820–$E823 | IEEE-488 data in/out and ATN/NDAC control lines |
| VIA (6522) | $E840–$E84F | IEEE-488 NRFD/NDAC/DAV/ATN lines, user port, timers, shift register (CB2 sound), character set select |
| CRTC (6545) | $E880 (register select), $E881 (data) | Video timing; programmed by the editor from an 18-register table |

## PIA 1 [DOC]

| Address | Dec | Register |
|---|---|---|
| $E810 | 59408 | Port A: bits 0–3 keyboard row to scan, bit 4–5 cassette switch sense, bit 6 EOI in, bit 7 diagnostic sense |
| $E811 | 59409 | Control A |
| $E812 | 59410 | Port B: keyboard columns of the selected row (0 = key down) |
| $E813 | 59411 | Control B (CB1: video retrace, the 60 Hz interrupt) |

Reading the keyboard yourself: write a row number to $E810, read $E812.
Graphics and business keyboards have different matrices; prefer `GETIN`
or `GET` unless you need several keys at once.

## VIA [DOC]

| Address | Dec | Register |
|---|---|---|
| $E840 | 59456 | Port B: IEEE-488 handshake lines, cassette motor/write |
| $E841 | 59457 | Port A (user port) with handshake |
| $E842/$E843 | 59458/59459 | Data direction B / A |
| $E844/$E845 | 59460/59461 | Timer 1 low / high |
| $E848/$E849 | 59464/59465 | Timer 2 low / high |
| $E84A | 59466 | Shift register |
| $E84B | 59467 | Auxiliary control |
| $E84C | 59468 | Peripheral control (12 = graphics set, 14 = text set) [EMU] |
| $E84D | 59469 | Interrupt flags |
| $E84E | 59470 | Interrupt enable |
| $E84F | 59471 | Port A (user port) without handshake |

## Sound (CB2) [DOC]

The PET has no sound chip. The VIA shift register drives the CB2 line,
which reaches the internal speaker on 12" models (or a speaker on the
user port):

```
POKE 59467,16        : REM SHIFT REGISTER FREE-RUNNING
POKE 59466,15        : REM WAVE SHAPE (15, 51, 85 SOUND DIFFERENT)
POKE 59464,N         : REM PITCH, LOWER N = HIGHER NOTE
POKE 59467,0         : REM SOUND OFF
```

The emulator can't confirm how this sounds; test music on the real PET.

## User port [DOC]

8 data lines on VIA port A (`POKE 59459,255` makes all outputs, then
`POKE 59471,value`; `PEEK(59471)` reads them). CB2 is also on the user
port.

## IEEE-488

Disk drives, printers and the PETdisk MAX connect here. From BASIC use the
disk commands in [basic4.md](basic4.md); from machine code use the KERNAL
calls in [kernal.md](kernal.md). Don't drive the bus lines directly.

## Timing

- 1 MHz 6502.
- Jiffy clock: 60 Hz from the video retrace on this 60 Hz machine [EMU:
  `TI` advances].
- For delays in BASIC, wait on `TI` rather than empty `FOR` loops:
  `10 T=TI` / `20 IF TI-T<60 THEN 20` waits one second.
