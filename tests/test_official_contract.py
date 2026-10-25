import json

import pytest
from fastapi.testclient import TestClient

from backend.app import crawler, main
from backend.app.comparison import evaluation_url_key
from backend.app.detection import detect_page
from backend.app.evaluation import capture_site, evaluate_capture
from backend.app.result import build_result_json


@pytest.mark.parametrize('other', [
    'http://example.test/path/?a=1&b=2#section',
    'https://example.test/path?b=2&a=1',
    'https://example.test/path/?b=2&a=1#other',
])
def test_pdf_url_equivalence(other):
    assert evaluation_url_key(other) == evaluation_url_key('https://example.test/path?a=1&b=2')


@pytest.mark.parametrize('other', [
    'https://example.test/path?a=2&b=2', 'https://example.test/other?a=1&b=2',
    'https://example.test/path?a=1&b=', 'https://example.test/path?a=1&b=2&b=2',
    'https://other.test/path?a=1&b=2',
])
def test_pdf_distinct_pages_are_not_merged(other):
    assert evaluation_url_key(other) != evaluation_url_key('https://example.test/path?a=1&b=2')


def test_raw_evidence_keeps_whitespace_unicode_and_long_text():
    original = '  ㅋㅏㅈㅣㄴㅗ\n\tｍｅｇａ－ＢＥＴ\u200b  ' + '원문' * 400 + ' 끝  '
    findings = detect_page({'url': 'https://example.test', 'html': f'<p>{original}</p>'})
    result = build_result_json('https://example.test', findings)
    assert result['meta']['topic'] == 'TOPIC'
    assert {item['technique'] for item in result['findings']} == {'JAMO', 'HOMOGLYPH'}
    assert all(item['evidence_text'] == original for item in result['findings'])
    assert all('감지되었습니다' not in item['evidence_text'] for item in result['findings'])


def test_equivalent_urls_deduplicate_submission_without_rewriting_output_url():
    base = dict(url='http://example.test/page/?b=2&a=1#x', location='p#ad',
                technique='JAMO', source_text='원문')
    result = build_result_json(base['url'], [base, {**base, 'url': 'https://example.test/page?a=1&b=2'}])
    assert len(result['findings']) == 1
    assert result['findings'][0]['url'] == base['url']


def test_submission_refuses_explanation_without_original_text():
    with pytest.raises(ValueError, match='original source_text'):
        build_result_json('https://example.test', [dict(url='https://example.test',
                          location='p', technique='JAMO', evidence='판정 설명만 있음')])


def test_api_writes_separate_pdf_extra_file_with_original_block_text(monkeypatch, tmp_path):
    original = '  성인<span>영상</span>\n 무료시청\u200b  '
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: (f'<p>{original}</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.test'})
    assert response.status_code == 200, response.text
    data = response.json()
    extra = data['result_extra_json']
    assert set(extra) == {'meta', 'findings'}
    assert extra['meta'] == data['result_json']['meta']
    item = extra['findings'][0]
    assert item['evidence_text'] == '  성인영상\n 무료시청\u200b  '
    assert item['technique'] == 'ETC'
    assert item['extra_finding'] == 'ADULT_CONTENT_PROMOTION_CANDIDATE'
    assert 'is_violation' not in item
    for name, expected in [('result.json', data['result_json']), ('result_extra.json', extra)]:
        raw = (tmp_path / name).read_bytes()
        assert not raw.startswith(b'\xef\xbb\xbf')
        assert json.loads(raw) == expected
    assert not data['result_json']['findings']


def test_extra_file_is_empty_on_clean_success_and_preserved_on_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: ('<p>일반 안내</p>', url))
    with TestClient(main.app) as client:
        assert client.post('/api/analyze', json={'url': 'https://example.test'}).status_code == 200
        extra_path = tmp_path / 'result_extra.json'
        assert json.loads(extra_path.read_bytes())['findings'] == []
        before = {p.name: p.read_bytes() for p in tmp_path.glob('result*.json')}

        def fail(*args, **kwargs):
            raise RuntimeError('fixture failure')
        monkeypatch.setattr(crawler, 'fetch_html', fail)
        assert client.post('/api/analyze', json={'url': 'https://example.test'}).status_code == 502
        assert before == {p.name: p.read_bytes() for p in tmp_path.glob('result*.json')}


@pytest.mark.parametrize('kind', ['feature', 'content'])
def test_offline_labels_accept_pdf_equivalent_urls_and_selectors(monkeypatch, tmp_path, kind):
    url = 'https://example.test/page?a=1&b=2'
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: ('<p id="ad" style="opacity:0">카지노 가입 보너스</p>', url))
    output = tmp_path / 'capture'
    capture_site(url, output)
    label_file = output / ('labels.json' if kind == 'feature' else 'content-labels.json')
    labels = json.loads(label_file.read_bytes())
    labels.update(complete=True, policy='Synthetic fixture only')
    labels['labels'][0].update(url='http://example.test/page/?b=2&a=1#ignored', location='#ad',
                                expected=True, reviewed=True, reason='Synthetic positive')
    label_file.write_text(json.dumps(labels), encoding='utf-8')
    report = evaluate_capture(output, kind=kind)
    assert report['counts'] == dict(tp=1, fp=0, fn=0, tn=0)
    assert report['metrics']['precision'] == report['metrics']['recall'] == 1


def test_equivalent_urls_with_conflicting_snapshots_are_rejected(monkeypatch, tmp_path):
    from backend.app import evaluation
    monkeypatch.setattr(evaluation, 'crawl_site', lambda *args, **kw: [
        dict(url='https://example.test/page', html='<p>First version</p>'),
        dict(url='http://example.test/page/', html='<p>Different version</p>'),
    ])
    output = tmp_path / 'conflict'
    capture_site('https://example.test/page', output)
    with pytest.raises(ValueError, match='conflicting'):
        evaluate_capture(output)
