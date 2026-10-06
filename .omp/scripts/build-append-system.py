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
    'codebase-memory': AGENT / 'skills/codebase-memory/SKILL.md',
}

# section titles in output order (HEADER, skills..., FOOTER)
ORDER = ['ponytail', 'caveman', 'unslop', 'codebase-memory']
TITLES = {
    'ponytail': 'Ponytail',
    'caveman': 'Caveman policy',
    'unslop': 'Unslop',
    'codebase-memory': 'Codebase memory',
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
    # unslop continued: soul section + puffery/name-dropping
    ('unslop', 'Edit text to remove AI patterns.',
     'Edit text to remove AI patterns and add human voice.'),
    ('unslop', '2. Rewrite. Preserve meaning, match intended tone.',
     '2. Rewrite. Preserve meaning, match intended tone.\n3. Add soul (see next section).\n4. Self-audit: "What makes this obviously AI generated?" Fix remaining tells.\n\n### Adding soul\n\nRemoving patterns is half the job. Sterile, voiceless writing is just as obvious.\n\n- **Have opinions.** React to facts instead of neutrally listing pros and cons.\n- **Vary rhythm.** Short sentences. Then longer ones that take their time. Mix it up.\n- **Acknowledge complexity.** "Impressive but also kind of unsettling" beats "impressive."\n- **Use "I" when it fits.** First person isn\'t unprofessional.\n- **Let some mess in.** Perfect structure looks machine-made.\n- **Be specific.** Not "this is concerning" but "there\'s something unsettling about agents churning away at 3am."'),
    ('unslop', 'Rule numbers are stable ids that other skills cite. A removed rule leaves a gap.\n\n#### Content',
     '#### Content\n\n1. **Puffery.** "pivotal moment", "testament to", "evolving landscape", "setting the stage for", "indelible mark", "deeply rooted". Cut puffery, state what happened.\n2. **Name-dropping.** Listing media outlets without context. Pick one, say what was said.'),
    ('codebase-memory', 'trace_path(direction="inbound")',
     'trace_path(project="...", function_name="X", direction="inbound")'),
    ('codebase-memory', 'trace_path(direction="outbound")',
     'trace_path(project="...", function_name="X", direction="outbound")'),
    ('codebase-memory', 'trace_path(direction="both")',
     'trace_path(project="...", function_name="X", direction="both", depth=3)'),
    ('codebase-memory', 'search_graph(name_pattern="...")',
     'search_graph(project="...", name_pattern="...")'),
    ('codebase-memory', 'detect_changes()', 'detect_changes(project="...")'),
    ('codebase-memory', 'trace_path(risk_labels=true)',
     'trace_path(project="...", function_name="X", risk_labels=true)'),
    ('codebase-memory', 'search_graph(label="Function", name_pattern=".*Pattern.*")',
     'search_graph(project="...", label="Function", name_pattern=".*Pattern.*")'),
    ('codebase-memory', 'get_code_snippet(qualified_name="project.path.FuncName")',
     'get_code_snippet(project="...", qualified_name="project.path.FuncName")'),
    ('codebase-memory', 'search_graph(name_pattern=".*FuncName.*")',
     'search_graph(project="...", name_pattern=".*FuncName.*")'),
    ('codebase-memory', 'trace_path(function_name="FuncName", direction="both", depth=3)',
     'trace_path(project="...", function_name="FuncName", direction="both", depth=3)'),
    ('codebase-memory', 'search_graph(max_degree=0, exclude_entry_points=true)',
     'search_graph(project="...", max_degree=0, exclude_entry_points=true)'),
    ('codebase-memory', 'search_graph(min_degree=10, relationship="CALLS", direction="outbound")',
     'search_graph(project="...", min_degree=10, relationship="CALLS", direction="outbound")'),
    ('codebase-memory', 'search_graph(min_degree=10, relationship="CALLS", direction="inbound")',
     'search_graph(project="...", min_degree=10, relationship="CALLS", direction="inbound")'),
]

DELETIONS = [
]


def load(name, path):
    raw = path.read_text().split('---', 2)[2].strip()
    has_h1 = bool(re.match(r'(?m)^# [^\n]+', raw))
    body = re.sub(r'(?m)^#(#{0,5}) ', r'##\1 ', raw)  # demote one level
    if name == 'codebase-memory':
        # your edition uses sentence case; upstream uses Title Case
        for src, dst in {'Quick Decision Matrix': 'Quick decision matrix',
                         'Exploration Workflow': 'Exploration workflow',
                         'Tracing Workflow': 'Tracing workflow',
                         'Evidence Tiers': 'Evidence tiers',
                         'Sessions and Subagents': 'Sessions and subagents',
                         'Quality Analysis': 'Quality analysis',
                         '15 MCP Tools': '15 MCP tools',
                         'Edge Types': 'Edge types',
                         'Cypher Examples': 'Cypher examples'}.items():
            body = body.replace(f'### {src}', f'### {dst}')
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
