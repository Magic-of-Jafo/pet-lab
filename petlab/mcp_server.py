"""PET MCP server: a persistent emulated Commodore PET for AI clients.

Tools drive one headless VICE xpet (PET 4032, BASIC 4.0 by default) that
keeps running between calls, plus the build tools (petcat, ACME, cc65) and
the verified machine reference.

Run:  python -m petlab.mcp_server            (stdio transport)

Environment:
  PETLAB_WORKSPACE   folder the file tools may use (default /workspace)
  PETLAB_REF         reference docs (default /opt/pet-ref)
  PETLAB_ROMDIS      ROM disassemblies (default /opt/pet-rom)
  PETLAB_IDLE        seconds before an idle emulator is shut down (default 1800)
"""
import atexit
import glob
import os
import re
import signal
import subprocess
import sys
import threading
import time

from mcp.server.fastmcp import FastMCP, Image

from . import basic, screen as scr
from .vice import Emulator, EmulatorError, parse_addr, find_free_port

WORKSPACE = os.path.realpath(os.environ.get("PETLAB_WORKSPACE", "/workspace"))
REF_DIR = os.environ.get("PETLAB_REF", "/opt/pet-ref")
ROMDIS_DIR = os.environ.get("PETLAB_ROMDIS", "/opt/pet-rom")
IDLE_SECONDS = float(os.environ.get("PETLAB_IDLE", "1800"))
MAX_WAIT = 120.0
TOOL_TIMEOUT = 120

mcp = FastMCP(
    "pet",
    instructions=(
        "A Commodore PET 4032 (BASIC 4.0, 40x25, 60 Hz) running in VICE, kept running "
        "between calls. Typical use: pet_load a BASIC listing (UPPERCASE, {CLR}-style "
        "control codes) or a PRG, pet_type keys, pet_screen to look. For machine code: "
        "asm_acme, then pet_break / pet_continue / pet_peek / pet_registers. Check facts "
        "with ref_search / ref_read before guessing addresses or keywords."
    ),
)

_lock = threading.RLock()
_emu = None
_settings = {"model": "4032", "hz": 60, "warp": False, "drives": {}}
_last_used = time.time()


# --- helpers ---------------------------------------------------------------

def _path(rel, must_exist=False):
    """Resolve a path inside the workspace."""
    full = os.path.realpath(os.path.join(WORKSPACE, rel))
    if full != WORKSPACE and not full.startswith(WORKSPACE + os.sep):
        raise ValueError(f"path must be inside the workspace ({WORKSPACE})")
    if must_exist and not os.path.exists(full):
        raise ValueError(f"not found: {rel}")
    return full


def _emulator():
    """The running emulator, started on first use."""
    global _emu, _last_used
    _last_used = time.time()
    if _emu is None or not _emu.alive():
        _emu = Emulator(_settings["model"], _settings["hz"], _settings["warp"],
                        _settings["drives"], port=find_free_port())
        _emu.start()
    return _emu


def _report(emu, label="screen"):
    lines = emu.screen_lines()
    text = scr.framed(lines, emu.cols, label)
    errors = scr.basic_errors(lines)
    status = "BASIC ERRORS ON SCREEN: " + " / ".join(errors) if errors else "No BASIC errors on screen."
    held = ""
    if emu.mon.held:
        held = (f"\nCPU STOPPED AT BREAKPOINT: {emu.mon.last_stop}\n{emu.registers()}\n"
                "(pet_peek / pet_registers / pet_step to inspect, pet_continue to go on)")
    return f"{text}\n{status}{held}"


def _hexdump(data, start):
    rows = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        ascii_ = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        rows.append(f"${start + i:04X}  " + " ".join(f"{b:02X}" for b in chunk).ljust(48) + "  " + ascii_)
    return "\n".join(rows)


def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TOOL_TIMEOUT)
    return r.returncode, (r.stdout + r.stderr).strip()


def _idle_watch():
    global _emu
    while True:
        time.sleep(30)
        with _lock:
            if _emu is not None and time.time() - _last_used > IDLE_SECONDS:
                _emu.stop()
                _emu = None


