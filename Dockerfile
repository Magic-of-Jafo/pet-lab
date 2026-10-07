# Pet Lab: a Commodore PET 4032 development lab for AI agents.
#
# VICE xpet (headless), petcat, the ACME / cc65 / xa65 toolchains, the PET MCP
# server, petrun, a verified machine reference, and the Claude Code CLI.
FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive

# VICE lives in contrib on Debian. dbus-x11 satisfies GTK's session-bus
# dependency so apt doesn't pull in systemd, whose postinst fails on some
# Docker hosts (e.g. Synology: "Failed to take /etc/passwd lock").
RUN sed -i 's/^Components: main$/Components: main contrib non-free/' /etc/apt/sources.list.d/debian.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      vice dbus-x11 xvfb xauth \
      python3 python3-venv nodejs npm \
      cc65 acme xa65 \
      git curl ca-certificates procps less nano tini \
 && rm -rf /var/lib/apt/lists/*

# Debian's vice package has the Commodore ROMs removed (+dfsg). Take the PET
# ROMs from the matching official VICE source release.
ARG VICE_VERSION=3.9
RUN curl -fsSL -o /tmp/vice.tgz "https://sourceforge.net/projects/vice-emu/files/releases/vice-${VICE_VERSION}.tar.gz/download" \
 && tar -xzf /tmp/vice.tgz -C /tmp "vice-${VICE_VERSION}/data/PET" \
 && mkdir -p /usr/share/vice/PET \
 && cp -r --update=none /tmp/vice-${VICE_VERSION}/data/PET/. /usr/share/vice/PET/ \
 && rm -rf /tmp/vice.tgz /tmp/vice-${VICE_VERSION}

# Disassemble the BASIC 4, editor and KERNAL ROMs, so agents can check what a
# ROM routine really does (rom_lookup tool, /opt/pet-rom).
RUN mkdir -p /opt/pet-rom \
 && cd /usr/share/vice/PET \
 && da65 --cpu 6502 --start-addr 0xB000 basic-4.901465-23-20-21.bin > /opt/pet-rom/basic4-b000.dis \
 && da65 --cpu 6502 --start-addr 0xE000 edit-4-40-n-60Hz.901499-01.bin > /opt/pet-rom/edit4-40n-60hz-e000.dis \
 && da65 --cpu 6502 --start-addr 0xF000 kernal-4.901465-22.bin > /opt/pet-rom/kernal4-f000.dis

# Python environment for the PET MCP server (official MCP Python SDK).
RUN python3 -m venv /opt/petlab-venv \
 && /opt/petlab-venv/bin/pip install --no-cache-dir "mcp>=1.2,<2"

# Claude Code, for running an agent inside the lab. Optional: the MCP server
# and petrun work without it.
RUN npm install -g @anthropic-ai/claude-code && npm cache clean --force

# Run as a normal user. Set PETLAB_UID / PETLAB_GID (see compose.yaml) to
# match the owner of your workspace folder.
ARG PETLAB_UID=1000
ARG PETLAB_GID=1000
RUN (getent group ${PETLAB_GID} >/dev/null || groupadd -g ${PETLAB_GID} pet) \
 && useradd -u ${PETLAB_UID} -g ${PETLAB_GID} -m -d /home/pet -s /bin/bash pet \
 && mkdir -p /workspace && chown ${PETLAB_UID}:${PETLAB_GID} /workspace

COPY petlab /opt/petlab/petlab
COPY tests /opt/petlab/tests
COPY pet-ref /opt/pet-ref
COPY bin/entrypoint.sh bin/petrun bin/pet-mcp /usr/local/bin/
RUN chmod 755 /usr/local/bin/entrypoint.sh /usr/local/bin/petrun /usr/local/bin/pet-mcp

ENV DISPLAY=:99
USER pet
WORKDIR /workspace

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["sleep", "infinity"]
