import re
from typing import List, Tuple
from bs4 import BeautifulSoup

from seo_agent.models import RawFetchResult, RenderedFetchResult, DiffResult


def diff_raw_vs_rendered(
    raw: RawFetchResult,
    rendered: RenderedFetchResult,
) -> DiffResult:
    """T3: Compares raw server HTML against TinyFish JS-rendered markdown/DOM.
    Measures word count, titles, H1/H2 tags, canonical URLs, robots meta, link counts,
    and identifies content existing ONLY after client-side JavaScript execution.
    """
    soup = BeautifulSoup(raw.html, "html.parser")

    # 1. Title
    title_raw = ""
    if soup.title and soup.title.string:
        title_raw = soup.title.string.strip()
    title_rendered = rendered.title.strip()
    title_matches = (title_raw.lower() == title_rendered.lower()) if (title_raw and title_rendered) else False

    # 2. Headings from Raw HTML
    h1_raw = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
    h2_raw = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]

    # Headings from Rendered Markdown
    h1_rendered = [m.strip() for m in re.findall(r"^#\s+(.+)$", rendered.text, re.MULTILINE)]
    h2_rendered = [m.strip() for m in re.findall(r"^##\s+(.+)$", rendered.text, re.MULTILINE)]

    # 3. Canonical Tag
    canonical_raw = ""
    canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r)
    if canonical_tag and canonical_tag.get("href"):
        canonical_raw = canonical_tag.get("href", "").strip()
    
    # Check rendered text/links for canonical or rendered metadata
    canonical_rendered = canonical_raw  # Default to raw if rendered didn't change it

    # 4. Robots Meta
    robots_raw = ""
    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if robots_tag and robots_tag.get("content"):
        robots_raw = robots_tag.get("content", "").strip()
    robots_rendered = robots_raw

    # 5. Links
    raw_links = [a.get("href") for a in soup.find_all("a", href=True)]
    link_count_raw = len(raw_links)
    link_count_rendered = len(rendered.links) if rendered.links else link_count_raw

    # 6. Word Count & Text Extraction
    # Clean raw text from soup
    for elem in soup(["script", "style", "noscript", "svg"]):
        elem.extract()
    raw_text = soup.get_text(separator=" ", strip=True)
    raw_words = re.findall(r"\b\w+\b", raw_text.lower())
    rendered_words = re.findall(r"\b\w+\b", rendered.text.lower())

    word_count_raw = len(raw_words)
    word_count_rendered = len(rendered_words)
    word_count_diff = word_count_rendered - word_count_raw

    # 7. Text Overlap %
    raw_set = set(raw_words)
    rendered_set = set(rendered_words)
    if rendered_set:
        overlap_pct = round((len(raw_set.intersection(rendered_set)) / len(rendered_set)) * 100, 1)
    else:
        overlap_pct = 100.0

    # 8. Content that exists ONLY after rendering
    # Break rendered text into sentences/paragraphs and check if they exist in raw HTML
    js_only_snippets: List[str] = []
    rendered_lines = [line.strip() for line in rendered.text.split("\n") if line.strip()]
    for line in rendered_lines:
        # Ignore markdown headers syntax for check
        clean_line = re.sub(r"^#+\s*", "", line).strip()
        if len(clean_line) > 25 and clean_line.lower() not in raw.html.lower():
            js_only_snippets.append(clean_line)

    is_heavy_js = (
        (word_count_rendered > 100 and word_count_raw < 50)
        or (word_count_rendered > 2 * max(1, word_count_raw))
        or (not h1_raw and bool(h1_rendered))
        or (title_raw.lower() in ("loading...", "") and bool(title_rendered))
    )

    summary_parts = []
    if is_heavy_js:
        summary_parts.append(
            f"CRITICAL DISCREPANCY: Client-side JS generates {word_count_diff:+d} words not present in initial HTML."
        )
        if not h1_raw and h1_rendered:
            summary_parts.append(f"H1 '{h1_rendered[0]}' injected by JS only.")
        if title_raw != title_rendered:
            summary_parts.append(f"Title rendered dynamically ('{title_rendered}' vs raw '{title_raw}').")
    else:
        summary_parts.append("High parity: Server HTML contains primary text and meta tags.")

    return DiffResult(
        url=raw.url,
        word_count_raw=word_count_raw,
        word_count_rendered=word_count_rendered,
        word_count_diff=word_count_diff,
        title_raw=title_raw,
        title_rendered=title_rendered,
        title_matches=title_matches,
        h1_raw=h1_raw,
        h1_rendered=h1_rendered,
        h2_raw=h2_raw,
        h2_rendered=h2_rendered,
        canonical_raw=canonical_raw,
        canonical_rendered=canonical_rendered,
        robots_raw=robots_raw,
        robots_rendered=robots_rendered,
        link_count_raw=link_count_raw,
        link_count_rendered=link_count_rendered,
        main_text_overlap_pct=overlap_pct,
        js_only_content=js_only_snippets[:5],  # Top 5 illustrative snippets
        is_heavily_js_dependent=is_heavy_js,
        render_discrepancy_summary=" ".join(summary_parts),
    )
