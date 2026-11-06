# Specification

This document is the contract both implementations follow. If the Python and JavaScript packages disagree, one of them has a bug.
`spec/cases/*.json` are golden cases, and `scripts/parity_check.py` compares both implementations on thousands of random inputs.

## 1. `clean(text)`

Display-safe cleanup. Letters are not changed.

1. `null` becomes `""`. Apply Unicode **NFKC**.
2. Remove diacritics and tatweel: `U+064B-065F`, `U+0670`, `U+06D6-06ED`, `U+0640`.
3. Arabic-Indic and Persian digits become ASCII digits. `،` `؛` `؟` become `,` `;` `?`.
4. Line breaks (with surrounding spaces) become `", "`. Runs of whitespace collapse to one space. Trim.

## 2. `key(text, strip_article=true)`

Search key used for every comparison.

1. `clean`, then lowercase.
2. Fold letters: `أ إ آ ٱ`→`ا`, `ى ی`→`ي`, `ة`→`ه`, `ؤ`→`و`, `ئ`→`ي`, `ء` removed, `ک گ`→`ك`, `پ`→`ب`, `چ`→`ج`, `ڤ`→`ف`.
3. Every run of characters outside `[ء-ي a-z 0-9]` becomes one space.
4. A letter repeated 3+ times is cut to 2 (`التحريييير` → `التحرير`). Digits are untouched.
5. Per token, when `strip_article`: drop the Latin articles `el` and `al`; drop a leading `ال` when the token is longer than 3 characters (except `الله`).
6. Join with single spaces.

## 3. `parse(text, default_country=None)`

### 3.1 Extraction before tokenizing (on the cleaned text)

* **Phone:** a digit run `+?\d[\d-]{8,16}\d` not touching other letters or digits, with 10 to 13 digits. Removed.
* **Postal code:** a keyword (`الرمز البريدي`, `كود بريدي`, `zip`, `postal code`, `ص.ب`, `P.O. Box` ...) followed by 3 to 6 digits. Removed.
* **Saudi short address:** `[A-Z]{4}\d{4}`. Removed.

Removed spans become `" , "`. Only the first match of each kind is reported.

### 3.2 Segments and tokens

Split on `, ; |` and on ` - ` (dash with spaces). Per segment: insert a space between an Arabic letter and a following digit, and between a digit
and two or more following Arabic letters (so `ش9` and `15شارع` split, `5أ` stays whole). Split on whitespace and strip edge punctuation.

A token that looks like a number (`15`, `5أ`, `15/3`) stays whole with its lowercase form as key. Any other token is split on inner `. - _ / : ( ) [ ] " ' * `,
and each part gets `k = key(part, strip_article=false)` with spaces removed, then `token_key`. A part that becomes empty because it was `el`/`al` is glued to the
start of the next token's raw text (`el tahrir`). A leading `ب` is dropped when the rest is an address keyword (`بشارع` → `شارع`).

### 3.3 Gazetteer

`data/places.txt` defines countries, regions and places (`city` or `district`). Every canonical name and alias is indexed by `key()`.
Lookup is **longest match first** over consecutive unused tokens (up to the longest indexed phrase). Two different entries must never share a key
(the test-suite fails otherwise), and no address keyword may be a place name.

### 3.4 Per-segment passes

1. **Landmark.** From the first landmark keyword (`بجوار`, `بالقرب`, `near` ...) with at least one token after it (an optional `من` / `of` / `to` is skipped), to the end of the
   segment. Trailing tokens that form a country, region or `city` entry are released back to the address, always leaving at least one landmark token.
2. **Latin street suffix.** For a Latin keyword `street st road rd avenue ave square sq` at position 1 or later, the up-to-3 preceding tokens that are not stops become the street
   (`Tahrir St`). A number directly before them is the building unless it belongs to a floor/flat/block/building keyword.
3. **Left-to-right scan**, first rule that applies at each unused token:
   1. Gazetteer longest match. Country, region and place fill their slot; a second hit for a filled slot goes to `unparsed`.
   2. `رقم` / `no` followed by another token is skipped. Noise words (`محافظة`, `tel`, `موبايل` ...) are consumed.
   3. **Street keyword:** the name is the next 1 to 4 tokens. The first is always taken; the rest stop at any keyword, number, number word or gazetteer match.
      A second street fills `secondary_street`. A number right after the name becomes the building if none is set yet.
   4. **Building keyword:** a following number (`عمارة 7`) or up to 3 name tokens (`برج القاهرة`, kept with the keyword).
   5. **Floor / apartment / block keyword:** a following number. A floor also accepts ordinal words (`الثالث`=3, `الارضي`=0).
   6. **District / city keyword** (`حي`, `منطقة`, `مدينة` ...): if a gazetteer entry follows, the keyword is dropped and the entry resolves normally; otherwise up to 3 name tokens
      fill `district` / `city` as written. For `قسم`, a following ordinal is skipped (`قسم أول مدينة نصر`).
   7. A number directly before a street keyword is the building.
4. Tokens still unused are reported in `unparsed` (one string per contiguous run).

### 3.5 After all segments

* A resolved district or city without a region fills the region (`inferred: true`). With a different explicit region the result keeps the explicit one and adds
  `region_mismatch:<name>` to `warnings`. (Greater Cairo is often written loosely, so this is a warning, not an error.)
* `country_code` comes from the text, else the region's country, else `default_country`. A conflicting region adds `country_mismatch:<name>`.

### 3.6 Confidence

Integer points, divided by 100: region 25, city or district 20, street 30, building 15, any of floor/apartment/block/landmark/postal 10,
minus 5 per unparsed token (at most 30), clamped to 0..100.

## 4. `similarity(a, b)`

Content tokens are the tokens of `key(text)` without address keywords or the words `من في و of the`.
`score = 0.6 * Jaccard(token sets) + 0.4 * (1 - Levenshtein(sorted joined tokens) / longest)`.
The score is halved once for each of `building`, `apartment`, `floor` where both addresses have a value and they differ (case-insensitive).
Rounded to 4 decimals with half-up rounding. Two empty content sets score 1 if their keys are equal, else 0.

## 5. Output schema

See the README table. All field names are `snake_case` in both languages so that fixtures can be shared.
`floor` is an integer or `null`; every other component is a string or `null`; `unparsed` and `warnings` are string arrays.