threading.Thread(target=_idle_watch, daemon=True).start()


# --- emulator tools --------------------------------------------------------

@mcp.tool()
def pet_reset(model: str = "4032", hz: int = 60, warp: bool = False) -> str:
    """Power-cycle the emulated PET and wait for READY.

    model: 4032 (default, BASIC 4.0, 40 columns), 2001, 4016, 8032 ...
    hz: 60 (North America, default) or 50 (Europe).
    warp: run as fast as possible (timing is then not realistic).
    """
    global _emu
    with _lock:
        _settings.update(model=model, hz=hz, warp=warp)
        if _emu is not None:
            _emu.stop()
            _emu = None
        return _report(_emulator(), "after reset")


@mcp.tool()
def pet_load(basic_source: str = "", prg_path: str = "", run: bool = True,
             wait_seconds: float = 2.0) -> str:
    """Load a program into the PET and (by default) RUN it.

    Give either basic_source (a BASIC 4.0 listing: UPPERCASE keywords and
    text as on the PET, control characters in braces such as {CLR}
    {HOME} {DOWN} {RVS ON}) or prg_path (a .PRG or .BAS file in the
    workspace). A program loading at $0401 is RUN when run is true;
    machine code elsewhere is only loaded (start it with pet_type("SYS n\\r")).
    Returns the load address and the screen after wait_seconds.
    """
    with _lock:
        if bool(basic_source) == bool(prg_path):
            return "Give exactly one of basic_source or prg_path."
        try:
            prg = basic.tokenize(basic_source) if basic_source else basic.tokenize_file(_path(prg_path, True))
        except basic.TokenizeError as e:
            return f"TOKENIZE FAILED: {e}"
        emu = _emulator()
        start, end = emu.load_prg(prg, run=run)
        emu.idle(min(max(wait_seconds, 0), MAX_WAIT))
        return f"Loaded ${start:04X}-${end - 1:04X} ({end - start} bytes).\n" + _report(emu)


@mcp.tool()
def pet_type(keys: str, wait_seconds: float = 1.0) -> str:
    """Type on the PET keyboard, then return the screen after wait_seconds.

    Letters are typed unshifted (they show as uppercase). Use \\r or {RETURN}
    for RETURN; other named keys: {CLR} {HOME} {UP} {DOWN} {LEFT} {RIGHT}
    {RVS ON} {RVS OFF} {DEL} {INST}, or {n} for PETSCII code n.
    Typing continues the CPU if it is stopped at a breakpoint. If a
    breakpoint hits while typing or waiting, the CPU stays stopped there.
    """
    with _lock:
        emu = _emulator()
        try:
            emu.type(keys)
        except EmulatorError as e:
            return str(e)
        emu.idle(min(max(wait_seconds, 0), MAX_WAIT))
        return _report(emu)


@mcp.tool()
def pet_wait(seconds: float) -> str:
    """Let the PET run for a while (max 120 s), then return the screen.
    Stops early if a breakpoint hits. Does not continue from a breakpoint;
    use pet_continue for that."""
    with _lock:
        emu = _emulator()
        emu.idle(min(max(seconds, 0), MAX_WAIT))
        return _report(emu)


@mcp.tool()
def pet_wait_for(pattern: str, timeout_seconds: float = 10.0) -> str:
    """Run until a screen line matches the regular expression pattern
    (e.g. "READY\\." or "SCORE"), or until the timeout (max 120 s)."""
    with _lock:
        emu = _emulator()
        found = emu.wait_for(pattern, min(max(timeout_seconds, 0), MAX_WAIT))
        return ("Found." if found else f"Not found within {timeout_seconds:g}s.") + "\n" + _report(emu)


@mcp.tool()
def pet_screen(include_image: bool = False):
    """The PET screen as text (graphics characters shown as a shaded block,
    reverse spaces as a solid block). With include_image, also a PNG."""
    with _lock:
        emu = _emulator()
        text = _report(emu)
        if not include_image:
            return text
        png = emu.screenshot(os.path.join(emu.work, f"screen-{int(time.time() * 1000)}.png"))
        return [text, Image(path=png)]


