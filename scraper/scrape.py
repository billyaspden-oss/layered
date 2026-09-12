"""Find businesses worth approaching, from intent posts and trade-press signals.

Runs on a schedule (see .github/workflows/scrape.yml), appends new matches to
leads.csv, and skips items already in the file.

Sources:
  - Trade press RSS (no auth) — trigger events at named businesses
  - Bluesky (requires app password) — people describing operational problems
  - Freelancer.com, Hacker News — off by default, see config.yaml

See README.md for why signals matter more than intent for this business.
"""

from __future__ import annotations

import csv
import html
import json
import os
import re
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml
from anthropic import Anthropic

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"
LEADS_PATH = ROOT / "leads.csv"

LEADS_FIELDS = [
    "post_id",
    "source",
    "title",
    "author",
    "url",
    "created_utc",
    "score",
    "matched_query",
    "classifier_confidence",
    "classifier_reason",
    "found_at",
]

REQUEST_DELAY_SEC = 1.0
DEFAULT_UA = "layered-leadfinder/0.1 (+https://github.com/billyaspden-oss/layered)"


@dataclass
class Candidate:
    post_id: str
    source: str
    title: str
    selftext: str
    author: str
    url: str
    created_utc: float
    score: int
    matched_query: str


def load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def load_seen_ids() -> set[str]:
    if not LEADS_PATH.exists():
        return set()
    with LEADS_PATH.open() as f:
        reader = csv.DictReader(f)
        return {row["post_id"] for row in reader}


def ensure_leads_file() -> None:
    if LEADS_PATH.exists():
        return
    with LEADS_PATH.open("w", newline="") as f:
        csv.DictWriter(f, fieldnames=LEADS_FIELDS).writeheader()


def _http_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict | None = None,
    body: bytes | None = None,
) -> dict:
    merged_headers = {"User-Agent": DEFAULT_UA}
    if headers:
        merged_headers.update(headers)
    req = urllib.request.Request(url, method=method, headers=merged_headers, data=body)
    backoff = 2
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    return {}


# ----------------------------------------------------------------------
# Bluesky source
# ----------------------------------------------------------------------

def _bluesky_auth() -> str | None:
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        return None
    try:
        payload = _http_json(
            "https://bsky.social/xrpc/com.atproto.server.createSession",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"identifier": handle, "password": password}).encode(),
        )
        return payload.get("accessJwt")
    except Exception as e:
        print(f"  bluesky auth failed: {e}", file=sys.stderr)
        return None


def _bluesky_post_url(handle: str, uri: str) -> str:
    rkey = uri.rsplit("/", 1)[-1]
    return f"https://bsky.app/profile/{handle}/post/{rkey}"




# Someone describing what they built themselves is not a buyer. Checked before
# the LLM classifier to save tokens.
#
# Applies to INTENT sources only. Trade press is exempt: a news story saying a
# hotel group "built an AI" tool is a signal worth seeing, not noise, and the
# old web-design-era phrases would have silently binned exactly those items.
_DIY_SIGNALS = [
    "claude built", "chatgpt built", "built with ai", "built using ai",
    "vibe cod", "cursor built", "built my own", "built it myself",
    "built myself", "coded it myself", "i built my", "i made my own",
    "i designed my", "made it myself",
]

_INTENT_SOURCES = {"bluesky", "hackernews", "freelancer"}


def _is_diy_noise(candidate) -> bool:
    """True if the candidate is almost certainly someone's own build, not a lead."""
    if candidate.source not in _INTENT_SOURCES:
        return False
    combined = (candidate.title + " " + candidate.selftext).lower()
    return any(sig in combined for sig in _DIY_SIGNALS)

