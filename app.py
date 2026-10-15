import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, AsyncGenerator

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
import uvicorn

# Configure UTF-8 on Windows
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from seo_agent.agent.orchestrator import AuditOrchestrator
from seo_agent.models import AuditStepTrace, AuditReport
from seo_agent.config import settings

# Initialize FastAPI App
app = FastAPI(title="Verified SEO Audit Agent UI", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
REPORT_MD_PATH = BASE_DIR / "report.md"
REPORT_JSON_PATH = BASE_DIR / "report.json"


@app.get("/api/download/report.md")
async def download_report_md():
    if REPORT_MD_PATH.exists():
        return FileResponse(REPORT_MD_PATH, media_type="text/markdown", filename="report.md")
    return {"error": "report.md not found. Run an audit first."}


@app.get("/api/download/report.json")
async def download_report_json():
    if REPORT_JSON_PATH.exists():
        return FileResponse(REPORT_JSON_PATH, media_type="application/json", filename="report.json")
    return {"error": "report.json not found. Run an audit first."}


@app.get("/api/audit/stream")
async def stream_audit(
    url: str = Query(..., description="Target webpage URL"),
    query: Optional[str] = Query(None, description="Target search query"),
    mock: bool = Query(True, description="Toggle mock mode"),
    benchmark: Optional[str] = Query(None, description="Optional path to tool export benchmark"),
):
    """Server-Sent Events (SSE) streaming endpoint for live agent steps and final report."""
    queue: asyncio.Queue = asyncio.Queue()

    async def step_callback(step: AuditStepTrace):
        await queue.put({"type": "step", "data": step.model_dump()})

    async def run_task():
        try:
            orchestrator = AuditOrchestrator(mock=mock)
            # Use sample benchmark if requested
            bm_path = benchmark
            if not bm_path and "spa" in url.lower():
                sample_bm = BASE_DIR / "samples" / "screaming_frog_export.csv"
                if sample_bm.exists():
                    bm_path = str(sample_bm)

            report = await orchestrator.run(
                url=url,
                query=query,
                benchmark_path=bm_path,
                output_dir=BASE_DIR,
                on_step=step_callback,
            )
            await queue.put({"type": "complete", "data": json.loads(report.model_dump_json())})
        except Exception as e:
            await queue.put({"type": "error", "data": {"message": str(e)}})
        finally:
            await queue.put(None)  # Sentinel to end stream

    # Launch audit in background task
    asyncio.create_task(run_task())

    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            item = await queue.get()
            if item is None:
                break
            event_type = item["type"]
            data_str = json.dumps(item["data"])
            yield f"event: {event_type}\ndata: {data_str}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Returns the standalone HTML5/CSS3/Vanilla JS single-page application."""
    html_path = BASE_DIR / "seo_agent" / "ui" / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>UI index.html not found</h1>"


if __name__ == "__main__":
    print("\n[+] Starting Verified SEO Audit Agent Demo UI on http://127.0.0.1:8000 ...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
