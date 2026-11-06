// Text cleaning and search-key normalization. Mirrors python/src/arabic_address_parser/normalize.py
// (see spec/SPEC.md): `clean` is display-safe, `key` is the search key used for comparisons.

const DIACRITICS = /[ً-ٰٟۖ-ۭـ]/g;
const DIGITS = "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹";
const PUNCT = { "،": ",", "؛": ";", "؟": "?" };
const NEWLINES = /\s*[\r\n]+\s*/g;
const SPACES = /\s+/g;

const LETTERS = {
  "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
  "ى": "ي", "ی": "ي",
  "ة": "ه",
  "ؤ": "و", "ئ": "ي", "ء": "",
  "ک": "ك", "گ": "ك",
  "پ": "ب", "چ": "ج", "ڤ": "ف",
};
const LETTERS_RE = new RegExp(`[${Object.keys(LETTERS).join("")}]`, "g");
const NON_KEY_CHARS = /[^ء-يa-z0-9]+/g;
const REPEATS = /([^\d\s])\1{2,}/g;

/** Return a display-safe version of `text` (letters are left untouched). */
export function clean(text) {
  if (text === null || text === undefined) return "";
  let t = String(text).normalize("NFKC");
  t = t.replace(DIACRITICS, "");
  t = t.replace(/[٠-٩۰-۹]/g, (c) => String(DIGITS.indexOf(c) % 10));
  t = t.replace(/[،؛؟]/g, (c) => PUNCT[c]);
  t = t.replace(NEWLINES, ", ");
  return t.replace(SPACES, " ").trim();
}

/** Key for a single already-folded token (no spaces). */
export function tokenKey(token, stripArticle = true) {
  if (stripArticle) {
    if (token === "el" || token === "al") return "";
    if (token.startsWith("ال") && token.length > 3 && token !== "الله") return token.slice(2);
  }
  return token;
}

/** Return the normalized search key of `text`. */
export function key(text, stripArticle = true) {
  let t = clean(text).toLowerCase().replace(LETTERS_RE, (c) => LETTERS[c]);
  t = t.replace(NON_KEY_CHARS, " ");
  t = t.replace(REPEATS, "$1$1");
  const out = [];
  for (const tok of t.split(" ")) {
    if (!tok) continue;
    const k = tokenKey(tok, stripArticle);
    if (k) out.push(k);
  }
  return out.join(" ");
}

export const normalize = key;
