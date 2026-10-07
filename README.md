# .config — Dotfiles

My personal configuration files. Managed as a monorepo, each config in its own
directory or file.

## Install

```sh
git clone https://github.com/yuzu-octopus/dotfiles.git
cd dotfiles
./install.sh
```

Copies everything into place, backing up existing files to `.bak`. Safe to
re-run. Preview with `./install.sh --dry-run`.

| Repo path | Installed to |
|---|---|
| `nushell/` | `~/.config/nushell/` |
| `starship.toml` | `~/.config/starship.toml` |
| `fastfetch/` | `~/.config/fastfetch/` (wifi helper made executable) |
| `ghostty/config` | macOS: `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty`, Linux: `~/.config/ghostty/config` |
| `.omp/` | `~/.omp/agent/` |
| `ruff/` | `~/.config/ruff/` |
| `ty/` | `~/.config/ty/` |
| `biome/` | `~/.config/biome/` (macOS also symlinked into `~/Library/Application Support/biome/`) |

Two manual steps: re-add account emails to `~/.omp/agent/RULES.md`
(the repo copy is redacted and never overwrites yours), then restart
your shell.

## Contents

- **[fastfetch/config.jsonc](./fastfetch/config.jsonc)** — Fastfetch system info
  display with Dracula theme
- **[fastfetch/fastfetch-wifi](./fastfetch/fastfetch-wifi)** — Wi-Fi status
  helper used by the fastfetch config (macOS/arm64 binary)
- **[ghostty/config](./ghostty/config)** — Ghostty terminal emulator settings
- **[nushell/config.nu](./nushell/config.nu)** — Nushell shell configuration
  (aliases, fuzzy completions, sqlite history, starship integration)
- **[nushell/env.nu](./nushell/env.nu)** — Nushell environment (PATH, editor,
  vivid Dracula LS_COLORS)
- **[nushell/themes/](./nushell/themes/)** — Nushell color themes (Dracula)
- **[scripts/code_runner.zsh](./scripts/code_runner.zsh)** — Polyglot file
  runner with Dracula-themed output
- **[starship.toml](./starship.toml)** — Starship prompt configuration
- **[ruff/ruff.toml](./ruff/ruff.toml)** — Global Ruff config, strict for
  AI-written code (ANN, D, S, TRY, ERA, T20). Fallback only: a repo
  `[tool.ruff]` shadows it entirely
- **[ty/ty.toml](./ty/ty.toml)** — Global ty config (merges with project
  config, project wins scalars)
- **[biome/biome.json](./biome/biome.json)** — Global Biome config
  (tabs, 100 cols, double quotes, organizeImports). Fallback only
- **[.omp/](./.omp/)** — Agent context: AGENTS, APPEND_SYSTEM, PERSONALITY,
  RULES, five agent definitions (researcher, gossip, codebase-memory family),
  two skills (deep-research, codebase-memory), ten rules. Account emails
  redacted; re-add locally.
- **[.agents/.skill-lock.json](./.agents/.skill-lock.json)** — Manifest of
  the 59 global skills (sources, hashes). Reference copy; not installed
  by install.sh.

`APPEND_SYSTEM.md` is generated, not hand-edited. After `npx skills update`,
run `~/.omp/agent/scripts/build-append-system.py` to re-splice the ponytail,
caveman, unslop, and codebase-memory skill bodies into the header and footer
fragments. Overrides in that script fail loudly when upstream text drifts, so
a silent regeneration can never drop a local deviation.

- **[.omp/scripts/gossip.py](./.omp/scripts/gossip.py)** — Multi-source
  social/technical chatter reader behind the `gossip` agent (HN, Reddit,
  arXiv, GitHub, YouTube, RSS, Polymarket). Needs `gh`, `yt-dlp`, and network
  access; adapters degrade independently.
- **[.omp/scripts/build-append-system.py](./.omp/scripts/build-append-system.py)**
  — Regenerates `APPEND_SYSTEM.md` from upstream skills plus local overrides.

## Related

- Portfolio site showcasing these configs:
  [yuzu-octopus.github.io](https://yuzu-octopus.github.io)
- All configs use the [Dracula theme](https://draculatheme.com) color palette
