import time
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from seo_agent.models import (
    AuditReport,
    VerificationStatus,
    QAStatus,
)

console = Console(legacy_windows=False)


class AgentTracer:
    """Rich console visualizer for step-by-step agent decisions, timings, and results."""

    def __init__(self, console_instance: Optional[Console] = None):
        self.console = console_instance or console

    def print_banner(self, url: str, query: Optional[str], mock_mode: bool):
        mode_text = "[bold yellow]MOCK MODE (Replaying Real Fixtures)[/bold yellow]" if mock_mode else "[bold green]LIVE API MODE (TinyFish Connected)[/bold green]"
        query_text = f" | Target Query: '[cyan]{query}[/cyan]'" if query else ""

        banner_text = (
            f"[bold cyan]🔍 VERIFIED SEO AUDIT AGENT[/bold cyan] [dim](Powered by TinyFish)[/dim]\n"
            f"[bold white]Target URL:[/bold white] [underline blue]{url}[/underline blue]{query_text}\n"
            f"[bold white]Engine:[/bold white] {mode_text}"
        )
        self.console.print(Panel(banner_text, border_style="cyan", padding=(0, 1)))

    def log_step(
        self,
        step_num: int,
        decision: str,
        tool: str,
        summary: str,
        duration_ms: float,
        status: str = "DONE",
    ):
        status_style = "green" if status == "DONE" else "yellow"
        self.console.print(
            f"[bold cyan][Step {step_num}][/bold cyan] "
            f"[dim]{decision}[/dim] ➔ "
            f"[bold magenta]{tool}[/bold magenta] "
            f"([cyan]{duration_ms:.1f}ms[/cyan]) ➔ "
            f"[{status_style}]{summary}[/{status_style}]"
        )

    def print_summary(self, report: AuditReport):
        """Prints high-impact, screen-record-friendly summary tables."""
        self.console.print("\n")

        # 1. Executive Metrics Panel
        confirmed = sum(1 for f in report.findings if f.verification_status == VerificationStatus.CONFIRMED)
        false_positives = sum(1 for f in report.findings if f.verification_status == VerificationStatus.LIKELY_FALSE_POSITIVE)
        qa_score = report.qa_test.ai_readiness_score if report.qa_test else 0.0

        metrics_text = (
            f"[bold white]Audit Complete in [cyan]{report.total_duration_ms:.1f}ms[/cyan][/bold white] | "
            f"AI Readiness Score: [bold green]{qa_score}%[/bold green] | "
            f"Confirmed Issues: [bold red]{confirmed}[/bold red] | "
            f"False Positives Filtered: [bold yellow]{false_positives}[/bold yellow]"
        )
        self.console.print(Panel(metrics_text, title="📊 Executive Audit Summary", border_style="green"))

        # 2. Verified Findings Table
        findings_table = Table(title="🛡️ Verified Findings (Impact x Effort Heuristic)", show_header=True, header_style="bold cyan")
        findings_table.add_column("Issue", style="bold white", width=30)
        findings_table.add_column("Status", justify="center", width=22)
        findings_table.add_column("Impact/Effort", justify="center", width=14)
        findings_table.add_column("Priority", justify="center", width=10)
        findings_table.add_column("Deterministic Evidence", style="dim", width=46)

        sorted_findings = sorted(report.findings, key=lambda f: f.priority_score, reverse=True)
        for f in sorted_findings[:6]:  # Keep terminal output concise
            if f.verification_status == VerificationStatus.CONFIRMED:
                status_str = "[bold red]✅ CONFIRMED[/bold red]"
            elif f.verification_status == VerificationStatus.LIKELY_FALSE_POSITIVE:
                status_str = "[bold yellow]⚠️ FALSE POSITIVE[/bold yellow]"
            else:
                status_str = "[dim]⚪ UNCONFIRMED[/dim]"

            findings_table.add_row(
                f.title,
                status_str,
                f"{f.impact_score}/5 / {f.effort_score}/5",
                f"[bold cyan]{f.priority_score}[/bold cyan]",
                f.evidence[:44] + "..." if len(f.evidence) > 44 else f.evidence,
            )
        self.console.print(findings_table)

        # 3. AI Q&A Readiness Matrix (The Differentiator)
        if report.qa_test:
            qa_table = Table(title="🤖 AI Answer Engine Readiness (5-Question Test)", show_header=True, header_style="bold magenta")
            qa_table.add_column("Question", style="bold white", width=28)
            qa_table.add_column("Status", justify="center", width=16)
            qa_table.add_column("Substring Verified?", justify="center", width=20)
            qa_table.add_column("Verified Evidence Quote", style="italic", width=48)

            for q in report.qa_test.questions:
                if q.status == QAStatus.ANSWERED:
                    st = "[bold green]✅ ANSWERED[/bold green]"
                elif q.status == QAStatus.VAGUE:
                    st = "[bold yellow]⚠️ VAGUE[/bold yellow]"
                else:
                    st = "[bold red]❌ NOT FOUND[/bold red]"

                ver = "[green]✅ Real Substring[/green]" if q.is_verified_substring else "[dim]⚪ N/A[/dim]"
                quote = f'"{q.evidence_quote}"' if q.evidence_quote else "[dim]No verbatim quote[/dim]"
                qa_table.add_row(q.question, st, ver, quote[:46] + "..." if len(quote) > 46 else quote)

            self.console.print(qa_table)

        # 4. Raw vs Rendered Parity (If Discrepancy Exists)
        if report.diff and report.diff.is_heavily_js_dependent:
            diff_panel = (
                f"[bold red]⚠️ SEVERE JAVASCRIPT RENDERING DISCREPANCY DETECTED[/bold red]\n"
                f"• Server Raw HTML: [yellow]{report.diff.word_count_raw} words[/yellow]\n"
                f"• TinyFish Rendered: [green]{report.diff.word_count_rendered} words[/green] ([bold cyan]{report.diff.word_count_diff:+d} words[/bold cyan] injected via client JS)\n"
                f"• Overlap: [yellow]{report.diff.main_text_overlap_pct}%[/yellow]\n"
                f"• Non-rendering crawlers (older search bots, AI scrapers) miss {len(report.diff.js_only_content)} core content blocks!"
            )
            self.console.print(Panel(diff_panel, title="⚡ JavaScript Rendering Analysis", border_style="red"))

        # 5. Output File Links
        self.console.print(
            "\n[bold green]✓ Audit Complete![/bold green] Detailed reports written:\n"
            "  📄 Markdown: [cyan]report.md[/cyan]\n"
            "  📊 JSON:     [cyan]report.json[/cyan]\n"
        )
