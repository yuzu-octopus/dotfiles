---
name: deep-research
description: Deep research on any topic using parallel sub-agents with web search. Use when user asks for thorough multi-source investigation with cited report. NOT for simple lookups (single search suffices) or academic literature surveys.
---

# Deep Research

Orchestrate parallel research, then write ONE coherent cited report. Research parallel; writing single-point — never let multiple agents write report sections.

**Primary sources only.** Every claim trace to owner: official docs, source code, specs, first-party APIs, original data. Never secondary write-up, blog summarizing blog, summary of summary. Deliverable: auditable citation chain, not opinion.

## Output style

Two tiers:

- **Internal evidence — caveman full.** Findings files and worker summaries: caveman full, follow Caveman Policy (RULES.md), level full. Token-efficient scratch state; compress prose, never facts. Every finding item: fact, source URL, fetch date, confidence. No filler.
- **User-facing report — default caveman (lite).** Final `REPORT.md` synthesis: default level from RULES.md (lite) — professional but tight. This is the deliverable the user reads. Structure markers (## headings, tables, citations, code paths) stay normal in both tiers.

## Tools

Tool choice per RULES.md → Research priority. Default set:

| Job | Best Tool | Call Method |
|---|---|---|
| Quick factual verification / recent news | `tavily__tavily_search` | `xd://mcp__mcp_pool_tavily_tavily_search` |
| Broad keyword / site-specific search | `web_search` | native tool (`query: "..."`) |
| Semantic / technical docs / conceptual recall | `exa__web_search_exa` | `xd://mcp__mcp_pool_exa_web_search_exa` |
| Broad discovery / competitive landscape | `codex-search` | `xd://codex-search` (`{query: "..."}`) |
| Iterative research / page exploration | `codex-research` | `xd://codex-research` |
| Academic papers / preprint deep dive | `firecrawl_research_search_papers` | `xd://mcp__mcp_pool_firecrawl_firecrawl_research_search_papers` |
| GitHub repos / source code specs | `firecrawl_research_search_github` | `xd://mcp__mcp_pool_firecrawl_firecrawl_research_search_github` |
| Deep page / article markdown scrape | `firecrawl__firecrawl_scrape` | `xd://mcp__mcp_pool_firecrawl_firecrawl_scrape` |
| Clean page fetch | `exa__web_fetch_exa` or `read` | `xd://mcp__mcp_pool_exa_web_fetch_exa` or `read <url>` |
| PDF whitepapers / specs / benchmarks | `mineru_parse_documents` | `xd://mcp__mineru_parse_documents` |

Match tool to angle type. Always extract to primary sources.

## Step 0 — Always first (Main)

1. `date +%Y-%m-%d` via bash. Never assume year from training data.
2. Triage:
   - Answerable with 1-2 searches? → STOP, use mcp-pool direct. Not this skill.
   - Enumeration (N items × M fields)? → still this skill, table decomposition (one worker per item batch).
   - Open-ended investigation? → continue.
3. Pick depth (default **standard**; user can override):

| Mode | Workers (round 1) | Max follow-up rounds | Sources target |
|---|---|---|---|
| quick | 2-3 | 0 | 8+ |
| standard | 3-5 | 1 | 15+ |
| deep | 5-8 | 2 | 25+ |

## Step 0.5 — Route

- **quick**, or `researcher` agent unavailable → run all phases inline (Main does Steps 1-6 below directly).
- **standard / deep** with `researcher` available → Main dispatches ONE background task: `{agent: "researcher", task: "<topic> + depth + user constraints + today's date"}` and relays the report path when it yields. Main does no further research work.

## Step 1 — Scope

Ask at most one round via `ask` (Main only — subagents cannot ask), only if genuinely ambiguous: audience, time frame, region, decision at stake. Intent clear? Skip asking, write assumptions into brief instead.

Then write `docs/research/<slug>/brief.md`:

- **Question** — refined.
- **Decision** — what choice does this inform? "Postgres or MongoDB" unanswerable; "which fits a write-heavy event log, SQL-fluent team" answerable.
- **Answer form** — recommendation / comparison table / number / yes-no.
- **Scope** — in/out boundaries. **Assumptions** — written, never blocking. **Depth mode**. **Date**.

Sharpened question materially different from what the user asked? Confirm before spending the effort (Main only).

## Step 2 — Plan

Decompose brief into 3-8 **independent** angles. Lenses: core facts/definitions · recent developments · quantitative data/benchmarks · counter-arguments & failure cases · practitioner experience (forums, issues) · community discourse (threads, practitioner chatter) · academic work · key players/alternatives.

Counter-angle queries use failure-mode patterns: `"X problems"`, `"migrating away from X"`, `"X postmortem"` — critical sources are underrepresented because vendors publish more than victims.

**Size trigger.** Count angles after decomposition. At 12 or fewer, dispatch flat (Step 3a). Above 12, group into 2–4 clusters by affinity and note the grouping in the brief under `## Clusters`; dispatch goes through managers (Step 3b). Twelve leaves headroom: follow-up rounds add angles, and the trigger fires before the coordinator's context becomes the bottleneck, not after. The researcher applies this at runtime — it is not a user-facing mode.

## Step 3a — Parallel research (flat, default)

Spawn one worker per angle in **single `task` call** (parallel). Template:

```
Investigate ONE angle. Output caveman full — follow Caveman Policy (RULES.md), level full.

Think what you know → search → observe results → search again for gaps.

**CRITICAL — Primary sources only.** Read official docs, source code, specs, first-party APIs, original data. Never cite secondary blog, summarizing article, forum hearsay when primary exists. Secondary only → mark secondary in confidence. Before marking secondary: one extra search MUST attempt to locate underlying primary. Ten blogs repeating one benchmark are ONE source — trace to origin.

**Data integrity:** never estimate or simulate numbers. Every statistic carries source URL. Unverifiable → report as "unverified", never omit silently.

Tools available:
- Tavily (`xd://mcp__mcp_pool_tavily_tavily_search`) — current news & structured facts
- Built-in `web_search` — Google-style search with site:/filetype:/intitle:
- Exa (`xd://mcp__mcp_pool_exa_web_search_exa` & `exa_web_fetch_exa`) — semantic search & clean markdown fetch
- Codex (`xd://codex-search` & `xd://codex-research`) — fast breadth search & iterative browser research
- Firecrawl (`firecrawl_scrape`, `firecrawl_research_search_papers`, `firecrawl_research_search_github`) — clean scrapes, arXiv/paper searches, repo discovery
- MinerU (`xd://mcp__mineru_parse_documents`) — PDF/spec/image parsing
- Direct `read <url>` — instant webpage reading
- Gossip script (`~/.omp/agent/scripts/gossip.py`) — community discourse: Reddit, HN threads, YouTube transcripts, arXiv, GitHub, Polymarket, RSS. Practitioner-experience and community-discourse angles use this first; `{agent: "gossip"}` for a dedicated discourse sweep returning consensus/disagreement/gaps.

You are a worker. Never spawn subagents.

Angle: {angle from brief}
Question: {specific question}
Depth: {quick/standard/deep}

Write findings to findings/<N>.md on disk:
## Angle
## Claims (claim / source URL / fetch date / confidence per item — confidence: primary > secondary > speculative)
## Searches (query strings used)
## Conflicting evidence
## Gaps

Return 3-5 line caveman summary only.
```

Each worker: ONE angle only; findings to `findings/F<N>.md`; return 3-5 caveman lines. Fail or thin results → note, move on; do not block other angles.

## Step 3b — Clustered research (triggered, angles above 12)

Dispatch one `task` agent per cluster from the brief's `## Clusters`. Managers
merge and reconcile a cluster; they do no independent research and never write
the report. Template:

```
Own ONE cluster of angles. You may spawn workers via `task`, one per angle in
this cluster — nothing else. Output caveman full.

For each angle: dispatch worker, collect its findings file, note conflicts
within the cluster and which source wins and why (conditions / definitions /
stale / wrong). Merge surviving claims into `findings/C<N>.md` with the same
shape as a worker file (Claims / Searches / Conflicting evidence / Gaps),
plus a `## Cluster verdict` of 3-5 lines.

You are a leaf-merger, not a researcher. Never search independently; every
claim traces to a worker's findings file. Never spawn beyond one level —
your workers are leaves.

Return the cluster verdict only, 3-5 lines.
```

One angle per worker still holds: a manager dispatches the same worker
template from Step 3a, scoped to its cluster. Workers stay leaves — at
depth 3 they lose `task` anyway, which enforces it mechanically.

Flat runs and manager runs are disjoint: the trigger fires strictly before
first dispatch. A worker already dispatched flat is never promoted.

## Step 4 — Reflect (gap check)

Read all `findings/*.md`. Against `brief.md`:

- Parts with no evidence? → targeted re-dispatch, narrower angle, explicit "find the primary source".
- Major claims on single source? → corroboration dispatch.
- **Conflicts → reconciliation dispatch** (dedicated worker): input = both claims + sources. Job: which source wins and why (different conditions / different definitions / stale / one wrong — state which), what claim to carry forward. Never smooth over with "opinions differ" — the boundary between two right answers is often the real answer.
- Same sources returning repeatedly? → angle saturated, stop it.
- **Step repetition.** One angle per worker — never two workers on overlapping angles. Dedupe sources before dispatch, stop saturated angles immediately. Repetition is the top observed failure mode; every duplicate finding costs context and adds no evidence.

**Acceptance gate (per file, before synthesis).** Each findings or cluster file
must carry sources, fetch dates, and confidence tags on major claims. Any file
missing them goes back for re-dispatch, not into the gaps section. Per-source
verification beats end-of-report checks; a missing citation found here costs a
worker round, found later costs the report.

Follow-up budget: 1 round (standard), 2 (deep). Budget done or coverage sufficient → proceed. Record unresolved gaps → report's "Open questions".

**Quality gate — ALL must pass before synthesis:**
- ☐ Every brief facet investigated (not just encountered)
- ☐ Major claims: 2+ independent sources
- ☐ Conflicts reconciled with stated reasoning
- ☐ Every number carries a source
- ☐ No major gaps

Any unchecked → more workers. Do NOT synthesize early.

## Step 5 — Write (single-point)

You alone write `docs/research/<slug>/REPORT.md` in one pass. Prose: default caveman (lite) — user-facing deliverable, not internal scratch. Structure:

```markdown
# <Question>

**Answer:** conclusion in 2-3 sentences, up front.
**Confidence:** high / medium / low + what drives it.

## Why
Reasoning, evidence attached to each step. [n]

## What would change this
The specific finding that would flip the conclusion.

## Considered and rejected
Alternatives and the specific reason each lost.

## Findings
Detailed sections per theme/angle.

## Open questions
What is still unknown, what it would take to resolve.

## Sources
Numbered, URL, access date, [primary]/[secondary] tag, grouped by weight.
```

Rules:

- Every non-obvious claim carries inline citation `[n]` → Sources section. URLs only from findings files — never memory.
- Sources conflict → present both sides + dates; prefer newer + primary.
- Tag every citation: `[primary]`, `[secondary]`, or `[speculative]`.
- Single-source claims → `[single source]`. Speculation → `[speculative]`.
- Major claim confidence: high = 2+ independent primary; medium = single authoritative; low = single/conflicted. State it.
- A reader who stops after the Answer paragraph still has the conclusion.

## Step 6 — Verify (deep mode only)

Reread REPORT.md as a skeptic. For each major claim:

- Does its `[n]` actually support the claim (not just exist)?
- Any URL fabricated or dead? Any quote distorted?
- Any claim that should be cited but isn't?
- Conflicts surfaced, not buried?

Fix in place. One pass.

Finally: 5-10 line summary of key conclusions + report path, default caveman (lite).

## When NOT to use

- Simple lookup → mcp-pool direct
- Quick fact check → mcp-pool
- Sources sufficient → synthesize direct
