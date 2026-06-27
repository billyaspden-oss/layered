# Lead finder

Scrapes social media on a schedule for posts that look like someone shopping
for a website, runs each candidate through Claude Haiku to filter out noise,
and appends matches to `leads.csv`. Optional SMTP email digest on runs that
produce new leads.

**Sources:**
- **Freelancer** — public projects API (no auth), GBP-only RFPs. Highest intent.
- **Bluesky** — requires a free Bluesky account + app password (1-minute setup)
- **Hacker News** — uses the public Algolia search API, no auth required
- **LinkedIn** — *outbound* prospecting via a paid third-party data API
  (off by default). See "LinkedIn source" below.

Enabled sources are queried in every run; results are deduped and merged into a
single ranked list. The first three are **inbound intent** (people asking for a
website); LinkedIn is **outbound** (profiles matching your ICP) and is handled
differently — see below.

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

For **LinkedIn** leads the `outreach_message` is a ≤300-char LinkedIn
connection-request note instead of a reply, and the scorer always runs (it's
the qualification gate), so only `QUALIFIED` profiles are saved.

## LinkedIn source (outbound)

LinkedIn has **no usable public API** — the official API needs partner approval
and can't keyword-search public content, and scraping LinkedIn directly
violates their ToS, needs a logged-in cookie, and gets blocked fast. So this
source is **outbound prospecting through a paid third-party data API** rather
than a scraper.

Unlike the inbound sources, LinkedIn profiles aren't run through the
"is-this-person-shopping-for-a-website" classifier (they're not). Instead each
profile is scored against your ICP and only `QUALIFIED` ones are kept, each with
a drafted connection note.

**Setup:**

1. Pick a provider. The easiest is a [RapidAPI](https://rapidapi.com)-hosted
   "LinkedIn Data API" (search the RapidAPI hub) that offers a people-search
   endpoint. Proxycurl-style services work too. **You pay per lookup** — check
   the provider's pricing.
2. Add the key as a repo secret named `RAPIDAPI_KEY` (or `LINKEDIN_API_KEY`).
3. In `config.yaml`, set `linkedin_enabled: true` and edit the `linkedin:`
   block: `api_host`, `search_path`, and `search_params` to match your
   provider's docs. **Param names and response shapes differ between
   providers** — parsing tries common field names defensively, but you may need
   to tweak `search_params` keys. Optionally set `linkedin_icp` to target a
   different profile than your inbound `business_context`.
4. Run the workflow manually (**Actions → Scrape leads → Run workflow**) and
   check the logs. If you see `linkedin: no profiles in response`, your
   provider returns results under a field name the parser doesn't recognise —
   share its response shape and it's a one-line fix.

> **Note on compliance:** using LinkedIn data this way is subject to LinkedIn's
> terms and your provider's terms. Use it for legitimate, low-volume outreach
> and respect connection/messaging limits.

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
