import time
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from seo_agent.models import (
    AuditReport,
    AuditStepTrace,
    RawFetchResult,
    RenderedFetchResult,
    DiffResult,
    VerifiedFinding,
    QATestResult,
    SearchVisibilityResult,
    CompetitorComparisonResult,
    BenchmarkResult,
)
from seo_agent.config import settings
from seo_agent.client.tinyfish import TinyFishClient
from seo_agent.client.llm import LLMClient
from seo_agent.agent.tracer import AgentTracer

from seo_agent.tools.fetch_raw import fetch_raw
from seo_agent.tools.fetch_rendered import fetch_rendered
from seo_agent.tools.diff import diff_raw_vs_rendered
from seo_agent.tools.checks import run_checks
from seo_agent.tools.verify import verify_finding
from seo_agent.tools.qa_test import run_qa_test
from seo_agent.tools.visibility import check_search_visibility
from seo_agent.tools.competitors import compare_competitors
from seo_agent.tools.report import write_report


class AuditOrchestrator:
    """The central agent reasoning loop with step budget, tiering, branching, and live trace."""

    def __init__(
        self,
        mock: Optional[bool] = None,
        max_steps: Optional[int] = None,
        tracer: Optional[AgentTracer] = None,
    ):
        self.mock = mock if mock is not None else settings.MOCK_MODE
        self.max_steps = max_steps or settings.MAX_STEPS
        self.tf_client = TinyFishClient(mock=self.mock)
        self.llm_client = LLMClient()
        self.tracer = tracer or AgentTracer()

    async def run(
        self,
        url: str,
        query: Optional[str] = None,
        benchmark_path: Optional[str] = None,
        monitor_cron: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> AuditReport:
        """Executes full verified SEO audit across tiers with live trace."""
        start_time = time.perf_counter()
        steps: List[AuditStepTrace] = []
        step_counter = 1

        self.tracer.print_banner(url=url, query=query, mock_mode=self.mock)

        # ---------------------------------------------------------
        # TIER 0: Deterministic Raw & Rendered Ingestion
        # ---------------------------------------------------------
        # Step 1: Plain HTTP GET (T2)
        s1_start = time.perf_counter()
        decision_1 = "Ingest raw server HTML via HTTP GET to establish baseline (no JS execution)"
        raw_res = await fetch_raw(url=url, mock=self.mock)
        s1_dur = (time.perf_counter() - s1_start) * 1000
        s1_summary = f"Status {raw_res.status_code}, {len(raw_res.html)} bytes, {len(raw_res.redirect_chain)} redirects"
        self.tracer.log_step(step_counter, decision_1, "fetch_raw(T2)", s1_summary, s1_dur)
        steps.append(AuditStepTrace(
            step_index=step_counter,
            decision=decision_1,
            tool_called="fetch_raw",
            summary=s1_summary,
            duration_ms=s1_dur,
        ))
        step_counter += 1

        # Step 2: TinyFish Rendered Fetch (T1)
        s2_start = time.perf_counter()
        decision_2 = "Render page through TinyFish Chromium engine to capture client-side DOM and clean markdown"
        rendered_res = await fetch_rendered(url=url, client=self.tf_client, mock=self.mock)
        s2_dur = (time.perf_counter() - s2_start) * 1000
        s2_summary = f"Extracted '{rendered_res.title[:30]}...', {len(rendered_res.text)} chars markdown, {len(rendered_res.links)} links"
        self.tracer.log_step(step_counter, decision_2, "fetch_rendered(T1)", s2_summary, s2_dur)
        steps.append(AuditStepTrace(
            step_index=step_counter,
            decision=decision_2,
            tool_called="fetch_rendered",
            summary=s2_summary,
            duration_ms=s2_dur,
        ))
        step_counter += 1

        # ---------------------------------------------------------
        # TIER 1: Raw vs Rendered Diff & Verification Engine
        # ---------------------------------------------------------
        # Step 3: Raw vs Rendered Diff (T3)
        s3_start = time.perf_counter()
        decision_3 = "Compare raw server HTML vs TinyFish rendered DOM for word count, tags, and JS parity"
        diff_res = diff_raw_vs_rendered(raw=raw_res, rendered=rendered_res)
        s3_dur = (time.perf_counter() - s3_start) * 1000
        s3_summary = f"Word diff: {diff_res.word_count_diff:+d} | Overlap: {diff_res.main_text_overlap_pct}% | JS-only blocks: {len(diff_res.js_only_content)}"
        self.tracer.log_step(step_counter, decision_3, "diff_raw_vs_rendered(T3)", s3_summary, s3_dur)
        steps.append(AuditStepTrace(
            step_index=step_counter,
            decision=decision_3,
            tool_called="diff_raw_vs_rendered",
            summary=s3_summary,
            duration_ms=s3_dur,
        ))
        step_counter += 1

        # Dynamic Branching Decision
        if diff_res.is_heavily_js_dependent:
            decision_branch = "CRITICAL BRANCH: Significant JS discrepancy detected. Prioritize client-side rendering audit."
            self.tracer.log_step(step_counter, decision_branch, "branch_decision", "CSR Dependency Alert Flagged", 0.5)
            steps.append(AuditStepTrace(
                step_index=step_counter,
                decision=decision_branch,
                tool_called="branch_evaluator",
                summary="Client-side rendering barrier identified",
                duration_ms=0.5,
            ))
            step_counter += 1

        # Step 4 & 5: Candidate Checks (T4) & Verification Engine (T5)
        s4_start = time.perf_counter()
        decision_4 = "Generate candidate issue list and independently verify each against deterministic evidence"
        candidates = run_checks(raw=raw_res, rendered=rendered_res, diff=diff_res)
        verified_findings: List[VerifiedFinding] = []
        for cand in candidates:
            vf = verify_finding(candidate=cand, raw=raw_res, rendered=rendered_res, diff=diff_res)
            verified_findings.append(vf)
        s4_dur = (time.perf_counter() - s4_start) * 1000
        confirmed_count = sum(1 for f in verified_findings if f.verification_status == "CONFIRMED")
        fp_count = sum(1 for f in verified_findings if f.verification_status == "LIKELY_FALSE_POSITIVE")
        s4_summary = f"Evaluated {len(candidates)} candidates: {confirmed_count} CONFIRMED, {fp_count} FALSE POSITIVE, {len(candidates)-confirmed_count-fp_count} UNCONFIRMED"
        self.tracer.log_step(step_counter, decision_4, "run_checks+verify(T4+T5)", s4_summary, s4_dur)
        steps.append(AuditStepTrace(
            step_index=step_counter,
            decision=decision_4,
            tool_called="verify_finding",
            summary=s4_summary,
            duration_ms=s4_dur,
        ))
        step_counter += 1

        # ---------------------------------------------------------
        # TIER 2: AI Q&A Test, Search Visibility, Competitor Gap
        # ---------------------------------------------------------
        # Step 6: AI Q&A Readiness Test (T6)
        s6_start = time.perf_counter()
        decision_6 = "Evaluate AI answer engine usability with strict programmatic substring verification (5 questions)"
        qa_res = await run_qa_test(rendered=rendered_res, llm=self.llm_client)
        s6_dur = (time.perf_counter() - s6_start) * 1000
        s6_summary = f"Score {qa_res.ai_readiness_score}% | {qa_res.answered_count} Answered, {qa_res.vague_count} Vague, {qa_res.not_found_count} Not Found"
        self.tracer.log_step(step_counter, decision_6, "qa_test(T6)", s6_summary, s6_dur)
        steps.append(AuditStepTrace(
            step_index=step_counter,
            decision=decision_6,
            tool_called="qa_test",
            summary=s6_summary,
            duration_ms=s6_dur,
        ))
        step_counter += 1

        # Step 7: Search Visibility Check (T7)
        s7_start = time.perf_counter()
        decision_7 = "Query TinyFish Search to determine organic SERP ranking position, title, and snippet quality"
        visibility_res = await check_search_visibility(
            target_url=url,
            query=query,
            rendered=rendered_res,
            tf_client=self.tf_client,
            llm=self.llm_client,
        )
        s7_dur = (time.perf_counter() - s7_start) * 1000
        s7_summary = f"Query: '{visibility_res.query}' ➔ {visibility_res.visibility_status} | {len(visibility_res.title_issues)} title issues"
        self.tracer.log_step(step_counter, decision_7, "search_visibility(T7)", s7_summary, s7_dur)
        steps.append(AuditStepTrace(
            step_index=step_counter,
            decision=decision_7,
            tool_called="search_visibility",
            summary=s7_summary,
            duration_ms=s7_dur,
        ))
        step_counter += 1

        # Step 8: Competitor Comparison & Side-by-Side Q&A (T8)
        s8_start = time.perf_counter()
        decision_8 = "Batch-fetch top 2 organic competitors via TinyFish, run side-by-side 5 Q&A test, and extract content gaps"
        competitors_res = await compare_competitors(
            target_url=url,
            query=visibility_res.query,
            target_rendered=rendered_res,
            tf_client=self.tf_client,
            llm=self.llm_client,
        )
        s8_dur = (time.perf_counter() - s8_start) * 1000
        s8_summary = f"Analyzed {len(competitors_res.competitors)} competitors | Found {len(competitors_res.our_advantages)} our advantages, {len(competitors_res.competitor_advantages)} competitor advantages"
        self.tracer.log_step(step_counter, decision_8, "compare_competitors(T8)", s8_summary, s8_dur)
        steps.append(AuditStepTrace(
            step_index=step_counter,
            decision=decision_8,
            tool_called="compare_competitors",
            summary=s8_summary,
            duration_ms=s8_dur,
        ))
        step_counter += 1

        # Optional: Benchmark against external tool export (T9)
        benchmark_res: Optional[BenchmarkResult] = None
        if benchmark_path:
            from seo_agent.tools.benchmark import import_tool_export
            s9_start = time.perf_counter()
            decision_9 = f"Import external SEO tool export '{benchmark_path}' and verify claimed issues against evidence"
            benchmark_res = import_tool_export(
                file_path=benchmark_path,
                raw=raw_res,
                rendered=rendered_res,
                diff=diff_res,
            )
            s9_dur = (time.perf_counter() - s9_start) * 1000
            s9_summary = f"Benchmark: {benchmark_res.total_issues} issues flagged, {benchmark_res.confirmed_count} confirmed, {benchmark_res.likely_false_positives} false positives ({benchmark_res.confirmed_precision_pct}% precision)"
            self.tracer.log_step(step_counter, decision_9, "import_tool_export(T9)", s9_summary, s9_dur)
            steps.append(AuditStepTrace(
                step_index=step_counter,
                decision=decision_9,
                tool_called="import_tool_export",
                summary=s9_summary,
                duration_ms=s9_dur,
            ))
            step_counter += 1

        # Optional: TinyFish Monitor creation (T10)
        monitor_data = None
        if monitor_cron:
            s10_start = time.perf_counter()
            decision_10 = f"Register automated TinyFish monitor on cron '{monitor_cron}'"
            monitor_data = await self.tf_client.create_monitor(url=url, cron=monitor_cron)
            s10_dur = (time.perf_counter() - s10_start) * 1000
            s10_summary = f"Monitor registered ID={monitor_data.get('id')}, status={monitor_data.get('status')}"
            self.tracer.log_step(step_counter, decision_10, "create_monitor(T10)", s10_summary, s10_dur)
            steps.append(AuditStepTrace(
                step_index=step_counter,
                decision=decision_10,
                tool_called="create_monitor",
                summary=s10_summary,
                duration_ms=s10_dur,
            ))
            step_counter += 1

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Construct Full Audit Report
        report = AuditReport(
            url=url,
            target_query=visibility_res.query,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_duration_ms=total_elapsed_ms,
            tier_level_executed=2,
            steps=steps,
            raw_fetch=raw_res,
            rendered_fetch=rendered_res,
            diff=diff_res,
            findings=verified_findings,
            qa_test=qa_res,
            search_visibility=visibility_res,
            competitor_comparison=competitors_res,
            benchmark=benchmark_res,
            monitor_created=monitor_data,
            usage_stats={
                "tinyfish_calls": self.tf_client.stats["fetch_calls"] + self.tf_client.stats["search_calls"] + self.tf_client.stats["monitor_calls"],
                "mock_hits": self.tf_client.stats["mock_hits"],
                "estimated_credits": self.tf_client.stats["estimated_credits"],
            },
        )

        # Step 11: Write Reports (T12)
        s11_start = time.perf_counter()
        files = write_report(report=report, output_dir=output_dir)
        s11_dur = (time.perf_counter() - s11_start) * 1000
        self.tracer.log_step(step_counter, "Serialize audit report to Markdown and JSON", "write_report(T12)", f"Saved {files['report_md']} and {files['report_json']}", s11_dur)

        # Print final rich summary
        self.tracer.print_summary(report)

        return report
