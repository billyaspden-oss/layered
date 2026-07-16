# Brand Reframe Implementation Plan — Problem-First AI Positioning

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition the Layered site from "bespoke websites + AI" to problem-first AI systems across index.html, ai.html, seo.html, contact.html, thank-you.html, per `docs/superpowers/specs/2026-07-16-brand-reframe-design.md`.

**Architecture:** Static HTML pages with inline CSS/JS, deployed on Cloudflare Pages (functions/ dir holds the contact API). This is a copy/structure rewrite reusing the existing CSS classes — no new stylesheets, no URL changes, no visual redesign. Each page's nav is duplicated markup and must be edited per page.

**Tech Stack:** Plain HTML/CSS/JS, Cloudflare Pages Functions (contact.js), Resend email API.

## Global Constraints

- Visual design system unchanged: reuse existing classes (`svc-grid`, `svc`, `svc-dark`, `svc-full`, `pc`, `pc feat`, `wc`, `ps`, etc.). No new CSS unless a step says so.
- No URL changes; sitemap.xml and canonicals untouched.
- The `#services` id on index.html MUST remain (subpages deep-link `/#services`). New frustrations section gets id `#problems`.
- "Bespoke website(s)" never appears as a pitch anywhere. One delivery-detail mention only (Task 3 strip).
- Honest-claims rule: no invented numbers. Allowed claims: Plato live in production at a five-star hotel; 8 departments; 24hr quote turnaround; free scoping call.
- Voice: plain English, no jargon, customer's-words-first.
- Form field names (`name`, `email`, `phone`, `service`, `message`) unchanged.
- HTML entity escaping: use `&amp;` in HTML text, `—` em-dashes as literal chars (file already does this).
- Commit after every task; run the task's verify step before committing.
- The site is static: "test" = grep assertions + local serve + JSON parse of the JSON-LD block. Local serve: `cd` to repo root, `uv run python3 -m http.server 8080`, then `curl -s localhost:8080/index.html | grep ...` or open in browser.

---

### Task 1: index.html — head metadata + JSON-LD

**Files:**
- Modify: `index.html:6-48` (title, meta description/keywords, OG/Twitter, JSON-LD)

**Interfaces:**
- Produces: new page title / meta copy that Tasks 2–5 must stay consistent with.

- [ ] **Step 1: Rewrite title/meta/OG/Twitter**

Replace lines 6–8 content:

```html
<title>AI Systems That Solve Business Problems · Kendal | Layered</title>
<meta name="description" content="Layered builds AI systems that take real work off your plate — workflow automations, knowledge platforms, assistants, and bespoke ops platforms. Based in Kendal, working with businesses anywhere. Free scoping call.">
<meta name="keywords" content="AI systems for business, business process automation, AI knowledge platform, AI assistant for business, workflow automation Cumbria, AI integration Kendal, bespoke business software">
```

Replace the OG/Twitter title/description values (lines 14–18):

```html
<meta property="og:title" content="AI Systems That Solve Business Problems · Kendal | Layered">
<meta property="og:description" content="AI systems that take real work off your plate — automations, knowledge platforms, assistants, and ops platforms. Based in Kendal, working with businesses anywhere.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="AI Systems That Solve Business Problems · Kendal | Layered">
<meta name="twitter:description" content="AI systems that take real work off your plate. Based in Kendal, working with businesses anywhere. Free scoping call.">
```

- [ ] **Step 2: Update JSON-LD**

In the `<script type="application/ld+json">` block, change two values only:

```json
"description": "AI systems that solve business problems — workflow automations, knowledge platforms, assistants, and bespoke operations platforms. Based in Kendal, Cumbria, working with businesses anywhere.",
"serviceType": ["AI Systems Integration", "Business Process Automation", "Web Development"],
```

Also change `"areaServed"` to `["Cumbria", "Lake District", "North West England", "United Kingdom"]`.

- [ ] **Step 3: Verify**

```bash
cd "/Users/billyaspden/Documents/Website dev/web-agency"
uv run python3 -c "
import re, json
html = open('index.html').read()
block = re.search(r'<script type=\"application/ld\+json\">(.*?)</script>', html, re.S).group(1)
data = json.loads(block)
assert data['serviceType'][0] == 'AI Systems Integration', data['serviceType']
assert 'United Kingdom' in data['areaServed']
print('JSON-LD OK')
"
grep -c "AI Systems That Solve Business Problems" index.html   # expect 3 (title, og, twitter)
```

