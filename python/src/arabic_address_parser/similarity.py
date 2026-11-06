"""Address similarity for de-duplication and matching."""
import math

from .normalize import key
from .parser import ALL_KEYWORDS, NUMWORD, parse

_STOP = ALL_KEYWORDS | NUMWORD | {"من", "في", "و", "of", "the"}


def _content(text):
    return [t for t in key(text).split() if t not in _STOP]


def _levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if ca == cb else 1)))
        prev = cur
    return prev[-1]


def _round4(x):
    return math.floor(x * 10000 + 0.5) / 10000


def similarity(a, b):
    """Return a score in [0, 1]: 1 means the same address once normalized.

    ``0.6 * token Jaccard + 0.4 * character ratio`` on the content tokens (street/building keywords removed),
    halved for every conflicting building / apartment / floor number.
    """
    ta, tb = _content(a), _content(b)
    if not ta and not tb:
        return 1.0 if key(a) == key(b) else 0.0
    sa, sb = set(ta), set(tb)
    union = len(sa | sb)
    jaccard = len(sa & sb) / union if union else 0.0
    ja, jb = " ".join(sorted(ta)), " ".join(sorted(tb))
    longest = max(len(ja), len(jb))
    ratio = 1 - _levenshtein(ja, jb) / longest if longest else 1.0
    score = 0.6 * jaccard + 0.4 * ratio
    pa, pb = parse(a), parse(b)
    for field in ("building", "apartment", "floor"):
        va, vb = pa[field], pb[field]
        if va is not None and vb is not None and str(va).lower() != str(vb).lower():
            score *= 0.5
    return _round4(score)


def is_same_address(a, b, threshold=0.85):
    return similarity(a, b) >= threshold
