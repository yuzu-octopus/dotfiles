---
name: no-python3
description: "Never run python3 or pip/pip3 directly — use uv (uv run, uvx, uv tool) with Python 3.15 default"
condition: "\b(python3|pip3|pip)\b"
scope: "tool:bash"
---

Never run `python3` / `pip` / `pip3` directly — use `uv` (`uv run`, `uvx`, `uv tool`). Same job, faster, no global state. Default to Python 3.15 (`--python 3.15`, `requires-python = ">=3.15"`); drop to 3.14 only when a dependency lacks 3.15 wheels. Commands work identically across patch versions; the floor follows the interpreter default for new local scripts, never published libraries. `uv run python` and `uv run --with <pkg>` are fine (they route through uv). If there is a genuine reason to invoke a bare interpreter, ask the user first.