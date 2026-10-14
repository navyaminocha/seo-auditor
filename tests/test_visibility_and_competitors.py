import pytest
from seo_agent.models import RenderedFetchResult
from seo_agent.tools.visibility import check_search_visibility
from seo_agent.tools.competitors import compare_competitors
from seo_agent.client.tinyfish import TinyFishClient


@pytest.mark.asyncio
async def test_search_visibility_position_matching():
    tf_client = TinyFishClient(mock=True)
    rendered = RenderedFetchResult(
        url="https://docs.stripe.com/payments",
        title="Stripe Payments - Online Payment Processing",
        text="# Stripe Payments",
    )

    res = await check_search_visibility(
        target_url="https://docs.stripe.com/payments",
        query="online payment processing",
        rendered=rendered,
        tf_client=tf_client,
    )

    assert res.is_visible is True
    assert res.position is not None
    assert "RANKING" in res.visibility_status


@pytest.mark.asyncio
async def test_competitor_comparison_excludes_self_and_aggregators():
    tf_client = TinyFishClient(mock=True)
    rendered = RenderedFetchResult(
        url="https://docs.stripe.com/payments",
        title="Stripe Payments",
        text="# Stripe Payments\n\nStripe provides online payment infrastructure.",
    )

    comp_res = await compare_competitors(
        target_url="https://docs.stripe.com/payments",
        query="online payment processing",
        target_rendered=rendered,
        tf_client=tf_client,
    )

    # Competitors must not include self domain
    for c in comp_res.competitors:
        assert "docs.stripe.com" not in c
    assert len(comp_res.competitors) == 2
    assert len(comp_res.competitor_qa) == 2
