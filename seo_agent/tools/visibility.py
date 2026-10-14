import re
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from seo_agent.models import (
    SearchVisibilityResult,
    RenderedFetchResult,
)
from seo_agent.client.tinyfish import TinyFishClient
from seo_agent.client.llm import LLMClient

logger = logging.getLogger("seo_agent.visibility")


async def check_search_visibility(
    target_url: str,
    query: Optional[str] = None,
    rendered: Optional[RenderedFetchResult] = None,
    tf_client: Optional[TinyFishClient] = None,
    llm: Optional[LLMClient] = None,
) -> SearchVisibilityResult:
    """T7: Evaluates target page search visibility via TinyFish Search.
    Infers target query if omitted, checks position, and audits SERP title/snippet.
    """
    client = tf_client or TinyFishClient()
    llm_client = llm or LLMClient()

    # 1. Infer query if not provided
    effective_query = query
    if not effective_query:
        if rendered:
            inferred = await _infer_target_query(rendered, llm_client)
            effective_query = inferred
        else:
            effective_query = "payment infrastructure developer apis"

    # 2. Run TinyFish Search
    search_results = await client.search(query=effective_query, limit=10)

    # 3. Check if target page appears in SERP
    target_domain = _extract_domain(target_url)
    position: Optional[int] = None
    serp_title = ""
    serp_snippet = ""
    is_visible = False

    for idx, item in enumerate(search_results, 1):
        item_url = item.get("url", "")
        item_domain = _extract_domain(item_url)
        # Check domain or path match
        if target_domain and target_domain in item_domain:
            position = idx
            is_visible = True
            serp_title = item.get("title", "")
            serp_snippet = item.get("snippet", "")
            break

    # If visible, audit title and snippet quality
    title_issues: List[str] = []
    snippet_issues: List[str] = []

    if is_visible:
        # Title analysis
        if len(serp_title) > 65:
            title_issues.append(f"Title truncated in SERP ({len(serp_title)} chars, exceeds ~60 chars display limit)")
        elif len(serp_title) < 25:
            title_issues.append(f"Title is too brief ({len(serp_title)} chars)")

        query_tokens = [t.lower() for t in effective_query.split() if len(t) > 3]
        if query_tokens and not any(t in serp_title.lower() for t in query_tokens):
            title_issues.append(f"Target query keyword missing from title ('{effective_query}')")

        # Snippet analysis
        if not serp_snippet:
            snippet_issues.append("Search snippet is empty or missing")
        elif len(serp_snippet) < 60:
            snippet_issues.append(f"Snippet is too short ({len(serp_snippet)} chars) to persuade clicks")
        if query_tokens and not any(t in serp_snippet.lower() for t in query_tokens):
            snippet_issues.append("Snippet does not contain search query terms (misses bolding opportunity)")

    # Status classification
    if position is not None and position <= 3:
        status = f"RANKING_TOP_3 (Position #{position})"
    elif position is not None and position <= 10:
        status = f"RANKING_PAGE_1 (Position #{position})"
    elif position is not None:
        status = f"RANKING_LOWER (Position #{position})"
    else:
        status = "NOT_RANKING (Page 1 visibility absent)"

    return SearchVisibilityResult(
        target_url=target_url,
        query=effective_query,
        is_visible=is_visible,
        position=position,
        serp_title=serp_title,
        serp_snippet=serp_snippet,
        title_issues=title_issues,
        snippet_issues=snippet_issues,
        visibility_status=status,
    )


async def _infer_target_query(rendered: RenderedFetchResult, llm: LLMClient) -> str:
    """Infers optimal search query from title and H1."""
    title = rendered.title or ""
    h1_match = re.search(r"^#\s+(.+)$", rendered.text, re.MULTILINE)
    h1 = h1_match.group(1).strip() if h1_match else ""

    system_prompt = (
        "You are an SEO search query analyst. Given a webpage title and H1, infer the single "
        "most accurate, high-intent 2-4 word search query that searchers would use to find this specific page."
    )
    user_prompt = f"Title: {title}\nH1: {h1}\nFirst 200 words:\n{rendered.text[:400]}"

    res = await llm.generate_json(system_prompt, user_prompt)
    query = res.get("query")
    if query and isinstance(query, str) and len(query.strip()) > 3:
        return query.strip()

    # Heuristic fallback if LLM response format differed
    cleaned = re.sub(r"[|\-–].*$", "", title).strip()
    return cleaned.lower() if cleaned else "online services platform"


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    domain = re.sub(r"^www\.", "", domain)
    return domain.split(":")[0].lower()
