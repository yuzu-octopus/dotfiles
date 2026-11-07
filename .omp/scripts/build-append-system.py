#!/usr/bin/env uv run python
"""Regenerate APPEND_SYSTEM.md from upstream skill files + local overrides.

Usage: ./build-append-system.py   (run after `bunx skills update`)
Reads each SKILL.md, strips frontmatter, demotes headings one level,
applies OVERRIDES, splices between HEADER and FOOTER files.
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
}

# section titles in output order (HEADER, skills..., FOOTER)
ORDER = ['ponytail', 'caveman', 'unslop']
TITLES = {
    'ponytail': 'Ponytail',
    'caveman': 'Caveman policy',
    'unslop': 'Unslop',
}

# ---- config: (skill, find, replace); FAILS if find absent ----
OVERRIDES = [
    ('unslop', '13. **Em dash overuse.** Avoid em dashes entirely. Use periods or commas only (no parentheses, no en dashes, no hyphen-as-dash substitutes). If a thought needs separation, end the sentence or use a comma.',
     '13. **Em dash overuse.** Avoid em dashes in mid-sentence prose. Prefer periods or commas to separate thoughts. Em dashes remain acceptable where needed as deliberate structural delimiters in reference tables, CLI option lists, and concise rule definitions.'),
    ('unslop', '3. **Superficial -ing phrases.** "highlighting...", "ensuring...", "reflecting...", "showcasing...", "fostering...". Delete or expand with real sources.',
     '3. **Superficial -ing phrases.** "highlighting...", "ensuring...", "reflecting...", "showcasing...", "fostering...". Delete or expand with real sources.\n4. **Promotional language.** "nestled", "vibrant", "breathtaking", "groundbreaking", "renowned", "stunning", "must-visit". Use neutral descriptions.'),
    ('unslop', '5. **Vague attributions.** "Experts believe", "Industry reports suggest", "Some critics argue". Name the source or delete.',
     '5. **Vague attributions.** "Experts believe", "Industry reports suggest", "Some critics argue". Name the source or delete.\n6. **Formulaic challenges.** "Despite challenges... continues to thrive." Replace with specific facts.'),
    ('unslop', '20. **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!", "Found the smoking gun!" Remove.',
     '20. **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!", "Found the smoking gun!" Remove.\n21. **Cutoff disclaimers.** "While specific details are limited..." Find sources or remove.'),
    # unslop: our soul section (upstream has none) spliced after the intro line
    ('unslop', 'Edit text to remove AI patterns. Scan for the patterns below, then rewrite. Preserve meaning and match the intended tone.',
     'Edit text to remove AI patterns and add human voice. Scan for the patterns below, then rewrite. Preserve meaning and match the intended tone.\n\n### Adding soul\n\nRemoving patterns is half the job. Sterile, voiceless writing is just as obvious.\n\n- **Have opinions.** React to facts instead of neutrally listing pros and cons.\n- **Vary rhythm.** Short sentences. Then longer ones that take their time. Mix it up.\n- **Acknowledge complexity.** "Impressive but also kind of unsettling" beats "impressive."\n- **Use "I" when it fits.** First person isn\'t unprofessional.\n- **Let some mess in.** Perfect structure looks machine-made.\n- **Be specific.** Not "this is concerning" but "there\'s something unsettling about agents churning away at 3am."'),
    ('unslop', 'Rule numbers are stable ids that other skills cite. A removed rule leaves a gap.\n\n#### Content',
     '#### Content\n\n1. **Puffery.** "pivotal moment", "testament to", "evolving landscape", "setting the stage for", "indelible mark", "deeply rooted". Cut puffery, state what happened.\n2. **Name-dropping.** Listing media outlets without context. Pick one, say what was said.'),
]

DELETIONS = [
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
    return body


def main():
    header = (HERE / 'append-header.md').read_text().rstrip()
    footer = (HERE / 'append-footer.md').read_text().rstrip()
    for name, path in SKILLS.items():
        if not path.exists():
            sys.exit(f'missing skill file: {path}')
    parts = [header]
    for name in ORDER:
        parts.append(load(name, SKILLS[name]))
    parts.append(footer)
    out = AGENT / 'APPEND_SYSTEM.md'
    out.write_text('\n\n'.join(parts) + '\n')
    print(f'wrote {out} ({len(out.read_text().splitlines())} lines)')


main()
