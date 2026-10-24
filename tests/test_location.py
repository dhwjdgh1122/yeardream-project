import html

import pytest
from bs4 import BeautifulSoup

from backend.app.detection import detect_page
from backend.app.location import build_selector


@pytest.mark.parametrize('markup', [
    '<main><p class="ad">Same</p><p class="ad">Same</p></main>',
    '<div><span>A</span></div><div><span>A</span></div>',
    '<div><p id="duplicate">Same</p><p id="duplicate">Same</p></div>',
    '<ul><li>A</li><li>B</li><li>C</li></ul>',
])
def test_each_element_can_be_reidentified_uniquely(markup):
    soup = BeautifulSoup(markup, 'html5lib')
    for element in soup.find_all(True):
        selected = soup.select(build_selector(element))
        assert len(selected) == 1
        assert selected[0] is element


@pytest.mark.parametrize('element_id', ['123:ad.[x]', 'a b,c', 'a >>> b', 'slash\\id', '한글'])
def test_special_id_and_class_are_css_escaped(element_id):
    soup = BeautifulSoup(
        f'<p id="{html.escape(element_id, quote=True)}" class="ad:promo">Text</p>',
        'html.parser',
    )
    assert soup.select_one(build_selector(soup.p)) is soup.p


def test_repeated_ads_have_distinct_locations_without_url_prefix():
    markup = '<div><span class="ad" style="opacity:0">First</span><span class="ad" style="opacity:0">Second</span></div>'
    findings = detect_page({'url': 'https://example.com', 'html': markup})
    assert len(findings) == 2
    assert len({finding['location'] for finding in findings}) == 2
    soup = BeautifulSoup(markup, 'html5lib')
    for finding in findings:
        assert finding['location'] == finding['selector']
        assert len(soup.select(finding['location'])) == 1


def test_table_locations_include_browser_inserted_tbody():
    markup = ''.join(
        f'<table><tr><td style="opacity:0">Table {name}</td></tr></table>'
        for name in ['first', 'second']
    )
    findings = detect_page({'url': 'https://example.com', 'html': markup})
    soup = BeautifulSoup(markup, 'html5lib')
    assert len(findings) == 2
    for finding in findings:
        matches = soup.select(finding['location'])
        assert len(matches) == 1
        assert matches[0].get_text() in finding['evidence']
        assert 'tbody' in finding['location']