def search_bluesky(config: dict, seen: set[str]) -> list[Candidate]:
    token = _bluesky_auth()
    if not token:
        print("Skipping Bluesky (missing BLUESKY_HANDLE/BLUESKY_APP_PASSWORD)")
        return []

    cutoff = time.time() - config["lookback_hours"] * 3600
    limit = min(int(config["limit_per_query"]), 100)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    candidates: dict[str, Candidate] = {}

    for query in config["queries"]:
        url = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?" + urllib.parse.urlencode({
            "q": f'"{query}"',
            "limit": str(limit),
            "sort": "latest",
            "lang": "en",
        })
        try:
            payload = _http_json(url, headers=headers)
        except Exception as e:
            print(f"  bluesky search failed for {query!r}: {e}", file=sys.stderr)
            time.sleep(REQUEST_DELAY_SEC)
            continue

        for post in payload.get("posts", []):
            uri = post.get("uri", "")
            if not uri or uri in seen or uri in candidates:
                continue
            record = post.get("record", {}) or {}
            created_str = record.get("createdAt") or post.get("indexedAt", "")
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00")).timestamp()
            except (ValueError, AttributeError):
                continue
            if created < cutoff:
                continue
            author = post.get("author", {}) or {}
            handle = author.get("handle", "")
            text = (record.get("text") or "")[:4000]
            candidates[uri] = Candidate(
                post_id=uri,
                source="bluesky",
                title=text.split("\n", 1)[0][:200],
                selftext=text,
                author=handle or "[unknown]",
                url=_bluesky_post_url(handle, uri),
                created_utc=created,
                score=int(post.get("likeCount", 0)),
                matched_query=query,
            )

        time.sleep(REQUEST_DELAY_SEC)

    return list(candidates.values())


# ----------------------------------------------------------------------
# Hacker News (Algolia) source
# ----------------------------------------------------------------------


def search_freelancer(config: dict, seen: set[str]) -> list[Candidate]:
    """Search Freelancer.com for GBP-denominated web design projects.

    Uses the public projects API (no auth required). currency_ids[]=4 restricts
    to GBP projects, meaning the client is almost certainly UK-based.
    Every result is a person who has actively posted an RFP — much higher
    intent than social media posts.
    """
    cutoff = int(time.time() - config["lookback_hours"] * 3600)
    limit = int(config["limit_per_query"])
    candidates: dict[str, Candidate] = {}

    freelancer_queries = config.get("freelancer_queries") or config["queries"]
    for query in freelancer_queries:
        url = "https://www.freelancer.com/api/projects/0.1/projects/active/?" + urllib.parse.urlencode({
            "query": query,
            "currency_ids[]": "4",   # GBP only
            "limit": str(limit),
            "full_description": "false",
        })
        try:
            payload = _http_json(url)
        except Exception as e:
            print(f"  freelancer search failed for {query!r}: {e}", file=sys.stderr)
            time.sleep(REQUEST_DELAY_SEC)
            continue

        for proj in payload.get("result", {}).get("projects", []):
            proj_id = proj.get("id")
            if not proj_id:
                continue
            post_id = f"freelancer:{proj_id}"
            if post_id in seen or post_id in candidates:
                continue
            submitted = float(proj.get("time_submitted") or proj.get("submitdate") or 0)
            if submitted < cutoff:
                continue
            seo = proj.get("seo_url") or ""
            url_link = f"https://www.freelancer.com/projects/{seo}" if seo else f"https://www.freelancer.com/projects/{proj_id}"
            budget_min = proj.get("budget", {}).get("minimum") or 0
            budget_max = proj.get("budget", {}).get("maximum") or 0
            title = proj.get("title") or ""
            desc = (proj.get("description") or proj.get("preview_description") or "")[:4000]
            candidates[post_id] = Candidate(
                post_id=post_id,
                source="freelancer",
                title=f"£{budget_min:.0f}-{budget_max:.0f}: {title}",
                selftext=desc,
                author="[freelancer client]",
                url=url_link,
                created_utc=submitted,
                score=0,
                matched_query=query,
            )

        time.sleep(REQUEST_DELAY_SEC)

    return list(candidates.values())


