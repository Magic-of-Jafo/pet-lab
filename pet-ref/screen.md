# Screen, screen codes and PETSCII (PET 4032)

## Screen memory [EMU]

- 40 columns × 25 rows at $8000–$83E7 (32768–33767).
- Position of row R (0–24), column C (0–39): `32768 + 40*R + C`.
- A byte in screen memory is a **screen code**, not PETSCII.
- Bit 7 set = reverse video (`B` = 2, reverse `B` = 130).

## Screen codes in graphics mode (the default) [EMU spot checks]

| Screen code | Shows |
|---|---|
| 0 | `@` |
| 1–26 | `A`–`Z` |
| 27–31 | `[` `\` `]` `↑` `←` |
| 32–63 | space, `!"#$%&'()*+,-./`, `0`–`9`, `:;<=>?` (same as PETSCII) |
| 64–127 | PET graphics characters |
| 128–255 | reverse versions of 0–127 |

## PETSCII → screen code when PRINTed [EMU spot checks]

| PETSCII | Screen code | Example |
|---|---|---|
| 32–63 | same | `!` 33 → 33 |
| 64–95 | − 64 | `A` 65 → 1, `@` 64 → 0, `[` 91 → 27 |
| 96–127 | − 64 | 97 → 33 (on this PET, codes 96–127 print like 32–63) |
| 160–191 | − 64 | graphics [DOC] |
| 192–223 | − 128 | 193 → 65 (graphics) |

When POKEing text to the screen, convert letters with `ASC(C$)-64`.

## Control characters [EMU unless marked]

| Code | `{name}` in petrun listings | Effect |
|---|---|---|
| 13 | | RETURN |
| 14 | | Text mode: lowercase + uppercase character set (VIA PCR $E84C becomes 14) |
| 142 | | Graphics mode: uppercase + graphics (PCR back to 12) |
| 147 | `{clr}` | Clear screen, cursor home |
| 19 | `{home}` | Cursor home |
| 17 / 145 | `{down}` / `{up}` | Cursor down / up |
| 29 / 157 | `{right}` / `{left}` | Cursor right / left |
| 18 / 146 | `{rvs on}` / `{rvs off}` | Reverse video on / off |
| 20 / 148 | `{del}` / `{inst}` | Delete / insert [DOC] |
| 7 | | Bell on models with a speaker [DOC] |

Also `POKE 59468,14` (text) and `POKE 59468,12` (graphics) [EMU].

In text mode, PETSCII 65–90 show as lowercase and 193–218 as uppercase,
which is the reverse of what ASCII suggests [DOC]. Replies meant for the
default graphics mode should be plain uppercase.

## Cursor

- Column in $C6, row in $D8 [EMU]; pointer to the line start in $C4/$C5
  [ROM].
- Place the cursor: `PRINT "{home}";:FOR I=1 TO R:PRINT "{down}";:NEXT`
  then `TAB(C)` or `{right}`s. Writing $C6/$D8 directly is not enough;
  the line pointer must match.
