import sys
import asyncio
from pathlib import Path
from typing import Optional
import click

# Ensure utf-8 encoding on Windows terminals
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from seo_agent.agent.orchestrator import AuditOrchestrator
from seo_agent.config import settings


@click.command(name="audit")
@click.argument("url")
@click.option(
    "--query", "-q",
    default=None,
    help="Target search query to audit visibility and competitor gaps against (inferred if omitted).",
)
@click.option(
    "--benchmark", "-b",
    default=None,
    type=click.Path(exists=False),
    help="Path to CSV/JSON export from another SEO tool (Screaming Frog, Semrush) to benchmark.",
)
@click.option(
    "--monitor", "-m",
    default=None,
    help="Cron expression (e.g. '0 9 * * *') to schedule an automated TinyFish monitor baseline.",
)
@click.option(
    "--mock",
    is_flag=True,
    default=False,
    help="Run in offline mock mode using real captured fixtures.",
)
@click.option(
    "--output-dir", "-o",
    default=".",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Directory to save report.md and report.json (default: current directory).",
)
def main(
    url: str,
    query: Optional[str],
    benchmark: Optional[str],
    monitor: Optional[str],
    mock: bool,
    output_dir: str,
):
    """Verified SEO Audit Agent (Powered by TinyFish)
    
    Conducts deterministic, evidence-backed SEO audits, raw vs JS-rendered diffing,
    the 5-Question AI Q&A readiness test, and competitor gap analysis.
    """
    is_mock = mock or settings.MOCK_MODE or not bool(settings.TINYFISH_API_KEY)
    
    orchestrator = AuditOrchestrator(mock=is_mock)
    target_path = Path(output_dir)

    try:
        asyncio.run(
            orchestrator.run(
                url=url,
                query=query,
                benchmark_path=benchmark,
                monitor_cron=monitor,
                output_dir=target_path,
            )
        )
    except KeyboardInterrupt:
        click.echo("\n[!] Audit interrupted by user.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n[!] Error during audit execution: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
