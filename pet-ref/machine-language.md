# Machine language and C on the PET 4032

Tools in pet-lab: **ACME** (assembler), **cc65** (`cl65` C compiler and
`ca65`/`ld65` assembler/linker with a PET target, `da65` disassembler),
**xa65** (assembler), and VICE's monitor through `petrun`.

## Recipe 1: assembly with a BASIC SYS line (ACME) [EMU]

The program loads at $0401 like a BASIC program and starts itself with
`RUN`, so on the real PET it's just `LOAD"HELLO",9` and `RUN`.

```
; hello.a  -  assemble with:  acme hello.a   (writes HELLO.PRG)
!cpu 6502
!to "HELLO.PRG", cbm        ; cbm = 2-byte load address header
* = $0401
        !word basic_end, 10 ; BASIC line 10 ...
        !byte $9e           ; ... SYS
        !text "1037", 0     ; 1037 = $040D, the first byte after the stub
basic_end:
        !word 0             ; end of BASIC program
start:  ldx #0
loop:   lda msg,x
        beq done
        jsr $ffd2           ; CHROUT
        inx
        bne loop
done:   rts
msg:    !text "HELLO FROM MACHINE CODE", 13, 0
```

Test: `petrun HELLO.PRG --wait 2`.

The stub is 12 bytes, so code starts at $040D = 1037. If you change the
line number or the digits, recount: the address in the SYS text must be
the byte right after the final `!word 0`.

ACME tips: `!text` copies ASCII bytes as they are, which is right for
uppercase letters, digits and punctuation in graphics mode. `acme -r
listing.txt prog.a` writes a listing with addresses, which you need for
breakpoints.

## Recipe 2: machine code at a fixed address

```
!to "ML7000.PRG", cbm
* = $7000
...
```

A PRG that doesn't load at $0401 is only loaded by petrun, not RUN. Start
it with `--sys`:

```
petrun ML7000.PRG --sys '$7000' --wait 1 --screen
```

On the real PET: `LOAD"ML7000",9`. The PET always loads a file at its
own address; there is no `,1` as on the C64 [EMU: `LOAD"ML7000",8` put
the code at $7000]. Then `NEW` (LOAD in direct mode moves BASIC's end of
program pointer to the end of the loaded file) [DOC], then `SYS 28672`. Protect $7000–$7FFF from BASIC first if a BASIC program
will run too (see [memory-map.md](memory-map.md)).

## Recipe 3: C with cc65 [EMU]

```
/* helloc.c */
#include <stdio.h>
int main(void) { printf("hello from c, 2+2=%d\n", 2 + 2); return 0; }
```

```
cl65 -t pet -O -o HELLOC.PRG helloc.c
petrun HELLOC.PRG --wait 3
```

The output includes a BASIC SYS line, so it runs with `RUN`. Write
lowercase in C strings: cc65's PET target converts them so they show as
uppercase in graphics mode (the example prints `HELLO FROM C, 2+2=4`).
The C runtime adds about 2.5 KB. `conio.h` gives direct screen access
(`gotoxy`, `cputc`, `cgetc`).

cc65's headers are in `/usr/share/cc65/include` (`pet.h`, `cbm.h`,
`conio.h`); read them for what the PET library offers. The Debian package
has no HTML manual; the full documentation is at https://cc65.github.io/doc/
(PET target: `pet.html`).

## Debugging with petrun [EMU]

```
petrun PROG.PRG --break '$700f' --sys '$7000' --until-break 5 \
       --peek '$7100' --peek '$8000-$8027' --regs --wait 1
```

| Option | Does |
|---|---|
| `--break ADDR` | Stop when the CPU executes ADDR (set before starting the code) |
| `--until-break S` | Wait up to S seconds for the stop; prints where it stopped and the registers. The CPU stays stopped for the following `--peek`/`--regs`/`--mon` |
| `--peek A-B` | Hex dump |
| `--regs` | Registers |
| `--mon CMD` | Any VICE monitor command, e.g. `--mon 'd 7000 7020'` to disassemble |
| `--wait`, `--keys`, `--sys` | Continue running |

Typical loop: assemble with a listing, find the address of the line in
question, break there, look at registers and memory, fix, repeat.

## Things that bite

- **Decimal mode.** Clear it (`CLD`) before arithmetic if your code can be
  entered from an interrupt or after other code.
- **Zero page.** BASIC and the KERNAL use most of it. Save and restore
  bytes you borrow; $FB–$FE are often used by programs but are not
  guaranteed free on the PET [DOC].
- **Screen codes vs PETSCII.** `CHROUT` takes PETSCII; writing to $8000
  takes screen codes ([screen.md](screen.md)).
- **No C64 KERNAL calls.** No SETLFS/SETNAM/PLOT ([kernal.md](kernal.md)).
- **Returning to BASIC.** End with `RTS` when started by `SYS`.
- **Interrupts.** Change $90/$91 only between `SEI` and `CLI`, and chain
  to $E455.

## Disassembling

- ROMs: already done, in `/opt/pet-rom/*.dis`.
- Any PRG: strip the 2-byte load address first, then disassemble at that
  address:
  `tail -c +3 PROG.PRG > /tmp/p.bin && da65 --cpu 6502 --start-addr 0x0401 /tmp/p.bin`
- Inside a running program: `petrun PROG.PRG --mon 'd 7000 7040'`.
