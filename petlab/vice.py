"""Run a headless VICE xpet and control it through VICE's remote text monitor."""
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import tempfile
import time

from . import screen as scr

PROMPT_RE = re.compile(rb"\(C:\$[0-9a-f]{4}\) $")
PROMPT_ANY_RE = re.compile(rb"\(C:\$[0-9a-f]{4}\) ")

# BASIC 4.0 keyboard buffer [EMU]
KEYBUF, KEYCOUNT, KEYBUF_LEN = 0x026F, 0x9E, 10
# BASIC 4.0 end-of-program pointers VARTAB/ARYTAB/STREND [EMU]
BASIC_END_POINTERS = (0x2A, 0x2C, 0x2E)
SCREEN = 0x8000

EDITOR_ROMS = {
    ("4032", 60): "edit-4-40-n-60Hz.901499-01.bin",
    ("4032", 50): "edit-4-40-n-50Hz.901498-01.bin",
}

# Named keys for type(): {RETURN}, {CLR}, ...
KEY_NAMES = {
    "RETURN": 13, "CR": 13, "CLR": 147, "HOME": 19, "UP": 145, "DOWN": 17,
    "LEFT": 157, "RIGHT": 29, "RVS": 18, "RVS ON": 18, "RVS OFF": 146, "OFF": 146,
    "DEL": 20, "INST": 148, "SPACE": 32,
}


class EmulatorError(Exception):
    pass


def parse_addr(value):
    """'$7000', '0x7000', '28672' or an int -> int."""
    if isinstance(value, int):
        return value
    t = str(value).strip().lower()
    if t.startswith("$"):
        return int(t[1:], 16)
    if t.startswith("0x"):
        return int(t[2:], 16)
    return int(t)


def keys_to_petscii(text):
    """Text with {NAMED} keys and \\r for RETURN -> PETSCII codes."""
    codes = []
    for m in re.finditer(r"\{([^}]*)\}|(\\r|\\n|\r|\n)|(.)", text, re.S):
        name, newline, ch = m.groups()
        if name is not None:
            n = name.strip().upper()
            if n.isdigit():
                codes.append(int(n) & 0xFF)
            elif n in KEY_NAMES:
                codes.append(KEY_NAMES[n])
            else:
                raise EmulatorError(f"unknown key {{{name}}}; use one of {sorted(KEY_NAMES)} or {{n}}")
        elif newline is not None:
            codes.append(13)
        else:
            codes.append(ord(ch.upper()) & 0xFF)
    return codes


class Monitor:
    """VICE remote text monitor.

    Tracks whether the emulator is stopped in the monitor. Entering the
    monitor from a running emulator prints an extra prompt before the output
    of the command; a breakpoint that hits while nobody is talking to the
    monitor prints its stop message and a prompt on its own.
    """

    def __init__(self, port, timeout=20):
        self.active = False      # emulator stopped in the monitor
        self.held = False        # stopped at a breakpoint: stay stopped until released
        self.last_stop = ""      # message from the last breakpoint hit
        deadline = time.time() + timeout
        while True:
            try:
                self.s = socket.create_connection(("127.0.0.1", port), timeout=10)
                break
            except OSError:
                if time.time() > deadline:
                    raise
                time.sleep(0.25)

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass

    def poll(self, wait=0.05):
        """Read anything the monitor sent on its own. A prompt means the
        emulator stopped at a breakpoint."""
        self.s.settimeout(wait)
        buf = b""
        try:
            while True:
                chunk = self.s.recv(65536)
                if not chunk:
                    break
                buf += chunk
        except (socket.timeout, BlockingIOError):
            pass
        finally:
            self.s.settimeout(10)
        if buf and not self.active and PROMPT_RE.search(buf):
            self.active = True
            self.held = True
            self.last_stop = clean(buf.decode(errors="replace"))
        return buf

    def cmd(self, line):
        """Send a monitor command (this stops the emulator) and return its output."""
        self.poll()
        prompts = 1 if self.active else 2
        self.active = True
        self.s.sendall(line.encode() + b"\n")
        buf = b""
        while len(PROMPT_ANY_RE.findall(buf)) < prompts or not PROMPT_RE.search(buf):
            chunk = self.s.recv(65536)
            if not chunk:
                break
            buf += chunk
        return buf.decode(errors="replace")

    def resume(self):
        """Let the emulator run again, unless it is held at a breakpoint."""
        if self.active and not self.held:
            self.s.sendall(b"x\n")
            self.active = False

    def release(self):
        """Continue after a breakpoint."""
        self.held = False
        self.resume()

    def wait_stop(self, seconds):
        """Wait up to `seconds` for a breakpoint. True if the CPU stopped."""
        if self.active:
            return True
        deadline = time.time() + seconds
        while time.time() < deadline:
            self.poll(wait=min(0.25, max(0.01, deadline - time.time())))
            if self.active:
                return True
        return False


