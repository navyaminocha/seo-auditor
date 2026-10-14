from seo_agent.models import (
    FindingCandidate,
    RawFetchResult,
    RenderedFetchResult,
    DiffResult,
    VerificationStatus,
    Severity,
)
from seo_agent.tools.verify import verify_finding


def test_verify_detects_false_positive_when_js_renders_title():
    cand = FindingCandidate(
        id="c1",
        check_id="TITLE_MISSING",
        title="Missing Title Tag",
        description="Missing title",
        severity=Severity.CRITICAL,
        suggested_impact=5,
        suggested_effort=1,
    )
    # Raw HTML has NO title, but Rendered DOM DOES have title
    raw = RawFetchResult(
        url="https://csr-app.com",
        final_url="https://csr-app.com",
        status_code=200,
        html="<html><head></head><body><div id='root'></div></body></html>",
    )
    rendered = RenderedFetchResult(
        url="https://csr-app.com",
        title="Dynamically Injected Title",
        text="Content",
    )
    diff = DiffResult(url="https://csr-app.com", title_raw="", title_rendered="Dynamically Injected Title")

    vf = verify_finding(cand, raw, rendered, diff)
    assert vf.verification_status == VerificationStatus.LIKELY_FALSE_POSITIVE
    assert "Legacy crawler false positive" in vf.evidence
    # Check priority score formula: (impact * 2) / effort = (5 * 2) / 1 = 10.0
    assert vf.priority_score == 10.0


def test_verify_confirms_true_missing_canonical():
    cand = FindingCandidate(
        id="c2",
        check_id="CANONICAL_MISSING",
        title="Missing Canonical Tag",
        description="Missing canonical",
        severity=Severity.MEDIUM,
        suggested_impact=3,
        suggested_effort=1,
    )
    raw = RawFetchResult(
        url="https://mysite.com",
        final_url="https://mysite.com",
        status_code=200,
        headers={},
        html="<html><head><title>Some Title Here With Chars</title></head><body><h1>H1</h1></body></html>",
    )
    rendered = RenderedFetchResult(url="https://mysite.com", title="Some Title Here With Chars")
    diff = DiffResult(url="https://mysite.com", canonical_raw="")

    vf = verify_finding(cand, raw, rendered, diff)
    assert vf.verification_status == VerificationStatus.CONFIRMED
    assert "Confirmed: No <link rel='canonical'>" in vf.evidence
    # Priority score: (3 * 2) / 1 = 6.0
    assert vf.priority_score == 6.0
