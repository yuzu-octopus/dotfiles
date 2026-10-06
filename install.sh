#!/usr/bin/env bash
# install.sh — install these dotfiles into place.
# Usage: ./install.sh [--dry-run]
#
# Copies files (backing up existing ones to .bak). Safe to re-run:
# identical files are skipped.
set -u

DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

DOT="$(cd "$(dirname "$0")" && pwd)"

put() { # put <repo-rel-src> <dest-abs-path>
    local src="$DOT/$1" dst="$2"
    if [ ! -f "$src" ]; then echo "SKIP (missing in repo): $1"; return; fi
    if [ -f "$dst" ] && cmp -s "$src" "$dst"; then echo "OK   $dst"; return; fi
    if [ "$DRY" = 1 ]; then echo "WOULD INSTALL $dst"; return; fi
    mkdir -p "$(dirname "$dst")"
    [ -f "$dst" ] && cp "$dst" "$dst.bak" && echo "BACKUP $dst.bak"
    cp "$src" "$dst" && echo "INSTALL $dst"
}

put nushell/config.nu        "$HOME/.config/nushell/config.nu"
put nushell/env.nu           "$HOME/.config/nushell/env.nu"
put nushell/themes/dracula.nu "$HOME/.config/nushell/themes/dracula.nu"
put starship.toml            "$HOME/.config/starship.toml"
put fastfetch/config.jsonc   "$HOME/.config/fastfetch/config.jsonc"
put fastfetch/fastfetch-wifi "$HOME/.config/fastfetch/fastfetch-wifi"
if [ "$DRY" = 0 ]; then chmod +x "$HOME/.config/fastfetch/fastfetch-wifi" 2>/dev/null; fi

case "$(uname -s)" in
    Darwin) put ghostty/config "$HOME/Library/Application Support/com.mitchellh.ghostty/config.ghostty" ;;
    *)      put ghostty/config "$HOME/.config/ghostty/config" ;;
esac

# Agent context. RULES.md holds private account emails upstream, so the
# repo copy is redacted: never overwrite a real one.
for f in AGENTS.md APPEND_SYSTEM.md PERSONALITY.md agents/researcher.md agents/codebase-memory.md agents/codebase-memory-scout.md agents/codebase-memory-auditor.md agents/gossip.md skills/deep-research/SKILL.md skills/codebase-memory/SKILL.md rules/composio.md rules/git-init-commits.md rules/commit-author-fidelity.md rules/no-bash-grep.md rules/no-brew-install.md rules/no-curl-pipe-sh.md rules/no-git-commit-push.md rules/no-npm-npx.md rules/no-python3.md rules/no-rm-rf.md rules/no-system-pip-install.md; do
    put ".omp/$f" "$HOME/.omp/agent/$f"
done
if [ -f "$HOME/.omp/agent/RULES.md" ]; then
    echo "SKIP  $HOME/.omp/agent/RULES.md (exists, repo copy is redacted)"
else
    put ".omp/RULES.md" "$HOME/.omp/agent/RULES.md"
fi

echo "Done. Re-add account emails to ~/.omp/agent/RULES.md if needed, then restart your shell."
