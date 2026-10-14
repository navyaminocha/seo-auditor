from seo_agent.models import RawFetchResult, RenderedFetchResult, DiffResult
from seo_agent.tools.checks import run_checks


def test_checks_detects_missing_tags():
    raw = RawFetchResult(
        url="https://empty-meta.com",
        final_url="https://empty-meta.com",
        status_code=200,
        html="<html><head></head><body><p>Bare content</p><img src='/hero.png'></body></html>",
    )
    rendered = RenderedFetchResult(
        url="https://empty-meta.com",
        title="",
        description="",
        text="Bare content",
        links=[],
    )
    diff = DiffResult(url="https://empty-meta.com", title_raw="", title_rendered="")

    candidates = run_checks(raw, rendered, diff)
    check_ids = [c.check_id for c in candidates]

    assert "TITLE_MISSING" in check_ids
    assert "META_DESC_MISSING" in check_ids
    assert "CANONICAL_MISSING" in check_ids
    assert "H1_MISSING" in check_ids
    assert "IMG_MISSING_ALT" in check_ids


def test_checks_detects_robots_noindex():
    raw = RawFetchResult(
        url="https://noindex.com",
        final_url="https://noindex.com",
        status_code=200,
        headers={"x-robots-tag": "noindex, nofollow"},
        html="<html><head><title>Noindex Page with Enough Characters</title></head><body><h1>Heading</h1></body></html>",
    )
    rendered = RenderedFetchResult(
        url="https://noindex.com",
        title="Noindex Page with Enough Characters",
        text="# Heading",
    )
    diff = DiffResult(url="https://noindex.com", robots_raw="noindex")

    candidates = run_checks(raw, rendered, diff)
    check_ids = [c.check_id for c in candidates]
    assert "ROBOTS_NOINDEX" in check_ids
