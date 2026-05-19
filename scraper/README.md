# Reddit lead finder

Scrapes Reddit on a schedule for posts that look like someone shopping for a
website, runs each candidate through Claude Haiku to filter out noise, and
appends matches to `leads.csv`.

## One-time setup

### 1. Create a Reddit app (free, 2 minutes)

1. Sign in to Reddit, go to https://www.reddit.com/prefs/apps
2. Click **create app** (scroll to bottom)
3. Pick **script** as the type
4. Name: anything (e.g. `layered-leadfinder`)
5. Redirect URI: `http://localhost:8080` (unused but required)
6. Click **create app**
7. Note the **client ID** (under the app name, looks like `abc123XYZ`) and
   **secret**

### 2. Get an Anthropic API key

https://console.anthropic.com → Settings → API Keys → Create Key.
Haiku 4.5 is cheap; expect well under $1/month at default volumes.

### 3. Add GitHub secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name                    | Value                                                                |
| ----------------------- | -------------------------------------------------------------------- |
| `REDDIT_CLIENT_ID`      | from step 1                                                          |
| `REDDIT_CLIENT_SECRET`  | from step 1                                                          |
| `REDDIT_USER_AGENT`     | `layered-leadfinder/0.1 (by u/your_reddit_username)`                 |
| `ANTHROPIC_API_KEY`     | from step 2                                                          |

### 4. Add SMTP secrets for email digest (optional)

If these aren't set, the run still works — it just won't email. Add the same
way as above (Settings → Secrets and variables → Actions).

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

**Actions → Scrape Reddit leads → Run workflow**.
After it finishes you should see a `chore(scraper): add new leads ...` commit
if anything matched.

## Tuning

Edit `scraper/config.yaml` to change subreddits, queries, lookback window, and
the business-context description used by the classifier. No code changes
needed.

## Running locally

```bash
cd scraper
pip install -r requirements.txt
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USER_AGENT="layered-leadfinder/0.1 (by u/your_reddit_username)"
export ANTHROPIC_API_KEY=...
python scrape.py
```

## Output

`scraper/leads.csv` — one row per matched post. The workflow commits this back
to the branch on every run, so the file is your durable lead list.
