from backend.app.crawler import extract_iframe_sources
from backend.app.detection import build_result_json, build_selector, detect_page


def test_extract_iframe_sources_handles_nested_frames():
    html = """
    <html><body>
      <iframe src="/frame1.html"></iframe>
      <div><iframe src="https://example.com/inner/child.html"></iframe></div>
      <iframe src="https://other.com/external.html"></iframe>
    </body></html>
    """
    sources = extract_iframe_sources(html, "https://example.com/page")
    assert sources == [
        "https://example.com/frame1.html",
        "https://example.com/inner/child.html",
    ]


def test_build_selector_uses_id_and_classes():
    tag = {"tag": "div", "id": "promo", "class": ["ad", "hide"]}
    assert build_selector(tag) == "div#promo.ad.hide"


def test_detects_transparent_ad_style():
    page = {
        "url": "https://example.com/page",
        "html": "<div id='promo' class='ad' style='color: transparent; opacity: 0;'>광고</div>",
        "text": "광고",
    }
    detections = detect_page(page)
    techniques = {item["technique"] for item in detections}
    assert "TRANSPARENT" in techniques


def test_ignores_clean_pages():
    page = {
        "url": "https://example.com/clean",
        "html": "<div id='content'>정상 콘텐츠</div>",
        "text": "정상 콘텐츠",
    }
    detections = detect_page(page)
    assert detections == []


def test_build_result_json_uses_required_schema():
    findings = [
        {
            "technique": "OFFSCREEN",
            "selector": "div.ad",
            "location": "div.ad",
            "url": "https://example.com",
            "evidence": "화면 밖 배치가 감지되었습니다.",
            "source_text": "광고 원문",
            "is_violation": True,  # Explicit synthetic schema input, not detector adjudication.
            "confidence": 0.82,
        }
    ]

    payload = build_result_json("https://example.com", findings)

    assert "meta" in payload
    assert "findings" in payload
    assert payload["findings"][0]["technique"] == "OFFSCREEN"
    assert payload["findings"][0]["is_violation"] is True
    assert payload["findings"][0]["location"] == "div.ad"
