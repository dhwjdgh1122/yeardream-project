import json
import sqlite3
from contextlib import nullcontext
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .crawler import crawl_site
from .detection import detect_page
from .result import build_extra_result_json, build_result_json
from .models import AnalyzeRequest, AnalysisResponse, Finding, ReviewRequest, JobRequest
from .limits import AnalysisTimeout, Deadline
from .browser import BrowserRenderer, BrowserUnavailable
from .content import POLICY_VERSION, detect_content
from .policy import POLICY_VERSION as SUBMISSION_POLICY_VERSION, assess_findings
from .paths import output_root, resource_root, history_database_path
from .history import HistoryStore
from .coverage import build_coverage
from .jobs import AnalysisJobs, JobBusy

app = FastAPI(title="YearDream Illegal Ad Detection API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Local review records are only exposed to the bundled same-origin UI.
    allow_origins=[],
    allow_methods=["*"],
    allow_headers=["*"],
)

project_root = resource_root()
frontend_dir = project_root / "frontend" / "static"
result_path = output_root() / "result.json"
history_path = history_database_path()
analysis_lock = Lock()
jobs = AnalysisJobs()


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze(payload: AnalyzeRequest) -> AnalysisResponse:
    return guarded_analysis(payload)


def guarded_analysis(payload, control=None):
    if not analysis_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail='다른 분석이 실행 중입니다.')
    try:
        return run_analysis(payload, control)
    finally:
        analysis_lock.release()


