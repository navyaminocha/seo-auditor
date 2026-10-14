import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

from seo_agent.models import (
    RawFetchResult,
    RenderedFetchResult,
    DiffResult,
    FindingCandidate,
    VerifiedFinding,
    VerificationStatus,
    Severity,
)


def verify_finding(
    candidate: FindingCandidate,
    raw: RawFetchResult,
    rendered: RenderedFetchResult,
    diff: DiffResult,
) -> VerifiedFinding:
    """T5: Re-tests an issue candidate against concrete deterministic evidence.
    Returns CONFIRMED, UNCONFIRMED, or LIKELY_FALSE_POSITIVE with exact raw tag, status code,
    and a transparent priority score (impact x effort heuristic).
    """
    soup = BeautifulSoup(raw.html, "html.parser")
    status = VerificationStatus.CONFIRMED
    evidence_parts = []
    impact = candidate.suggested_impact
    effort = candidate.suggested_effort
    recommendation = ""

    # Check 1: Missing Title
    if candidate.check_id in ("TITLE_MISSING", "TITLE_TOO_SHORT", "TITLE_TOO_LONG"):
        raw_title = soup.title.string.strip() if (soup.title and soup.title.string) else ""
        rendered_title = rendered.title.strip()

        if candidate.check_id == "TITLE_MISSING":
            if not raw_title and not rendered_title:
                status = VerificationStatus.CONFIRMED
                evidence_parts.append("Confirmed absent in both raw HTML <title> and TinyFish rendered DOM.")
                recommendation = "Add an explicit <title> tag in the HTML <head> with your primary brand and value proposition."
            elif not raw_title and rendered_title:
                status = VerificationStatus.LIKELY_FALSE_POSITIVE
                evidence_parts.append(
                    f"Legacy crawler false positive: <title> is missing in raw HTML, but injected client-side by JS ('{rendered_title}')."
                )
                recommendation = "Server-render the <title> tag so non-rendering crawlers and social scrapers see it immediately."
            else:
                status = VerificationStatus.UNCONFIRMED
                evidence_parts.append(f"Title tag found: '{raw_title}' ({len(raw_title)} chars).")

        elif candidate.check_id == "TITLE_TOO_SHORT":
            t = rendered_title or raw_title
            if len(t) < 25:
                status = VerificationStatus.CONFIRMED
                evidence_parts.append(f"Title length is {len(t)} characters (exact text: '{t}').")
                recommendation = "Expand title to 35-60 characters including high-intent search keywords."
            else:
                status = VerificationStatus.UNCONFIRMED
                evidence_parts.append(f"Title length is {len(t)} characters, which meets minimal threshold.")

        elif candidate.check_id == "TITLE_TOO_LONG":
            t = rendered_title or raw_title
            if len(t) > 65:
                status = VerificationStatus.CONFIRMED
                evidence_parts.append(f"Title length is {len(t)} characters (exceeds Google desktop 600px / ~65 chars cutoff).")
                recommendation = "Trim title to under 60 characters to prevent ellipsis truncation in SERPs."
            else:
                status = VerificationStatus.UNCONFIRMED
                evidence_parts.append(f"Title is {len(t)} characters.")

    # Check 2: Missing Meta Description
    elif candidate.check_id in ("META_DESC_MISSING", "META_DESC_TOO_SHORT"):
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag.get("content", "").strip()
        rendered_desc = rendered.description.strip() or meta_desc

        if candidate.check_id == "META_DESC_MISSING":
            if not meta_desc and not rendered_desc:
                status = VerificationStatus.CONFIRMED
                evidence_parts.append("Confirmed: <meta name='description'> tag is completely absent.")
                recommendation = "Add a compelling meta description between 120-155 characters."
            elif not meta_desc and rendered_desc:
                status = VerificationStatus.LIKELY_FALSE_POSITIVE
                evidence_parts.append(f"Injected via JS ('{rendered_desc[:40]}...'). Legacy raw crawlers missed it.")
                recommendation = "Move meta description to server-side HTML."
            else:
                status = VerificationStatus.UNCONFIRMED
                evidence_parts.append(f"Meta description exists: '{meta_desc[:50]}...'")
        elif candidate.check_id == "META_DESC_TOO_SHORT":
            d = rendered_desc or meta_desc
            if len(d) < 50:
                status = VerificationStatus.CONFIRMED
                evidence_parts.append(f"Meta description is only {len(d)} characters ('{d}').")
                recommendation = "Expand meta description to at least 120 characters."
            else:
                status = VerificationStatus.UNCONFIRMED
                evidence_parts.append(f"Description length is {len(d)} chars.")

    # Check 3: Canonical Tag
    elif candidate.check_id == "CANONICAL_MISSING":
        canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r)
        http_link_header = raw.headers.get("link", "")
        has_http_canonical = "rel=\"canonical\"" in http_link_header or "rel=canonical" in http_link_header

        if not canonical_tag and not has_http_canonical:
            status = VerificationStatus.CONFIRMED
            evidence_parts.append("Confirmed: No <link rel='canonical'> in HTML and no Link canonical HTTP header.")
            recommendation = f"Add <link rel='canonical' href='{raw.url}'> to prevent duplicate URL indexing."
        elif has_http_canonical and not canonical_tag:
            status = VerificationStatus.LIKELY_FALSE_POSITIVE
            evidence_parts.append(f"Legacy tool false positive: Canonical supplied via HTTP header: '{http_link_header}'")
            recommendation = "Canonical is validly served via HTTP header. No action needed."
        else:
            status = VerificationStatus.UNCONFIRMED
            evidence_parts.append(f"Canonical tag present: '{canonical_tag.get('href')}'")

    # Check 4: Robots Noindex
    elif candidate.check_id == "ROBOTS_NOINDEX":
        meta_robots = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        content = meta_robots.get("content", "").lower() if meta_robots else ""
        x_robots = raw.headers.get("x-robots-tag", "").lower()

        if "noindex" in content or "noindex" in x_robots:
            status = VerificationStatus.CONFIRMED
            evidence_parts.append(f"Confirmed indexing blocked: meta='{content}', x-robots-tag='{x_robots}'")
            recommendation = "Remove 'noindex' directive immediately if this page is intended for public search engines."
        else:
            status = VerificationStatus.UNCONFIRMED
            evidence_parts.append("No active 'noindex' directive found in meta or HTTP response.")

    # Check 5: Heading Structure
    elif candidate.check_id in ("H1_MISSING", "H1_MULTIPLE"):
        raw_h1s = diff.h1_raw
        rendered_h1s = diff.h1_rendered

        if candidate.check_id == "H1_MISSING":
            if not raw_h1s and not rendered_h1s:
                status = VerificationStatus.CONFIRMED
                evidence_parts.append("Confirmed: 0 <h1> tags found in server HTML or rendered document.")
                recommendation = "Add a single, semantic <h1> heading describing the page topic."
            elif not raw_h1s and rendered_h1s:
                status = VerificationStatus.LIKELY_FALSE_POSITIVE
                evidence_parts.append(f"Rendered parity note: <h1> '{rendered_h1s[0]}' rendered dynamically via JS.")
                recommendation = "Render <h1> in server HTML for faster crawler discovery."
            else:
                status = VerificationStatus.UNCONFIRMED
                evidence_parts.append(f"H1 tag verified: '{raw_h1s[0]}'")

        elif candidate.check_id == "H1_MULTIPLE":
            all_h1s = rendered_h1s or raw_h1s
            if len(all_h1s) > 1:
                status = VerificationStatus.CONFIRMED
                evidence_parts.append(f"Confirmed {len(all_h1s)} distinct <h1> tags: {', '.join(all_h1s[:2])}")
                recommendation = "Refactor heading hierarchy so only one top-level <h1> represents the page title."
            else:
                status = VerificationStatus.UNCONFIRMED
                evidence_parts.append(f"Only {len(all_h1s)} H1 tag found.")

    # Check 6: Images Missing Alt
    elif candidate.check_id == "IMG_MISSING_ALT":
        img_tags = soup.find_all("img")
        unlabeled = [img.get("src", "unknown") for img in img_tags if not img.get("alt")]
        if unlabeled:
            status = VerificationStatus.CONFIRMED
            evidence_parts.append(f"Confirmed: {len(unlabeled)} images lack alt attribute (e.g. {unlabeled[0]}).")
            recommendation = "Add descriptive alt attributes to all informational images."
        else:
            status = VerificationStatus.UNCONFIRMED
            evidence_parts.append("All inspected images contain alt attributes.")

    # Check 7: JS Render Dependency
    elif candidate.check_id == "JS_RENDER_DEPENDENCY":
        if diff.is_heavily_js_dependent:
            status = VerificationStatus.CONFIRMED
            evidence_parts.append(
                f"Confirmed: Raw word count is {diff.word_count_raw} vs {diff.word_count_rendered} rendered. "
                f"Overlap is only {diff.main_text_overlap_pct}%. Initial HTML is missing {len(diff.js_only_content)} core content blocks."
            )
            recommendation = "Adopt Server-Side Rendering (SSR) or Static Site Generation (SSG) to ensure indexability."
        else:
            status = VerificationStatus.UNCONFIRMED
            evidence_parts.append("Content parity between raw and rendered is satisfactory.")

    # Check 8: Redirect Chain
    elif candidate.check_id == "REDIRECT_CHAIN":
        if len(raw.redirect_chain) > 2:
            status = VerificationStatus.CONFIRMED
            evidence_parts.append(f"Confirmed redirect chain ({len(raw.redirect_chain)} hops): {' -> '.join(raw.redirect_chain)}")
            recommendation = f"Update internal links and server redirects to point directly to {raw.final_url}."
        else:
            status = VerificationStatus.UNCONFIRMED
            evidence_parts.append(f"No excessive redirect chain ({len(raw.redirect_chain)} hops).")

    # Priority score formula:
    # Priority = (Impact * 2.0) / max(1, Effort)
    # Range: from 0.4 (Impact 1, Effort 5) up to 10.0 (Impact 5, Effort 1)
    priority_score = round((impact * 2.0) / max(1, effort), 2)
    formula_explanation = "Priority = (Impact[1-5] * 2) / Effort[1-5] (Heuristic: high impact, quick win yields highest score)"

    return VerifiedFinding(
        id=candidate.id,
        check_id=candidate.check_id,
        title=candidate.title,
        description=candidate.description,
        severity=candidate.severity,
        verification_status=status,
        evidence=" ".join(evidence_parts),
        impact_score=impact,
        effort_score=effort,
        priority_score=priority_score,
        priority_formula=formula_explanation,
        recommendation=recommendation,
    )
