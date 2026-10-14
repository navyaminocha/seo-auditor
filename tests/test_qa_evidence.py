import pytest
from seo_agent.models import RenderedFetchResult, QAStatus
from seo_agent.tools.qa_test import run_qa_test
from seo_agent.client.llm import LLMClient


class MockLLMWithHallucination(LLMClient):
    """Simulates an LLM that invents a quote not present in the text."""
    async def generate_json(self, system_prompt: str, user_prompt: str, **kwargs):
        return {
            "results": [
                {
                    "question": "What does this site offer?",
                    "status": "ANSWERED",
                    "answer": "They offer quantum cloud hyper-scaling.",
                    "evidence_quote": "This sentence definitely does not exist anywhere on the page at all."
                },
                {
                    "question": "What does it cost?",
                    "status": "ANSWERED",
                    "answer": "Starts at $49/month",
                    "evidence_quote": "starts at $49/month"
                },
                {
                    "question": "How do I contact them?",
                    "status": "NOT_FOUND",
                    "answer": "Not specified",
                    "evidence_quote": ""
                },
                {
                    "question": "Where is it located?",
                    "status": "NOT_FOUND",
                    "answer": "Not specified",
                    "evidence_quote": ""
                },
                {
                    "question": "Who is it for?",
                    "status": "NOT_FOUND",
                    "answer": "Not specified",
                    "evidence_quote": ""
                }
            ]
        }


@pytest.mark.asyncio
async def test_qa_rejects_hallucinated_quote_and_downgrades():
    page_text = "# Cloud Services\n\nPricing starts at $49/month for all standard accounts.\nContact page is disabled."
    rendered = RenderedFetchResult(
        url="https://cloud.io",
        title="Cloud Services",
        text=page_text,
    )

    fake_llm = MockLLMWithHallucination()
    qa_result = await run_qa_test(rendered, llm=fake_llm)

    # Q1 had a hallucinated quote!
    q1 = qa_result.questions[0]
    assert q1.is_verified_substring is False
    assert q1.status == QAStatus.VAGUE  # Downgraded from ANSWERED!
    assert "Downgraded from ANSWERED" in q1.verification_notes

    # Q2 had a real quote ("starts at $49/month")!
    q2 = qa_result.questions[1]
    assert q2.is_verified_substring is True
    assert q2.status == QAStatus.ANSWERED
    assert q2.evidence_quote == "starts at $49/month"
