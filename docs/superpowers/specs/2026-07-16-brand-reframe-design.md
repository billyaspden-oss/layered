# Brand Reframe — Problem-First AI Positioning

**Date:** 2026-07-16
**Scope:** Copy and structure across index.html, ai.html, seo.html, contact.html, thank-you.html
**Explicitly out of scope:** Visual redesign, new pages, URL changes, pricing/productisation, removal of Leck/preview pages, scraper/functions machinery

## 1. Goal

Reposition Layered from a general web agency ("bespoke websites + AI") to a niche problem-solver: **AI systems that solve business problems**, framed around business needs and frustrations. Websites stop being a pitched service and become a delivery detail.

## 2. Decisions made

| Question | Decision |
|---|---|
| Websites as an offering | Delivery detail only — never pitched, still built when the solution needs one |
| Geography | Keep local anchor, soften: "based in Kendal, working with businesses anywhere" |
| Lead pain points | All four: repetitive admin, knowledge trapped in heads, leads slipping through, disconnected tools |
| Scope | Full site overhaul (all four main pages + thank-you) |
| Approach | Problem-first narrative (Approach A), with honest real numbers woven in where they exist |

## 3. Messaging foundation

- **Positioning statement:** Layered builds AI systems that take real work off your plate — for businesses tired of drowning in admin, repeating themselves, and juggling tools that don't talk to each other. Based in Kendal, working with businesses anywhere.
- **Voice:** plain-English, honest, no jargon (existing discipline retained). Every section opens in the customer's words — naming the frustration — before mentioning technology.
- **"Bespoke website" disappears sitewide as a pitch.** Single delivery-detail line: "When the solution needs a front door, we build that too — fast, found on Google, and wired into the system behind it."
- **Honesty differentiator, promoted:** the free scoping call ends with an honest verdict on whether AI is worth building — or not.
- **Honest-claims rule:** only real numbers (Plato live in production at a five-star hotel, 8 departments, 24hr quote turnaround). No invented stats.

## 4. The four frustrations → solutions → proof map

| Frustration (customer's words) | Solution type | Proof |
|---|---|---|
| Drowning in repetitive admin | Workflow automations | Capability set (ai.html) |
| Knowledge trapped in people's heads ("ask Dave") | Knowledge platforms | **Plato / Gilpin Hotel** (live, featured) |
| Leads and enquiries slipping through | Assistants & enquiry handling | Chat demo in hero card; SEO page as "get found" layer |
| Tools that don't talk / manual processes | Bespoke ops platforms | **Boat HQ** |

## 5. Page designs

### 5.1 index.html (full copy/structure rewrite; visual system unchanged)

1. **Hero (dark):** pain-led headline, territory: "Half your week is work a system should be doing." Sub: Layered builds AI systems that answer the questions, chase the leads, and shift the admin — so your team does the work only they can do. CTAs: "Book a free scoping call" / "See what we've built". Stats row → honest proof: *In production at a five-star hotel · Quote within 24 hours · Built in Kendal, works anywhere*. Browser-mockup card keeps AI-chat animation with aligned copy.
2. **"Sound familiar?"** — four frustration cards, each written as the owner's inner monologue, each ending with one line on what we build for it. Replaces the services grid as the emotional spine.
3. **"What we build"** — four solution types (automations, knowledge platforms, assistants, ops platforms). Websites appear here only as the delivery-detail line.
4. **Proof** — portfolio reframed "problems we solved". Order: Plato/Gilpin (featured), Boat HQ, Leck (recaptioned as a front-door build for a business that needed to be found).
5. **Why Layered** — small and personal; we run these systems ourselves; we tell you when AI *isn't* worth it; rooted in Cumbria, not bounded by it.
6. **Process** — Scoping call → Map the problem → Build in phases → Run & improve.
7. **Contact (dark)** — heading: "Tell us what's eating your time."

**Nav:** What we solve · Work · How we build · Process · Contact. SEO demoted to footer.

### 5.2 ai.html — "How we build" (alignment pass)

- Hero sub drops "for Cumbria businesses" phrasing in favour of the softened geography; "AI built for your business, not bolted on" headline stays.
- "Three kinds of AI work" gains the fourth pattern (bespoke ops platforms) to match the homepage's four solution types.
- Nav label "AI" → "How we build".
- Capabilities grid, Plato case study, five-phase process: unchanged.

### 5.3 seo.html — supporting "get found" layer (intro reframe)

- Intro reframed: leads slipping through starts with customers not finding you.
- Leaves main nav; linked from footer, the "leads" frustration card, and the front-door delivery line.
- Title tag keeps local SEO terms (this page carries the "web/SEO Cumbria" equity).
- Layer content unchanged.

### 5.4 contact.html (rewrite)

- Hero: "Tell us what's eating your time." Sub keeps 24-hour plain-English promise.
- Service dropdown → problem types: Too much repetitive admin · Knowledge stuck in people's heads · Leads slipping through · Tools that don't talk to each other · We need a website · Not sure — let's talk. ("We need a website" retained as an option; not pitched.)
- Title: drops "Free Web Design Consultation" → "Book a free scoping call".

### 5.5 thank-you.html — one-line alignment pass only.

## 6. SEO / metadata

- **index.html:** title → territory of "AI Systems That Solve Business Problems · Kendal | Layered". Meta description, keywords, OG/Twitter tags rewritten to match. Schema `serviceType` → `["AI Systems Integration", "Business Process Automation", "Web Development"]` (web dev retained in schema for long-tail, never leads).
- **ai.html, contact.html:** titles/meta updated to new frame.
- **seo.html:** keeps local-search title equity.
- **No URL changes**; sitemap and canonicals untouched — zero redirect risk.
- **Accepted trade-off:** "web design Kendal" homepage equity weakens over time. Deliberate cost of niching.

## 7. Error handling / risk

- Contact form field name/values change (dropdown): keep the underlying form field name and submission handling identical unless the handler (functions/) is verified to accept new option values — check before editing.
- Any copy claiming outcomes must trace to a real deployment or be softened ("designed to", "built to").

## 8. Testing / verification

- Serve locally and click through all pages: nav links (including renamed labels), footer links, frustration-card links to seo.html/ai.html, contact dropdown submit path.
- Validate JSON-LD parses (paste into a schema validator or JSON parse the script block).
- Grep sitewide for leftover "bespoke website" pitch language and old nav labels.
- Visual check on mobile widths (existing responsive CSS reused, so risk is low).
