---
name: no-rm-rf
description: "Never use rm -rf — use trash instead; destructive and irreversible"
condition: '\brm\s+(-rf|-fr|--recursive\s+--force|--force\s+--recursive)\b'
scope: "tool:bash"
---

Never use `rm -rf` (or `-fr`/`--recursive --force`) — destructive and irreversible. Use `trash` instead. cc-safety-net may block destructive commands anyway; if a genuine forced delete is required, ask the user explicitly first and confirm the exact path.