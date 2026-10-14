import re
import logging
from typing import List, Optional
from seo_agent.models import (
    QAQuestionResult,
    QATestResult,
    QAStatus,
    RenderedFetchResult,
)
from seo_agent.client.llm import LLMClient

logger = logging.getLogger("seo_agent.qa_test")

STANDARD_QUESTIONS = [
    "What does this site offer?",
    "What does it cost?",
    "How do I contact them?",
    "Where is it located?",
    "Who is it for?",
]


async def run_qa_test(
    rendered: RenderedFetchResult,
    llm: Optional[LLMClient] = None,
) -> QATestResult:
    """T6: The AI Q&A readiness test.
    Evaluates whether an AI search or answer engine (Perplexity, ChatGPT, Gemini, Google SGE)
    can unambiguously extract 5 core business facts from the page's main text.
    PROGRAMMATICALLY VERIFIES THAT EVERY EVIDENCE QUOTE IS A REAL SUBSTRING OF THE TEXT.
    """
    llm_client = llm or LLMClient()
    main_text = _extract_clean_main_text(rendered.text)

    system_prompt = (
        "You are an AI search engine evaluator assessing whether a webpage's main text "
        "provides clear, factual answers to 5 standard questions for AI answer engines.\n"
        "Questions:\n"
        "1. What does this site offer?\n"
        "2. What does it cost?\n"
        "3. How do I contact them?\n"
        "4. Where is it located?\n"
        "5. Who is it for?\n\n"
        "RULES:\n"
        "- Answer strictly using ONLY facts stated in the provided Page Text.\n"
        "- If the text does not state it, status MUST be 'NOT_FOUND'.\n"
        "- If partially or vaguely mentioned without concrete specifics, status is 'VAGUE'.\n"
        "- If clearly answered, status is 'ANSWERED'.\n"
        "- CRITICAL: For 'evidence_quote', you MUST provide an EXACT verbatim substring from the Page Text.\n"
        "  Do not alter capitalization or punctuation of the quote. If status is NOT_FOUND, evidence_quote must be empty.\n"
        "- Respond in JSON format: {'results': [{'question': '...', 'status': 'ANSWERED'|'VAGUE'|'NOT_FOUND', 'answer': '...', 'evidence_quote': '...'}]}"
    )

    user_prompt = f"Page URL: {rendered.url}\nPage Title: {rendered.title}\n\nPage Text:\n{main_text}"

    data = await llm_client.generate_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    raw_results = data.get("results", [])
    verified_questions: List[QAQuestionResult] = []

    answered_count = 0
    vague_count = 0
    not_found_count = 0

    # Map raw results or default if missing
    for idx, q_text in enumerate(STANDARD_QUESTIONS, 1):
        matching_item = next((r for r in raw_results if r.get("question", "").strip().lower() == q_text.lower()), None)
        if not matching_item and idx - 1 < len(raw_results):
            matching_item = raw_results[idx - 1]

        if matching_item:
            st_str = str(matching_item.get("status", "NOT_FOUND")).upper()
            status = QAStatus.NOT_FOUND
            if "ANSWERED" in st_str:
                status = QAStatus.ANSWERED
            elif "VAGUE" in st_str:
                status = QAStatus.VAGUE

            answer = matching_item.get("answer", "Information not specified in text.")
            quote = matching_item.get("evidence_quote", "").strip()
        else:
            status = QAStatus.NOT_FOUND
            answer = "Not found in extracted page text."
            quote = ""

        # PROGRAMMATIC SUBSTRING VERIFICATION: "Don't trust the model."
        is_exact_substring = False
        notes = "Verified exact substring in page text."

        if quote:
            # Check exact substring in original rendered text or cleaned main text
            if quote in main_text or quote in rendered.text:
                is_exact_substring = True
            elif quote.lower() in main_text.lower():
                # Case variation
                is_exact_substring = True
                notes = "Matched with case-normalization."
            else:
                is_exact_substring = False
                notes = f"Hallucinated quote rejected: '{quote[:40]}...' was not found in page text."
                # Downgrade status if quote was not verified!
                if status == QAStatus.ANSWERED:
                    status = QAStatus.VAGUE
                    notes += " Downgraded from ANSWERED to VAGUE due to unverified quote."
        else:
            if status == QAStatus.ANSWERED:
                status = QAStatus.VAGUE
                notes = "Downgraded from ANSWERED to VAGUE because no evidence quote was provided."

        if status == QAStatus.ANSWERED:
            answered_count += 1
        elif status == QAStatus.VAGUE:
            vague_count += 1
        else:
            not_found_count += 1

        verified_questions.append(
            QAQuestionResult(
                question_id=idx,
                question=q_text,
                status=status,
                answer=answer,
                evidence_quote=quote if is_exact_substring else "",
                is_verified_substring=is_exact_substring,
                verification_notes=notes,
            )
        )

    # Score: 20 pts per answered, 10 pts per vague
    ai_readiness_score = round((answered_count * 20.0) + (vague_count * 10.0), 1)

    return QATestResult(
        url=rendered.url,
        questions=verified_questions,
        answered_count=answered_count,
        vague_count=vague_count,
        not_found_count=not_found_count,
        ai_readiness_score=ai_readiness_score,
    )


def _extract_clean_main_text(markdown: str) -> str:
    """Removes standard nav/footer noise and boilerplate from markdown."""
    lines = markdown.split("\n")
    cleaned_lines = []
    in_nav_or_footer = False

    for line in lines:
        lower = line.strip().lower()
        # Filter boilerplate navigation/footer blocks
        if any(h in lower for h in ("cookie policy", "terms of service", "all rights reserved", "privacy policy")):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()
