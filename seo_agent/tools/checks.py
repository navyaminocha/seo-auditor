import re
from typing import List
from bs4 import BeautifulSoup

from seo_agent.models import (
    RawFetchResult,
    RenderedFetchResult,
    DiffResult,
    FindingCandidate,
    Severity,
)


def run_checks(
    raw: RawFetchResult,
    rendered: RenderedFetchResult,
    diff: DiffResult,
) -> List[FindingCandidate]:
    """T4: Deterministic issue candidate generator.
    Scans raw HTML, rendered metadata, and diff metrics for common SEO flaws.
    """
    candidates: List[FindingCandidate] = []
    soup = BeautifulSoup(raw.html, "html.parser")

    # 1. Title Checks
    title = rendered.title or diff.title_raw
    if not title:
        candidates.append(
            FindingCandidate(
                id="chk-title-missing",
                check_id="TITLE_MISSING",
                title="Missing Title Tag",
                description="The page lacks a descriptive <title> tag in both server HTML and rendered DOM.",
                severity=Severity.CRITICAL,
                raw_evidence="<title> not found in document",
                suggested_impact=5,
                suggested_effort=1,
            )
        )
    elif len(title) < 25:
        candidates.append(
            FindingCandidate(
                id="chk-title-short",
                check_id="TITLE_TOO_SHORT",
                title=f"Title Tag Is Too Short ({len(title)} chars)",
                description=f"Title '{title}' is under the recommended 30 characters and misses keyword context.",
                severity=Severity.MEDIUM,
                raw_evidence=f"Title length: {len(title)} chars ('{title}')",
                suggested_impact=3,
                suggested_effort=1,
            )
        )
    elif len(title) > 65:
        candidates.append(
            FindingCandidate(
                id="chk-title-long",
                check_id="TITLE_TOO_LONG",
                title=f"Title Tag Exceeds SERP Display Limit ({len(title)} chars)",
                description=f"Title '{title}' exceeds 65 characters and is likely truncated in Google search snippets.",
                severity=Severity.LOW,
                raw_evidence=f"Title length: {len(title)} chars",
                suggested_impact=2,
                suggested_effort=1,
            )
        )

    # 2. Meta Description Checks
    desc = rendered.description
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if meta_desc_tag and meta_desc_tag.get("content"):
        desc = desc or meta_desc_tag.get("content", "").strip()

    if not desc:
        candidates.append(
            FindingCandidate(
                id="chk-desc-missing",
                check_id="META_DESC_MISSING",
                title="Missing Meta Description",
                description="No meta description found. Search engines will automatically generate snippets from arbitrary page text.",
                severity=Severity.HIGH,
                raw_evidence="<meta name='description'> tag absent",
                suggested_impact=4,
                suggested_effort=1,
            )
        )
    elif len(desc) < 50:
        candidates.append(
            FindingCandidate(
                id="chk-desc-short",
                check_id="META_DESC_TOO_SHORT",
                title=f"Meta Description Too Short ({len(desc)} chars)",
                description=f"Description is too brief ({len(desc)} chars). Recommended length is 120-160 characters.",
                severity=Severity.LOW,
                raw_evidence=f"Meta description: '{desc}'",
                suggested_impact=2,
                suggested_effort=1,
            )
        )

    # 3. Canonical Tag Checks
    canonical = diff.canonical_raw or diff.canonical_rendered
    if not canonical:
        candidates.append(
            FindingCandidate(
                id="chk-canonical-missing",
                check_id="CANONICAL_MISSING",
                title="Missing Canonical Tag",
                description="No <link rel='canonical'> specified. Search engines may split ranking authority across query parameters.",
                severity=Severity.MEDIUM,
                raw_evidence="<link rel='canonical'> not found in HTML head",
                suggested_impact=3,
                suggested_effort=1,
            )
        )

    # 4. Robots Noindex Checks
    robots = (diff.robots_raw or "").lower()
    x_robots = raw.headers.get("x-robots-tag", "").lower()
    if "noindex" in robots or "noindex" in x_robots:
        candidates.append(
            FindingCandidate(
                id="chk-robots-noindex",
                check_id="ROBOTS_NOINDEX",
                title="Robots Noindex Directive Active",
                description="The page explicitly requests search engines not to index this URL.",
                severity=Severity.CRITICAL,
                raw_evidence=f"Robots meta: '{diff.robots_raw}' | X-Robots-Tag: '{x_robots}'",
                suggested_impact=5,
                suggested_effort=1,
            )
        )

    # 5. Heading Structure Checks
    h1s = diff.h1_rendered or diff.h1_raw
    if not h1s:
        candidates.append(
            FindingCandidate(
                id="chk-h1-missing",
                check_id="H1_MISSING",
                title="Missing H1 Heading",
                description="No primary <h1> heading found on the page.",
                severity=Severity.HIGH,
                raw_evidence="0 <h1> tags detected in rendered markdown and raw HTML",
                suggested_impact=4,
                suggested_effort=1,
            )
        )
    elif len(h1s) > 1:
        candidates.append(
            FindingCandidate(
                id="chk-h1-multiple",
                check_id="H1_MULTIPLE",
                title=f"Multiple H1 Headings ({len(h1s)} detected)",
                description=f"Found {len(h1s)} separate H1 tags. Recommended best practice is exactly one H1 per page.",
                severity=Severity.LOW,
                raw_evidence=f"H1 tags: {', '.join(h1s[:3])}",
                suggested_impact=2,
                suggested_effort=1,
            )
        )

    # 6. Redirect Chains
    if len(raw.redirect_chain) > 2:
        candidates.append(
            FindingCandidate(
                id="chk-redirect-chain",
                check_id="REDIRECT_CHAIN",
                title=f"Long Redirect Chain ({len(raw.redirect_chain)} hops)",
                description=f"URL goes through {len(raw.redirect_chain)} redirects before reaching destination, wasting crawl budget.",
                severity=Severity.MEDIUM,
                raw_evidence=f"Hops: {' -> '.join(raw.redirect_chain)}",
                suggested_impact=3,
                suggested_effort=2,
            )
        )

    # 7. Images Missing Alt Text
    img_tags = soup.find_all("img")
    imgs_without_alt = [img.get("src", "unknown") for img in img_tags if not img.get("alt")]
    if imgs_without_alt:
        candidates.append(
            FindingCandidate(
                id="chk-img-missing-alt",
                check_id="IMG_MISSING_ALT",
                title=f"Images Missing Alt Text ({len(imgs_without_alt)} found)",
                description=f"{len(imgs_without_alt)} images lack accessibility and search-friendly alt attributes.",
                severity=Severity.MEDIUM,
                raw_evidence=f"Images without alt: {', '.join(imgs_without_alt[:3])}",
                suggested_impact=3,
                suggested_effort=2,
            )
        )

    # 8. JS Render Dependency / Discrepancy
    if diff.is_heavily_js_dependent:
        candidates.append(
            FindingCandidate(
                id="chk-js-render-dependency",
                check_id="JS_RENDER_DEPENDENCY",
                title="Critical Client-Side Rendering Dependency",
                description=f"Server HTML is an empty shell or lacks core content. TinyFish rendered {diff.word_count_diff:+d} words not present in initial HTML.",
                severity=Severity.CRITICAL,
                raw_evidence=f"Raw words: {diff.word_count_raw} vs Rendered words: {diff.word_count_rendered} | JS-only snippets: {len(diff.js_only_content)}",
                suggested_impact=5,
                suggested_effort=4,
            )
        )

    return candidates
