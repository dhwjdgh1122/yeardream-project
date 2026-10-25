import pytest
from fastapi.testclient import TestClient

from backend.app import crawler, main
from backend.app.detection import detect_page
from backend.app.textnorm import normalize_mapped


@pytest.mark.parametrize('text', [
    'ㅋㅋ', 'ㅎㅎ', 'ㅋㅋㅎㅎ', 'ㅋㅎㅋ', '정말 재미있다ㅋㅋ!', 'ㅎㅎ 반갑습니다',
    '비 오는 날 구글 직원인 줄 알려나? ㅋㅋ', '카지노 가입 보너스 ㅋㅋ',
])
def test_contiguous_laughter_is_not_a_jamo_feature(text):
    assert detect_page({'url': 'https://example.test', 'html': f'<p>{text}</p>'}) == []


@pytest.mark.parametrize('text', ['ㅋ', 'ㅎ', 'ㄱㄴㄷ', 'ㅋㅏㅈㅣㄴㅗ', 'ㅎㅎㅏ', '카지노', 'ㅋㅋ ㄱ'])
def test_other_jamo_is_not_blanket_suppressed(text):
    findings = detect_page({'url': 'https://example.test', 'html': f'<p>{text}</p>'})
    assert {item['technique'] for item in findings} == {'JAMO'}
    assert findings[0]['source_text'] == text


def test_laughter_does_not_suppress_css_or_split_inline_promotion(monkeypatch, tmp_path):
    html = '<p style="opacity:0">ㅋㅋ</p><p><span>ㅋ</span>ㅏㅈㅣㄴㅗ 보너스 ㅎㅎ</p>'
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (html, url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        data = client.post('/api/analyze', json={'url': 'https://example.test'}).json()
        schema = client.get('/openapi.json').json()
    assert {item['technique'] for item in data['result_json']['findings']} == {'JAMO'}
    assert any(item['technique'] == 'TRANSPARENT' and item['source_text'] == 'ㅋㅋ' for item in data['findings'])
    assert all('confidence' not in item for item in data['findings'])
    assert 'confidence' not in schema['components']['schemas']['Finding']['properties']
    assert any('ㅋ' in item['evidence_text'] for item in data['result_json']['findings'])


@pytest.mark.parametrize('text', ['ㅋㅏㅈㅣㄴㅗ 보너스ㅎㅎ', 'ㅋㅏㅈㅣㄴㅗ 가입ㅋㅋ', 'ㅋㅋㅋㅏㅈㅣㄴㅗ 보너스'])
def test_laughter_does_not_hide_advertising_and_ranges_remain_original(text):
    from backend.app.content import detect_content
    page = {'url': 'https://example.test', 'html': f'<p>{text}</p>'}
    findings = detect_page(page)
    candidates = detect_content(page, feature_findings=findings)
    assert {item['category'] for item in candidates} == {'GAMBLING'}
    assert candidates[0]['techniques'] == ['JAMO']
    assert findings[0]['source_text'] == text
    normalized, ranges = normalize_mapped(text)
    assert len(normalized) == len(ranges)
    assert all(0 <= start < end <= len(text) for start, end in ranges)
    assert ranges[-1][1] == len(text)
