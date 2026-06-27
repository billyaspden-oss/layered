"""Find social media posts from people who appear to be shopping for a website.

Runs on a schedule (see .github/workflows/scrape.yml), appends new matches to
leads.csv, and skips posts already in the file.

Sources:
  - Bluesky (requires app password)
  - Hacker News via Algolia API (no auth required)
"""

from __future__ import annotations

import csv
import html
import json
import os
import smtplib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
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
    "icp_status",
    "icp_reasoning",
    "outreach_hook",
    "outreach_message",
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
    if not LEADS_PATH.exists():
        with LEADS_PATH.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=LEADS_FIELDS).writeheader()
        return
    migrate_leads_file()


def migrate_leads_file() -> None:
    """Rewrite leads.csv if its header predates the current LEADS_FIELDS.

    Older files lack the scoring/outreach columns. Appending wider rows to a
    narrower header would misalign the CSV, so we rewrite once, backfilling
    the new columns with empty values for historical rows.
    """
    with LEADS_PATH.open(newline="") as f:
        reader = csv.DictReader(f)
        existing_fields = reader.fieldnames or []
        if existing_fields == LEADS_FIELDS:
            return
        rows = list(reader)

    with LEADS_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEADS_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in LEADS_FIELDS})


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




# Keywords that reliably indicate someone is using AI/DIY to build their own site —
# not shopping to hire a designer. Checked before the LLM classifier to save tokens.
_AI_DIY_SIGNALS = [
    "claude built", "chatgpt built", "ai built", "built with ai", "built using ai",
    "built by ai", "ai designed", "ai generated", "vibe cod", "cursor built",
    "built my own", "built it myself", "built myself", "coded it myself",
    "i built my", "i made my own", "i designed my", "made it myself",
    "no way i could afford", "why would i pay", "never pay a web",
    "stop paying for web", "pay for a web designer",
]


def _is_ai_diy_noise(candidate) -> bool:
    """Return True if the post is almost certainly AI/DIY noise, not a hire signal."""
    combined = (candidate.title + " " + candidate.selftext).lower()
    return any(sig in combined for sig in _AI_DIY_SIGNALS)

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


# ----------------------------------------------------------------------
# LinkedIn source (paid third-party data API)
# ----------------------------------------------------------------------

# Field names vary by provider, so parsing tries several common keys for each
# piece of data. These cover the RapidAPI "LinkedIn Data API" family and most
# Proxycurl-style responses.
_LI_LIST_KEYS = ("data", "items", "results", "people", "elements", "profiles")
_LI_NAME_KEYS = ("fullName", "full_name", "name", "displayName")
_LI_HEADLINE_KEYS = ("headline", "title", "occupation", "subtitle")
_LI_ABOUT_KEYS = ("summary", "about", "description", "bio")
_LI_URL_KEYS = ("profileURL", "profile_url", "linkedin_url", "url", "publicProfileUrl", "navigationUrl")
_LI_ID_KEYS = ("urn", "entityUrn", "publicIdentifier", "username", "id", "profile_id")
_LI_COMPANY_KEYS = ("companyName", "company", "company_name", "currentCompany")


def _li_first(obj: dict, keys: tuple[str, ...]) -> str:
    """Return the first present, non-empty string value among candidate keys."""
    for k in keys:
        val = obj.get(k)
        if isinstance(val, dict):
            val = val.get("name") or val.get("title") or val.get("text")
        if val:
            return str(val)
    return ""