@mcp.tool()
def pet_peek(address: str, length: int = 16) -> str:
    """Hex dump of memory. address: $hex, 0xhex or decimal. length: 1-4096."""
    with _lock:
        start = parse_addr(address)
        length = max(1, min(length, 4096))
        end = min(start + length - 1, 0xFFFF)
        return _hexdump(_emulator().peek(start, end), start)


@mcp.tool()
def pet_poke(address: str, values: list[int]) -> str:
    """Write bytes (0-255) to memory starting at address."""
    with _lock:
        start = parse_addr(address)
        _emulator().poke(start, values)
        return f"Wrote {len(values)} byte(s) at ${start:04X}."


@mcp.tool()
def pet_registers() -> str:
    """CPU registers (PC, A, X, Y, SP, flags)."""
    with _lock:
        return _emulator().registers()


@mcp.tool()
def pet_break(address: str) -> str:
    """Stop the CPU when it executes the instruction at address. Then run
    the code and call pet_continue(wait_for_break_seconds=...) to wait for it."""
    with _lock:
        return _emulator().set_break(parse_addr(address))


@mcp.tool()
def pet_clear_breaks() -> str:
    """Delete all breakpoints."""
    with _lock:
        return _emulator().delete_breaks() or "Breakpoints deleted."


@mcp.tool()
def pet_continue(wait_for_break_seconds: float = 0.0) -> str:
    """Continue running (from a breakpoint if stopped). With
    wait_for_break_seconds > 0, wait that long for the next breakpoint and
    report where it stopped and the registers; the CPU then stays stopped.

    Note: pet_type, pet_load and pet_wait already report a breakpoint that
    hits while they run. Don't call pet_continue just to "see" that stop:
    it would continue past it."""
    with _lock:
        emu = _emulator()
        emu.mon.release()
        if wait_for_break_seconds <= 0:
            return "Running."
        if emu.wait_break(min(wait_for_break_seconds, MAX_WAIT)):
            return f"Stopped: {emu.mon.last_stop}\n{emu.registers()}"
        return f"No breakpoint hit within {wait_for_break_seconds:g}s; still running."


@mcp.tool()
def pet_step(count: int = 1) -> str:
    """Execute count instructions (1-100) one at a time and show them. The
    CPU stays stopped afterwards."""
    with _lock:
        return _emulator().step(max(1, min(count, 100)))


@mcp.tool()
def pet_disassemble(address: str, length: int = 32) -> str:
    """Disassemble memory starting at address (length in bytes, max 1024)."""
    with _lock:
        start = parse_addr(address)
        end = min(start + max(1, min(length, 1024)) - 1, 0xFFFF)
        return _emulator().disassemble(start, end)


@mcp.tool()
def pet_attach_drive(device: int, folder: str) -> str:
    """Make a workspace folder disk device 8-11 (files appear as PET files).
    Restarts the PET: memory and the running program are lost."""
    global _emu
    with _lock:
        if not 8 <= device <= 11:
            return "device must be 8-11"
        full = _path(folder)
        os.makedirs(full, exist_ok=True)
        _settings["drives"] = dict(_settings["drives"], **{device: full})
        if _emu is not None:
            _emu.stop()
            _emu = None
        return f"Device {device} is now {folder}.\n" + _report(_emulator(), "after restart")


# --- build tools -----------------------------------------------------------

@mcp.tool()
def basic_tokenize(source_path: str, out_path: str) -> str:
    """Tokenize a BASIC 4.0 listing (.BAS, UPPERCASE as on the PET) into a
    .PRG that loads at $0401. Use this for the final program you hand over."""
    try:
        data = basic.tokenize_file(_path(source_path, True), _path(out_path))
    except basic.TokenizeError as e:
        return f"TOKENIZE FAILED: {e}"
    return f"Wrote {out_path} ({len(data)} bytes)."


@mcp.tool()
def basic_list(prg_path: str) -> str:
    """List a BASIC .PRG as text (UPPERCASE, control codes in braces)."""
    with open(_path(prg_path, True), "rb") as f:
        return basic.detokenize(f.read())


