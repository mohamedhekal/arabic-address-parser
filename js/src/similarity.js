// Address similarity for de-duplication. Mirrors python/src/arabic_address_parser/similarity.py.
import { key } from "./normalize.js";
import { ALL_KEYWORDS, NUMWORD, parse } from "./parser.js";

const STOP = new Set([...ALL_KEYWORDS, ...NUMWORD, "من", "في", "و", "of", "the"]);
const content = (text) => key(text).split(" ").filter((t) => t && !STOP.has(t));

function levenshtein(a, b) {
  if (a === b) return 0;
  if (!a.length) return b.length;
  if (!b.length) return a.length;
  let prev = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur.push(Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)));
    }
    prev = cur;
  }
  return prev[prev.length - 1];
}

const round4 = (x) => Math.floor(x * 10000 + 0.5) / 10000;

/**
 * Score in [0, 1]: 1 means the same address once normalized.
 * `0.6 * token Jaccard + 0.4 * character ratio` on content tokens, halved per conflicting building/apartment/floor.
 */
export function similarity(a, b) {
  const ta = content(a);
  const tb = content(b);
  if (!ta.length && !tb.length) return key(a) === key(b) ? 1.0 : 0.0;
  const sa = new Set(ta);
  const sb = new Set(tb);
  const unionSize = new Set([...sa, ...sb]).size;
  let inter = 0;
  for (const t of sa) if (sb.has(t)) inter++;
  const jaccard = unionSize ? inter / unionSize : 0.0;
  const ja = [...ta].sort().join(" ");
  const jb = [...tb].sort().join(" ");
  const longest = Math.max(ja.length, jb.length);
  const ratio = longest ? 1 - levenshtein(ja, jb) / longest : 1.0;
  let score = 0.6 * jaccard + 0.4 * ratio;
  const pa = parse(a);
  const pb = parse(b);
  for (const field of ["building", "apartment", "floor"]) {
    const va = pa[field];
    const vb = pb[field];
    if (va !== null && vb !== null && String(va).toLowerCase() !== String(vb).toLowerCase()) score *= 0.5;
  }
  return round4(score);
}

export function isSameAddress(a, b, threshold = 0.85) {
  return similarity(a, b) >= threshold;
}
