#!/usr/bin/env zsh
#
# code_runner.zsh — A polyglot file runner with Dracula-themed output.
#
# Detects the file extension and runs it with the appropriate interpreter.
# Supports Python, JavaScript/TypeScript, Go, Rust, C/C++, Java, Shell,
# Nushell, Ruby, Perl, Lua, and Swift.
#
# Usage:
#   code_runner <file> [-- <args>...]
#   code_runner --list
#   code_runner --version
#
# Installation:
#   cp code_runner.zsh ~/.local/bin/code_runner
#   chmod +x ~/.local/bin/code_runner
#
# Designed for use with Zed, but works from any terminal.
#

VERSION="2.0.0"

# ── High-Resolution Timing ──────────────────────────────────────────────────
zmodload zsh/datetime

# ── Dracula Color Palette ───────────────────────────────────────────────────
# https://github.com/dracula/dracula-theme
PURPLE='\033[38;2;189;147;249m'
PINK='\033[38;2;255;121;198m'
RED='\033[38;2;255;85;85m'
GREEN='\033[38;2;80;250;123m'
COMMENT='\033[38;2;98;114;164m'
FG='\033[38;2;248;248;242m'
BOLD='\033[1m'
RESET='\033[0m'

# ── NO_COLOR Support ────────────────────────────────────────────────────────
# Disable colors when NO_COLOR is set or stdout is not a terminal.
if [[ -n "$NO_COLOR" ]] || [[ ! -t 1 ]]; then
    PURPLE=""
    PINK=""
    RED=""
    GREEN=""
    COMMENT=""
    FG=""
    BOLD=""
    RESET=""
fi

# ── Output Helpers ──────────────────────────────────────────────────────────
SEP_LEN=$(tput cols 2>/dev/null || echo 80)
SEP=$(printf '%*s' "$SEP_LEN" '' | tr ' ' '─')

# Print the run header with a purple ▶ play icon and full-width separator.
print_header() {
    printf "${PURPLE}${BOLD}▶${RESET} ${BOLD}${FG}%s${RESET}\n" "$1"
    printf "${COMMENT}${SEP}${RESET}\n"
}

# Print the run footer with status icon, duration, and color-coded exit code.
print_footer() {
    local duration="$1" exit_code="$2" icon exit_color
    if [[ "$exit_code" -eq 0 ]]; then
        icon="${PURPLE}${BOLD}✓${RESET}"
        exit_color="${GREEN}"
    else
        icon="${RED}${BOLD}✗${RESET}"
        exit_color="${RED}"
    fi
    printf "${COMMENT}${SEP}${RESET}\n"
    printf "${icon} ${BOLD}${FG}Finished in ${PINK}%s${RESET} ${FG}(exit: ${exit_color}%s${RESET}${FG})${RESET}\n" \
        "$duration" "$exit_code"
}

# Print an error message to stderr with a red ✗ icon.
print_error() {
    printf "${RED}${BOLD}✗${RESET} ${RED}%s${RESET}\n" "$1" >&2
}

# Format duration with smart unit selection (ns → μs → ms → s → min → hr).
format_time() {
    local t=$1
    if (( t < 0.000001 )); then
        printf "%.2f ns" $(( t * 1000000000 ))
    elif (( t < 0.001 )); then
        printf "%.2f μs" $(( t * 1000000 ))
    elif (( t < 1 )); then
        printf "%.2f ms" $(( t * 1000 ))
    elif (( t < 60 )); then
        printf "%.2f s" $t
    elif (( t < 3600 )); then
        printf "%d min %d s" $(( t / 60 )) $(( t % 60 ))
    else
        printf "%d hr %d min" $(( t / 3600 )) $(( (t % 3600) / 60 ))
    fi
}

# ── Signal Forwarding ───────────────────────────────────────────────────────
# Forward signals to the child process so Ctrl-C works cleanly.
CHILD_PID=""
forward_signal() {
    local sig="$1"
    [[ -n "$CHILD_PID" ]] && kill -"$sig" "$CHILD_PID" 2>/dev/null
}
trap 'forward_signal INT' INT
trap 'forward_signal TERM' TERM