- [ ] **Step 4: Commit**

```bash
git add index.html && git commit -m "reframe: index head metadata + schema to problem-first AI positioning"
```

---

### Task 2: index.html — nav, mobile menu, hero

**Files:**
- Modify: `index.html:1125-1152` (nav-links + mobile menu), `index.html:1157-1213` (hero)

**Interfaces:**
- Produces: nav labels/targets that Tasks 6–9 replicate on subpages: What we solve → `#problems` (subpages: `/#problems`), Work → `#portfolio`, How we build → `ai.html`, Process → `#process`, Contact → `contact.html`, CTA "Book a scoping call" → `contact.html`. SEO leaves main nav (footer only).

- [ ] **Step 1: Replace nav links (lines 1125–1134)**

```html
      <ul class="nav-links">
        <li><a href="#problems">What we solve</a></li>
        <li><a href="#portfolio">Work</a></li>
        <li><a href="ai.html">How we build</a></li>
        <li><a href="#process">Process</a></li>
        <li><a href="contact.html">Contact</a></li>
      </ul>
      <a href="contact.html" class="nav-cta">Book a scoping call</a>
```

- [ ] **Step 2: Replace mobile menu links (lines 1144–1151)**

```html
  <div class="mm-link"><a href="#problems">What we solve</a></div>
  <div class="mm-link"><a href="#portfolio">Work</a></div>
  <div class="mm-link"><a href="ai.html">How we build</a></div>
  <div class="mm-link"><a href="#process">Process</a></div>
  <div class="mm-link"><a href="contact.html">Contact</a></div>
  <div class="mm-link"><a href="contact.html" class="mm-cta">Book a scoping call</a></div>
```

- [ ] **Step 3: Rewrite hero header (lines 1161–1172)**

```html
      <div class="h-label li li1">AI Systems for Business &nbsp;·&nbsp; Kendal, Cumbria</div>
      <h1 class="h-title li li2">Half your week is work<br>a <span class="accent">system</span> should be doing.</h1>
      <p class="h-sub li li3">Layered builds AI systems that answer the questions, chase the admin, and keep the knowledge — so your team can do the work only they can do. Based in Kendal. Working with businesses anywhere.</p>
      <div class="h-acts li li4">
        <a href="contact.html" class="btn btn-p">Book a free scoping call <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
        <a href="#portfolio" class="btn btn-g">See what we've built <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
      </div>
      <div class="h-stats li li5">
        <div class="h-stat"><div class="h-stat-n">Live</div><div class="h-stat-l">In production at a five-star hotel</div></div>
        <div class="h-stat"><div class="h-stat-n">24hr</div><div class="h-stat-l">Quote turnaround</div></div>
        <div class="h-stat"><div class="h-stat-n">&infin;</div><div class="h-stat-l">Support after launch</div></div>
      </div>
```

- [ ] **Step 4: Align the hero-card mockup copy (lines 1175, 1195–1198)**

Change the card's `aria-label` to `"A Layered build: a business system with an embedded AI assistant"`.
Change the eyebrow text `Bespoke websites &amp; AI systems` → `AI systems for real work`.
Keep the headline `Built for the way you work.` Change the sub-line
`Fast, bespoke, and wired with intelligent automation, designed and built around your business.` →
`Answers customers, books the work, and keeps your knowledge in one place — around the clock.`
Change the mockup CTA `Start a project &#8594;` → `Book a call &#8594;`. Leave the AI-chat panel untouched.

- [ ] **Step 5: Verify**

```bash
grep -c "Book a scoping call\|Book a free scoping call" index.html   # expect >= 3
grep -c "We build the web" index.html                                 # expect 0
grep -c "crafts bespoke websites" index.html                          # expect 0
```

- [ ] **Step 6: Commit**

```bash
git add index.html && git commit -m "reframe: index nav + hero to pain-led AI positioning"
```

---

### Task 3: index.html — "Sound familiar?" section, "What we build", remove deeper section

**Files:**
- Modify: `index.html:1219-1335` (services section rewritten to two sections; deeper section deleted)

**Interfaces:**
- Consumes: nav target `#problems` from Task 2.
- Produces: `#problems` section; `#services` section retitled "What we build" (id preserved); links to `ai.html` and `seo.html` that replace the deleted deeper cards.

