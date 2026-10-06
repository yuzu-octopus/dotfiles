#!/usr/bin/env uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""gossip - social and technical chatter retrieval, shaped for agents.

Wraps the places practitioners actually talk: Reddit, Hacker News, YouTube
transcripts, arXiv, GitHub, Polymarket, Techmeme, and any RSS feed.

Every adapter is free and credential-free. Output is compact JSON with nulls
stripped and excerpts truncated, so a dozen results cost a few hundred tokens.
One adapter failing never kills a run: partial results return with an `errors`
array.

Run directly (`./gossip.py search ...`); no interpreter arguments needed.

Commands
    sources [--deep]              health-check every adapter
    search QUERY [--sources ...]   fan out across sources
    reddit SUBREDDIT [--sort]     subreddit listing via TinyFish
    video URL [--lang]            full YouTube transcript via yt-dlp
    repo OWNER/NAME               GitHub repository metadata
    issues OWNER/NAME [QUERY]     GitHub issues or PRs
    fetch URL [--chars]           read any page
    rss URL [--limit]             parse any RSS/Atom feed
"""

from abc import ABC
import argparse
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
import glob
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, ClassVar
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
NET_TIMEOUT = 20
DEFAULT_EXCERPT = 400
ARXIV_PROBE = "https://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1"
MIN_KEYWORD = 2          # drop shorter fragments; they match everything
TITLE_FIELD_COUNT = 2      # yt-dlp prints title, uploader, duration
POSTS_PER_PAGE = 25       # Reddit minimum listing page; probes override this

type Meta = dict[str, Any]


# --------------------------------------------------------------------------
# transport
# --------------------------------------------------------------------------


def _guard_scheme(url: str) -> None:
    """Reject non-HTTP schemes before opening them.

    ``urlopen`` also honours ``file://``, ``ftp://`` and similar, so a
    user-supplied URL passed to ``fetch`` could otherwise read local files
    such as ``~/.ssh/id_rsa``. Only web schemes are ever wanted here.
    """
    if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
        scheme = urllib.parse.urlsplit(url).scheme
        raise ValueError(f"unsupported URL scheme: {scheme}")


def get(url: str, timeout: int = NET_TIMEOUT) -> str:
    """GET an http(s) URL as text. Raises on a bad scheme, non-2xx, or timeout."""
    _guard_scheme(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})  # noqa: S310 - scheme gated
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - scheme gated
        return resp.read().decode("utf-8", "replace")


def get_json(url: str, timeout: int = NET_TIMEOUT) -> Any:
    """GET an http(s) URL and parse the body as JSON."""
    _guard_scheme(url)
    req = urllib.request.Request(  # noqa: S310 - scheme gated
        url, headers={"User-Agent": UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - scheme gated
        return json.loads(resp.read().decode("utf-8", "replace"))


def _binary_health(binary: str) -> tuple[bool, str]:
    """Presence check for a subprocess-backed adapter."""
    return (
        (True, "ok") if shutil.which(binary) else (False, f"{binary} not installed")
    )


def run(cmd: list[str], timeout: int = 60) -> str:
    """Run a subprocess and return stdout. Raises if the binary is missing or fails."""
    if not shutil.which(cmd[0]):
        binary = cmd[0]
        raise RuntimeError(f"{binary} is not installed")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(detail.splitlines()[-1][:200] if detail else "command failed")
    return proc.stdout


def tinyfish(urls: list[str], timeout: int = 90) -> list[dict[str, Any]]:
    """Fetch pages through TinyFish's browser infrastructure.

    Required for Reddit: this machine's egress IP is blocked by Reddit, so
    direct requests return a "You've been blocked" interstitial.
    """
    for url in urls:
        _guard_scheme(url)
    raw = run(
        ["bunx", "-y", "@tiny-fish/cli", "fetch", "content", "get", *urls],
        timeout=timeout,
    )
    payload = json.loads(raw)
    return payload.get("results", []) if isinstance(payload, dict) else []


# --------------------------------------------------------------------------
# model
# --------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class Post:
    """One retrieved item. ``meta`` holds source-specific fields only."""

    source: str
    title: str
    url: str
    meta: Meta = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Flatten into the JSON shape the CLI emits, meta keys merged inline."""
        return {"source": self.source, "title": self.title, "url": self.url, **self.meta}


