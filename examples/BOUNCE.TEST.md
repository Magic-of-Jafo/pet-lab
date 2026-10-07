# BOUNCE test plan

ML routine at 830 ($033E), state at 826-829 ($033A-$033D):
826 = X (0-39), 827 = Y (0-24), 828 = DX (1 or 255), 829 = DY (1 or 255).
Each SYS 830 erases the old ball, moves one step diagonally, bounces off
the edges, and pokes screen code 81 at 32768+Y*40+X.

1. pet_load BOUNCE.BAS, wait 2 s: screen clear, one ball visible,
   no ?ERROR.
2. pet_break at the routine ($033E), pet_step through one call:
   X/Y at 826/827 change by DX/DY; pet_peek of the computed screen
   address shows $51 (81) and the old cell shows $20.
3. Edge cases (poke state, then single calls from direct mode):
   - X=39, DX=1  -> after call X=38, DX=255
   - X=0,  DX=255 -> X=1, DX=1
   - Y=24, DY=1  -> Y=23, DY=255
   - Y=0,  DY=255 -> Y=1, DY=1
   - Corner X=39,Y=24 DX=DY=1 -> X=38,Y=23 DX=DY=255
4. Let it run 10 s: only one ball on screen (no trail), always inside.
5. Press a key: program ends, screen cleared, READY. shown.
