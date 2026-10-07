# From Pet Lab to a real PET

Pet Lab produces ordinary Commodore `.PRG` files. Anything that can put a
file in front of a PET works.

## Ways to move a program

| Device | How |
|---|---|
| **PETdisk MAX** | Copy the `.PRG` to its SD card, or to the folder its network drive serves, then `LOAD"NAME",8` or `,9` |
| **SD2PET, petSD+, other SD drives** | Copy the `.PRG` to the SD card |
| **A real disk drive** | Put the `.PRG` into a `.D64` disk image with VICE's `c1541` (included in the image) and write it to a disk with your usual tools |

Example with `c1541`:

```bash
docker exec pet-lab sh -c 'cd /workspace/programs && c1541 -format "pet lab,01" d64 games.d64 -write BOUNCE.PRG bounce'
```

## The PETdisk MAX network drive

The PETdisk MAX can serve a folder on a web server as a disk drive. Point
it at a folder Pet Lab writes into, and new programs show up on the PET
straight away: the agent finishes, you type `LOAD"GAME",9`.

The upstream PETdisk MAX firmware has bugs in its network drive code (lost
saves, buffer overruns, drives interfering with each other) and its server
script lets requests read and write files outside its folder. Fixing these
is the hardware half of Pet Lab: corrected firmware, subfolders on network
drives, a hardened server script and a PET test program. The work is
being tested on real hardware and will be folded into this project once it
passes; until then it lives on the `fixes` branch of a petdisk-max fork.

## Talking to an AI from the PET

The plan:

1. **Mailbox mode** (works with stock PETdisk firmware): a PET program
   saves your message to the network drive, a bridge service passes it to
   a model, and the PET reads the reply.
2. **Agent channel** (new firmware): send with `PRINT#`, check progress on
   the command channel, read the reply with `GET#`.
3. **Pet Lab MCP tools** to publish programs to the real PET and to read
   and answer messages typed on it.

The bridge is model-agnostic: local models (Ollama, LM Studio), Claude or
OpenAI, an n8n webhook, or Pet Lab's own Claude Code agent for vibe coding
from the PET keyboard.
