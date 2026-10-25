import re
from typing import Dict, List

from bs4 import BeautifulSoup, Comment, NavigableString
from soupsieve import SelectorSyntaxError

# Keep the existing import used by scripts/tests while separating result mapping.
from .result import build_result_json
from .location import build_selector
from .limits import Deadline
from .rendered import rendered_techniques

HOMOGLYPH_PATTERN = re.compile(r'[а-яА-ЯёЁіІјЈѕЅ\uff10-\uff19\uff21-\uff3a\uff41-\uff5a]')
JAMO_PATTERN = re.compile(r'[\u1100-\u11ff\u3130-\u318f]')


def _build_element_selector(element) -> str:
    return build_selector(element)


def _direct_text(element) -> str:
    return " ".join(
        str(child).strip() for child in element.children
        if isinstance(child, NavigableString) and not isinstance(child, Comment)
        and str(child).strip()
    )


def _inline_styles(element) -> Dict[str, str]:
    """Read simple inline declarations; external CSS/layout needs a browser."""
    styles = {}
    important = set()
    for declaration in str(element.get("style", "")).split(";"):
        name, separator, value = declaration.partition(":")
        if not separator:
            continue
        name = name.strip().lower()
        value = value.strip().lower()
        is_important = bool(re.search(r"!\s*important\s*$", value))
        value = re.sub(r"\s*!\s*important\s*$", "", value).strip()
        if name in important and not is_important:
            continue
        styles[name] = value
        if is_important:
            important.add(name)
    return styles


def _zero_opacity(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?(?:0+(?:\.0*)?|\.0+)%?", value))


def _offscreen_style(styles: Dict[str, str]) -> bool:
    if styles.get("display") == "none":
        return True
    size = styles.get("font-size", "")
    if size == "0" or (re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)px", size)
                       and float(size[:-2]) <= 1):
        return True
    if styles.get("position") not in {"absolute", "fixed"}:
        return False
    return any(
        re.fullmatch(r"-\d+(?:\.\d+)?px", styles.get(axis, ""))
        and float(styles[axis][:-2]) < 0
        for axis in ("left", "top")
    )


def _matches_technique(element, technique: str) -> bool:
    text = _direct_text(element)

    if technique == "HOMOGLYPH":
        return bool(HOMOGLYPH_PATTERN.search(text))
    if technique == "JAMO":
        return bool(JAMO_PATTERN.search(text))
    if technique == "TRANSPARENT":
        styles = _inline_styles(element)
        if styles.get("color") == "transparent" or styles.get("visibility") == "hidden":
            return True
        # An ancestor's zero opacity hides its descendants too.
        return any(_zero_opacity(_inline_styles(node).get("opacity", ""))
                   for node in [element, *element.parents] if node.name != "[document]")
    if technique == "OFFSCREEN":
        return _offscreen_style(_inline_styles(element))
    return False


def detect_page(page: Dict[str, object], *, deadline: Deadline | None = None) -> List[Dict[str, object]]:
    if deadline:
        deadline.check()
    findings: List[Dict[str, object]] = []
    url = str(page.get("top_url") or page.get("url", ""))
    frame_path = list(page.get("frame_path", []))
    html = str(page.get("html", ""))
    # HTML5 tree construction includes browser repairs such as implicit tbody.
    soup = BeautifulSoup(html, "html5lib")
    rendered = {}
    if 'rendered_style' in page:
        snapshot = page['rendered_style']
        if snapshot.get('schema_version') != 1:
            raise ValueError('Unsupported rendered style schema')
        for observation in snapshot['observations']:
            if deadline:
                deadline.check()
            try:
                matches = soup.select(observation['selector'])
            except SelectorSyntaxError as error:
                raise ValueError('Invalid rendered style selector') from error
            if len(matches) != 1:
                raise ValueError('Rendered style selector must identify one saved element')
            element = matches[0]
            original = ''.join(str(child) for child in element.children
                               if isinstance(child, NavigableString) and not isinstance(child, Comment))
            if original != observation['source_text'] or id(element) in rendered:
                raise ValueError('Rendered style text mismatch or duplicate element')
            rendered[id(element)] = rendered_techniques(observation)

    for technique, explanation in [
        ("HOMOGLYPH", "유사 문자 기반 위장 문자열이 감지되었습니다."),
        ("JAMO", "자모 분해 또는 분리형 한글 표현이 발견되었습니다."),
        ("TRANSPARENT", "투명 또는 시각적 은닉 스타일이 감지되었습니다."),
        ("OFFSCREEN", "화면 밖 배치 또는 시각적으로 숨긴 요소가 감지되었습니다."),
    ]:
        for element in soup.find_all(True):
            if deadline:
                deadline.check()
            if any(node.name in {"head", "script", "style", "template", "noscript"}
                   for node in [element, *element.parents]):
                continue
            text = _direct_text(element)
            if not text:
                continue
            if technique in {'TRANSPARENT', 'OFFSCREEN'} and 'rendered_style' in page:
                matched = technique in rendered.get(id(element), set())
            else:
                matched = _matches_technique(element, technique)
            if not matched:
                continue
            selector = _build_element_selector(element)
            findings.append(
                {
                    "technique": technique,
                    "selector": selector,
                    "location": " >>> ".join([*frame_path, selector]),
                    "url": url,
                    "evidence": f"{explanation} 원문: {text[:500]}",
                    "source_text": ''.join(str(child) for child in element.children
                                           if isinstance(child, NavigableString) and not isinstance(child, Comment)),
                    "confidence": 0.82 if technique in {"TRANSPARENT", "OFFSCREEN"} else 0.75,
                }
            )

    if deadline:
        deadline.check()
    return findings
