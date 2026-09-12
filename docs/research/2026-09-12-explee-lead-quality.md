# Explee as a lead generator for Layered

**Date:** 12 September 2026
**Question:** Is explee.com a good source of leads for Layered (AI systems for owner-managed UK businesses, Kendal)?
**Verdict:** No as a lead generator. Maybe as a free list-building tool for one narrow segment. Do not subscribe and do not use its AutoGTM cold-email agent.

> Research constraint: explee.com, its pricing page, G2, Companies House and most review sites were blocked by this session's network proxy. Figures below come from search-engine summaries of those pages and from third-party write-ups, and they disagree with each other in places. Every number that matters is flagged where the sources conflict. Verify pricing and credit costs on explee.com before spending anything.

---

## 1. What Explee actually is

Explee is a B2B contact-data platform with a natural-language search on top. You type a description of a company type ("fintech startups in the US with German founders" is their own example), it returns matching companies from a crawled index, and then charges credits to reveal verified emails and phone numbers. In 2026 it added **AutoGTM**, a fully automated cold-email agent: paste your domain, it picks an ICP, builds the list, writes the emails and sends them from pre-warmed mailboxes at roughly $0.03 per email.

Its filter set tells you who it was built for: funding stage, hiring status, technologies used, website traffic, "remote teams", "founders' origin". That is a venture-backed SaaS prospecting tool. Location, headcount and industry filters exist, but they are not the centre of gravity.

**Company facts**

| Item | Finding |
|---|---|
| Legal entity | Explee Ltd, company no. 15759064, incorporated 4 June 2024, registered at a London virtual-office address (International House, 50 Essex Street) |
| Team | 1 to 10 employees per Crunchbase; one angel round, amount undisclosed |
| Founders | Thomas Olivier (CEO), Morgan Giraud (CTO), plus Alex Kataev and Khariton Matveev |
| Reviews | 5 reviews on G2, all 5 stars, no new review in the last two months. No Trustpilot or Reddit footprint found |
| Domain history | explee.com was previously a whiteboard-animation video product. Several directories still merge the two, which is why some write-ups say "founded 2011" and mention "video presentations" |

**Claimed pricing** (sources conflict, so ranges are given)

| Plan | Price | Credits | Roughly buys |
|---|---|---|---|
| Free | $0 | 500 welcome credits; other sources say 200 or 333 free emails | A test run |
| Starter | $49/mo | 5,000 credits, valid 2 months | Up to 3,333 emails or 500 phones per month |
| Growth | $329/mo | 40,000 credits, valid 2 months | Up to 26,666 emails or 4,000 phones per month |
| Pro | $490/mo | Not documented in accessible sources | |
| Top-up | $1 per 100 credits | | ~1.5 credits per email, ~10 per phone |
| AutoGTM | ~$0.03 per email sent, $50 free credit | Pay as you go | |

Refunds are pro-rated within the first 30 days. Cancellation is in-app.

**Claimed data** (again, inconsistent): 40M, 74M, 75M, 103M or 105M companies depending on the page; 536M people profiles; "under 3% bounce" and "97% deliverability" via a verification chain ending in ZeroBounce. Sources are described as web crawl plus LinkedIn plus funding and hiring datasets. No UK-specific coverage figure is published anywhere I could reach.

---

## 2. Why it is a poor fit for Layered

### 2.1 It sells contacts. Layered needs intent.

Layered's product is a bespoke AI system for a business that already feels a specific pain: staff asking the same questions, enquiries answered late, Friday spent reconciling spreadsheets. The site is built around that ("Tell us what's eating your time"). The existing `scraper/` in this repo works the same way: it finds people publicly saying they need something, then filters with Claude.

Explee does the opposite. It returns a firmographic list with no signal that anyone is looking. A Lake District hotel with 60 staff might be a perfect Gilpin lookalike, but Explee cannot tell you whether the GM is fed up with onboarding or perfectly happy. Every contact starts cold, and a bespoke build costing thousands of pounds is not something an owner-manager buys off a cold email.

Illustrative funnel, using ordinary cold-email benchmarks rather than anything Explee-specific:

