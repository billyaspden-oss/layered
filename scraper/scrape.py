"""Find Reddit posts from people who appear to be shopping for a website.

Runs on a schedule (see .github/workflows/scrape.yml), appends new matches to
leads.csv, and skips posts already in the file.
"""

from __future__ import annotations

import csv
import html
import json
import os
import smtplib
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import praw
import yaml
from anthropic import Anthropic

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.yaml"
LEADS_PATH = ROOT / "leads.csv"

LEADS_FIELDS = [
    "post_id",
    "subreddit",
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


@dataclass
class Candidate:
    post_id: str
    subreddit: str
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


def reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get(
            "REDDIT_USER_AGENT",
            "layered-leadfinder/0.1 (by u/unknown)",
        ),
    )


def search_reddit(reddit: praw.Reddit, config: dict, seen: set[str]) -> list[Candidate]:
    cutoff = time.time() - config["lookback_hours"] * 3600
    limit = config["limit_per_query"]
    candidates: dict[str, Candidate] = {}

    for subreddit_name in config["subreddits"]:
        subreddit = reddit.subreddit(subreddit_name)
        for query in config["queries"]:
            try:
                submissions = subreddit.search(
                    query, sort="new", time_filter="week", limit=limit
                )
                for s in submissions:
                    if s.id in seen or s.id in candidates:
                        continue
                    if s.created_utc < cutoff:
                        continue
                    candidates[s.id] = Candidate(
                        post_id=s.id,
                        subreddit=subreddit_name,
                        title=s.title or "",
                        selftext=(s.selftext or "")[:4000],
                        author=str(s.author) if s.author else "[deleted]",
                        url=f"https://reddit.com{s.permalink}",
                        created_utc=s.created_utc,
                        score=s.score,
                        matched_query=query,
                    )
            except Exception as e:
                print(f"  search failed in r/{subreddit_name} for {query!r}: {e}", file=sys.stderr)
                continue

    return list(candidates.values())


CLASSIFIER_SYSTEM = """You judge whether a Reddit post is a genuine lead for a web design agency.

A post is a LEAD only if the author is personally looking to hire someone to
design, build, or rebuild a website. NOT leads:
- People offering their own web design services
- People asking how to DIY a site
- People asking about hosting, domains, or technical specifics with no intent to hire
- People complaining about an existing site with no intent to redo it
- Posts older than a few days where the author may have already found someone

Respond with a single JSON object, no prose, no code fences:
{"is_lead": true|false, "confidence": 0.0-1.0, "reason": "one short sentence"}"""


def classify(anthropic: Anthropic, business_context: str, candidate: Candidate) -> dict:
    user_msg = (
        f"Business context:\n{business_context}\n\n"
        f"--- Reddit post ---\n"
        f"Subreddit: r/{candidate.subreddit}\n"
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
    port = int(os.environ.get("SMTP_PORT", "587"))
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


def _render_digest(leads: list[dict]) -> tuple[str, str]:
    ranked = sorted(
        leads,
        key=lambda r: float(r.get("classifier_confidence") or 0),
        reverse=True,
    )

    text_lines = [f"{len(leads)} new Reddit lead(s):\n"]
    rows_html = []
    for r in ranked:
        conf = r.get("classifier_confidence", "")
        try:
            conf_str = f"{float(conf):.0%}"
        except (TypeError, ValueError):
            conf_str = str(conf)

        text_lines.append(
            f"- [{conf_str}] r/{r['subreddit']}: {r['title']}\n"
            f"    {r['url']}\n"
            f"    why: {r.get('classifier_reason', '')}\n"
        )
        rows_html.append(
            "<tr>"
            f"<td style='padding:8px;border-bottom:1px solid #eee;white-space:nowrap'>{html.escape(conf_str)}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #eee;white-space:nowrap'>r/{html.escape(r['subreddit'])}</td>"
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
        f"<h2 style='margin-bottom:16px'>{len(leads)} new Reddit lead(s)</h2>"
        "<table style='border-collapse:collapse;width:100%;max-width:780px'>"
        "<thead><tr style='background:#f6f8fa;text-align:left'>"
        "<th style='padding:8px'>Conf.</th>"
        "<th style='padding:8px'>Sub</th>"
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


def main() -> int:
    config = load_config()
    ensure_leads_file()
    seen = load_seen_ids()

    print(f"Loaded {len(seen)} previously-seen post ids")

    reddit = reddit_client()
    candidates = search_reddit(reddit, config, seen)
    print(f"Found {len(candidates)} new candidate posts")

    if not candidates:
        return 0

    anthropic = Anthropic()
    new_leads: list[dict] = []

    for c in candidates:
        try:
            verdict = classify(anthropic, config["business_context"], c)
        except Exception as e:
            print(f"  classifier failed for {c.post_id}: {e}", file=sys.stderr)
            continue

        if not verdict.get("is_lead"):
            continue

        new_leads.append({
            "post_id": c.post_id,
            "subreddit": c.subreddit,
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