def search_linkedin(config: dict, seen: set[str]) -> list[Candidate]:
    """Search a paid LinkedIn data API for ICP-matching profiles.

    This is OUTBOUND prospecting, not inbound intent: results are people who
    fit the target customer profile, not people who posted asking for a site.
    They therefore bypass the intent classifier and go straight to ICP scoring.

    LinkedIn has no usable public search API and scraping it directly violates
    their ToS, so this calls a configurable third-party provider (e.g. a
    RapidAPI-hosted "LinkedIn Data API" or a Proxycurl-style service). The
    provider host/path/params live in config.yaml; the key comes from the
    RAPIDAPI_KEY (or LINKEDIN_API_KEY) secret. Response shapes vary by vendor,
    so parsing is defensive across common field names.
    """
    li = config.get("linkedin") or {}
    api_key = os.environ.get("RAPIDAPI_KEY") or os.environ.get("LINKEDIN_API_KEY")
    if not api_key:
        print("Skipping LinkedIn (missing RAPIDAPI_KEY/LINKEDIN_API_KEY)")
        return []

    api_host = li.get("api_host")
    search_path = li.get("search_path", "/search-people")
    if not api_host:
        print("Skipping LinkedIn (no linkedin.api_host in config)")
        return []

    params = dict(li.get("search_params") or {})
    params.setdefault("limit", li.get("limit", 25))
    url = f"https://{api_host}{search_path}?" + urllib.parse.urlencode(params)
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host,
        "Accept": "application/json",
    }

    try:
        payload = _http_json(url, headers=headers)
    except Exception as e:
        print(f"  linkedin search failed: {e}", file=sys.stderr)
        return []

    # The list of profiles can sit at the top level or under a wrapper key.
    people = payload if isinstance(payload, list) else None
    if people is None:
        for key in _LI_LIST_KEYS:
            val = payload.get(key)
            if isinstance(val, list):
                people = val
                break
            if isinstance(val, dict):  # e.g. {"data": {"items": [...]}}
                for inner in _LI_LIST_KEYS:
                    if isinstance(val.get(inner), list):
                        people = val[inner]
                        break
            if people is not None:
                break
    if not people:
        print("  linkedin: no profiles in response (check provider field names)")
        return []

    limit = int(li.get("limit", 25))
    candidates: dict[str, Candidate] = {}
    now = time.time()
    for person in people[:limit]:
        if not isinstance(person, dict):
            continue
        profile_url = _li_first(person, _LI_URL_KEYS)
        ident = _li_first(person, _LI_ID_KEYS) or profile_url
        if not ident:
            continue
        post_id = f"linkedin:{ident}"
        if post_id in seen or post_id in candidates:
            continue

        name = _li_first(person, _LI_NAME_KEYS) or "[unknown]"
        headline = _li_first(person, _LI_HEADLINE_KEYS)
        about = _li_first(person, _LI_ABOUT_KEYS)
        company = _li_first(person, _LI_COMPANY_KEYS)
        recent_post = _li_first(person, ("recentPost", "lastPost", "latest_post"))

        body = "\n\n".join(
            part for part in (
                f"Headline: {headline}" if headline else "",
                f"Company: {company}" if company else "",
                f"About: {about}" if about else "",
                f"Recent post: {recent_post}" if recent_post else "",
            ) if part
        )[:4000]

        candidates[post_id] = Candidate(
            post_id=post_id,
            source="linkedin",
            title=f"{name} — {headline}" if headline else name,
            selftext=body,
            author=name,
            url=profile_url or "",
            created_utc=now,
            score=0,
            matched_query="linkedin:icp-search",
        )

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
# Classifier
# ----------------------------------------------------------------------

CLASSIFIER_SYSTEM = """You judge whether a social media post is a genuine lead for a web design agency.

A post is a LEAD only if the author is personally looking to hire someone to
design, build, or rebuild a website. NOT leads:
- People offering their own web design services
- People asking how to DIY a site
- Hosting/domain/technical questions with no intent to hire
- People complaining about an existing site with no intent to redo it
- News, opinions, jokes, ironic posts, or commentary about web design generally

Respond with a single JSON object, no prose, no code fences:
{"is_lead": true|false, "confidence": 0.0-1.0, "reason": "one short sentence"}"""


def classify(anthropic: Anthropic, business_context: str, candidate: Candidate) -> dict:
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
        system=CLASSIFIER_SYSTEM,
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
# ICP scorer + outreach copywriter
# ----------------------------------------------------------------------

_SCORER_HEAD = """You are a sharp, no-nonsense growth operator for a web design agency.
You take a single lead and do four things in order.

ROLE 1 — RESEARCH: From the material below, infer:
  - what the person's business or project actually is (their "value prop"),
  - their core focus or need,
  - the single most specific HOOK you could open a message with — a concrete
    detail (their trade, location, the kind of site, a pain they named, a
    deadline, something from their profile or post). Never a generic platitude.

ROLE 2 — ICP GATE: Decide QUALIFIED or DISQUALIFIED against the agency's ICP
below. DISQUALIFY if they are outside the target market (e.g. enterprise/complex
platforms, pure dev work like scraping or apps, someone offering their own
services, a budget far below or above the agency's range, or a profile/post too
vague or inactive to act on). Give a one-sentence reason either way."""