def search_hackernews(config: dict, seen: set[str]) -> list[Candidate]:
    cutoff = int(time.time() - config["lookback_hours"] * 3600)
    limit = int(config["limit_per_query"])
    candidates: dict[str, Candidate] = {}

    for query in config["queries"]:
        url = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode({
            "query": f'"{query}"',
            "tags": "story",
            "numericFilters": f"created_at_i>{cutoff}",
            "hitsPerPage": str(limit),
        })
        try:
            payload = _http_json(url)
        except Exception as e:
            print(f"  hn search failed for {query!r}: {e}", file=sys.stderr)
            time.sleep(REQUEST_DELAY_SEC)
            continue

        for hit in payload.get("hits", []):
            object_id = hit.get("objectID")
            if not object_id:
                continue
            post_id = f"hn:{object_id}"
            if post_id in seen or post_id in candidates:
                continue
            created = float(hit.get("created_at_i", 0))
            if created < cutoff:
                continue
            candidates[post_id] = Candidate(
                post_id=post_id,
                source="hackernews",
                title=hit.get("title") or "",
                selftext=(hit.get("story_text") or "")[:4000],
                author=hit.get("author") or "[unknown]",
                url=f"https://news.ycombinator.com/item?id={object_id}",
                created_utc=created,
                score=int(hit.get("points") or 0),
                matched_query=query,
            )

        time.sleep(REQUEST_DELAY_SEC)

    return list(candidates.values())


# ----------------------------------------------------------------------
# Trade press RSS source
# ----------------------------------------------------------------------
#
# Unlike the social sources, RSS items are not people asking to hire anyone.
# They are trigger events inside a target vertical — a new general manager, a
# refurbishment, an acquisition, an award. The classifier judges whether the
# event makes the named business worth approaching, not whether someone is
# shopping.

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(raw: str) -> str:
    return _WS_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", raw or ""))).strip()


def _http_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA})
    backoff = 2
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    return ""


ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _rss_entries(root: ET.Element) -> list[ET.Element]:
    """RSS 2.0 uses <item>; Atom uses <entry>. Support both."""
    items = root.findall(".//item")
    if items:
        return items
    return root.findall(f".//{ATOM_NS}entry")


def _entry_field(entry: ET.Element, *names: str) -> str:
    for name in names:
        node = entry.find(name)
        if node is None:
            node = entry.find(f"{ATOM_NS}{name}")
        if node is None:
            continue
        if name == "link" and not (node.text or "").strip():
            href = node.get("href")
            if href:
                return href.strip()
        if node.text and node.text.strip():
            return node.text.strip()
    return ""


def _entry_timestamp(entry: ET.Element) -> float | None:
    for name in ("pubDate", "published", "updated", "date"):
        raw = _entry_field(entry, name)
        if not raw:
            continue
        try:
            return parsedate_to_datetime(raw).timestamp()
        except (TypeError, ValueError):
            pass
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
    return None


def search_rss(config: dict, seen: set[str]) -> list[Candidate]:
    feeds = config.get("rss_feeds") or []
    keywords = [k.lower() for k in (config.get("rss_keywords") or [])]
    cutoff = time.time() - config["lookback_hours"] * 3600
    candidates: dict[str, Candidate] = {}

    for feed_url in feeds:
        try:
            raw = _http_text(feed_url)
            root = ET.fromstring(raw)
        except Exception as e:
            print(f"  rss fetch/parse failed for {feed_url}: {e}", file=sys.stderr)
            time.sleep(REQUEST_DELAY_SEC)
            continue

        for entry in _rss_entries(root):
            link = _entry_field(entry, "link")
            guid = _entry_field(entry, "guid", "id") or link
            if not guid:
                continue
            post_id = f"rss:{guid}"
            if post_id in seen or post_id in candidates:
                continue

            created = _entry_timestamp(entry)
            # An undated item is kept rather than dropped: some feeds omit
            # dates, and the seen-id check already stops repeat processing.
            if created is not None and created < cutoff:
                continue

            title = _strip_html(_entry_field(entry, "title"))
            body = _strip_html(
                _entry_field(entry, "description", "summary", "content")
            )[:4000]

            haystack = f"{title} {body}".lower()
            matched = next((k for k in keywords if k in haystack), None)
            if keywords and not matched:
                continue

            candidates[post_id] = Candidate(
                post_id=post_id,
                source="tradepress",
                title=title,
                selftext=body,
                author=_strip_html(_entry_field(entry, "creator", "author")) or "[trade press]",
                url=link or guid,
                created_utc=created if created is not None else time.time(),
                score=0,
                matched_query=matched or "(no keyword filter)",
            )

        time.sleep(REQUEST_DELAY_SEC)

    return list(candidates.values())


