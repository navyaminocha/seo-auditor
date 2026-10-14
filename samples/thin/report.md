# Verified SEO Audit Report: https://stealth-ai.io/landing

**Audit Date**: 2026-10-14 18:45:11 | **Execution Time**: 58.0ms | **Tier**: 2

---

## Executive Summary
- **Target URL**: `https://stealth-ai.io/landing`
- **AI Answer Engine Readiness Score**: **10.0%**
- **Verified Issues (CONFIRMED)**: `5`
- **Legacy Crawler False Positives Filtered**: `0`
- **Unconfirmed Candidates**: `0`
- **JavaScript Render Discrepancy**: `High parity: Server HTML contains primary text and meta tags.`

> [!NOTE]
> **Priority Score Formula (Heuristic)**: `Priority = (Impact[1-5] * 2) / Effort[1-5]`.
> High-impact quick wins score up to 10.0; low-impact high-effort issues score near 0.4.

---

## 1. Verified Findings & Evidence Table

| ID | Issue | Severity | Status | Impact / Effort | Priority | Verified Evidence |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `chk-desc-missing` | **Missing Meta Description** | `HIGH` | ✅ **CONFIRMED** | 4/5 / 1/5 | **8.0** | Confirmed: <meta name='description'> tag is completely absent. |
| `chk-h1-missing` | **Missing H1 Heading** | `HIGH` | ✅ **CONFIRMED** | 4/5 / 1/5 | **8.0** | Confirmed: 0 <h1> tags found in server HTML or rendered document. |
| `chk-title-short` | **Title Tag Is Too Short (10 chars)** | `MEDIUM` | ✅ **CONFIRMED** | 3/5 / 1/5 | **6.0** | Title length is 10 characters (exact text: 'Stealth AI'). |
| `chk-canonical-missing` | **Missing Canonical Tag** | `MEDIUM` | ✅ **CONFIRMED** | 3/5 / 1/5 | **6.0** | Confirmed: No <link rel='canonical'> in HTML and no Link canonical HTTP header. |
| `chk-img-missing-alt` | **Images Missing Alt Text (2 found)** | `MEDIUM` | ✅ **CONFIRMED** | 3/5 / 2/5 | **3.0** | Confirmed: 2 images lack alt attribute (e.g. /stealth-hero.png). |

### Actionable Recommendations for Confirmed Issues
- **Missing Meta Description** (`Priority: 8.0`): Add a compelling meta description between 120-155 characters.
- **Missing H1 Heading** (`Priority: 8.0`): Add a single, semantic <h1> heading describing the page topic.
- **Title Tag Is Too Short (10 chars)** (`Priority: 6.0`): Expand title to 35-60 characters including high-intent search keywords.
- **Missing Canonical Tag** (`Priority: 6.0`): Add <link rel='canonical' href='https://stealth-ai.io/landing'> to prevent duplicate URL indexing.
- **Images Missing Alt Text (2 found)** (`Priority: 3.0`): Add descriptive alt attributes to all informational images.

---

## 2. AI Answer Engine Readiness (5-Question Test)

> Evaluates whether modern AI answer engines (ChatGPT Search, Perplexity, Google SGE, Gemini) can extract primary business facts from raw main text alone. All evidence quotes are programmatically verified against extracted text.

**Overall Readiness**: 10.0% (0 answered, 1 vague, 4 not found)

| # | Standard Question | Status | Substring Verified? | Answer & Evidence Quote |
| :-: | :--- | :---: | :---: | :--- |
| 1 | **What does this site offer?** | ⚠️ VAGUE | ⚪ N/A | General web services mentioned, but specific core offering is not clearly articulated. |
| 2 | **What does it cost?** | ❌ NOT_FOUND | ⚪ N/A | No pricing or cost information found in the extracted text. |
| 3 | **How do I contact them?** | ❌ NOT_FOUND | ⚪ N/A | No contact information, email, or telephone number found on the page. |
| 4 | **Where is it located?** | ❌ NOT_FOUND | ⚪ N/A | No physical address, city, or headquarters location specified. |
| 5 | **Who is it for?** | ❌ NOT_FOUND | ⚪ N/A | Target persona or audience is unspecified. |

---

