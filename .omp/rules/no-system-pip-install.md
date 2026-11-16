---
name: no-system-pip-install
description: "Never install Python packages into system Python via pip or uv pip --system — use uv/project-local tooling instead"
condition: '(?<!uv )(?<!uv  )\bpip(?:\d|\.\d+)*(?:\s+)(install|uninstall)\b|\buv\s+pip\b[^\n]*--system\b'
scope: "tool:bash"
---

Always install Python dependencies into the project-local environment (`uv add`, `uv pip install`, project venv, `uv run --with`). `uv pip` without `--system` refuses system Python (prompts for venv) — the dangerous forms are bare `pip install` against system Python (needs `--break-system-packages` on Homebrew macOS, risks breaking system Python) and `uv pip install --system` (explicit opt-in to the same). Never either without explicit user permission.