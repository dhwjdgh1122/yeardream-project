"""Shared conservative boundaries for compatibility-jamo chat laughter."""

import re

JAMO_PATTERN = re.compile(r'[\u1100-\u11ff\u3130-\u318f]')
JAMO_RUN_PATTERN = re.compile(r'[\u1100-\u11ff\u3130-\u318f]+')
CHAT_LAUGHTER_PATTERN = re.compile(r'[ㅋㅎ]{2,}')


def has_jamo_feature(text):
    # A complete laughter run is exempt; a single initial, vowels, other
    # consonants and decomposed modern Hangul remain detectable.
    return any(not CHAT_LAUGHTER_PATTERN.fullmatch(match.group())
               for match in JAMO_RUN_PATTERN.finditer(text))


def laughter_spans(text, deadline=None):
    for match in JAMO_RUN_PATTERN.finditer(text):
        if deadline:
            deadline.check()
        if CHAT_LAUGHTER_PATTERN.fullmatch(match.group()):
            yield match.start(), match.end()
