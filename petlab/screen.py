"""PET screen memory -> text."""
import re

ERROR_RE = re.compile(r"\?.*ERROR")


def screen_char(code):
    """Screen code -> a printable character (graphics mode character set)."""
    rev, c = code & 0x80, code & 0x7F
    if c < 0x20:
        ch = {0x1E: "^", 0x1F: "_"}.get(c, chr(0x40 + c))
    elif c < 0x40:
        ch = chr(c)
    elif c == 0x60:
        ch = " "
    else:
        ch = "▒"  # PET graphics character
    if rev and ch == " ":
        ch = "█"
    return ch


def screen_lines(data, cols):
    return ["".join(screen_char(b) for b in data[r * cols:(r + 1) * cols]).rstrip() for r in range(25)]


def framed(lines, cols, label=""):
    rows = [f"+{'-' * cols}+ {label}".rstrip()]
    rows += [f"|{ln.ljust(cols)}|" for ln in lines]
    rows.append(f"+{'-' * cols}+")
    return "\n".join(rows)


def basic_errors(lines):
    return [ln.strip() for ln in lines if ERROR_RE.search(ln)]