@mcp.tool()
def asm_acme(source_path: str) -> str:
    """Assemble with ACME in the source file's folder. The source chooses
    the output file (!to "NAME.PRG", cbm). Also writes NAME.lst with
    addresses for breakpoints."""
    src = _path(source_path, True)
    folder = os.path.dirname(src)
    listing = os.path.splitext(src)[0] + ".lst"
    code, out = _run(["acme", "-r", listing, os.path.basename(src)], folder)
    return ("OK" if code == 0 else "FAILED") + (f"\n{out}" if out else "") + \
        (f"\nListing: {os.path.relpath(listing, WORKSPACE)}" if code == 0 else "")


@mcp.tool()
def c_compile(source_path: str, out_path: str) -> str:
    """Compile C for the PET with cc65 (cl65 -t pet -O). The PRG starts with
    a BASIC SYS line, so it runs with RUN."""
    src = _path(source_path, True)
    out = _path(out_path)
    code, msg = _run(["cl65", "-t", "pet", "-O", "-o", out, src], os.path.dirname(src))
    return ("OK" if code == 0 else "FAILED") + (f"\n{msg}" if msg else "")


# --- reference -------------------------------------------------------------

def _ref_files():
    return sorted(glob.glob(os.path.join(REF_DIR, "*.md")))


@mcp.tool()
def ref_list() -> str:
    """List the PET reference documents (verified facts for this machine)."""
    out = []
    for f in _ref_files():
        with open(f, encoding="utf-8") as h:
            title = h.readline().lstrip("# ").strip()
        out.append(f"{os.path.basename(f)}: {title}")
    return "\n".join(out)


@mcp.tool()
def ref_read(name: str) -> str:
    """Read one reference document, e.g. "basic4.md" or "memory-map.md"."""
    path = os.path.join(REF_DIR, os.path.basename(name))
    if not path.endswith(".md"):
        path += ".md"
    if not os.path.isfile(path):
        return "Not found. Available:\n" + ref_list()
    with open(path, encoding="utf-8") as f:
        return f.read()


@mcp.tool()
def ref_search(query: str) -> str:
    """Search the reference for a word, keyword, address ($E840) or phrase.
    Returns matching lines with their file and section."""
    rx = re.compile(re.escape(query), re.I)
    hits = []
    for f in _ref_files():
        section = ""
        with open(f, encoding="utf-8") as h:
            for line in h:
                if line.startswith("#"):
                    section = line.strip("# \n")
                if rx.search(line):
                    hits.append(f"{os.path.basename(f)} [{section}]: {line.strip()}")
    return "\n".join(hits[:60]) or "No matches."


@mcp.tool()
def rom_lookup(address: str, lines: int = 30) -> str:
    """Show the ROM disassembly (BASIC $B000-$DFFF, editor $E000-$E7FF,
    KERNAL $F000-$FFFF) starting at an address, to check what a ROM routine
    really does."""
    addr = parse_addr(address)
    label = f"L{addr:04X}"
    for f in sorted(glob.glob(os.path.join(ROMDIS_DIR, "*.dis"))):
        with open(f, encoding="utf-8", errors="replace") as h:
            text = h.read().splitlines()
        for i, line in enumerate(text):
            if line.startswith(label + ":") or line.startswith(label + " "):
                body = "\n".join(text[i:i + max(1, min(lines, 200))])
                return f"{os.path.basename(f)}:\n{body}"
    return (f"No label at ${addr:04X} (only addresses that are jump/branch targets have "
            "labels). Try a nearby routine start, or pet_disassemble.")


@mcp.resource("pet-ref://{name}")
def ref_resource(name: str) -> str:
    """A PET reference document."""
    return ref_read(name)


def _shutdown(*_):
    """Stop the emulator when the server ends (client disconnected, SIGTERM)."""
    global _emu
    if _emu is not None:
        try:
            _emu.stop()
        except Exception:
            pass
        _emu = None


def main():
    atexit.register(_shutdown)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    signal.signal(signal.SIGHUP, lambda *_: sys.exit(0))
    try:
        mcp.run()
    finally:
        _shutdown()


if __name__ == "__main__":
    main()
