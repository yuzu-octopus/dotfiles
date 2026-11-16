---
name: no-rm-rf
description: "Never use rm -rf — use trash instead; destructive and irreversible"
condition: '\brm\b(?=(?:(?!--)[^\n;|&])*\s-[A-Za-z]*[rR][A-Za-z]*)(?=(?:(?!--)[^\n;|&])*\s-[A-Za-z]*[fF][A-Za-z]*)|\brm\b[^\n;|&]*--recursive[^\n;|&]*--force|\brm\b[^\n;|&]*--force[^\n;|&]*--recursive'
scope: "tool:bash"
---

Never use `rm -rf` (or `-fr`/`--recursive --force`) — destructive and irreversible. Use `trash` instead. cc-safety-net may block destructive commands anyway; if a genuine forced delete is required, ask the user explicitly first and confirm the exact path.