# ── Run a command with signal tracking ──────────────────────────────────────
run_with_tracking() {
    "$@" &
    CHILD_PID=$!
    wait "$CHILD_PID"
    local exit_code=$?
    CHILD_PID=""
    return $exit_code
}

# ── Cleanup compiled binaries ───────────────────────────────────────────────
cleanup_bin() {
    [[ -n "${1:-}" && -f "$1" ]] || return 0
    if command -v trash >/dev/null 2>&1; then
        trash "$1"
    else
        rm -f -- "$1"
    fi
}

# ── CLI Flags ───────────────────────────────────────────────────────────────
case "${1:-}" in
    --version|-v)
        echo "code_runner $VERSION"
        exit 0
        ;;
    --list|-l)
        echo "Supported extensions:"
        echo "  Python:       py"
        echo "  JavaScript:   js, ts, jsx, tsx"
        echo "  Go:           go"
        echo "  Rust:         rs"
        echo "  C/C++:        c, cpp, cc, cxx"
        echo "  Java:         java"
        echo "  Shell:        sh, zsh"
        echo "  Nushell:      nu"
        echo "  Ruby:         rb"
        echo "  Perl:         pl, pm"
        echo "  Lua:          lua"
        echo "  Swift:        swift"
        exit 0
        ;;
esac

# ── Argument Handling ───────────────────────────────────────────────────────
# Split argv on -- quote-safely, then resolve the file path.
# Zed passes paths unquoted; rejoin pre--- args only when the joined
# path is a real file, so quoted paths containing spaces still work.
# Support pass-through args after --: code_runner script.py -- arg1 arg2
PRE_ARGS=()
PASS_ARGS=()
in_pass_args=false
for arg in "$@"; do
    if [[ "$arg" == "--" ]] && ! $in_pass_args; then
        in_pass_args=true
        continue
    fi
    if $in_pass_args; then
        PASS_ARGS+=("$arg")
    else
        PRE_ARGS+=("$arg")
    fi
done

