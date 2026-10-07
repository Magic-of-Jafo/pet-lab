"""Tokenize and list Commodore BASIC 4.0 programs with VICE's petcat."""
import os
import re
import subprocess
import tempfile


class TokenizeError(Exception):
    pass


def swap_case(text):
    """Listings are written as they look on the PET (UPPERCASE). petcat wants
    lowercase for unshifted letters, so swap case outside {control} codes."""
    return re.sub(r"(\{[^}]*\})|([^{]+)",
                  lambda m: m.group(1) or m.group(2).swapcase(), text)


def tokenize(source):
    """BASIC source text (UPPERCASE, {controls} in braces) -> PRG bytes at $0401."""
    with tempfile.TemporaryDirectory(prefix="petcat-") as work:
        txt = os.path.join(work, "src.txt")
        out = os.path.join(work, "prog.prg")
        with open(txt, "w", encoding="ascii", errors="replace") as f:
            f.write(swap_case(source))
        r = subprocess.run(["petcat", "-w40", "-l", "0401", "-ic", "-o", out, "--", txt],
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out) or r.stderr.strip():
            raise TokenizeError((r.stdout + r.stderr).strip() or "petcat failed")
        with open(out, "rb") as f:
            return f.read()


def tokenize_file(path, out_path=None):
    """Tokenize a .BAS file; .PRG files are returned as they are."""
    if path.lower().endswith(".prg"):
        with open(path, "rb") as f:
            data = f.read()
    else:
        with open(path, encoding="ascii", errors="replace") as f:
            data = tokenize(f.read())
    if out_path:
        with open(out_path, "wb") as f:
            f.write(data)
    return data


def detokenize(prg):
    """PRG bytes -> BASIC listing text, UPPERCASE with {controls}."""
    with tempfile.TemporaryDirectory(prefix="petcat-") as work:
        src = os.path.join(work, "prog.prg")
        out = os.path.join(work, "list.txt")
        with open(src, "wb") as f:
            f.write(prg)
        r = subprocess.run(["petcat", "-40", "-o", out, "--", src], capture_output=True, text=True)
        if not os.path.exists(out):
            raise TokenizeError((r.stdout + r.stderr).strip() or "petcat failed")
        with open(out, encoding="ascii", errors="replace") as f:
            return swap_case(f.read())