- [ ] **Step 1: Insert the frustrations section**

Immediately BEFORE `<section class="sec services-wrap" id="services">` insert:

```html
<!-- PROBLEMS -->
<section class="sec services-wrap" id="problems">
  <div class="wrap">
    <div class="sec-hdr rv">
      <h2>Sound familiar?</h2>
      <p>Most businesses we talk to aren't looking for "AI". They're looking for a way out of the same four frustrations.</p>
    </div>

    <div class="svc-grid">

      <div class="svc rv d1">
        <div class="svc-num">01</div>
        <h3>Drowning in repetitive admin</h3>
        <p>Every week disappears into copying data between spreadsheets, formatting the same reports, chasing the same paperwork. It isn't skilled work — it just has to be done.</p>
        <ul>
          <li>We build workflow automations that do it for you — accurately, instantly, every time.</li>
        </ul>
      </div>

      <div class="svc rv d2">
        <div class="svc-num">02</div>
        <h3>The knowledge lives in someone's head</h3>
        <p>New starters shadow whoever's free. Standards drift. And when your most experienced person is off, everyone else waits — or guesses.</p>
        <ul>
          <li>We build knowledge platforms trained on your own documents — every answer instant, accurate, and cited.</li>
        </ul>
      </div>

      <div class="svc rv d3">
        <div class="svc-num">03</div>
        <h3>Leads slip through the cracks</h3>
        <p>Enquiries land at 9pm and get answered at lunchtime. Follow-ups get forgotten. Every slow reply is a customer who called someone else. And if they never found you at all, the problem starts a step earlier — <a href="seo.html" style="color:var(--accent);font-weight:600">that's our get-found layer</a>.</p>
        <ul>
          <li>We build assistants that answer instantly, capture the details, and book the work — day and night.</li>
        </ul>
      </div>

      <div class="svc rv d4">
        <div class="svc-num">04</div>
        <h3>Your tools don't talk to each other</h3>
        <p>The calendar doesn't know what the spreadsheet knows. Nothing quite matches, and someone spends every Friday reconciling it all by hand.</p>
        <ul>
          <li>We build bespoke ops platforms — one system, one source of truth, built around how you actually work.</li>
        </ul>
      </div>

    </div>
  </div>
</section>
```

Note: `.d4` transition-delay class already exists in the CSS (line 128). The reveal JS attaches to all `.rv` elements generically — no JS change needed.

- [ ] **Step 2: Rewrite the services section into "What we build"**

Replace the entire existing `#services` section content (header + three `svc` cards, lines 1219–1287) with:

```html
<!-- WHAT WE BUILD -->
<section class="sec" id="services" style="background:var(--bg-alt)">
  <div class="wrap">
    <div class="sec-hdr rv">
      <h2>What we build to fix it.</h2>
      <p>Four kinds of system, matched to the four frustrations — every one built around your business: your documents, your tools, your way of working.</p>
    </div>

    <div class="svc-grid">

      <div class="svc rv d1">
        <div class="svc-num">01</div>
        <div class="svc-ico" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg>
        </div>
        <h3>Workflow automations</h3>
        <p>Background systems that handle the repeatable work — categorising, drafting, summarising, moving data — without a human in the loop.</p>
        <ul>
          <li>Enquiry and paperwork triage</li>
          <li>Reports drafted and formatted automatically</li>
          <li>Data moved between systems, not re-typed</li>
          <li>Runs around the clock, never forgets a step</li>
        </ul>
      </div>

      <div class="svc svc-dark rv d2">
        <div class="svc-num">02</div>
        <div class="svc-badge">Live at a five-star hotel</div>
        <div class="svc-ico" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20M4 19.5A2.5 2.5 0 006.5 22H20V2H6.5A2.5 2.5 0 004 4.5v15z"/></svg>
        </div>
        <h3>Knowledge platforms</h3>
        <p>Your SOPs, policies and know-how turned into an assistant that answers instantly — with citations, and "I don't know" when your sources don't say.</p>
        <ul>
          <li>Trained on your own documents, nothing invented</li>
          <li>Every answer cited back to the source</li>
          <li>Training, quizzes and sign-off built in</li>
          <li>In production at The Gilpin Hotel across 8 departments</li>
        </ul>
      </div>

      <div class="svc rv d3">
        <div class="svc-num">03</div>
        <div class="svc-ico" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
        </div>
        <h3>Assistants &amp; enquiry handling</h3>
        <p>Customer-facing AI that answers questions, captures leads and books work in your own voice — at 9pm on a Sunday as reliably as 9am on a Monday.</p>
        <ul>
          <li>Answers grounded in your real prices and policies</li>
          <li>Captures the details a missed call loses</li>
          <li>Hands over to a human the moment it should</li>
          <li>Embedded wherever your customers already are</li>
        </ul>
      </div>

      <div class="svc rv d4">
        <div class="svc-num">04</div>
        <div class="svc-ico" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
        </div>
        <h3>Bespoke ops platforms</h3>
        <p>When the spreadsheets stop scaling: one system for the whole operation — tasks, records, schedules — with an AI that knows your business inside out.</p>
        <ul>
          <li>One source of truth instead of five almost-matching ones</li>
          <li>Built around your workflow, not a template's</li>
          <li>AI assistant grounded in your own operational data</li>
          <li>Grows with the business instead of fighting it</li>
        </ul>
      </div>

      <!-- Delivery detail: websites + hosting fold in here, never pitched -->
      <div class="svc svc-full rv d3">
        <div>
          <div class="svc-num">&amp;</div>
          <h3>And yes — websites too.</h3>
          <p>When the solution needs a front door, we build that too: fast, found on Google, and wired into the system behind it. It's just never the point — the point is the problem it solves.</p>
        </div>
        <ul>
          <li>Hosting, SSL, domains and backups — all looked after</li>
          <li>Search visibility built in, not bolted on</li>
        </ul>
        <ul>
          <li><a href="ai.html" style="color:var(--accent);font-weight:600">How we build AI systems &rarr;</a></li>
          <li><a href="seo.html" style="color:var(--accent);font-weight:600">The get-found layer &rarr;</a></li>
        </ul>
      </div>

    </div>
  </div>
</section>
```

Note: the original `#services` had class `services-wrap` (white surface); the new `#problems` takes that class, and `#services` uses `background:var(--bg-alt)` for alternation against the portfolio section's `bg-alt`… **check adjacent backgrounds after edit**: order is problems (surface) → services (bg-alt) → portfolio (bg-alt). Two `bg-alt` sections adjacent is acceptable but flat — if it looks flat in the browser check, set the new `#services` to `style="background:var(--bg)"` instead.

- [ ] **Step 3: Delete the deeper section**

Delete the entire `<section class="sec deeper-wrap" id="deeper">…</section>` block (originally lines 1290–1335) including the `<!-- DEEPER … -->` comment. Its ai.html/seo.html links now live in the nav ("How we build") and the delivery-detail strip.

- [ ] **Step 4: Verify**

```bash
grep -c 'id="problems"' index.html            # expect 1
grep -c 'id="services"' index.html            # expect 1
grep -c 'id="deeper"' index.html              # expect 0
grep -c "Never a template. Never a theme." index.html   # expect 0
grep -c 'Sound familiar' index.html           # expect 1
uv run python3 -m http.server 8080 &  # then eyeball http://localhost:8080 section flow; kill afterwards
```

- [ ] **Step 5: Commit**

```bash
git add index.html && git commit -m "reframe: replace services pitch with four-frustration spine + what-we-build"
```

---

### Task 4: index.html — portfolio reorder + recaption (Gilpin featured)

**Files:**
- Modify: `index.html` portfolio section (`id="portfolio"`, originally lines 1338 onward)

**Interfaces:**
- Consumes: `.pc.feat` CSS (full-width card with `.pb-head` + `.feat-side`) already defined at lines 721–745.

- [ ] **Step 1: Rewrite the section header**

```html
      <div>
        <h2 style="font-family:var(--display);font-size:clamp(2rem,4vw,3rem);font-weight:700;letter-spacing:-.035em;line-height:1.04;color:var(--text)">Problems we've solved.</h2>
      </div>
      <a href="contact.html" class="btn btn-gl" style="flex-shrink:0">Book a scoping call <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" width="13" height="13"><path d="M5 12h14M12 5l7 7-7 7"/></svg></a>
```

- [ ] **Step 2: Make Gilpin the featured card and move it first**

Reorder the three `.pc` cards inside `.port-grid` to: **Gilpin (featured, full-width) → Boat HQ → Leck**.

