---
name: no-brew-install
description: "Never run brew install — system-wide installs need explicit user permission; prefer ephemeral or project-scoped tooling"
condition: '\bbrew\s+(install|i)\b'
scope: "tool:bash"
---

Never install system-wide packages via `brew install` (or `brew i`) without explicit user permission. Prefer project-scoped or ephemeral alternatives (`bunx`, `uvx`, `uv run --with`). If a brew install is truly required, ask the user first — it mutates the system Python/Node/other toolchains and is hard to undo cleanly.