# ----------------------------------------------------------------------
# Classifier
# ----------------------------------------------------------------------

# Fallback only. The live rules come from `classifier_rules` in config.yaml so
# that positioning lives in one editable place rather than in code.
DEFAULT_CLASSIFIER_RULES = """A post is a LEAD only if it names a real business that has a plausible
reason to want the services described in the business context. Not leads:
people offering their own services, DIY questions, general commentary, or
news with no named business attached."""

CLASSIFIER_SYSTEM_TEMPLATE = """You judge whether an item is a genuine lead for the business described below.

{rules}

Respond with a single JSON object, no prose, no code fences:
{{"is_lead": true|false, "confidence": 0.0-1.0, "reason": "one short sentence"}}"""


def classify(
    anthropic: Anthropic,
    business_context: str,
    candidate: Candidate,
    rules: str = DEFAULT_CLASSIFIER_RULES,
) -> dict:
    user_msg = (
        f"Business context:\n{business_context}\n\n"
        f"--- Post ({candidate.source}) ---\n"
        f"Author: {candidate.author}\n"
        f"Title: {candidate.title}\n\n"
        f"Body:\n{candidate.selftext or '(no body)'}\n"
    )
    resp = anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=CLASSIFIER_SYSTEM_TEMPLATE.format(rules=rules.strip()),
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

def append_leads(rows: list[dict]) -> None:
    with LEADS_PATH.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEADS_FIELDS)
        for row in rows:
            writer.writerow(row)


