"""Map internal output to the contest PDF's result tables/examples (pp.10–14)."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .comparison import evaluation_url_key


class StrictResultModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ResultMeta(StrictResultModel):
    topic: Literal['TOPIC'] = 'TOPIC'
    entry_url: str = Field(min_length=1)
    started_at: str
    finished_at: str
    elapsed_sec: float = Field(ge=0)
    tool_version: str = "YearDream-0.1.0"


class ResultFinding(StrictResultModel):
    id: str = Field(min_length=1)
    url: str = Field(min_length=1)
    is_violation: StrictBool
    location: str = Field(min_length=1)
    evidence_text: str = Field(min_length=1)
    technique: Literal["HOMOGLYPH", "JAMO", "TRANSPARENT", "OFFSCREEN"]


class ResultDocument(StrictResultModel):
    meta: ResultMeta
    findings: list[ResultFinding]


class ExtraFinding(StrictResultModel):
    id: str = Field(min_length=1)
    url: str = Field(min_length=1)
    location: str = Field(min_length=1)
    evidence_text: str = Field(min_length=1)
    technique: Literal['ETC'] = 'ETC'
    extra_finding: Literal['GAMBLING_PROMOTION_CANDIDATE', 'ADULT_CONTENT_PROMOTION_CANDIDATE']


class ExtraResultDocument(StrictResultModel):
    meta: ResultMeta
    findings: list[ExtraFinding]


def build_result_json(entry_url, findings, *, started_at=None, finished_at=None):
    finished = datetime.fromisoformat(finished_at) if finished_at else datetime.now(timezone.utc)
    started = datetime.fromisoformat(started_at) if started_at else finished
    if started.utcoffset() is None or finished.utcoffset() is None:
        raise ValueError("Result timestamps must include a timezone")

    converted = []
    seen = set()
    for finding in findings:
        if 'source_text' not in finding:
            raise ValueError('Submission findings require original source_text')
        if 'is_violation' not in finding:
            raise ValueError('Submission findings require an explicit is_violation Boolean')
        key = (evaluation_url_key(finding["url"]), finding["location"], finding["technique"])
        if key in seen:
            continue
        seen.add(key)
        converted.append(ResultFinding(
            id=f"finding-{len(converted) + 1}",
            url=finding["url"],
            is_violation=finding['is_violation'],
            location=finding["location"],
            evidence_text=finding['source_text'],
            technique=finding["technique"],
        ))

    return ResultDocument(
        meta=ResultMeta(
            entry_url=entry_url,
            started_at=started.isoformat(),
            finished_at=finished.isoformat(),
            elapsed_sec=(finished - started).total_seconds(),
        ),
        findings=converted,
    ).model_dump()


def build_extra_result_json(meta, candidates):
    """Export optional content candidates, not confirmed legal verdicts (PDF p.13)."""
    findings = []
    seen = set()
    for candidate in candidates:
        key = (evaluation_url_key(candidate['url']), candidate['location'], candidate['category'])
        if key in seen:
            continue
        seen.add(key)
        findings.append(ExtraFinding(
            id=f'extra-{len(findings) + 1}', url=candidate['url'], location=candidate['location'],
            evidence_text=candidate['source_text'],
            extra_finding=candidate['category'] + '_PROMOTION_CANDIDATE',
        ))
    return ExtraResultDocument(meta=ResultMeta.model_validate(meta), findings=findings).model_dump()
