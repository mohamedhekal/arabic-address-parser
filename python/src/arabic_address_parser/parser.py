"""Rule-based parser that splits a free-text Arabic / Franco-Arabic address into components.

The algorithm is fully specified in spec/SPEC.md and mirrored line-for-line by the JavaScript package,
so both produce identical output for the shared test cases in spec/cases/.
"""
import re

from ._data import DATA
from .normalize import clean, key, token_key

# ---------------------------------------------------------------------------------------------- data


def _kw(name):
    return {key(w) for w in DATA["keywords"][name]}


STREET = _kw("street")
BUILDING = _kw("building")
FLOOR = _kw("floor")
APARTMENT = _kw("apartment")
BLOCK = _kw("block")
DISTRICT = _kw("district")
CITY = _kw("city")
LANDMARK = _kw("landmark")
NOISE = _kw("noise")
NUMWORD = _kw("number_word")
STREET_SUFFIX = _kw("street_suffix")
SKIP_AFTER_LANDMARK = _kw("skip_after_landmark")
ORDINALS = {key(k): v for k, v in DATA["keywords"]["ordinals"].items()}
ALL_KEYWORDS = STREET | BUILDING | FLOOR | APARTMENT | BLOCK | DISTRICT | CITY | LANDMARK | NOISE
_PREFIXABLE = STREET | BUILDING | FLOOR | APARTMENT | BLOCK | DISTRICT | CITY | LANDMARK

COUNTRIES = {c["code"]: c for c in DATA["countries"]}
REGIONS = {r["id"]: r for r in DATA["regions"]}

INDEX = {}  # key -> entry
COLLISIONS = []  # [(key, first_label, second_label)]  (checked by the test-suite)
_MAX_N = 1


def _register(entry, names):
    global _MAX_N
    for name in names:
        k = key(name)
        if not k:
            continue
        existing = INDEX.get(k)
        if existing is not None and existing is not entry:
            COLLISIONS.append((k, existing["name_ar"], entry["name_ar"]))
            continue
        INDEX[k] = entry
        _MAX_N = max(_MAX_N, len(k.split()))


for _c in DATA["countries"]:
    _register({"kind": "country", "code": _c["code"], "name_ar": _c["name_ar"], "name_en": _c["name_en"], "country": _c["code"]},
              [_c["name_ar"], _c["name_en"], *_c["aliases"]])
for _r in DATA["regions"]:
    _register({"kind": "region", "id": _r["id"], "name_ar": _r["name_ar"], "name_en": _r["name_en"], "country": _r["country"]},
              [_r["name_ar"], _r["name_en"], *_r["aliases"]])
for _p in DATA["places"]:
    _register({"kind": "place", "type": _p["type"], "region": _p["region"], "name_ar": _p["name_ar"], "name_en": _p["name_en"],
               "country": REGIONS[_p["region"]]["country"]},
              [_p["name_ar"], _p["name_en"], *_p["aliases"]])

# ------------------------------------------------------------------------------------------- patterns

_ARABIC_LETTER = "ء-ي"
_PHONE = re.compile(r"(?<![A-Za-z0-9" + _ARABIC_LETTER + r"])\+?\d[\d\-]{8,16}\d(?![A-Za-z0-9" + _ARABIC_LETTER + "])")
_POSTAL = re.compile(
    r"(?:الرمز البريدي|الرمز البريدى|رمز بريدي|رمز بريدى|الكود البريدي|الكود البريدى|كود بريدي|كود بريدى|postal code|post code|zip code|zip|ص\.?\s?ب\.?|p\.?o\.?\s?box)\s*[:\-]?\s*(\d{3,6})",
    re.IGNORECASE,
)
_SHORT_ADDRESS = re.compile(r"(?<![A-Za-z0-9])[A-Z]{4}\d{4}(?![A-Za-z0-9])")
_SEGMENT_SPLIT = re.compile(r"[,;|]+|\s[-–—]\s")
_LETTER_DIGIT = re.compile("([" + _ARABIC_LETTER + r"])(\d)")
_DIGIT_LETTER = re.compile(r"(\d)(?=[" + _ARABIC_LETTER + "]{2})")
_DIGITISH = re.compile(r"^\d+[A-Za-z\u0621-\u064A]?(?:[/\-]\d+)?$")
_TOKEN_SPLIT = re.compile(r"[.\-_/:()\[\]\"'`*]+")
_EDGE = ".:()[]\"'`-_*"


def _digitish(s):
    return bool(_DIGITISH.match(s))