| Stage | Assumption | Result from 1,000 emails |
|---|---|---|
| Delivered | 95% | 950 |
| Any reply | 2% | ~19 |
| Positive reply | 0.5 to 1% | 5 to 10 |
| Scoping call booked | half of positives | 2 to 5 |
| Project won | 1 in 4 calls | 0 to 1 |

The Explee cost of those 1,000 emails is about $15 to $50. That is not where the cost sits. The cost is the writing, the follow-up, the domain reputation, and the compliance exposure below. If one project a quarter comes out of it the maths may still work, but it is a full-time-ish outbound habit, not a lead source you switch on.

### 2.2 Its index is built for startups, not for Cumbrian SMEs

Layered's proof points are a five-star hotel, a 1946 construction firm and a yacht-owner platform. These are owner-managed businesses, often unincorporated or with a single generic `info@` address, thin LinkedIn presence, and no funding or hiring data. That is the part of the web a crawl-plus-LinkedIn index covers worst. Expect:

- lower match rates on person-level emails for small firms (you will get `info@` and `enquiries@`, which the credit still charges for)
- weak coverage of sole traders and partnerships, who form a large share of local service businesses
- semantic queries like "hotels in the Lake District with more than 30 staff" to work reasonably, but "businesses drowning in admin" to return noise, because the pain is not observable from a website

No accessible source publishes Explee's UK company count, so this is inference from how the index is described, not a measured fact. It is the single most important thing the free-tier test in section 4 should settle.

### 2.3 Compliance risk is real for this specific target market

- **PECR:** limited companies and LLPs can be cold-emailed without consent. **Sole traders and non-LLP partnerships count as individual subscribers** and need consent or the soft opt-in. Layered's natural market is full of them. Explee's data does not tell you which is which.
- **UK GDPR:** Explee's terms make **you** the controller and disclaim liability for fines. Its data is scraped from public sources and LinkedIn. You would need a legitimate-interests assessment and a privacy notice covering purchased data before the first send.
- **Penalties:** since February 2026 the PECR maximum is £17.5m or 4% of turnover under the Data (Use and Access) Act. The ICO has been actively enforcing against small lead-gen operators.
- **AutoGTM specifically** sends from pre-warmed shared mailboxes it provisions. That means outreach in Layered's name from domains Layered does not control, with copy Layered did not write, to a list Layered did not vet. That is directly at odds with a brand whose pitch is "we're not a faceless agency" and "you deal with the person building your system".

### 2.4 Vendor risk

A two-year-old company with under ten staff, one angel round, five reviews, inconsistent marketing numbers and a pivoted domain. None of that makes it a bad product. It does mean nothing about Layered's pipeline should depend on it, and any list you pull should be exported immediately, because credits expire after two months and the company may not exist in 2028.

### 2.5 A note on the existing scraper

While checking fit I read `scraper/config.yaml`. Its `business_context` still describes Layered as "a small web design agency ... 3-10 page site, £500-£3000", and the queries are all "need a web designer". That predates the July brand reframe. Of the 18 leads in `leads.csv`, 17 are Freelancer.com website RFPs in the £250 to £750 bracket. Whatever you decide about Explee, the intent scraper is currently generating leads for a business Layered no longer positions itself as. Fixing that is cheaper and closer to the right customer than any list tool.

---

## 3. Where Explee could genuinely help

Used as a **research and targeting tool**, not a lead generator:

1. **Lookalike lists for one segment at a time.** "Independent hotels in Cumbria and the Lake District with 20 to 150 staff" is exactly the kind of query semantic search is good at, and it produces a named-account list you could approach warmly: LinkedIn, a letter, a referral through Gilpin, a local business event.
2. **Sizing a niche before building for it.** Before investing in a hospitality-specific version of the Gilpin platform, a 20-minute Explee search tells you how many plausible buyers exist in the North West.
3. **Enriching leads you already have.** When the intent scraper or a referral surfaces a company name, Explee can supply a decision-maker's name and a verified email cheaply.

All three fit inside the free tier or a single $49 month.

---

## 4. Recommended test (one hour, £0)

Run before deciding anything. Success criteria are set in advance so the outcome cannot be rationalised afterwards.

