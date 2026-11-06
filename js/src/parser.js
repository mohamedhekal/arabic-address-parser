// Rule-based address parser. Line-for-line mirror of python/src/arabic_address_parser/parser.py;
// both are specified in spec/SPEC.md and verified against the shared cases in spec/cases/.
import DATA from "./data.js";
import { clean, key, tokenKey } from "./normalize.js";

const kw = (name) => new Set(DATA.keywords[name].map((w) => key(w)));
const union = (...sets) => new Set(sets.flatMap((s) => [...s]));

export const STREET = kw("street");
export const BUILDING = kw("building");
export const FLOOR = kw("floor");
export const APARTMENT = kw("apartment");
export const BLOCK = kw("block");
export const DISTRICT = kw("district");
export const CITY = kw("city");
export const LANDMARK = kw("landmark");
export const NOISE = kw("noise");
export const NUMWORD = kw("number_word");
const STREET_SUFFIX = kw("street_suffix");
const SKIP_AFTER_LANDMARK = kw("skip_after_landmark");
const ORDINALS = new Map(Object.entries(DATA.keywords.ordinals).map(([k, v]) => [key(k), v]));
export const ALL_KEYWORDS = union(STREET, BUILDING, FLOOR, APARTMENT, BLOCK, DISTRICT, CITY, LANDMARK, NOISE);
const PREFIXABLE = union(STREET, BUILDING, FLOOR, APARTMENT, BLOCK, DISTRICT, CITY, LANDMARK);

const COUNTRIES = new Map(DATA.countries.map((c) => [c.code, c]));
const REGIONS = new Map(DATA.regions.map((r) => [r.id, r]));

export const INDEX = new Map(); // key -> entry
export const COLLISIONS = []; // [key, firstName, secondName]  (checked by the test-suite)
let MAX_N = 1;

function register(entry, names) {
  for (const name of names) {
    const k = key(name);
    if (!k) continue;
    const existing = INDEX.get(k);
    if (existing !== undefined && existing !== entry) {
      COLLISIONS.push([k, existing.name_ar, entry.name_ar]);
      continue;
    }
    INDEX.set(k, entry);
    MAX_N = Math.max(MAX_N, k.split(" ").length);
  }
}

for (const c of DATA.countries) {
  register({ kind: "country", code: c.code, name_ar: c.name_ar, name_en: c.name_en, country: c.code }, [c.name_ar, c.name_en, ...c.aliases]);
}
for (const r of DATA.regions) {
  register({ kind: "region", id: r.id, name_ar: r.name_ar, name_en: r.name_en, country: r.country }, [r.name_ar, r.name_en, ...r.aliases]);
}
for (const p of DATA.places) {
  register(
    { kind: "place", type: p.type, region: p.region, name_ar: p.name_ar, name_en: p.name_en, country: REGIONS.get(p.region).country },
    [p.name_ar, p.name_en, ...p.aliases],
  );
}

// ------------------------------------------------------------------------------------------ patterns

