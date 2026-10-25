import pytest

from backend.app.content import detect_content
from backend.app.detection import detect_page
from backend.app.policy import assess_findings


@pytest.mark.parametrize('text,expected', [
    ('먹튀검증 | 구글검색 커뮤니티A | 검증 커뮤니티 안내', {'GAMBLING'}),
    ('야동 | 구글검색 서비스B | 전용관', {'ADULT_CONTENT'}),
    ('토토사이트 구글검색을 하지 마세요.', set()),
    ('야동 구글검색 금지 안내', set()),
    ('성인영상 구글검색 차단 방법 안내', set()),
    ('보도자료: 먹튀검증 구글검색 홍보 글을 적발했습니다.', set()),
    ('도박 예방교육: 토토사이트 구글검색 광고에 주의하세요.', set()),
    ('먹튀검증에 관한 안내입니다. 학교 구글검색 활용 교육.', set()),
    ('구글검색 활용 방법을 배우는 무료 교육 안내', set()),
])
def test_search_invitation_and_protective_boundaries(text, expected):
    page = {'url': 'https://synthetic.example.test', 'html': f'<p>{text}</p>'}
    assert {item['category'] for item in detect_content(page)} == expected


def test_plain_search_promotion_does_not_invent_a_required_technique():
    page = {'url': 'https://synthetic.example.test', 'html': '<p>먹튀검증 구글검색 커뮤니티A</p>'}
    features = detect_page(page)
    candidates = detect_content(page, feature_findings=features)
    assert len(candidates) == 1 and candidates[0]['techniques'] == []
    assert assess_findings(features, candidates) == []