For Gilpin: change its wrapper `<div class="pc rv d2">` to `<div class="pc feat rv d1">`. Keep the entire preview `.pt`/`.pg` block and `Live` badge exactly as-is. Replace its `.pb` block with the feat layout:

```html
        <div class="pb">
          <div class="pb-head">
            <div class="p-tag">Knowledge trapped in heads &rarr; solved</div>
            <h3>Plato — AI training for The Gilpin Hotel &amp; Lake House</h3>
            <p>A five-star Lake District hotel needed every staff member, across eight departments, answered instantly and accurately. We built two apps on one knowledge base: a staff-facing assistant trained on Gilpin's own SOPs, and the admin tool where department heads author and govern the source material. Live in production.</p>
          </div>
          <div class="feat-side">
            <div class="feat-side-label">Inside the system</div>
            <div class="feat-meta">
              <span class="chip">Custom RAG</span>
              <span class="chip">Cited answers</span>
              <span class="chip">Voice + TTS</span>
              <span class="chip">AI training videos</span>
              <span class="chip">Quizzes &amp; streaks</span>
              <span class="chip">SOP governance</span>
              <span class="chip">8 departments</span>
              <span class="chip">Audit log</span>
            </div>
          </div>
        </div>
```

- [ ] **Step 3: Demote Boat HQ to a standard card, problem-framed caption**

Change its wrapper `<div class="pc feat rv d3">` to `<div class="pc rv d2">`. Keep its preview `.pg` intact (the standard `.pt` crops it to 240px — acceptable). Replace its `.pb` (the pb-head + feat-side + "Built with" chips block) with a standard caption:

```html
        <div class="pb">
          <div class="p-tag">Tools that don't talk &rarr; solved</div>
          <h3>Boat HQ</h3>
          <p>A complete operations platform for live-aboard yacht owners — maintenance, voyages, manuals, crew and inventory in one system, with an AI assistant grounded in the boat's own documentation. In development.</p>
        </div>
```

- [ ] **Step 4: Recaption Leck as a front-door build**

Change its wrapper to `<div class="pc rv d3">`, keep preview and badge, replace the `.pb`:

```html
        <div class="pb">
          <div class="p-tag">A front door that gets found</div>
          <h3>Leck Construction Ltd</h3>
          <p>When the solution is being found and trusted, we build that too — a complete redesign for one of Cumbria's longest-established construction firms. Est. 1946, NHBC Grade A.</p>
        </div>
```

- [ ] **Step 5: Verify**

```bash
grep -n 'class="pc feat' index.html            # expect exactly 1 match, the Gilpin card
uv run python3 -m http.server 8080 &            # eyeball: Gilpin full-width first, Boat HQ + Leck below; kill afterwards
```
Check on a ~375px viewport too (responsive CSS collapses feat to single column).

- [ ] **Step 6: Commit**

```bash
git add index.html && git commit -m "reframe: portfolio reordered problem-first, Gilpin/Plato featured"
```

---

### Task 5: index.html — why, process, contact heading, footer

**Files:**
- Modify: `index.html` sections `#about` (1625), `#process` (1668), `#contact` (1710), footer (1788)

- [ ] **Step 1: Rewrite the why section (`#about`)**

Sticky header block:

```html
      <h2>Problems first. Technology second.</h2>
      <p>We're not a faceless agency selling AI because it's fashionable. We build systems that earn their keep — and we're honest when one wouldn't.</p>
```

Keep the "Work With Us" button. Replace the four `.wc` items:

```html
        <div class="wc rv d1">
          <div class="w-num">01</div>
          <div>
            <h3>We tell you when AI isn't worth it</h3>
            <p>Every project starts with a free scoping call that ends in an honest verdict — including "don't build this". If a £30 off-the-shelf tool solves your problem, we'll point you at it.</p>
          </div>
        </div>
        <div class="wc rv d2">
          <div class="w-num">02</div>
          <div>
            <h3>We run these systems ourselves</h3>
            <p>We're not reselling someone else's widget. The platforms we build are our own engineering, running in production every day — including at a five-star Lake District hotel.</p>
          </div>
        </div>
        <div class="wc rv d3">
          <div class="w-num">03</div>
          <div>
            <h3>Small, personal, accountable</h3>
            <p>You deal directly with the person building your system — no account managers, no handoffs, no ticket queues. Questions get answers, not reference numbers.</p>
          </div>
        </div>
        <div class="wc rv d4">
          <div class="w-num">04</div>
          <div>
            <h3>Rooted in Cumbria, not bounded by it</h3>
            <p>We live and work in Kendal and know what local businesses are up against. But systems travel — we work with businesses wherever they are.</p>
          </div>
        </div>
```

