from seo_agent.models import RawFetchResult, RenderedFetchResult
from seo_agent.tools.diff import diff_raw_vs_rendered


def test_diff_normal_site():
    raw = RawFetchResult(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        headers={"content-type": "text/html"},
        html="<html><head><title>Example Page</title><link rel='canonical' href='https://example.com'></head><body><h1>Example Heading</h1><p>This is a solid paragraph explaining our service with enough detail.</p></body></html>",
    )
    rendered = RenderedFetchResult(
        url="https://example.com",
        final_url="https://example.com",
        title="Example Page",
        text="# Example Heading\n\nThis is a solid paragraph explaining our service with enough detail.",
        links=["https://example.com/pricing"],
    )

    diff = diff_raw_vs_rendered(raw, rendered)
    assert diff.title_matches is True
    assert abs(diff.word_count_diff) <= 5
    assert diff.is_heavily_js_dependent is False
    assert diff.canonical_raw == "https://example.com"


def test_diff_js_heavy_site():
    raw = RawFetchResult(
        url="https://spa.com",
        final_url="https://spa.com",
        status_code=200,
        headers={"content-type": "text/html"},
        html="<html><head><title>Loading...</title></head><body><div id='root'></div></body></html>",
    )
    rendered = RenderedFetchResult(
        url="https://spa.com",
        final_url="https://spa.com",
        title="Dynamic Analytics Platform",
        text="# Real-time Telemetry Dashboard\n\nWe provide deep cloud monitoring across thousands of distributed microservices.\n\nPricing starts at $99/mo with 24/7 dedicated engineering support in Austin, TX.",
        links=["/docs", "/pricing"],
    )

    diff = diff_raw_vs_rendered(raw, rendered)
    assert diff.title_matches is False
    assert diff.is_heavily_js_dependent is True
    assert len(diff.js_only_content) > 0
