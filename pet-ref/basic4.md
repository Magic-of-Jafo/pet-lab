# BASIC 4.0 on the PET 4032

BASIC 4.0 is Commodore's Microsoft BASIC 2.0 plus disk commands. On a 32 KB
4032 it starts with **31743 BYTES FREE** [EMU].

## Keywords and tokens [ROM]

The ROM's keyword table (at $B0B2) has exactly 91 entries, tokens $80–$DA.
These are all of them; there are no others.

| Token | Keyword | Token | Keyword | Token | Keyword | Token | Keyword |
|---|---|---|---|---|---|---|---|
| 80 | END | 97 | POKE | AE | ^ | C5 | VAL |
| 81 | FOR | 98 | PRINT# | AF | AND | C6 | ASC |
| 82 | NEXT | 99 | PRINT | B0 | OR | C7 | CHR$ |
| 83 | DATA | 9A | CONT | B1 | > | C8 | LEFT$ |
| 84 | INPUT# | 9B | LIST | B2 | = | C9 | RIGHT$ |
| 85 | INPUT | 9C | CLR | B3 | < | CA | MID$ |
| 86 | DIM | 9D | CMD | B4 | SGN | CB | GO |
| 87 | READ | 9E | SYS | B5 | INT | CC | CONCAT |
| 88 | LET | 9F | OPEN | B6 | ABS | CD | DOPEN |
| 89 | GOTO | A0 | CLOSE | B7 | USR | CE | DCLOSE |
| 8A | RUN | A1 | GET | B8 | FRE | CF | RECORD |
| 8B | IF | A2 | NEW | B9 | POS | D0 | HEADER |
| 8C | RESTORE | A3 | TAB( | BA | SQR | D1 | COLLECT |
| 8D | GOSUB | A4 | TO | BB | RND | D2 | BACKUP |
| 8E | RETURN | A5 | FN | BC | LOG | D3 | COPY |
| 8F | REM | A6 | SPC( | BD | EXP | D4 | APPEND |
| 90 | STOP | A7 | THEN | BE | COS | D5 | DSAVE |
| 91 | ON | A8 | NOT | BF | SIN | D6 | DLOAD |
| 92 | WAIT | A9 | STEP | C0 | TAN | D7 | CATALOG |
| 93 | LOAD | AA | + | C1 | ATN | D8 | RENAME |
| 94 | SAVE | AB | - | C2 | PEEK | D9 | SCRATCH |
| 95 | VERIFY | AC | * | C3 | LEN | DA | DIRECTORY |
| 96 | DEF | AD | / | C4 | STR$ | | |

**Not in PET BASIC 4.0:** `DCLEAR`, `BANK`, `BLOAD`, `BSAVE` (CBM-II
B-series only). `petcat -w40` will still tokenize them, and the PET then
gives `?SYNTAX ERROR`. Also no `ELSE`, `WHILE`, `GRAPHIC`, `COLOR`, `SOUND`.

`GET#` is `GET` followed by `#`; `GO TO` works because `GO` is a token.

## Reserved variables

| Name | Meaning |
|---|---|
| `ST` | I/O status of the last operation: 64 = end of file, 2 = read timeout, 128 = device not present [EMU for 64; others DOC] |
| `TI` | Jiffy clock, 60 per second, since power on (also bytes $8D–$8F) [EMU] |
| `TI$` | Time as "HHMMSS"; assign to set the clock: `TI$="120000"` [DOC] |
| `DS` | Disk status number from the current drive [EMU] |
| `DS$` | Disk status text, e.g. `00, OK,00,00` [EMU] |

## Program and variable rules

- Line numbers 0–63999. A logical line may be up to 80 characters
  (two 40-column screen lines) when typed [DOC].
- Variable names: only the first **two** characters count (`SCORE` and
  `SCALE` are the same variable). Names must not contain keywords
  (`TOTAL` contains `TO`) [DOC].
- Types: `A` float, `A%` integer (−32768..32767, not faster), `A$` string
  (up to 255 characters).
- Arrays over 11 elements need `DIM`.
- `DEF FN F(X)=...` takes one numeric argument.
- `FOR` loops always run at least once.
- `IF ... THEN` with no `ELSE`; the rest of the line runs only when true.
- `ON X GOTO 100,200,300` / `ON X GOSUB ...`.

## Input

- `INPUT A$` stops at a comma or colon and warns `?EXTRA IGNORED`; quotes
  are special. For free text, read characters with `GET` and build the
  string yourself.
- `GET A$` returns `""` immediately if no key is waiting. A key-wait loop:
  `10 GET A$:IF A$="" THEN 10`.
- `GET#n,A$` returns `""` for a zero byte; use `ASC(A$+CHR$(0))` to get
  the byte value safely.

## Output and the screen

- `PRINT` control characters in strings (see [screen.md](screen.md)):
  `{clr}` clear, `{home}`, `{down}`, `{up}`, `{left}`, `{right}`,
  `{rvs on}`, `{rvs off}`. In listings for petrun write them in braces.
- `TAB(n)`, `SPC(n)`, `POS(0)` work as on other Commodores.
- Cursor position: column in $C6, row in $D8 [EMU]. To place the cursor,
  print `{home}` and then `{down}`/`{right}` (there is no PLOT routine in
  the KERNAL jump table).

## Disk commands [EMU: syntax accepted by the ROM]

All take optional `,Dd` (drive 0 or 1) and `,Uu` or `ON Uu` (device,
default 8). Names can be expressions in parentheses: `DSAVE (N$)`.

| Command | Example |
|---|---|
| `DSAVE "name"` | `DSAVE "@GAME"` (`@` replaces an existing file), `DSAVE "GAME",D0,U9` |
| `DLOAD "name"` | `DLOAD "GAME",U9` |
| `DIRECTORY` / `CATALOG` | `DIRECTORY`, `CATALOG D0,U9`, `DIRECTORY D0 ON U9` |
| `SCRATCH "name"` | Deletes. Asks `ARE YOU SURE ?` in direct mode [ROM text] |
| `RENAME "old" TO "new"` | |
| `COPY "src" TO "dst"` | Also whole-disk `COPY D0 TO D1` on dual drives |
| `CONCAT "a" TO "b"` | Appends file a to file b |
| `DOPEN#lf,"name"` | Open sequential file for reading; add `,W` to write: `DOPEN#2,"DATA",W` |
| `APPEND#lf,"name"` | Open sequential file to add to its end |
| `DCLOSE#lf` | Close (or `DCLOSE` to close all on the drive) |
| `RECORD#lf,rec[,byte]` | Position in a relative file |
| `HEADER "name",Iid,D0` | **Formats the disk.** Never run in tests |
| `COLLECT D0` | Validates the disk |
| `BACKUP D0 TO D1` | Dual-drive disk copy |

Classic forms still work: `LOAD"name",8`, `SAVE"name",8`,
`OPEN 2,8,2,"name,S,W"`, `PRINT#2,...`, `INPUT#2,...`, `GET#2,A$`,
`CLOSE 2`, and the command channel `OPEN 15,8,15,"command"`.

## Error messages [ROM]

BASIC (`?... ERROR`, `IN line` when running): NEXT WITHOUT FOR, SYNTAX,
RETURN WITHOUT GOSUB, OUT OF DATA, ILLEGAL QUANTITY, OVERFLOW, OUT OF
MEMORY, UNDEF'D STATEMENT, BAD SUBSCRIPT, REDIM'D ARRAY, DIVISION BY ZERO,
ILLEGAL DIRECT, TYPE MISMATCH, STRING TOO LONG, FILE DATA, FORMULA TOO
COMPLEX, CAN'T CONTINUE, UNDEF'D FUNCTION.

I/O (from the KERNAL): FILE OPEN, FILE NOT OPEN, FILE NOT FOUND, DEVICE NOT
PRESENT, NOT INPUT FILE, NOT OUTPUT FILE.

## Speed tips [DOC]

- Put frequently used variables first (variables are searched in order of
  creation), and numbers used in loops into variables.
- Several statements per line with `:` is faster than many short lines.
- `GOTO`/`GOSUB` to low line numbers is faster (lines are searched from the
  start, or from the current line when jumping forward).
- Direct screen writes with `POKE 32768+40*ROW+COL,CODE` are much faster
  than `PRINT` positioning for games.

## Writing listings for petrun

- Write keywords in full and in UPPERCASE; petrun converts case for petcat.
- Control characters go in braces: `{clr}`, `{rvs on}`.
- Test with `petrun PROG.BAS --wait 3 --screen ...`; a `?...ERROR` on the
  screen makes petrun exit with code 1.
