from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .location import build_selector
from .limits import AnalysisTimeout, Deadline


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


def fetch_html(url: str, *, timeout_sec: float = 10.0, deadline: Deadline | None = None) -> Tuple[str, str]:
    headers = {"User-Agent": "Mozilla/5.0"}
    timeout = min(timeout_sec, deadline.remaining()) if deadline else timeout_sec
    with httpx.Client(follow_redirects=True, timeout=timeout) as client:
        with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()
            chunks = []
            for chunk in response.iter_bytes():
                if deadline:
                    deadline.check()
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


def crawl_site(seed_url: str, max_pages: int = 10, max_iframe_depth: int = 3,
               max_depth: int = 2, total_timeout_sec: float = 60.0,
               *, deadline: Deadline | None = None) -> List[Dict[str, object]]:
    """Collect bounded document contexts, retaining each iframe insertion path.

    max_pages limits contexts (including failures), not just unique fetches.
    Responses are cached per URL so repeated frames need not be downloaded twice.
    """
    if max_pages < 1 or max_iframe_depth < 0 or max_depth < 0 or total_timeout_sec <= 0:
        raise ValueError("Invalid crawl limits")
    deadline = deadline or Deadline.after(total_timeout_sec)
    base_url = normalize_url(seed_url)
    queue = deque([_CrawlTask(base_url)])
    scheduled_pages = {base_url}
    visited_pages = set()
    cache = {}
    result: List[Dict[str, object]] = []

    def stop_for_timeout():
        if not result:
            result.append({"url": base_url, "error": "분석 시간 제한에 도달했습니다."})
        result[-1]["crawl_truncated"] = True
        result[-1]["crawl_stop_reason"] = "total_timeout"

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
        task = queue.popleft()
        if task.inline_html is not None:
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
            "top_url": top_url,
            "frame_path": list(task.frame_path),
            "page_type": "iframe" if task.frame_path else "page",
            "parent_url": task.parent_url or None,
            "depth": task.depth,
        }
        if "error" in document:
            result.append({**context, "error": document["error"]})
            continue
        if not task.frame_path:
            if final_url in visited_pages:
                continue
            visited_pages.add(final_url)
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
            if absolute_url not in links:
                links.append(absolute_url)
            if absolute_url not in scheduled_pages:
                if task.depth >= max_depth:
                    link_omissions.append({"url": absolute_url, "reason": "max_depth"})
                    continue
                scheduled_pages.add(absolute_url)
                queue.append(_CrawlTask(absolute_url, parent_url=final_url, depth=task.depth + 1))

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
            }
        )

    if queue and result:
        result[-1]["crawl_truncated"] = True
        result[-1]["crawl_stop_reason"] = "max_pages"
    try:
        deadline.check()
    except AnalysisTimeout:
        stop_for_timeout()
    return result