def clean(out):
    """Monitor output without prompts and blank lines."""
    text = PROMPT_ANY_RE.sub(b"", out.encode()).decode()
    return "\n".join(ln for ln in text.splitlines() if ln.strip())


class Emulator:
    """A headless PET running in VICE xpet."""

    def __init__(self, model="4032", hz=60, warp=False, drives=None, port=6510, workdir=None):
        self.model = model
        self.hz = hz
        self.warp = warp
        self.drives = dict(drives or {})
        self.port = port
        self.cols = 80 if model.startswith("8") else 40
        self.work = workdir or tempfile.mkdtemp(prefix="petlab-")
        self.proc = None
        self.mon = None
        self.log_path = os.path.join(self.work, "xpet.log")

    # --- lifecycle ---------------------------------------------------------

    def command_line(self):
        cmd = ["xpet", "-default", "-model", self.model]
        if (self.model, self.hz) in EDITOR_ROMS:
            cmd += ["-editor", EDITOR_ROMS[(self.model, self.hz)]]
        cmd += ["-remotemonitor", "-remotemonitoraddress", f"ip4://127.0.0.1:{self.port}",
                "-sounddev", "dummy"]
        for dev, folder in sorted(self.drives.items()):
            cmd += [f"-virtualdev{dev}", f"-device{dev}", "1", f"-fs{dev}", os.path.abspath(folder)]
        if self.warp:
            cmd.append("-warp")
        return cmd

    def start(self, boot_timeout=20):
        self.stop()
        log = open(self.log_path, "w")
        # Run xpet under a small shell watchdog that ends it if this Python
        # process goes away for any reason (client disconnect, crash, kill -9),
        # so emulators are never left running on their own.
        watchdog = (f"{shlex.join(self.command_line())} & XP=$!; "
                    f'trap "kill $XP 2>/dev/null" TERM INT HUP; '
                    f"while kill -0 {os.getpid()} 2>/dev/null && kill -0 $XP 2>/dev/null; do sleep 2; done; "
                    f"kill $XP 2>/dev/null; wait $XP")
        self.proc = subprocess.Popen(["sh", "-c", watchdog], stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
        try:
            self.mon = Monitor(self.port)
        except OSError:
            raise EmulatorError("emulator failed to start:\n" + self.log_tail())
        if not self.wait_for(r"^READY\.", boot_timeout):
            raise EmulatorError("PET did not reach READY.\n" + self.log_tail())
        return self

    def stop(self):
        if self.mon:
            try:
                self.mon.held = False
                self.mon.cmd("quit")
            except OSError:
                pass
            self.mon.close()
            self.mon = None
        if self.proc:
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # stop the watchdog and xpet together (own process group)
                for sig in (signal.SIGTERM, signal.SIGKILL):
                    try:
                        os.killpg(self.proc.pid, sig)
                        self.proc.wait(timeout=3)
                        break
                    except (ProcessLookupError, subprocess.TimeoutExpired):
                        continue
            self.proc = None

    def alive(self):
        return self.proc is not None and self.proc.poll() is None and self.mon is not None

    def log_tail(self, n=3000):
        try:
            with open(self.log_path) as f:
                return f.read()[-n:]
        except OSError:
            return ""

    # --- state -------------------------------------------------------------

    @property
    def stopped(self):
        """True if the CPU is held at a breakpoint."""
        self.mon.poll()
        return self.mon.held

    def idle(self, seconds):
        """Let time pass while the PET runs. If a breakpoint hits, stop
        waiting and stay stopped. Returns True if stopped at a breakpoint."""
        if self.mon.active and not self.mon.held:
            self.mon.resume()
        return self.mon.wait_stop(seconds) if seconds > 0 else self.stopped

    def run(self, seconds):
        """Continue from a breakpoint if held, then let the PET run."""
        self.mon.release()
        return self.idle(seconds)

    # --- memory ------------------------------------------------------------

    def peek(self, start, end=None):
        """Bytes start..end inclusive."""
        end = start if end is None else end
        if not 0 <= start <= end <= 0xFFFF:
            raise EmulatorError("address out of range")
        path = os.path.join(self.work, "dump.bin")
        if os.path.exists(path):
            os.remove(path)
        self.mon.cmd(f'save "{path}" 0 {start:04x} {end:04x}')
        for _ in range(60):
            if os.path.exists(path) and os.path.getsize(path) >= end - start + 3:
                break
            time.sleep(0.05)
        with open(path, "rb") as f:
            data = f.read()[2:]  # strip load address
        self.mon.resume()
        return data

    def poke(self, start, values):
        if not values:
            return
        if start < 0 or start + len(values) - 1 > 0xFFFF:
            raise EmulatorError("address out of range")
        for i in range(0, len(values), 32):
            chunk = values[i:i + 32]
            self.mon.cmd("> %04x %s" % (start + i, " ".join("%02x" % (v & 0xFF) for v in chunk)))
        self.mon.resume()

    def load_bytes(self, prg):
        """Put PRG bytes (2-byte load address first) into memory. Returns (start, end)."""
        start = prg[0] | prg[1] << 8
        end = start + len(prg) - 2
        path = os.path.join(self.work, "load.prg")
        with open(path, "wb") as f:
            f.write(prg)
        self.mon.cmd(f'load "{path}" 0')
        self.mon.resume()
        return start, end

    def load_prg(self, prg, run=True):
        """Load a PRG. A BASIC program at $0401 gets its pointers set and is
        RUN (if run); machine code elsewhere is only loaded."""
        start, end = self.load_bytes(prg)
        if start == 0x0401:
            for zp in BASIC_END_POINTERS:
                self.poke(zp, [end & 0xFF, end >> 8])
            if run:
                self.type_codes(keys_to_petscii("RUN\r"))
        return start, end

    # --- keyboard and screen ---------------------------------------------

    def type_codes(self, codes):
        """Feed PETSCII codes through the PET's keyboard buffer."""
        self.mon.release()
        for i in range(0, len(codes), KEYBUF_LEN - 1):
            chunk = codes[i:i + KEYBUF_LEN - 1]
            for _ in range(200):    # wait for the PET to empty the buffer
                if self.peek(KEYCOUNT)[0] == 0:
                    break
                if self.mon.held:   # a breakpoint hit while typing: stop here
                    return False
                time.sleep(0.05)
            self.mon.cmd("> %04x %s" % (KEYBUF, " ".join("%02x" % c for c in chunk)))
            self.mon.cmd("> %04x %02x" % (KEYCOUNT, len(chunk)))
            self.mon.resume()
            if self.mon.wait_stop(0.1):
                return False
        return True

    def type(self, text):
        """Type text; False if a breakpoint stopped the CPU before all of it was typed."""
        return self.type_codes(keys_to_petscii(text))

    def screen_lines(self):
        return scr.screen_lines(self.peek(SCREEN, SCREEN + self.cols * 25 - 1), self.cols)

    def screen_text(self, label=""):
        return scr.framed(self.screen_lines(), self.cols, label)

    def wait_for(self, pattern, timeout):
        """Run until a line on screen matches the regex pattern."""
        rx = re.compile(pattern)
        deadline = time.time() + timeout
        while True:
            if self.mon.active and not self.mon.held:
                self.mon.resume()
            if any(rx.search(ln) for ln in self.screen_lines()):
                return True
            if time.time() > deadline:
                return False
            time.sleep(0.25)

    def screenshot(self, path):
        path = os.path.abspath(path)
        if os.path.exists(path):
            os.remove(path)
        self.mon.cmd(f'screenshot "{path}" 2')
        for _ in range(60):
            if os.path.exists(path) and os.path.getsize(path) > 0:
                break
            time.sleep(0.05)
        self.mon.resume()
        return path

    # --- debugging ---------------------------------------------------------

    def monitor(self, command):
        out = clean(self.mon.cmd(command))
        self.mon.resume()
        return out

    def registers(self):
        return self.monitor("r")

    def disassemble(self, start, end):
        return self.monitor(f"d {start:04x} {end:04x}")

    def set_break(self, addr):
        return self.monitor(f"break exec {addr:04x}")

    def delete_breaks(self):
        return self.monitor("del")

    def wait_break(self, seconds):
        """Wait for a breakpoint; True if hit (the CPU then stays stopped)."""
        return self.mon.wait_stop(seconds)

    def step(self, count=1):
        """Single-step `count` instructions (stops the CPU). Returns one line
        per instruction executed: address, bytes, instruction, registers."""
        lines = []
        for _ in range(count):
            out = clean(self.mon.cmd("z"))
            self.mon.held = True
            lines += [ln for ln in out.splitlines() if ln.startswith(".C:")]
        return "\n".join(lines)


def find_free_port(preferred=6510):
    for port in range(preferred, preferred + 50):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise EmulatorError("no free port for the VICE monitor")


def have_vice():
    return shutil.which("xpet") is not None