| Step | What to do | Pass if |
|---|---|---|
| 1 | Sign up free (no card). Search: "independent hotels in Cumbria / Lake District, 20 to 150 staff" | ≥ 25 real, currently trading hotels returned; Gilpin itself appears |
| 2 | Search: "construction firms in Cumbria, NHBC registered, established 20+ years" | ≥ 15 real firms; Leck Construction appears |
| 3 | Reveal 20 contacts across both lists | ≥ 12 are named people, not `info@`; ≥ 15 have a role that could buy (owner, MD, GM, ops) |
| 4 | Spot-check 10 emails against the companies' own websites or LinkedIn | ≤ 1 obviously wrong or stale |
| 5 | Note how many are sole traders or partnerships | Record it. This is your PECR exposure |

If steps 1 to 4 pass, Explee is worth $49 occasionally for **named-account research** feeding a warm, personal approach. If any of them fail, drop it and spend the time on section 5.

---

## 5. Better-fit alternatives

| Source | What it gives | Cost | Fit for Layered |
|---|---|---|---|
| Existing intent scraper, re-tuned to the AI positioning | People publicly describing operational pain | Already built, < $1/mo | Best fit. Currently mis-targeted (section 2.5) |
| Companies House API | Every UK company: SIC code, age, size band, incorporation status (which settles the PECR question) | Free | Strong for building a compliant UK list |
| Google Maps scraping (Outscraper, Apify) | Local businesses by category and area, with website and phone | ~$9 to $14 per 1,000 fully enriched | Good for local service businesses that never appear in B2B databases |
| Apollo.io | Broad B2B database with sequencing | $49 to $59 per user/month | Same intent problem as Explee, bigger index, better tooling |
| Cognism | UK-strong data with mobile numbers | ~$15k+/year platform fee | Enterprise pricing, far beyond need |
| Explee | Semantic company search, cheap verified emails | Free to $49/month | Niche research tool only |

---

## 6. Bottom line

Explee is a cheap, plausibly decent list-builder aimed at startup outbound teams. Layered sells a considered, high-trust, high-ticket engagement to owner-managed UK businesses who need to be feeling the pain before they call. Those two things do not meet in the middle. The tool costs almost nothing, so run the one-hour test for named-account research. Do not build a pipeline on it, and do not let AutoGTM send email in Layered's name.

---

## Sources

- G2: Explee reviews and pricing — https://www.g2.com/products/explee/reviews
- Companies House: EXPLEE LTD 15759064 — https://find-and-update.company-information.service.gov.uk/company/15759064
- Crunchbase: Explee — https://www.crunchbase.com/organization/explee
- ColdIQ: Explee review, features, pricing — https://coldiq.com/tools/explee
- aidirectori.es: Explee review — https://www.aidirectori.es/blog/explee-review
- Futurepedia: Explee — https://www.futurepedia.io/tool/explee
- Cleanlist: 10 AI lead gen tools tested, pricing and limits — https://www.cleanlist.ai/blog/2026-03-31-best-ai-lead-generation-tools
- TestingCatalog: Explee launches AutoGTM — https://www.testingcatalog.com/explee-launches-autogtm-ai-agent-for-outbound-sales/
- Explee pricing (mirror) — https://explee.org/pricing
- Explee terms of use and privacy policy — https://explee.com/terms-of-use, https://explee.com/privacy-policy
- ICO: business-to-business marketing — https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/
- salespeople.co.uk: cold email under PECR regulation 22 — https://www.salespeople.co.uk/explained/cold-email-pecr-regulation-22
- Puzzle Inbox: UK cold email PECR and UK GDPR 2026 — https://puzzleinbox.com/blog/cold-email-uk-pecr-2026
- Warmly: Apollo pricing 2026 — https://www.warmly.ai/p/blog/apollo-pricing
- SyncGTM: Outscraper review 2026 — https://syncgtm.com/blog/outscraper-review-2026
- Landbase: Cognism pricing 2026 — https://www.landbase.com/blog/cognism-pricing
- Litemail: pre-warmed inboxes for cold email — https://litemail.ai/blog/pre-warmed-inboxes-cold-email-guide
