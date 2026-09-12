# Lead finder

Watches for businesses worth approaching, runs each candidate through Claude
Haiku to filter out noise, and appends matches to `leads.csv`. Optional SMTP
email digest on runs that produce new leads.

## Two kinds of source, and why it matters

The tool originally looked for **intent**: people publicly posting "I need a
web designer". That works for a commodity purchase people know how to ask for.

It does not work for what Layered sells now. Nobody posts "my staff keep asking
the same questions and our SOPs are in a binder" — that is ambient friction,
not a recognised purchase. So intent search finds almost nothing, and the
queries that *do* return volume (freelance website jobs at £250-£750) are for
the positioning Layered left behind in July 2026.

The main source is now **signals** instead:

| Kind | Source | What it finds |
| ---- | ------ | ------------- |
| Signal | Trade press RSS | A named business had a trigger event — new GM, refurbishment, acquisition, award, staffing trouble |
| Intent | Bluesky | Someone describes an operational problem out loud. Low volume; a long shot |
| Intent | Freelancer.com | **Off.** Produced only cheap website jobs |
| Intent | Hacker News | **Off.** Wrong audience |

A signal is not a person asking to buy. It is a reason to get there first.
A new general manager in their first six months is the single best moment to
arrive: they are forming their own view of what is broken and have licence to
change it.

Sources are queried in every run; results are deduped and merged.

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

If `BLUESKY_*` aren't set, Bluesky is silently skipped and the run continues
on the trade-press feeds alone. The feeds need no credentials, so you can
launch on RSS only and add Bluesky later if you want.

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

## Verify the feeds first

The RSS feed URLs in `config.yaml` were written in an environment that could
not reach them, so **they are unverified**. Check them once before trusting
the output:

```bash
cd scraper
python scrape.py --check-feeds
```

This makes no API calls and costs nothing. It reports, per feed, whether it
parses, how many items it has, and how old the newest one is. Drop or correct
anything that fails. At runtime a bad feed logs to stderr and is skipped, so a
dead URL degrades the run quietly rather than breaking it.

## Tuning

Edit `scraper/config.yaml` — no code changes needed:

- `rss_feeds` — which publications to watch
- `rss_keywords` — the trigger events an item must mention to reach the
  classifier. This is the cheap filter that keeps the Claude bill near zero
- `queries` — Bluesky exact phrases
- `business_context` — who you are, used by the classifier to judge fit
- `classifier_rules` — how to judge. This lives in config rather than in code,
  so positioning is defined in exactly one place

Expect to iterate for a week or two. Check `classifier_reason` in `leads.csv`
to see why borderline items were kept or dropped, and tighten
`business_context` or `classifier_rules` if false positives slip through.

**Adding a vertical.** The feed list and keywords are currently aimed at
hospitality, because Gilpin is the strongest reference. To open a second
vertical, add its trade publications to `rss_feeds` and widen
`business_context` — the keyword list is mostly vertical-neutral already.

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

## A note on lead volume

Expect single figures per week, and treat that as correct rather than broken.

This tool is not a funnel. Layered sells a bespoke build worth thousands of
pounds to a finite number of businesses in and around Cumbria. The addressable
list is hundreds of names, not hundreds of thousands, so the job is to notice
the right moment at a business you could already name — not to generate volume.

A signal is a prompt to make contact personally. It is not a list to mail.
Before emailing a sole trader or an unincorporated partnership, note that UK
PECR treats them as individual subscribers and they need consent; limited
companies and LLPs do not.

The architecture is source-pluggable: adding a source is a single function
alongside `search_bluesky`, `search_rss` and `search_hackernews`.