(Match the existing `.wc` inner markup structure exactly — check the current file for whether `w-num` and the text sit in separate divs, and mirror it.)

- [ ] **Step 2: Rewrite the process section (`#process`)**

Sticky header: `<h2>Simple from first call to running system.</h2>` and keep/adjust intro `<p>Four clear steps, complete transparency throughout. No surprises, no disappearing acts, no jargon.</p>`. Replace the four `.ps` steps:

```html
01  Scoping call — Free, 30 minutes, plain English. Tell us what's eating your time, and we'll tell you honestly whether a system is worth building — or not.
02  Map the problem — We dig into how the work actually happens — who does it, where it lives, what it costs you — then propose the smallest system that fixes it. Fixed price, no surprises.
03  Build in phases — The system takes shape in working stages you can try as they land. You always know where things stand — nothing arrives as a big reveal.
04  Run &amp; improve — We host it, watch it, and keep it sharp as your business changes. Still here when you need us six months — or six years — down the line.
```

(Wrap each in the existing `.ps` / `.ps-n` / `.ps-t` / `.ps-d` markup, mirroring the current structure.)

- [ ] **Step 3: Contact section heading**

Replace `<h2>` and intro `<p>` in `#contact`:

```html
        <h2>Tell us what's eating your time.</h2>
        <p>Describe the frustration — the admin, the questions, the chasing — in your own words. We'll come back with a plain-English answer and a clear price, usually within 24 hours.</p>
```

- [ ] **Step 4: Footer**

Replace tagline `Web development &amp; AI systems integration, engineered layer by layer.` →
`AI systems that solve business problems, engineered layer by layer.`

Replace the footer nav links:

```html
        <a href="#problems">What we solve</a>
        <a href="#portfolio">Work</a>
        <a href="ai.html">How we build</a>
        <a href="#process">Process</a>
        <a href="seo.html">SEO</a>
        <a href="contact.html">Contact</a>
```

Replace the footer bottom line `// Kendal, Cumbria · Web Development &amp; AI Systems` →
`// Kendal, Cumbria &nbsp;·&nbsp; AI Systems for Business`.

- [ ] **Step 5: Verify**

```bash
grep -c "faceless agency sending automated emails" index.html   # expect 0
grep -c "Tell us what's eating your time" index.html            # expect 1
grep -ci "bespoke website" index.html                           # expect 0
```

- [ ] **Step 6: Commit**

```bash
git add index.html && git commit -m "reframe: why/process/contact/footer to problem-first voice"
```

---

### Task 6: ai.html — alignment pass

**Files:**
- Modify: `ai.html:733-759` (nav + mobile menu), hero sub copy, "three kinds" copy, footer links (~line 960)

- [ ] **Step 1: Update nav + mobile menu**

Apply the Task 2 nav (same labels/targets, subpage variant — hash links prefixed `/#`):

```html
      <ul class="nav-links">
        <li><a href="/#problems">What we solve</a></li>
        <li><a href="/#portfolio">Work</a></li>
        <li><a href="ai.html" aria-current="page">How we build</a></li>
        <li><a href="/#process">Process</a></li>
        <li><a href="contact.html">Contact</a></li>
      </ul>
      <a href="contact.html" class="nav-cta">Book a scoping call</a>
```

Mobile menu mirrors the same five links + CTA (same pattern as Task 2 Step 2, with `/#` prefixes).

- [ ] **Step 2: Update `<title>` and hero sub**

Title → `How We Build AI Systems · Grounded, bespoke, in production | Layered`.
Hero headline `AI built for your business, not bolted on.` stays. Hero sub:
`Custom AI systems for Cumbria businesses — chat, voice, video, search, governance, and automation. Built on your own knowledge, integrated into your real tools, deployed to production.` →
`Custom AI systems — chat, voice, video, search, governance, and automation. Built on your own knowledge, integrated into your real tools, deployed to production. Based in Kendal, built for businesses anywhere.`
Also update the page's meta description and any og:/twitter: title/description tags to match the new title framing.

