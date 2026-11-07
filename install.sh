#!/usr/bin/env bash
# install.sh — install these dotfiles into place.
# Usage: ./install.sh [--dry-run] [group ...]
#
# No group given: install everything.
# Groups:
#   terminal    nushell, starship, fastfetch, ghostty
#   lint        ruff, ty, biome (+ macOS App Support symlink)
#   omp         every omp-* group below
#   omp-context AGENTS.md, APPEND_SYSTEM.md, PERSONALITY.md, RULES.md
#   omp-agents  agents/
#   omp-rules   rules/
#   omp-skills  skills/, global skill lock
#   omp-scripts scripts/
#   omp-configs config.yml, models.yml, mcp.json
#
# Copies files (backing up existing ones to .bak). Safe to re-run:
# identical files are skipped.
set -u

DRY=0
WANT=()
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY=1 ;;
        -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
        -*) echo "unknown flag: $arg" >&2; exit 2 ;;
        *) WANT+=("$arg") ;;
    esac
done

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

# want <group> — true when no group was requested, or when the group was
# named directly or via its "omp" parent.
want() {
    [ ${#WANT[@]} -eq 0 ] && return 0
    local g
    for g in ${WANT[@]+"${WANT[@]}"}; do
        [ "$g" = "$1" ] && return 0
        if [ "$g" = omp ]; then
            case "$1" in omp-*) return 0 ;; esac
        fi
    done
    return 1
}

if want terminal; then
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
fi

if want lint; then
    # Biome also needs the App Support symlink on macOS (biome reads
    # ~/Library/Application Support/biome/biome.json, not ~/.config).
    put ruff/ruff.toml   "$HOME/.config/ruff/ruff.toml"
    put ty/ty.toml       "$HOME/.config/ty/ty.toml"
    put biome/biome.json "$HOME/.config/biome/biome.json"
    if [ "$DRY" = 0 ] && [ "$(uname -s)" = Darwin ]; then
        mkdir -p "$HOME/Library/Application Support/biome"
        ln -sfn "$HOME/.config/biome/biome.json" "$HOME/Library/Application Support/biome/biome.json"
    fi
fi

if want omp-context; then
    for f in AGENTS.md APPEND_SYSTEM.md PERSONALITY.md; do
        put ".omp/$f" "$HOME/.omp/agent/$f"
    done
    # RULES.md holds private account emails upstream, so the repo copy is
    # redacted: never overwrite a real one.
    if [ -f "$HOME/.omp/agent/RULES.md" ]; then
        echo "SKIP  $HOME/.omp/agent/RULES.md (exists, repo copy is redacted)"
    else
        put ".omp/RULES.md" "$HOME/.omp/agent/RULES.md"
    fi
fi

if want omp-agents; then
    for f in agents/researcher.md agents/gossip.md; do
        put ".omp/$f" "$HOME/.omp/agent/$f"
    done
fi

if want omp-rules; then
    for f in composio.md git-init-commits.md commit-author-fidelity.md \
             no-bash-grep.md no-brew-install.md no-curl-pipe-sh.md \
             no-git-commit-push.md no-npm-npx.md no-python3.md \
             no-rm-rf.md no-system-pip-install.md; do
        put ".omp/rules/$f" "$HOME/.omp/agent/rules/$f"
    done
fi

if want omp-skills; then
    put ".omp/skills/deep-research/SKILL.md" "$HOME/.omp/agent/skills/deep-research/SKILL.md"
    put .agents/.skill-lock.json "$HOME/.agents/.skill-lock.json"
fi

if want omp-scripts; then
    for f in scripts/append-header.md scripts/append-footer.md \
             scripts/build-append-system.py scripts/gossip.py; do
        put ".omp/$f" "$HOME/.omp/agent/$f"
    done
    if [ "$DRY" = 0 ]; then
        chmod +x "$HOME/.omp/agent/scripts/build-append-system.py" "$HOME/.omp/agent/scripts/gossip.py" 2>/dev/null
    fi
fi

if want omp-configs; then
    for f in config.yml models.yml mcp.json; do
        put ".omp/$f" "$HOME/.omp/agent/$f"
    done
fi

echo "Done."
