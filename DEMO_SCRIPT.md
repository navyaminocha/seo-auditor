# 90-Second Demo Video Script: Verified SEO Audit Agent

**Target Runtime**: 90 seconds  
**Format**: Screen recording of live terminal + generated `report.md`  
**Core Highlights**:
1. The Raw vs Rendered Diff (JavaScript SEO parity via TinyFish)
2. Verified vs False Positive Table (Filtering legacy crawler noise)
3. The AI Q&A Readiness Moment (5 Questions with strict programmatic substring proof)
4. The Thin-Content Contrast (Exposing hype sites with no real answers)

---

### Shot 1: The Problem & The Agent Launch (0:00 – 0:15)
* **Screen**: Clean terminal window.
* **Command to run**:
  ```bash
  audit https://spa-showcase.app/dashboard --mock --benchmark samples/screaming_frog_export.csv
  ```
* **What to point at**:
  - The live agent step-by-step trace (`[Step 1] Ingest raw HTML`, `[Step 2] TinyFish Chromium render`).
  - The dynamic branching trigger: `[Step 4] CRITICAL BRANCH: Significant JS discrepancy detected`.
* **Narration**:
  *"Legacy SEO tools crawl static HTML, missing client-side JavaScript and generating dozens of false alarms. Our Verified SEO Agent uses TinyFish to render the real DOM, verify deterministic evidence, and test whether modern AI answer engines can actually understand your site."*

---

### Shot 2: Raw vs Rendered Diff & False Positive Filtering (0:15 – 0:35)
* **Screen**: Terminal output highlighting the `⚡ JavaScript Rendering Analysis` panel and `🛡️ Verified Findings Table`.
* **What to point at**:
  - Raw HTML word count: `1 word` vs TinyFish Rendered: `81 words` (+80 words injected via client JS).
  - The legacy crawler benchmark: `5 issues flagged, 1 confirmed, 1 false positive (20.0% precision)`.
  - Point to the priority score formula: `Priority = (Impact * 2) / Effort (Heuristic)`.
* **Narration**:
  *"Watch this render diff: standard crawlers saw an empty single-page app with just one word and flagged a missing title. But TinyFish rendered the real DOM, proving the title was dynamically injected and filtering out the false alarm while pinpointing the real culprit: a critical client-side rendering dependency."*

---

### Shot 3: The AI Q&A Readiness Test — The Differentiator (0:35 – 0:55)
* **Screen**: Terminal output focusing on the `🤖 AI Answer Engine Readiness (5-Question Test)` table.
* **What to point at**:
  - The 5 standard questions: Offer, Cost, Contact, Location, Audience.
  - The ✅ / ⚠️ / ❌ status badges.
  - The `Substring Verified?` column: `[✅ Real Substring]`.
  - The verified evidence quote: *"Pricing starts at $49/month for starter nodes..."*.
* **Narration**:
  *"Here is our core differentiator: AI search engines like Perplexity, ChatGPT, and Gemini don't just count meta tags—they need answers to 5 core business questions. Our agent extracts those answers and programmatically verifies that every single evidence quote is a verbatim substring of the page text. No model hallucinations allowed."*

---

### Shot 4: The Thin-Content / Buzzword Contrast (0:55 – 1:15)
* **Screen**: Run the thin-content command in terminal:
  ```bash
  audit https://stealth-ai.io/landing --mock
  ```
* **What to point at**:
  - AI Readiness Score drops to **10.0%**.
  - 4 out of 5 questions marked **❌ NOT FOUND**.
  - Status for Offer: **⚠️ VAGUE** (Buzzwords without a clear product description).
  - Search visibility: `NOT_RANKING (Page 1 visibility absent)`.
* **Narration**:
  *"Now let's audit a buzzword-heavy stealth startup landing page. Traditional tools give it a passing score because meta tags exist. But our AI Q&A test exposes the truth: AI Readiness Score is only 10%. Cost? Not found. Contact? Not found. Location? Not found. An AI search engine cannot recommend this business."*

---

### Shot 5: Competitor Gap Matrix & Wrap-up (1:15 – 1:30)
* **Screen**: Quick switch to `samples/normal/report.md` in markdown preview.
* **What to point at**:
  - Section 5: Side-by-Side Competitor Matrix (Target vs Stripe vs Braintree).
  - Our Advantages vs Competitor Advantages with text citations.
  - Structured `report.json` file on disk.
* **Narration**:
  *"Finally, the agent batch-fetches top competitors via TinyFish Search, benchmarked side-by-side on the exact same 5 questions, and generates comprehensive Markdown and JSON reports in under two seconds. That's verified, evidence-backed SEO for the age of AI search."*
