# Troubleshooting

## Building

**`dpkg: error processing package systemd` / `Failed to take /etc/passwd lock`**
Seen on Synology. The Dockerfile already installs `dbus-x11` so systemd
isn't pulled in; if you changed the package list, keep it.

**`NanoCPUs can not be set` when limiting CPU**
Some NAS kernels don't support `--cpus`. Use `--cpuset-cpus=0-2` instead.

**Docker Hub downloads fail with `httpReadSeeker: failed open ... EOF`**
Seen with Docker Desktop's built-in proxy on large layers. Retry, or build
on another host (`scripts/deploy.sh`), or copy an image across with
`docker save | ssh host docker load`.

**`docker compose build` sits there doing nothing**
Seen with Synology's Compose v2 (BuildKit): no build step runs and the CPU
is idle. Build with plain Docker instead, then start with Compose:
`docker build -t pet-lab:latest . && docker compose up -d`.
`scripts/deploy.sh` does this.

**The VICE ROM download fails**
The build fetches the VICE 3.9 source release from SourceForge. If it's
unreachable, try again later or change `VICE_VERSION` to a current
release that matches Debian's `vice` package version.

## Running

**Files in `./workspace` belong to the wrong user**
Rebuild with your ids: `PETLAB_UID=$(id -u) PETLAB_GID=$(id -g) docker compose up -d --build`.

**`EMULATOR FAILED` / `PET did not reach READY.`**
Look at the VICE log in the error message. Make sure the container is
running (`docker ps`), since the virtual display starts with it.

**A program runs but the screen looks wrong in text**
`▒` stands for any PET graphics character and `█` for a reverse space.
Use `pet_screen(include_image=true)` or `petrun --shot` to see the real
thing.

**Typed keys come out wrong**
Letters are typed unshifted (uppercase on screen). Use `{NAME}` for
special keys and `{n}` for a PETSCII code. The STOP key can't be typed
through the keyboard buffer; use `pet_reset` instead.

**`?SYNTAX ERROR` on a keyword that "should" work**
Check `pet-ref/basic4.md`. PET BASIC 4.0 has exactly 91 keywords: no
`ELSE`, no `WHILE`, and none of the C64/C128 graphics or sound commands.
`petcat -w40` also accepts CBM-II keywords (`BANK`, `BLOAD`, `DCLEAR`,
`BSAVE`) that the PET doesn't have.

**Claude Code mentions Gmail, Stripe or other connectors**
It sees your claude.ai account's connectors. Start it with
`--mcp-config /workspace/.mcp.json --strict-mcp-config` to limit it to the
`pet` tools.

## Asking for help

Open an issue with what you ran, the output, and your Docker host (OS,
CPU, Docker version).
