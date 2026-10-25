from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="점검할 웹사이트 URL")
    collection_mode: Literal['static', 'browser'] = 'static'
    render_wait_ms: int = Field(default=500, ge=0, le=5000, description="동적 분석의 DOMContentLoaded 후 추가 대기(ms)")
    max_depth: int = Field(default=2, ge=0, le=20, description="시작 페이지가 0인 링크 탐색 깊이")
    total_timeout_sec: float = Field(default=60.0, gt=0, le=1800, allow_inf_nan=False,
                                     description="수집과 탐지가 공유하는 시간 예산(초)")


class Finding(BaseModel):
    technique: str
    selector: str
    location: str
    url: str
    evidence: str
    confidence: float = 0.0


class ContentCandidate(BaseModel):
    category: Literal['GAMBLING', 'ADULT_CONTENT']
    url: str
    selector: str
    location: str
    evidence: str
    matched_terms: List[str]
    techniques: List[str] = Field(default_factory=list)
    review_status: Literal['needs_review'] = 'needs_review'
    policy_version: str


class AnalysisResponse(BaseModel):
    url: str
    collection_mode: Literal['static', 'browser'] = 'static'
    page_title: Optional[str] = None
    crawled_pages: List[str]
    findings: List[Finding]
    content_candidates: List[ContentCandidate] = Field(default_factory=list)
    content_policy_version: str = 'content-rules-v1'
    result_json: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
