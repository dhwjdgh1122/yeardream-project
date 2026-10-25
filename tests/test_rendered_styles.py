import pytest

from backend.app.detection import detect_page


def observe(**changes):
    result = dict(selector='p#ad', source_text='Fixture text', display_none=False, zero_opacity=False,
                  visibility='visible', color='rgb(0, 0, 0)', background='rgb(255, 255, 255)',
                  font_size='16px', rect=dict(left=8, top=8, right=208, bottom=28, width=200, height=20))
    result.update(changes)
    return result


def page(observation):
    return dict(url='https://example.test', html='<p id="ad">Fixture text</p>',
                rendered_style=dict(schema_version=1, observations=[observation]))


@pytest.mark.parametrize('change, technique', [
    ({'zero_opacity': True}, 'TRANSPARENT'),
    ({'visibility': 'hidden'}, 'TRANSPARENT'),
    ({'color': 'rgba(10, 20, 30, 0)'}, 'TRANSPARENT'),
    ({'color': 'rgb(255, 255, 255)'}, 'TRANSPARENT'),
    ({'display_none': True}, 'OFFSCREEN'),
    ({'font_size': '1px'}, 'OFFSCREEN'),
    ({'rect': dict(right=-100, bottom=20, width=200, height=20)}, 'OFFSCREEN'),
])
def test_saved_computed_values_detect_features(change, technique):
    observation = observe()
    observation.update(change)
    found = detect_page(page(observation))
    assert [item['technique'] for item in found] == [technique]
    assert found[0]['source_text'] == 'Fixture text'


@pytest.mark.parametrize('change', [
    {}, {'color': 'rgba(255, 255, 255, 0.5)'},
    {'background': None}, {'background': 'rgba(0, 0, 0, 0.5)'},
    {'color': 'rgb(255, 255, 255)', 'text_effects': True},
    {'color': 'rgba(0, 0, 0, 0)', 'text_effects': True},
    {'rect': dict(right=199, bottom=20, width=200, height=20)},
    {'rect': dict(right=208, bottom=3020, width=200, height=20)},
])
def test_visible_partial_below_fold_and_uncertain_colors_are_not_features(change):
    observation = observe()
    observation.update(change)
    assert detect_page(page(observation)) == []


def test_browser_values_override_superseded_inline_styles():
    value = page(observe())
    value['html'] = '<p id="ad" style="opacity:0;position:absolute;left:-1px">Fixture text</p>'
    assert len(detect_page({key: val for key, val in value.items() if key != 'rendered_style'})) == 2
    assert detect_page(value) == []


@pytest.mark.parametrize('change', [{'source_text': 'stale'}, {'selector': 'p.missing'}, {'selector': '('}])
def test_stale_or_invalid_observations_are_rejected(change):
    observation = observe()
    observation.update(change)
    with pytest.raises(ValueError):
        detect_page(page(observation))


def test_duplicate_observations_are_rejected():
    value = page(observe())
    value['rendered_style']['observations'] *= 2
    with pytest.raises(ValueError, match='duplicate'):
        detect_page(value)


def test_saved_styles_replay_without_browser_or_network(monkeypatch, tmp_path):
    import json
    from backend.app import evaluation

    observation = observe(zero_opacity=True)
    saved = page(observation)
    monkeypatch.setattr(evaluation, 'crawl_site', lambda *args, **kw: [saved])
    directory = tmp_path / 'captured'
    evaluation.capture_site('https://example.test', directory)
    capture = json.loads((directory / 'capture.json').read_bytes())
    assert capture['documents'][0]['rendered_style']['observations'] == [observation]
    labels_path = directory / 'labels.json'
    labels = json.loads(labels_path.read_bytes())
    labels.update(complete=True, policy='Synthetic style feature, not legal verdict')
    labels['labels'] = [dict(url='https://example.test', location='#ad', technique='TRANSPARENT',
                            expected=True, reviewed=True, reason='Saved computed opacity is zero')]
    labels_path.write_text(json.dumps(labels), encoding='utf-8')

    def forbid(*args, **kwargs):
        pytest.fail('Offline evaluation must not invoke a browser or network')
    monkeypatch.setattr(evaluation, 'crawl_site', forbid)
    monkeypatch.setattr(evaluation, 'BrowserRenderer', forbid)
    report = evaluation.evaluate_capture(directory)
    assert report['counts'] == dict(tp=1, fp=0, fn=0, tn=0)
    assert report['observation_basis'] == dict(rendered_documents=1, static_documents=0)
    assert report['rendered_policy_version'] == 'rendered-style-rules-v1'
