---
name: no-curl-pipe-sh
description: "Never curl | sh — system-wide installs need explicit user permission"
condition: '(?:\b(?:curl|wget)\b[^;]*\|(?:[^\n;|]*\|)?\s*(?:sudo\s+)?(?:[\w./-]+\/)?(?:ba)?sh\b|\b(?:(ba)?sh)\s+-c\b[^\n;]*\b(?:curl|wget)\b)'
scope: "tool:bash"
---

Never pipe `curl` into `sh`/`bash` (e.g. `curl https://… | sh` or with `sudo`). That installs system-wide without explicit user permission. Prefer project-scoped or ephemeral installs (`bunx`, `uvx`, `uv run --with`, `brew install` only with explicit approval). Remote-pipe-to-shell is a supply-chain risk and a permission violation; stop and ask first.