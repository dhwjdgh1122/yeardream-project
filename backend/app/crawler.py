from collections import deque
from dataclasses import dataclass, replace
from typing import Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .location import build_selector
from .limits import AnalysisTimeout, Deadline

MAX_HTML_BYTES = 5 * 1024 * 1024


def extract_iframe_sources(html: str, page_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html5lib")
    source_urls: List[str] = []
    seen = set()

    for iframe in soup.find_all("iframe", src=True):
        raw_src = str(iframe.get("src", "")).strip()
        if not raw_src:
            continue
        absolute_url = urljoin(page_url, raw_src)
        if not same_domain(page_url, absolute_url):
            continue
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        source_urls.append(absolute_url)

    return source_urls


def normalize_url(raw_url: str) -> str:
    value = raw_url.strip()
    if not value:
        raise ValueError("URL is empty")
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must use HTTP or HTTPS and include a host")
    return urldefrag(value)[0]


def same_domain(base_url: str, target_url: str) -> bool:
    base_host = urlparse(base_url).netloc.lower()
    target_host = urlparse(target_url).netloc.lower()
    return base_host == target_host


def page_identity(url):
    parsed = urlparse(url)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    values = dict(pairs)
    if parsed.path.endswith('/xboard/board.php') and values.get('mode') == 'view' and values.get('number') and values.get('tbnum'):
        pairs = [(k, v) for k, v in pairs if k.lower() not in {'page', 'scat', 'keyset', 'searchword'}]
    return parsed._replace(query=urlencode(sorted(pairs)), fragment='').geturl()


def xboard_read_url(url):
    parsed = urlparse(url)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    values = dict(pairs)
    if (parsed.path.endswith('/xboard/board.php') and values.get('mode') == 'view'
            and values.get('mode1') == 'go' and values.get('number') and values.get('tbnum')):
        return parsed._replace(query=urlencode([(k, v) for k, v in pairs if k != 'mode1'])).geturl()
    return url


def link_priority(url, label=''):
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    path = parsed.path.lower()
    board = any(word in path for word in ('board', '/bbs', '/forum', '/post'))
    if board and any(word in label for word in ('자유', '참여', '소통', '열린', '의견')):
        return 0
    if board and (query.get('mode') == 'view' or any(k in query for k in ('nttId', 'postSeq', 'articleNo'))):
        return 1
    if board:
        try:
            page = int(query.get('page', query.get('pageIndex', '1')))
        except ValueError:
            page = 1
        return 0 if page <= 1 else 2
    return 10


def attachment_link(url):
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query))
    return query.get('mode', '').lower() in {'downpost', 'download'} or parsed.path.lower().endswith(
        ('.pdf', '.zip', '.hwp', '.hwpx', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
         '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3', '.exe'))


def non_readonly_link(url):
    parsed = urlparse(url)
    actions = {'write', 'modify', 'edit', 'delete', 'remove', 'reply', 'insert', 'update', 'save', 'logout'}
    if any(value.lower() in actions for key, value in parse_qsl(parsed.query)
           if key.lower() in {'mode', 'action', 'act', 'cmd', 'do'}):
        return True
    return any(part.split('.')[0].lower() in actions for part in parsed.path.split('/'))