FILE_PATH=""
if (( ${#PRE_ARGS} > 0 )); then
    joined="${(j: :)PRE_ARGS}"
    if [[ -f "$joined" ]]; then
        FILE_PATH="$joined"
    else
        FILE_PATH="${PRE_ARGS[1]}"
    fi
fi

if [[ -z "$FILE_PATH" ]]; then
    echo "Usage: code_runner <file> [-- <args>...]"
    echo ""
    echo "Runs a file with the appropriate interpreter based on its extension."
    echo ""
    echo "Options:"
    echo "  --list, -l       Show supported extensions"
    echo "  --version, -v    Show version"
    echo ""
    echo "Supported extensions:"
    echo "  Python:    py"
    echo "  JavaScript: js, ts, jsx, tsx"
    echo "  Go:        go"
    echo "  Rust:      rs"
    echo "  C/C++:     c, cpp, cc, cxx"
    echo "  Java:      java"
    echo "  Shell:     sh, zsh"
    echo "  Nushell:   nu"
    echo "  Ruby:      rb"
    echo "  Perl:      pl, pm"
    echo "  Lua:       lua"
    echo "  Swift:     swift"
    exit 1
fi

if [[ ! -f "$FILE_PATH" ]]; then
    print_error "File '$FILE_PATH' not found."
    exit 1
fi

# ── File Metadata ───────────────────────────────────────────────────────────
EXT="${FILE_PATH##*.}"
FILENAME=$(basename -- "$FILE_PATH")
DIR_PATH=$(dirname -- "$FILE_PATH")

# Show relative path from $HOME for cleaner output; fall back to filename.
REL_PATH="${FILE_PATH#$HOME/}"
[[ "$REL_PATH" == "$FILE_PATH" ]] && REL_PATH="$FILENAME"

# ── Timing Start ────────────────────────────────────────────────────────────
start_time=$EPOCHREALTIME

# ── Execution Logic ─────────────────────────────────────────────────────────
case "$EXT" in
    # ── Python ──────────────────────────────────────────────────────────────
    py)
        if command -v uv >/dev/null; then
            print_header "uv run $REL_PATH"
            uv run -- "$FILE_PATH" "${PASS_ARGS[@]}"
        else
            print_header "python3 $REL_PATH"
            python3 -- "$FILE_PATH" "${PASS_ARGS[@]}"
        fi
        ;;

    # ── JavaScript / TypeScript ─────────────────────────────────────────────
    js|ts|jsx|tsx)
        if command -v bun >/dev/null; then
            print_header "bun run $REL_PATH"
            bun run -- "$FILE_PATH" "${PASS_ARGS[@]}"
        else
            print_header "node $REL_PATH"
            node -- "$FILE_PATH" "${PASS_ARGS[@]}"
        fi
        ;;

    # ── Go ──────────────────────────────────────────────────────────────────
    go)
        print_header "go run $REL_PATH"
        go run "$FILE_PATH" "${PASS_ARGS[@]}"
        ;;

    # ── Rust ────────────────────────────────────────────────────────────────
    rs)
        if [[ -f "$DIR_PATH/Cargo.toml" ]]; then
            print_header "cargo run"
            cargo run --quiet --manifest-path "$DIR_PATH/Cargo.toml" -- "${PASS_ARGS[@]}"
        else
            local BIN_NAME="${FILE_PATH%.*}"
            trap "cleanup_bin '$BIN_NAME'" EXIT

            print_header "rustc $REL_PATH && ./$FILENAME:r"
            rustc "$FILE_PATH" -o "$BIN_NAME" && run_with_tracking "$BIN_NAME" "${PASS_ARGS[@]}"
        fi
        ;;

    # ── C / C++ ─────────────────────────────────────────────────────────────
    cpp|cc|cxx|c)
        local compiler="g++"; [[ "$EXT" == "c" ]] && compiler="gcc"
        local BIN_NAME="${FILE_PATH%.*}"
        trap "cleanup_bin '$BIN_NAME'" EXIT

        print_header "$compiler $REL_PATH && ./$FILENAME:r"
        $compiler "$FILE_PATH" -o "$BIN_NAME" && run_with_tracking "$BIN_NAME" "${PASS_ARGS[@]}"
        ;;

    # ── Java ────────────────────────────────────────────────────────────────
    java)
        print_header "java $REL_PATH"
        java "$FILE_PATH" "${PASS_ARGS[@]}"
        ;;

    # ── Shell ───────────────────────────────────────────────────────────────
    sh|zsh)
        print_header "zsh $REL_PATH"
        zsh -- "$FILE_PATH" "${PASS_ARGS[@]}"
        ;;

    # ── Nushell ─────────────────────────────────────────────────────────────
    nu)
        print_header "nu $REL_PATH"
        nu -- "$FILE_PATH" "${PASS_ARGS[@]}"
        ;;

    # ── Ruby ────────────────────────────────────────────────────────────────
    rb)
        print_header "ruby $REL_PATH"
        ruby "$FILE_PATH" "${PASS_ARGS[@]}"
        ;;

    # ── Perl ────────────────────────────────────────────────────────────────
    pl|pm)
        print_header "perl $REL_PATH"
        perl "$FILE_PATH" "${PASS_ARGS[@]}"
        ;;

    # ── Lua ─────────────────────────────────────────────────────────────────
    lua)
        print_header "lua $REL_PATH"
        lua "$FILE_PATH" "${PASS_ARGS[@]}"
        ;;

    # ── Swift ───────────────────────────────────────────────────────────────
    swift)
        print_header "swift $REL_PATH"
        swift "$FILE_PATH" "${PASS_ARGS[@]}"
        ;;

    # ── Unknown ─────────────────────────────────────────────────────────────
    *)
        print_error "No runner configured for .$EXT files."
        exit 1
        ;;
esac

# ── Timing End ──────────────────────────────────────────────────────────────
exit_code=$?
end_time=$EPOCHREALTIME

# Calculate duration in seconds (floating point).
duration=$(( end_time - start_time ))

# ── Done ────────────────────────────────────────────────────────────────────
print_footer "$(format_time $duration)" "$exit_code"
exit $exit_code
