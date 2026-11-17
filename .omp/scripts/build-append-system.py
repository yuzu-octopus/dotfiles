#!/usr/bin/env uv run python
"""Regenerate APPEND_SYSTEM.md from upstream skill files + local additions.

Usage: ./build-append-system.py   (run after `bunx skills update`)
Reads each SKILL.md, strips frontmatter, demotes headings one level,
applies OVERRIDES, prepends the local header.
Fails loudly on unmatched override so upstream rewrites surface
instead of silently dropping your deviations.
"""

from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
AGENT = HERE.parent
AGENTS_SKILLS = Path.home() / '.agents/skills'

# ---- config: skill name -> source file ----
SKILLS = {
    'ponytail': AGENTS_SKILLS / 'ponytail/SKILL.md',
    'caveman': AGENTS_SKILLS / 'caveman/SKILL.md',
    'unslop': AGENTS_SKILLS / 'unslop/SKILL.md',
    'using-superpowers': AGENTS_SKILLS / 'using-superpowers/SKILL.md',
}

# section titles in output order (HEADER, skills...)
ORDER = ['ponytail', 'caveman', 'unslop', 'using-superpowers']
TITLES = {
    'ponytail': 'Ponytail',
    'caveman': 'Caveman policy',
    'unslop': 'Unslop',
    'using-superpowers': 'Using superpowers',
}

# ---- config: (skill, find, replace); FAILS if find absent ----
# Keep this list short. An exact-string override dies with the line it
# anchors to, so every entry here is a maintenance liability upstream
# can break. Prefer DELETIONS for removing whole sections.
OVERRIDES = []

# ---- config: (skill, section marker); deletes marker line through the
# next heading or numbered rule. FAILS if the marker is absent. ----
DELETIONS = [
    # omp is the harness. None of the listed platform reference files apply.
    ('using-superpowers', '### Platform Adaptation'),
]


def load(name, path):
    raw = path.read_text().split('---', 2)[2].strip()
    has_h1 = bool(re.match(r'(?m)^# [^\n]+', raw))
    body = re.sub(r'(?m)^#(#{0,5}) ', r'##\1 ', raw)  # demote one level
    for s, find, repl in OVERRIDES:
        if s != name:
            continue
        if find not in body:
            sys.exit(f'override missed in {name}: {find!r}')
        body = body.replace(find, repl)
    for s, marker in DELETIONS:
        if s != name:
            continue
        if marker not in body:
            sys.exit(f'deletion marker missed in {name}: {marker!r}')
        lines = body.splitlines()
        start = next(i for i, l in enumerate(lines) if marker in l)
        end = next((i for i in range(start + 1, len(lines)) if re.match(r'^\d+\. \*\*|^#{1,6} ', lines[i])), len(lines))
        del lines[start:end]
        body = '\n'.join(lines).strip()
    if has_h1:
        body = re.sub(r'(?m)^##+ .+$', f'## {TITLES[name]}', body, count=1)
    else:
        body = f'## {TITLES[name]}\n\n' + body
    return re.sub(r'\n{3,}', '\n\n', body)


def main():
    header = (HERE / 'append-header.md').read_text().rstrip()
    for name, path in SKILLS.items():
        if not path.exists():
            sys.exit(f'missing skill file: {path}')
    parts = [header]
    for name in ORDER:
        parts.append(load(name, SKILLS[name]))
    out = AGENT / 'APPEND_SYSTEM.md'
    out.write_text('\n\n'.join(parts) + '\n')
    print(f'wrote {out} ({len(out.read_text().splitlines())} lines)')


main()
