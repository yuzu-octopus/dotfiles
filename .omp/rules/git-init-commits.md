---
name: git-init-commits
description: "New code projects start with git init; commits stay atomic with conventional messages"
condition: "\\bgit\\s+(init|commit)\\b"
scope: "tool:bash"
---

New code project only (not dotfiles, not edits inside an existing repo): `git init` first, `.gitignore` before the first commit. One change set = one atomic commit, conventional message (`feat:`, `fix:`, `chore:`, `docs:`). Permission stays with `no-git-commit-push`: never commit or push unless explicitly asked — this rule shapes the commit, never authorizes it.