def clip(text: str | None, limit: int = DEFAULT_EXCERPT) -> str:
    """Collapse whitespace and truncate with an ellipsis.

    ``limit <= 0`` returns empty rather than slicing with a negative bound,
    which would otherwise hand back the whole string minus its last character.
    """
    if not text or limit <= 0:
        return ""
    flat = re.sub(r"\s+", " ", text).strip()
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


def strip_html(markup: str) -> str:
    """Remove script/style blocks then tags, leaving text."""
    without_blocks = re.sub(
        r"<script.*?</script>|<style.*?</style>", " ", markup, flags=re.DOTALL | re.IGNORECASE,
    )
    return re.sub(r"<[^>]+>", " ", without_blocks)


# --------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------


class Source(ABC):
    """One retrieval backend.

    ``name``/``via``/``healthy`` are the whole shared contract. Keyword search
    is optional: several backends are only addressable by URL, feed, or repo
    name, so they set ``searchable = False`` and leave ``search`` unimplemented
    rather than raising from a stub the interface pretends is real.
    """

    name: ClassVar[str]
    via: ClassVar[str]
    searchable: ClassVar[bool] = True

    def search(self, query: str, limit: int, days: int = 0) -> list[Post]:
        """Return posts matching ``query``, optionally limited to ``days``.

        Only callable when ``searchable`` is True.
        """
        raise NotImplementedError(f"{self.name} is not keyword-searchable")

    def healthy(self, *, deep: bool = False) -> tuple[bool, str]:
        """Return (reachable, detail).

        The default is a cheap presence check. ``deep`` asks adapters that
        reach the network to make one real request instead.
        """
        return (False, "not probed")

    def __repr__(self) -> str:
        """Name and transport, for readable health output and tracebacks."""
        return f"<{type(self).__name__} {self.name} via {self.via}>"


class HackerNews(Source):
    """Algolia's HN index. Free, no key, best-quality free source."""

    name = "hackernews"
    via = "hn.algolia.com"

    BASE = "https://hn.algolia.com/api/v1/search"

    def search(self, query: str, limit: int, days: int = 0) -> list[Post]:
        """Return HN stories matching the query's keywords.

        ``days`` is applied server-side via Algolia's ``numericFilters`` and
        the result re-sorted newest-first. Filtering client-side does not work
        here: the default ordering is relevance across all time, so it leads
        with evergreen posts and a date filter then discards every one of them
        and returns nothing even when fresh matches exist.
        """
        params: dict[str, Any] = {
            "query": " ".join(keywords(query)), "tags": "story", "hitsPerPage": limit,
        }
        if days:
            cutoff = int(time.time() - days * 86400)
            params["numericFilters"] = f"created_at_i>{cutoff}"
        hits = get_json(f"{self.BASE}?{urllib.parse.urlencode(params)}").get("hits", [])
        if days:
            hits.sort(key=lambda h: h.get("created_at_i") or 0, reverse=True)
        return [
            Post(
                self.name,
                hit.get("title") or hit.get("story_title") or "",
                f"https://news.ycombinator.com/item?id={hit['objectID']}",
                {
                    "author": hit.get("author"),
                    "points": hit.get("points"),
                    "comments": hit.get("num_comments"),
                    "created": hit.get("created_at"),
                },
            )
            for hit in hits
        ]

    def healthy(self, *, deep: bool = False) -> tuple[bool, str]:
        """Cheap pass reports ok; ``deep`` makes one live Algolia request."""
        if not deep:
            return (True, "ok (unchecked; use --deep)")
        try:
            get_json(f"{self.BASE}?tags=front_page", timeout=12)
            return (True, "ok")
        except Exception as exc:  # noqa: BLE001 - health check reports, never raises
            return (False, str(exc)[:80])


