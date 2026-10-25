import html
import json
from pathlib import Path

import pytest

from backend.app.content import detect_content

CASES = json.loads((Path(__file__).parent / 'fixtures/content/cases.json').read_text(encoding='utf-8'))['cases']


@pytest.mark.parametrize('case', CASES, ids=[case['id'] for case in CASES])
def test_reviewed_synthetic_context(case):
    found = detect_content({'url': 'https://example.test', 'html': '<p>' + html.escape(case['text']) + '</p>'})
    assert {item['category'] for item in found} == set(case['expected']), case['reason']
