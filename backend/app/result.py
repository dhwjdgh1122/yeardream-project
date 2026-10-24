"""Map internal detector output to the team's result file format."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, StrictBool


class ResultMeta(BaseModel):
    topic: str = "illegal-ad-detection"
    entry_url: str = Field(min_length=1)
    started_at: str
    finished_at: str
    elapsed_sec: float = Field(ge=0)
    tool_version: str = "YearDream-0.1.0"


class ResultFinding(BaseModel):
    id: str = Field(min_length=1)
    url: str = Field(min_length=1)
    is_violation: StrictBool
    location: str = Field(min_length=1)
    evidence_text: str = Field(min_length=1)
    technique: Literal["HOMOGLYPH", "JAMO", "TRANSPARENT", "OFFSCREEN"]


class ResultDocument(BaseModel):
    meta: ResultMeta
    findings: list[ResultFinding]


def build_result_json(entry_url, findings, *, started_at=None, finished_at=None):
    finished = datetime.fromisoformat(finished_at) if finished_at else datetime.now(timezone.utc)
    started = datetime.fromisoformat(started_at) if started_at else finished
    if started.utcoffset() is None or finished.utcoffset() is None:
        raise ValueError("Result timestamps must include a timezone")

    converted = []
    seen = set()
    for finding in findings:
        key = (finding["url"], finding["location"], finding["technique"])
        if key in seen:
            continue
        seen.add(key)
        converted.append(ResultFinding(
            id=f"finding-{len(converted) + 1}",
            url=finding["url"],
            # Preserve the legacy contract until the analyst's verdict policy is defined.
            is_violation=finding.get("is_violation", True),
            location=finding["location"],
            evidence_text=finding["evidence"],
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
