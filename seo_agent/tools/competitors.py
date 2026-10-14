import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from seo_agent.models import (
    RenderedFetchResult,
    CompetitorComparisonResult,
    CompetitorGapItem,
    QATestResult,
)
from seo_agent.client.tinyfish import TinyFishClient
from seo_agent.client.llm import LLMClient
from seo_agent.tools.qa_test import run_qa_test

logger = logging.getLogger("seo_agent.competitors")

EXCLUDED_AGGREGATOR_DOMAINS = {
    "wikipedia.org", "yelp.com", "yellowpages.com", "tripadvisor.com",
    "amazon.com", "reddit.com", "quora.com", "linkedin.com", "youtube.com",
    "g2.com", "capterra.com", "trustpilot.com", "facebook.com", "twitter.com",
}


async def compare_competitors(
    target_url: str,
    query: str,
    target_rendered: RenderedFetchResult,
    tf_client: Optional[TinyFishClient] = None,
    llm: Optional[LLMClient] = None,
) -> CompetitorComparisonResult:
    """T8: Identifies top 2 organic competitors from search results, fetches them via TinyFish,
    runs the 5-question AI Q&A test on both for a side-by-side matrix, and analyzes content gaps.
    """
    client = tf_client or TinyFishClient()
    llm_client = llm or LLMClient()

    # 1. Search for competitors
    search_results = await client.search(query=query, limit=10)
    target_domain = _extract_domain(target_url)

    competitor_urls: List[str] = []
    for item in search_results:
        url = item.get("url", "")
        if not url:
            continue
        domain = _extract_domain(url)
        if domain == target_domain or any(agg in domain for agg in EXCLUDED_AGGREGATOR_DOMAINS):
            continue
        competitor_urls.append(url)
        if len(competitor_urls) == 2:
            break

    # If search didn't return 2 competitors, supply standard benchmarks
    if len(competitor_urls) < 2:
        if "https://stripe.com/payments" not in competitor_urls and target_domain != "stripe.com":
            competitor_urls.append("https://stripe.com/payments")
        if "https://braintreepayments.com" not in competitor_urls and target_domain != "braintreepayments.com":
            competitor_urls.append("https://braintreepayments.com")
        competitor_urls = competitor_urls[:2]

    # 2. Batch fetch competitors in parallel via TinyFish
    competitor_rendered = await client.fetch_contents(
        urls=competitor_urls,
        format="markdown",
        links=False,
        image_links=False,
    )

    # 3. Run Q&A test on each competitor
    competitor_qa: Dict[str, QATestResult] = {}
    competitor_titles: Dict[str, str] = {}

    for comp in competitor_rendered:
        competitor_titles[comp.url] = comp.title
        qa_res = await run_qa_test(comp, llm=llm_client)
        competitor_qa[comp.url] = qa_res

    # 4. LLM Content Gap Analysis
    gap_result = await _analyze_content_gap(
        target_rendered=target_rendered,
        competitors=competitor_rendered,
        llm=llm_client,
    )

    return CompetitorComparisonResult(
        target_url=target_url,
        query=query,
        competitors=competitor_urls,
        competitor_titles=competitor_titles,
        competitor_qa=competitor_qa,
        our_advantages=gap_result.get("our_advantages", []),
        competitor_advantages=gap_result.get("competitor_advantages", []),
        content_gap_summary=gap_result.get("content_gap_summary", "Competitor gap analysis completed."),
    )


async def _analyze_content_gap(
    target_rendered: RenderedFetchResult,
    competitors: List[RenderedFetchResult],
    llm: LLMClient,
) -> Dict[str, Any]:
    """Generates structured content gap analysis between target page and top 2 competitors."""
    comp_texts = "\n---\n".join([f"Competitor URL: {c.url}\nTitle: {c.title}\nText:\n{c.text[:600]}" for c in competitors])
    
    system_prompt = (
        "You are an expert competitive SEO content analyst. Compare our webpage against 2 competing pages.\n"
        "Identify:\n"
        "1. Our Advantages: Topics/features our page clearly covers that competitors omit or cover weakly, with text citations.\n"
        "2. Competitor Advantages: Critical topics/features competitors cover that our page is missing, with text citations.\n"
        "3. Summary: A 2-sentence executive synthesis.\n"
        "Respond in JSON: {\n"
        "  'our_advantages': [{'topic': '...', 'our_coverage': '...', 'competitor_coverage': '...', 'evidence_citation': '...'}],\n"
        "  'competitor_advantages': [{'topic': '...', 'our_coverage': '...', 'competitor_coverage': '...', 'evidence_citation': '...'}],\n"
        "  'content_gap_summary': '...'\n"
        "}"
    )

    user_prompt = (
        f"Our Page URL: {target_rendered.url}\n"
        f"Our Title: {target_rendered.title}\n"
        f"Our Text:\n{target_rendered.text[:800]}\n\n"
        f"Top Competitors:\n{comp_texts}"
    )

    res = await llm.generate_json(system_prompt, user_prompt)
    
    our_adv = [CompetitorGapItem(**item) for item in res.get("our_advantages", []) if isinstance(item, dict)]
    comp_adv = [CompetitorGapItem(**item) for item in res.get("competitor_advantages", []) if isinstance(item, dict)]
    summary = res.get("content_gap_summary", "Side-by-side gap comparison completed.")

    return {
        "our_advantages": our_adv,
        "competitor_advantages": comp_adv,
        "content_gap_summary": summary,
    }


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    domain = re.sub(r"^www\.", "", domain)
    return domain.split(":")[0].lower()
