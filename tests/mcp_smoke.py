"""Smoke test for the PET MCP server: talk to it over stdio like any MCP
client and exercise every group of tools.

Run in the container:
  docker exec pet-lab /opt/petlab-venv/bin/python /opt/petlab/tests/mcp_smoke.py
It uses (and leaves behind) the folder mcptest/ in the workspace.
"""
import asyncio
import os
import subprocess
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

WORK = "/workspace/mcptest"

ASM = """!cpu 6502
!to "COUNT.PRG", cbm
* = $7000
start:  lda #1
        sta $8000
        ldx #0
loop:   inx
        stx $7100
        cpx #$10
        bne loop
mark:   nop
        rts
"""

failures = 0


def check(name, ok, detail=""):
    global failures
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"\n{detail}"))
    if not ok:
        failures += 1


def text_of(result):
    return "\n".join(c.text for c in result.content if getattr(c, "type", "") == "text")


async def main():
    os.makedirs(WORK, exist_ok=True)
    with open(f"{WORK}/count.a", "w") as f:
        f.write(ASM)
    with open(f"{WORK}/HELLO.BAS", "w") as f:
        f.write('10 PRINT "{CLR}HELLO FROM PET LAB"\n20 GOTO 10\n')

    params = StdioServerParameters(command="pet-mcp", env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = {t.name for t in (await s.list_tools()).tools}
            print("tools:", ", ".join(sorted(tools)))
            check("all tools listed", {"pet_reset", "pet_load", "pet_type", "pet_screen", "pet_peek",
                                       "pet_break", "pet_continue", "asm_acme", "ref_search",
                                       "rom_lookup"} <= tools)

            async def call(name, **args):
                return await s.call_tool(name, args)

            r = text_of(await call("pet_reset"))
            check("reset shows BASIC 4", "COMMODORE BASIC 4.0" in r, r)

            src = '10 PRINT "{CLR}WHAT IS YOUR NAME";\n20 INPUT N$\n30 PRINT "HI ";N$\n'
            r = text_of(await call("pet_load", basic_source=src, wait_seconds=2))
            check("load + run BASIC", "WHAT IS YOUR NAME?" in r, r)

            r = text_of(await call("pet_type", keys="ADA{RETURN}", wait_seconds=1))
            check("type keys", "HI ADA" in r and "No BASIC errors" in r, r)

            # state persists between calls: the program is still in memory
            r = text_of(await call("pet_type", keys="LIST\r", wait_seconds=1))
            check("emulator persists (LIST shows program)", "20 INPUT N$" in r, r)

            r = text_of(await call("pet_load", basic_source="10 PRINT 1/0\n", wait_seconds=1))
            check("BASIC error reported", "BASIC ERRORS ON SCREEN" in r and "DIVISION BY ZERO" in r, r)

            r = await call("pet_screen", include_image=True)
            kinds = [c.type for c in r.content]
            check("screen image returned", "image" in kinds, kinds)

            r = text_of(await call("asm_acme", source_path="mcptest/count.a"))
            check("acme assembles", r.startswith("OK"), r)

            r = text_of(await call("pet_load", prg_path="mcptest/COUNT.PRG", run=False, wait_seconds=0))
            check("ML loaded at $7000", "$7000" in r, r)

            r = text_of(await call("pet_break", address="$700f"))
            check("breakpoint set", "700f" in r.lower(), r)

            r = text_of(await call("pet_type", keys="SYS 28672\r", wait_seconds=3))
            check("breakpoint hit with X=$10 (reported by pet_type)",
                  "STOPPED AT BREAKPOINT" in r and "700f" in r and " 10 " in r, r)

            r = text_of(await call("pet_peek", address="$7100", length=1))
            check("peek while stopped", "$7100  10" in r, r)

            r = text_of(await call("pet_step", count=2))
            check("single step", "NOP" in r.upper() or "RTS" in r.upper(), r)

            r = text_of(await call("pet_disassemble", address="$7000", length=16))
            check("disassemble", "STA $8000" in r.upper(), r)

            # continue to the next hit: run the routine again
            r = text_of(await call("pet_continue"))
            r = text_of(await call("pet_wait_for", pattern=r"^READY\.", timeout_seconds=5))
            await call("pet_type", keys="SYS 28672\r", wait_seconds=0)
            r = text_of(await call("pet_registers"))
            r2 = text_of(await call("pet_screen"))
            check("second run stops again", "STOPPED AT BREAKPOINT" in r2, r2)

            await call("pet_clear_breaks")
            r = text_of(await call("pet_continue"))
            r = text_of(await call("pet_wait_for", pattern=r"^READY\.", timeout_seconds=5))
            check("continue back to READY", r.startswith("Found"), r)

            r = text_of(await call("pet_poke", address="$8000", values=[8, 9]))
            r = text_of(await call("pet_peek", address="32768", length=2))
            check("poke + peek", "08 09" in r, r)

            r = text_of(await call("ref_search", query="SETLFS"))
            check("reference search", "kernal.md" in r, r)

            r = text_of(await call("rom_lookup", address="$E442"))
            check("ROM lookup of IRQ entry", "pha" in r and "($0090)" in r.replace("L0090", "$0090"), r)

            r = text_of(await call("basic_tokenize", source_path="mcptest/HELLO.BAS", out_path="mcptest/HELLO.PRG"))
            r2 = text_of(await call("basic_list", prg_path="mcptest/HELLO.PRG"))
            check("tokenize + list round trip", "HELLO FROM PET LAB" in r2, r + "\n" + r2)

            r = text_of(await call("basic_list", prg_path="../etc/passwd"))
            check("workspace confinement", "workspace" in r.lower() or "error" in r.lower(), r)

    return failures


def xpet_count():
    out = subprocess.run(["ps", "-eo", "comm"], capture_output=True, text=True).stdout
    return sum(1 for line in out.splitlines() if line.strip() == "xpet")


def leak_checks(baseline):
    """No emulator may outlive the process that started it."""
    time.sleep(3)
    check("no emulator left after the client disconnects", xpet_count() == baseline,
          f"{xpet_count()} xpet running, expected {baseline}")

    # a server killed with SIGKILL can't clean up; the watchdog must
    code = ("import sys,time; sys.path.insert(0,'/opt/petlab'); "
            "from petlab.vice import Emulator, find_free_port; "
            "Emulator(port=find_free_port()).start(); time.sleep(120)")
    p = subprocess.Popen(["/opt/petlab-venv/bin/python", "-c", code])
    for _ in range(60):
        if xpet_count() > baseline:
            break
        time.sleep(0.5)
    time.sleep(3)   # let it boot
    p.kill()
    p.wait()
    time.sleep(5)   # the watchdog checks every 2 s
    check("no emulator left after kill -9 of its owner", xpet_count() == baseline,
          f"{xpet_count()} xpet running, expected {baseline}")


baseline = xpet_count()
asyncio.run(main())
leak_checks(baseline)
print(f"\n{'ALL PASSED' if failures == 0 else f'{failures} FAILED'}")
sys.exit(1 if failures else 0)
