import json
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .crawler import crawl_site
from .detection import detect_page
from .result import build_extra_result_json, build_result_json
from .models import AnalyzeRequest, AnalysisResponse, Finding
from .limits import AnalysisTimeout, Deadline
from .browser import BrowserRenderer, BrowserUnavailable
from .content import POLICY_VERSION, detect_content
from .policy import POLICY_VERSION as SUBMISSION_POLICY_VERSION, assess_findings

app = FastAPI(title="YearDream Illegal Ad Detection API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

project_root = Path(__file__).resolve().parents[2]
frontend_dir = project_root / "frontend" / "static"
result_path = project_root / "result.json"


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze(payload: AnalyzeRequest) -> AnalysisResponse:
    try:
        started_at = datetime.now(timezone.utc).isoformat()
        deadline = Deadline.after(payload.total_timeout_sec)
        rendering = (BrowserRenderer(deadline, payload.render_wait_ms)
                     if payload.collection_mode == 'browser' else nullcontext(None))
        with rendering as renderer:
            pages = crawl_site(payload.url, max_pages=8, max_depth=payload.max_depth,
                               deadline=deadline, renderer=renderer)
        crawl_timed_out = any(page.get("crawl_stop_reason") == "total_timeout" for page in pages)
        successful_pages = [page for page in pages if "error" not in page]
        if not successful_pages:
            if crawl_timed_out:
                raise HTTPException(status_code=504, detail="분석 시간 제한에 도달했습니다.")
            raise HTTPException(status_code=502, detail="분석할 페이지를 수집하지 못했습니다.")
        warnings = []
        for page in pages:
            warnings.extend(page.get('collection_warnings', []))
            if "error" in page:
                path = " >>> ".join(page.get("frame_path", []))
                warnings.append(f"수집 실패: {page['url']} ({path or 'page'})")
            for omission in page.get("frame_omissions", []):
                warnings.append(f"iframe 분석 제외: {omission['location']} ({omission['reason']})")
            if page.get("link_omissions"):
                warnings.append(f"링크 탐색 깊이 제한: {page['url']} (max_depth={payload.max_depth})")
            if page.get("crawl_truncated"):
                if page.get("crawl_stop_reason") == "total_timeout":
                    warnings.append("분석 시간 제한에 도달했습니다.")
                else:
                    warnings.append("탐색 한도에 도달해 일부 페이지 또는 iframe을 분석하지 못했습니다.")
        findings: List[Finding] = []
        seen = set()
        raw_findings: List[Dict[str, Any]] = []
        content_candidates = []
        seen_content = set()

        analyzed_pages = 0
        for page in successful_pages:
            try:
                page_findings = detect_page(page, deadline=deadline)
                page_content = detect_content(page, feature_findings=page_findings, deadline=deadline)
                page_findings = assess_findings(page_findings, page_content, deadline=deadline)
            except AnalysisTimeout:
                if not analyzed_pages:
                    raise HTTPException(status_code=504, detail="분석 시간 제한에 도달했습니다.")
                warnings.append("분석 시간 제한으로 나머지 페이지 분석을 중단했습니다.")
                break
            analyzed_pages += 1
            for candidate in page_content:
                key = (candidate['url'], candidate['location'], candidate['category'])
                if key not in seen_content:
                    seen_content.add(key)
                    content_candidates.append(candidate)
            for detected in page_findings:
                key = (detected["url"], detected["location"], detected["technique"])
                if key in seen:
                    continue
                seen.add(key)
                finding = Finding(
                    technique=detected["technique"],
                    selector=detected["selector"],
                    location=detected["location"],
                    url=detected["url"],
                    evidence=detected["evidence"],
                    confidence=float(detected["confidence"]),
                    submission_status=detected['submission_status'],
                    submission_reason=detected['submission_reason'],
                    submission_categories=detected['submission_categories'],
                )
                findings.append(finding)
                if detected['submission_status'] == 'included':
                    raw_findings.append(detected)

        finished_at = datetime.now(timezone.utc).isoformat()
        result_json = build_result_json(payload.url, raw_findings, started_at=started_at, finished_at=finished_at)
        result_extra_json = build_extra_result_json(result_json['meta'], content_candidates)
        result_path.write_text(json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")
        result_path.with_name('result_extra.json').write_text(
            json.dumps(result_extra_json, ensure_ascii=False, indent=2), encoding='utf-8')

        page_title = successful_pages[0].get("title")
        return AnalysisResponse(
            url=payload.url,
            collection_mode=payload.collection_mode,
            page_title=str(page_title) if page_title else None,
            crawled_pages=list(dict.fromkeys(str(page["url"]) for page in successful_pages)),
            findings=findings,
            content_candidates=content_candidates,
            content_policy_version=POLICY_VERSION,
            submission_policy_version=SUBMISSION_POLICY_VERSION,
            result_json=result_json,
            result_extra_json=result_extra_json,
            warnings=list(dict.fromkeys(warnings)),
        )
    except HTTPException:
        raise
    except BrowserUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AnalysisTimeout as exc:
        raise HTTPException(status_code=504, detail="분석 시간 제한에 도달했습니다.") from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
