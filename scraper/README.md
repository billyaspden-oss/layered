# Lead finder

Scrapes social media on a schedule for posts that look like someone shopping
for a website, runs each candidate through Claude Haiku to filter out noise,
and appends matches to `leads.csv`. Optional SMTP email digest on runs that
produce new leads.

**Sources:**
- **Bluesky** — requires a free Bluesky account + app password (1-minute setup)
- **Hacker News** — uses the public Algolia search API, no auth required

Both sources are queried in every run; results are deduped and merged into a
single ranked list.

## One-time setup

### 1. Get an Anthropic API key

https://console.anthropic.com → Settings → API Keys → Create Key.
Haiku 4.5 is cheap; expect well under $1/month at default volumes.

### 2. Get a Bluesky app password

1. Sign up at https://bsky.app (free, no captcha gates)
2. Go to **Settings → App Passwords → Add App Password**
3. Name it something like `lead-finder`
4. Copy the password — it's only shown once. Format: `xxxx-xxxx-xxxx-xxxx`

### 3. Add GitHub secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name                   | Required | Value                                                 |
| ---------------------- | -------- | ----------------------------------------------------- |
| `ANTHROPIC_API_KEY`    | yes      | from step 1                                           |
| `BLUESKY_HANDLE`       | optional | your Bluesky handle, e.g. `layered.bsky.social`       |
| `BLUESKY_APP_PASSWORD` | optional | from step 2                                           |

If `BLUESKY_*` aren't set, Bluesky is silently skipped and only Hacker News
runs. So you can launch with HN-only and add Bluesky later if you want.

### 4. Add SMTP secrets for email digest (optional)

If these aren't set the run still works — it just won't email. New leads are
always saved to `leads.csv` regardless.

| Name            | Value                                                                  |
| --------------- | ---------------------------------------------------------------------- |
| `SMTP_HOST`     | e.g. `smtp.gmail.com`, `smtp.fastmail.com`                             |
| `SMTP_PORT`     | `587` for STARTTLS (default), `465` for SSL                            |
| `SMTP_USER`     | the SMTP login (usually your email address)                            |
| `SMTP_PASSWORD` | **app password**, not your real password (see below)                   |
| `EMAIL_FROM`    | sender address (defaults to `SMTP_USER` if unset)                      |
| `EMAIL_TO`      | where the digest goes                                                  |

**Gmail:** turn on 2FA, then create an **app password** at
https://myaccount.google.com/apppasswords. Use that as `SMTP_PASSWORD`.
**Fastmail:** Settings → Privacy & Security → Integrations → New app password.

You get one email per scraper run *only when there are new leads* — so at
most 4/day, usually fewer. No empty digests.

### 5. (Optional) Trigger a first run manually

**Actions → Scrape leads → Run workflow**.
After it finishes you should see a `chore(scraper): add new leads ...` commit
if anything matched.

## Tuning

Edit `scraper/config.yaml` to change queries, lookback window, and the
business-context description used by the classifier. No code changes needed.

Expect to iterate on queries for a week or two — check `classifier_reason` in
`leads.csv` to see why borderline posts were kept/dropped, and adjust the
business-context blurb if too many false positives slip through.

## Running locally

```bash
cd scraper
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export BLUESKY_HANDLE=...        # optional
export BLUESKY_APP_PASSWORD=...  # optional
python scrape.py
```

## Output

`scraper/leads.csv` — one row per matched post. The workflow commits this
back to the branch on every run, so the file is your durable lead list.

### Scoring & outreach columns

When `outreach_enabled` is on (the default), every kept lead gets a second
Haiku pass that scores it against your `business_context` as an ICP and drafts
a reply you can send. This adds four columns:

| Column             | Meaning                                                            |
| ------------------ | ------------------------------------------------------------------ |
| `icp_status`       | `QUALIFIED` or `DISQUALIFIED` against your ideal-customer profile  |
| `icp_reasoning`    | One sentence on why                                                |
| `outreach_hook`    | The single most specific detail the message opens on              |
| `outreach_message` | A ≤300-char, 3-sentence draft reply (blank when `DISQUALIFIED`)    |

The email digest shows the ICP badge and the drafted message inline, so a
qualified lead arrives ready to action. The draft is a starting point — skim
it before sending. Set `outreach_enabled: false` in `config.yaml` to skip this
pass (one fewer Haiku call per kept lead).

## A note on lead volume

Both sources are smaller than Reddit:

- **Bluesky** has a growing audience that skews tech-savvy and creative,
  but is still ~10% the size of Reddit. Expect a handful of leads per
  week, not per day.
- **Hacker News** is technical and DIY-leaning, so direct "need a website"
  posts are rare. Most value here comes from "Show HN" / "Ask HN" threads
  where non-technical founders mention needing help. Low yield, but
  occasionally high quality.

If you want more volume later, the architecture is source-pluggable — adding
a Mastodon or a paid Twitter/X source is a single function alongside
`search_bluesky` and `search_hackernews`.
