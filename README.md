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
- **[.omp/](./.omp/)** — Agent context (AGENTS, APPEND_SYSTEM, PERSONALITY,
  RULES, agents, skills, rules). Account emails redacted; re-add locally.
- **[.agents/.skill-lock.json](./.agents/.skill-lock.json)** — Manifest of
  the 59 global skills (sources, hashes). Reference copy; not installed
  by install.sh.

## Related

- Portfolio site showcasing these configs:
  [yuzu-octopus.github.io](https://yuzu-octopus.github.io)
- All configs use the [Dracula theme](https://draculatheme.com) color palette