_ROLE3_REPLY = """ROLE 3 — COPYWRITER: Only if QUALIFIED, write a reply they could receive on the
platform they posted on. Hard rules:
  - Maximum 300 characters, 3 sentences.
  - Casual, peer-to-peer, confident, zero fluff.
  - Sentence 1: a specific observation built from the HOOK.
  - Sentence 2: tie it to a sharp, likely pain point for their situation.
  - Sentence 3: a low-friction, open-ended question. Do NOT ask for a call and
    do NOT pitch a price or service yet.
  - Banned: "Hope this finds you well", "I stumbled across", "I came across",
    "Reaching out", and exclamation marks.
  - If DISQUALIFIED, leave outreach_message as an empty string."""

_ROLE3_LINKEDIN = """ROLE 3 — COPYWRITER: Only if QUALIFIED, write a LinkedIn connection-request
note to this person. Hard rules:
  - Maximum 300 characters, 3 sentences (LinkedIn's connection-note limit).
  - Casual, peer-to-peer, confident, zero fluff.
  - Sentence 1: a specific observation built from the HOOK (their role, company,
    or a detail from their profile).
  - Sentence 2: tie it to a sharp, likely pain point for their situation.
  - Sentence 3: a low-friction, open-ended question. Do NOT ask for a call and
    do NOT pitch a price or service yet.
  - Banned: "Hope this finds you well", "I stumbled across", "I came across",
    "Reaching out", and exclamation marks.
  - If DISQUALIFIED, leave outreach_message as an empty string."""

_SCORER_TAIL = """ROLE 4 — OUTPUT: Respond with a single JSON object, no prose, no code fences:
{"company_value_prop": "...", "lead_core_focus": "...", "outreach_hook": "...",
 "icp_status": "QUALIFIED"|"DISQUALIFIED", "icp_reasoning": "...",
 "outreach_message": "..."}"""


def build_scorer_system(source: str) -> str:
    role3 = _ROLE3_LINKEDIN if source == "linkedin" else _ROLE3_REPLY
    return f"{_SCORER_HEAD}\n\n{role3}\n\n{_SCORER_TAIL}"


def score_and_draft(anthropic: Anthropic, icp_context: str, candidate: Candidate) -> dict:
    label = "profile" if candidate.source == "linkedin" else "post"
    user_msg = (
        f"Agency ICP / business context:\n{icp_context}\n\n"
        f"--- Lead {label} ({candidate.source}) ---\n"
        f"Author: {candidate.author}\n"
        f"Title: {candidate.title}\n\n"
        f"Body:\n{candidate.selftext or '(no body)'}\n"
    )
    resp = anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=build_scorer_system(candidate.source),
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
    msg["Subject"] = f"[Layered] {len(leads)} new website lead{'s' if len(leads) != 1 else ''}"
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


