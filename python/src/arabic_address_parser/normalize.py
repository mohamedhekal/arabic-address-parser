"""Text cleaning and search-key normalization for Arabic (and mixed Arabic/Latin) addresses.

Two levels, kept identical to the JavaScript implementation (see spec/SPEC.md):

* ``clean``  - display-safe: removes diacritics/tatweel, converts digits and punctuation, collapses whitespace.
* ``key``    - search key: ``clean`` + letter folding + article stripping. Use it to compare strings.
"""
import re
import unicodedata

_DIACRITICS = re.compile("[ً-ٰٟۖ-ۭـ]")
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_PUNCT = str.maketrans({"،": ",", "؛": ";", "؟": "?"})
_NEWLINES = re.compile(r"\s*[\r\n]+\s*")
_SPACES = re.compile(r"\s+")

_LETTERS = str.maketrans(
    {
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي", "ی": "ي",
        "ة": "ه",
        "ؤ": "و", "ئ": "ي", "ء": "",
        "ک": "ك", "گ": "ك",
        "پ": "ب", "چ": "ج", "ڤ": "ف",
    }
)
_NON_KEY_CHARS = re.compile(r"[^ء-يa-z0-9]+")
_REPEATS = re.compile(r"([^\d\s])\1{2,}")


def clean(text):
    """Return a display-safe version of ``text`` (letters are left untouched)."""
    if text is None:
        return ""
    t = unicodedata.normalize("NFKC", str(text))
    t = _DIACRITICS.sub("", t).translate(_DIGITS).translate(_PUNCT)
    t = _NEWLINES.sub(", ", t)
    return _SPACES.sub(" ", t).strip()


def token_key(token, strip_article=True):
    """Key for a single already-folded token (no spaces)."""
    if strip_article:
        if token in ("el", "al"):
            return ""
        if token.startswith("ال") and len(token) > 3 and token != "الله":
            return token[2:]
    return token


def key(text, strip_article=True):
    """Return the normalized search key of ``text``.

    >>> key("الإسكندرية") == key("اسكندريه")
    True
    """
    t = clean(text).lower().translate(_LETTERS)
    t = _NON_KEY_CHARS.sub(" ", t)
    t = _REPEATS.sub(r"\1\1", t)
    out = [token_key(tok, strip_article) for tok in t.split()]
    return " ".join(tok for tok in out if tok)


normalize = key
