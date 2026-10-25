"""Conservative feature decisions from saved browser observations, not ad verdicts."""
import math
import re

POLICY_VERSION = 'rendered-style-rules-v1'


def _rgb(value):
    match = re.fullmatch(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)', value or '')
    if not match:
        return None
    return tuple(float(part) for part in (*match.groups()[:3], match.group(4) or '1'))


def rendered_techniques(observation):
    techniques = set()
    color = _rgb(observation.get('color'))
    background = _rgb(observation.get('background'))
    same_solid_color = (not observation.get('text_effects') and color is not None and background is not None
                        and color[3] == background[3] == 1 and color[:3] == background[:3])
    if (observation.get('zero_opacity') or observation.get('visibility') in {'hidden', 'collapse'}
            or not observation.get('text_effects') and color is not None and color[3] == 0 or same_solid_color):
        techniques.add('TRANSPARENT')
    size = re.fullmatch(r'(\d+(?:\.\d+)?|\.\d+)px', observation.get('font_size', ''))
    rect = observation.get('rect') or {}
    # Document coordinates avoid confusing a scrolled viewport or below-fold content with hiding.
    outside_negative = (all(isinstance(rect.get(key), (int, float)) and math.isfinite(rect[key])
                            for key in ('right', 'bottom', 'width', 'height'))
                        and rect['width'] > 0 and rect['height'] > 0
                        and (rect['right'] <= 0 or rect['bottom'] <= 0))
    if observation.get('display_none') or size and float(size.group(1)) <= 1 or outside_negative:
        techniques.add('OFFSCREEN')
    return techniques
