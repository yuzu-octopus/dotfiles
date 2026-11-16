#!/usr/bin/env uv run --script
"""Regression suite for the TTSR tripwire rules under rules/.

Run from anywhere: uv run path/to/test-rules.py
Exit 0 when every sample matches its expectation, else 1 with misses.

Self-match note: TTSR scans raw text, so literal outside-path samples in
this file would trip the rules under test. Samples are assembled at
runtime with chr and join; only plain fragments appear below.
"""
import re
import sys
from pathlib import Path

S = chr(47)
T = chr(126)
D = chr(92)
P = chr(37)
Q = chr(96)
DL = chr(36)
SQ = chr(39)
DQ = chr(34)

RULES = Path(__file__).resolve().parent.parent / "rules"


def load_condition(name):
    text = (RULES / name).read_text()
    _, fm, _ = text.split("---", 2)
    for line in fm.splitlines():
        if line.startswith("condition:"):
            v = line.split(":", 1)[1].strip()
            if len(v) >= 2 and v.startswith("'") and v.endswith("'"):
                v = v[1:-1].replace("''", "'")
            return re.compile(v)
    raise AssertionError("no condition in " + name)


ETC = S + "etc" + S + "x"
TMP = S + "tmp" + S + "x"

# (sample, True means the rule must match)
PATH_CASES = [
    (T + S + "f", True), (T, True), (T + "root", True),
    (DL + "HOME" + S + "x", True),
    (DL + "{HOME:-" + S + "d}" + S + "x", True),
    (S + "Users" + S + "a", True), (ETC, True), (S + "x", True),
    (S * 2 + "srv" + S + "x", True), (S * 3 + "etc", True),
    ("C:" + S + "w", True), ("C:" + D + "w", True), (D * 2 + "s", True),
    ("." + ".", True), ("." + "." + S + "x", True),
    ("a" + S + "." + "." + S + "b", True),
    (P + "2e" + S + "x", True), (P + "2F" + S + "x", True),
    (P + "5c" + S + "x", True), (P + "252e" + S + "x", True),
    ("sftp:" + S * 2 + "h" + S + "x", True),
    ("SSH:" + S * 2 + "h" + S + "x", True),
    (P + "252f" + S + "x", True), (P + "252F", True),
    (S + "tmpfoo" + S + "x", True), (S + "dev" + S + "tcp" + S + "h" + S + "80", True),
    ("rel" + S + "p", False), ("." + S + "x", False),
    (TMP, False), (S + "private" + S + "tmp" + S + "x", False),
    (S + "var" + S + "folders" + S + "a", False),
    (S + "dev" + S + "null", False), (S + "dev" + S + "fd" + S + "63", False),
    ("." + "." + "hidden", False),
    ("agent:" + S * 2 + "F", False), ("local:" + S * 2 + "r.md", False),
    ("https:" + S * 2 + "e.com" + S + "x", False),
    ("file..txt", False), (".omp" + S + "agent" + S + "x", False),
]

SHELL_CASES = [
    ("cat " + S + "etc" + S + "passwd", False),
    ("ls " + S + "tmp", False),
    ("curl https:" + S * 2 + "e.com" + S + "x", False),
    ("echo hi", False),
    ("cd " + "." + ".", False),
    ("ls " + "." + "." + S, False),
    ("cat | tee", False),
    ("echo hi > ." + S + "l.txt", False),
    ("cp a b", False),
    ("curl u -o " + TMP, False),
    ("Bun.write(" + SQ + TMP + SQ + ", d)", False),
    ("echo hi > " + S + "dev" + S + "null", False),
    ("echo hi > " + TMP, False),
    ("echo " + Q + "id" + Q + " > " + ETC, True),
    ("echo hi > " + DQ + ETC + DQ, True),
    ("cp a " + DQ + ETC + DQ, True),
    ("echo hi > " + DL + "{OUT}", True),
    ("echo x >| " + ETC, True),
    ("open(" + SQ + ETC + SQ + "," + SQ + "r+" + SQ + ")", True),
    ("fs.appendFile(" + SQ + ETC + SQ + ", d)", True),
    ("tar -cf " + ETC + " .", True),
    ("tar -tf " + ETC, False),
    ("tar -cf out.tar .", False),
    ("curl u --output " + ETC, True),
    ("echo hi > " + T + S + "f", True),
    ("echo hi > " + ETC, True),
    ("cat " + S + "e" + S + "p > " + TMP, False),
    ("cp " + ETC + " .", False),
    ("echo " + DL + "HOME > out.txt", False),
    ("cat " + S + "etc" + S + "passwd | tee " + TMP, False),
    ("open(" + SQ + ETC + SQ + "," + SQ + "r" + SQ + ")", False),
    ("rm " + ETC, True),
    ("rmdir " + ETC, True),
    ("sed -i s/a/b/ " + ETC, True),
    ("writeFile(" + SQ + ETC + SQ + ", d)", True),
    ("cp a " + ETC, True),
    ("tee " + ETC, True),
    ("echo x | sponge " + ETC, True),
    ("dd if=a of=" + ETC, True),
    ("exec 3>" + ETC, True),
    ("echo hi > " + DL + "OUT", True),
    ("echo hi > " + P + "OUT" + P, True),
    ("echo hi > " + DL + "(curl u)", True),
    ("eval " + DQ + "echo hi > " + ETC + DQ, True),
    ("base64 -d > " + ETC, True),
    ("xxd -r > " + ETC, True),
    ("curl u -o " + ETC, True),
    ("open(" + SQ + ETC + SQ + "," + SQ + "w" + SQ + ")", True),
    ("Bun.write(" + SQ + ETC + SQ + ", d)", True),
    ("Out-File " + ETC, True),
    ("Path(" + DQ + ETC + DQ + ").write_text(d)", True),
]

