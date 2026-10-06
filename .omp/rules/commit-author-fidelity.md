---
name: commit-author-fidelity
description: "Never hand-pass `user.name`/`user.email` to `git commit`; commit as the configured identity so no tool/agent gets co-attributed as a contributor"
condition: "git[^\\n]*-c\\s+user\\.(name|email)|\\-c\\s+user\\.(name|email)|user\\.name=|user\\.email="
scope: "tool"
---

Run a plain `git commit -m "…"` and let the repo's configured identity apply. Do NOT pass `-c user.name=…` or `-c user.email=…` (or `--author=…`, or any `--author`/`GIT_AUTHOR_*` override) when the identity is already correct in config or environment — that is how a co-author/trailer from a different tool gets attributed as a GitHub contributor on commits you authored yourself.

Why it matters: the identity you override *to* is not the only identity that lands. Trailers such as `Co-Authored-By:` and tooling-injected authorship make GitHub count someone as a contributor on every commit. Once attributed, contributor graphs and repo analytics keep the record; you then have to strip it manually per repo.

How to keep identity correct without per-command overrides:
- Set it once, at the repo or globally, not on every commit: `git config user.name "…"` and `git config user.email "…"` (add `--global` only if you want it everywhere).
- Keep commit commands minimal: `git commit -m "subject"` — the message plus nothing else.
- If a commit message template inserts a `Co-Authored-By:` trailer, delete that trailer from the message before committing.

Before pushing, if you did use an override, check `git log -1 --format='%an <%ae>%n%(trailers)'` and fix the offending commit (`git rebase`/`git filter-repo` for history, then force-push only when the user explicitly asks).

Removing an already-attributed contributor (GitHub UI): the repo owner's **Settings → Collaborators / Collaborate** is not it — contributor attribution comes from commit email matching. The reliable fixes are:
- **Rewrite the offending commit(s)** so no commit matches the tool's verified/noreply email: `git rebase -i` to reword, or `git filter-repo --commit-callback 'c.message = re.sub(r"Co-Authored-By:.*", "", c.message)'` (and for a rewritten author, `--mailmap` or a callback setting `c.author_name`/`c.author_email`).
- Force-push rewritten history: `git push --force-with-lease` (never plain `--force`).
- After the rewrite, GitHub recomputes contributors on the next push; the mapping is applied through `.mailmap` for *name* differences, but contributor *counts* only change when the commit email no longer matches a linked account.
- Deleting and recreating the repository is the blunt fallback: contributors are recomputed from history, so a fresh push of cleaned history removes the attribution entirely.

Do the identity fix, not a per-commit workaround.