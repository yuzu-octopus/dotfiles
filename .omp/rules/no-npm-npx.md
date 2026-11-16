---
name: no-npm-npx
description: "Never use npm or npx — use bun / bunx instead"
condition: '(?:^|[;&|]+\s*|"(?:command|code)"\s*:\s*"?)(?:[A-Za-z_][A-Za-z0-9_]*=[^\s;&|]+\s+|sudo\s+|env\s+|command\s+|time\s+|nohup\s+|bash\s+-c\s+(?:\\?["''])?|sh\s+-c\s+(?:\\?["''])?|xargs\s+)?\b(npm|npx)\b(?=\s|$)'
scope: "tool:bash"
---

Never use `npm` / `npx`. Use `bun` / `bunx` instead (`bun run`, `bunx`). Same job, faster, no global state. The Node package managers are banned outright — if there is a genuine reason to reach for npm, ask the user first.
