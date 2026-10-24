"""CSS selectors that identify one element in its source document."""

from bs4 import Tag
from soupsieve import escape


def _short_selector(name, element_id=None, classes=()):
    selector = escape(str(name or "div"))
    if element_id:
        selector += "#" + escape(str(element_id))
    if isinstance(classes, str):
        classes = classes.split()
    for token in classes or ():
        if str(token):
            selector += "." + escape(str(token))
    return selector


def build_selector(element) -> str:
    """Dict input retains the legacy fragment API; DOM input guarantees uniqueness."""
    if element is None:
        return "body"
    if isinstance(element, dict):
        return _short_selector(
            element.get("tag") or element.get("name"),
            element.get("id"), element.get("class", ()),
        )
    if not isinstance(element, Tag) or element.parent is None:
        raise ValueError("Selector generation requires an element attached to a document")

    root = element
    while root.parent is not None:
        root = root.parent

    def uniquely_selects_target(selector):
        matches = root.select(selector, limit=2)
        return len(matches) == 1 and matches[0] is element

    short = _short_selector(element.name, element.get("id"), element.get("class", ()))
    if uniquely_selects_target(short):
        return short

    parts = []
    current = element
    while current is not root:
        siblings = current.parent.find_all(current.name, recursive=False)
        position = next(i for i, sibling in enumerate(siblings, 1) if sibling is current)
        parts.insert(0, f"{escape(current.name)}:nth-of-type({position})")
        selector = " > ".join(parts)
        if uniquely_selects_target(selector):
            return selector
        current = current.parent
    raise ValueError("Unable to generate a unique selector")
