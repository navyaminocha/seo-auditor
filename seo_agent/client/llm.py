import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from seo_agent.config import settings

logger = logging.getLogger("seo_agent.llm")


class LLMClient:
    """Provider-agnostic LLM client with structured JSON output and mock/offline fallback."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = (
            api_key
            or settings.OPENAI_API_KEY
            or settings.GROQ_API_KEY
            or settings.GEMINI_API_KEY
        )
        self.model = model or settings.OPENAI_MODEL
        self.base_url = settings.OPENAI_BASE_URL
        
        # Determine if OpenAI client is available
        self._client = None
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON response using LLM or offline fallback."""
        if self._client:
            try:
                messages = [
                    {"role": "system", "content": system_prompt + "\nRespond ONLY with a valid JSON object matching the requested schema. Do not enclose in markdown blocks if possible."},
                    {"role": "user", "content": user_prompt},
                ]
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "response_format": {"type": "json_object"},
                }
                response = await self._client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or "{}"
                return json.loads(content)
            except Exception as e:
                logger.warning(f"LLM API call failed: {e}. Using deterministic extraction fallback.")

        # Deterministic offline fallback if no API key or call failed
        return self._deterministic_fallback(system_prompt, user_prompt)

    def _deterministic_fallback(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Deterministic heuristic fallback when LLM API is not configured or in mock mode."""
        prompt_lower = (system_prompt + " " + user_prompt).lower()
        
        # 1. AI Q&A Fallback
        if "qa_test" in prompt_lower or "5 questions" in prompt_lower or "what does this site offer" in prompt_lower:
            return self._fallback_qa_test(user_prompt)
            
        # 2. Competitor Gap Analysis Fallback
        if "competitor" in prompt_lower or "gap analysis" in prompt_lower:
            return self._fallback_competitor_gap(user_prompt)

        # 3. Query Inference Fallback
        if "infer" in prompt_lower and "query" in prompt_lower:
            return self._fallback_infer_query(user_prompt)

        # 4. Agent Planning Step Fallback
        if "orchestrator" in prompt_lower or "decide next tool" in prompt_lower:
            return {
                "decision": "Execute next deterministic SEO audit check",
                "next_tool": "run_checks",
                "reasoning": "Standard progression of audit checks."
            }

        return {"status": "ok", "message": "Deterministic fallback output"}

    def _fallback_infer_query(self, text: str) -> Dict[str, Any]:
        # Extract title or main keywords
        title_match = re.search(r"Title:\s*([^\n]+)", text)
        if title_match:
            clean_title = re.sub(r"[|\-–].*$", "", title_match.group(1)).strip()
            if clean_title:
                return {"query": clean_title.lower()}
        return {"query": "web agent developer tools"}

    def _fallback_qa_test(self, text: str) -> Dict[str, Any]:
        """Extract answers to 5 standard questions deterministically with strict substring quotes."""
        # Find the text payload
        extracted_text = text
        text_match = re.search(r"Page Text:\s*(.*)", text, re.DOTALL)
        if text_match:
            extracted_text = text_match.group(1).strip()

        questions = [
            "What does this site offer?",
            "What does it cost?",
            "How do I contact them?",
            "Where is it located?",
            "Who is it for?",
        ]

        answers = []

        # Q1: Offer
        offer_match = re.search(r"(?:provides?|offers?|built for|infrastructure for|platform for|specializes in|solution for)\s+([^.\n]{10,120})", extracted_text, re.IGNORECASE)
        h1_match = re.search(r"^#\s+(.+)$", extracted_text, re.MULTILINE)
        if offer_match:
            quote = offer_match.group(0)
            answers.append({
                "question": questions[0],
                "status": "ANSWERED",
                "answer": f"The site offers: {quote.strip()}",
                "evidence_quote": quote
            })
        elif h1_match:
            quote = h1_match.group(1).strip()
            answers.append({
                "question": questions[0],
                "status": "ANSWERED",
                "answer": f"The page is dedicated to: {quote}",
                "evidence_quote": quote
            })
        else:
            answers.append({
                "question": questions[0],
                "status": "VAGUE",
                "answer": "General web services mentioned, but specific core offering is not clearly articulated.",
                "evidence_quote": ""
            })

        # Q2: Cost
        cost_match = re.search(r"(\$\d+(?:\.\d+)?(?:\s*/\s*(?:mo|month|year|yr|user|credit))?|free trial|custom pricing|starts at \$?\d+|pricing starts at [^\n.]+)", extracted_text, re.IGNORECASE)
        if cost_match:
            quote = cost_match.group(0)
            answers.append({
                "question": questions[1],
                "status": "ANSWERED",
                "answer": f"Pricing stated: {quote}",
                "evidence_quote": quote
            })
        elif "pricing" in extracted_text.lower():
            p_snippet = re.search(r"([^.\n]{0,30}pricing[^.\n]{0,50})", extracted_text, re.IGNORECASE)
            quote = p_snippet.group(1).strip() if p_snippet else "pricing"
            answers.append({
                "question": questions[1],
                "status": "VAGUE",
                "answer": "Pricing is mentioned but concrete numbers/tiers are not explicitly listed in the main text.",
                "evidence_quote": quote if quote in extracted_text else ""
            })
        else:
            answers.append({
                "question": questions[1],
                "status": "NOT_FOUND",
                "answer": "No pricing or cost information found in the extracted text.",
                "evidence_quote": ""
            })

        # Q3: Contact
        contact_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+|contact us at [^\n.]+|\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})", extracted_text, re.IGNORECASE)
        if contact_match:
            quote = contact_match.group(0)
            answers.append({
                "question": questions[2],
                "status": "ANSWERED",
                "answer": f"Contact via {quote}",
                "evidence_quote": quote
            })
        elif "contact" in extracted_text.lower() or "support" in extracted_text.lower():
            c_snippet = re.search(r"([^.\n]{0,30}(?:contact|support)[^.\n]{0,50})", extracted_text, re.IGNORECASE)
            quote = c_snippet.group(1).strip() if c_snippet else "contact"
            answers.append({
                "question": questions[2],
                "status": "VAGUE",
                "answer": "Mentions contact or support link, but direct email/phone/form is not presented in the body text.",
                "evidence_quote": quote if quote in extracted_text else ""
            })
        else:
            answers.append({
                "question": questions[2],
                "status": "NOT_FOUND",
                "answer": "No contact information, email, or telephone number found on the page.",
                "evidence_quote": ""
            })

        # Q4: Location
        location_match = re.search(r"(San Francisco|New York|London|California|Austin|Seattle|Boston|Berlin|Toronto|CA|NY|USA|United States|headquartered in [^\n.]+)", extracted_text, re.IGNORECASE)
        if location_match:
            quote = location_match.group(0)
            answers.append({
                "question": questions[3],
                "status": "ANSWERED",
                "answer": f"Located / operating in: {quote}",
                "evidence_quote": quote
            })
        else:
            answers.append({
                "question": questions[3],
                "status": "NOT_FOUND",
                "answer": "No physical address, city, or headquarters location specified.",
                "evidence_quote": ""
            })

        # Q5: Who is it for
        audience_match = re.search(r"(?:built for|designed for|for developers|for enterprises|targeted at|for teams|for marketers|for creators)\s+([^.\n]{5,80})", extracted_text, re.IGNORECASE)
        if audience_match:
            quote = audience_match.group(0)
            answers.append({
                "question": questions[4],
                "status": "ANSWERED",
                "answer": f"Target audience: {quote}",
                "evidence_quote": quote
            })
        elif "developers" in extracted_text.lower() or "teams" in extracted_text.lower() or "enterprises" in extracted_text.lower():
            a_snippet = re.search(r"([^.\n]{0,30}(?:developers|teams|enterprises|businesses)[^.\n]{0,50})", extracted_text, re.IGNORECASE)
            quote = a_snippet.group(1).strip() if a_snippet else "teams"
            answers.append({
                "question": questions[4],
                "status": "VAGUE",
                "answer": "Implied target audience mentioned in context, but lacks an explicit target user statement.",
                "evidence_quote": quote if quote in extracted_text else ""
            })
        else:
            answers.append({
                "question": questions[4],
                "status": "NOT_FOUND",
                "answer": "Target persona or audience is unspecified.",
                "evidence_quote": ""
            })

        return {"results": answers}

    def _fallback_competitor_gap(self, text: str) -> Dict[str, Any]:
        """Deterministic gap comparison fallback."""
        return {
            "our_advantages": [
                {
                    "topic": "JavaScript Rendering & DOM Inspection",
                    "our_coverage": "Explicitly separates client-side JS rendered nodes from server HTML with side-by-side diffing.",
                    "competitor_coverage": "Focuses primarily on server-side HTTP response or standard tags without rendering parity verification.",
                    "evidence_citation": "Raw vs Rendered diff inspection"
                },
                {
                    "topic": "AI Search Engine Answer Readiness (5-Question Test)",
                    "our_coverage": "Tests whether LLM answer engines can parse 5 foundational business facts with substring verification.",
                    "competitor_coverage": "Lacks LLM answer readiness test; only audits conventional crawler tags.",
                    "evidence_citation": "AI Q&A readiness module"
                }
            ],
            "competitor_advantages": [
                {
                    "topic": "Ecosystem API Integrations",
                    "our_coverage": "Provides direct CLI and JSON report outputs.",
                    "competitor_coverage": "Offers turnkey webhooks, historical dashboards, and broader enterprise connectors.",
                    "evidence_citation": "API documentation and dashboard integration"
                }
            ],
            "content_gap_summary": "Our page provides superior technical depth on JS rendering discrepancies and AI answer engine usability, while competitors feature broader historical monitoring and integration marketing."
        }