def run_analysis(payload, control=None):
    try:
        started_at = datetime.now(timezone.utc).isoformat()
        deadline = Deadline.after(payload.total_timeout_sec, control.cancel_event if control else None)
        warnings = []
        findings: List[Finding] = []
        seen = set()
        raw_findings: List[Dict[str, Any]] = []
        content_candidates = []
        seen_content = set()

        analyzed = []
        processed = set()
        collected = failed = 0

        def consume(page):
            nonlocal collected, failed
            processed.add(id(page))
            if 'error' in page:
                failed += 1
                if control:
                    control.update(failed_documents=failed)
                return
            collected += 1
            if control:
                control.update(phase='analyzing', current_url=page['url'], collected_documents=collected)
            try:
                page_findings = detect_page(page, deadline=deadline)
                page_content = detect_content(page, feature_findings=page_findings, deadline=deadline)
                page_findings = assess_findings(page_findings, page_content, deadline=deadline)
            except AnalysisTimeout:
                return
            analyzed.append(page)
            if control:
                control.update(analyzed_documents=len(analyzed))
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
                    source_text=detected['source_text'],
                    submission_status=detected['submission_status'],
                    submission_reason=detected['submission_reason'],
                    submission_categories=detected['submission_categories'],
                )
                findings.append(finding)
                if detected['submission_status'] == 'included':
                    raw_findings.append(detected)
            return bool(page_content)

        rendering = (BrowserRenderer(deadline, payload.render_wait_ms)
                     if payload.collection_mode == 'browser' else nullcontext(None))
        with rendering as renderer:
            pages = crawl_site(payload.url, max_pages=payload.max_pages, max_depth=payload.max_depth,
                               deadline=deadline, renderer=renderer, prioritize_boards=payload.prioritize_boards,
                               on_document=consume, on_progress=control.update if control else None)
        # Also support callers/test collectors that return documents without callbacks.
        for page in pages:
            if id(page) not in processed:
                consume(page)
        successful_pages = [page for page in pages if 'error' not in page]
        timed_out = any(p.get('crawl_stop_reason') == 'total_timeout' for p in pages)
        if not analyzed:
            if deadline.cancelled:
                raise HTTPException(status_code=409, detail='분석을 중단했습니다. 완료한 문서가 없어 이전 결과를 유지합니다.')
            if timed_out or successful_pages:
                raise HTTPException(status_code=504, detail='분석 시간 제한에 도달했습니다.')
            raise HTTPException(status_code=502, detail='분석할 페이지를 수집하지 못했습니다.')
        if deadline.cancelled:
            warnings.append('사용자 요청으로 중단했습니다. 분석을 마친 문서의 결과만 반환합니다.')
        if len(analyzed) < len(successful_pages):
            warnings.append('중단 또는 시간 제한으로 수집한 문서 일부의 탐지를 완료하지 못했습니다.')
        for page in pages:
            warnings.extend(page.get('collection_warnings', []))
            if 'error' in page:
                warnings.append(f"수집 실패: {page['url']}")
            for omission in page.get('frame_omissions', []):
                warnings.append(f"iframe 분석 제외: {omission['location']} ({omission['reason']})")
            if any(item['reason'] == 'max_depth' for item in page.get('link_omissions', [])):
                warnings.append(f"링크 탐색 깊이 제한: {page['url']} (max_depth={payload.max_depth})")
            if any(item['reason'] == 'attachment' for item in page.get('link_omissions', [])):
                warnings.append(f"HTML 수집 대상이 아닌 첨부 링크 제외: {page['url']}")
            if page.get('crawl_truncated'):
                warnings.append('탐색이 중단돼 미분석 범위가 있습니다: ' + page.get('crawl_stop_reason', 'unknown'))
        if control:
            control.update(phase='saving', current_url='')

        finished_at = datetime.now(timezone.utc).isoformat()
        result_json = build_result_json(payload.url, raw_findings, started_at=started_at, finished_at=finished_at)
        result_extra_json = build_extra_result_json(result_json['meta'], content_candidates)
        result_path.write_text(json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")
        result_path.with_name('result_extra.json').write_text(
            json.dumps(result_extra_json, ensure_ascii=False, indent=2), encoding='utf-8')

        page_title = successful_pages[0].get("title")
        response = AnalysisResponse(
            coverage=build_coverage(pages, analyzed, max_pages=payload.max_pages,
                                    max_depth=payload.max_depth, timeout_sec=payload.total_timeout_sec,
                                    prioritize_boards=payload.prioritize_boards),
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
        if control:
            control.update(collected_documents=response.coverage['collected_documents'],
                           analyzed_documents=response.coverage['analyzed_documents'],
                           failed_documents=response.coverage['failed_documents'])
        try:
            response.analysis_id = HistoryStore(history_path).save(
                payload.model_dump(), response.model_dump(exclude={'analysis_id'}))
        except (OSError, sqlite3.Error):
            response.warnings.append('분석 이력을 저장하지 못했습니다. 현재 결과와 JSON 다운로드는 사용할 수 있습니다.')
        return response
    except HTTPException:
        raise
    except BrowserUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AnalysisTimeout as exc:
        if deadline.cancelled:
            raise HTTPException(status_code=409, detail='사용자가 중단했습니다. 완료한 문서가 없어 이전 결과를 유지합니다.') from exc
        raise HTTPException(status_code=504, detail="분석 시간 제한에 도달했습니다.") from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post('/api/jobs', status_code=202)
def start_job(payload: JobRequest):
    if analysis_lock.locked():
        raise HTTPException(status_code=409, detail='다른 분석이 실행 중입니다.')
    try:
        return {'id': jobs.start(payload, guarded_analysis)}
    except JobBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get('/api/jobs/{job_id}')
def job_status(job_id: str):
    try:
        return jobs.snapshot(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='작업이 없거나 앱 재시작/보관 한도로 만료됐습니다.') from exc


@app.post('/api/jobs/{job_id}/cancel')
def cancel_job(job_id: str):
    try:
        return jobs.cancel(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='작업을 찾을 수 없습니다.') from exc


def history_call(method, *args):
    try:
        return getattr(HistoryStore(history_path), method)(*args)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='이력 또는 후보를 찾을 수 없습니다.') from exc
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail='이력 저장소를 사용할 수 없습니다.') from exc


@app.get('/api/history')
def list_history(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    return history_call('list', limit, offset)


@app.get('/api/history/{analysis_id}')
def get_history(analysis_id: str):
    return history_call('get', analysis_id)


@app.post('/api/history/{analysis_id}/candidates/{candidate_id}/reviews')
def save_review(analysis_id: str, candidate_id: str, payload: ReviewRequest):
    record = payload.model_dump()
    for key in ('reviewer', 'reason'):
        record[key] = record[key].strip()
        if not record[key]:
            raise HTTPException(status_code=422, detail='검토자와 이유를 입력해 주세요.')
    return history_call('review', analysis_id, candidate_id, record)


@app.get('/history')
def serve_history() -> FileResponse:
    return FileResponse(frontend_dir / 'history.html')


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