## 3. Raw Server HTML vs TinyFish Rendered DOM Diff

Traditional SEO tools see only raw HTTP GET HTML. TinyFish renders client-side JavaScript.

| Metric | Raw Server HTML (httpx) | TinyFish Rendered (JS DOM) | Discrepancy / Parity |
| :--- | :---: | :---: | :--- |
| **Word Count** | 28 words | 21 words | -7 words (100.0% overlap) |
| **Title Tag** | `Stealth AI` | `Stealth AI` | ✅ Matched |
| **H1 Headings** | 0 detected | 0 detected | None |
| **Canonical** | `None` | `None` | ✅ Identical |
| **Robots Meta** | `None` | `None` | Parity preserved |
| **Link Count** | 1 links | 1 links | +0 rendered links |

---

## 4. Search Visibility & SERP Diagnostics

- **Target Search Query**: `"stealth ai"`
- **SERP Ranking Status**: **NOT_RANKING (Page 1 visibility absent)**
- **SERP Display Title**: `(Not displayed on Page 1)`
- **SERP Display Snippet**: `(No snippet generated)`

---

## 5. Competitor Gap Analysis & Side-by-Side AI Matrix

**Query Tested**: `"stealth ai"` | **Competitors Analyzed**: https://stripe.com/payments, https://braintreepayments.com

### Side-by-Side 5-Question AI Readiness Matrix

| Question | Our Page (`Target`) | Competitor 1 (`stripe.com`) | Competitor 2 (`braintreepayments.com`) |
| :--- | :---: | :---: | :---: |
| **1. Offer** | ⚠️ Vague | ✅ Yes | ✅ Yes |
| **2. Cost** | ❌ No | ✅ Yes | ✅ Yes |
| **3. Contact** | ❌ No | ✅ Yes | ✅ Yes |
| **4. Location** | ❌ No | ✅ Yes | ✅ Yes |
| **5. Audience** | ❌ No | ✅ Yes | ✅ Yes |

**Executive Synthesis**: Our page provides superior technical depth on JS rendering discrepancies and AI answer engine usability, while competitors feature broader historical monitoring and integration marketing.

#### What Our Page Covers (Competitors Omit):
- **JavaScript Rendering & DOM Inspection**: Explicitly separates client-side JS rendered nodes from server HTML with side-by-side diffing. *(Citation: Raw vs Rendered diff inspection)*
- **AI Search Engine Answer Readiness (5-Question Test)**: Tests whether LLM answer engines can parse 5 foundational business facts with substring verification. *(Citation: AI Q&A readiness module)*

#### What Competitors Cover (Our Page Omits):
- **Ecosystem API Integrations**: Offers turnkey webhooks, historical dashboards, and broader enterprise connectors. *(Citation: API documentation and dashboard integration)*

---

## 6. Execution Trace & TinyFish API Usage

| Step | Action / Decision | Tool Called | Latency | Status |
| :-: | :--- | :--- | :---: | :---: |
| 1 | Ingest raw server HTML via HTTP GET to establish baseline (no JS execution) | `fetch_raw` | 5.6ms | `DONE` |
| 2 | Render page through TinyFish Chromium engine to capture client-side DOM and clean markdown | `fetch_rendered` | 0.9ms | `DONE` |
| 3 | Compare raw server HTML vs TinyFish rendered DOM for word count, tags, and JS parity | `diff_raw_vs_rendered` | 22.2ms | `DONE` |
| 4 | Generate candidate issue list and independently verify each against deterministic evidence | `verify_finding` | 2.7ms | `DONE` |
| 5 | Evaluate AI answer engine usability with strict programmatic substring verification (5 questions) | `qa_test` | 1.9ms | `DONE` |
| 6 | Query TinyFish Search to determine organic SERP ranking position, title, and snippet quality | `search_visibility` | 1.4ms | `DONE` |
| 7 | Batch-fetch top 2 organic competitors via TinyFish, run side-by-side 5 Q&A test, and extract content gaps | `compare_competitors` | 2.5ms | `DONE` |

**Resource & Credit Metrics**:
- Total Latency: `58.0ms`
- TinyFish Calls: `4` (Mock hits: `5`)
- Estimated Credits: `0`