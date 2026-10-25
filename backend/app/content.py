"""Conservative promotional-context rules; candidates require human review."""

import re

from bs4 import BeautifulSoup, Comment, NavigableString

from .location import build_selector
from .textnorm import normalize_mapped
from .detection import HOMOGLYPH_PATTERN, JAMO_PATTERN
from .comparison import evaluation_url_key

POLICY_VERSION = 'content-rules-v5'
BLOCKS = {'body', 'main', 'article', 'section', 'aside', 'nav', 'header', 'footer',
          'div', 'p', 'li', 'td', 'th', 'blockquote', 'figcaption', 'pre',
          'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
EXCLUDED = {'head', 'script', 'style', 'template', 'noscript'}
RULES = {
    'GAMBLING': (
        re.compile(r'토토(?:사이트|커뮤니티|베팅|배팅)|카지노|꽁머니|먹튀검증|메이저사이트|온라인도박|슬롯(?:체험|게임)|casino|mega-?bet'),
        re.compile(r'신규가입|가입|보너스|첫충|바로가기|추천|홍보|환전|출금|고배당|구글검색|signup|bonus|join|(?:상담)?텔레그램@[a-z0-9_]+|상담텔레그램'),
    ),
    'ADULT_CONTENT': (
        re.compile(r'야동|성인(?:물|영상|사이트|방송)|음란(?:물|사이트)|19금(?:영상|사이트)'),
        re.compile(r'무료시청|시청|무료|바로가기|접속|가입|추천|다운로드|고화질|플랫폼|스트리밍|무제한|빠른주소|구글검색'),
    ),
}
PROTECTIVE = re.compile(
    r'예방교육|예방캠페인|피해예방|피해(?:상담|신고)|성교육|보도자료|검거|적발|수사결과|'
    r'(?:가입|접속|이용|시청|다운로드|검색).{0,18}(?:하지마|금지|주의|조심|위험)|'
    r'(?:도박|성인물|음란물|성폭력).{0,12}(?:예방|교육|근절)|차단(?:방법|안내)|'
    r'불법광고신고(?:안내|방법)|(?:광고|홍보).{0,8}(?:신고해|신고하|신고바|삭제요청)'
)
# A dot inside a domain or decimal is not a sentence boundary.
SENTENCE_END = re.compile(r'[.!?．](?=\s|$)|[。！？]')


def _promotional_contexts(text, topic_pattern, action_pattern, deadline):
    start = 0
    boundaries = [*SENTENCE_END.finditer(text), None]
    for boundary in boundaries:
        if deadline:
            deadline.check()
        end = boundary.start() if boundary else len(text)
        compact, positions = normalize_mapped(text[start:end], offset=start, deadline=deadline)
        for topic in topic_pattern.finditer(compact):
            if deadline:
                deadline.check()
            left, right = max(0, topic.start() - 45), min(len(compact), topic.end() + 100)
            window = compact[left:right]
            actions = list(action_pattern.finditer(window))
            if actions and not PROTECTIVE.search(window):
                spans = positions[topic.start():topic.end()]
                for action in actions:
                    spans += positions[left + action.start():left + action.end()]
                yield dict(topic=topic.group(), action=actions[0].group(), ranges=spans,
                           excerpt=text[positions[left][0]:positions[right - 1][1]])
        start = boundary.end() if boundary else end


def _text_units(soup, deadline, *, with_nodes=False):
    """Assign text to the nearest block, preserving inline fragments only."""
    groups = {}
    for node in soup.descendants:
        if deadline:
            deadline.check()
        if not isinstance(node, NavigableString) or isinstance(node, Comment):
            continue
        parents = list(node.parents)
        if any(parent.name in EXCLUDED for parent in parents):
            continue
        owner = next((parent for parent in parents if parent.name in BLOCKS), node.parent)
        if owner.name == '[document]':
            continue
        group = groups.setdefault(id(owner), (owner, [], []))
        group[1].append(str(node))
        group[2].append(node)
    return groups.values() if with_nodes else [(owner, parts) for owner, parts, _ in groups.values()]


def _overlaps(left, right, deadline):
    left, right = sorted(left), sorted(right)
    first = second = 0
    while first < len(left) and second < len(right):
        if deadline:
            deadline.check()
        a, b = left[first]
        c, d = right[second]
        if a < d and c < b:
            return True
        if b <= c:
            first += 1
        else:
            second += 1
    return False


def detect_content(page, *, feature_findings=(), deadline=None):
    if deadline:
        deadline.check()
    soup = BeautifulSoup(str(page.get('html', '')), 'html5lib')
    url = str(page.get('top_url') or page.get('url', ''))
    frame_path = list(page.get('frame_path', []))
    candidates = []
    features = []
    for feature in feature_findings:
        if deadline:
            deadline.check()
        if (feature['location'].split(' >>> ')[:-1] != frame_path
                or evaluation_url_key(feature['url']) != evaluation_url_key(url)):
            continue
        matches = soup.select(feature['selector'])
        if len(matches) != 1:
            raise ValueError('Content feature must identify one element')
        features.append((feature, matches[0]))
    for element, parts, nodes in _text_units(soup, deadline, with_nodes=True):
        if deadline:
            deadline.check()
        text = ''.join(parts)
        feature_ranges = []
        for feature, match in features:
            pattern = {'HOMOGLYPH': HOMOGLYPH_PATTERN, 'JAMO': JAMO_PATTERN}.get(feature['technique'])
            spans, offset = [], 0
            for node in nodes:
                if deadline:
                    deadline.check()
                raw = str(node)
                if node.parent is match:
                    if pattern:
                        spans.extend((offset + hit.start(), offset + hit.end()) for hit in pattern.finditer(raw))
                    else:
                        spans.extend((offset + hit.start(), offset + hit.end())
                                     for hit in re.finditer(r'[^\s\u200b-\u200d\ufeff]+', raw))
                offset += len(raw)
            if spans:
                feature_ranges.append((feature, spans))
        for category, (topic_pattern, action_pattern) in RULES.items():
            contexts = list(_promotional_contexts(text, topic_pattern, action_pattern, deadline))
            if contexts:
                if deadline:
                    deadline.check()
                selector = build_selector(element)
                links = []
                context = contexts[0]
                for feature, spans in feature_ranges:
                    if deadline:
                        deadline.check()
                    supported = next((item for item in contexts if _overlaps(spans, item['ranges'], deadline)), None)
                    if supported:
                        links.append(dict(location=feature['location'], technique=feature['technique']))
                        context = supported
                candidates.append({
                    'category': category, 'url': url, 'selector': selector,
                    'location': ' >>> '.join([*frame_path, selector]),
                    'evidence': f"홍보 내용 후보: {context['topic']} / {context['action']}. 문맥: {context['excerpt']}",
                    'source_text': ''.join(parts),
                    'matched_terms': [context['topic'], context['action']],
                    'techniques': sorted({item['technique'] for item in links}),
                    'feature_links': links, 'review_status': 'needs_review',
                    'policy_version': POLICY_VERSION,
                })
    if deadline:
        deadline.check()
    return candidates
