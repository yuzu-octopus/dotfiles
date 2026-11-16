---
name: no-unsanctioned-global-paths
description: "Stay in workspace or /tmp; never write outside via any tool without explicit permission"
condition: '(?:(?<![\w/])~(?:\/|$)|(?<![\w/])~[A-Za-z0-9_][A-Za-z0-9_+-]*(?:\/|$)|(?<![\w/])~(?![\w/+.-])|\$\{?HOME\}?|\$\{HOME[^}]*\}|(?i:ssh|sftp|ftp|s3|gs|smb|cfg|file):\/\/|(?<![\w.:/])\/{2,}|(?<![\w.:/])\/(?!\/|tmp(?:\/|$)|private\/tmp(?:\/|$)|var\/folders(?:\/|$)|dev\/(?:null|zero|stdout|stderr|tty|fd)(?:\/|$))|(?<![\w.])\.\.(?![\w.])|%2[eE]|%2[fF]|%5[cC]|%252[efEF]|(?<![A-Za-z])[A-Za-z]:[\\/]|\\\\)'
scope: "tool:write, tool:edit"
---

Write only inside your cwd/workspace (relative paths) or global `/tmp`. Any `/`-rooted path outside `/tmp`, macOS temp (`/private/tmp`, `/var/folders`), or safe `/dev` sinks is forbidden — as are `~`, `$HOME`, `//` multi-slash, `..` segments, encoded `..` (`%2e`, `%2f`, `%5c`, double-encoded), drive letters (`C:\`, `C:/` — bare `X:` only when not a URL scheme), UNC `\\`, and remote schemes (`ssh://`, `sftp://`, `ftp://`, `s3://`, `cfg://`, `file://`). `agent://`, `local://`, `https://` stay allowed. Applies to file writes and edits. If a step genuinely needs an outside path: stop, explain why, stage the script or file under `/tmp` with the exact commands shown, and ask the user to run or approve it. Never write outside yourself.