- [ ] **Step 3: Three kinds → four kinds**

In the "One process, applied to three kinds of AI work" section: change the `<h2>` to `One process, applied to <em>four kinds of AI work</em>.` (match existing em/italic markup pattern), and extend the intro paragraph:

`Whether it's a conversational assistant, a full knowledge platform with governance and learning, a background automation handling repeatable work, or a full operations platform running the whole business — the build follows the same five phases, with product and intelligence advancing together.`

Below the existing three tabs (Assistants / Knowledge platforms / Automations), add one sentence after the tab block (matching surrounding paragraph styling):

`Ops platforms — complete business systems like Boat HQ — follow the automation playbook at platform scale: same phases, bigger footprint.`

Do NOT add a fourth tab; the tab JS/content stays untouched.

- [ ] **Step 4: Footer links**

In the footer link row (~line 960), keep SEO/Contact links, change `AI` label to `How we build` if the label text is user-visible (`<a href="ai.html">AI</a>` → `<a href="ai.html">How we build</a>`).

- [ ] **Step 5: Verify**

```bash
grep -c "for Cumbria businesses" ai.html          # expect 0
grep -c "four kinds" ai.html                      # expect >= 1
grep -c 'aria-current="page">How we build' ai.html # expect 1
```

- [ ] **Step 6: Commit**

```bash
git add ai.html && git commit -m "reframe: ai.html aligned — four patterns, softened geography, new nav"
```

---

### Task 7: seo.html — supporting-layer reframe

**Files:**
- Modify: `seo.html` nav + mobile menu (~line 601 area), hero intro paragraph, footer links

- [ ] **Step 1: Update nav + mobile menu**

Same five-link nav as Task 6 Step 1, except no `aria-current` (SEO has left the main nav, so no nav item is current on this page). CTA `Book a scoping call`.

- [ ] **Step 2: Reframe the hero intro**

Keep the headline `Four layers of SEO, each one building on the last.` Replace the intro paragraph:

`A complete SEO package designed for local businesses in Cumbria and the Lake District. We don't sell bolt-ons or tricks — we build the stack from the foundation up, so every month's work compounds the one before.` →

`Leads slipping through often starts a step earlier: customers who never find you. This is our get-found layer — a complete SEO stack for local businesses, built from the foundation up so every month's work compounds the one before.`

Keep the `<title>` as-is (it carries the local-search equity). Leave all four layer sections untouched.

- [ ] **Step 3: Footer links**

In seo.html's footer link row, change the `AI` label → `How we build` and any `Services` label → `What we solve` (pointing at `/#problems`); keep SEO/Contact links as they are.

- [ ] **Step 4: Verify**

```bash
grep -c "get-found layer" seo.html        # expect >= 1
grep -c "What we solve" seo.html          # expect 2 (nav + mobile menu)
```

- [ ] **Step 5: Commit**

```bash
git add seo.html && git commit -m "reframe: seo.html repositioned as the get-found layer"
```

---

### Task 8: contact.html rewrite + service line in the enquiry email

**Files:**
- Modify: `contact.html` (title/meta, nav ~532–570, hero ~575, dropdown ~633, footer)
- Modify: `functions/api/contact.js:17,37-46`

**Interfaces:**
- Consumes: contact.html's submit JS already sends `service` in the JSON payload (line 868) — verified; only the function needs to surface it.

- [ ] **Step 1: Title, meta, hero**

Title → `Book a Free Scoping Call · Layered — Kendal, Cumbria` (update meta description and any og:/twitter: tags on this page to match).
Hero h1 `Let's build something great.` → `Tell us what's eating your time.`
Hero sub → `Describe the frustration in your own words — the admin, the questions, the chasing. We'll come back with a plain-English answer and a clear price, usually within 24 hours.`
Keep the three trust chips, but change `Free, no-obligation quote` → `Free scoping call, honest verdict`.

- [ ] **Step 2: Nav + mobile menu**

Same five-link nav as Task 6 Step 1 with `aria-current="page"` on Contact. CTA `Book a scoping call`.

- [ ] **Step 3: Replace the dropdown options (line 633 area)**

```html
              <label for="fservice">What's the problem?</label>
              <select id="fservice" name="service">
                <option value="" disabled selected>Pick the closest fit…</option>
                <option>Too much repetitive admin</option>
                <option>Knowledge stuck in people's heads</option>
                <option>Leads slipping through</option>
                <option>Tools that don't talk to each other</option>
                <option>We need a website</option>
                <option>Not sure yet — let's talk</option>
              </select>
```

