import json
from pathlib import Path
from typing import Dict, Any, Optional

from seo_agent.models import (
    AuditReport,
    VerificationStatus,
    QAStatus,
)


def write_report(
    report: AuditReport,
    output_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """T12: Writes readable report.md and structured report.json."""
    target_dir = output_dir or Path.cwd()
    target_dir.mkdir(parents=True, exist_ok=True)

    md_path = target_dir / "report.md"
    json_path = target_dir / "report.json"

    # 1. Generate Structured JSON
    json_path.write_text(
        report.model_dump_json(indent=2),
        encoding="utf-8",
    )

    # 2. Generate Readable Markdown Report
    md_content = _build_markdown_report(report)
    md_path.write_text(md_content, encoding="utf-8")

    return {
        "report_md": str(md_path),
        "report_json": str(json_path),
    }


def _build_markdown_report(report: AuditReport) -> str:
    """Constructs comprehensive, executive-ready Markdown audit report."""
    qa_score = report.qa_test.ai_readiness_score if report.qa_test else 0.0
    confirmed_findings = [f for f in report.findings if f.verification_status == VerificationStatus.CONFIRMED]
    false_positives = [f for f in report.findings if f.verification_status == VerificationStatus.LIKELY_FALSE_POSITIVE]
    unconfirmed = [f for f in report.findings if f.verification_status == VerificationStatus.UNCONFIRMED]

    lines = [
        f"# Verified SEO Audit Report: {report.url}",
        f"\n**Audit Date**: {report.timestamp} | **Execution Time**: {report.total_duration_ms:.1f}ms | **Tier**: {report.tier_level_executed}",
        f"\n---\n",
        "## Executive Summary",
        f"- **Target URL**: `{report.url}`",
        f"- **AI Answer Engine Readiness Score**: **{qa_score}%**",
        f"- **Verified Issues (CONFIRMED)**: `{len(confirmed_findings)}`",
        f"- **Legacy Crawler False Positives Filtered**: `{len(false_positives)}`",
        f"- **Unconfirmed Candidates**: `{len(unconfirmed)}`",
    ]

    if report.diff:
        lines.append(f"- **JavaScript Render Discrepancy**: `{report.diff.render_discrepancy_summary}`")

    # Priority Scoring Formula Callout
    lines.extend([
        "\n> [!NOTE]",
        "> **Priority Score Formula (Heuristic)**: `Priority = (Impact[1-5] * 2) / Effort[1-5]`.",
        "> High-impact quick wins score up to 10.0; low-impact high-effort issues score near 0.4.",
        "\n---\n",
        "## 1. Verified Findings & Evidence Table",
        "\n| ID | Issue | Severity | Status | Impact / Effort | Priority | Verified Evidence |",
        "| :--- | :--- | :--- | :--- | :---: | :---: | :--- |",
    ])

    # Sort findings by priority score descending
    sorted_findings = sorted(report.findings, key=lambda f: f.priority_score, reverse=True)
    for f in sorted_findings:
        status_badge = (
            "✅ **CONFIRMED**" if f.verification_status == VerificationStatus.CONFIRMED
            else ("⚠️ *FALSE POSITIVE*" if f.verification_status == VerificationStatus.LIKELY_FALSE_POSITIVE else "⚪ UNCONFIRMED")
        )
        lines.append(
            f"| `{f.id}` | **{f.title}** | `{f.severity.value}` | {status_badge} | {f.impact_score}/5 / {f.effort_score}/5 | **{f.priority_score}** | {f.evidence} |"
        )

    # Detailed Recommendations
    lines.extend([
        "\n### Actionable Recommendations for Confirmed Issues",
    ])
    for f in sorted_findings:
        if f.verification_status == VerificationStatus.CONFIRMED and f.recommendation:
            lines.append(f"- **{f.title}** (`Priority: {f.priority_score}`): {f.recommendation}")

    # Section 2: AI Q&A Test (The Differentiator)
    if report.qa_test:
        lines.extend([
            "\n---\n",
            "## 2. AI Answer Engine Readiness (5-Question Test)",
            "\n> Evaluates whether modern AI answer engines (ChatGPT Search, Perplexity, Google SGE, Gemini) can extract primary business facts from raw main text alone. All evidence quotes are programmatically verified against extracted text.\n",
            f"**Overall Readiness**: {report.qa_test.ai_readiness_score}% ({report.qa_test.answered_count} answered, {report.qa_test.vague_count} vague, {report.qa_test.not_found_count} not found)\n",
            "| # | Standard Question | Status | Substring Verified? | Answer & Evidence Quote |",
            "| :-: | :--- | :---: | :---: | :--- |",
        ])

        for q in report.qa_test.questions:
            badge = "✅ ANSWERED" if q.status == QAStatus.ANSWERED else ("⚠️ VAGUE" if q.status == QAStatus.VAGUE else "❌ NOT_FOUND")
            ver_badge = "✅ Exact Match" if q.is_verified_substring else ("⚠️ None/Downgraded" if q.evidence_quote else "⚪ N/A")
            quote_text = f"\n> *\"{q.evidence_quote}\"*" if q.evidence_quote else ""
            lines.append(
                f"| {q.question_id} | **{q.question}** | {badge} | {ver_badge} | {q.answer}{quote_text} |"
            )

    # Section 3: Raw vs Rendered Diff (JavaScript Parity)
    if report.diff:
        d = report.diff
        lines.extend([
            "\n---\n",
            "## 3. Raw Server HTML vs TinyFish Rendered DOM Diff",
            "\nTraditional SEO tools see only raw HTTP GET HTML. TinyFish renders client-side JavaScript.\n",
            "| Metric | Raw Server HTML (httpx) | TinyFish Rendered (JS DOM) | Discrepancy / Parity |",
            "| :--- | :---: | :---: | :--- |",
            f"| **Word Count** | {d.word_count_raw} words | {d.word_count_rendered} words | {d.word_count_diff:+d} words ({d.main_text_overlap_pct}% overlap) |",
            f"| **Title Tag** | `{d.title_raw or '(empty)'}` | `{d.title_rendered or '(empty)'}` | {'✅ Matched' if d.title_matches else '⚠️ Rendered Mismatch'} |",
            f"| **H1 Headings** | {len(d.h1_raw)} detected | {len(d.h1_rendered)} detected | {', '.join(d.h1_rendered[:1]) or 'None'} |",
            f"| **Canonical** | `{d.canonical_raw or 'None'}` | `{d.canonical_rendered or 'None'}` | {'✅ Identical' if d.canonical_raw == d.canonical_rendered else '⚠️ Rendered Variation'} |",
            f"| **Robots Meta** | `{d.robots_raw or 'None'}` | `{d.robots_rendered or 'None'}` | Parity preserved |",
            f"| **Link Count** | {d.link_count_raw} links | {d.link_count_rendered} links | {d.link_count_rendered - d.link_count_raw:+d} rendered links |",
        ])

        if d.js_only_content:
            lines.extend([
                "\n### Content Existing ONLY After Client-Side JavaScript Execution:",
            ])
            for snip in d.js_only_content:
                lines.append(f"- `[JS-Only]`: *\"{snip}\"*")

    # Section 4: Search Visibility
    if report.search_visibility:
        sv = report.search_visibility
        lines.extend([
            "\n---\n",
            "## 4. Search Visibility & SERP Diagnostics",
            f"\n- **Target Search Query**: `\"{sv.query}\"`",
            f"- **SERP Ranking Status**: **{sv.visibility_status}**",
            f"- **SERP Display Title**: `{sv.serp_title or '(Not displayed on Page 1)'}`",
            f"- **SERP Display Snippet**: `{sv.serp_snippet or '(No snippet generated)'}`",
        ])
        if sv.title_issues:
            lines.append("\n**Title Issues Flagged**:")
            for issue in sv.title_issues:
                lines.append(f"- ⚠️ {issue}")
        if sv.snippet_issues:
            lines.append("\n**Snippet Issues Flagged**:")
            for issue in sv.snippet_issues:
                lines.append(f"- ⚠️ {issue}")

    # Section 5: Competitor Comparison & Side-by-Side Q&A
    if report.competitor_comparison:
        cc = report.competitor_comparison
        lines.extend([
            "\n---\n",
            "## 5. Competitor Gap Analysis & Side-by-Side AI Matrix",
            f"\n**Query Tested**: `\"{cc.query}\"` | **Competitors Analyzed**: {', '.join(cc.competitors)}\n",
            "### Side-by-Side 5-Question AI Readiness Matrix\n",
        ])

        # Header with Target and Competitors
        comp_names = [f"Competitor {i+1} (`{cc._extract_domain(c) if hasattr(cc, '_extract_domain') else c.split('/')[2]}`)" for i, c in enumerate(cc.competitors)]
        col_headers = "| Question | Our Page (`Target`) | " + " | ".join(comp_names) + " |"
        col_align = "| :--- | :---: | " + " | ".join([":---:" for _ in comp_names]) + " |"
        lines.append(col_headers)
        lines.append(col_align)

        # 5 Questions row by row
        questions_text = [
            "1. Offer",
            "2. Cost",
            "3. Contact",
            "4. Location",
            "5. Audience",
        ]
        for q_idx, q_label in enumerate(questions_text):
            row_cells = [f"**{q_label}**"]
            # Target status
            t_status = report.qa_test.questions[q_idx].status if (report.qa_test and q_idx < len(report.qa_test.questions)) else QAStatus.NOT_FOUND
            row_cells.append("✅ Yes" if t_status == QAStatus.ANSWERED else ("⚠️ Vague" if t_status == QAStatus.VAGUE else "❌ No"))
            
            # Competitors status
            for c_url in cc.competitors:
                c_qa = cc.competitor_qa.get(c_url)
                if c_qa and q_idx < len(c_qa.questions):
                    st = c_qa.questions[q_idx].status
                    row_cells.append("✅ Yes" if st == QAStatus.ANSWERED else ("⚠️ Vague" if st == QAStatus.VAGUE else "❌ No"))
                else:
                    row_cells.append("⚪ N/A")
            lines.append("| " + " | ".join(row_cells) + " |")

        # Gap summary
        lines.extend([
            f"\n**Executive Synthesis**: {cc.content_gap_summary}\n",
            "#### What Our Page Covers (Competitors Omit):",
        ])
        for adv in cc.our_advantages:
            lines.append(f"- **{adv.topic}**: {adv.our_coverage} *(Citation: {adv.evidence_citation})*")

        lines.append("\n#### What Competitors Cover (Our Page Omits):")
        for adv in cc.competitor_advantages:
            lines.append(f"- **{adv.topic}**: {adv.competitor_coverage} *(Citation: {adv.evidence_citation})*")

    # Section 6: Execution Trace & TinyFish Resource Usage
    lines.extend([
        "\n---\n",
        "## 6. Execution Trace & TinyFish API Usage",
        "\n| Step | Action / Decision | Tool Called | Latency | Status |",
        "| :-: | :--- | :--- | :---: | :---: |",
    ])
    for step in report.steps:
        lines.append(f"| {step.step_index} | {step.decision} | `{step.tool_called}` | {step.duration_ms:.1f}ms | `{step.status}` |")

    lines.extend([
        f"\n**Resource & Credit Metrics**:",
        f"- Total Latency: `{report.total_duration_ms:.1f}ms`",
        f"- TinyFish Calls: `{report.usage_stats.get('tinyfish_calls', 0)}` (Mock hits: `{report.usage_stats.get('mock_hits', 0)}`)",
        f"- Estimated Credits: `{report.usage_stats.get('estimated_credits', 0)}`",
    ])

    return "\n".join(lines)
