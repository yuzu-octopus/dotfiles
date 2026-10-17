# Global agent context

## Workflow

- Execution default; ASK at ambiguity
- Batch phases: implement → tests → review → run once
- One agenda per turn
- Delete over add, boring over clever
- Subagent routing: scout (broad search) → researcher (external research) → reviewer / security-reviewer (code review) → sonic (mechanical) → task (default implementation)
- Tool defaults: Python 3.15 via uv; Bun/TS for web

## MCP routing (by task, no global order)

- Library docs: context7
- PDFs, Office docs, images, document URLs: mineru `parse_documents` first
- Authenticated app actions (Gmail, Drive, GitHub, etc.): composio; never web research
- Code structure (callers, callees, data flow, impact, dead code): `scout` subagent, or `ast_grep` for syntax shapes; `grep` for literal text only
- Interactive browser (click, forms, login, dynamic pages): tinyfish automation tools only, never for search
- Web search + page fetch: tinyfish `search`/`fetch_content`; complex pipelines or data shaping: `eval` (py/js kernel) or `jq`

## Research (6-question shootout, 2026-09-19)

- Library/framework API, known package → context7 first (resolve ID, query per concept). Official examples, no ranking gamble. Useless for current events.
- Composed answer with code/synthesis → native `web_search` (tinyfish provider 3rd in chain, sources-only; synthesis comes from model-backed providers ahead).
- First-pass retrieval breadth → `codex-search` (won breadth 6/6; free, zero GPT inference). Needs `CODEX_ACCESS_TOKEN`, else auth error.
- Multi-hop, answer-inside-page (changelogs, version tables, crawls) → `codex-research` (search+open+find+click; 3-5x context cost).
- Depth per page → exa (`xd://mcp__mcp_pool_exa_web_search_exa` then `xd://mcp__mcp_pool_exa_web_fetch_exa` on best URLs).
- Domain-pinned docs → tavily (`include_domains` + `search_depth: advanced`). Note: `exact_match` hard-errors without inner quotes.
- Code/GitHub corpus → firecrawl `categories: ["developer"]`. News vertical needs tight queries (vague returns empty).
- Tinyfish: `tinyfish_search` for current/general/known-error queries (compact); weak at domain-constrained and freshness-ranked (`include_domains`/`after_date` advisory). Automation tools for interactive browser only, never search.
- Fallback chain: context7 → codex-search/codex-research → web_search → mcp-pool (exa/tavily/firecrawl) → skill://deep-research (multi-source cited reports).
