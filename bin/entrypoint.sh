#!/bin/sh
# Start a virtual X display for xpet (VICE's GTK UI needs one), then run CMD.
Xvfb :99 -screen 0 1024x768x24 -nolisten tcp >/tmp/xvfb.log 2>&1 &
exec "$@"