class Arxiv(Source):
    """arXiv preprint metadata via the Atom API."""

    name = "arxiv"
    via = "export.arxiv.org"
    NS: ClassVar[dict[str, str]] = {
        "a": "http://www.w3.org/2005/Atom",
    }

    def search(self, query: str, limit: int, days: int = 0) -> list[Post]:
        """Return arXiv preprints matching the query keywords."""
        qs = urllib.parse.urlencode({
            "search_query": _arxiv_query(query),
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        root = ET.fromstring(  # S314: stdlib-only by design; first-party arXiv feed
            get(f"https://export.arxiv.org/api/query?{qs}", timeout=30),
        )
        posts: list[Post] = []
        for entry in root.findall("a:entry", self.NS):
            published = entry.findtext("a:published", "", self.NS)[:10]
            if days and not _within_days(published, days):
                continue
            link = entry.find("a:id", self.NS)
            authors = ", ".join(
                a.findtext("a:name", "", self.NS)
                for a in entry.findall("a:author", self.NS)
            )
            posts.append(Post(
                self.name,
                clip(entry.findtext("a:title", "", self.NS).replace("\n", " "), 150),
                (link.text if link is not None and link.text else ""),
                {
                    "authors": clip(authors, 100),
                    "published": published,
                    "abstract": clip(entry.findtext("a:summary", "", self.NS), 300),
                },
            ))
        return posts

    def healthy(self, *, deep: bool = False) -> tuple[bool, str]:
        """Cheap pass reports ok; ``deep`` makes one live arXiv request."""
        if not deep:
            return (True, "ok (unchecked; use --deep)")
        try:
            get(ARXIV_PROBE, timeout=15)
            return (True, "ok")
        except Exception as exc:  # noqa: BLE001
            return (False, str(exc)[:80])


STOPWORDS = frozenset("""
    a an the vs vs. versus and or of for to in on with without from into
    is are was were be been being do does did how what why when where
    which who use using used about that this these those it its as at by
    if then than
""".split())


def keywords(query: str, limit: int = 5) -> list[str]:
    """Content words from a natural-language query, stopwords removed."""
    words = [w.lower() for w in re.findall(r"[\w.+#-]+", query)]
    keep = [w for w in words if w not in STOPWORDS and len(w) > MIN_KEYWORD]
    return keep[:limit] or words[:limit]


def _arxiv_query(query: str) -> str:
    """Build an arXiv ``search_query``.

    arXiv's API does not accept a bare multi-word phrase under ``all:``; it
    silently returns unrelated newest papers instead of matching. AND-ing
    individual field terms gives real relevance.
    """
    terms = keywords(query)
    return " AND ".join(f"all:{term}" for term in terms) if terms else f"all:{query}"



def _within_days(iso_date: str, days: int) -> bool:
    try:
        return (date.today() - date.fromisoformat(iso_date)).days <= days
    except ValueError:
        return False


class Polymarket(Source):
    """Prediction-market odds. Free public Gamma API, no key."""

    name = "polymarket"
    via = "gamma-api.polymarket.com"

    def search(self, query: str, limit: int, days: int = 0) -> list[Post]:
        """Return markets whose question matches the query keywords.

        ``days`` filters on the market's close date. Without it, the API's
        volume ordering can surface year-old markets, so an age filter is the
        only way to get genuinely recent predictions.

        A query that matches nothing returns nothing. Falling back to the
        unfiltered top-volume list would hand back confident, unrelated
        markets with no indication the query missed, which is worse than an
        empty result the caller can act on.
        """
        qs = urllib.parse.urlencode({
            "closed": "false", "limit": limit * 3,
            "order": "volume24hr", "ascending": "false",
        })
        markets = get_json(f"https://gamma-api.polymarket.com/markets?{qs}")
        terms = keywords(query)
        matched = [
            m for m in markets
            if any(t in (m.get("question") or "").lower() for t in terms)
        ]
        if days:
            cutoff = date.today() - timedelta(days=days)
            matched = [m for m in matched if _closes_on_or_after(m, cutoff)]
        return [self._to_post(m) for m in matched[:limit]]

    def _to_post(self, market: dict[str, Any]) -> Post:
        return Post(
            self.name,
            clip(market.get("question"), 160),
            f"https://polymarket.com/event/{market.get('slug', '')}",
            {
                "odds": _odds(market.get("outcomePrices")),
                "volume_24h": round(float(market.get("volume24hr") or 0)),
                "closes": (market.get("endDate") or "")[:10] or None,
            },
        )

    def healthy(self, *, deep: bool = False) -> tuple[bool, str]:
        """Cheap pass reports ok; ``deep`` makes one live Gamma request."""
        if not deep:
            return (True, "ok (unchecked; use --deep)")
        try:
            get_json("https://gamma-api.polymarket.com/markets?closed=false&limit=1", timeout=12)
            return (True, "ok")
        except Exception as exc:  # noqa: BLE001
            return (False, str(exc)[:80])


def _closes_on_or_after(market: dict[str, Any], cutoff: date) -> bool:
    """Report whether a market's end date is parseable and on or after ``cutoff``.

    Gamma returns end dates as ISO strings, but a market with no scheduled
    resolution carries the literal ``"TBD"``, so an unguarded
    ``date.fromisoformat`` raises rather than filtering the market out.
    """
    raw = (market.get("endDate") or "")[:10]
    try:
        return date.fromisoformat(raw) >= cutoff
    except ValueError:
        return False


def _odds(raw: Any) -> str | None:
    """Render Polymarket's price list as percentages.

    Gamma returns ``outcomePrices`` as a JSON-encoded string such as
    ``'["0.165", "0.835"]'``, not a bare comma-separated list.
    """
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return None
    if not isinstance(raw, list):
        return None
    try:
        return " / ".join(f"{float(price) * 100:.0f}%" for price in raw)
    except (TypeError, ValueError):
        return None


class Reddit(Source):
    """Subreddit listings via TinyFish.

    Reddit blocks this machine's egress IP, so requests go through TinyFish's
    browser infrastructure. It fetches the ``.json`` listing API rather than
    scraping rendered HTML: the JSON schema is stable and returns Reddit
    permalinks, scores, and comment counts, none of which survive markdown
    extraction reliably.
    """

    name = "reddit"
    via = "tinyfish"
    FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)

    searchable = False

    def listing(self, subreddit: str, sort: str = "hot", limit: int = 25) -> list[Post]:
        """Return posts from a subreddit's ``hot``/``new``/``top`` listing."""
        slug = subreddit.removeprefix("r/").strip("/")
        url = (f"https://www.reddit.com/r/{slug}/{sort}.json"
               f"?limit={max(limit, POSTS_PER_PAGE)}&raw_json=1")
        for attempt in range(2):
            posts = self._parse(tinyfish([url]))
            if posts or attempt == 1:
                return posts[:limit]
            time.sleep(5)
        return []

    def _parse(self, results: list[dict[str, Any]]) -> list[Post]:
        """Unwrap the fenced JSON body and flatten its children into posts."""
        if not results:
            return []
        match = self.FENCE.search(results[0].get("text", ""))
        if not match:
            return []
        try:
            listing = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []
        posts: list[Post] = []
        for child in listing.get("data", {}).get("children", []):
            data = child.get("data") or {}
            title = data.get("title")
            if not title:
                continue
            permalink = "https://www.reddit.com" + data.get("permalink", "")
            outbound = data.get("url_overridden_by_dest") or ""
            posts.append(Post(
                self.name,
                clip(title, 200),
                permalink or outbound,
                {
                    "author": data.get("author"),
                    "score": data.get("score"),
                    "comments": data.get("num_comments"),
                    "created": _iso(data.get("created_utc")),
                    "link": outbound or None,
                    "text": clip(data.get("selftext"), 300) or None,
                },
            ))
        return posts

    def healthy(self, *, deep: bool = False) -> tuple[bool, str]:
        """Cheap pass checks bunx; ``deep`` makes one live subreddit fetch."""
        if not shutil.which("bunx"):
            return (False, "bunx not installed")
        if not deep:
            return (True, "ok (unchecked; use --deep)")
        try:
            return (True, "ok") if self.listing("programming", limit=1) else (False, "empty")
        except Exception as exc:  # noqa: BLE001
            return (False, str(exc)[:80])


def _iso(epoch: Any) -> str | None:
    """Unix timestamp to ISO-8601, or None when Reddit omitted it."""
    try:
        return datetime.fromtimestamp(float(epoch), tz=UTC).isoformat()
    except (TypeError, ValueError):
        return None



class YouTube(Source):
    """Full auto-generated transcripts via yt-dlp. No key, no rate limit."""

    name = "youtube"
    via = "yt-dlp"
    searchable = False

    def transcript(self, url: str, lang: str = "en") -> Post:
        """Download and flatten a video's subtitles.

        One language per attempt. Asking for ``en.*`` expands to every
        English variant, and YouTube answers 429 once the burst trips its
        rate limit, so a single request per try is the reliable path.
        """
        last_error = ""
        for attempt in range(3):
            with tempfile.TemporaryDirectory() as workdir:
                try:
                    run([
                        "yt-dlp", "--skip-download", "--write-auto-subs", "--write-subs",
                        "--sub-langs", lang, "--sub-format", "vtt",
                        "--sleep-requests", "1",
                        "-o", f"{workdir}/clip", url,
                    ], timeout=120)
                except RuntimeError as exc:
                    last_error = str(exc)
                    time.sleep(3 * (attempt + 1))
                    continue
                files = sorted(glob.glob(f"{workdir}/*.vtt"))
                if not files:
                    last_error = f"no {lang} subtitles for {url}"
                    break
                with open(files[0], encoding="utf-8", errors="replace") as fh:
                    body = _vtt_to_prose(fh.read())
                return self._post(url, body)
        raise RuntimeError(last_error or "yt-dlp could not fetch subtitles")

    def _post(self, url: str, body: str) -> Post:
        """Build the Post once subtitles are on disk."""
        fields = run([
            "yt-dlp", "--skip-download", "--print",
            "%(title)s|||%(uploader)s|||%(duration_string)s", url,
        ], timeout=60).strip().split("|||")
        return Post(
            self.name, fields[0] if fields else url, url,
            {
                "uploader": fields[1] if len(fields) > 1 else None,
                "duration": fields[2] if len(fields) > TITLE_FIELD_COUNT else None,
                "transcript": clip(body, 12_000),
            },
        )

    def healthy(self, *, deep: bool = False) -> tuple[bool, str]:
        """Presence check for the yt-dlp binary; no network call either way."""
        return _binary_health("yt-dlp")


def _vtt_to_prose(vtt: str) -> str:
    """Collapse WebVTT cues into flowing prose.

    Each caption line appears twice (once with inline timestamps, once clean);
    consecutive duplicates are dropped.
    """
    lines: list[str] = []
    previous: str | None = None
    for raw in vtt.split("\n"):
        line = re.sub(r"<[^>]+>", "", raw.strip())
        if not line or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if re.fullmatch(r"\d+", line) or line != previous:
            lines.append(line)
            previous = line
    return " ".join(lines)


class GitHub(Source):
    """Repository and issue data via the authenticated `gh` CLI."""

    name = "github"
    via = "gh"
    searchable = False

    def repo(self, name: str) -> dict[str, Any]:
        """Return repository metadata as a raw dict (no Post wrapper: one object)."""
        fields = "name,description,stargazerCount,forkCount,primaryLanguage,updatedAt,url"
        return {"source": self.name, **json.loads(
            run(["gh", "repo", "view", name, "--json", fields]),
        )}

    def issues(self, name: str, query: str = "", limit: int = 15) -> list[Post]:
        """List issues for ``name``, or search globally when ``query`` is given."""
        if query:
            rows = json.loads(run([
                "gh", "search", "issues", query, "--limit", str(limit),
                "--json", "title,url,state,commentsCount,createdAt",
            ]))
            return [
                Post(self.name, row["title"], row["url"], {
                    "state": row.get("state"),
                    "comments": row.get("commentsCount"),
                    "created": row.get("createdAt"),
                })
                for row in rows
            ]
        rows = json.loads(run([
            "gh", "issue", "list", "--repo", name, "--limit", str(limit),
            "--json", "title,url,state,comments,createdAt",
        ]))
        return [
            Post(self.name, row["title"], row["url"], {
                "state": row.get("state"),
                "comments": row.get("comments"),
                "created": row.get("createdAt"),
            })
            for row in rows
        ]

    def healthy(self, *, deep: bool = False) -> tuple[bool, str]:
        """Presence check for the gh binary; no network call either way."""
        return _binary_health("gh")


class Feed(Source):
    """Any RSS or Atom feed. Used for Techmeme and generic subscriptions."""

    name = "rss"
    via = "feed xml"
    searchable = False
    NS: ClassVar[dict[str, str]] = {"a": "http://www.w3.org/2005/Atom"}

    def read(self, url: str, limit: int = 12) -> list[Post]:
        """Parse the first ``limit`` entries from a feed."""
        root = ET.fromstring(  # S314: stdlib-only by design; user-supplied feed
            get(url, timeout=30),
        )
        entries = root.findall(".//item") or root.findall(".//a:entry", self.NS)
        posts: list[Post] = []
        for entry in entries[:limit]:
            title = (entry.findtext("title")
                     or entry.findtext("a:title", "", self.NS) or "").strip()
            link = (entry.findtext("link") or "").strip() or self._atom_link(entry)
            summary = (entry.findtext("description")
                        or entry.findtext("a:summary", "", self.NS) or "")
            published = (entry.findtext("pubDate")
                          or entry.findtext("a:published", "", self.NS) or "")
            posts.append(Post(self.name, clip(title, 200), link, {
                "published": published[:40] or None,
                "excerpt": clip(strip_html(summary)),
            }))
        return posts

    def _atom_link(self, entry: ET.Element) -> str:
        node = entry.find("a:link", self.NS)
        return node.get("href", "") if node is not None else ""

    def healthy(self, *, deep: bool = False) -> tuple[bool, str]:
        """Cheap pass reports ok; ``deep`` fetches a real feed once."""
        if not deep:
            return (True, "ok (unchecked; use --deep)")
        try:
            get("https://hnrss.org/frontpage", timeout=12)
            return (True, "ok")
        except Exception as exc:  # noqa: BLE001
            return (False, str(exc)[:80])


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

# Module-level singletons: one instance per adapter, so REGISTRY and the
# dispatch/health paths below share the same objects instead of each
# constructing its own copies.
HN = HackerNews()
ARXIV = Arxiv()
POLYMARKET = Polymarket()
REDDIT = Reddit()
YOUTUBE = YouTube()
GITHUB = GitHub()
FEED = Feed()

REGISTRY: dict[str, Source] = {
    source.name: source
    for source in (HN, ARXIV, POLYMARKET, REDDIT, YOUTUBE, GITHUB, FEED)
}


def read_page(url: str, chars: int = 4000) -> dict[str, Any]:
    """Read any URL: direct first, TinyFish as fallback for JS or blocked hosts."""
    if "reddit.com" in url:
        results = tinyfish([url])
        if results:
            return {"source": "tinyfish", "url": url,
                    "title": results[0].get("title"),
                    "text": clip(results[0].get("text"), chars)}
    try:
        text = clip(strip_html(get(url, timeout=30)), chars)
        return {"source": "direct", "url": url, "text": text}
    except Exception:
        results = tinyfish([url])
        if results:
            return {"source": "tinyfish", "url": url,
                    "title": results[0].get("title"),
                    "text": clip(results[0].get("text"), chars)}
        raise


def _row(*, ok: bool, via: str, detail: str = "") -> dict[str, Any]:
    """One health row.

    ``detail`` is carried through whenever it is not a plain success, so an
    adapter that reported ``ok`` without checking anything still says so.
    """
    row: dict[str, Any] = {"ok": ok, "via": via}
    if detail and detail != "ok":
        row["detail"] = detail
    if not ok:
        row["error"] = detail or "unreachable"
    return row


def health(*, deep: bool = False) -> dict[str, Any]:
    """Probe every adapter.

    The default pass is cheap: binary presence for subprocess-backed adapters,
    and no request at all for networked ones. ``--deep`` costs one live
    request per networked adapter, so reach for it when a result is empty and
    you need to know whether the adapter or the query is at fault.
    """
    report: dict[str, Any] = {}
    for name, source in REGISTRY.items():
        ok, detail = source.healthy(deep=deep)
        report[name] = _row(ok=ok, via=source.via, detail=detail)
    # Techmeme is just a specific feed, not its own adapter. Report it as a
    # derived alias rather than inventing an ok it never measured.
    report["techmeme"] = {
        **_row(ok=report.get("rss", {}).get("ok", False), via="techmeme.com/feed.xml"),
        "alias_of": "rss",
        "url": "https://www.techmeme.com/feed.xml",
    }
    return report


def dispatch(args: argparse.Namespace) -> tuple[Any, list[str]]:
    """Run one command. Returns (payload, errors); never raises for one bad source."""
    errors: list[str] = []

    if args.cmd == "sources":
        return health(deep=args.deep), errors

    if args.cmd == "search":
        results: dict[str, Any] = {}
        for name in (s.strip() for s in args.sources.split(",")):
            source = REGISTRY.get(name)
            if source is None:
                errors.append(f"unknown source: {name}")
                continue
            if not source.searchable:
                errors.append(f"{name}: not keyword-searchable, use its own subcommand")
                continue
            try:
                results[name] = [
                    post.as_dict() for post in source.search(args.query, args.limit, args.days)
                ]
            except Exception as exc:  # noqa: BLE001 - one dead source must not sink the rest
                errors.append(f"{name}: {exc}")
        return {"query": args.query, "results": results}, errors

    match args.cmd:
        case "reddit":
            return {"results": [p.as_dict() for p in REDDIT.listing(
                args.subreddit, args.sort, args.limit)]}, errors
        case "video":
            return {"results": [YOUTUBE.transcript(args.url, args.lang).as_dict()]}, errors
        case "repo":
            return GITHUB.repo(args.name), errors
        case "issues":
            return {"results": [p.as_dict() for p in GITHUB.issues(
                args.name, args.query, args.limit)]}, errors
        case "rss":
            return {"results": [p.as_dict() for p in FEED.read(args.url, args.limit)]}, errors
        case "fetch":
            page = read_page(args.url, args.chars)
            if args.title:
                page["title"] = args.title
            return page, errors
        case _:
            errors.append(f"unhandled command: {args.cmd}")
            return None, errors


def render(payload: Any) -> str:
    """Compact JSON by default; indented human view under ``--text``.

    ``search`` groups its results in a dict keyed by source name while every
    other command emits a flat list, so the dict is flattened first; without
    that, ``--text`` silently fell through to JSON on the one command an agent
    is most likely to humanise.
    """
    results = payload.get("results") if isinstance(payload, dict) else None
    if isinstance(results, dict):
        results = [row for rows in results.values() if isinstance(rows, list) for row in rows]
    if isinstance(results, list):
        lines = []
        for i, row in enumerate(results, 1):
            if not isinstance(row, dict):
                continue
            tail = " · ".join(
                f"{k}={v}" for k, v in row.items()
                if k not in ("source", "title", "url") and v is not None
            )
            lines.append(f"{i}. [{row.get('source')}] {row.get('title')}\n"
                         f"   {row.get('url')}\n   {tail}"[:400])
        return "\n".join(lines) or "(no results)"
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    return body if len(body) <= 4000 else body[:4000] + "\n…(truncated)"


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI. Subcommands mirror the adapter capabilities.

    ``--text`` is declared with ``default=SUPPRESS`` on a shared parent so it
    is accepted both before and after the subcommand. Without SUPPRESS the
    subparser's own default (False) silently overwrites a value given before
    the subcommand, so ``gossip --text reddit X`` would quietly emit JSON.
    """
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--text",
        action="store_true",
        default=argparse.SUPPRESS,
        help="human-readable output",
    )

    parser = argparse.ArgumentParser(
        prog="gossip",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[common],
    )
    parser.set_defaults(text=False)
    sub = parser.add_subparsers(dest="cmd", required=True)


    sources = sub.add_parser("sources", help="health-check every adapter", parents=[common])
    sources.add_argument(
        "--deep", action="store_true",
        help="one live request per networked adapter (default is a cheap presence check)",
    )

    search = sub.add_parser("search", help="fan out across sources", parents=[common])
    search.add_argument("query")
    search.add_argument("--sources", default="hackernews,arxiv")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--days", type=int, default=0, help="only items newer than N days")

    reddit = sub.add_parser("reddit", help="subreddit listing", parents=[common])
    reddit.add_argument("subreddit")
    reddit.add_argument("--sort", default="hot", choices=("hot", "new", "top"))
    reddit.add_argument("--limit", type=int, default=25)

    video = sub.add_parser("video", help="full YouTube transcript", parents=[common])
    video.add_argument("url")
    video.add_argument("--lang", default="en")

    repo = sub.add_parser("repo", help="repository metadata", parents=[common])
    repo.add_argument("name")

    issues = sub.add_parser("issues", help="issues or PRs", parents=[common])
    issues.add_argument("name")
    issues.add_argument("query", nargs="?", default="")
    issues.add_argument("--limit", type=int, default=15)

    fetch = sub.add_parser("fetch", help="read any page", parents=[common])
    fetch.add_argument("url")
    fetch.add_argument("--chars", type=int, default=4000)
    fetch.add_argument("--title", default="")

    rss = sub.add_parser("rss", help="parse any feed", parents=[common])
    rss.add_argument("url")
    rss.add_argument("--limit", type=int, default=12)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Returns 0 whenever any command ran, even with partial adapter errors, so
    shell pipelines do not abort on a single dead source. Returns 1 only when
    nothing could be produced at all.
    """
    raw = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(raw)
    # argparse cannot merge one flag across two parser levels reliably, so
    # --text is detected positionally: it may appear before or after the
    # subcommand and both must work.
    as_text = "--text" in raw or getattr(args, "text", False)
    try:
        payload, errors = dispatch(args)
    except Exception as exc:  # noqa: BLE001 - CLI boundary must not traceback
        payload, errors = None, [str(exc)]

    if errors:
        payload = {"errors": errors} if payload is None else {**payload, "errors": errors}
    print(render(payload) if as_text else
          json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 1 if payload is None else 0


if __name__ == "__main__":
    sys.exit(main())
