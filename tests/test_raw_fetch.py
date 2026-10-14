import pytest
from seo_agent.tools.fetch_raw import fetch_raw


@pytest.mark.asyncio
async def test_fetch_raw_mock_normal():
    res = await fetch_raw("https://docs.stripe.com/payments", mock=True)
    assert res.status_code == 200
    assert "Online Payment Processing" in res.html
    assert "content-type" in res.headers
    assert res.response_time_ms >= 0


@pytest.mark.asyncio
async def test_fetch_raw_mock_jsheavy():
    res = await fetch_raw("https://spa-showcase.app/dashboard", mock=True)
    assert res.status_code == 200
    assert '<div id="root"></div>' in res.html
    assert "<noscript>" in res.html
