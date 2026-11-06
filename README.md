# Arabic Address Parser · محلل العناوين العربية

Normalize, parse and compare free-text **Arabic**, **Franco-Arabic** (Arabizi) and mixed addresses from **Egypt and the Gulf**.
Zero dependencies. Identical results in **Python** and **JavaScript**.

> تفكيك وتطبيع ومقارنة العناوين المكتوبة بالعربية أو بالفرانكو أو بخليط منهما، لمصر ودول الخليج. بدون أي مكتبات خارجية، ونفس النتيجة في Python و JavaScript.

```text
محافظة الإسكندرية سموحة شارع فوزي معاذ عمارة 7 الدور الخامس شقة 21 بالقرب من مول سان ستيفانو
```

```json
{
  "country_code": "EG",
  "region": "الإسكندرية",
  "district": "سموحة",
  "street": "شارع فوزي معاذ",
  "building": "7",
  "floor": 5,
  "apartment": "21",
  "landmark": "بالقرب من مول سان ستيفانو",
  "confidence": 1.0
}
```

## Why

Every delivery company, online store and ride app ends up writing the same fragile regexes for addresses like
`٢٢ ش مصطفى النحاس مدينه نصر` or `15 share3 el tahrir el dokki`. Spelling varies (`ة/ه`, `أ/ا`, `ى/ي`), digits come in two scripts,
`ش` means *street*, the building number sits on either side of the street name, and nobody writes the governorate the same way twice.
This library turns that into structured data you can validate, geocode, route and de-duplicate.

## Install

Not published to a registry yet. Until then, use it from a clone:

```bash
# Python 3.9+
pip install ./python

# Node 18+
npm install ./js
```

## Use

**Python**

```python
from arabic_address_parser import parse, similarity, format_address

r = parse("15 شارع التحرير الدقي الجيزة")
r["street"], r["building"], r["district"], r["region"]
# ('شارع التحرير', '15', 'الدقي', 'الجيزة')

format_address(r, "en")                      # '15 شارع التحرير, Dokki, Giza, Egypt'
similarity("15 شارع التحرير الدقي", "١٥ ش التحرير، الدقي")   # 1.0
parse("شارع النصر", default_country="EG")["country_code"]    # 'EG'
```

**JavaScript**

```js
import { parse, similarity, formatAddress } from "arabic-address-parser";

const r = parse("Flat 12, Floor 3, 15 Tahrir St, Dokki, Giza, Egypt");
r.street;   // 'Tahrir St'
r.building; // '15'
r.region;   // 'الجيزة'   (canonical Arabic name; r.resolved.region.name_en is 'Giza')
```

**Command line**

```bash
python -m arabic_address_parser "قطعة 3 شارع 5 جادة 2 منزل 10 السالمية الكويت"
python -m arabic_address_parser --format en "15 شارع التحرير الدقي الجيزة"
python -m arabic_address_parser --compare "15 ش التحرير" "15 شارع التحرير"
node js/bin/cli.js "15 شارع التحرير الدقي الجيزة"
```

## What you get

`parse(text)` returns:

| Field | Meaning |
| --- | --- |
| `country_code` | ISO code (`EG`, `SA`, `AE`, `KW`, `QA`, `BH`, `OM`), taken from the text, inferred from the region, or `default_country` |
| `region` | Governorate / emirate / province, canonical Arabic name. Inferred from a district or city when not written |
| `city`, `district` | Canonical Arabic name when found in the gazetteer, otherwise the text as written |
| `street`, `secondary_street` | Street phrase including its keyword (`شارع التحرير`, `Tahrir St`); a second street (Kuwait avenue) goes to `secondary_street` |
| `building`, `floor`, `apartment`, `block` | Building number or name, floor (`الدور الثالث` → `3`, ground → `0`), flat/office, block (`قطعة`/`مجمع`) |
| `landmark` | `بجوار …`, `بالقرب من …`, `near …` |
| `postal_code`, `phone`, `short_address` | Postal code / P.O. box, phone number, Saudi short address (`RRRD2929`) |
| `unparsed` | Text that matched nothing. It is never silently dropped |
| `warnings` | e.g. `region_mismatch:الدقي` when the district belongs to another governorate than the one written |
| `confidence` | 0 to 1, how much of a delivery-grade address was recovered (see `spec/SPEC.md`) |
| `resolved` | Gazetteer objects with ids and English names, and whether the region was `inferred` |
| `normalized`, `cleaned`, `language` | Search key, display-safe text, `ar` / `en` / `mixed` |

Also: `key(text)` (search key: `الإسكندرية` = `اسكندريه`, `٦ أكتوبر` = `6 اكتوبر`), `clean(text)`, `format_address`, `similarity(a, b)` and `is_same_address(a, b)` for de-duplication.

## Coverage

* **Egypt:** all 27 governorates and about 220 cities and districts (Greater Cairo, Alexandria, Delta, canal, Sinai, Red Sea, Upper Egypt, north coast), with Arabic spelling variants and Franco-Arabic aliases.
* **Gulf:** the regions of Saudi Arabia, UAE, Kuwait, Qatar, Bahrain and Oman, plus main cities and districts (a first pass, much thinner than Egypt).
* **Address words:** street, building, floor, flat, block, district, landmark keywords in Arabic, English and Arabizi, written ordinals (`الدور الخامس`), Arabic-Indic and Persian digits.

## What it is not

* It does **not** geocode. It gives you clean components to feed to a geocoder or a delivery system.
* It is rule-based and deterministic, not a trained model. Unusual word order, heavy typos and place names missing from the gazetteer end up in `unparsed` or in `district`/`city` as written text, which is the intended failure mode.
* Spelling variants are handled by normalization and curated aliases. There is no fuzzy matching of typos yet (see the roadmap).
* Levant and Maghreb addresses are not covered yet.

## How it works

[`spec/SPEC.md`](spec/SPEC.md) describes the exact algorithm. Both packages implement it and are checked against the same
golden cases in [`spec/cases/`](spec/cases) plus a randomized parity check (`scripts/parity_check.py`) in CI.
The gazetteer lives in one readable text file, [`data/places.txt`](data/places.txt), so adding a missing place is a one-line pull request.

## Contribute

New places, spellings, countries and test addresses are the most valuable contributions, and most need no code.
Read [CONTRIBUTING.md](CONTRIBUTING.md) and pick something from [docs/ROADMAP.md](docs/ROADMAP.md).

## License

MIT, see [LICENSE](LICENSE). The gazetteer contains public geographic facts written for this project; it does not include data from commercial or restricted-license datasets.
