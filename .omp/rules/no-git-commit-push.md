---
name: no-git-commit-push
description: "Never git commit or push unless the user explicitly asked"
condition: '\bgit\s+(commit|push)\b'
scope: "tool:bash"
---

Never `git commit` or `git push` unless the user explicitly asked for it in this conversation. Safety rule: no commits or pushes without explicit request. If the user did ask, proceed; otherwise stop and ask first.