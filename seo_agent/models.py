from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    UNCONFIRMED = "UNCONFIRMED"
    LIKELY_FALSE_POSITIVE = "LIKELY_FALSE_POSITIVE"


class QAStatus(str, Enum):
    ANSWERED = "ANSWERED"
    VAGUE = "VAGUE"
    NOT_FOUND = "NOT_FOUND"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RawFetchResult(BaseModel):
    url: str
    final_url: str
    status_code: int
    headers: Dict[str, str] = Field(default_factory=dict)
    html: str = ""
    redirect_chain: List[str] = Field(default_factory=list)
    response_time_ms: float = 0.0


class RenderedFetchResult(BaseModel):
    url: str
    final_url: str = ""
    title: str = ""
    description: str = ""
    language: str = ""
    format: str = "markdown"
    text: str = ""  # Clean markdown extracted text
    links: List[str] = Field(default_factory=list)
    image_links: List[str] = Field(default_factory=list)
    response_time_ms: float = 0.0


class DiffResult(BaseModel):
    url: str
    word_count_raw: int = 0
    word_count_rendered: int = 0
    word_count_diff: int = 0
    title_raw: str = ""
    title_rendered: str = ""
    title_matches: bool = True
    h1_raw: List[str] = Field(default_factory=list)
    h1_rendered: List[str] = Field(default_factory=list)
    h2_raw: List[str] = Field(default_factory=list)
    h2_rendered: List[str] = Field(default_factory=list)
    canonical_raw: str = ""
    canonical_rendered: str = ""
    robots_raw: str = ""
    robots_rendered: str = ""
    link_count_raw: int = 0
    link_count_rendered: int = 0
    main_text_overlap_pct: float = 100.0
    js_only_content: List[str] = Field(default_factory=list)
    is_heavily_js_dependent: bool = False
    render_discrepancy_summary: str = ""


class FindingCandidate(BaseModel):
    id: str
    check_id: str
    title: str
    description: str
    severity: Severity = Severity.MEDIUM
    raw_evidence: str = ""
    suggested_impact: int = 3  # 1-5 scale
    suggested_effort: int = 2  # 1-5 scale


class VerifiedFinding(BaseModel):
    id: str
    check_id: str
    title: str
    description: str
    severity: Severity
    verification_status: VerificationStatus
    evidence: str
    impact_score: int = Field(ge=1, le=5)  # 1 (lowest) to 5 (highest impact)
    effort_score: int = Field(ge=1, le=5)  # 1 (easiest) to 5 (hardest effort)
    priority_score: float = 0.0
    priority_formula: str = "Impact / Effort (Heuristic)"
    recommendation: str = ""


class QAQuestionResult(BaseModel):
    question_id: int
    question: str
    status: QAStatus
    answer: str
    evidence_quote: str = ""
    is_verified_substring: bool = False
    verification_notes: str = ""


class QATestResult(BaseModel):
    url: str
    questions: List[QAQuestionResult] = Field(default_factory=list)
    answered_count: int = 0
    vague_count: int = 0
    not_found_count: int = 0
    ai_readiness_score: float = 0.0  # Percentage 0-100


class SearchVisibilityResult(BaseModel):
    target_url: str
    query: str
    is_visible: bool = False
    position: Optional[int] = None
    serp_title: str = ""
    serp_snippet: str = ""
    title_issues: List[str] = Field(default_factory=list)
    snippet_issues: List[str] = Field(default_factory=list)
    visibility_status: str = "NOT_RANKING"  # RANKING_TOP_10, RANKING_LOWER, NOT_RANKING


class CompetitorGapItem(BaseModel):
    topic: str
    our_coverage: str
    competitor_coverage: str
    evidence_citation: str = ""


class CompetitorComparisonResult(BaseModel):
    target_url: str
    query: str
    competitors: List[str] = Field(default_factory=list)
    competitor_titles: Dict[str, str] = Field(default_factory=dict)
    competitor_qa: Dict[str, QATestResult] = Field(default_factory=dict)
    our_advantages: List[CompetitorGapItem] = Field(default_factory=list)
    competitor_advantages: List[CompetitorGapItem] = Field(default_factory=list)
    content_gap_summary: str = ""


class BenchmarkRow(BaseModel):
    tool_issue: str
    url: str
    agent_status: VerificationStatus
    evidence: str
    severity: Severity


class BenchmarkResult(BaseModel):
    source_tool: str
    total_issues: int = 0
    confirmed_count: int = 0
    unconfirmed_count: int = 0
    likely_false_positives: int = 0
    confirmed_precision_pct: float = 0.0
    items: List[BenchmarkRow] = Field(default_factory=list)


class AuditStepTrace(BaseModel):
    step_index: int
    decision: str
    tool_called: str
    summary: str
    duration_ms: float
    status: str = "DONE"


class AuditReport(BaseModel):
    url: str
    target_query: Optional[str] = None
    timestamp: str
    total_duration_ms: float
    tier_level_executed: int = 2
    steps: List[AuditStepTrace] = Field(default_factory=list)
    raw_fetch: Optional[RawFetchResult] = None
    rendered_fetch: Optional[RenderedFetchResult] = None
    diff: Optional[DiffResult] = None
    findings: List[VerifiedFinding] = Field(default_factory=list)
    qa_test: Optional[QATestResult] = None
    search_visibility: Optional[SearchVisibilityResult] = None
    competitor_comparison: Optional[CompetitorComparisonResult] = None
    benchmark: Optional[BenchmarkResult] = None
    monitor_created: Optional[Dict[str, Any]] = None
    browser_verification: Optional[Dict[str, Any]] = None
    usage_stats: Dict[str, Any] = Field(default_factory=dict)
