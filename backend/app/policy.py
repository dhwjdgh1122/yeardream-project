"""Explicit submission selection from attributed promotional evidence, not legal adjudication."""
from .comparison import evaluation_url_key

POLICY_VERSION = 'feature-content-policy-v1'


def assess_findings(findings, candidates, *, deadline=None):
    supported = {}
    for candidate in candidates:
        if deadline:
            deadline.check()
        for link in candidate.get('feature_links', []):
            key = (evaluation_url_key(candidate['url']), link['location'], link['technique'])
            supported.setdefault(key, set()).add(candidate['category'])
    assessed = []
    for finding in findings:
        if deadline:
            deadline.check()
        key = (evaluation_url_key(finding['url']), finding['location'], finding['technique'])
        categories = sorted(supported.get(key, set()))
        included = bool(categories)
        item = {**finding, 'submission_status': 'included' if included else 'needs_review',
                'submission_categories': categories,
                'submission_reason': ('위장·은닉 구간이 홍보 주제 또는 이용 유도 표현과 겹침: ' + ', '.join(categories)
                                      if included else '관련 홍보 근거가 부족해 검토 필요. 정상 판정은 아님.'),
                'submission_policy_version': POLICY_VERSION}
        # Unknown findings do not acquire either a true or false legal verdict.
        item.pop('is_violation', None)
        if included:
            item['is_violation'] = True
        assessed.append(item)
    return assessed