def send_digest(leads: list[dict]) -> None:
    """Email a digest of new leads via SMTP. Silently skipped if not configured."""
    required = ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Skipping email digest (missing env: {', '.join(missing)})")
        return

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT") or "587")
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    sender = os.environ.get("EMAIL_FROM", user)
    recipient = os.environ["EMAIL_TO"]

    text_body, html_body = _render_digest(leads)

    msg = EmailMessage()
    msg["Subject"] = f"[Layered] {len(leads)} new lead{'s' if len(leads) != 1 else ''}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=30) as s:
                s.login(user, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.starttls()
                s.login(user, password)
                s.send_message(msg)
        print(f"Sent digest to {recipient}")
    except Exception as e:
        print(f"  email send failed: {e}", file=sys.stderr)


SOURCE_LABEL = {"bluesky": "bsky", "hackernews": "HN"}


def _render_digest(leads: list[dict]) -> tuple[str, str]:
    ranked = sorted(
        leads,
        key=lambda r: float(r.get("classifier_confidence") or 0),
        reverse=True,
    )

    text_lines = [f"{len(leads)} new lead(s):\n"]
    rows_html = []
    for r in ranked:
        conf = r.get("classifier_confidence", "")
        try:
            conf_str = f"{float(conf):.0%}"
        except (TypeError, ValueError):
            conf_str = str(conf)

        source = SOURCE_LABEL.get(r.get("source", ""), r.get("source", ""))

        text_lines.append(
            f"- [{conf_str}] {source}: {r['title']}\n"
            f"    {r['url']}\n"
            f"    why: {r.get('classifier_reason', '')}\n"
        )
        rows_html.append(
            "<tr>"
            f"<td style='padding:8px;border-bottom:1px solid #eee;white-space:nowrap'>{html.escape(conf_str)}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #eee;white-space:nowrap'>{html.escape(source)}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #eee'>"
            f"<a href='{html.escape(r['url'])}' style='color:#0366d6;text-decoration:none'>"
            f"{html.escape(r['title'])}</a>"
            f"<div style='color:#586069;font-size:13px;margin-top:4px'>"
            f"{html.escape(r.get('classifier_reason', ''))}</div>"
            f"</td>"
            "</tr>"
        )

    html_body = (
        "<html><body style='font-family:-apple-system,sans-serif;color:#24292e'>"
        f"<h2 style='margin-bottom:16px'>{len(leads)} new lead(s)</h2>"
        "<table style='border-collapse:collapse;width:100%;max-width:780px'>"
        "<thead><tr style='background:#f6f8fa;text-align:left'>"
        "<th style='padding:8px'>Conf.</th>"
        "<th style='padding:8px'>Source</th>"
        "<th style='padding:8px'>Post</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows_html)}</tbody>"
        "</table>"
        "<p style='color:#586069;font-size:13px;margin-top:24px'>"
        "Full history in <code>scraper/leads.csv</code>. "
        "Tune queries in <code>scraper/config.yaml</code>."
        "</p></body></html>"
    )
    return "\n".join(text_lines), html_body


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def check_feeds(config: dict) -> int:
    """Verify every configured RSS feed resolves and parses. No API calls."""
    feeds = config.get("rss_feeds") or []
    if not feeds:
        print("No rss_feeds configured.")
        return 1

    failures = 0
    for feed_url in feeds:
        try:
            root = ET.fromstring(_http_text(feed_url))
        except Exception as e:
            print(f"  FAIL  {feed_url}\n        {type(e).__name__}: {e}")
            failures += 1
            continue

        entries = _rss_entries(root)
        if not entries:
            print(f"  EMPTY {feed_url}  (parsed, but no <item>/<entry> found)")
            failures += 1
            continue

        newest = max((_entry_timestamp(e) or 0) for e in entries)
        age = "unknown age"
        if newest:
            hours = (time.time() - newest) / 3600
            age = f"newest {hours:.0f}h old"
        sample = _strip_html(_entry_field(entries[0], "title"))[:60]
        print(f"  OK    {feed_url}\n        {len(entries)} items, {age} — {sample!r}")

    print(f"\n{len(feeds) - failures}/{len(feeds)} feeds usable")
    return 1 if failures else 0


def main() -> int:
    config = load_config()

    if "--check-feeds" in sys.argv:
        return check_feeds(config)

    ensure_leads_file()
    seen = load_seen_ids()

    print(f"Loaded {len(seen)} previously-seen post ids")

    candidates: list[Candidate] = []
    if config.get("bluesky_enabled", True):
        candidates.extend(search_bluesky(config, seen))
    if config.get("hackernews_enabled", True):
        candidates.extend(search_hackernews(config, seen))
    if config.get("freelancer_enabled", True):
        candidates.extend(search_freelancer(config, seen))
    if config.get("rss_enabled", False):
        candidates.extend(search_rss(config, seen))

    print(f"Found {len(candidates)} new candidate posts")

    # Pre-filter: cheap string check before spending classifier tokens
    prefiltered = []
    for c in candidates:
        if _is_diy_noise(c):
            print(f"  [{c.source}] pre-filter — {c.title[:80]!r}")
        else:
            prefiltered.append(c)
    if len(prefiltered) < len(candidates):
        print(f"  Pre-filter removed {len(candidates) - len(prefiltered)} DIY-build posts")
    candidates = prefiltered

    if not candidates:
        return 0

    anthropic = Anthropic()
    min_conf = float(config.get("min_confidence", 0.0))
    new_leads: list[dict] = []

    for c in candidates:
        try:
            verdict = classify(
                anthropic,
                config["business_context"],
                c,
                config.get("classifier_rules") or DEFAULT_CLASSIFIER_RULES,
            )
        except Exception as e:
            print(f"  classifier failed for {c.post_id}: {e}", file=sys.stderr)
            continue

        conf = verdict.get("confidence") or 0
        keep_str = "KEEP" if verdict.get("is_lead") else "drop"
        print(f"  [{c.source}] {keep_str} ({float(conf):.0%}) — {c.title[:80]!r}  | {verdict.get('reason', '')}")

        if not verdict.get("is_lead") or float(conf) < min_conf:
            continue

        new_leads.append({
            "post_id": c.post_id,
            "source": c.source,
            "title": c.title,
            "author": c.author,
            "url": c.url,
            "created_utc": datetime.fromtimestamp(c.created_utc, tz=timezone.utc).isoformat(),
            "score": c.score,
            "matched_query": c.matched_query,
            "classifier_confidence": verdict.get("confidence", ""),
            "classifier_reason": verdict.get("reason", ""),
            "found_at": datetime.now(timezone.utc).isoformat(),
        })

    if new_leads:
        append_leads(new_leads)
        send_digest(new_leads)

    print(f"Added {len(new_leads)} new leads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
