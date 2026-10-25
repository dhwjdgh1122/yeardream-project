import pytest

from backend.app.result import build_result_json


def test_result_preserves_distinct_locations_and_techniques():
    base = dict(url='https://example.com', location='div#a', technique='JAMO', source_text='sample')
    payload = build_result_json(
        base['url'],
        [base, base.copy(), {**base, 'location': 'div#b'}, {**base, 'technique': 'HOMOGLYPH'}],
        started_at='2026-10-23T09:00:00+09:00',
        finished_at='2026-10-23T00:00:01.500000+00:00',
    )
    assert len(payload['findings']) == 3
    assert len({f['id'] for f in payload['findings']}) == 3
    assert payload['meta']['elapsed_sec'] == 1.5


@pytest.mark.parametrize('changes', [
    {'technique': 'UNKNOWN'},
    {'is_violation': 'false'},
    {'location': ''},
    {'source_text': ''},
])
def test_invalid_result_data_is_rejected(changes):
    finding = dict(url='https://example.com', location='div', technique='JAMO', source_text='sample')
    with pytest.raises(ValueError):
        build_result_json(finding['url'], [{**finding, **changes}])


@pytest.mark.parametrize('start,end', [
    ('2026-10-23T00:00:00', '2026-10-23T00:00:01+00:00'),
    ('2026-10-23T00:00:02+00:00', '2026-10-23T00:00:01+00:00'),
])
def test_invalid_result_times_are_rejected(start, end):
    with pytest.raises(ValueError):
        build_result_json('https://example.com', [], started_at=start, finished_at=end)
