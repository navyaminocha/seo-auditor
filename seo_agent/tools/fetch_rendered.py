import logging
from typing import Optional
from seo_agent.models import RenderedFetchResult
from seo_agent.client.tinyfish import TinyFishClient

logger = logging.getLogger("seo_agent.fetch_rendered")


async def fetch_rendered(
    url: str,
    client: Optional[TinyFishClient] = None,
    mock: Optional[bool] = None,
) -> RenderedFetchResult:
    """T1: TinyFish fetch_content (JS-rendered, markdown + page_metadata + links)."""
    tf_client = client or TinyFishClient(mock=mock)
    results = await tf_client.fetch_contents(
        urls=[url],
        format="markdown",
        links=True,
        image_links=True,
    )
    if results:
        return results[0]
    return RenderedFetchResult(url=url, title="Failed Fetch", text="")
