import json

import pytest
from fastapi.testclient import TestClient

from backend.app import crawler, main
from backend.app.limits import AnalysisTimeout
from backend.app.textnorm import normalize_mapped


@pytest.mark.parametrize('text, expected', [
    ('ㅋㅏㅈㅣㄴㅗ', '카지노'), ('ㄷㅗㅂㅏㄱ', '도박'), ('ㅅㅓㅇㅇㅣㄴㅇㅕㅇㅅㅏㅇ', '성인영상'),
    ('카지노', '카지노'), ('카지노', '카지노'), ('ｍｅｇａ－ＢＥＴ', 'mega-bet'),
    ('cаsino', 'casino'), ('ㅋ ㅏ\u200bㅈㅣㄴㅗ', '카지노'),
])
def test_match_normalization_retains_original_ranges(text, expected):
    normalized, ranges = normalize_mapped(text)
    assert normalized == expected
    assert len(ranges) == len(normalized)
    assert ranges[0][0] == 0 and ranges[-1][1] == len(text)
    assert all(0 <= start < end <= len(text) for start, end in ranges)


def analyze_html(monkeypatch, tmp_path, html):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: (html, url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.test'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert json.loads((tmp_path / 'result.json').read_bytes()) == data['result_json']
    return data


@pytest.mark.parametrize('html, techniques', [
    ('<p id="ad" style="opacity:0">카지노 가입 보너스</p>', {'TRANSPARENT'}),
    ('<p id="ad" style="font-size:1px">카지노 가입 보너스</p>', {'OFFSCREEN'}),
    ('<p id="ad">ㅋㅏㅈㅣㄴㅗ 보너스</p>', {'JAMO'}),
    ('<p id="ad">ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ</p>', {'JAMO'}),
    ('<p id="ad">ｍｅｇａ－ＢＥＴ 첫충 30％ 지급</p>', {'HOMOGLYPH'}),
    ('<p id="ad">cаsino signup bonus</p>', {'HOMOGLYPH'}),
    ('<p id="ad">casіno signup bonus</p>', {'HOMOGLYPH'}),
    ('<p id="ad" style="opacity:0">먹튀검증 안전놀이터 상담 텔레그램 @promo_777</p>', {'TRANSPARENT'}),
    ('<p id="ad" style="position:absolute;left:-9999px">무료 슬롯 체험 바로가기</p>', {'OFFSCREEN'}),
    ('<p id="ad" style="opacity:0">ㅋㅏㅈㅣㄴㅗ 보너스</p>', {'JAMO', 'TRANSPARENT'}),
    ('<p><span id="ad" style="opacity:0">카지노</span> 가입 보너스</p>', {'TRANSPARENT'}),
    ('<p>카지노 <span id="ad" style="opacity:0">가입 보너스</span></p>', {'TRANSPARENT'}),
])
def test_supported_feature_promotions_are_submitted(monkeypatch, tmp_path, html, techniques):
    data = analyze_html(monkeypatch, tmp_path, html)
    submitted = data['result_json']['findings']
    assert {item['technique'] for item in submitted} == techniques
    assert all(item['is_violation'] is True for item in submitted)
    assert all(item['submission_status'] == 'included' for item in data['findings'])
    assert data['submission_policy_version'] == 'feature-content-policy-v1'
    assert all(item['evidence_text'] for item in submitted)


@pytest.mark.parametrize('html', [
    '<p>Привет, добро пожаловать</p>', '<p>ㅋ 정말 재미있다</p>',
    '<span style="opacity:0">메뉴 열기</span>',
    '<p style="font-size:1px">도박 예방교육: 카지노 가입 보너스 광고에 주의하세요.</p>',
    '<p style="opacity:0">성인영상 무료시청 광고를 신고해주세요.</p>',
    '<p style="opacity:0">먹튀검증 사칭 광고 피해상담 안내: 가입 보너스 광고를 신고하세요.</p>',
    '<p>카지노 가입 보너스. <span style="opacity:0">메뉴</span></p>',
    '<p>카지노 가입 보너스 안내 <span style="opacity:0">메뉴</span></p>',
    '<p>Ｗelcome 카지노 가입 보너스</p>', '<p>Привет 카지노 가입 보너스</p>',
    '<p><span style="opacity:0">Ｍenu</span> 카지노 가입 보너스</p>',
])
def test_unrelated_features_remain_reviewable_without_implicit_true(monkeypatch, tmp_path, html):
    data = analyze_html(monkeypatch, tmp_path, html)
    assert data['findings'], 'A feature must remain available for review'
    assert data['result_json']['findings'] == []
    assert all(item['submission_status'] == 'needs_review' for item in data['findings'])
    assert all(item['submission_reason'] for item in data['findings'])


def test_policy_timeout_preserves_both_files(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: ('<p style="opacity:0">카지노 가입 보너스</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    for name in ('result.json', 'result_extra.json'):
        (tmp_path / name).write_text('previous', encoding='utf-8')

    def expired(*args, **kwargs):
        raise AnalysisTimeout('Submission policy expired')
    monkeypatch.setattr(main, 'assess_findings', expired)
    with TestClient(main.app) as client:
        assert client.post('/api/analyze', json={'url': 'https://example.test'}).status_code == 504
    assert all((tmp_path / name).read_text(encoding='utf-8') == 'previous' for name in ('result.json', 'result_extra.json'))


def test_hidden_zero_width_between_jamo_does_not_become_ad_content(monkeypatch, tmp_path):
    data = analyze_html(monkeypatch, tmp_path,
                        '<p>ㅋ<span style="opacity:0">\u200b</span>ㅏㅈㅣㄴㅗ 보너스</p>')
    assert {item['technique'] for item in data['result_json']['findings']} == {'JAMO'}
    assert next(item for item in data['findings'] if item['technique'] == 'TRANSPARENT')['submission_status'] == 'needs_review'


def test_offline_assessments_are_separate_from_feature_accuracy(monkeypatch, tmp_path):
    from backend.app.evaluation import capture_site, evaluate_capture
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: (
        '<p style="opacity:0">메뉴 열기</p><p style="opacity:0">카지노 가입 보너스</p>', url))
    directory = tmp_path / 'capture'
    capture_site('https://example.test', directory)
    report = evaluate_capture(directory)
    assert report['prediction_count'] == 2
    assert report['submission_candidate_count'] == 1
    assert report['metrics'] is None
    assert report['metrics_purpose'] == 'four_technique_features_only'
    assert report['submission_policy_version'] == 'feature-content-policy-v1'


def test_two_promotion_categories_on_one_feature_remain_one_submission(monkeypatch, tmp_path):
    data = analyze_html(monkeypatch, tmp_path,
                        '<p style="opacity:0">카지노 가입 보너스. 성인영상 무료시청.</p>')
    assert len(data['result_json']['findings']) == 1
    assert len(data['result_extra_json']['findings']) == 2
    assert data['findings'][0]['submission_categories'] == ['ADULT_CONTENT', 'GAMBLING']
