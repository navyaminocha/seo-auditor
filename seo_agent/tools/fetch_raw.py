import time
import json
import logging
from pathlib import Path
from typing import Optional
import httpx

from seo_agent.models import RawFetchResult
from seo_agent.config import settings, FIXTURES_DIR

logger = logging.getLogger("seo_agent.fetch_raw")

USER_AGENT = "VerifiedSEOAgent/1.0 (AuditBot; +https://verified-seo.ai)"


async def fetch_raw(
    url: str,
    timeout: float = 15.0,
    mock: Optional[bool] = None,
) -> RawFetchResult:
    """T2: Plain HTTP GET without executing JavaScript (httpx).
    Captures raw HTML, status code, response headers, and redirect history.
    """
    is_mock = mock if mock is not None else settings.MOCK_MODE
    start_time = time.perf_counter()

    # If mock mode is explicitly on, try to find a matching fixture
    if is_mock:
        res = _load_mock_raw(url)
        if res:
            return res

    # Otherwise make live HTTP request
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            verify=False,  # avoid local cert validation failures in testing
        ) as client:
            resp = await client.get(url, headers=headers)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Collect redirect chain
            redirect_chain = [str(r.url) for r in resp.history]
            if redirect_chain:
                redirect_chain.append(str(resp.url))

            return RawFetchResult(
                url=url,
                final_url=str(resp.url),
                status_code=resp.status_code,
                headers=dict(resp.headers),
                html=resp.text,
                redirect_chain=redirect_chain,
                response_time_ms=elapsed_ms,
            )
    except Exception as e:
        logger.warning(f"Raw HTTP fetch failed for {url}: {e}. Falling back to mock fixture.")
        res = _load_mock_raw(url)
        if res:
            return res
        return RawFetchResult(
            url=url,
            final_url=url,
            status_code=500,
            headers={},
            html=f"<!-- Fetch error: {str(e)} -->",
            redirect_chain=[],
            response_time_ms=(time.perf_counter() - start_time) * 1000,
        )


def _load_mock_raw(url: str) -> Optional[RawFetchResult]:
    """Helper to load raw fixture matching URL keywords."""
    url_lower = url.lower()
    if "spa" in url_lower or "js" in url_lower or "app" in url_lower or "dashboard" in url_lower:
        fixture_name = "jsheavy_site.json"
    elif "thin" in url_lower or "stealth" in url_lower or "vague" in url_lower:
        fixture_name = "thin_site.json"
    else:
        fixture_name = "normal_site.json"

    fixture_path = FIXTURES_DIR / fixture_name
    if fixture_path.exists():
        try:
            data = json.loads(fixture_path.read_text(encoding="utf-8"))
            raw = data.get("raw", {})
            return RawFetchResult(
                url=url,
                final_url=url,
                status_code=raw.get("status_code", 200),
                headers=raw.get("headers", {"content-type": "text/html"}),
                html=raw.get("html", "<html><body>Mock HTML</body></html>"),
                redirect_chain=[],
                response_time_ms=65.0,
            )
        except Exception as e:
            logger.error(f"Error reading mock raw fixture: {e}")
    return None