def _tokenize(segment):
    segment = _LETTER_DIGIT.sub(r"\1 \2", segment)
    segment = _DIGIT_LETTER.sub(r"\1 ", segment)
    out = []
    pending = ""
    for raw in segment.split():
        raw = raw.strip(_EDGE)
        if not raw:
            continue
        if _digitish(raw):
            out.append({"raw": pending + raw, "k": raw.lower()})
            pending = ""
            continue
        for part in _TOKEN_SPLIT.split(raw):
            if not part:
                continue
            k = key(part, strip_article=False).replace(" ", "")
            if not k:
                continue
            k = token_key(k)
            if not k:
                pending += part + " "  # Latin article ("el", "al"): glued to the next token's raw text
                continue
            if len(k) > 2 and k[0] == "ب" and k[1:] in _PREFIXABLE and k not in ALL_KEYWORDS:
                k = k[1:]
            out.append({"raw": pending + part, "k": k})
            pending = ""
    return out


def _detect_language(text):
    has_ar = re.search("[؀-ۿ]", text) is not None
    has_la = re.search("[A-Za-z]", text) is not None
    if has_ar and has_la:
        return "mixed"
    if has_ar:
        return "ar"
    if has_la:
        return "en"
    return "unknown"


def _place_obj(entry):
    return {"name_ar": entry["name_ar"], "name_en": entry["name_en"], "type": entry["type"], "region_id": entry["region"]}


def _region_obj(entry, inferred=False):
    return {"id": entry["id"], "name_ar": entry["name_ar"], "name_en": entry["name_en"], "inferred": inferred}


def _country_obj(code):
    c = COUNTRIES[code]
    return {"code": c["code"], "name_ar": c["name_ar"], "name_en": c["name_en"]}


# ----------------------------------------------------------------------------------------------- parse


