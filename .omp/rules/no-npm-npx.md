---
name: no-npm-npx
description: "Never use npm or npx — use bun / bunx instead"
condition: '\b(npm|npx)\b'
scope: "tool:bash"
---

Never use `npm` / `npx`. Use `bun` / `bunx` instead (`bun run`, `bunx`). Same job, faster, no global state. The Node package managers are banned outright — if there is a genuine reason to reach for npm, ask the user first.