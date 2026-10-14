# Verified SEO Audit Agent 🔍

An autonomous, evidence-backed SEO audit agent powered by **TinyFish**. Unlike legacy crawlers that only inspect static server HTML, the Verified SEO Agent renders JavaScript through TinyFish Chromium, programmatically verifies deterministic evidence to filter out false positives, benchmarks against legacy tool exports, and evaluates whether modern AI answer engines (ChatGPT, Perplexity, Gemini, Google SGE) can understand your site with a strict 5-Question AI Readiness Test.

---

## 🚀 Quickstart & Setup

### 1. Installation
Requires Python 3.10+ (tested on Python 3.14).
```bash
# Clone and enter directory
git clone <repo-url>
cd SEO_Agent

# Install dependencies and CLI entry point
pip install -r requirements.txt
pip install -e .
```

### 2. Environment Variables
Create a `.env` file in the project root:
```env
# TinyFish API (Required for live mode; omitted for mock mode)
TINYFISH_API_KEY=your_tinyfish_api_key_here

# LLM Configuration (Provider-Agnostic: OpenAI, Groq, Gemini)
OPENAI_API_KEY=your_openai_or_groq_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional Execution Limits
SEO_AGENT_TIMEOUT=30.0
SEO_AGENT_MAX_STEPS=12
SEO_AGENT_MOCK=false
```

---

## 🎬 Demo Commands

The agent features a built-in **Mock Mode** using real captured fixtures, guaranteeing that live video demos and offline testing run with zero external network or API key latency.

### 1. Audit a Modern JS-Heavy Single Page Application (CSR Discrepancy + Benchmark)
Demonstrates the raw vs rendered diff, client-side rendering dependency detection, and legacy crawler false positive filtering:
```bash
audit https://spa-showcase.app/dashboard --mock --benchmark samples/screaming_frog_export.csv -o samples/jsheavy
```

### 2. Audit a Thin-Content / Buzzword Startup Landing Page
Demonstrates the AI Q&A Readiness test exposing vague marketing buzzwords with ❌ NOT FOUND ratings:
```bash
audit https://stealth-ai.io/landing --mock -o samples/thin
```

### 3. Audit a Fully-Optimized Production Site
Demonstrates 100% AI Readiness score, verified verbatim substring evidence quotes, and competitor gap analysis:
```bash
audit https://docs.stripe.com/payments --mock -o samples/normal
```

### 4. Live Mode (TinyFish Connected)
When `TINYFISH_API_KEY` is provided:
```bash
audit https://stripe.com/payments --query "payment infrastructure for developers"
```

---

## 🛠️ Tools Architecture (Deterministic Code; LLM for Planning & Interpretation)

| Tool | Function | Purpose |
| :--- | :--- | :--- |
| **T1** | `fetch_rendered(url)` | TinyFish `POST https://api.fetch.tinyfish.ai` (Chromium JS-rendered, markdown, metadata, links). |
| **T2** | `fetch_raw(url)` | Plain HTTP GET via `httpx` (no JS): raw HTML, status code, response headers, redirects. |
| **T3** | `diff_raw_vs_rendered(raw, rendered)` | Word count diff, title parity, H1/H2 parity, canonical diff, and snippets existing *only* after client JS execution. |
| **T4** | `run_checks(raw, rendered, diff)` | Deterministic issue candidate generator (missing/short title, canonical, noindex, broken links, image alt). |
| **T5** | `verify_finding(candidate)` | Re-tests candidate against deterministic evidence. Outputs `CONFIRMED`, `UNCONFIRMED`, or `LIKELY_FALSE_POSITIVE`. |
| **T6** | `qa_test(url)` | **The AI Q&A Differentiator**: Tests 5 core questions (Offer, Cost, Contact, Location, Audience). **Programmatically verifies verbatim substring match against extracted text**. Downgrades model if quote is hallucinated. |
| **T7** | `search_visibility(url, query?)` | Inquires TinyFish Search API for ranking position, audits SERP title length and snippet relevance. |
| **T8** | `compare_competitors(url, query)` | Batch-fetches top 2 competitors via TinyFish, runs side-by-side 5-question matrix, and extracts content gaps. |
| **T9** | `import_tool_export(path)` | Imports CSV/JSON from Screaming Frog/Semrush and benchmarks true precision vs false positives. |
| **T10** | `create_monitor(url, cron)` | Registers scheduled change monitor via TinyFish Monitor API. |
| **T11** | `browser_verify(url, goal)` | Metered browser automation via TinyFish Agent API for specialized DOM interactions. |
| **T12** | `write_report(report)` | Outputs human-readable `report.md` (with formulas and evidence tables) and structured `report.json`. |

---

## ⚖️ Priority Score Formula (Heuristic)

To avoid arbitrary "critical/high" ratings, every confirmed finding includes a transparent, deterministic priority score:

$$\text{Priority Score} = \frac{\text{Impact Score } [1-5] \times 2}{\text{Effort Score } [1-5]}$$

- **Scale**: $0.4$ (Low impact, heavy engineering effort) to $10.0$ (High impact, quick win).
- **Labeling**: Explicitly labeled in all reports and CLI outputs as a heuristic formula.

---

## 🧠 Decisions (Operating Mode Notes)

In accordance with the hackathon build brief, the following architectural decisions were made autonomously:
1. **Agent-First CLI Architecture**: Built as a pure terminal agent with Rich console output and file report outputs (`report.md`, `report.json`), without web frontend overhead.
2. **Strict Programmatic Substring Verification**: Rather than trusting LLM assertions for AI readiness, the tool programmatically validates that every `evidence_quote` is an exact verbatim substring of the parsed page text. Any unverified or hallucinated quote immediately downgrades the finding.
3. **Dual-Mode Offline Replay**: Designed a mock fixture layer matching real production captures (`normal_site.json`, `jsheavy_site.json`, `thin_site.json`) so the agent runs deterministically during video recording without depending on internet speed or API limits.
4. **Provider-Agnostic LLM Wrapper**: Supports any OpenAI-compatible API (`OPENAI_API_KEY`, Groq, Gemini) with a built-in deterministic heuristic fallback for offline evaluation.
5. **Multi-Tier Execution Flow**:
   - **Tier 0**: Cheap raw HTTP GET and TinyFish rendered fetch.
   - **Tier 1**: Deterministic diffing, checks, and evidence verification.
   - **Tier 2**: AI readiness Q&A, TinyFish search visibility, and competitor gap analysis.

---

## ⚠️ Known Limitations
1. **Aggregator Filtering**: Search competitor discovery filters known directories (e.g., Yelp, Wikipedia, G2, Reddit) using a curated exclusion list. Niche aggregators outside this list may occasionally be selected as competitors.
2. **Sub-page Crawling**: To respect robots.txt and prevent aggressive crawling, the agent audits only user-specified URLs and directly associated competitor pages (no recursive site spiders).
3. **Search Position Window**: Search visibility queries evaluate the top 10 search engine results (Page 1 visibility). Positions beyond Page 1 are categorized as `RANKING_LOWER` or `NOT_RANKING`.

---

## 🧪 Testing

Run the full pytest suite covering raw fetching, render diffing, deterministic candidate generation, verification engine, and Q&A substring matching:
```bash
pytest -v
```