TOOL_CASES = [
    ("no-python3.md", [
        ("pip install x", True), ("uv pip install x", False),
        ("uvx ruff check .", False), ("uv run python3 a.py", False),
        ("python3 a.py", True), ("uv  pip install x", False),
        ("python -m pip install x", True), ("uv run --with pip black .", False),
        ("uv" + chr(9) + "pip install x", False), ("uv run  python3 a.py", False),
        ("pip install x && uv run y", True), ("echo uv pip", False),
        ('{"command":"pip install x"}', True),
        ('{"command":"uv pip install x"}', False),
        ('{"command":"python -m pip install x"}', True),
    ]),
    ("no-curl-pipe-sh.md", [
        ("curl https:" + S * 2 + "e.com" + S + "i | sh", True),
        ("curl u | sudo bash -s", True),
        ("wget u | sh", True),
        ("sh -c " + DQ + DL + "(curl u)" + DQ, True),
        ("curl u | " + S + "bin" + S + "sh", True),
        ("curl u | tee " + TMP + " | sh", True),
        ("curl https:" + S * 2 + "e.com" + S + "x | jq", False),
    ]),
    ("no-brew-install.md", [
        ("brew install f", True), ("brew reinstall f", True),
        ("brew bundle", True), ("brew upgrade", True), ("brew list", False),
    ]),
    ("no-rm-rf.md", [
        ("rm -rf " + S, True), ("rm -fr x", True),
        ("rm -r -f x", True), ("rm -rfv x", True),
        ("rm --recursive --force x", True),
        ("rm -Rf x", True), ("rm -fR x", True),
        ("rm -- -rf", False), ("rm ./" + "-rf", False),
        ("rm -f a", False), ("rm -r d", False), ("rm a b", False),
    ]),
    ("no-git-commit-push.md", [
        ("git commit -m " + DQ + "x" + DQ, True),
        ("git -c core.hooksPath=" + S + "dev" + S + "null commit", True),
        ("git push", True), ("git status", False),
    ]),
    ("git-init-commits.md", [
        ("git init", True),
        ("git -C sub init", True),
        ("git commit -m " + DQ + "x" + DQ, False),
    ]),
    ("no-npm-npx.md", [
        ("npm install x", True), ("npx foo", True),
        ("echo npm", False), ("bunx @npm/foo", False),
        ("bun install x", False), ("bunx foo", False),
        ("PATH=" + S + "usr" + S + "bin npm run build", True),
        ('bash -c ' + DQ + "npm install x" + DQ, True),
        ('{"command":"npm i x"}', True),
        ('{"command":"echo npm"}', False),
    ]),
    ("no-system-pip-install.md", [
        ("pip install x", True), ("pip3 uninstall x", True),
        ("uv pip install x --system", True),
        ("uv pip sync req.txt --system", True),
        ("pip3.15 install x", True), ("uv pip --system install x", True),
        ("uv pip install x", False), ("uv add x", False),
        ("python -m pip install x", True),
    ]),
    ("no-bash-grep.md", [
        ("grep foo bar", True), ("egrep foo", True),
        ("fgrep foo", True), ("zgrep foo", True),
        ("git  grep foo", False), ("git --no-pager grep foo", False),
        ("git grep foo", False), ("rg foo", False),
        ("git -C sub grep foo", False),
        ("git -c color.ui=always grep foo", False),
        ("git log --grep=bar", False),
        ("rg --grep foo", False),
        ("ls | grep foo", True), ("xargs grep foo", True),
        ("sudo grep foo", True), ("VAR=1 grep x", True),
        ('{"command":"grep foo"}', True),
        ('{"command":"git grep foo"}', False),
        ('{"command":"ls | grep foo"}', True),
        ('{"command":"echo grep"}', False),
    ]),
    ("commit-author-fidelity.md", [
        ("git -c user.name=x commit", True),
        ("git -c user.email=x@y commit", True),
        ("git commit --author=X", True),
        ("GIT_AUTHOR_NAME=X git commit", True),
        ("git commit -m hi", False),
        ("git config user.name x", False),
    ]),
    ("no-unsanctioned-global-paths.md", [
        ("path: " + T + S + "f", True),
        ("path: " + ETC, True),
        ("path: " + TMP, False),
        ("path: rel" + S + "x", False),
    ]),
    ("no-unsanctioned-shell-writes.md", [
        ("echo hi > " + ETC, True),
        ("cat " + ETC, False),
    ]),
]


def run(name, rx, cases):
    fails = []
    for sample, want in cases:
        if bool(rx.search(sample)) != want:
            fails.append(("BLOCK" if want else "allow") + " expected: " + sample)
    tag = "ok" if not fails else str(len(fails)) + " MISS"
    print(name + ": " + tag + " (" + str(len(cases)) + " cases)")
    return fails


def main():
    all_fails = []
    all_fails += run("paths", load_condition("no-unsanctioned-global-paths.md"), PATH_CASES)
    all_fails += run("shell", load_condition("no-unsanctioned-shell-writes.md"), SHELL_CASES)
    for name, cases in TOOL_CASES:
        all_fails += run(name, load_condition(name), cases)
    if all_fails:
        print("FAILURES:")
        for f in all_fails:
            print("  " + f)
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