def fetch_html(url: str, *, timeout_sec: float = 10.0, deadline: Deadline | None = None) -> Tuple[str, str]:
    headers = {"User-Agent": "Mozilla/5.0"}
    timeout = min(timeout_sec, deadline.remaining()) if deadline else timeout_sec
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            media_type = response.headers.get('content-type', '').split(';')[0].strip().lower()
            if media_type and media_type not in {'text/html', 'application/xhtml+xml'}:
                raise ValueError(f'HTML 문서가 아닌 응답 제외: {media_type}')
            if response.headers.get('content-disposition', '').lower().startswith('attachment'):
                raise ValueError('첨부파일 응답은 HTML 수집에서 제외합니다.')
            try:
                content_length = int(response.headers.get('content-length', '0'))
            except ValueError:
                content_length = 0
            if content_length > MAX_HTML_BYTES:
                raise ValueError('HTML 수집 크기 한도(5 MiB)를 초과한 응답입니다.')
            chunks = []
            total_bytes = 0
            for chunk in response.iter_bytes():
                if deadline:
                    deadline.check()
                total_bytes += len(chunk)
                if total_bytes > MAX_HTML_BYTES:
                    raise ValueError('HTML 수집 크기 한도(5 MiB)를 초과한 응답입니다.')
                if not chunks and chunk.startswith((b'%PDF-', b'PK\x03\x04', b'\x89PNG', b'\xff\xd8\xff')):
                    raise ValueError('HTML이 아닌 파일 응답은 제외합니다.')
                chunks.append(chunk)
            if deadline:
                deadline.check()
            # iter_bytes already decompresses the body; retain only encoding headers.
            decoded = httpx.Response(200, content=b"".join(chunks), headers={
                "Content-Type": response.headers.get("Content-Type", ""),
            })
            return decoded.text, str(response.url)


@dataclass(frozen=True)
class _CrawlTask:
    url: str
    top_url: str = ""
    frame_path: tuple = ()
    ancestor_urls: tuple = ()
    inline_html: str | None = None
    parent_url: str = ""
    depth: int = 0
    browser_frame: object | None = None
    priority: int = 10
    source_link: str | None = None


