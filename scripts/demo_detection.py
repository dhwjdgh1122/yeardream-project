import json

from backend.app.detection import detect_page

SAMPLES = [
    {
        "name": "HOMOGLYPH",
        "page": {
            "url": "https://example.com/homoglyph",
            "html": "<div class='ad'>ｅxample 광고</div>",
            "text": "ｅxample 광고",
        },
    },
    {
        "name": "JAMO",
        "page": {
            "url": "https://example.com/jamo",
            "html": "<div class='ad'>ㅈㅏㅁㅗ 광고</div>",
            "text": "ㅈㅏㅁㅗ 광고",
        },
    },
    {
        "name": "TRANSPARENT",
        "page": {
            "url": "https://example.com/transparent",
            "html": "<div style='color: transparent; opacity: 0;'>숨김광고</div>",
            "text": "숨김광고",
        },
    },
    {
        "name": "OFFSCREEN",
        "page": {
            "url": "https://example.com/offscreen",
            "html": "<div style='position:absolute; left:-999px;'>시각적 은닉 광고</div>",
            "text": "시각적 은닉 광고",
        },
    },
]

for sample in SAMPLES:
    results = detect_page(sample["page"])
    print(sample["name"], json.dumps(results, ensure_ascii=False))