SOURCE_LABEL = {"bluesky": "bsky", "hackernews": "HN", "linkedin": "LinkedIn"}


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
        icp_status = (r.get("icp_status") or "").upper()
        message = r.get("outreach_message") or ""

        text_lines.append(
            f"- [{conf_str}] {source}: {r['title']}\n"
            f"    {r['url']}\n"
            f"    why: {r.get('classifier_reason', '')}\n"
            + (f"    ICP: {icp_status} — {r.get('icp_reasoning', '')}\n" if icp_status else "")
            + (f"    draft: {message}\n" if message else "")
        )

        if icp_status == "QUALIFIED":
            badge_bg, badge_fg = "#dafbe1", "#1a7f37"
        elif icp_status == "DISQUALIFIED":
            badge_bg, badge_fg = "#ffebe9", "#cf222e"
        else:
            badge_bg, badge_fg = "#f6f8fa", "#586069"
        icp_html = (
            f"<span style='display:inline-block;background:{badge_bg};color:{badge_fg};"
            f"font-size:11px;font-weight:600;padding:1px 6px;border-radius:10px'>"
            f"{html.escape(icp_status)}</span>"
            if icp_status else ""
        )
        message_html = (
            f"<div style='margin-top:8px;padding:8px 10px;background:#f6f8fa;"
            f"border-left:3px solid #0366d6;font-size:13px;color:#24292e'>"
            f"{html.escape(message)}</div>"
            if message else ""
        )
        rows_html.append(
            "<tr>"
            f"<td style='padding:8px;border-bottom:1px solid #eee;white-space:nowrap'>{html.escape(conf_str)}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #eee;white-space:nowrap'>{html.escape(source)}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #eee'>"
            f"<a href='{html.escape(r['url'])}' style='color:#0366d6;text-decoration:none'>"
            f"{html.escape(r['title'])}</a>"
            f" {icp_html}"
            f"<div style='color:#586069;font-size:13px;margin-top:4px'>"
            f"{html.escape(r.get('classifier_reason', ''))}</div>"
            f"{message_html}"
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

def main() -> int:
    config = load_config()
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
    if config.get("linkedin_enabled", False):
        candidates.extend(search_linkedin(config, seen))

    print(f"Found {len(candidates)} new candidate leads")

    # LinkedIn results are outbound ICP matches, not inbound intent posts, so
    # they bypass the intent classifier and its AI/DIY pre-filter.
    intent_candidates = [c for c in candidates if c.source != "linkedin"]
    linkedin_candidates = [c for c in candidates if c.source == "linkedin"]

    # Pre-filter: cheap string check before spending classifier tokens
    prefiltered = []
    for c in intent_candidates:
        if _is_ai_diy_noise(c):
            print(f"  [{c.source}] pre-filter — {c.title[:80]!r}")
        else:
            prefiltered.append(c)
    if len(prefiltered) < len(intent_candidates):
        print(f"  Pre-filter removed {len(intent_candidates) - len(prefiltered)} AI/DIY noise posts")
    intent_candidates = prefiltered

    if not intent_candidates and not linkedin_candidates:
        return 0

    anthropic = Anthropic()
    min_conf = float(config.get("min_confidence", 0.0))
    outreach_enabled = config.get("outreach_enabled", True)
    business_context = config["business_context"]
    # Outbound prospecting can target a different ICP than inbound intent.
    linkedin_icp = config.get("linkedin_icp") or business_context
    new_leads: list[dict] = []

    def base_lead(c: Candidate) -> dict:
        return {
            "post_id": c.post_id,
            "source": c.source,
            "title": c.title,
            "author": c.author,
            "url": c.url,
            "created_utc": datetime.fromtimestamp(c.created_utc, tz=timezone.utc).isoformat(),
            "score": c.score,
            "matched_query": c.matched_query,
            "classifier_confidence": "",
            "classifier_reason": "",
            "icp_status": "",
            "icp_reasoning": "",
            "outreach_hook": "",
            "outreach_message": "",
            "found_at": datetime.now(timezone.utc).isoformat(),
        }

    def apply_scoring(lead: dict, c: Candidate, icp: str) -> None:
        try:
            scored = score_and_draft(anthropic, icp, c)
            lead["icp_status"] = scored.get("icp_status", "")
            lead["icp_reasoning"] = scored.get("icp_reasoning", "")
            lead["outreach_hook"] = scored.get("outreach_hook", "")
            lead["outreach_message"] = scored.get("outreach_message", "")
            print(f"      ICP {lead['icp_status'] or '?'} — {lead['icp_reasoning']}")
        except Exception as e:
            print(f"  scorer failed for {c.post_id}: {e}", file=sys.stderr)

    # Inbound intent posts: classify first, then score the keepers.
    for c in intent_candidates:
        try:
            verdict = classify(anthropic, business_context, c)
        except Exception as e:
            print(f"  classifier failed for {c.post_id}: {e}", file=sys.stderr)
            continue

        conf = verdict.get("confidence") or 0
        keep_str = "KEEP" if verdict.get("is_lead") else "drop"
        print(f"  [{c.source}] {keep_str} ({float(conf):.0%}) — {c.title[:80]!r}  | {verdict.get('reason', '')}")

        if not verdict.get("is_lead") or float(conf) < min_conf:
            continue

        lead = base_lead(c)
        lead["classifier_confidence"] = verdict.get("confidence", "")
        lead["classifier_reason"] = verdict.get("reason", "")
        if outreach_enabled:
            apply_scoring(lead, c, business_context)
        new_leads.append(lead)

    # Outbound LinkedIn prospects: score against the ICP; keep only QUALIFIED.
    for c in linkedin_candidates:
        lead = base_lead(c)
        # ICP scoring is the gate here, so always run it regardless of toggle.
        apply_scoring(lead, c, linkedin_icp)
        if lead["icp_status"].upper() != "QUALIFIED":
            print(f"  [linkedin] drop (not QUALIFIED) — {c.title[:80]!r}")
            continue
        new_leads.append(lead)

    if new_leads:
        append_leads(new_leads)
        send_digest(new_leads)

    print(f"Added {len(new_leads)} new leads")
    return 0


if __name__ == "__main__":
    sys.exit(main())
