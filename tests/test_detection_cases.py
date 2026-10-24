import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from backend.app.detection import detect_page
from backend.app.result import build_result_json


FIXTURES = Path(__file__).parent / 'fixtures' / 'detection'
CASES = json.loads((FIXTURES / 'cases.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', CASES, ids=lambda case: case['file'])
def test_detection_matches_exact_elements_and_techniques(case):
    html = (FIXTURES / case['file']).read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html5lib')
    findings = detect_page({'url': 'https://example.com/fixture', 'html': html})
    actual = []
    for finding in findings:
        matches = soup.select(finding['selector'])
        assert len(matches) == 1, finding
        actual.append((matches[0].get('id'), finding['technique']))
        assert matches[0].get_text(strip=True) in finding['evidence']
    expected = [(element_id, technique)
                for element_id, techniques in case['expected'].items()
                for technique in techniques]
    assert sorted(actual) == sorted(expected)
    result = build_result_json('https://example.com/fixture', findings)
    assert len(result['findings']) == len(expected)
