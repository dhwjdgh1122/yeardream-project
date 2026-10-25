"""Conservative promotional-context rules; candidates require human review."""

import re
import unicodedata

from bs4 import BeautifulSoup, Comment, NavigableString

from .location import build_selector

POLICY_VERSION = 'content-rules-v1'
BLOCKS = {'body', 'main', 'article', 'section', 'aside', 'nav', 'header', 'footer',
          'div', 'p', 'li', 'td', 'th', 'blockquote', 'figcaption', 'pre',
          'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
EXCLUDED = {'head', 'script', 'style', 'template', 'noscript'}
RULES = {
    'GAMBLING': (
        re.compile(r'토토(?:사이트|커뮤니티|베팅|배팅)|카지노|꽁머니|먹튀검증|메이저사이트|온라인도박'),
        re.compile(r'신규가입|가입|보너스|첫충|바로가기|추천|홍보|환전|출금|고배당'),
    ),
    'ADULT_CONTENT': (
        re.compile(r'야동|성인(?:물|영상|사이트|방송)|음란(?:물|사이트)|19금(?:영상|사이트)'),
        re.compile(r'무료시청|시청|무료|바로가기|접속|가입|추천|다운로드|고화질|플랫폼|스트리밍|무제한|빠른주소'),
    ),
}
PROTECTIVE = re.compile(
    r'예방교육|예방캠페인|피해예방|성교육|보도자료|검거|적발|수사결과|'
    r'(?:가입|접속|이용|시청|다운로드).{0,18}(?:하지마|금지|주의|조심|위험)|'
    r'(?:도박|성인물|음란물|성폭력).{0,12}(?:예방|교육|근절)|차단(?:방법|안내)'
)


def _text_units(soup, deadline):
    """Assign text to the nearest block, preserving inline fragments only."""
    groups = {}
    for node in soup.descendants:
        if deadline:
            deadline.check()
        if not isinstance(node, NavigableString) or isinstance(node, Comment) or not node.strip():
            continue
        parents = list(node.parents)
        if any(parent.name in EXCLUDED for parent in parents):
            continue
        owner = next((parent for parent in parents if parent.name in BLOCKS), node.parent)
        if owner.name == '[document]':
            continue
        group = groups.setdefault(id(owner), (owner, []))
        group[1].append(str(node))
    return groups.values()


def detect_content(page, *, feature_findings=(), deadline=None):
    if deadline:
        deadline.check()
    soup = BeautifulSoup(str(page.get('html', '')), 'html5lib')
    url = str(page.get('top_url') or page.get('url', ''))
    frame_path = list(page.get('frame_path', []))
    candidates = []
    for element, parts in _text_units(soup, deadline):
        if deadline:
            deadline.check()
        text = unicodedata.normalize('NFKC', ' '.join(parts))
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        text = ' '.join(text.split())
        positions = [index for index, char in enumerate(text) if not char.isspace()]
        compact = ''.join(text[index] for index in positions)
        for category, (topic_pattern, action_pattern) in RULES.items():
            for topic in topic_pattern.finditer(compact):
                if deadline:
                    deadline.check()
                start, end = max(0, topic.start() - 45), min(len(compact), topic.end() + 100)
                window = compact[start:end]
                action = action_pattern.search(window)
                if action is None or PROTECTIVE.search(window):
                    continue
                selector = build_selector(element)
                techniques = set()
                for feature in feature_findings:
                    if deadline:
                        deadline.check()
                    if feature['location'].split(' >>> ')[:-1] != frame_path:
                        continue
                    for match in soup.select(feature['selector']):
                        owner = next((node for node in [match, *match.parents] if node.name in BLOCKS), match)
                        if owner is element:
                            techniques.add(feature['technique'])
                excerpt = text[positions[start]:positions[end - 1] + 1]
                candidates.append({
                    'category': category, 'url': url, 'selector': selector,
                    'location': ' >>> '.join([*frame_path, selector]),
                    'evidence': f'홍보 내용 후보: {topic.group()} / {action.group()}. 문맥: {excerpt}',
                    'matched_terms': [topic.group(), action.group()],
                    'techniques': sorted(techniques), 'review_status': 'needs_review',
                    'policy_version': POLICY_VERSION,
                })
                break
    if deadline:
        deadline.check()
    return candidates
