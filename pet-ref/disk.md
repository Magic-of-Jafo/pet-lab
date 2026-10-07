# Disk files, the command channel and the PETdisk MAX

The real PET uses a **PETdisk MAX**: SD card on device 8 and a network
drive (a folder on the Synology served by `petdisk.php`) on device 9. In
pet-lab, `petrun --drive 9=FOLDER` gives the emulator a folder as a drive
for testing.

## Files from BASIC

```
10 OPEN 2,9,2,"SCORES,S,W"        : REM SEQUENTIAL, WRITE
20 PRINT#2,"ALICE";CHR$(13);"42"
30 CLOSE 2
40 OPEN 2,9,2,"SCORES,S,R"        : REM SEQUENTIAL, READ
50 INPUT#2,N$,S
60 CLOSE 2
```

Or the BASIC 4 forms: `DOPEN#2,"SCORES",W`, `INPUT#2,...`, `DCLOSE#2`,
`APPEND#2,"SCORES"` [EMU]. See [basic4.md](basic4.md) for all disk
commands.

Reading byte by byte, safely:

```
100 OPEN 2,9,2,"DATA,S,R"
110 GET#2,A$:B=ASC(A$+CHR$(0)):S=ST
120 REM ... USE B ...
130 IF S=0 THEN 110
140 CLOSE 2
```

`ST` is 64 after the last byte. Check `ST` right after the `GET#`, before
anything else changes it.

- Use `"@:NAME"` or `"@NAME"` to replace an existing file.
- `INPUT#` has the same comma/colon limits as `INPUT`; write one item per
  line (`CHR$(13)` between items) and read with `INPUT#`, or use `GET#`.
- The command channel: `OPEN 15,9,15` then `PRINT#15,"command"` and
  `INPUT#15,E,E$,T,S` for status.

## PETdisk MAX specifics

From the firmware source and testing (see the `fixes` branch of
github.com/Magic-of-Jafo/petdisk-max):

- File names on the network drive become files like `SCORES.SEQ` and
  `GAME.PRG` in the server folder. `LOAD"GAME",9` finds `GAME.PRG`.
- `LOAD"$",9` lists the folder; `LOAD"$:GAMES",9` / `PRINT#15,"CD:GAMES"`
  goes into a subfolder and `LOAD"$:..",9` / `"CD←"` goes back up
  (subfolders on network drives need the `fixes` firmware and the new
  `petdisk.php`).
- `.D64` disk images can be mounted with `LOAD"$:NAME.D64",8`. **Don't
  save into a mounted D64**: an open upstream bug can corrupt it.
- The status channel does not return standard Commodore DOS error codes.
  Don't rely on `DS$` or `INPUT#15` from a PETdisk; test `ST` instead.
- One open file per network drive at a time is safest. Reading one
  network file while writing another on the same drive was unreliable in
  older firmware.
- Scratch, rename and copy are not supported. Manage files on the server
  side.
- Wildcards: avoid `LOAD"*",9` with older firmware (it could hang).

## Handing programs to the real PET

Programs saved as `NAME.PRG` into the network drive's folder can be loaded
on the PET with `LOAD"NAME",9`. Use names of up to 16 characters, letters
and digits only, uppercase.
