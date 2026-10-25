import pytest
from fastapi.testclient import TestClient

from backend.app import crawler, main
from backend.app.content import detect_content
from backend.app.detection import detect_page
from backend.app.limits import AnalysisTimeout


@pytest.mark.parametrize('text, category', [
    ('토토사이트 신규 가입 첫충 보너스 지급', 'GAMBLING'),
    ('카지노 추천 사이트 바로가기', 'GAMBLING'),
    ('먹튀검증 커뮤니티 홍보와 가입 혜택 안내', 'GAMBLING'),
    ('야동티비 고화질 무료 시청 플랫폼', 'ADULT_CONTENT'),
    ('성인영상 최신 콘텐츠 무료시청 바로가기', 'ADULT_CONTENT'),
    ('토 토 사 이 트 신규가입 보너스', 'GAMBLING'),
    ('ｶｼﾞﾉ 토토사이트 가\u200b입 보너스', 'GAMBLING'),
])
def test_promotional_context_is_detected(text, category):
    found = detect_content({'url': 'https://example.test', 'html': f'<p id="ad">{text}</p>'})
    assert len(found) == 1
    assert found[0]['category'] == category
    assert found[0]['location'] == 'p#ad'
    assert found[0]['review_status'] == 'needs_review'
    assert found[0]['matched_terms'] and found[0]['evidence']


@pytest.mark.parametrize('text', [
    '도박 예방교육: 토토사이트 가입 보너스 광고를 주의하세요.',
    '불법 도박사이트 신규가입 홍보 운영자를 경찰이 검거했습니다.',
    '성인영상 무료시청 사이트 차단 방법 안내',
    '보도자료: 야동사이트 무료시청 홍보 사건 수사 결과',
    '성인물 유포 예방교육 무료 강좌 신청',
    '청소년 도박 피해 예방 상담 신청 안내',
    '토토사이트와 카지노의 위험성을 배웠습니다.',
    '야동', '무료 회원가입 안내', '성인 대상 무료 교육 신청',
    '동화 주인공 토토의 모험: 무료 회원가입으로 감상하세요.',
])
def test_education_news_and_isolated_terms_are_not_candidates(text):
    assert detect_content({'url': 'https://example.test', 'html': f'<p>{text}</p>'}) == []


def test_inline_text_is_combined_but_unrelated_blocks_are_not():
    found = detect_content({'url': 'https://example.test', 'html':
        '<div><p><b>토토</b>사이트 <a>신규가입 보너스</a></p></div>'})
    assert len(found) == 1 and found[0]['selector'] == 'p'
    assert detect_content({'url': 'https://example.test', 'html':
        '<div><p>토토사이트</p><p>학교 무료 회원가입 안내</p></div>'}) == []
    assert detect_content({'url': 'https://example.test', 'html':
        '<script>토토사이트 가입 보너스</script><template>야동 무료 시청</template>'}) == []


def test_prevention_block_does_not_hide_a_separate_ad_and_features_are_linked():
    page = {'url': 'https://example.test/frame', 'top_url': 'https://example.test',
            'frame_path': ['iframe#outer'], 'html':
            '<p>도박 예방교육 안내</p><p id="ad" style="opacity:0">카지노 가입 보너스</p>'}
    findings = detect_page(page)
    found = detect_content(page, feature_findings=findings)
    assert len(found) == 1
    assert found[0]['techniques'] == ['TRANSPARENT']
    assert found[0]['location'] == 'iframe#outer >>> p#ad'
    assert found[0]['url'] == 'https://example.test'


def test_content_api_keeps_plain_ads_out_of_four_technique_json(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (
        '<p id="gamble">토토사이트 가입 보너스</p><p id="adult">야동 무료시청</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.test'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert {item['category'] for item in data['content_candidates']} == {'GAMBLING', 'ADULT_CONTENT'}
    assert data['findings'] == data['result_json']['findings'] == []
    assert all(item['review_status'] == 'needs_review' for item in data['content_candidates'])


def test_content_timeout_does_not_publish_half_a_page(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: ('<p style="opacity:0">카지노 가입 보너스</p>', url))

    def expired(*args, **kwargs):
        raise AnalysisTimeout('Content stage expired')

    monkeypatch.setattr(main, 'detect_content', expired)
    output = tmp_path / 'result.json'
    output.write_text('previous', encoding='utf-8')
    monkeypatch.setattr(main, 'result_path', output)
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.test'})
    assert response.status_code == 504
    assert output.read_text(encoding='utf-8') == 'previous'


def test_repeated_frame_content_candidates_stay_distinct(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (
        '<iframe src="/frame"></iframe><iframe src="/frame"></iframe>' if not url.endswith('/frame')
        else '<p style="opacity:0">카지노 가입 보너스</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.test'})
    data = response.json()
    assert len(data['content_candidates']) == len(data['findings']) == 2
    assert len({item['location'] for item in data['content_candidates']}) == 2
    assert all(item['techniques'] == ['TRANSPARENT'] for item in data['content_candidates'])


def test_only_features_in_the_same_text_block_are_associated():
    page = {'url': 'https://example.test', 'html':
            '<div>카지노 가입 보너스<p style="opacity:0">Normal note</p></div>'}
    found = detect_content(page, feature_findings=detect_page(page))
    assert len(found) == 1 and found[0]['techniques'] == []
    page['html'] = '<p>카지노 <span style="opacity:0">가입 보너스</span></p>'
    found = detect_content(page, feature_findings=detect_page(page))
    assert len(found) == 1 and found[0]['techniques'] == ['TRANSPARENT']