def crawl_site(seed_url: str, max_pages: int = 10, max_iframe_depth: int = 3,
               max_depth: int = 2, total_timeout_sec: float = 60.0,
               *, deadline: Deadline | None = None, renderer=None, prioritize_boards=False,
               on_document=None, on_progress=None) -> List[Dict[str, object]]:
    """Collect bounded document contexts, retaining each iframe insertion path.

    max_pages limits contexts (including failures), not just unique fetches.
    Responses are cached per URL so repeated frames need not be downloaded twice.
    """
    if max_pages < 1 or max_iframe_depth < 0 or max_depth < 0 or total_timeout_sec <= 0:
        raise ValueError("Invalid crawl limits")
    deadline = deadline or Deadline.after(total_timeout_sec)
    base_url = normalize_url(seed_url)
    if non_readonly_link(base_url):
        raise ValueError('작성·수정·삭제 등 작업 URL은 자동 수집 대상이 아닙니다.')
    queue = deque([_CrawlTask(base_url)])
    identity = page_identity if prioritize_boards else lambda url: url
    scheduled_pages = {identity(base_url): 0}
    visited_pages = {}
    cache = {}
    result: List[Dict[str, object]] = []
    active_task = None

    def pending_contexts():
        return [dict(url=item.url, parent_url=item.parent_url or None,
                     frame_path=list(item.frame_path), depth=item.depth) for item in queue]

    def stop_for_timeout():
        reason = 'user_cancelled' if deadline.cancelled else 'total_timeout'
        message = '사용자 요청으로 수집을 중단했습니다.' if deadline.cancelled else '수집 또는 전처리 중 시간 예산에 도달했습니다.'
        if result and active_task is not None:
            result[-1]['interrupted_context'] = dict(
                url=active_task.url, requested_url=active_task.url,
                parent_url=active_task.parent_url or None, depth=active_task.depth,
                frame_path=list(active_task.frame_path),
                error=message)
        if not result:
            result.append({"url": base_url, "error": "분석 시간 제한에 도달했습니다."})
        result[-1]["crawl_truncated"] = True
        result[-1]["crawl_stop_reason"] = reason
        result[-1]['pending_contexts'] = pending_contexts()

    def allowed_url(raw, parent):
        absolute = urldefrag(urljoin(parent, raw))[0]
        if urlparse(absolute).scheme in {"http", "https"} and same_domain(base_url, absolute):
            return absolute
        return None

    while queue and len(result) < max_pages:
        try:
            deadline.check()
        except AnalysisTimeout:
            stop_for_timeout()
            return result
        if prioritize_boards and not queue[0].frame_path:
            index = min(range(len(queue)), key=lambda i: queue[i].priority)
            queue.rotate(-index)
            task = queue.popleft()
            queue.rotate(index)
        else:
            task = queue.popleft()
        if not task.frame_path and (task.depth > scheduled_pages.get(identity(task.url), task.depth)
                                    or visited_pages.get(identity(task.url), float('inf')) <= task.depth):
            continue
        active_task = task
        if on_progress:
            on_progress(phase='collecting', current_url=task.url, pending_documents=len(queue))
        if renderer is not None:
            try:
                document = (renderer.snapshot(task.browser_frame, task.url)
                            if task.browser_frame is not None else renderer.fetch(task.url))
                deadline.check()
                document['url'] = urldefrag(str(document['url']))[0]
                if not allowed_url(document['url'], task.url):
                    raise ValueError('Redirect target is outside the allowed crawl scope')
            except AnalysisTimeout:
                stop_for_timeout()
                return result
            except Exception as exc:
                try:
                    deadline.check()
                except AnalysisTimeout:
                    stop_for_timeout()
                    return result
                document = {'url': task.url, 'error': str(exc)}
        elif task.inline_html is not None:
            document = {"html": task.inline_html, "url": task.url}
        else:
            if task.url not in cache:
                try:
                    html, final_url = fetch_html(task.url, deadline=deadline)
                    deadline.check()
                    final_url = urldefrag(str(final_url))[0]
                    if not allowed_url(final_url, task.url):
                        raise ValueError("Redirect target is outside the allowed crawl scope")
                    document = {"html": html, "url": final_url}
                    cache[final_url] = document
                except AnalysisTimeout:
                    stop_for_timeout()
                    return result
                except Exception as exc:
                    try:
                        deadline.check()
                    except AnalysisTimeout:
                        stop_for_timeout()
                        return result
                    document = {"url": task.url, "error": str(exc)}
                cache[task.url] = document
            document = cache[task.url]

        final_url = document["url"]
        top_url = task.top_url or final_url
        context = {
            "url": final_url,
            "requested_url": task.url,
            "source_link": task.source_link,
            "top_url": top_url,
            "frame_path": list(task.frame_path),
            "page_type": "iframe" if task.frame_path else "page",
            "parent_url": task.parent_url or None,
            "depth": task.depth,
        }
        if "error" in document:
            result.append({**context, "error": document["error"]})
            active_task = None
            if on_document:
                on_document(result[-1])
            continue
        if not task.frame_path:
            if visited_pages.get(identity(final_url), float('inf')) <= task.depth:
                active_task = None
                continue
            visited_pages[identity(final_url)] = task.depth
        html = document["html"]
        soup = BeautifulSoup(html, "html5lib")
        links = []
        link_omissions = []
        for anchor in soup.find_all("a", href=True):
            try:
                deadline.check()
            except AnalysisTimeout:
                stop_for_timeout()
                return result
            absolute_url = allowed_url(str(anchor["href"]), final_url)
            if not absolute_url:
                continue
            source_link = absolute_url
            if prioritize_boards:
                absolute_url = xboard_read_url(absolute_url)
                if source_link != absolute_url:
                    if source_link not in links:
                        links.append(source_link)
                    link_omissions.append({'url': source_link, 'reason': 'redirect_link', 'read_url': absolute_url})
            if absolute_url not in links:
                links.append(absolute_url)
            if non_readonly_link(absolute_url):
                link_omissions.append({'url': absolute_url, 'reason': 'non_readonly'})
                continue
            if attachment_link(absolute_url):
                link_omissions.append({'url': absolute_url, 'reason': 'attachment'})
                continue
            if task.depth + 1 < scheduled_pages.get(identity(absolute_url), float('inf')):
                if task.depth >= max_depth:
                    link_omissions.append({"url": absolute_url, "reason": "max_depth"})
                    continue
                scheduled_pages[identity(absolute_url)] = task.depth + 1
                label = anchor.get_text(' ', strip=True) or str(anchor.get('aria-label') or anchor.get('title') or '')
                if not label:
                    label = ' '.join(str(img.get('alt', '')) for img in anchor.find_all('img'))
                queue.append(_CrawlTask(absolute_url, parent_url=final_url, depth=task.depth + 1,
                                       priority=link_priority(absolute_url, label), source_link=source_link))

        iframe_sources = []
        frame_omissions = []
        for iframe in soup.find_all("iframe"):
            try:
                deadline.check()
            except AnalysisTimeout:
                stop_for_timeout()
                return result
            selector = build_selector(iframe)
            frame_path = (*task.frame_path, selector)
            if len(frame_path) > max_iframe_depth:
                frame_omissions.append({"location": " >>> ".join(frame_path), "reason": "max_iframe_depth"})
                continue
            if renderer is not None:
                try:
                    child = renderer.child_frame(document['browser_frame'], selector)
                    if child is None:
                        frame_omissions.append({'location': ' >>> '.join(frame_path), 'reason': 'frame_unavailable'})
                        continue
                    child_url = renderer.frame_url(child)
                    raw_src = str(iframe.get('src', '')).strip()
                    if child_url == 'about:blank' and (iframe.has_attr('srcdoc') or raw_src not in {'', 'about:blank'}):
                        frame_omissions.append({'location': ' >>> '.join(frame_path), 'reason': 'frame_not_loaded'})
                        continue
                    if child_url in {'about:blank', 'about:srcdoc'}:
                        # Embedded runtime documents use their parent's URL as the link base.
                        iframe_url = final_url
                    else:
                        iframe_url = allowed_url(child_url, final_url)
                    if iframe_url is None:
                        frame_omissions.append({'location': ' >>> '.join(frame_path), 'reason': 'unsupported_or_external_src'})
                        continue
                    iframe_sources.append(iframe_url)
                    queue.appendleft(_CrawlTask(iframe_url, top_url, frame_path,
                                               parent_url=final_url, depth=task.depth,
                                               browser_frame=child))
                except AnalysisTimeout:
                    stop_for_timeout()
                    return result
                except Exception:
                    frame_omissions.append({'location': ' >>> '.join(frame_path), 'reason': 'frame_unavailable'})
                continue
            if iframe.has_attr("srcdoc"):
                queue.appendleft(_CrawlTask(final_url, top_url, frame_path,
                                           task.ancestor_urls, str(iframe["srcdoc"]), final_url,
                                           task.depth))
                continue
            raw_src = str(iframe.get("src", "")).strip()
            iframe_url = allowed_url(raw_src, final_url) if raw_src else None
            if not iframe_url:
                frame_omissions.append({"location": " >>> ".join(frame_path), "reason": "unsupported_or_external_src"})
                continue
            iframe_sources.append(iframe_url)
            if iframe_url in (*task.ancestor_urls, final_url):
                frame_omissions.append({"location": " >>> ".join(frame_path), "reason": "frame_cycle"})
                continue
            queue.appendleft(_CrawlTask(iframe_url, top_url, frame_path,
                                       (*task.ancestor_urls, final_url), parent_url=final_url,
                                       depth=task.depth))

        result.append(
            {
                **context,
                "title": soup.title.get_text(strip=True) if soup.title else "",
                "links": links,
                "link_omissions": link_omissions,
                "iframe_sources": iframe_sources,
                "frame_omissions": frame_omissions,
                "html": html,
                "text": " ".join(soup.stripped_strings)[:2500],
                "collection_warnings": document.get('collection_warnings', []),
                **({'rendered_style': document['rendered_style']} if 'rendered_style' in document else {}),
            }
        )
        active_task = None
        if on_progress:
            on_progress(pending_documents=len(queue))
        if on_document:
            relevant = on_document(result[-1])
            if prioritize_boards and relevant:
                # Prefer children of an observed promotion context, preserving live iframe order.
                queue = deque(replace(item, priority=item.priority - 2)
                              if item.parent_url == final_url and not item.frame_path else item
                              for item in queue)

    if queue and result:
        result[-1]["crawl_truncated"] = True
        result[-1]["crawl_stop_reason"] = "max_pages"
        result[-1]['pending_contexts'] = pending_contexts()
    try:
        deadline.check()
    except AnalysisTimeout:
        stop_for_timeout()
    return result
