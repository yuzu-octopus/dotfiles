---
name: no-bash-grep
description: "Never run BSD grep in bash — use rg or the OMP grep tool (same ripgrep engine, structured output)"
condition: "\b(egrep|fgrep|zgrep|grep)\b"
scope: "tool:bash"
---

Never run BSD `grep` in bash (`/usr/bin/grep` on macOS is 2.6.0-FreeBSD: slower, no `-P`, weaker recursion). Use `rg` (ripgrep 15.x) or the OMP `grep` tool instead — same Rust engine. Prefer the `grep` tool for plain searches (structured matches, edit anchors, archive/internal-URL search); reach for CLI `rg` for power flags the tool lacks (`-C`, `-l`/`-c`, `-g`/`-t`, `-w`/`-F`/`-v`, `--multiline`, `--hidden`).