const AR = "\\u0621-\\u064A";
const PHONE = new RegExp(`(?<![A-Za-z0-9${AR}])\\+?\\d[\\d\\-]{8,16}\\d(?![A-Za-z0-9${AR}])`, "g");
const POSTAL = new RegExp(
  "(?:الرمز البريدي|الرمز البريدى|رمز بريدي|رمز بريدى|الكود البريدي|الكود البريدى|كود بريدي|كود بريدى|postal code|post code|zip code|zip|ص\\.?\\s?ب\\.?|p\\.?o\\.?\\s?box)\\s*[:\\-]?\\s*(\\d{3,6})",
  "gi",
);
const SHORT_ADDRESS = /(?<![A-Za-z0-9])[A-Z]{4}\d{4}(?![A-Za-z0-9])/g;
const SEGMENT_SPLIT = /[,;|]+|\s[-–—]\s/;
const LETTER_DIGIT = new RegExp(`([${AR}])(\\d)`, "g");
const DIGIT_LETTER = new RegExp(`(\\d)(?=[${AR}]{2})`, "g");
const DIGITISH = new RegExp(`^\\d+[A-Za-z${AR}]?(?:[/\\-]\\d+)?$`);
const TOKEN_SPLIT = /[.\-_/:()[\]"'`*]+/;
const EDGE = new Set([...".:()[]\"'`-_*"]);

const digitish = (s) => DIGITISH.test(s);

function stripEdge(s) {
  let a = 0;
  let b = s.length;
  while (a < b && EDGE.has(s[a])) a++;
  while (b > a && EDGE.has(s[b - 1])) b--;
  return s.slice(a, b);
}

function tokenize(segment) {
  segment = segment.replace(LETTER_DIGIT, "$1 $2").replace(DIGIT_LETTER, "$1 ");
  const out = [];
  let pending = "";
  for (let raw of segment.split(/\s+/)) {
    raw = stripEdge(raw);
    if (!raw) continue;
    if (digitish(raw)) {
      out.push({ raw: pending + raw, k: raw.toLowerCase() });
      pending = "";
      continue;
    }
    for (const part of raw.split(TOKEN_SPLIT)) {
      if (!part) continue;
      let k = key(part, false).replace(/ /g, "");
      if (!k) continue;
      k = tokenKey(k);
      if (!k) {
        pending += `${part} `; // Latin article ("el", "al"): glued to the next token's raw text
        continue;
      }
      if (k.length > 2 && k[0] === "ب" && PREFIXABLE.has(k.slice(1)) && !ALL_KEYWORDS.has(k)) k = k.slice(1);
      out.push({ raw: pending + part, k });
      pending = "";
    }
  }
  return out;
}

function detectLanguage(text) {
  const hasAr = /[؀-ۿ]/.test(text);
  const hasLa = /[A-Za-z]/.test(text);
  if (hasAr && hasLa) return "mixed";
  if (hasAr) return "ar";
  if (hasLa) return "en";
  return "unknown";
}

const placeObj = (e) => ({ name_ar: e.name_ar, name_en: e.name_en, type: e.type, region_id: e.region });
const regionObj = (e, inferred = false) => ({ id: e.id, name_ar: e.name_ar, name_en: e.name_en, inferred });
const countryObj = (code) => {
  const c = COUNTRIES.get(code);
  return { code: c.code, name_ar: c.name_ar, name_en: c.name_en };
};

// ---------------------------------------------------------------------------------------------- parse

/**
 * Parse `text` into address components.
 * @param {string|null|undefined} text
 * @param {{defaultCountry?: string|null}} [options]
 */
export function parse(text, options = {}) {
  const defaultCountry = options.defaultCountry ?? null;
  const cleaned = clean(text);
  let work = cleaned;

  const phones = [];
  work = work.replace(PHONE, (m) => {
    const digits = m.replace(/[+-]/g, "");
    if (digits.length >= 10 && digits.length <= 13) {
      phones.push(m);
      return " , ";
    }
    return m;
  });

  const postal = [];
  work = work.replace(POSTAL, (_m, code) => {
    postal.push(code);
    return " , ";
  });

  const short = [];
  work = work.replace(SHORT_ADDRESS, (m) => {
    short.push(m);
    return " , ";
  });

  const st = {
    country: null, region: null, city: null, district: null, street: null, building: null,
    floor: null, apartment: null, block: null, landmark: null, secondary_street: null,
  };
  const resolved = { country: null, region: null, city: null, district: null };
  const unparsed = [];
  let unparsedTokens = 0;
  const warnings = [];

  for (const segment of work.split(SEGMENT_SPLIT)) {
    const toks = tokenize(segment);
    const n = toks.length;
    if (n === 0) continue;
    const used = new Array(n).fill(false);

    const gazAt = (i) => {
      if (used[i]) return null;
      for (let ln = Math.min(MAX_N, n - i); ln > 0; ln--) {
        let blocked = false;
        for (let x = i; x < i + ln; x++) if (used[x]) blocked = true;
        if (blocked) continue;
        const entry = INDEX.get(toks.slice(i, i + ln).map((t) => t.k).join(" "));
        if (entry !== undefined) return [ln, entry];
      }
      return null;
    };
    const isStop = (j) => {
      const k = toks[j].k;
      return ALL_KEYWORDS.has(k) || NUMWORD.has(k) || digitish(toks[j].raw) || gazAt(j) !== null;
    };
    const takeName = (start, maxn) => {
      const names = [];
      let j = start;
      while (j < n && !used[j] && names.length < maxn) {
        if (names.length > 0 && isStop(j)) break;
        names.push(j);
        j++;
      }
      return names;
    };
    const rawOf = (idx) => idx.map((i) => toks[i].raw).join(" ");
    const range = (a, b) => Array.from({ length: Math.max(0, b - a) }, (_, i) => a + i);

    // 1. landmark: from the first landmark keyword to the end of the segment
    for (let i = 0; i < n; i++) {
      if (LANDMARK.has(toks[i].k) && i + 1 < n) {
        let j = i + 1;
        if (SKIP_AFTER_LANDMARK.has(toks[j].k) && j + 1 < n) j++;
        // a country / region / city at the very end belongs to the address, not to the landmark
        let end = n;
        for (;;) {
          let hit = 0;
          for (let ln = Math.min(MAX_N, end - (j + 1)); ln > 0; ln--) {
            const entry = INDEX.get(toks.slice(end - ln, end).map((t) => t.k).join(" "));
            if (entry !== undefined && (entry.kind !== "place" || entry.type === "city")) {
              hit = ln;
              break;
            }
          }
          if (!hit) break;
          end -= hit;
        }
        const text_ = toks.slice(i, end).map((t) => t.raw).join(" ");
        if (st.landmark === null) st.landmark = text_;
        else unparsed.push(text_);
        for (let x = i; x < end; x++) used[x] = true;
        break;
      }
    }

    // 1b. Latin street suffix: "Tahrir St", "26th of July Road"
    for (let i = 1; i < n; i++) {
      if (used[i] || !STREET_SUFFIX.has(toks[i].k) || /[؀-ۿ]/.test(toks[i].raw)) continue;
      const names = [];
      let j = i - 1;
      while (j >= 0 && names.length < 3 && !used[j] && !isStop(j)) {
        names.unshift(j);
        j--;
      }
      if (names.length === 0) continue;
      const phrase = `${rawOf(names)} ${toks[i].raw}`;
      for (const x of names) used[x] = true;
      used[i] = true;
      if (st.street === null) st.street = phrase;
      else st.secondary_street = st.secondary_street ?? phrase;
      if (
        st.building === null && j >= 0 && !used[j] && digitish(toks[j].raw) &&
        !(j > 0 && (FLOOR.has(toks[j - 1].k) || APARTMENT.has(toks[j - 1].k) || BLOCK.has(toks[j - 1].k) || BUILDING.has(toks[j - 1].k)))
      ) {
        st.building = toks[j].raw;
        used[j] = true;
      }
    }

    // 2. left-to-right scan
    let i = 0;
    while (i < n) {
      if (used[i]) {
        i++;
        continue;
      }
      const k = toks[i].k;
      const g = gazAt(i);
      if (g !== null) {
        const [ln, entry] = g;
        const phrase = rawOf(range(i, i + ln));
        for (let x = i; x < i + ln; x++) used[x] = true;
        if (entry.kind === "country") {
          if (st.country === null) {
            st.country = entry.code;
            resolved.country = countryObj(entry.code);
          } else unparsed.push(phrase);
        } else if (entry.kind === "region") {
          if (st.region === null) {
            st.region = entry.id;
            resolved.region = regionObj(entry);
          } else unparsed.push(phrase);
        } else {
          const slot = entry.type === "city" ? "city" : "district";
          if (st[slot] === null) {
            st[slot] = entry.name_ar;
            resolved[slot] = placeObj(entry);
          } else unparsed.push(phrase);
        }
        i += ln;
        continue;
      }

      if (NUMWORD.has(k) && i + 1 < n && !used[i + 1]) {
        used[i] = true;
        i++;
        continue;
      }
      if (NOISE.has(k)) {
        used[i] = true;
        i++;
        continue;
      }

      if (STREET.has(k)) {
        let j = i + 1;
        if (j < n && NUMWORD.has(toks[j].k) && j + 1 < n) {
          used[j] = true;
          j++;
        }
        const names = j < n ? takeName(j, 4) : [];
        if (names.length === 0) {
          i++;
          continue;
        }
        const phrase = `${toks[i].raw} ${rawOf(names)}`;
        used[i] = true;
        for (const x of names) used[x] = true;
        if (st.street === null) st.street = phrase;
        else if (st.secondary_street === null) st.secondary_street = phrase;
        else unparsed.push(phrase);
        const nxt = names[names.length - 1] + 1;
        if (st.building === null && nxt < n && !used[nxt] && digitish(toks[nxt].raw) && gazAt(nxt) === null) {
          st.building = toks[nxt].raw;
          used[nxt] = true;
        }
        i = nxt;
        continue;
      }

      if (BUILDING.has(k)) {
        let j = i + 1;
        if (j < n && NUMWORD.has(toks[j].k) && j + 1 < n) {
          used[j] = true;
          j++;
        }
        let value;
        if (j < n && !used[j] && digitish(toks[j].raw)) {
          value = toks[j].raw;
          used[i] = used[j] = true;
          i = j + 1;
        } else {
          const names = j < n ? takeName(j, 3) : [];
          if (names.length === 0) {
            i++;
            continue;
          }
          value = `${toks[i].raw} ${rawOf(names)}`;
          used[i] = true;
          for (const x of names) used[x] = true;
          i = names[names.length - 1] + 1;
        }
        if (st.building === null) st.building = value;
        else unparsed.push(value);
        continue;
      }

      if (FLOOR.has(k) || APARTMENT.has(k) || BLOCK.has(k)) {
        let j = i + 1;
        if (j < n && NUMWORD.has(toks[j].k) && j + 1 < n) {
          used[j] = true;
          j++;
        }
        if (j >= n || used[j]) {
          i++;
          continue;
        }
        const tk = toks[j];
        let value;
        let slot;
        if (FLOOR.has(k)) {
          if (digitish(tk.raw) && /^\d+$/.test(tk.raw)) value = parseInt(tk.raw, 10);
          else if (ORDINALS.has(tk.k)) value = ORDINALS.get(tk.k);
          else {
            i++;
            continue;
          }
          slot = "floor";
        } else {
          if (!digitish(tk.raw)) {
            i++;
            continue;
          }
          value = tk.raw;
          slot = APARTMENT.has(k) ? "apartment" : "block";
        }
        used[i] = used[j] = true;
        if (st[slot] === null) st[slot] = value;
        else unparsed.push(String(value));
        i = j + 1;
        continue;
      }

      if (DISTRICT.has(k) || CITY.has(k)) {
        let j = i + 1;
        if (k === "قسم" && j + 1 < n && ORDINALS.has(toks[j].k)) {
          used[j] = true; // "قسم أول مدينة نصر": the ordinal is a precinct number, not a place
          j++;
        }
        if (j < n && !used[j] && gazAt(j) !== null) {
          used[i] = true; // keyword before a known place name: the name is resolved on the next loop
          i++;
          continue;
        }
        const names = j < n ? takeName(j, 3) : [];
        if (names.length === 0) {
          i++;
          continue;
        }
        const slot = CITY.has(k) ? "city" : "district";
        used[i] = true;
        for (const x of names) used[x] = true;
        if (st[slot] === null) st[slot] = rawOf(names);
        else unparsed.push(rawOf(names));
        i = names[names.length - 1] + 1;
        continue;
      }

      if (digitish(toks[i].raw) && i + 1 < n && !used[i + 1] && STREET.has(toks[i + 1].k) && st.building === null) {
        st.building = toks[i].raw;
        used[i] = true;
        i++;
        continue;
      }

      i++;
    }

    // 3. whatever is left in this segment is unparsed
    let run = [];
    for (let x = 0; x < n; x++) {
      if (used[x]) {
        if (run.length) {
          unparsed.push(run.join(" "));
          run = [];
        }
      } else {
        run.push(toks[x].raw);
        unparsedTokens++;
      }
    }
    if (run.length) unparsed.push(run.join(" "));
  }

  // ---- inference and consistency checks
  for (const slot of ["district", "city"]) {
    const place = resolved[slot];
    if (place === null) continue;
    if (resolved.region === null) {
      resolved.region = regionObj(REGIONS.get(place.region_id), true);
      st.region = place.region_id;
    } else if (resolved.region.id !== place.region_id) {
      warnings.push(`region_mismatch:${place.name_ar}`);
    }
  }

  let countryCode = st.country;
  if (resolved.region !== null) {
    const regionCountry = REGIONS.get(resolved.region.id).country;
    if (countryCode === null) countryCode = regionCountry;
    else if (countryCode !== regionCountry) warnings.push(`country_mismatch:${resolved.region.name_ar}`);
  }
  if (countryCode === null) countryCode = defaultCountry;
  if (countryCode !== null && resolved.country === null && COUNTRIES.has(countryCode)) resolved.country = countryObj(countryCode);

  // ---- confidence
  let points = 0;
  points += resolved.region ? 25 : 0;
  points += st.city || st.district ? 20 : 0;
  points += st.street ? 30 : 0;
  points += st.building ? 15 : 0;
  points += st.apartment !== null || st.floor !== null || st.landmark || postal.length || st.block ? 10 : 0;
  points -= Math.min(30, 5 * unparsedTokens);
  points = Math.max(0, Math.min(100, points));

  return {
    input: text ?? "",
    cleaned,
    normalized: key(cleaned),
    language: detectLanguage(cleaned),
    country_code: countryCode,
    region: resolved.region ? resolved.region.name_ar : null,
    city: st.city,
    district: st.district,
    street: st.street,
    secondary_street: st.secondary_street,
    building: st.building,
    floor: st.floor,
    apartment: st.apartment,
    block: st.block,
    landmark: st.landmark,
    postal_code: postal.length ? postal[0] : null,
    phone: phones.length ? phones[0] : null,
    short_address: short.length ? short[0] : null,
    unparsed,
    warnings,
    confidence: points / 100,
    resolved,
  };
}

/** Render a parsed address (the object returned by `parse`) as one canonical line. */
export function formatAddress(parsed, lang = "ar") {
  const resolved = parsed.resolved || {};
  const english = lang === "en";
  const name = (slot, fallback) => {
    const obj = resolved[slot];
    if (obj) return english ? obj.name_en : obj.name_ar;
    return fallback;
  };
  const parts = [];
  const { street, building } = parsed;
  if (building && street && digitish(String(building))) parts.push(`${building} ${street}`);
  else if (building && street) parts.push(String(building), street);
  else if (street) parts.push(street);
  else if (building) parts.push(String(building));
  if (parsed.block) parts.push((english ? "Block " : "قطعة ") + parsed.block);
  if (parsed.floor !== null && parsed.floor !== undefined) parts.push((english ? "Floor " : "الدور ") + parsed.floor);
  if (parsed.apartment) parts.push((english ? "Apt " : "شقة ") + parsed.apartment);
  for (const slot of ["district", "city"]) {
    const value = name(slot, parsed[slot]);
    if (value) parts.push(value);
  }
  if (resolved.region) parts.push(name("region", parsed.region));
  else if (parsed.region) parts.push(parsed.region);
  if (resolved.country) parts.push(name("country", null));
  return parts.filter(Boolean).join(english ? ", " : "، ");
}