def parse(text, default_country=None):
    """Parse ``text`` into address components. See README for the output schema."""
    cleaned = clean(text)
    work = cleaned

    phones = []

    def _take_phone(m):
        digits = re.sub(r"[+\-]", "", m.group(0))
        if 10 <= len(digits) <= 13:
            phones.append(m.group(0))
            return " , "
        return m.group(0)

    work = _PHONE.sub(_take_phone, work)

    postal = []

    def _take_postal(m):
        postal.append(m.group(1))
        return " , "

    work = _POSTAL.sub(_take_postal, work)

    short = []

    def _take_short(m):
        short.append(m.group(0))
        return " , "

    work = _SHORT_ADDRESS.sub(_take_short, work)

    st = {
        "country": None, "region": None, "city": None, "district": None, "street": None, "building": None,
        "floor": None, "apartment": None, "block": None, "landmark": None, "secondary_street": None,
    }
    resolved = {"country": None, "region": None, "city": None, "district": None}
    unparsed = []
    unparsed_tokens = 0
    warnings = []

    for segment in _SEGMENT_SPLIT.split(work):
        toks = _tokenize(segment)
        n = len(toks)
        if n == 0:
            continue
        used = [False] * n

        def gaz_at(i):
            if used[i]:
                return None
            best = None
            for ln in range(min(_MAX_N, n - i), 0, -1):
                if any(used[i:i + ln]):
                    continue
                entry = INDEX.get(" ".join(t["k"] for t in toks[i:i + ln]))
                if entry is not None:
                    best = (ln, entry)
                    break
            return best

        def is_stop(j):
            k = toks[j]["k"]
            return k in ALL_KEYWORDS or k in NUMWORD or _digitish(toks[j]["raw"]) or gaz_at(j) is not None

        def take_name(start, maxn):
            names = []
            j = start
            while j < n and not used[j] and len(names) < maxn:
                if names and is_stop(j):
                    break
                names.append(j)
                j += 1
            return names

        def raw_of(idx):
            return " ".join(toks[i]["raw"] for i in idx)

        # 1. landmark: everything from the first landmark keyword to the end of the segment
        for i in range(n):
            if toks[i]["k"] in LANDMARK and i + 1 < n:
                j = i + 1
                if toks[j]["k"] in SKIP_AFTER_LANDMARK and j + 1 < n:
                    j += 1
                # a country / region / city at the very end belongs to the address, not to the landmark
                end = n
                while True:
                    hit = 0
                    for ln in range(min(_MAX_N, end - (j + 1)), 0, -1):
                        entry = INDEX.get(" ".join(t["k"] for t in toks[end - ln:end]))
                        if entry is not None and (entry["kind"] != "place" or entry["type"] == "city"):
                            hit = ln
                            break
                    if not hit:
                        break
                    end -= hit
                text_ = " ".join(t["raw"] for t in toks[i:end])
                if st["landmark"] is None:
                    st["landmark"] = text_
                else:
                    unparsed.append(text_)
                for x in range(i, end):
                    used[x] = True
                break

        # 1b. Latin street suffix: "Tahrir St", "26th of July Road"
        for i in range(1, n):
            if used[i] or toks[i]["k"] not in STREET_SUFFIX or re.search("[\u0600-\u06FF]", toks[i]["raw"]):
                continue
            names = []
            j = i - 1
            while j >= 0 and len(names) < 3 and not used[j] and not is_stop(j):
                names.insert(0, j)
                j -= 1
            if not names:
                continue
            phrase = raw_of(names) + " " + toks[i]["raw"]
            for x in names:
                used[x] = True
            used[i] = True
            if st["street"] is None:
                st["street"] = phrase
            else:
                st["secondary_street"] = st["secondary_street"] or phrase
            if (st["building"] is None and j >= 0 and not used[j] and _digitish(toks[j]["raw"])
                    and not (j > 0 and toks[j - 1]["k"] in (FLOOR | APARTMENT | BLOCK | BUILDING))):
                st["building"] = toks[j]["raw"]
                used[j] = True

        # 2. left-to-right scan
        i = 0
        while i < n:
            if used[i]:
                i += 1
                continue
            k = toks[i]["k"]
            g = gaz_at(i)
            if g is not None:
                ln, entry = g
                phrase = raw_of(range(i, i + ln))
                for x in range(i, i + ln):
                    used[x] = True
                if entry["kind"] == "country":
                    if st["country"] is None:
                        st["country"] = entry["code"]
                        resolved["country"] = _country_obj(entry["code"])
                    else:
                        unparsed.append(phrase)
                elif entry["kind"] == "region":
                    if st["region"] is None:
                        st["region"] = entry["id"]
                        resolved["region"] = _region_obj(entry)
                    else:
                        unparsed.append(phrase)
                else:
                    slot = "city" if entry["type"] == "city" else "district"
                    if st[slot] is None:
                        st[slot] = entry["name_ar"]
                        resolved[slot] = _place_obj(entry)
                    else:
                        unparsed.append(phrase)
                i += ln
                continue

            if k in NUMWORD and i + 1 < n and not used[i + 1]:
                used[i] = True
                i += 1
                continue
            if k in NOISE:
                used[i] = True
                i += 1
                continue

            if k in STREET:
                j = i + 1
                if j < n and toks[j]["k"] in NUMWORD and j + 1 < n:
                    used[j] = True
                    j += 1
                names = take_name(j, 4) if j < n else []
                if not names:
                    i += 1
                    continue
                phrase = toks[i]["raw"] + " " + raw_of(names)
                used[i] = True
                for x in names:
                    used[x] = True
                if st["street"] is None:
                    st["street"] = phrase
                elif st["secondary_street"] is None:
                    st["secondary_street"] = phrase
                else:
                    unparsed.append(phrase)
                nxt = names[-1] + 1
                if st["building"] is None and nxt < n and not used[nxt] and _digitish(toks[nxt]["raw"]) and gaz_at(nxt) is None:
                    st["building"] = toks[nxt]["raw"]
                    used[nxt] = True
                i = nxt
                continue

            if k in BUILDING:
                j = i + 1
                if j < n and toks[j]["k"] in NUMWORD and j + 1 < n:
                    used[j] = True
                    j += 1
                if j < n and not used[j] and _digitish(toks[j]["raw"]):
                    value = toks[j]["raw"]
                    used[i] = used[j] = True
                    i = j + 1
                else:
                    names = take_name(j, 3) if j < n else []
                    if not names:
                        i += 1
                        continue
                    value = toks[i]["raw"] + " " + raw_of(names)
                    used[i] = True
                    for x in names:
                        used[x] = True
                    i = names[-1] + 1
                if st["building"] is None:
                    st["building"] = value
                else:
                    unparsed.append(value)
                continue

            if k in FLOOR or k in APARTMENT or k in BLOCK:
                j = i + 1
                if j < n and toks[j]["k"] in NUMWORD and j + 1 < n:
                    used[j] = True
                    j += 1
                if j >= n or used[j]:
                    i += 1
                    continue
                tk = toks[j]
                if k in FLOOR:
                    if _digitish(tk["raw"]) and tk["raw"].isdigit():
                        value = int(tk["raw"])
                    elif tk["k"] in ORDINALS:
                        value = ORDINALS[tk["k"]]
                    else:
                        i += 1
                        continue
                    slot = "floor"
                else:
                    if not _digitish(tk["raw"]):
                        i += 1
                        continue
                    value = tk["raw"]
                    slot = "apartment" if k in APARTMENT else "block"
                used[i] = used[j] = True
                if st[slot] is None:
                    st[slot] = value
                else:
                    unparsed.append(str(value))
                i = j + 1
                continue

            if k in DISTRICT or k in CITY:
                j = i + 1
                if k == "قسم" and j + 1 < n and toks[j]["k"] in ORDINALS:
                    used[j] = True  # "قسم أول مدينة نصر": the ordinal is a precinct number, not a place
                    j += 1
                if j < n and not used[j] and gaz_at(j) is not None:
                    used[i] = True  # keyword before a known place name: the name is resolved on the next loop
                    i += 1
                    continue
                names = take_name(j, 3) if j < n else []
                if not names:
                    i += 1
                    continue
                slot = "city" if k in CITY else "district"
                used[i] = True
                for x in names:
                    used[x] = True
                if st[slot] is None:
                    st[slot] = raw_of(names)
                else:
                    unparsed.append(raw_of(names))
                i = names[-1] + 1
                continue

            if _digitish(toks[i]["raw"]) and i + 1 < n and not used[i + 1] and toks[i + 1]["k"] in STREET and st["building"] is None:
                st["building"] = toks[i]["raw"]
                used[i] = True
                i += 1
                continue

            i += 1

        # 3. whatever is left in this segment is unparsed
        run = []
        for x in range(n):
            if used[x]:
                if run:
                    unparsed.append(" ".join(run))
                    run = []
            else:
                run.append(toks[x]["raw"])
                unparsed_tokens += 1
        if run:
            unparsed.append(" ".join(run))

    # ---- inference and consistency checks
    for slot in ("district", "city"):
        place = resolved[slot]
        if place is None:
            continue
        if resolved["region"] is None:
            resolved["region"] = _region_obj(REGIONS[place["region_id"]], inferred=True)
            st["region"] = place["region_id"]
        elif resolved["region"]["id"] != place["region_id"]:
            warnings.append("region_mismatch:" + place["name_ar"])

    country_code = st["country"]
    if resolved["region"] is not None:
        region_country = REGIONS[resolved["region"]["id"]]["country"]
        if country_code is None:
            country_code = region_country
        elif country_code != region_country:
            warnings.append("country_mismatch:" + resolved["region"]["name_ar"])
    if country_code is None:
        country_code = default_country
    if country_code is not None and resolved["country"] is None and country_code in COUNTRIES:
        resolved["country"] = _country_obj(country_code)

    # ---- confidence
    points = 0
    points += 25 if resolved["region"] else 0
    points += 20 if (st["city"] or st["district"]) else 0
    points += 30 if st["street"] else 0
    points += 15 if st["building"] else 0
    points += 10 if (st["apartment"] is not None or st["floor"] is not None or st["landmark"] or postal or st["block"]) else 0
    points -= min(30, 5 * unparsed_tokens)
    points = max(0, min(100, points))

    region_name = resolved["region"]["name_ar"] if resolved["region"] else None
    return {
        "input": text if text is not None else "",
        "cleaned": cleaned,
        "normalized": key(cleaned),
        "language": _detect_language(cleaned),
        "country_code": country_code,
        "region": region_name,
        "city": st["city"],
        "district": st["district"],
        "street": st["street"],
        "secondary_street": st["secondary_street"],
        "building": st["building"],
        "floor": st["floor"],
        "apartment": st["apartment"],
        "block": st["block"],
        "landmark": st["landmark"],
        "postal_code": postal[0] if postal else None,
        "phone": phones[0] if phones else None,
        "short_address": short[0] if short else None,
        "unparsed": unparsed,
        "warnings": warnings,
        "confidence": points / 100,
        "resolved": resolved,
    }


