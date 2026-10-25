"""Describe observed crawl/detection coverage without claiming website completeness."""


def build_coverage(pages, analyzed, *, max_pages, max_depth, timeout_sec, prioritize_boards=False):
    from .crawler import page_identity
    identity = page_identity if prioritize_boards else lambda url: url
    pages = [*pages, *(p['interrupted_context'] for p in pages if p.get('interrupted_context'))]
    analyzed_ids = {id(page) for page in analyzed}
    documents = []
    visited = set()
    discovered = {}
    frames = []
    stop_reasons = list(dict.fromkeys(
        p['crawl_stop_reason'] for p in pages if p.get('crawl_stop_reason')))
    for page in pages:
        if not page.get('frame_path'):
            visited.update([identity(page['url']), identity(page.get('requested_url', page['url']))])
        collected = 'error' not in page
        documents.append(dict(
            url=page['url'], requested_url=page.get('requested_url', page['url']),
            source_link=page.get('source_link'),
            parent_url=page.get('parent_url'), depth=page.get('depth', 0),
            frame_path=page.get('frame_path', []),
            status=('collection_failed' if not collected else
                    'analyzed' if id(page) in analyzed_ids else 'not_analyzed'),
            reason=page.get('error', ''),
        ))
        for url in page.get('links', []):
            discovered.setdefault(url, dict(url=url, source_url=page['url'], reason='not_collected'))
        for item in page.get('link_omissions', []):
            discovered.setdefault(item['url'], dict(url=item['url'], source_url=page['url'],
                                                   reason=item['reason']))
            if discovered[item['url']]['reason'] == 'not_collected':
                discovered[item['url']]['reason'] = item['reason']
        for item in page.get('frame_omissions', []):
            frames.append(dict(source_url=page['url'], location=item['location'], reason=item['reason']))

    for page in pages:
        for item in page.get('pending_contexts', []):
            reason = page.get('crawl_stop_reason', 'not_collected')
            if item['frame_path']:
                frames.append(dict(source_url=item.get('parent_url') or item['url'],
                                   location=' >>> '.join(item['frame_path']), reason=reason))
            else:
                discovered[item['url']] = dict(url=item['url'],
                                              source_url=item.get('parent_url'), reason=reason)

    unvisited = []
    unvisited_keys = set()
    for url, item in discovered.items():
        if identity(url) in visited or identity(url) in unvisited_keys:
            continue
        unvisited_keys.add(identity(url))
        if item['reason'] == 'not_collected' and stop_reasons:
            item['reason'] = stop_reasons[-1]
        unvisited.append(item)
    # A URL can be known but unavailable as a live iframe document; retain its location.
    return dict(
        scope='observed_documents_only', website_complete=False,
        limits=dict(max_documents=max_pages, max_depth=max_depth, total_timeout_sec=timeout_sec,
                    max_iframe_depth=3),
        attempted_documents=len(documents),
        collected_documents=sum(d['status'] != 'collection_failed' for d in documents),
        analyzed_documents=sum(d['status'] == 'analyzed' for d in documents),
        failed_documents=sum(d['status'] == 'collection_failed' for d in documents),
        unvisited_known_urls=len(unvisited), stop_reasons=stop_reasons,
        documents=documents, unvisited_links=unvisited, excluded_frames=frames,
    )
