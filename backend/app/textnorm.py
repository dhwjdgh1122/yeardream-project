"""Bounded keyword normalization with original character ranges for attribution."""
import unicodedata

CONFUSABLES = str.maketrans('аАеЕоОрРсСхХуУіІјЈѕЅ', 'aAeEoOpPcCxXyYiIjJsS')
LEADING_TO_FINAL = dict(zip('ᄀᄁᄂᄃᄅᄆᄇᄉᄊᄋᄌᄎᄏᄐᄑᄒ', [1, 2, 4, 7, 8, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27]))
FINAL_CLUSTERS = {(1, 19): 3, (4, 22): 5, (4, 27): 6, (8, 1): 9, (8, 16): 10,
                  (8, 17): 11, (8, 19): 12, (8, 25): 13, (8, 26): 14, (8, 27): 15, (17, 19): 18}


def normalize_mapped(text, offset=0, deadline=None):
    tokens = []
    for index, char in enumerate(text):
        if deadline:
            deadline.check()
        if char.isspace() or char in '\u200b\u200c\u200d\ufeff':
            continue
        hangul = '\uac00' <= char <= '\ud7a3' or '\u1100' <= char <= '\u11ff' or '\u3130' <= char <= '\u318f'
        normalized = unicodedata.normalize('NFKD' if hangul else 'NFKC', char).translate(CONFUSABLES).casefold()
        tokens.extend((part, offset + index, offset + index + 1) for part in normalized)
    output, ranges = [], []
    index = 0
    while index < len(tokens):
        if deadline:
            deadline.check()
        char, start, end = tokens[index]
        leading = ord(char) - 0x1100
        vowel = ord(tokens[index + 1][0]) - 0x1161 if index + 1 < len(tokens) else -1
        if 0 <= leading < 19 and 0 <= vowel < 21:
            count, final = 2, 0
            if index + 2 < len(tokens):
                tail = tokens[index + 2][0]
                following_vowel = index + 3 < len(tokens) and 0x1161 <= ord(tokens[index + 3][0]) <= 0x1175
                if 0x11a8 <= ord(tail) <= 0x11c2:
                    final, count = ord(tail) - 0x11a7, 3
                elif tail in LEADING_TO_FINAL and not following_vowel:
                    final, count = LEADING_TO_FINAL[tail], 3
                    if index + 3 < len(tokens):
                        second = LEADING_TO_FINAL.get(tokens[index + 3][0])
                        next_vowel = index + 4 < len(tokens) and 0x1161 <= ord(tokens[index + 4][0]) <= 0x1175
                        if (final, second) in FINAL_CLUSTERS and not next_vowel:
                            final, count = FINAL_CLUSTERS[(final, second)], 4
            output.append(chr(0xac00 + (leading * 21 + vowel) * 28 + final))
            ranges.append((start, tokens[index + count - 1][2]))
            index += count
        else:
            output.append(char)
            ranges.append((start, end))
            index += 1
    return ''.join(output), ranges