def format_address(parsed, lang="ar"):
    """Render a parsed address (or the dict returned by :func:`parse`) as one canonical line."""
    resolved = parsed.get("resolved") or {}
    english = lang == "en"

    def name(slot, fallback):
        obj = resolved.get(slot)
        if obj:
            return obj["name_en"] if english else obj["name_ar"]
        return fallback

    parts = []
    street = parsed.get("street")
    building = parsed.get("building")
    if building and street and _digitish(str(building)):
        parts.append(f"{building} {street}")
    elif building and street:
        parts.extend([str(building), street])
    elif street:
        parts.append(street)
    elif building:
        parts.append(str(building))
    if parsed.get("block"):
        parts.append(("Block " if english else "قطعة ") + str(parsed["block"]))
    if parsed.get("floor") is not None:
        parts.append(("Floor " if english else "الدور ") + str(parsed["floor"]))
    if parsed.get("apartment"):
        parts.append(("Apt " if english else "شقة ") + str(parsed["apartment"]))
    for slot in ("district", "city"):
        value = name(slot, parsed.get(slot))
        if value:
            parts.append(value)
    if resolved.get("region"):
        parts.append(name("region", parsed.get("region")))
    elif parsed.get("region"):
        parts.append(parsed["region"])
    if resolved.get("country"):
        parts.append(name("country", None))
    return (", " if english else "، ").join(p for p in parts if p)