Also update the form intro line `Tell us what you need.` → `Tell us what's getting in the way.` and the message field label `Tell us about your project` → `Describe the problem in your own words` (keep the same `id`/`name`).

In contact.html's footer nav, apply the same label updates as index (Task 5 Step 4): `What we solve` → `/#problems`, `Work` → `/#portfolio`, `How we build` → `ai.html`, `Process` → `/#process`, `SEO` → `seo.html`, `Contact` → `contact.html`. Update the footer tagline to `AI systems that solve business problems, engineered layer by layer.`

- [ ] **Step 4: Surface `service` in the enquiry email**

In `functions/api/contact.js` line 17:

```js
    const { name, email, phone, service, message } = body;
```

And in the `emailBody` array add after the Phone line:

```js
      `Problem: ${service || "Not specified"}`,
```

- [ ] **Step 5: Verify**

```bash
grep -c "Free Web Design Consultation" contact.html   # expect 0
grep -c "Too much repetitive admin" contact.html      # expect 1
grep -c "service" functions/api/contact.js            # expect >= 2
node --check functions/api/contact.js 2>/dev/null || uv run python3 -c "print('use: node --check')"  # syntax check must pass
```

- [ ] **Step 6: Commit**

```bash
git add contact.html functions/api/contact.js && git commit -m "reframe: contact page around problems; include selection in enquiry email"
```

---

### Task 9: thank-you.html — alignment

**Files:**
- Modify: `thank-you.html:231-266`

- [ ] **Step 1: Update the secondary action + copy**

The page's minimal nav (brand + "Back to site") stays. Change the secondary button `<a href="/#services" class="btn btn-g">Our Services</a>` → `<a href="/#problems" class="btn btn-g">What we solve</a>`. Change the primary button label `See Our Work` → `See what we've built` (href stays `/#portfolio`). Body copy already matches the honest voice — leave it.

- [ ] **Step 2: Verify + commit**

```bash
grep -c "/#problems" thank-you.html   # expect 1
git add thank-you.html && git commit -m "reframe: thank-you page links aligned"
```

---

### Task 10: Sitewide sweep + click-through verification

**Files:**
- Read-only verification, plus any stragglers found.

- [ ] **Step 1: Grep sweep for stale positioning**

```bash
cd "/Users/billyaspden/Documents/Website dev/web-agency"
grep -rni "bespoke website" index.html ai.html seo.html contact.html thank-you.html   # expect 0 hits
grep -rn "Start a Project" index.html ai.html seo.html contact.html                    # expect 0 hits (all CTAs now "Book a scoping call")
grep -rn 'href="#services"\|/#services' index.html ai.html seo.html contact.html thank-you.html  # any hits must be intentional (the id still exists; nav should point to #problems)
grep -rn '"AI"</a>\|>AI</a>' index.html ai.html seo.html contact.html                  # expect 0 (nav label is now "How we build")
```

Fix anything the sweep catches; the only permitted "website" mentions are the Task 3 delivery strip, the Leck caption, the contact dropdown option, and schema/keywords.

- [ ] **Step 2: JSON-LD + link check**

```bash
uv run python3 - <<'EOF'
import re, json, pathlib
html = pathlib.Path('index.html').read_text()
for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
    json.loads(block)
print('JSON-LD OK')
for page in ['index.html','ai.html','seo.html','contact.html','thank-you.html']:
    text = pathlib.Path(page).read_text()
    for target in re.findall(r'href="#([a-z-]+)"', text):
        assert f'id="{target}"' in text, f'{page}: broken anchor #{target}'
print('Anchors OK')
EOF
```

- [ ] **Step 3: Manual click-through**

```bash
uv run python3 -m http.server 8080
```

In a browser: home → all five nav links → both frustration-card links (seo.html from card 03) → delivery-strip links → portfolio cards → contact page dropdown renders → mobile width (~375px) nav + featured card. Kill the server.

- [ ] **Step 4: Final commit (if sweep fixed anything)**

```bash
git add -A -- index.html ai.html seo.html contact.html thank-you.html functions/api/contact.js
git commit -m "reframe: final sweep fixes" || echo "nothing to fix — done"
```
