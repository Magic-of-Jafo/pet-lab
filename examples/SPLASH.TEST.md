# SPLASH test plan

1. Load and RUN, wait 4 s. Screen shows, with no ?...ERROR:
   - solid reverse-video border on row 0, row 24, column 0, column 39
   - PET LAB in block letters (reverse spaces, rounded corners,
     checkerboard drop shadow) on rows 2-7
   - a PET computer drawing in the middle (case, screen with READY.
     and a cursor, keyboard), with circuit traces / chip / flask beside it
   - AI PAIR PROGRAMMING / FOR THE COMMODORE PET centred near the bottom
     (41 characters do not fit in 38, so it is two lines)
   - no READY. prompt and no cursor: program is waiting
2. pet_screen include_image=true: check balance (equal margins left and
   right of the letters and the picture).
3. Wait 5 more seconds: screen unchanged (still waiting).
4. Type a key (space). Screen clears, READY. appears, no error.
5. Time the draw (without warp): should finish in about 2 s or less.
